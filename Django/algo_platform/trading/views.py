from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from .api_service import shoonya_service
from django.shortcuts import render, redirect, get_object_or_404 # Ensure get_object_or_404 is here
from .models import Strategy, Order # Ensure Strategy is imported
from django.shortcuts import render, redirect
from django.contrib import messages
from .api_service import shoonya_service

def login_view(request):
    if request.method == 'POST':
        totp = request.POST.get('totp')
        
        if not totp:
            messages.error(request, "Please enter the TOTP.")
            return render(request, 'trading/login.html')

        # Attempt Shoonya Login
        res = shoonya_service.login_with_totp(totp)

        if res and res.get('stat') == 'Ok':
            # Store essential data in session
            request.session['shoonya_token'] = res.get('susertoken')
            request.session['user_id'] = res.get('uid')
            
            messages.success(request, f"Logged in as {res.get('uname')}")
            return redirect('dashboard')
        else:
            error_emsg = res.get('emsg', 'Invalid TOTP or Credentials') if res else "Connection Error"
            messages.error(request, f"Login Failed: {error_emsg}")

    return render(request, 'trading/login.html')

def dashboard(request):
    token = request.session.get('shoonya_token')
    if not token:
        return redirect('login')

    # Pass the session token into the service to ensure the SDK object is 're-hydrated'
    nifty_data = shoonya_service.get_nifty_price('26000', session_token=token)
    
    if not nifty_data:
        messages.warning(request, "Market data currently unavailable. Ensure NSE exchange is enabled.")

    context = {
        'user_id': request.session.get('user_id'),
        'nifty': nifty_data,
    }
    return render(request, 'trading/dashboard.html', context)


def logout_user(request):
    logout(request)
    return redirect('login')


import json
import numpy as np
import pandas as pd
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .backtest_engine import Backtester
from .models import Strategy
from .api_service import shoonya_service

