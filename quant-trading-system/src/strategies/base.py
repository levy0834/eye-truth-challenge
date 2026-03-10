"""
策略基类
"""
from abc import ABC, abstractmethod
import pandas as pd
from typing import Dict, Any

class Strategy(ABC):
    """策略基类"""
    def __init__(self, params: Dict[str, Any] = None):
        self.params = params or {}

    @abstractmethod
    def generate_signal(self, row: pd.Series) -> str:
        """
        根据当前行数据生成信号
        Args:
            row: DataFrame的一行，包含所有指标
        Returns:
            'buy', 'sell', 或 'hold'
        """
        pass

    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """可选：预计算指标"""
        return df
