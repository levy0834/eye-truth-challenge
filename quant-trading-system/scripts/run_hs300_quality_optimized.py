#!/usr/bin/env python3
"""
优质老股票专项回测
筛选成立10年以上的沪深300成分股（约116支）
使用优化后的风控参数
"""
import os
import sys
import yaml
import pandas as pd
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from src.strategies import STRATEGY_REGISTRY
from src.backtest.engine import Backtester
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

def load_config(optimized=False):
    """加载配置文件"""
    config_file = ROOT / ("config/settings_optimized.yaml" if optimized else "config/settings.yaml")
    with open(config_file, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def load_hs300_components():
    """加载沪深300成分股列表"""
    file = ROOT / "data" / "hs300_components.txt"
    if not file.exists():
        logger.error(f"未找到成分股列表: {file}")
        return []
    codes = [line.strip() for line in file.read_text().splitlines() if line.strip()]
    return codes

def load_data_quality_report():
    """加载数据质量报告，筛选优质股票"""
    report_file = ROOT / "data" / "hs300_data_quality_report.csv"
    if not report_file.exists():
        logger.warning("未找到数据质量报告，将使用全部股票")
        return None
    
    df = pd.read_csv(report_file)
    # 筛选成立10年以上的股票（start <= 2015-12-31）
    df['start'] = pd.to_datetime(df['start'])
    cutoff_date = pd.to_datetime('2015-12-31')
    quality_stocks = df[df['start'] <= cutoff_date]
    
    logger.info(f"数据质量报告: 共{len(df)}支股票，其中{len(quality_stocks)}支成立于2015年以前（10年以上）")
    return set(quality_stocks['symbol'].tolist())

def find_data_file(symbol: str) -> Path:
    """查找股票数据文件"""
    safe_name = symbol.replace('/', '_').replace('.', '_')
    raw_dir = ROOT / "data" / "raw" / "a_share"
    if not raw_dir.exists():
        return None
    
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

def run_backtest_on_data(data_df: pd.DataFrame, strategy, config: dict, symbol: str) -> dict:
    """对单只股票运行回测"""
    try:
        # 划分训练测试
        train_df, test_df = split_train_test(data_df)
        if len(train_df) < 250 or len(test_df) < 250:
            return None
        
        # 训练集
        bt_train = Backtester(train_df, strategy, config)
        bt_train.run()
        train_metrics = bt_train.evaluate()
        
        # 测试集
        bt_test = Backtester(test_df, strategy, config)
        bt_test.run()
        test_metrics = bt_test.evaluate()
        
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
    print("=" * 70)
    print("🎯 沪深300优质成分股专项回测")
    print("=" * 70)
    
    # 1. 加载配置
    print("\n📋 加载配置...")
    config = load_config(optimized=True)
    print(f"   风控参数: 仓位={config['risk_control']['position_size']*100:.0f}%, "
          f"止损={config['risk_control']['stop_loss']*100:.0f}%, "
          f"止盈={config['risk_control']['take_profit']*100:.0f}%")
    
    # 2. 加载成分股
    all_components = load_hs300_components()
    if not all_components:
        print("❌ 无法加载成分股列表")
        return
    
    # 3. 筛选优质股票（10年以上历史）
    quality_set = load_data_quality_report()
    if quality_set:
        quality_components = [c for c in all_components if c in quality_set]
        logger.info(f"筛选出优质股票: {len(quality_components)} / {len(all_components)}")
    else:
        # 如果没有质量报告，使用成立时间判断（基于数据文件存在）
        print("\n🔍 扫描数据文件筛选优质股票...")
        quality_components = []
        for code in all_components:
            data_file = find_data_file(code)
            if data_file:
                try:
                    df = pd.read_csv(data_file, parse_dates=['date'])
                    if len(df) >= 2000:  # 约8年数据
                        quality_components.append(code)
                except:
                    pass
        print(f"   优质股票: {len(quality_components)} 支")
    
    # 限制数量（可选，避免跑太久）
    max_stocks = 100  # 先跑100支优质股票
    if len(quality_components) > max_stocks:
        print(f"⚠️  优质股票较多({len(quality_components)})，先测试前 {max_stocks} 支")
        quality_components = quality_components[:max_stocks]
    
    # 4. 选择策略
    strategies = {
        'MA Cross': STRATEGY_REGISTRY['ma_cross'](),
        'MACD Cross': STRATEGY_REGISTRY['macd_cross'](),
        'RSI Extreme': STRATEGY_REGISTRY['rsi_extreme'](),
        'Bollinger Band': STRATEGY_REGISTRY['bollinger'](),
        'TA Confluence': STRATEGY_REGISTRY['confluence']()
    }
    
    print(f"\n📊 开始回测: {len(quality_components)} 支股票 × {len(strategies)} 种策略")
    print(f"   预计耗时: {len(quality_components) * len(strategies) * 2 / 60:.1f} 分钟")
    
    # 5. 执行回测
    results_dir = ROOT / "results" / "hs300_quality_optimized"
    results_dir.mkdir(parents=True, exist_ok=True)
    
    all_results = []
    total_tasks = len(quality_components) * len(strategies)
    completed = 0
    
    for symbol in quality_components:
        data_file = find_data_file(symbol)
        if not data_file:
            logger.warning(f"未找到 {symbol} 数据文件，跳过")
            continue
        
        try:
            df = pd.read_csv(data_file, parse_dates=['date'])
        except Exception as e:
            logger.error(f"读取 {data_file} 失败: {e}")
            continue
        
        print(f"\n📈 处理 {symbol} ({len(df)} 行数据)")
        
        for name, strategy in strategies.items():
            res = run_backtest_on_data(df, strategy, config, symbol)
            if res:
                all_results.append(res)
                test_return = res['test'].get('total_return_pct', 0)
                print(f"  [{completed+1}/{total_tasks}] {name}: {test_return:.2f}%")
            else:
                print(f"  [{completed+1}/{total_tasks}] {name}: 跳过")
            completed += 1
    
    # 6. 保存结果
    if not all_results:
        print("❌ 没有任何成功结果")
        return
    
    print(f"\n✅ 回测完成！共收集 {len(all_results)} 条结果")
    
    # 转为DataFrame
    summary_rows = []
    for r in all_results:
        summary_rows.append({
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
        })
    
    summary_df = pd.DataFrame(summary_rows)
    summary_file = results_dir / "detailed_results.csv"
    summary_df.to_csv(summary_file, index=False, encoding='utf-8-sig')
    print(f"📁 详细结果: {summary_file}")
    
    # 策略汇总
    strategy_summary = summary_df.groupby('strategy').agg({
        'test_return_pct': ['mean', 'std', 'min', 'max'],
        'test_sharpe': 'mean',
        'test_maxdd_pct': 'mean',
        'win_rate_pct': 'mean',
        'symbol': 'count'
    }).round(2)
    
    strategy_summary.columns = ['avg_return', 'std_return', 'min_return', 'max_return',
                               'avg_sharpe', 'avg_maxdd', 'avg_winrate', 'stock_count']
    strategy_summary = strategy_summary.sort_values('avg_return', ascending=False)
    
    summary_csv = results_dir / "strategy_summary.csv"
    strategy_summary.to_csv(summary_csv, encoding='utf-8-sig')
    print(f"📁 策略汇总: {summary_csv}")
    
    # 7. 打印结果
    print("\n" + "=" * 70)
    print("📊 策略表现排名（按平均测试收益）:")
    print("=" * 70)
    print(strategy_summary.to_string())
    
    print(f"\n🏆 最佳策略: {strategy_summary.index[0]} (平均收益: {strategy_summary.iloc[0]['avg_return']:.2f}%)")
    print(f"📈 最优单股: {summary_df.loc[summary_df['test_return_pct'].idxmax(), 'symbol']} "
          f"({summary_df['test_return_pct'].max():.2f}%)")
    
    # 8. 生成Markdown报告
    generate_report(summary_df, strategy_summary, results_dir)
    print(f"\n📄 报告已生成: {results_dir / 'report.md'}")

def generate_report(detailed_df, summary_df, results_dir):
    """生成Markdown报告"""
    lines = [
        "# 沪深300优质成分股优化回测报告",
        f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "## 实验设置",
        "- **股票池**: 沪深300成分股中成立10年以上的优质股票",
        "- **回测股票数**: " + str(len(detailed_df['symbol'].unique())),
        "- **时间范围**: 2006-2025（训练: 2006-2021, 测试: 2022-2025）",
        "- **风控参数（优化）**:",
        "  - 仓位: 15% (原10%)",
        "  - 止损: -5% (原-3%)",
        "  - 止盈: +12% (原+8%)",
        "  - 最大回撤停损: -25%",
        "",
        "## 策略表现排名",
        "",
        summary_df.to_markdown(),
        "",
        "## 详细结果（Top 20）",
        "",
        detailed_df.sort_values('test_return_pct', ascending=False).head(20).to_markdown(index=False),
        "",
        "## 关键发现",
        "1. 优化风控后，胜率可能提升（减少假止损）",
        "2. 优质老股票表现更稳定（回撤可能更小）",
        "3. 最佳策略仍可能是MA均线或MACD",
        "",
        "## 建议下一步",
        "1. 继续调整参数（止损-8%、止盈+15%）",
        "2. 加入动态仓位管理（趋势强时加大仓位）",
        "3. 测试不同股票池（如市值排名前50）"
    ]
    
    report_file = results_dir / "report.md"
    report_file.write_text('\n'.join(lines), encoding='utf-8-sig')

if __name__ == "__main__":
    main()
