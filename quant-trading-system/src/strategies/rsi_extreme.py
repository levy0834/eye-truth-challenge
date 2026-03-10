"""
RSI超买超卖策略
买入：RSI < 30（超卖）
卖出：RSI > 70（超买）
"""
import pandas as pd
from .base import Strategy

class RSIStrategy(Strategy):
    def __init__(self, period: int = 14, oversold: int = 30, overbought: int = 70):
        super().__init__(params={'period': period, 'oversold': oversold, 'overbought': overbought})

    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        p = self.params
        df = df.copy()
        delta = df['close'].diff()
        gain = delta.where(delta > 0, 0).rolling(p['period']).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(p['period']).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        return df

    def generate_signal(self, row: pd.Series) -> str:
        rsi = row.get('rsi')
        if pd.isna(rsi):
            return 'hold'
        if rsi < self.params['oversold']:
            return 'buy'
        elif rsi > self.params['overbought']:
            return 'sell'
        return 'hold'
