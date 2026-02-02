import pandas as pd
import pandas_ta as ta

class BacktestEngine:
    @staticmethod
    def to_heikin_ashi(df):
        """Converts standard OHLC to Heikin Ashi"""
        ha_df = df.copy()
        ha_df['close'] = (df['open'] + df['high'] + df['low'] + df['close']) / 4
        
        # Calculate HA Open (Midpoint of previous HA candle)
        for i in range(1, len(df)):
            ha_df.iloc[i, ha_df.columns.get_loc('open')] = (ha_df.iloc[i-1]['open'] + ha_df.iloc[i-1]['close']) / 2
            
        ha_df['high'] = ha_df[['high', 'open', 'close']].max(axis=1)
        ha_df['low'] = ha_df[['low', 'open', 'close']].min(axis=1)
        return ha_df

    def run(self, data, params):
        """
        data: pandas DataFrame
        params: dict containing indicator settings and colors
        """
        # Apply Heikin Ashi if selected
        if params.get('candle_type') == 'heikin_ashi':
            data = self.to_heikin_ashi(data)

        # Calculate Indicators
        data['ema'] = ta.ema(data['close'], length=params.get('ema_period', 20))
        data['rsi'] = ta.rsi(data['close'], length=params.get('rsi_period', 14))
        
        # Backtesting Loop (Simplified)
        results = {"trades": [], "final_balance": 100000}
        # ... logic to simulate buy/sell ...
        return data, results
    
    def apply_indicators(self, df, params):
        # 1. EMA with Customizable Color (Stored for Frontend)
        if params.get('use_ema'):
            df['ema'] = ta.ema(df['close'], length=params.get('ema_len'))
            
        # 2. RSI
        if params.get('use_rsi'):
            df['rsi'] = ta.rsi(df['close'], length=14)
            
        # 3. Heikin Ashi Logic
        if params.get('candle_type') == 'heikin_ashi':
            df['ha_close'] = (df['open'] + df['high'] + df['low'] + df['close']) / 4
            # Implementation of HA Open recursive logic...
            # Apply "Bright" colors logic: 
            # if ha_close > ha_open -> #00FF00 (Green) 
            # else -> #FF0000 (Red)
        return df
    
    def process_data(self, df, params):
        # 1. Convert Shoonya 'sswevent' to Unix Timestamp (Seconds)
        df['time'] = pd.to_datetime(df['sswevent'], dayfirst=True).astype('int64') // 10**9

        # 2. Calculate Heikin Ashi
        df['ha_close'] = (df['into'] + df['inth'] + df['intl'] + df['intc']) / 4
        df['ha_open'] = df['into'] 
        for i in range(1, len(df)):
            df.iloc[i, df.columns.get_loc('ha_open')] = (df.iloc[i-1]['ha_open'] + df.iloc[i-1]['ha_close']) / 2
        
        df['ha_high'] = df[['inth', 'ha_open', 'ha_close']].max(axis=1)
        df['ha_low'] = df[['intl', 'ha_open', 'ha_close']].min(axis=1)

        # 3. EMA Calculation
        ema_len = int(params.get('ema_len', 20))
        df['ema_line'] = ta.ema(df['ha_close'], length=ema_len)
        
        df = df.dropna()
        
        # 4. Map columns to final names expected by the chart
        # We return a list of dicts directly
        final_data = []
        for _, row in df.iterrows():
            final_data.append({
                "time": int(row['time']),
                "open": float(row['ha_open']),
                "high": float(row['ha_high']),
                "low": float(row['ha_low']),
                "close": float(row['ha_close']),
                "ema": float(row['ema_line'])
            })
        
        return final_data