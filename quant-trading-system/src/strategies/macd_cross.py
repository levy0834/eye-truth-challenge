"""
MACD交叉策略
"""
import pandas as pd
from .base import Strategy

class MACDCrossStrategy(Strategy):
    def __init__(self, fast: int = 12, slow: int = 26, signal: int = 9):
        super().__init__(params={'fast': fast, 'slow': slow, 'signal': signal})

    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        p = self.params
        df = df.copy()
        exp1 = df['close'].ewm(span=p['fast'], adjust=False).mean()
        exp2 = df['close'].ewm(span=p['slow'], adjust=False).mean()
        df['macd'] = exp1 - exp2
        df['macd_signal'] = df['macd'].ewm(span=p['signal'], adjust=False).mean()
        return df

    def generate_signal(self, row: pd.Series) -> str:
        if pd.isna(row.get('macd')) or pd.isna(row.get('macd_signal')):
            return 'hold'
        if row['macd'] > row['macd_signal']:
            return 'buy'
        elif row['macd'] < row['macd_signal']:
            return 'sell'
        return 'hold'
