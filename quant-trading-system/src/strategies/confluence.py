"""
TAV多因子共振策略
Trend + Momentum + Volume confluence
买入：三者同时满足
卖出：趋势破坏
"""
import pandas as pd
from .base import Strategy
from .ma_cross import MACrossStrategy
from .macd_cross import MACDCrossStrategy
from .rsi_extreme import RSIStrategy

class TAConfluenceStrategy(Strategy):
    def __init__(self):
        super().__init__(params={})
        self.ma_strategy = MACrossStrategy(fast=5, slow=20)
        self.macd_strategy = MACDCrossStrategy()
        self.rsi_strategy = RSIStrategy()

    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        df = self.ma_strategy.calculate_indicators(df)
        df = self.macd_strategy.calculate_indicators(df)
        df = self.rsi_strategy.calculate_indicators(df)
        # 成交量指标
        df['volume_ma5'] = df['volume'].rolling(5).mean()
        df['volume_ratio'] = df['volume'] / df['volume_ma5']
        return df

    def generate_signal(self, row: pd.Series) -> str:
        # 趋势：价格 > MA20 且 MA5 > MA20
        trend_ok = (
            not pd.isna(row.get('ma20')) and
            row['close'] > row['ma20'] and
            row.get('ma5', 0) > row['ma20']
        )

        # 动量：RSI 健康区间 (30-70) 且 MACD金叉
        momentum_ok = (
            not pd.isna(row.get('rsi')) and
            30 < row['rsi'] < 70 and
            not pd.isna(row.get('macd')) and
            not pd.isna(row.get('macd_signal')) and
            row['macd'] > row['macd_signal']
        )

        # 成交量放大（>1.5倍均量）
        volume_ok = row.get('volume_ratio', 1) > 1.5

        if trend_ok and momentum_ok and volume_ok:
            return 'buy'

        # 卖出：趋势破坏（价格跌破MA20）
        if trend_ok is False and row.get('signal') == 'sell':
            return 'sell'

        return 'hold'
