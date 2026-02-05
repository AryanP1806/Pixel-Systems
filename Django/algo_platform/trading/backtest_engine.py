import pandas as pd
import datetime
import numpy as np
import logging
from .api_service import shoonya_service

logger = logging.getLogger(__name__)

class Backtester:
    def __init__(self, token='26000', exchange='NSE'):
        self.token = token
        self.exchange = exchange

    def get_history(self, timeframe='D', days=365):
        """
        Fetches history and normalizes data across different Shoonya endpoints.
        Handles the key differences between Daily (ss_c) and Intraday (intc).
        """
        end_time = datetime.datetime.now()
        # Fetch extra days to ensure SMA 200 is calculated for the visible start date
        buffer_days = days + 350 
        start_time = end_time - datetime.timedelta(days=buffer_days)
        
        try:
            if timeframe == 'D':
                # Daily API for Index usually requires 'Nifty 50' string
                # Note: Shoonya is picky about the symbol name for indices in daily calls
                ret = shoonya_service.api.get_daily_price_series(
                    exchange=self.exchange,
                    tradingsymbol='Nifty 50', 
                    startdate=start_time.timestamp(),
                    enddate=end_time.timestamp()
                )
            else:
                # Intraday API uses numeric token
                ret = shoonya_service.api.get_time_price_series(
                    exchange=self.exchange, 
                    token=self.token, 
                    starttime=int(start_time.timestamp()), 
                    endtime=int(end_time.timestamp()),
                    interval=int(timeframe)
                )

            if not ret or not isinstance(ret, list):
                logger.error(f"Broker error or empty data: {ret}")
                return None

            df = pd.DataFrame(ret)
            # Shoonya returns data newest-first; reverse for technical analysis
            df = df.iloc[::-1].reset_index(drop=True)

            # --- KEY MAPPING ---
            # Intraday: intc, into, inth, intl, time
            # Daily: ss_c, ss_o, ss_h, ss_l, ss_t
            mapping = {
                'into': 'open', 'ss_o': 'open',
                'inth': 'high', 'ss_h': 'high',
                'intl': 'low', 'ss_l': 'low',
                'intc': 'close', 'ss_c': 'close',
                'time': 'time', 'ss_t': 'time'
            }
            df.rename(columns={k: v for k, v in mapping.items() if k in df.columns}, inplace=True)

            # Force numeric for indicator calculations
            for col in ['open', 'high', 'low', 'close']:
                df[col] = pd.to_numeric(df[col], errors='coerce')

            # --- SMA Calculations ---
            # These will automatically vary based on the interval (Daily SMA vs 15m SMA)
            df['sma50'] = df['close'].rolling(window=50).mean()
            df['sma200'] = df['close'].rolling(window=200).mean()

            # --- STRATEGY LOGIC ---
            # Golden Cross: SMA 50 crosses ABOVE SMA 200
            signals = []
            for i in range(len(df)):
                if i < 1 or pd.isna(df['sma50'][i]) or pd.isna(df['sma200'][i]):
                    signals.append(None)
                    continue
                
                # Buy: Current 50 > 200 AND Previous 50 <= 200
                if df['sma50'][i] > df['sma200'][i] and df['sma50'][i-1] <= df['sma200'][i-1]:
                    signals.append('BUY')
                # Sell: Current 50 < 200 AND Previous 50 >= 200
                elif df['sma50'][i] < df['sma200'][i] and df['sma50'][i-1] >= df['sma200'][i-1]:
                    signals.append('SELL')
                else:
                    signals.append(None)
            
            df['signal'] = signals

            # Return only the requested number of days (the 'tail')
            return df.tail(days)

        except Exception as e:
            logger.exception("Backtest engine critical failure:")
            return None