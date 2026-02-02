import logging

logger = logging.getLogger(__name__)

class ExecutionHandler:
    def __init__(self, api_instance):
        self.api = api_instance

    def place_shoonya_order(self, symbol, exchange, qty, side):
        """
        side: 'B' for Buy, 'S' for Sell
        product_type: 'I' for MIS (Intraday), 'M' for NRML
        """
        try:
            order = self.api.place_order(
                buy_or_sell=side,
                product_type='I', # MIS for Intraday
                exchange=exchange,
                tradingsymbol=symbol,
                quantity=qty,
                discloseqty=0,
                price_type='MKT', # Market order to ensure execution
                price=0,
                trigger_price=0,
                retention='DAY',
                remarks='AlgoOrder'
            )
            
            if order and order.get('stat') == 'Ok':
                return order['norenordno']
            else:
                logger.error(f"Order Failed: {order.get('emsg')}")
                return None
        except Exception as e:
            logger.error(f"Execution Error: {e}")
            return None