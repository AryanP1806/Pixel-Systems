from celery import shared_task
from .models import Strategy, Order
from .engine.strategy import StrategyEngine
from .engine.execution import ExecutionHandler

@shared_task
def run_trading_bot():
    """Main background loop for the algo"""
    active_strategies = Strategy.objects.filter(is_active=True)
    if not active_strategies.exists():
        return "No active strategies."

    engine = StrategyEngine()
    executor = ExecutionHandler(engine.api)
    
    for strat in active_strategies:
        # Fetching data using Shoonya token from Model
        df = engine.fetch_data(strat.exchange, strat.token)
        
        if df is not None:
            df = engine.calculate_indicators(df, strat.ema_period, strat.rsi_period)
            signal = engine.check_signals(df)
            
            if signal in ["BUY", "SELL"]:
                side = 'B' if signal == "BUY" else 'S'
                order_id = executor.place_shoonya_order(strat.symbol, strat.exchange, 1, side)
                
                if order_id:
                    Order.objects.create(
                        strategy=strat,
                        noren_order_no=order_id,
                        side=side,
                        status='COMPLETE',
                        price=df.iloc[-1]['close'],
                        qty=1
                    )
    return f"Processed {active_strategies.count()} strategies."