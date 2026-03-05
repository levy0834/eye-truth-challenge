"""
MA均线交叉策略
买入：MA5 上穿 MA20（金叉）
卖出：MA5 下穿 MA20（死叉）
"""
import pandas as pd
from .base import Strategy

class MACrossStrategy(Strategy):
    def __init__(self, fast: int = 5, slow: int = 20):
        super().__init__(params={'fast': fast, 'slow': slow})

    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        fast = self.params['fast']
        slow = self.params['slow']
        df = df.copy()
        df[f'ma{fast}'] = df['close'].rolling(fast).mean()
        df[f'ma{slow}'] = df['close'].rolling(slow).mean()
        return df

    def generate_signal(self, row: pd.Series) -> str:
        fast_col = f"ma{self.params['fast']}"
        slow_col = f"ma{self.params['slow']}"

        if pd.isna(row.get(fast_col)) or pd.isna(row.get(slow_col)):
            return 'hold'

        if row[fast_col] > row[slow_col]:
            return 'buy'
        elif row[fast_col] < row[slow_col]:
            return 'sell'
        return 'hold'
