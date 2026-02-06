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


    def get_history(self, timeframe='D', days=180):
        """
        Fetches historical data and calculates SMA 50/200 crossover.
        """

        end_time = datetime.datetime.now()

        # Buffer: SMA 200 needs 200 bars of history BEFORE the chart starts.
        buffer_days = days + 400

        start_time = end_time - datetime.timedelta(days=buffer_days)


        try:

            # ✅ ENSURE SESSION BEFORE ANY API CALL
            shoonya_service.ensure_session(
                getattr(shoonya_service, "session_token", None)
            )


            # ---------- FIX: API CALL WITH RETRY ----------

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


                    if ret:
                        break


                except Exception as api_err:

                    logger.warning(
                        f"API attempt {attempt+1} failed: {api_err}"
                    )


                time.sleep(1)   # small backoff


            # ---------------------------------------------


            print("API RESPONSE TYPE:", type(ret))
            print("API RESPONSE RAW:", ret)



            if ret is None:

                logger.error(
                    "Shoonya API returned None (session/timeout/rate-limit)"
                )

                raise RuntimeError("Shoonya API returned None")



            if not isinstance(ret, list):

                logger.error(f"Invalid API response: {ret}")

                raise RuntimeError("Invalid Shoonya response")



            if len(ret) == 0:

                logger.warning("Shoonya API returned empty list")

                return pd.DataFrame()


            # ---------- FIX: Parse JSON strings if needed ----------

            if isinstance(ret[0], str):

                try:
                    ret = [json.loads(r) for r in ret]

                except Exception as e:

                    logger.error(f"Failed to parse JSON strings: {e}")

                    raise RuntimeError("Invalid Shoonya JSON format")


            # -------------------------------------------------------


            df = pd.DataFrame(ret)


            # Reversing to chronological order (Left-to-Right)
            df = df.iloc[::-1].reset_index(drop=True)



            # Map varied keys (Daily: ss_c vs Intraday: intc)
            mapping = {

                'into': 'open', 'ss_o': 'open',
                'inth': 'high', 'ss_h': 'high',
                'intl': 'low',  'ss_l': 'low',
                'intc': 'close','ss_c': 'close',

                'time': 'time', 'ss_t': 'time'
            }


            df.rename(
                columns={k: v for k, v in mapping.items() if k in df.columns},
                inplace=True
            )



            # Ensure numeric
            for col in ['open', 'high', 'low', 'close']:

                df[col] = pd.to_numeric(df[col], errors='coerce')



            # --- Indicators ---

            df['sma50']  = df['close'].rolling(window=50).mean()
            df['sma200'] = df['close'].rolling(window=200).mean()



            # --- Strategy Logic: Golden Cross ---

            df['signal'] = None


            for i in range(1, len(df)):

                if pd.isna(df['sma50'][i]) or pd.isna(df['sma200'][i]):
                    continue


                if (
                    df['sma50'][i] > df['sma200'][i] and
                    df['sma50'][i-1] <= df['sma200'][i-1]
                ):

                    df.at[i, 'signal'] = 'BUY'


                elif (
                    df['sma50'][i] < df['sma200'][i] and
                    df['sma50'][i-1] >= df['sma200'][i-1]
                ):

                    df.at[i, 'signal'] = 'SELL'



            # ✅ FIX: return days + 50 for indicator stability
            return df.tail(days + 50)



        except Exception as e:

            logger.exception("Engine Failure")
            return None
