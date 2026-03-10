"""
性能指标计算（独立函数，用于扩展）
"""
import numpy as np
import pandas as pd

def calculate_returns(portfolio_values: pd.Series) -> pd.Series:
    """计算收益率序列"""
    return portfolio_values.pct_change().fillna(0)

def calculate_max_drawdown(portfolio_values: pd.Series) -> float:
    """计算最大回撤（百分比）"""
    cummax = portfolio_values.cummax()
    drawdown = (portfolio_values - cummax) / cummax
    return drawdown.min() * 100

def calculate_sharpe_ratio(returns: pd.Series, risk_free_rate: float = 0.02, periods: int = 252) -> float:
    """计算夏普比率"""
    excess_returns = returns - risk_free_rate / periods
    if excess_returns.std() == 0:
        return 0
    return excess_returns.mean() / excess_returns.std() * np.sqrt(periods)

def calculate_sortino_ratio(returns: pd.Series, risk_free_rate: float = 0.02, periods: int = 252) -> float:
    """计算索提诺比率（仅 downside risk）"""
    excess_returns = returns - risk_free_rate / periods
    downside = excess_returns[excess_returns < 0]
    if len(downside) == 0 or downside.std() == 0:
        return 0
    return excess_returns.mean() / downside.std() * np.sqrt(periods)

def calculate_calmar_ratio(total_return: float, max_drawdown: float, years: float) -> float:
    """计算卡玛比率"""
    if max_drawdown == 0:
        return 0
    return (total_return / 100) / (abs(max_drawdown) / 100) / years
