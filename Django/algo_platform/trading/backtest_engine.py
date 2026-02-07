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

    def get_history(self, timeframe='D', days=180, strategy_obj=None):
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

            # 2. Get Periods from Strategy or Defaults
            ema_p = getattr(strategy_obj, 'ema_period', 50)
            sma_p = getattr(strategy_obj, 'sma_period', 200)
            rsi_p = getattr(strategy_obj, 'rsi_period', 14)

            # 3. Dynamic Indicators (Using the names your chart expects)
            df['ema50'] = df['close'].ewm(span=ema_p, adjust=False).mean()
            df['sma200'] = df['close'].rolling(window=sma_p).mean()
            
            # RSI Calculation
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=rsi_p).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=rsi_p).mean()
            df['rsi14'] = 100 - (100 / (1 + (gain / loss)))

            # 4. Strategy Logic: Recorded Conditions
            df['signal'] = None
            for i in range(1, len(df)):
                if pd.isna(df['ema50'][i]) or pd.isna(df['sma200'][i]) or pd.isna(df['rsi14'][i]):
                    continue
                
                # LONG ENTRY: EMA crosses above SMA AND RSI < 30
                cross_above = df['ema50'][i] > df['sma200'][i] and df['ema50'][i-1] <= df['sma200'][i-1]
                if cross_above and df['rsi14'][i] < 30:
                    df.at[i, 'signal'] = 'BUY'
                
                # EXIT/SHORT: EMA crosses below SMA
                cross_below = df['ema50'][i] < df['sma200'][i] and df['ema50'][i-1] >= df['sma200'][i-1]
                if cross_below:
                    df.at[i, 'signal'] = 'SELL'

            return df.tail(days + 50).copy().reset_index(drop=True)
        except Exception as e:
            logger.exception("Engine Failure")
            return None