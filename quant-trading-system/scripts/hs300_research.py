#!/usr/bin/env python3
"""
沪深300成分股多因子量化策略研究
- 按时间划分训练集（2015-2022）和测试集（2023-2025）
- 多策略对比（MA、MACD、RSI、布林带、TAV共振）
- 多股票组合回测（等权重）
- 因子有效性分析
"""
import sys
import argparse
import yaml
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Any
import warnings
warnings.filterwarnings('ignore')

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data.fetchers import DataFetcher
from src.strategies import STRATEGY_REGISTRY
from src.backtest.engine import Backtester
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

class HS300MultiFactorResearch:
    """沪深300多因子研究"""
    
    def __init__(self, config_path: str = "config/settings.yaml"):
        self.config = self._load_config(config_path)
        self.components = self._load_components()
        self.results_dir = Path("results/hs300_research")
        self.results_dir.mkdir(parents=True, exist_ok=True)
        
    def _load_config(self, path: str) -> Dict:
        with open(path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    def _load_components(self) -> List[str]:
        """加载沪深300成分股列表"""
        list_file = Path("data/hs300_components.txt")
        if list_file.exists():
            with open(list_file, 'r') as f:
                codes = [line.strip() for line in f if line.strip()]
            logger.info(f"加载了 {len(codes)} 只沪深300成分股")
            return codes
        else:
            logger.error("未找到 hs300_components.txt，请先运行 fetch_hs300_components.py")
            return []
    
    def load_stock_data(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """加载单只股票数据（优先本地）"""
        # 尝试从本地 raw 目录加载
        safe_name = symbol.replace('.', '_').replace('/', '_')
        raw_dir = Path("data/raw/a_share")
        candidate = raw_dir / f"{safe_name}.csv"
        
        if candidate.exists():
            df = pd.read_csv(candidate, parse_dates=['date'])
            # 时间过滤
            df = df[(df['date'] >= pd.to_datetime(start_date)) & 
                    (df['date'] <= pd.to_datetime(end_date))].copy()
            if len(df) > 0:
                logger.debug(f"✅ 从本地加载 {symbol}: {len(df)} 行")
                return df
        
        # 如果本地没有，尝试通过fetcher下载
        logger.info(f"本地未找到 {symbol}，尝试下载...")
        fetcher = DataFetcher(self.config)
        df = fetcher.fetch(symbol, start_date, end_date)
        if df is not None:
            # 保存到本地
            raw_dir.mkdir(parents=True, exist_ok=True)
            df.to_csv(candidate, index=False, encoding='utf-8-sig')
            logger.info(f"✅ 下载并保存 {symbol}: {len(df)} 行")
        return df
    
    def prepare_universe(self, start_date: str, end_date: str, min_days: int = 100) -> List[str]:
        """准备股票池：筛选出在训练期内数据完整的股票"""
        logger.info(f"准备股票池：时间范围 {start_date} ~ {end_date}")
        universe = []
        
        for symbol in self.components[:50]:  # 先测试前50只，避免太慢
            try:
                df = self.load_stock_data(symbol, start_date, end_date)
                if df is not None and len(df) >= min_days:
                    universe.append(symbol)
                else:
                    logger.debug(f"❌ {symbol} 数据不足 ({len(df) if df is not None else 0} < {min_days})")
            except Exception as e:
                logger.warning(f"加载 {symbol} 失败: {e}")
            
        logger.info(f"股票池大小: {len(universe)} 只 (≥{min_days}天)")
        return universe
    
    def run_backtest_on_universe(self, 
                                 universe: List[str], 
                                 strategy_name: str,
                                 start_date: str, 
                                 end_date: str,
                                 initial_capital: float = 100000.0) -> Dict[str, Any]:
        """在股票池上运行回测（等权重组合）"""
        logger.info(f"\n{'='*60}")
        logger.info(f"回测: {strategy_name} | 股票池: {len(universe)} 只 | {start_date} ~ {end_date}")
        logger.info(f"{'='*60}")
        
        # 收集每只股票的回测结果
        individual_results = []
        portfolio_daily = []  # 组合日度资产
        
        for idx, symbol in enumerate(universe, 1):
            try:
                df = self.load_stock_data(symbol, start_date, end_date)
                if df is None or len(df) < 20:
                    logger.warning(f"跳过 {symbol}: 数据不足")
                    continue
                
                # 添加symbol列
                if 'symbol' not in df.columns:
                    df['symbol'] = symbol
                
                # 选择策略
                strategy_cls = STRATEGY_REGISTRY[strategy_name]
                strategy = strategy_cls()
                
                # 回测
                backtester = Backtester(df, strategy, self.config)
                results_df = backtester.run()
                metrics = backtester.evaluate()
                metrics['symbol'] = symbol
                metrics['data_points'] = len(df)
                individual_results.append(metrics)
                
                # 收集日度资产（用于组合）
                results_df['symbol'] = symbol
                portfolio_daily.append(results_df[['total_assets']].rename(columns={'total_assets': symbol}))
                
                if idx % 10 == 0:
                    logger.info(f"  进度: {idx}/{len(universe)}")
                    
            except Exception as e:
                logger.error(f"回测 {symbol} 失败: {e}")
                import traceback
                traceback.print_exc()
        
        if not individual_results:
            logger.error("所有股票回测失败！")
            return {}
        
        # 组合收益（等权重）
        portfolio_df = pd.concat(portfolio_daily, axis=1)
        # 假设每只股票分配初始资本 / 股票数量
        per_stock_capital = initial_capital / len(universe)
        # 计算组合总资产 = sum(每只股票资产)
        portfolio_df['total_assets'] = portfolio_df.sum(axis=1)
        
        # 计算组合指标
        final_assets = portfolio_df['total_assets'].iloc[-1]
        total_return = (final_assets - initial_capital) / initial_capital * 100
        years = (portfolio_df.index[-1] - portfolio_df.index[0]).days / 365.25
        annual_return = ((1 + total_return/100) ** (1/years) - 1) * 100 if years > 0 else 0
        
        portfolio_df['cummax'] = portfolio_df['total_assets'].cummax()
        portfolio_df['drawdown'] = (portfolio_df['total_assets'] - portfolio_df['cummax']) / portfolio_df['cummax']
        max_drawdown = portfolio_df['drawdown'].min() * 100
        
        portfolio_df['daily_return'] = portfolio_df['total_assets'].pct_change().fillna(0)
        excess_returns = portfolio_df['daily_return'] - 0.02/252
        sharpe = excess_returns.mean() / excess_returns.std() * (252 ** 0.5) if excess_returns.std() > 0 else 0
        
        # 胜率（基于单日收益）
        win_rate = (portfolio_df['daily_return'] > 0).sum() / len(portfolio_df) * 100
        
        # 汇总
        summary = {
            'strategy': strategy_name,
            'period': f"{start_date} ~ {end_date}",
            'universe_size': len(universe),
            'initial_capital': initial_capital,
            'final_assets': final_assets,
            'total_return_pct': total_return,
            'annual_return_pct': annual_return,
            'max_drawdown_pct': max_drawdown,
            'sharpe_ratio': sharpe,
            'win_rate_pct': win_rate,
            'avg_stock_return_pct': np.mean([r['total_return_pct'] for r in individual_results]),
            'median_stock_return_pct': np.median([r['total_return_pct'] for r in individual_results]),
            'positive_stocks_pct': sum(1 for r in individual_results if r['total_return_pct'] > 0) / len(individual_results) * 100,
            'portfolio_df': portfolio_df,
            'individual_results': individual_results
        }
        
        logger.info(f"\n组合回测结果:")
        logger.info(f"  总收益率: {total_return:.2f}%")
        logger.info(f"  年化收益率: {annual_return:.2f}%")
        logger.info(f"  最大回撤: {max_drawdown:.2f}%")
        logger.info(f"  夏普比率: {sharpe:.2f}")
        logger.info(f"  日胜率: {win_rate:.2f}%")
        logger.info(f"  正收益股票占比: {summary['positive_stocks_pct']:.1f}%")
        
        return summary
    
    def train_test_split_by_time(self, 
                                 universe: List[str],
                                 train_start: str = "2015-01-01",
                                 train_end: str = "2022-12-31",
                                 test_start: str = "2023-01-01",
                                 test_end: str = "2025-12-31") -> Dict[str, Any]:
        """按时间划分训练集和测试集"""
        logger.info(f"\n{'#'*60}")
        logger.info(f"开始时间序列划分研究")
        logger.info(f"训练集: {train_start} ~ {train_end}")
        logger.info(f"测试集: {test_start} ~ {test_end}")
        logger.info(f"{'#'*60}")
        
        results = {}
        
        # 所有策略
        strategies = list(STRATEGY_REGISTRY.keys())
        logger.info(f"测试策略: {strategies}")
        
        for strategy in strategies:
            # 训练集回测
            train_result = self.run_backtest_on_universe(
                universe, strategy, train_start, train_end
            )
            
            # 测试集回测
            test_result = self.run_backtest_on_universe(
                universe, strategy, test_start, test_end
            )
            
            results[strategy] = {
                'train': train_result,
                'test': test_result,
                'stability': self._calculate_stability(train_result, test_result)
            }
        
        # 生成对比报告
        self._generate_comparison_report(results)
        
        return results
    
    def _calculate_stability(self, train: Dict, test: Dict) -> Dict:
        """计算策略稳定性（训练vs测试）"""
        if not train or not test:
            return {}
        
        train_ret = train.get('total_return_pct', 0)
        test_ret = test.get('total_return_pct', 0)
        
        train_sharpe = train.get('sharpe_ratio', 0)
        test_sharpe = test.get('sharpe_ratio', 0)
        
        train_dd = train.get('max_drawdown_pct', 0)
        test_dd = test.get('max_drawdown_pct', 0)
        
        return {
            'return_ratio': test_ret / train_ret if train_ret != 0 else np.nan,
            'sharpe_ratio': test_sharpe / train_sharpe if train_sharpe != 0 else np.nan,
            'drawdown_ratio': test_dd / train_dd if train_dd != 0 else np.nan,
            'is_stable': abs(test_ret - train_ret) < 10 and test_sharpe > 0
        }
    
    def _generate_comparison_report(self, results: Dict):
        """生成策略对比报告"""
        logger.info(f"\n{'='*60}")
        logger.info("策略对比报告")
        logger.info(f"{'='*60}")
        
        # 创建对比表格
        rows = []
        for strategy, data in results.items():
            train = data.get('train', {})
            test = data.get('test', {})
            stability = data.get('stability', {})
            
            rows.append({
                'Strategy': strategy,
                'Train_Return_%': train.get('total_return_pct', np.nan),
                'Test_Return_%': test.get('total_return_pct', np.nan),
                'Train_Sharpe': train.get('sharpe_ratio', np.nan),
                'Test_Sharpe': test.get('sharpe_ratio', np.nan),
                'Train_MaxDD_%': train.get('max_drawdown_pct', np.nan),
                'Test_MaxDD_%': test.get('max_drawdown_pct', np.nan),
                'Positive_Stocks_%': test.get('positive_stocks_pct', np.nan),
                'Stability': stability.get('is_stable', False)
            })
        
        df_cmp = pd.DataFrame(rows)
        
        # 按测试集夏普排序
        df_cmp = df_cmp.sort_values('Test_Sharpe', ascending=False)
        
        print("\n" + df_cmp.to_string(index=False))
        
        # 保存到CSV
        report_file = self.results_dir / "strategy_comparison.csv"
        df_cmp.to_csv(report_file, index=False, encoding='utf-8-sig')
        logger.info(f"\n📊 对比报告已保存: {report_file}")
        
        # 保存详细结果（pickle）
        import pickle
        detail_file = self.results_dir / "detailed_results.pkl"
        with open(detail_file, 'wb') as f:
            pickle.dump(results, f)
        logger.info(f"📦 详细结果已保存: {detail_file}")
        
        # 生成最佳策略建议
        best_strategy = df_cmp.iloc[0]['Strategy']
        logger.info(f"\n🏆 最佳策略: {best_strategy}")
        logger.info(f"   测试集夏普: {df_cmp.iloc[0]['Test_Sharpe']:.2f}")
        logger.info(f"   测试集收益: {df_cmp.iloc[0]['Test_Return_%']:.2f}%")
        logger.info(f"   测试集最大回撤: {df_cmp.iloc[0]['Test_MaxDD_%']:.2f}%")

def main():
    parser = argparse.ArgumentParser(description="沪深300多因子量化策略研究")
    parser.add_argument('--train-start', default='2015-01-01', help='训练集开始日期')
    parser.add_argument('--train-end', default='2022-12-31', help='训练集结束日期')
    parser.add_argument('--test-start', default='2023-01-01', help='测试集开始日期')
    parser.add_argument('--test-end', default='2025-12-31', help='测试集结束日期')
    parser.add_argument('--universe-size', type=int, default=50, help='股票池大小（测试用小样本）')
    parser.add_argument('--min-days', type=int, default=500, help='最小数据天数')
    
    args = parser.parse_args()
    
    research = HS300MultiFactorResearch()
    
    # 1. 准备股票池（在训练期内数据完整的）
    universe = research.prepare_universe(
        start_date=args.train_start,
        end_date=args.train_end,
        min_days=args.min_days
    )
    
    if len(universe) > args.universe_size:
        logger.info(f"股票池过大，截取前 {args.universe_size} 只进行测试")
        universe = universe[:args.universe_size]
    
    if not universe:
        logger.error("股票池为空，退出")
        return
    
    # 2. 时间划分回测
    results = research.train_test_split_by_time(
        universe=universe,
        train_start=args.train_start,
        train_end=args.train_end,
        test_start=args.test_start,
        test_end=args.test_end
    )
    
    logger.info("\n✅ 研究完成！")

if __name__ == "__main__":
    main()
