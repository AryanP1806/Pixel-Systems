import os
import logging
from .api_helper import NorenApiPy

logger = logging.getLogger(__name__)

class ShoonyaService:
    def __init__(self):
        self.api = NorenApiPy()
        self.user_id = os.getenv('SHOONYA_USER_ID')
        self.password = os.getenv('SHOONYA_PASSWORD')
        self.api_key = os.getenv('SHOONYA_API_KEY')
        self.imei = os.getenv('SHOONYA_IMEI')
        self.vendor_code = os.getenv('SHOONYA_VENDOR_CODE')

    def login_with_totp(self, totp):
        try:
            res = self.api.login(
                userid=self.user_id,
                password=self.password,
                twoFA=totp,
                vendor_code=self.vendor_code,
                api_secret=self.api_key,
                imei=self.imei
            )
            return res
        except Exception as e:
            logger.error(f"Login Exception: {e}")
            return None


    def ensure_session(self, session_token):

        try:
            # If SDK has no session OR token is dead
            if not getattr(self.api, '_NorenApi__susertoken', None):

                logger.warning("Shoonya session missing. Re-login required.")

                raise RuntimeError("Session expired")

        except Exception as e:

            logger.error(f"Session invalid: {e}")


    def get_nifty_price(self, token_id, session_token=None):
        """
        Fetches LTP. 
        Note: We explicitly check if we are 'logged in' to the SDK object.
        """
        session_token = getattr(shoonya_service, "session_token", None)

        try:
            # If the object lost session, re-inject the token from Django session
            # if session_token and not getattr(self.api, '_NorenApi__susertoken', None):
            #     self.api.set_session(self.user_id, self.password, session_token)
            self.ensure_session(session_token)
            # Get Quote
            quote = self.api.get_quotes(exchange='NSE', token=token_id)
            
            if quote and quote.get('stat') == 'Ok':
                return {
                    'lp': quote.get('lp'),
                    'pc': quote.get('pc'),
                    'h': quote.get('h'),
                    'l': quote.get('l'),
                }
            else:
                logger.warning(f"Quote Stat Not Ok: {quote}")
                return None
        except Exception as e:
            # This catches the 'attribute' error and logs it without crashing the page
            logger.error(f"Error fetching Nifty Price: {e}")
            return None

shoonya_service = ShoonyaService()