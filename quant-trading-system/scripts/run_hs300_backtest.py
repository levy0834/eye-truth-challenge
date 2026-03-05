#!/usr/bin/env python3
"""
沪深300成分股批量回测脚本
支持：300支股票 × 5种策略 × 时间划分（训练/测试）
"""
import os
import sys
import time
import yaml
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

# 项目根目录
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from src.strategies import STRATEGY_REGISTRY
from src.backtest.engine import Backtester
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

def load_config() -> Dict[str, Any]:
    config_path = ROOT / "config" / "settings.yaml"
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def load_hs300_components() -> List[str]:
    """加载沪深300成分股列表"""
    file = ROOT / "data" / "hs300_components.txt"
    if not file.exists():
        logger.error(f"未找到成分股列表: {file}")
        return []
    codes = [line.strip() for line in file.read_text().splitlines() if line.strip()]
    logger.info(f"加载了 {len(codes)} 支成分股")
    return codes

def find_data_file(symbol: str) -> Path:
    """查找股票数据文件"""
    safe_name = symbol.replace('/', '_').replace('.', '_')
    raw_dir = ROOT / "data" / "raw" / "a_share"
    if not raw_dir.exists():
        return None
    # 尝试多种命名模式
    candidates = [
        raw_dir / f"{safe_name}.csv",
        raw_dir / f"{symbol}.csv",
        raw_dir / f"{symbol.replace('.', '_')}.csv"
    ]
    for cand in candidates:
        if cand.exists():
            return cand
    # 模糊匹配
    for file in raw_dir.glob("*.csv"):
        if symbol in file.name:
            return file
    return None

def split_train_test(df: pd.DataFrame, train_end='2021-12-31', test_start='2022-01-01'):
    """划分训练集和测试集"""
    df['date'] = pd.to_datetime(df['date'])
    train = df[df['date'] <= train_end].copy()
    test = df[df['date'] >= test_start].copy()
    return train, test

def run_backtest_on_data(data_df: pd.DataFrame, strategy, config: Dict, symbol: str) -> Dict:
    """对单只股票运行回测"""
    try:
        # 划分训练测试
        train_df, test_df = split_train_test(data_df)
        if len(train_df) < 250 or len(test_df) < 250:  # 至少1年数据
            logger.warning(f"{symbol}: 数据不足。训练{len(train_df)}天，测试{len(test_df)}天，跳过")
            return None

        # 在训练集上运行策略
        bt_train = Backtester(train_df, strategy, config)
        bt_train.run()
        train_metrics = bt_train.evaluate()
        train_metrics['data_points'] = len(train_df)

        # 在测试集上运行
        bt_test = Backtester(test_df, strategy, config)
        bt_test.run()
        test_metrics = bt_test.evaluate()
        test_metrics['data_points'] = len(test_df)

        return {
            'symbol': symbol,
            'strategy': strategy.__class__.__name__,
            'train': train_metrics,
            'test': test_metrics
        }
    except Exception as e:
        logger.error(f"{symbol} 回测失败: {e}")
        return None

