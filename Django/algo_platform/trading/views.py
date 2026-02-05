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
from django.shortcuts import render, redirect
from .backtest_engine import Backtester
from .api_service import shoonya_service

def backtest_view(request):
    if 'shoonya_token' not in request.session:
        return redirect('login')

    # Defaults
    timeframe = request.GET.get('timeframe', 'D')
    timeline = int(request.GET.get('timeline', '365'))

    token = request.session.get('shoonya_token')
    # Refresh API session
    shoonya_service.get_nifty_price('26000', session_token=token)

    engine = Backtester(token='26000')
    df = engine.get_history(timeframe=timeframe, days=timeline)
    
    if df is None or df.empty:
        return render(request, 'trading/backtest.html', {'error': 'Broker returned empty data. Check if symbols are correct.'})

    candles, sma50, sma200, buy_marks, sell_marks = [], [], [], [], []

    for _, row in df.iterrows():
        t = row['time']
        close_p = float(row['close'])
        
        # ApexCharts Format
        candles.append({'x': t, 'y': [row['open'], row['high'], row['low'], close_p]})
        
        # Line Indicators
        sma50.append({'x': t, 'y': float(row['sma50']) if not np.isnan(row['sma50']) else None})
        sma200.append({'x': t, 'y': float(row['sma200']) if not np.isnan(row['sma200']) else None})
        
        # Signals as scatter points on price
        if row['signal'] == 'BUY':
            buy_marks.append({'x': t, 'y': close_p})
        elif row['signal'] == 'SELL':
            sell_marks.append({'x': t, 'y': close_p})

    context = {
        'candles_json': json.dumps(candles),
        'sma50_json': json.dumps(sma50),
        'sma200_json': json.dumps(sma200),
        'buy_marks_json': json.dumps(buy_marks),
        'sell_marks_json': json.dumps(sell_marks),
        'current_tf': timeframe,
        'current_tl': timeline
    }
    return render(request, 'trading/backtest.html', context)