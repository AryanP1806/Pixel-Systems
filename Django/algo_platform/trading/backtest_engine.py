import pandas as pd
import datetime
import time
from .api_service import shoonya_service

class Backtester:
    def __init__(self, token='26000', exchange='NSE'):
        self.token = token
        self.exchange = exchange

    def get_history(self, days=5):
        """Fetches historical candles from Shoonya"""
        end_time = datetime.datetime.now()
        start_time = end_time - datetime.timedelta(days=days)
        
        # Shoonya expects epoch timestamps
        ret = shoonya_service.api.get_time_price_series(
            exchange=self.exchange, 
            token=self.token, 
            starttime=int(start_time.timestamp()), 
            endtime=int(end_time.timestamp()),
            interval=5 # 5 minute candles
        )
        
        if ret and isinstance(ret, list):
            df = pd.DataFrame(ret)
            # Shoonya returns strings, convert to numeric
            df['into'] = pd.to_numeric(df['into']) # Open
            df['inth'] = pd.to_numeric(df['inth']) # High
            df['intl'] = pd.to_numeric(df['intl']) # Low
            df['intc'] = pd.to_numeric(df['intc']) # Close
            return df
        return None

    def run_strategy(self, df, fast_ma=9, slow_ma=21):
        """Simple MA Crossover Backtest"""
        df = df.iloc[::-1].reset_index(drop=True) # Shoonya returns newest first, reverse it
        
        df['fast_ma'] = df['intc'].rolling(window=fast_ma).mean()
        df['slow_ma'] = df['intc'].rolling(window=slow_ma).mean()
        
        signals = []
        for i in range(len(df)):
            if i < slow_ma:
                signals.append(None)
                continue
            
            # Crossover logic
            if df['fast_ma'][i] > df['slow_ma'][i] and df['fast_ma'][i-1] <= df['slow_ma'][i-1]:
                signals.append('BUY')
            elif df['fast_ma'][i] < df['slow_ma'][i] and df['fast_ma'][i-1] >= df['slow_ma'][i-1]:
                signals.append('SELL')
            else:
                signals.append(None)
        
        df['signal'] = signals
        return df