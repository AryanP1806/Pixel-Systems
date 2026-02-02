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


# Add these imports to your existing views.py
import json
from .backtest_engine import Backtester

def backtest_view(request):
    if 'shoonya_token' not in request.session:
        return redirect('login')

    strategy = request.GET.get('strategy', 'MA_CROSS')
    
    # Initialize Shoonya session for the SDK
    token = request.session.get('shoonya_token')
    shoonya_service.get_nifty_price('26000', session_token=token)

    engine = Backtester(token='26000')
    df = engine.get_history(days=3)
    
    chart_data = []
    buy_signals = []
    sell_signals = []

    if df is not None:
        results = engine.run_strategy(df)
        
        # Prepare data for ApexCharts
        for _, row in results.iterrows():
            timestamp = row['time'] # Shoonya format: 'DD-MM-YYYY HH:MM:SS'
            price = float(row['intc'])
            chart_data.append({'x': timestamp, 'y': price})
            
            if row['signal'] == 'BUY':
                buy_signals.append({'x': timestamp, 'y': price})
            elif row['signal'] == 'SELL':
                sell_signals.append({'x': timestamp, 'y': price})

    context = {
        'chart_data': json.dumps(chart_data),
        'buy_signals': json.dumps(buy_signals),
        'sell_signals': json.dumps(sell_signals),
        'strategy': strategy
    }
    return render(request, 'trading/backtest.html', context)

def logout_user(request):
    logout(request)
    return redirect('login')