def main():
    print("=" * 60)
    print("🔬 沪深300成分股批量回测")
    print("=" * 60)

    config = load_config()
    components = load_hs300_components()
    if not components:
        print("❌ 无法加载成分股列表")
        return

    strategies = {
        'MA Cross': STRATEGY_REGISTRY['ma_cross'](),
        'MACD Cross': STRATEGY_REGISTRY['macd_cross'](),
        'RSI Extreme': STRATEGY_REGISTRY['rsi_extreme'](),
        'Bollinger Band': STRATEGY_REGISTRY['bollinger'](),
        'TA Confluence': STRATEGY_REGISTRY['confluence']()
    }

    results_dir = ROOT / "results" / "hs300_full"
    results_dir.mkdir(parents=True, exist_ok=True)

    # 存储所有结果
    all_results = []

    total_tasks = len(components) * len(strategies)
    completed = 0

    print(f"📊 开始批量回测：{len(components)} 支股票 × {len(strategies)} 种策略 = {total_tasks} 次任务\n")

    # 如果有中间结果，先加载已完成的symbol避免重复
    partial_file = results_dir / "partial_results.csv"
    completed_symbols = set()
    if partial_file.exists():
        try:
            partial_df = pd.read_csv(partial_file)
            completed_symbols = set(partial_df['symbol'].unique())
            logger.info(f"检测到已完成的 {len(completed_symbols)} 支股票，将跳过")
        except Exception as e:
            logger.warning(f"读取中间结果失败: {e}")

    # 跳过已完成的
    remaining_components = [c for c in components if c not in completed_symbols]
    logger.info(f"待处理: {len(remaining_components)} / {len(components)} 支股票")

    for symbol in remaining_components:  # 处理所有剩余股票
        data_file = find_data_file(symbol)
        if not data_file:
            logger.warning(f"未找到 {symbol} 的数据文件，跳过")
            continue

        print(f"📈 处理 {symbol} ...")
        try:
            df = pd.read_csv(data_file, parse_dates=['date'])
        except Exception as e:
            logger.error(f"读取 {data_file} 失败: {e}")
            continue

        for name, strategy in strategies.items():
            res = run_backtest_on_data(df, strategy, config, symbol)
            if res:
                all_results.append(res)
                test_return = res['test'].get('total_return_pct', 0)
            else:
                test_return = None
            completed += 1
            if test_return is not None:
                print(f"  [{completed}/{total_tasks}] {symbol} - {name}: 测试集收益 {test_return:.2f}%")
            else:
                print(f"  [{completed}/{total_tasks}] {symbol} - {name}: 跳过（数据不足或失败）")
            time.sleep(0.1)  # 避免日志过快

        # 每完成一支股票，保存一次中间结果
        if all_results:
            temp_df = pd.DataFrame([
                {
                    'symbol': r['symbol'],
                    'strategy': r['strategy'],
                    'train_return_pct': r['train'].get('total_return_pct', 0),
                    'train_sharpe': r['train'].get('sharpe_ratio', 0),
                    'train_maxdd_pct': r['train'].get('max_drawdown_pct', 0),
                    'test_return_pct': r['test'].get('total_return_pct', 0),
                    'test_sharpe': r['test'].get('sharpe_ratio', 0),
                    'test_maxdd_pct': r['test'].get('max_drawdown_pct', 0),
                    'test_trades': r['test'].get('total_trades', 0),
                    'win_rate_pct': r['test'].get('win_rate_pct', 0),
                    'train_days': r['train'].get('data_points', 0),
                    'test_days': r['test'].get('data_points', 0)
                }
                for r in all_results
            ])
            temp_df.to_csv(results_dir / "partial_results.csv", index=False, encoding='utf-8-sig')

    print("\n✅ 批量回测完成！")
    print(f"📁 结果保存在: {results_dir}")

    if not all_results:
        print("❌ 没有任何成功的结果")
        return

    # 生成汇总统计
    summary_df = pd.DataFrame([
        {
            'symbol': r['symbol'],
            'strategy': r['strategy'],
            'train_return_pct': r['train'].get('total_return_pct', 0),
            'test_return_pct': r['test'].get('total_return_pct', 0),
            'test_sharpe': r['test'].get('sharpe_ratio', 0),
            'test_maxdd_pct': r['test'].get('max_drawdown_pct', 0),
            'win_rate_pct': r['test'].get('win_rate_pct', 0)
        }
        for r in all_results
    ])

    # 按策略汇总
    strategy_summary = summary_df.groupby('strategy').agg({
        'test_return_pct': ['mean', 'std', 'min', 'max'],
        'test_sharpe': 'mean',
        'test_maxdd_pct': 'mean',
        'win_rate_pct': 'mean',
        'symbol': 'count'
    }).round(2)

    strategy_summary.columns = ['avg_return', 'std_return', 'min_return', 'max_return', 'avg_sharpe', 'avg_maxdd', 'avg_winrate', 'stock_count']
    strategy_summary = strategy_summary.sort_values('avg_return', ascending=False)

    print("\n📊 策略表现汇总（按测试集平均收益排序）:")
    print(strategy_summary.to_string())

    strategy_summary.to_csv(results_dir / "strategy_summary.csv", encoding='utf-8-sig')

    # 最佳策略
    best_strategy = strategy_summary.index[0]
    best_return = strategy_summary.iloc[0]['avg_return']
    print(f"\n🏆 最佳策略: {best_strategy} (平均测试收益: {best_return:.2f}%)")

    # 保存详细结果
    summary_df.to_csv(results_dir / "detailed_results.csv", index=False, encoding='utf-8-sig')

    # 生成Markdown报告
    generate_report(summary_df, strategy_summary, results_dir)

def generate_report(detailed_df, summary_df, results_dir):
    """生成Markdown格式的报告"""
    lines = [
        "# 沪深300成分股策略研究报告",
        f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "## 数据概览",
        f"- 成分股数量: {len(detailed_df['symbol'].unique())}",
        f"- 策略数量: {len(detailed_df['strategy'].unique())}",
        f"- 总回测次数: {len(detailed_df)}",
        "",
        "## 策略表现（按测试集平均收益排序）",
        "",
        summary_df.to_markdown(),
        "",
        "## 详细结果（Top 20）",
        "",
        detailed_df.sort_values('test_return_pct', ascending=False).head(20).to_markdown(index=False),
        "",
        "## 结论",
        "- 建议策略: **" + summary_df.index[0] + "**"
    ]
    report_file = results_dir / "report.md"
    report_file.write_text('\n'.join(lines), encoding='utf-8-sig')
    print(f"📄 报告已生成: {report_file}")

if __name__ == "__main__":
    main()