def backtest_view(request):
    if 'shoonya_token' not in request.session:
        return redirect('login')

    # ----------------- PARAMETERS -----------------
    all_strategies = Strategy.objects.all()
    timeframe = request.GET.get('timeframe', '5')
    timeline = int(request.GET.get('timeline', '5'))
    candle_type = request.GET.get('candle_type', 'normal')
    strategy_id = request.GET.get('strategy_id')

    strategy_obj = None
    if strategy_id and strategy_id != 'None':
        strategy_obj = get_object_or_404(Strategy, pk=strategy_id)

    token = strategy_obj.token if strategy_obj else '26000'
    exchange = strategy_obj.exchange if strategy_obj else 'NSE'

    # ----------------- FETCH DATA -----------------
    engine = Backtester(token=token, exchange=exchange)
    df = engine.get_history(
        timeframe=timeframe,
        days=timeline,
        strategy_obj=strategy_obj,
        candle_type=candle_type
    )

    if df is None or df.empty:
        messages.error(request, "Market data unavailable.")
        return render(request, 'trading/backtest.html', {
            'all_strategies': all_strategies
        })

    # ----------------- DYNAMIC INDICATORS -----------------
    # ----------------- MULTIPLE DYNAMIC INDICATORS -----------------
    indicator_types = request.GET.getlist("indicator_type[]")
    indicator_periods = request.GET.getlist("indicator_period[]")

    for ind_type, period in zip(indicator_types, indicator_periods):
        try:
            period = int(period)
        except:
            continue

        col_name = f"{ind_type}_{period}"

        if ind_type == "ema":
            df[col_name] = df['close'].ewm(
                span=period, adjust=False
            ).mean()

        elif ind_type == "sma":
            df[col_name] = df['close'].rolling(
                window=period
            ).mean()

        elif ind_type == "rsi":
            delta = df['close'].diff()
            gain = delta.where(delta > 0, 0).rolling(period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(period).mean()
            rs = gain / loss.replace(0, np.nan)
            df[col_name] = 100 - (100 / (1 + rs))
            
    # try:
    #     if ema_period:
    #         ema_period = int(ema_period)
    #         df[f'ema_{ema_period}'] = df['close'].ewm(
    #             span=ema_period, adjust=False
    #         ).mean()

    #     if sma_period:
    #         sma_period = int(sma_period)
    #         df[f'sma_{sma_period}'] = df['close'].rolling(
    #             window=sma_period
    #         ).mean()

    #     if rsi_period:
    #         rsi_period = int(rsi_period)
    #         delta = df['close'].diff()
    #         gain = delta.where(delta > 0, 0).rolling(rsi_period).mean()
    #         loss = (-delta.where(delta < 0, 0)).rolling(rsi_period).mean()
    #         rs = gain / loss.replace(0, np.nan)
    #         df[f'rsi_{rsi_period}'] = 100 - (100 / (1 + rs))
    # except:
    #     pass

    # ----------------- DATE CLEAN -----------------
    # if timeframe == 'D':
    #     df['time_dt'] = pd.to_datetime(
    #         df['time'],
    #         format='%d-%b-%Y',
    #         errors='coerce'
    #     )
    # else:
    #     df['time_dt'] = pd.to_datetime(
    #         df['time'],
    #         format='%d-%b-%Y %H:%M:%S',
    #         errors='coerce'
    #     )
    df['time_dt'] = pd.to_datetime(df['time'], errors='coerce', dayfirst=True)
    df = df.dropna(subset=['time_dt']).sort_values("time_dt")

    # ----------------- PACK DATA -----------------
    candles = []
    markers = []
    trades = []
    dynamic_studies = {}

    indicator_columns = [
        col for col in df.columns
        if col.startswith(("ema_", "sma_", "rsi_"))
    ]

    active_trade = None

    for row in df.itertuples():
        row_dict = row._asdict()
        t = int(row.time_dt.timestamp())
        close_val = float(row.close)

        candles.append({
            'time': t,
            'open': float(row.open),
            'high': float(row.high),
            'low': float(row.low),
            'close': close_val
        })

        # ---- PACK INDICATORS ----
        for col in indicator_columns:
            val = row_dict.get(col)
            if val is not None and not pd.isna(val):
                dynamic_studies.setdefault(col, []).append({
                    "time": t,
                    "value": float(val)
                })

        # ---- PACK TRADES ----
        signal = row_dict.get('signal')

        if signal == 'BUY' and not active_trade:
            active_trade = {
                'entry_price': close_val,
                'entry_time': row.time_dt.strftime('%Y-%m-%d %H:%M'),
                'side': 'BUY'
            }
            markers.append({
                'time': t,
                'position': 'belowBar',
                'color': '#10b981',
                'shape': 'arrowUp',
                'text': 'BUY'
            })

        elif signal == 'SELL' and active_trade:
            pnl = close_val - active_trade['entry_price']
            trades.append({
                'side': active_trade['side'],
                'entry_price': active_trade['entry_price'],
                'exit_price': close_val,
                'entry_time': active_trade['entry_time'],
                'exit_time': row.time_dt.strftime('%Y-%m-%d %H:%M'),
                'pnl': round(pnl, 2)
            })
            markers.append({
                'time': t,
                'position': 'aboveBar',
                'color': '#f43f5e',
                'shape': 'arrowDown',
                'text': 'SELL'
            })
            active_trade = None

    context = {
        'all_strategies': all_strategies,
        'strategy': strategy_obj,
        'candles_json': json.dumps(candles),
        'dynamic_studies_json': json.dumps(dynamic_studies),
        'markers_json': json.dumps(markers),
        'trades_json': json.dumps(trades),
        'current_tf': timeframe,
        'current_tl': timeline
    }

    return render(request, 'trading/backtest.html', context)


from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Strategy

def strategy_list(request):
    """Overall page showing all strategies."""
    if 'shoonya_token' not in request.session:
        return redirect('login')
    strategies = Strategy.objects.all()
    return render(request, 'trading/strategy_list.html', {'strategies': strategies})

import json
from django.shortcuts import render, redirect, get_object_or_404
from .models import Strategy

def strategy_upsert(request, pk=None):
    strategy = get_object_or_404(Strategy, pk=pk) if pk else None

    if request.method == 'POST':
        # Capture raw lists from the frontend condition-row names
        inds = request.POST.getlist('long_indicator[]')
        vals = request.POST.getlist('long_value[]')
        ops = request.POST.getlist('long_operator[]')
        target_inds = request.POST.getlist('long_target_indicator[]')
        target_vals = request.POST.getlist('long_target_value[]')

        # Structure the logic into a dictionary
        logic_data = {
            "long": [
                {
                    "ind1": i, 
                    "val1": v, 
                    "op": o, 
                    "ind2": ti, 
                    "val2": tv
                } for i, v, o, ti, tv in zip(inds, vals, ops, target_inds, target_vals)
            ]
        }

        if strategy:
            strategy.name = request.POST.get('name')
            strategy.logic_config = logic_data
            strategy.save()
        else:
            Strategy.objects.create(
                name=request.POST.get('name'),
                logic_config=logic_data,
                token=request.POST.get('token'),
                symbol=request.POST.get('symbol')
            )
        return redirect('strategy_list')

    return render(request, 'trading/strategy_builder.html', {'strategy': strategy})

def strategy_viewer(request, pk):
    """Detail page for a specific strategy logic."""
    if 'shoonya_token' not in request.session:
        return redirect('login')
    strategy = get_object_or_404(Strategy, pk=pk)
    return render(request, 'trading/strategy_viewer.html', {'strat': strategy})
