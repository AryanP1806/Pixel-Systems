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

    # Store token in service (needed for ensure_session)
    shoonya_service.session_token = token


    # Keep session alive
    shoonya_service.get_nifty_price('26000', session_token=token)


    engine = Backtester(token='26000')

    df = engine.get_history(timeframe=timeframe, days=timeline)



    # ✅ FIX: Do NOT logout on API failure
    if df is None:

        messages.error(
            request,
            "Unable to fetch market data right now. Please refresh and try again."
        )

        return render(request, 'trading/backtest.html', {
            'candles_json': '[]',
            'sma50_json': '[]',
            'sma200_json': '[]',
            'markers_json': '[]',
            'current_tf': timeframe,
            'current_tl': timeline
        })



    if df.empty:

        messages.warning(
            request,
            "No data available for selected timeframe."
        )

        return render(request, 'trading/backtest.html', {
            'candles_json': '[]',
            'sma50_json': '[]',
            'sma200_json': '[]',
            'markers_json': '[]',
            'current_tf': timeframe,
            'current_tl': timeline
        })



    # Sorting guarantee
    df['time_dt'] = pd.to_datetime(df['time'], dayfirst=True)

    df = df.sort_values("time_dt").reset_index(drop=True)



    candles, sma50, sma200, markers = [], [], [], []


    for _, row in df.iterrows():

        t = int(row['time_dt'].timestamp())

        open_p  = float(row['open'])
        high_p  = float(row['high'])
        low_p   = float(row['low'])
        close_p = float(row['close'])


        # Validate OHLC
        if np.isnan(open_p) or np.isnan(close_p):
            continue


        candles.append({
            'time': t,
            'open': open_p,
            'high': high_p,
            'low': low_p,
            'close': close_p
        })


        if not np.isnan(row['sma50']):
            sma50.append({
                'time': t,
                'value': float(row['sma50'])
            })


        if not np.isnan(row['sma200']):
            sma200.append({
                'time': t,
                'value': float(row['sma200'])
            })


        if row['signal'] == 'BUY':

            markers.append({
                'time': t,
                'position': 'belowBar',
                'color': '#10b981',
                'shape': 'arrowUp',
                'text': 'BUY'
            })


        elif row['signal'] == 'SELL':

            markers.append({
                'time': t,
                'position': 'aboveBar',
                'color': '#f43f5e',
                'shape': 'arrowDown',
                'text': 'SELL'
            })



    context = {
        'candles_json': json.dumps(candles or []),
        'sma50_json': json.dumps(sma50 or []),
        'sma200_json': json.dumps(sma200 or []),
        'markers_json': json.dumps(markers or []),
        'current_tf': timeframe,
        'current_tl': timeline
    }


    return render(request, 'trading/backtest.html', context)
