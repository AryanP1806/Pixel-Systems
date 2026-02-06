from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from .api_service import shoonya_service

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

    engine = Backtester(token='26000')
    df = engine.get_history(timeframe=timeframe, days=timeline)

    if df is None or df.empty:
        messages.error(request, "Unable to fetch market data.")
        return render(request, 'trading/backtest.html', {'candles_json': '[]', 'current_tf': timeframe, 'current_tl': timeline})

    df['time_dt'] = pd.to_datetime(df['time'], dayfirst=True)
    df = df.sort_values("time_dt").reset_index(drop=True)

    # Prepare Data Packs
    candles, sma50, sma200, ema9, ema21, sma20, rsi14, markers = [], [], [], [], [], [], [], []

    for _, row in df.iterrows():
        t = int(row['time_dt'].timestamp())
        close_p = float(row['close'])
        if np.isnan(float(row['open'])) or np.isnan(close_p): continue

        candles.append({'time': t, 'open': float(row['open']), 'high': float(row['high']), 'low': float(row['low']), 'close': close_p})
        
        if not np.isnan(row['sma50']): sma50.append({'time': t, 'value': float(row['sma50'])})
        if not np.isnan(row['sma200']): sma200.append({'time': t, 'value': float(row['sma200'])})
        if not np.isnan(row['ema9']): ema9.append({'time': t, 'value': float(row['ema9'])})
        if not np.isnan(row['ema21']): ema21.append({'time': t, 'value': float(row['ema21'])})
        if not np.isnan(row['sma20']): sma20.append({'time': t, 'value': float(row['sma20'])})
        if not np.isnan(row['rsi14']): rsi14.append({'time': t, 'value': float(row['rsi14'])})

        if row['signal'] == 'BUY':
            markers.append({'time': t, 'position': 'belowBar', 'color': '#10b981', 'shape': 'arrowUp', 'text': 'BUY'})
        elif row['signal'] == 'SELL':
            markers.append({'time': t, 'position': 'aboveBar', 'color': '#f43f5e', 'shape': 'arrowDown', 'text': 'SELL'})

    context = {
        'candles_json': json.dumps(candles),
        'sma50_json': json.dumps(sma50),
        'sma200_json': json.dumps(sma200),
        'ema9_json': json.dumps(ema9),
        'ema21_json': json.dumps(ema21),
        'sma20_json': json.dumps(sma20),
        'rsi14_json': json.dumps(rsi14),
        'markers_json': json.dumps(markers),
        'current_tf': timeframe, 'current_tl': timeline
    }
    return render(request, 'trading/backtest.html', context)