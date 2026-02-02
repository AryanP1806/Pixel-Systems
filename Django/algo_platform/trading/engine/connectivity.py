import os
import logging
from NorenRestApiPy.NorenApi import NorenApi

logger = logging.getLogger(__name__)


class ShoonyaSession:
    """
    Singleton session manager
    """
    _api = None


    @classmethod
    def login(cls, totp):
        """
        Login once and store API instance
        """

        api = NorenApi(
            host='https://api.shoonya.com/NorenWClientTP/',
            websocket='wss://api.shoonya.com/NorenWSTP/'
        )

        try:
            ret = api.login(
                userid=os.getenv('SHOONYA_USER_ID'),
                password=os.getenv('SHOONYA_PASSWORD'),
                twoFA=totp,
                vendor_code=os.getenv('SHOONYA_VENDOR_CODE'),
                api_secret=os.getenv('SHOONYA_API_KEY'),
                imei=os.getenv('SHOONYA_IMEI')
            )

            if ret and ret.get("stat") == "Ok":
                cls._api = api
                return ret

            return None

        except Exception as e:
            logger.error(f"Login failed: {e}")
            return None


    @classmethod
    def get_api(cls):
        """
        Return active API session
        """
        return cls._api


    @classmethod
    def logout(cls):
        cls._api = None
