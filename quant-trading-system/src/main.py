#!/usr/bin/env python3
"""
量化交易系统主入口
命令行接口：支持 fetch、backtest、list 命令
"""
import sys
import argparse
import yaml
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

# 导入模块
from src.data.fetchers import DataFetcher
from src.strategies import STRATEGY_REGISTRY
from src.backtest.engine import Backtester
from src.backtest.visualizer import plot_equity_curve, plot_drawdown
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

def load_config() -> Dict[str, Any]:
    config_path = Path("config/settings.yaml")
    if config_path.exists():
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    else:
        logger.warning("配置文件不存在，使用默认配置")
        return {
            'symbols': {'a_share': ['510300.SH']},
            'default_symbol': '510300.SH',
            'default_strategy': 'ma_cross'
        }

def cmd_fetch(args):
    """抓取数据命令"""
    config = load_config()
    fetcher = DataFetcher(config)

    # 确定要抓取的标的
    if args.symbol:
        symbols = [args.symbol]
    else:
        # 抓取所有配置的标的
        symbols = config.get('symbols', {}).get('a_share', []) + \
                  config.get('symbols', {}).get('us_etf', []) + \
                  config.get('symbols', {}).get('crypto', [])

    start_date = args.start or config.get('date_range', {}).get('start', '2015-01-01')
    end_date = args.end or config.get('date_range', {}).get('end', datetime.now().strftime('%Y-%m-%d'))

    logger.info(f"开始抓取 {len(symbols)} 个标的 ({start_date} ~ {end_date})")

    for symbol in symbols:
        df = fetcher.fetch(symbol, start_date, end_date)
        if df is not None:
            # 自动保存到 data/raw/ 按市场分类
            market = 'a_share' if symbol.endswith('.SH') or symbol.endswith('.SZ') else \
                     'crypto' if '/' in symbol else 'us_etf'
            out_dir = Path(f"data/raw/{market}")
            out_dir.mkdir(parents=True, exist_ok=True)
            safe_name = symbol.replace('/', '_').replace('.', '_')
            out_file = out_dir / f"{safe_name}.csv"
            df.to_csv(out_file, index=False, encoding='utf-8-sig')
            logger.info(f"已保存: {out_file} ({len(df)} 行)")
        else:
            logger.error(f"❌ {symbol} 抓取失败")

def cmd_backtest(args):
    """回测命令"""
    import pandas as pd  # 局部导入避免作用域问题
    config = load_config()
    symbol = args.symbol or config.get('default_symbol', '510300.SH')
    strategy_name = args.strategy or config.get('default_strategy', 'ma_cross')

    # 加载数据
    data_file = find_data_file(symbol)
    if not data_file:
        logger.error(f"未找到 {symbol} 的数据文件，请先运行 fetch")
        return

    logger.info(f"加载数据: {data_file}")
    df = pd.read_csv(data_file, parse_dates=['date'])

    # 选择策略
    if strategy_name not in STRATEGY_REGISTRY:
        logger.error(f"未知策略: {strategy_name}，可用: {list(STRATEGY_REGISTRY.keys())}")
        return
    strategy_cls = STRATEGY_REGISTRY[strategy_name]
    strategy = strategy_cls()  # TODO: 支持策略参数配置

    # 回测
    backtester = Backtester(df, strategy, config)
    results_df = backtester.run()

    # 输出结果
    metrics = backtester.evaluate()
    print("\n" + "="*60)
    print(f"回测结果: {symbol} - {strategy_name}")
    print("="*60)
    for k, v in metrics.items():
        if isinstance(v, float):
            print(f"{k:25s}: {v:,.2f}")
        else:
            print(f"{k:25s}: {v}")

    # 保存结果
    results_dir = Path("results") / symbol.replace('/', '_')
    results_dir.mkdir(parents=True, exist_ok=True)

    # 保存日度资产
    results_df.to_csv(results_dir / "portfolio_value.csv", encoding='utf-8-sig')

    # 保存交易记录
    trades_df = backtester.get_trades()
    if not trades_df.empty:
        trades_df.to_csv(results_dir / "trades.csv", index=False, encoding='utf-8-sig')

    # 保存指标JSON
    import json
    with open(results_dir / "metrics.json", 'w', encoding='utf-8') as f:
        json.dump(metrics, f, indent=2, ensure_ascii=False, default=str)

    # 生成图表
    plot_equity_curve(results_df, title=f"{symbol} - {strategy_name}", save_path=str(results_dir / "equity_curve.png"))
    plot_drawdown(results_df, save_path=str(results_dir / "drawdown.png"))

    print(f"\n✅ 结果已保存到: {results_dir}")

def cmd_list(args):
    """列出可用标的和策略"""
    config = load_config()
    print("\n可用标的:")
    for market, syms in config.get('symbols', {}).items():
        print(f"  {market}: {syms}")

    print("\n可用策略:")
    for name in STRATEGY_REGISTRY.keys():
        print(f"  - {name}")

def find_data_file(symbol: str) -> Path:
    """查找数据文件"""
    safe_name = symbol.replace('/', '_').replace('.', '_')
    # 在所有raw子目录中查找
    for market_dir in Path("data/raw").glob("*"):
        candidate = market_dir / f"{safe_name}.csv"
        if candidate.exists():
            return candidate
        # 兼容旧命名
        for file in market_dir.glob("*.csv"):
            if symbol in file.name:
                return file
    return None

def main():
    parser = argparse.ArgumentParser(description="量化交易系统")
    subparsers = parser.add_subparsers(dest='command', help='子命令')

    # fetch
    p_fetch = subparsers.add_parser('fetch', help='抓取历史数据')
    p_fetch.add_argument('--symbol', help='指定标的（否则抓取所有）')
    p_fetch.add_argument('--start', help='开始日期 YYYY-MM-DD')
    p_fetch.add_argument('--end', help='结束日期 YYYY-MM-DD')

    # backtest
    p_backtest = subparsers.add_parser('backtest', help='运行回测')
    p_backtest.add_argument('--symbol', help='标的代码')
    p_backtest.add_argument('--strategy', help='策略名称')

    # list
    subparsers.add_parser('list', help='列出可用标的和策略')

    args = parser.parse_args()

    if args.command == 'fetch':
        cmd_fetch(args)
    elif args.command == 'backtest':
        cmd_backtest(args)
    elif args.command == 'list':
        cmd_list(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
