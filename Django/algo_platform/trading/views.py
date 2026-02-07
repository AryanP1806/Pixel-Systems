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

    timeframe = request.GET.get('timeframe', 'D')
    timeline = int(request.GET.get('timeline', '365'))
    token = request.session.get('shoonya_token')
    shoonya_service.session_token = token
    shoonya_service.get_nifty_price('26000', session_token=token)

    # engine = Backtester(token='26000')
    # df = engine.get_history(timeframe=timeframe, days=timeline)

    strategy_id = request.GET.get('strategy_id')
    strategy_obj = None
    if strategy_id:
        strategy_obj = get_object_or_404(Strategy, pk=strategy_id)
        # Override chart settings with strategy settings
        token = strategy_obj.token
        # You could also override timeframe/timeline here if stored in model
    
    engine = Backtester(token=token)
    # PASS THE STRATEGY OBJECT TO THE ENGINE
    df = engine.get_history(timeframe=timeframe, days=timeline, strategy_obj=strategy_obj)
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
    candles, sma50, sma200, ema9, ema21, sma20, rsi14, markers = [], [], [], [], [], [], [], []

    # for _, row in df.iterrows():
    #     t = int(row['time_dt'].timestamp())
    #     close_p = float(row['close'])
    #     if np.isnan(float(row['open'])) or np.isnan(close_p): continue

    #     candles.append({'time': t, 'open': float(row['open']), 'high': float(row['high']), 'low': float(row['low']), 'close': close_p})
        
    #     if not np.isnan(row['sma50']): sma50.append({'time': t, 'value': float(row['sma50'])})
    #     if not np.isnan(row['sma200']): sma200.append({'time': t, 'value': float(row['sma200'])})
    #     if not np.isnan(row['ema9']): ema9.append({'time': t, 'value': float(row['ema9'])})
    #     if not np.isnan(row['ema21']): ema21.append({'time': t, 'value': float(row['ema21'])})
    #     if not np.isnan(row['sma20']): sma20.append({'time': t, 'value': float(row['sma20'])})
    #     if not np.isnan(row['rsi14']): rsi14.append({'time': t, 'value': float(row['rsi14'])})

    #     if row['signal'] == 'BUY':
    #         markers.append({'time': t, 'position': 'belowBar', 'color': '#10b981', 'shape': 'arrowUp', 'text': 'BUY'})
    #     elif row['signal'] == 'SELL':
    #         markers.append({'time': t, 'position': 'aboveBar', 'color': '#f43f5e', 'shape': 'arrowDown', 'text': 'SELL'})
    # Use itertuples for faster processing
    for row in df.itertuples():
        t = int(row.time_dt.timestamp())
        close_p = float(row.close)
        
        # 1. Standard Candle Data
        candles.append({'time': t, 'open': float(row.open), 'high': float(row.high), 'low': float(row.low), 'close': close_p})
        
        # 2. Strategy Indicators (Using names from backtest_engine.py)
        # We check hasattr because if the engine failed to calculate one, it won't crash the loop
        if hasattr(row, 'ema50') and not np.isnan(row.ema50): 
            ema9.append({'time': t, 'value': float(row.ema50)}) 
            
        if hasattr(row, 'sma200') and not np.isnan(row.sma200): 
            sma200.append({'time': t, 'value': float(row.sma200)})
            
        if hasattr(row, 'rsi14') and not np.isnan(row.rsi14): 
            rsi14.append({'time': t, 'value': float(row.rsi14)})

        # 3. Strategy Signals
        if hasattr(row, 'signal'):
            if row.signal == 'BUY':
                markers.append({'time': t, 'position': 'belowBar', 'color': '#10b981', 'shape': 'arrowUp', 'text': 'BUY'})
            elif row.signal == 'SELL':
                markers.append({'time': t, 'position': 'aboveBar', 'color': '#f43f5e', 'shape': 'arrowDown', 'text': 'SELL'})

    context = {
        # 'candles_json': json.dumps(candles),
        # 'sma50_json': json.dumps(sma50),
        # 'sma200_json': json.dumps(sma200),
        # 'ema9_json': json.dumps(ema9),
        # 'ema21_json': json.dumps(ema21),
        # 'sma20_json': json.dumps(sma20),
        # 'rsi14_json': json.dumps(rsi14),
        # 'markers_json': json.dumps(markers),
        # 'current_tf': timeframe, 'current_tl': timeline,

        'candles_json': json.dumps(candles) if candles else '[]',
        'sma50_json': json.dumps(sma50) if sma50 else '[]',
        'sma200_json': json.dumps(sma200) if sma200 else '[]',
        'ema9_json': json.dumps(ema9) if ema9 else '[]',
        'ema21_json': json.dumps(ema21) if ema21 else '[]',
        'sma20_json': json.dumps(sma20) if sma20 else '[]',
        'rsi14_json': json.dumps(rsi14) if rsi14 else '[]',
        'markers_json': json.dumps(markers) if markers else '[]',
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
        
        if strategy:
            # Update
            strategy.name = name
            strategy.symbol = symbol
            strategy.token = token
            strategy.exchange = exch
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