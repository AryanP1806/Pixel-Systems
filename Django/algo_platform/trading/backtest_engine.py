import json
import pandas as pd
import datetime
import numpy as np
import logging
import time

from .api_service import shoonya_service

logger = logging.getLogger(__name__)

class Backtester:
    def __init__(self, token='26000', exchange='NSE'):
        self.token = str(token).strip()
        self.exchange = exchange.strip().upper()

    def evaluate_signals(self, df, strategy_obj):
        if not strategy_obj or not strategy_obj.logic_config:
            return df

        logic = strategy_obj.logic_config
        df['signal'] = None

        # 1. Calculate all dynamic indicators first
        for cond in logic.get('long', []):
            self._add_indicator(df, cond['ind1'], int(cond['val1']))
            if cond['ind2'] != 'number':
                self._add_indicator(df, cond['ind2'], int(cond['val2']))

        # 2. Dynamic Evaluation
        for i in range(1, len(df)):
            conditions_met = []
            for cond in logic.get('long', []):
                col1 = f"{cond['ind1']}_{cond['val1']}"
                curr_val = df[col1][i]
                prev_val = df[col1][i-1]

                # Handle Static Number vs Dynamic Indicator
                if cond['ind2'] == 'number':
                    target_val = float(cond['val2'])
                    prev_target = target_val
                else:
                    col2 = f"{cond['ind2']}_{cond['val2']}"
                    target_val = df[col2][i]
                    prev_target = df[col2][i-1]

                # Apply logical operators
                if cond['op'] == 'crosses_above':
                    conditions_met.append(curr_val > target_val and prev_val <= prev_target)
                elif cond['op'] == 'greater_than':
                    conditions_met.append(curr_val > target_val)
                elif cond['op'] == 'less_than':
                    conditions_met.append(curr_val < target_val)

            if conditions_met and all(conditions_met):
                df.at[i, 'signal'] = 'BUY'
            else:
                df.at[i, 'signal'] = 'SELL' 

        return df
    def _add_indicator(self, df, name, period):
        col_name = f"{name}_{period}"
        if col_name in df.columns or name == 'number': return
        
        try:
            if name == 'ema':
                df[col_name] = df['close'].ewm(span=period, adjust=False).mean()
            elif name == 'sma':
                df[col_name] = df['close'].rolling(window=period).mean()
            elif name == 'rsi':
                delta = df['close'].diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
                df[col_name] = 100 - (100 / (1 + (gain / loss.replace(0, np.nan))))
        except Exception as e:
            logger.error(f"Error calculating {col_name}: {e}")


    def to_heikin_ashi(self, df):
        if df.empty: return df
        ha_df = df.copy()
        ha_df['close'] = (df['open'] + df['high'] + df['low'] + df['close']) / 4
        ha_opens = np.zeros(len(df))
        ha_opens[0] = (df['open'].values[0] + df['close'].values[0]) / 2
        for i in range(1, len(df)):
            ha_opens[i] = (ha_opens[i-1] + ha_df['close'].values[i-1]) / 2
        ha_df['open'] = ha_opens
        ha_df['high'] = ha_df[['high', 'open', 'close']].max(axis=1)
        ha_df['low'] = ha_df[['low', 'open', 'close']].min(axis=1)
        return ha_df

    def get_history(self, timeframe='5', days=5, strategy_obj=None, candle_type='normal'):
        end_time = datetime.datetime.now()
        buffer_days = days  # Reduced buffer for speed
        start_time = end_time - datetime.timedelta(days=buffer_days)
            
        try:
            shoonya_service.ensure_session(getattr(shoonya_service, "session_token", None))
            ret = None
            for attempt in range(3):
                try:
                    if timeframe == 'D':
                        ret = shoonya_service.api.get_daily_price_series(exchange=self.exchange, tradingsymbol='Nifty 50', startdate=start_time.timestamp(), enddate=end_time.timestamp())
                    else:
                        ret = shoonya_service.api.get_time_price_series(exchange=self.exchange, token=self.token, starttime=int(start_time.timestamp()), endtime=int(end_time.timestamp()), interval=int(timeframe))
                    if ret: break
                except: time.sleep(1)

            if not ret or not isinstance(ret, list):
                logger.error(f"Invalid API response: {ret}")
                return pd.DataFrame()

            # If response items are JSON strings, parse them
            if isinstance(ret[0], str):
                try:
                    ret = [json.loads(item) for item in ret]
                except Exception as e:
                    logger.error(f"JSON parse error: {e}")
                    return pd.DataFrame()

            # Now validate structure AFTER parsing
            if not isinstance(ret[0], dict):
                logger.error(f"Unexpected API structure: {ret}")
                return pd.DataFrame()

            df = pd.DataFrame(ret)
            df = df.iloc[::-1].reset_index(drop=True)
            # --------- NORMALIZE COLUMN NAMES SAFELY ---------
            df.columns = [str(c).lower() for c in df.columns]
            # Map possible variations
            column_map = {
                'into': 'open',
                'o': 'open',
                'inth': 'high',
                'h': 'high',
                'intl': 'low',
                'l': 'low',
                'intc': 'close',
                'c': 'close',
                'trandate': 'time',
                'date': 'time'
            }

            df.rename(columns=column_map, inplace=True)

            required_cols = ['open', 'high', 'low', 'close', 'time']

            missing = [col for col in required_cols if col not in df.columns]

            if missing:
                logger.error(f"Missing required columns: {missing}")
                return pd.DataFrame()

            for col in ['open', 'high', 'low', 'close']:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            if candle_type == 'heikin_ashi':
                df = self.to_heikin_ashi(df)

            # Apply Dynamic Strategy Logic
            df = self.evaluate_signals(df, strategy_obj)
            # -----IMPORTANT-------
            # Limit rows to keep frontend fast
            # if timeframe != 'D':
            #     MAX_CANDLES = 5000
            # else:
            #     MAX_CANDLES = 2000  # daily doesn’t need huge

            # if len(df) > MAX_CANDLES:
            #     df = df.tail(MAX_CANDLES)

            return df.copy().reset_index(drop=True)
            
        except Exception as e:
            logger.exception("Engine Failure")
            return None