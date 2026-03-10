#!/usr/bin/env python3
"""
沪深300成分股量化策略研究（直接使用现有本地数据）
- 按时间划分训练集（2015-2022）和测试集（2023-2025）
- 多策略对比
- 多股票组合回测
"""
import sys
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import Dict, List
import warnings
warnings.filterwarnings('ignore')

sys.path.insert(0, str(Path(__file__).parent.parent))
from src.strategies import STRATEGY_REGISTRY
from src.backtest.engine import Backtester
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

class HS300ResearchFast:
    """快速研究（使用本地已有数据）"""
    
    def __init__(self):
        self.results_dir = Path("results/hs300_research_local")
        self.results_dir.mkdir(parents=True, exist_ok=True)
        self.components = self._load_components()
        
    def _load_components(self) -> List[str]:
        list_file = Path("data/hs300_components.txt")
        if list_file.exists():
            with open(list_file, 'r') as f:
                codes = [line.strip() for line in f if line.strip()]
            logger.info(f"加载了 {len(codes)} 只沪深300成分股")
            return codes
        return []
    
    def load_local_data(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """直接从本地CSV加载数据"""
        safe_name = symbol.replace('.', '_').replace('/', '_')
        raw_dir = Path("data/raw/a_share")
        candidate = raw_dir / f"{safe_name}.csv"
        
        if candidate.exists():
            df = pd.read_csv(candidate, parse_dates=['date'])
            # 时间过滤
            start_dt = pd.to_datetime(start_date)
            end_dt = pd.to_datetime(end_date)
            df = df[(df['date'] >= start_dt) & (df['date'] <= end_dt)].copy()
            # 确保数据质量
            df = df.dropna(subset=['open', 'high', 'low', 'close', 'volume'])
            if len(df) > 0:
                if 'symbol' not in df.columns:
                    df['symbol'] = symbol
                return df
        
        return None
    
    def prepare_universe(self, start_date: str, end_date: str, min_days: int = 200) -> List[str]:
        """准备股票池"""
        universe = []
        for symbol in self.components[:50]:  # 测试用50只
            df = self.load_local_data(symbol, start_date, end_date)
            if df is not None and len(df) >= min_days:
                universe.append(symbol)
        logger.info(f"股票池: {len(universe)} 只 (≥{min_days}天)")
        return universe
    
    def run_portfolio_backtest(self, 
                             universe: List[str],
                             strategy_name: str,
                             start_date: str,
                             end_date: str,
                             initial_capital: float = 100000.0) -> Dict:
        """组合回测"""
        logger.info(f"\n{'='*60}")
        logger.info(f"策略: {strategy_name} | 股票数: {len(universe)} | {start_date}~{end_date}")
        logger.info(f"{'='*60}")
        
        portfolio_daily = []
        valid_symbols = []
        
        for idx, symbol in enumerate(universe, 1):
            try:
                df = self.load_local_data(symbol, start_date, end_date)
                if df is None or len(df) < 20:
                    continue
                    
                strategy_cls = STRATEGY_REGISTRY[strategy_name]
                strategy = strategy_cls()
                
                backtester = Backtester(df, strategy, {})
                results_df = backtester.run()
                
                # 每只股票分配等额资金
                per_stock_value = results_df['total_assets'] / len(universe)
                portfolio_daily.append(per_stock_value.rename(symbol))
                valid_symbols.append(symbol)
                
                if idx % 10 == 0:
                    logger.info(f"  进度: {idx}/{len(universe)}")
                    
            except Exception as e:
                logger.warning(f"  {symbol} 失败: {e}")
                continue
        
        if not portfolio_daily:
            logger.error("所有股票回测失败！")
            return {}
        
        # 组合
        portfolio = pd.concat(portfolio_daily, axis=1)
        portfolio['total_assets'] = portfolio.sum(axis=1)
        
        # 指标
        metrics = self._calculate_metrics(portfolio, initial_capital)
        metrics['strategy'] = strategy_name
        metrics['universe_size'] = len(valid_symbols)
        metrics['start_date'] = start_date
        metrics['end_date'] = end_date
        
        logger.info(f"\n结果:")
        logger.info(f"  总收益: {metrics['total_return_pct']:.2f}%")
        logger.info(f"  年化收益: {metrics['annual_return_pct']:.2f}%")
        logger.info(f"  最大回撤: {metrics['max_drawdown_pct']:.2f}%")
        logger.info(f"  夏普比率: {metrics['sharpe_ratio']:.2f}")
        
        # 保存
        out_dir = self.results_dir / strategy_name
        out_dir.mkdir(parents=True, exist_ok=True)
        portfolio.to_csv(out_dir / f"portfolio_{start_date[:4]}_{end_date[:4]}.csv", encoding='utf-8-sig')
        
        return metrics
    
    def _calculate_metrics(self, portfolio_df: pd.DataFrame, initial_capital: float) -> Dict:
        """计算绩效指标"""
        final = portfolio_df['total_assets'].iloc[-1]
        total_return = (final - initial_capital) / initial_capital * 100
        
        years = (portfolio_df.index[-1] - portfolio_df.index[0]).days / 365.25
        annual_return = ((1 + total_return/100) ** (1/years) - 1) * 100 if years > 0 else 0
        
        portfolio_df['cummax'] = portfolio_df['total_assets'].cummax()
        portfolio_df['drawdown'] = (portfolio_df['total_assets'] - portfolio_df['cummax']) / portfolio_df['cummax']
        max_drawdown = portfolio_df['drawdown'].min() * 100
        
        portfolio_df['daily_return'] = portfolio_df['total_assets'].pct_change().fillna(0)
        excess = portfolio_df['daily_return'] - 0.02/252
        sharpe = excess.mean() / excess.std() * (252 ** 0.5) if excess.std() > 0 else 0
        
        win_rate = (portfolio_df['daily_return'] > 0).sum() / len(portfolio_df) * 100
        
        return {
            'total_return_pct': total_return,
            'annual_return_pct': annual_return,
            'max_drawdown_pct': max_drawdown,
            'sharpe_ratio': sharpe,
            'win_rate_pct': win_rate,
            'final_assets': final,
            'portfolio_df': portfolio_df
        }
    
    def run_full_research(self):
        """运行完整研究"""
        logger.info("开始沪深300多策略研究（使用本地数据）")
        
        # 1. 准备股票池（训练期数据完整）
        train_start, train_end = "2015-01-01", "2022-12-31"
        test_start, test_end = "2023-01-01", "2025-12-31"
        
        universe = self.prepare_universe(train_start, train_end, min_days=1500)
        if not universe:
            logger.error("股票池为空，退出")
            return
        
        # 2. 所有策略在训练集和测试集上回测
        strategies = ['ma_cross', 'macd_cross', 'rsi_extreme', 'bollinger', 'confluence']
        results = []
        
        for strategy in strategies:
            train_res = self.run_portfolio_backtest(universe, strategy, train_start, train_end)
            test_res = self.run_portfolio_backtest(universe, strategy, test_start, test_end)
            
            if train_res and test_res:
                results.append({
                    'Strategy': strategy,
                    'Train_Return_%': train_res['total_return_pct'],
                    'Train_Sharpe': train_res['sharpe_ratio'],
                    'Train_MaxDD_%': train_res['max_drawdown_pct'],
                    'Test_Return_%': test_res['total_return_pct'],
                    'Test_Sharpe': test_res['sharpe_ratio'],
                    'Test_MaxDD_%': test_res['max_drawdown_pct'],
                    'Universe': len(universe)
                })
        
        # 3. 对比报告
        if results:
            df = pd.DataFrame(results)
            df = df.sort_values('Test_Sharpe', ascending=False)
            
            print("\n" + "="*80)
            print("沪深300量化策略对比报告")
            print("="*80)
            print(df.to_string(index=False))
            
            report_file = self.results_dir / "comparison.csv"
            df.to_csv(report_file, index=False, encoding='utf-8-sig')
            logger.info(f"\n📊 报告已保存: {report_file}")
            
            # 最佳策略
            best = df.iloc[0]
            logger.info(f"\n🏆 最佳策略: {best['Strategy']}")
            logger.info(f"   测试夏普: {best['Test_Sharpe']:.2f}")
            logger.info(f"   测试收益: {best['Test_Return_%']:.2f}%")
            logger.info(f"   测试回撤: {best['Test_MaxDD_%']:.2f}%")
        else:
            logger.error("没有可用的回测结果")

if __name__ == "__main__":
    research = HS300ResearchFast()
    research.run_full_research()
