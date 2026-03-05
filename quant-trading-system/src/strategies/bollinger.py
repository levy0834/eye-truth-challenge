"""
布林带突破策略
买入：价格跌破下轨（超卖反弹）
卖出：价格突破上轨（超买回落）
"""
import pandas as pd
from .base import Strategy

class BollingerStrategy(Strategy):
    def __init__(self, period: int = 20, std: float = 2.0):
        super().__init__(params={'period': period, 'std': std})

    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        p = self.params
        df = df.copy()
        df['bb_middle'] = df['close'].rolling(p['period']).mean()
        bb_std = df['close'].rolling(p['period']).std()
        df['bb_upper'] = df['bb_middle'] + p['std'] * bb_std
        df['bb_lower'] = df['bb_middle'] - p['std'] * bb_std
        return df

    def generate_signal(self, row: pd.Series) -> str:
        lower = row.get('bb_lower')
        upper = row.get('bb_upper')
        if pd.isna(lower) or pd.isna(upper):
            return 'hold'
        if row['close'] < lower:
            return 'buy'
        elif row['close'] > upper:
            return 'sell'
        return 'hold'
