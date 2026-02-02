import time
from datetime import datetime, timedelta
import pandas as pd
import pandas_ta as ta

class StrategyEngine:
    def __init__(self, api_instance):
        """
        Must be initialized with a ShoonyaClient that already has 
        an active session (via login or set_session_details).
        """
        self.api = api_instance

    def fetch_historical_data(self, exchange, token, days=30):
        """Fetches historical 1-minute data."""
        all_candles = []
        end_time = datetime.now()
        start_time = end_time - timedelta(days=days)

        # Shoonya API limits chunks, we fetch in 30-day blocks
        current_end = end_time
        while current_end > start_time:
            chunk_start = current_end - timedelta(days=30)
            if chunk_start < start_time:
                chunk_start = start_time

            ret = self.api.get_time_price_series(
                exchange=exchange,
                token=token,
                starttime=int(chunk_start.timestamp()),
                endtime=int(current_end.timestamp()),
                interval=1
            )
            
            if isinstance(ret, list):
                all_candles.extend(ret)
            elif isinstance(ret, dict) and ret.get('stat') != 'Ok':
                # Handle session errors here if needed
                print(f"Data Fetch Error: {ret.get('emsg')}")
                break
            
            current_end = chunk_start
            time.sleep(0.2) # Avoid rate limits

        if not all_candles:
            return None

        df = pd.DataFrame(all_candles)
        # Sort by time ascending (Shoonya returns descending usually)
        df['sswevent'] = pd.to_datetime(df['sswevent'], dayfirst=True)
        df = df.sort_values('sswevent')
        
        # Standardize column names for the backtester
        # inth=High, intl=Low, intc=Close, into=Open
        df[['into', 'inth', 'intl', 'intc']] = df[['into', 'inth', 'intl', 'intc']].apply(pd.to_numeric)
        return df