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
from django.shortcuts import render, redirect
from .backtest_engine import Backtester
from .api_service import shoonya_service

def backtest_view(request):
    if 'shoonya_token' not in request.session:
        return redirect('login')

    all_strategies = Strategy.objects.all()

    timeframe = request.GET.get('timeframe', '5')  # Candle size: 1, 3, 5, 15, 60, D
    timeline = int(request.GET.get('timeline', '5')) # Period: 5 (days), 30, 90, 180, 365, 730
    candle_type = request.GET.get('candle_type', 'normal') # normal or heikin_ashi
    
    token = request.session.get('shoonya_token')
    # 🔥 Force broker session before backtest
    shoonya_service.session_token = token
    shoonya_service.ensure_session(token)

    shoonya_service.get_nifty_price('26000', session_token=token)

    # engine = Backtester(token='26000')
    # df = engine.get_history(timeframe=timeframe, days=timeline)
    strategy_id = request.GET.get('strategy_id')
    strategy_obj = None

    if strategy_id and strategy_id != 'None':
        strategy_obj = get_object_or_404(Strategy, pk=strategy_id)
    
    # 3. Handle Parameter Access Safely
    if strategy_obj:
        # Verify parameters only if a strategy exists
        if strategy_obj.ema_period <= 0 or strategy_obj.sma_period <= 0:
            messages.error(request, f"Invalid parameters for {strategy_obj.name}. Please check settings.")
            return redirect('strategy_list')
        
        token = strategy_obj.token.strip()
        exchange = strategy_obj.exchange.strip().upper()

        # Hard safety
        if token == "26000":
            exchange = "NSE"
    else:
        # Fallback for "General" backtest (No strategy selected)
        token = '26000'
        exchange = 'NSE'
        # Optional: Create a dummy object or just use defaults in the engine
        strategy_obj = None

        
    engine = Backtester(token=token, exchange=exchange) 
    # df = engine.get_history(timeframe=timeframe, days=timeline, strategy_obj=strategy_obj)
    df = engine.get_history(timeframe=timeframe, days=timeline, strategy_obj=strategy_obj, candle_type=candle_type)
    if df is None or df.empty:
        messages.error(request, "Unable to fetch market data.")
        return render(request, 'trading/backtest.html', {'candles_json': '[]', 'current_tf': timeframe, 'current_tl': timeline})

    # 1. Define explicit formats to handle Shoonya's inconsistent API responses
    if timeframe == 'D':
        # Try primary daily format: 07-02-2026
        df['time_dt'] = pd.to_datetime(df['time'], format='%d-%m-%Y', errors='coerce')
        
        # Fallback 1: Shoonya sometimes uses 2026-02-07
        if df['time_dt'].isna().all():
            df['time_dt'] = pd.to_datetime(df['time'], format='%Y-%m-%d', errors='coerce')
        
        # Fallback 2: Shoonya sometimes uses 07-Feb-2026
        if df['time_dt'].isna().all():
            df['time_dt'] = pd.to_datetime(df['time'], format='%d-%b-%Y', errors='coerce')
    else:
        # Intraday format: 07-02-2026 15:30:00
        df['time_dt'] = pd.to_datetime(df['time'], format='%d-%m-%Y %H:%M:%S', errors='coerce')

    # 2. Final safety: If all explicit formats failed, use a fast, warning-free catch-all
    # We remove 'dayfirst' and use 'format' as None to let pandas use its C-engine if possible
    if df['time_dt'].isna().all():
        df['time_dt'] = pd.to_datetime(df['time'], errors='coerce')

    # 3. Clean and sort
    df = df.dropna(subset=['time_dt', 'open', 'close'])
    df = df.sort_values("time_dt").reset_index(drop=True)
    # Prepare Data Packs

    trades = []
    active_trade = None
    candles, ema_data, sma200_data, rsi_data, markers = [], [], [], [], []
    ema21_data, sma20_data, sma50_data = [], [], []
    for row in df.itertuples():
        t = int(row.time_dt.timestamp())
        curr_close = float(row.close)
        
        # 1. Standard Candle Data
        candles.append({'time': t, 'open': float(row.open), 'high': float(row.high), 'low': float(row.low), 'close': curr_close})
        
        # 2. Strategy Indicators (Using names from backtest_engine.py)
        # We check hasattr because if the engine failed to calculate one, it won't crash the loop
        if hasattr(row, 'ema50') and not np.isnan(row.ema50): 
            ema_data.append({'time': t, 'value': float(row.ema50)}) 
            
        if hasattr(row, 'sma200') and not np.isnan(row.sma200): 
            sma200_data.append({'time': t, 'value': float(row.sma200)})
            
        if hasattr(row, 'rsi14') and not np.isnan(row.rsi14): 
            rsi_data.append({'time': t, 'value': float(row.rsi14)})
            

        if not np.isnan(row.ema21): ema21_data.append({'time': t, 'value': float(row.ema21)})
        if not np.isnan(row.sma20): sma20_data.append({'time': t, 'value': float(row.sma20)})
        if not np.isnan(row.sma50): sma50_data.append({'time': t, 'value': float(row.sma50)})
        # 3. Strategy Signals
        # if hasattr(row, 'signal'):
        #     if row.signal == 'BUY':
        #         markers.append({'time': t, 'position': 'belowBar', 'color': '#10b981', 'shape': 'arrowUp', 'text': 'BUY'})
        #     elif row.signal == 'SELL':
        #         markers.append({'time': t, 'position': 'aboveBar', 'color': '#f43f5e', 'shape': 'arrowDown', 'text': 'SELL'})
        signal = getattr(row, 'signal', None)
        if signal == 'BUY' and not active_trade:
            active_trade = {
                'entry_price': curr_close, 
                'entry_time': row.time_dt.strftime('%Y-%m-%d %H:%M'), 
                'side': 'BUY'
            }
            markers.append({'time': t, 'position': 'belowBar', 'color': '#10b981', 'shape': 'arrowUp', 'text': 'BUY'})
        
        elif signal == 'SELL' and active_trade:
            pnl = curr_close - active_trade['entry_price']
            trades.append({
                'side': active_trade['side'],
                'entry_price': active_trade['entry_price'],
                'exit_price': curr_close,
                'entry_time': active_trade['entry_time'],
                'exit_time': row.time_dt.strftime('%Y-%m-%d %H:%M'),
                'pnl': round(pnl, 2)
            })
            markers.append({'time': t, 'position': 'aboveBar', 'color': '#f43f5e', 'shape': 'arrowDown', 'text': 'SELL'})
            active_trade = None
    if active_trade:
        final_price = float(df.iloc[-1]['close'])
        pnl = final_price - active_trade['entry_price']
        trades.append({
            'side': active_trade['side'],
            'entry_price': active_trade['entry_price'],
            'exit_price': final_price,
            'entry_time': active_trade['entry_time'],
            'exit_time': df.iloc[-1]['time_dt'].strftime('%Y-%m-%d %H:%M'),
            'pnl': round(pnl, 2)
        })    
    print(f"DEBUG: Total trades created = {len(trades)}")
    context = {
        # 'candles_json': json.dumps(candles) if candles else '[]',
        # 'sma50_json': json.dumps(sma50) if sma50 else '[]',
        # 'sma200_json': json.dumps(sma200) if sma200 else '[]',
        # 'ema9_json': json.dumps(ema9) if ema9 else '[]',
        # 'ema21_json': json.dumps(ema21) if ema21 else '[]',
        # 'sma20_json': json.dumps(sma20) if sma20 else '[]',
        # 'rsi14_json': json.dumps(rsi14) if rsi14 else '[]',
        # 'markers_json': json.dumps(markers) if markers else '[]',
        # 'current_tf': timeframe, 
        # 'current_tl': timeline
        'all_strategies': all_strategies,
        'strategy': strategy_obj,
        'candles_json': json.dumps(candles),
        'ema9_json': json.dumps(ema_data),     # This feeds the 'EMA 9' button on UI
        'ema21_json': json.dumps(ema21_data), # NEW
        'sma20_json': json.dumps(sma20_data), # NEW
        'sma50_json': json.dumps(sma50_data),
        'sma200_json': json.dumps(sma200_data), # This feeds the 'SMA 200' button on UI
        'rsi_json': json.dumps(rsi_data),       # This feeds the 'RSI 14' button on UI
        'markers_json': json.dumps(markers),
        'trades_json': json.dumps(trades),      # This populates the Trade Journal table
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

def strategy_upsert(request, pk=None):
    """Handles both Creating and Editing strategies."""
    if 'shoonya_token' not in request.session:
        return redirect('login')
    
    strategy = None
    if pk:
        strategy = get_object_or_404(Strategy, pk=pk)

    if request.method == 'POST':
        # Extraction
        name = request.POST.get('name')
        symbol = request.POST.get('symbol')
        token = request.POST.get('token')
        exch = request.POST.get('exchange', 'NSE')
        ema_p = request.POST.get('ema_period', 21)
        sma_p = request.POST.get('sma_period', 200)

        if strategy:
            # Update
            strategy.name = name
            strategy.symbol = symbol
            strategy.token = token
            strategy.exchange = exch
            strategy.ema_period = ema_p
            strategy.sma_period = sma_p
            strategy.save()
            messages.success(request, f"Strategy '{name}' updated.")
        else:
            # Create
            Strategy.objects.create(
                name=name,
                symbol=symbol,
                token=token,
                exchange=exch,
                is_active=False
            )
            messages.success(request, f"Strategy '{name}' created successfully.")
        
        return redirect('strategy_list')
        
    return render(request, 'trading/strategy_builder.html', {
        'strategy': strategy,
        'is_editing': strategy is not None
    })

def strategy_viewer(request, pk):
    """Detail page for a specific strategy logic."""
    if 'shoonya_token' not in request.session:
        return redirect('login')
    strategy = get_object_or_404(Strategy, pk=pk)
    return render(request, 'trading/strategy_viewer.html', {'strat': strategy})
