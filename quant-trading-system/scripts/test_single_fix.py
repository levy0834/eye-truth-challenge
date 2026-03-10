#!/usr/bin/env python3
"""
小范围测试验证：修复后win_rate应恢复正常
测试：1支股票 × 1个策略
"""
import sys
from pathlib import Path
import pandas as pd
from datetime import datetime

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from src.strategies import STRATEGY_REGISTRY
from src.backtest.engine import Backtester
from src.utils.logger import setup_logger
import yaml

logger = setup_logger(__name__)

def load_config():
    config_file = ROOT / "config/settings.yaml"
    with open(config_file, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def find_data_file(symbol: str) -> Path:
    """查找数据文件"""
    raw_dir = ROOT / "data" / "raw" / "a_share"
    # 文件名格式: 300308_SZ.csv
    safe_name = symbol.replace('.', '_')
    candidate = raw_dir / f"{safe_name}.csv"
    if candidate.exists():
        return candidate
    
    # 模糊匹配
    for file in raw_dir.glob("*.csv"):
        if symbol.replace('.', '_') in file.name:
            return file
    return None

def split_train_test(df: pd.DataFrame):
    train = df[df['date'] <= '2021-12-31'].copy()
    test = df[df['date'] >= '2022-01-01'].copy()
    return train, test

def main():
    print("=" * 60)
    print("🔬 小范围测试验证 - 修复后胜率统计")
    print("=" * 60)
    
    # 配置
    config = load_config()
    symbol = '300308.SZ'  # 之前表现最佳的股票之一
    strategy_name = 'MACrossStrategy'
    strategy = STRATEGY_REGISTRY['ma_cross']()
    
    print(f"\n📈 测试标的: {symbol}")
    print(f"🎯 测试策略: {strategy_name}")
    
    # 加载数据
    data_file = find_data_file(symbol)
    if not data_file:
        print(f"❌ 未找到 {symbol} 数据文件")
        return
    
    print(f"📁 数据文件: {data_file.name}")
    df = pd.read_csv(data_file, parse_dates=['date'])
    
    # 检查数据范围
    print(f"📊 数据范围: {df['date'].min().date()} ~ {df['date'].max().date()}")
    print(f"   总交易日: {len(df)}")
    
    # 划分训练/测试
    train_df, test_df = split_train_test(df)
    print(f"   训练期: {len(train_df)} 天 ({train_df['date'].min().date()} ~ {train_df['date'].max().date()})")
    print(f"   测试期: {len(test_df)} 天 ({test_df['date'].min().date()} ~ {test_df['date'].max().date()})")
    
    if len(test_df) < 100:
        print("❌ 测试期数据不足100天，跳过")
        return
    
    # 测试集回测
    print(f"\n🏃 运行测试集回测...")
    bt = Backtester(test_df, strategy, config)
    bt.run()
    metrics = bt.evaluate()
    
    # 获取交易记录
    trades = bt.get_trades()
    print(f"\n📊 回测结果:")
    print(f"   总收益: {metrics.get('total_return_pct', 0):.2f}%")
    print(f"   最大回撤: {metrics.get('max_drawdown_pct', 0):.2f}%")
    print(f"   Sharpe: {metrics.get('sharpe_ratio', 0):.2f}")
    print(f"   交易次数: {metrics.get('total_trades', 0)}")
    print(f"   胜率: {metrics.get('win_rate_pct', 0):.2f}%")
    
    # 详细检查交易盈亏
    if not trades.empty and 'pnl' in trades.columns:
        print(f"\n🔍 交易盈亏分析:")
        print(f"   总交易数: {len(trades)}")
        print(f"   买入数: {(trades['side'] == 'buy').sum()}")
        print(f"   卖出数: {(trades['side'] == 'sell').sum()}")
        
        pnl_series = trades['pnl']
        print(f"   盈亏均值: {pnl_series.mean():.2f}")
        print(f"   盈亏标准差: {pnl_series.std():.2f}")
        print(f"   最大单笔盈利: {pnl_series.max():.2f}")
        print(f"   最大单笔亏损: {pnl_series.min():.2f}")
        print(f"   正盈亏笔数: {(pnl_series > 0).sum()} ({(pnl_series > 0).mean()*100:.1f}%)")
        print(f"   零盈亏笔数: {(pnl_series == 0).sum()} ({(pnl_series == 0).mean()*100:.1f}%)")
        print(f"   负盈亏笔数: {(pnl_series < 0).sum()} ({(pnl_series < 0).mean()*100:.1f}%)")
        
        # 显示前5笔卖出交易
        sell_trades = trades[trades['side'] == 'sell'].head(5)
        if not sell_trades.empty:
            print(f"\n📝 前5笔卖出交易示例:")
            for idx, row in sell_trades.iterrows():
                print(f"   {row['timestamp'].date() if pd.notnull(row['timestamp']) else 'N/A'}: "
                      f"卖出 {row['quantity']}股 @ {row['price']:.2f}, "
                      f"盈亏: {row['pnl']:.2f} (佣金: {row['commission']:.2f})")
    
    # 结论
    print("\n" + "=" * 60)
    win_rate = metrics.get('win_rate_pct', 0)
    if win_rate > 0:
        print(f"✅ 验证通过！胜率 restored: {win_rate:.2f}%")
        print("   之前的0%问题已修复")
    else:
        print(f"❌ 胜率仍为0，需要进一步排查")
        print("   可能原因：1) 测试期无有效卖出 2) 其他逻辑bug")
        
        # 调试信息
        if not trades.empty:
            print(f"\n💡 调试提示:")
            print(f"   - 测试期总天数: {len(test_df)}")
            print(f"   - 信号总数: {len(bt.daily_signals)}")
            print(f"   - 'buy'信号数: {sum(s['signal']=='buy' for s in bt.daily_signals)}")
            print(f"   - 'sell'信号数: {sum(s['signal']=='sell' for s in bt.daily_signals)}")
    
    print("=" * 60)

if __name__ == "__main__":
    main()
