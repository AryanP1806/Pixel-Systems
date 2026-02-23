import json
import pandas as pd
import datetime
import numpy as np
import logging
import time   # ✅ ADD: for retry backoff

from .api_service import shoonya_service

logger = logging.getLogger(__name__)

class Backtester:

    def __init__(self, token='26000', exchange='NSE'):
        self.token = token
        self.exchange = exchange


    def to_heikin_ashi(self, df):
        """Mathematically accurate Heikin-Ashi calculation"""
        if df.empty: return df
        
        ha_df = df.copy()
        
        # 1. HA Close is always (Open + High + Low + Close) / 4
        ha_df['close'] = (df['open'] + df['high'] + df['low'] + df['close']) / 4
        
        # 2. HA Open must be recursive. Start with the first standard open.
        # We use .values for speed in the loop
        ha_opens = np.zeros(len(df))
        ha_closes = ha_df['close'].values
        standard_opens = df['open'].values
        standard_closes = df['close'].values
        
        # First HA Open is the average of the first standard candle's open and close
        ha_opens[0] = (standard_opens[0] + standard_closes[0]) / 2
        
        for i in range(1, len(df)):
            ha_opens[i] = (ha_opens[i-1] + ha_closes[i-1]) / 2
            
        ha_df['open'] = ha_opens
        
        # 3. HA High = Max(High, HA_Open, HA_Close)
        ha_df['high'] = ha_df[['high', 'open', 'close']].max(axis=1)
        
        # 4. HA Low = Min(Low, HA_Open, HA_Close)
        ha_df['low'] = ha_df[['low', 'open', 'close']].min(axis=1)
        
        return ha_df
    

    def get_history(self, timeframe='5', days=5, strategy_obj=None, candle_type='normal'):
        """
        Fetches historical data and calculates SMA 50/200 crossover + customizable indicators.
        """
        end_time = datetime.datetime.now()
        # Buffer: Indicator stability needs history
        buffer_days = days + 400
        start_time = end_time - datetime.timedelta(days=buffer_days)
            
        try:
            shoonya_service.ensure_session(
                getattr(shoonya_service, "session_token", None)
            )

            ret = None
            max_retries = 3

            for attempt in range(max_retries):
                try:
                    if timeframe == 'D':
                        ret = shoonya_service.api.get_daily_price_series(
                            exchange=self.exchange,
                            tradingsymbol='Nifty 50',
                            startdate=start_time.timestamp(),
                            enddate=end_time.timestamp()
                        )
                    else:
                        ret = shoonya_service.api.get_time_price_series(
                            exchange=self.exchange,
                            token=self.token,
                            starttime=int(start_time.timestamp()),
                            endtime=int(end_time.timestamp()),
                            interval=int(timeframe)
                        )
                    if ret: break
                except Exception as api_err:
                    logger.warning(f"API attempt {attempt+1} failed: {api_err}")
                time.sleep(1)

            if ret is None:
                raise RuntimeError("Shoonya API returned None")

            if not isinstance(ret, list):
                raise RuntimeError("Invalid Shoonya response")

            if len(ret) == 0:
                return pd.DataFrame()

            if isinstance(ret[0], str):
                ret = [json.loads(r) for r in ret]

            df = pd.DataFrame(ret)
            df = df.iloc[::-1].reset_index(drop=True)

            mapping = {
                'into': 'open', 'ss_o': 'open', 'o': 'open',
                'inth': 'high', 'ss_h': 'high', 'h': 'high',
                'intl': 'low',  'ss_l': 'low',  'l': 'low',
                'intc': 'close','ss_c': 'close', 'c': 'close',
                'time': 'time', 'ss_t': 'time', 'trandate': 'time'
            }
            # 1. Map and CLEAN types (Fixes the TypeError)
            df.rename(columns={k: v for k, v in mapping.items() if k in df.columns}, inplace=True)
            for col in ['open', 'high', 'low', 'close']:
                df[col] = pd.to_numeric(df[col], errors='coerce').astype(float) # Forced float cast

            if candle_type == 'heikin_ashi':
                df = self.to_heikin_ashi(df)
        
            # 2. Get Periods from Strategy or Defaults
            ema_p = getattr(strategy_obj, 'ema_period', 50)
            sma_p = getattr(strategy_obj, 'sma_period', 200)
            rsi_p = getattr(strategy_obj, 'rsi_period', 14)

            # 3. Dynamic Indicators (Using the names your chart expects)
            df['ema50'] = df['close'].ewm(span=ema_p, adjust=False).mean()
            df['ema21'] = df['close'].ewm(span=21, adjust=False).mean()
            df['sma20'] = df['close'].rolling(window=20).mean()
            df['sma50'] = df['close'].rolling(window=50).mean()
            df['sma200'] = df['close'].rolling(window=sma_p).mean()
            
            # RSI Calculation
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=rsi_p).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=rsi_p).mean()
            df['rsi14'] = 100 - (100 / (1 + (gain / loss)))

            # 4. Strategy Logic: Recorded Conditions
            df['signal'] = None
            for i in range(1, len(df)):
                # Verify parameters exist for the current row
                if pd.isna(df['sma200'][i]) or pd.isna(df['sma50'][i]):
                    continue
                    
                # Strategy Logic using model parameters
                bullish_filter = (df['close'][i] > df['sma200'][i]) and (df['sma50'][i] > df['sma200'][i])
                ema_cross_up = (df['ema21'][i] > df['sma50'][i]) and (df['ema21'][i-1] <= df['sma50'][i-1])
                
                if bullish_filter and ema_cross_up:
                    df.at[i, 'signal'] = 'BUY'
            return df.tail(days + 50).copy().reset_index(drop=True)
        except Exception as e:
            logger.exception("Engine Failure")
            return None
        

    def calculate_advanced_signals(df, strategy_obj=None):
        """
        Implements testing logic for EMA 21, SMA 20, SMA 50, and SMA 200.
        """
        # 1. Calculate Indicators
        df['ema21'] = df['close'].ewm(span=21, adjust=False).mean()
        df['sma20'] = df['close'].rolling(window=20).mean()
        df['sma50'] = df['close'].rolling(window=50).mean()
        df['sma200'] = df['close'].rolling(window=200).mean()
        
        # 2. Strategy Logic: The "Triple Filter"
        df['signal'] = None
        
        for i in range(1, len(df)):
            # Ensure we have enough data for the SMA 200
            if pd.isna(df['sma200'][i]):
                continue
                
            # BUY LOGIC: 
            # 1. Price is above SMA 200 (Long-term Bullish)
            # 2. EMA 21 crosses above SMA 20
            # 3. SMA 20 is above SMA 50
            bullish_filter = (df['close'][i] > df['sma200'][i]) and (df['sma20'][i] > df['sma50'][i])
            ema_cross_up = (df['ema21'][i] > df['sma20'][i]) and (df['ema21'][i-1] <= df['sma20'][i-1])
            
            if bullish_filter and ema_cross_up:
                df.at[i, 'signal'] = 'BUY'
                
            # SELL LOGIC (Exit):
            # Exit when EMA 21 crosses below SMA 20
            ema_cross_down = (df['ema21'][i] < df['sma20'][i]) and (df['ema21'][i-1] >= df['sma20'][i-1])
            if ema_cross_down:
                df.at[i, 'signal'] = 'SELL'
                
        return df