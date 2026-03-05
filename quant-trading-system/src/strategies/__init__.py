"""策略包"""
from .base import Strategy
from .ma_cross import MACrossStrategy
from .macd_cross import MACDCrossStrategy
from .rsi_extreme import RSIStrategy
from .bollinger import BollingerStrategy
from .confluence import TAConfluenceStrategy

STRATEGY_REGISTRY = {
    'ma_cross': MACrossStrategy,
    'macd_cross': MACDCrossStrategy,
    'rsi_extreme': RSIStrategy,
    'bollinger': BollingerStrategy,
    'confluence': TAConfluenceStrategy
}

__all__ = [
    'Strategy', 'MACrossStrategy', 'MACDCrossStrategy',
    'RSIStrategy', 'BollingerStrategy', 'TAConfluenceStrategy',
    'STRATEGY_REGISTRY'
]
