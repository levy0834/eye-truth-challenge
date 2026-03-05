"""
可视化模块
"""
import matplotlib.pyplot as plt
import pandas as pd
from pathlib import Path

def plot_equity_curve(portfolio_df: pd.DataFrame, title: str = "Equity Curve", save_path: str = None):
    """绘制资金曲线"""
    plt.figure(figsize=(12, 6))
    plt.plot(portfolio_df.index, portfolio_df['total_assets'], label='Portfolio Value', linewidth=2)
    plt.fill_between(portfolio_df.index, portfolio_df['total_assets'], alpha=0.3)

    # 标记买入卖出点（如果有信号）
    if 'signal' in portfolio_df.columns:
        buy_signals = portfolio_df[portfolio_df['signal'] == 'buy']
        sell_signals = portfolio_df[portfolio_df['signal'] == 'sell']
        plt.scatter(buy_signals.index, buy_signals['total_assets'], color='green', marker='^', s=100, label='Buy', zorder=5)
        plt.scatter(sell_signals.index, sell_signals['total_assets'], color='red', marker='v', s=100, label='Sell', zorder=5)

    plt.title(title)
    plt.xlabel('Date')
    plt.ylabel('Portfolio Value (CNY/USD)')
    plt.grid(True, alpha=0.3)
    plt.legend()

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        plt.close()
        print(f"📈 图表已保存: {save_path}")
    else:
        plt.show()

def plot_drawdown(portfolio_df: pd.DataFrame, save_path: str = None):
    """绘制回撤图"""
    df = portfolio_df.copy()
    df['cummax'] = df['total_assets'].cummax()
    df['drawdown'] = (df['total_assets'] - df['cummax']) / df['cummax'] * 100

    plt.figure(figsize=(12, 4))
    plt.fill_between(df.index, df['drawdown'], 0, color='red', alpha=0.3)
    plt.plot(df.index, df['drawdown'], color='red', linewidth=1)
    plt.title('Drawdown (%)')
    plt.xlabel('Date')
    plt.ylabel('Drawdown %')
    plt.grid(True, alpha=0.3)
    plt.axhline(y=0, color='black', linewidth=0.5)

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        plt.close()
        print(f"📉 回撤图已保存: {save_path}")
    else:
        plt.show()
