import pandas as pd
import pandas_ta as ta
import numpy as np
import datetime
from .api_service import shoonya_service

class AdvancedBacktester:
    def __init__(self, token='26000', exchange='NSE'):
        self.token = token
        self.exchange = exchange

    def get_enriched_data(self, days=5, interval=5):
        """Fetches data and calculates all requested indicators with robust key handling"""
        end_time = datetime.datetime.now()
        start_time = end_time - datetime.timedelta(days=days)
        
        ret = shoonya_service.api.get_time_price_series(
            exchange=self.exchange, 
            token=self.token, 
            starttime=int(start_time.timestamp()), 
            endtime=int(end_time.timestamp()),
            interval=interval
        )
        
        if not ret or not isinstance(ret, list):
            return None

        # Convert to DataFrame
        df = pd.DataFrame(ret)
        df = df.iloc[::-1].reset_index(drop=True)
        
        # Convert types
        for col in ['into', 'inth', 'intl', 'intc', 'intv']:
            df[col] = pd.to_numeric(df[col])
            
        df.rename(columns={'into': 'open', 'inth': 'high', 'intl': 'low', 'intc': 'close', 'intv': 'volume'}, inplace=True)

        # 1. Technical Indicators
        df['EMA_20'] = ta.ema(df['close'], length=20)
        df['SMA_50'] = ta.sma(df['close'], length=50)
        df['RSI'] = ta.rsi(df['close'], length=14)
        
        # 2. Supertrend - Robust Column Access
        # Length 10, Multiplier 3.0
        st = ta.supertrend(df['high'], df['low'], df['close'], length=10, multiplier=3)
        if st is not None:
            # Instead of hardcoded keys, we find columns by position or partial name
            # st usually has 4 columns: [Supertrend, Direction, Long, Short]
            df['SUPERTREND'] = st.iloc[:, 0] 
            df['ST_DIR'] = st.iloc[:, 1]
        else:
            df['SUPERTREND'] = np.nan
            df['ST_DIR'] = 0

        # 3. Heikin Ashi
        ha_df = ta.ha(df['open'], df['high'], df['low'], df['close'])
        df['ha_open'] = ha_df.iloc[:, 0]
        df['ha_high'] = ha_df.iloc[:, 1]
        df['ha_low'] = ha_df.iloc[:, 2]
        df['ha_close'] = ha_df.iloc[:, 3]

        return df