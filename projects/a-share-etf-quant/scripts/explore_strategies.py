#!/usr/bin/env python3
"""
Step 2: 策略探索与回测
基于10年数据，探索天级别交易策略
"""
import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Callable
import matplotlib.pyplot as plt
from dataclasses import dataclass

# 配置
WORKSPACE = "/Users/levy/.openclaw/workspace"
PROJECT_DIR = os.path.join(WORKSPACE, "projects", "a-share-etf-quant")
DATA_DIR = os.path.join(PROJECT_DIR, "data")
RAW_DIR = os.path.join(DATA_DIR, "raw")
RESULTS_DIR = os.path.join(PROJECT_DIR, "results")
os.makedirs(RESULTS_DIR, exist_ok=True)

@dataclass
class Trade:
    """单笔交易记录"""
    date: str
    code: str
    action: str  # 'buy' or 'sell'
    price: float
    quantity: int
    cash_value: float
    reason: str

class Backtester:
    """回测引擎"""
    def __init__(self, data: pd.DataFrame, initial_capital=100000.0):
        """
        data: DataFrame 包含列 ['date', 'code', 'open', 'high', 'low', 'close', 'volume', 'pct_change']
        假设数据已按date排序，且为单一ETF
        """
        self.data = data.copy()
        self.initial_capital = initial_capital
        self.capital = initial_capital  # 现金
        self.position = 0  # 持股数
        self.position_cost = 0.0  # 持仓成本均价
        self.trades = []  # 交易记录
        self.daily_values = []  # 每日资产净值
        self.current_date = None
        
        # 风险参数
        self.position_pct = 0.10  # 单次交易仓位上限（10%）
        self.stop_loss = -0.03  # 止损线 -3%
        self.take_profit = 0.08  # 止盈线 +8%
        
    def calculate_signals(self, strategy_func: Callable) -> pd.DataFrame:
        """根据策略函数生成信号"""
        signals = []
        for idx, row in self.data.iterrows():
            signal = strategy_func(row)
            signals.append(signal if signal else 'hold')
        self.data['signal'] = signals
        return self.data
    
    def execute(self, row):
        """执行交易逻辑"""
        price = row['close']
        date = row['date']
        signal = row['signal']
        
        # 计算当前持仓市值
        position_value = self.position * price
        total_assets = self.capital + position_value
        
        # 检查止损/止盈
        if self.position > 0:
            current_pnl = (price - self.position_cost) / self.position_cost
            if current_pnl <= self.stop_loss:
                signal = 'sell'
                reason = 'stop_loss'
            elif current_pnl >= self.take_profit:
                signal = 'sell'
                reason = 'take_profit'
        
        # 执行信号
        if signal == 'buy' and self.position == 0:
            # 买入：固定金额仓位
            invest_amount = self.capital * self.position_pct
            quantity = int(invest_amount / price)
            if quantity > 0:
                self.capital -= quantity * price
                self.position = quantity
                self.position_cost = price
                self.trades.append(Trade(
                    date=date, code=row.get('code', 'UNKNOWN'),
                    action='buy', price=price, quantity=quantity,
                    cash_value=quantity * price, reason='strategy'
                ))
        elif signal == 'sell' and self.position > 0:
            # 卖出：全仓卖出
            cash = self.position * price
            self.capital += cash
            self.trades.append(Trade(
                date=date, code=row.get('code', 'UNKNOWN'),
                action='sell', price=price, quantity=self.position,
                cash_value=cash, reason=row.get('reason', 'strategy')
            ))
            self.position = 0
            self.position_cost = 0.0
        
        # 记录当日净值
        position_value = self.position * price
        total_assets = self.capital + position_value
        self.daily_values.append({
            'date': date,
            'capital': self.capital,
            'position': self.position,
            'position_value': position_value,
            'total_assets': total_assets,
            'signal': signal
        })
    
    def run(self, data: pd.DataFrame, strategy_func: Callable):
        """运行回测"""
        # 生成信号
        self.calculate_signals(strategy_func)
        data = self.data
        
        # 逐日执行
        for idx, row in data.iterrows():
            self.current_date = row['date']
            self.execute(row)
        
        # 生成结果DataFrame
        self.results_df = pd.DataFrame(self.daily_values)
        return self.results_df
    
    def evaluate(self) -> Dict:
        """评估回测结果"""
        if not self.daily_values:
            return {}
        
        df = self.results_df.copy()
        df['daily_return'] = df['total_assets'].pct_change().fillna(0)
        
        total_return = (df['total_assets'].iloc[-1] - self.initial_capital) / self.initial_capital
        years = (df['date'].iloc[-1] - df['date'].iloc[0]).days / 365.25
        annual_return = (1 + total_return) ** (1/years) - 1 if years > 0 else 0
        
        # 最大回撤
        df['cummax'] = df['total_assets'].cummax()
        df['drawdown'] = (df['total_assets'] - df['cummax']) / df['cummax']
        max_drawdown = df['drawdown'].min()
        
        # 夏普比率（假设无风险利率2%）
        risk_free_rate = 0.02
        excess_returns = df['daily_return'] - risk_free_rate/252
        if excess_returns.std() > 0:
            sharpe_ratio = excess_returns.mean() / excess_returns.std() * np.sqrt(252)
        else:
            sharpe_ratio = 0
        
        # 胜率
        winning_trades = 0
        total_trades = 0
        for i in range(1, len(self.trades), 2):  # 假设买卖成对
            if i < len(self.trades):
                buy = self.trades[i-1]
                sell = self.trades[i]
                if buy.action == 'buy' and sell.action == 'sell':
                    total_trades += 1
                    if sell.price > buy.price:
                        winning_trades += 1
        
        win_rate = winning_trades / total_trades if total_trades > 0 else 0
        
        return {
            'total_return': total_return * 100,
            'annual_return': annual_return * 100,
            'max_drawdown': max_drawdown * 100,
            'sharpe_ratio': sharpe_ratio,
            'win_rate': win_rate * 100,
            'total_trades': total_trades,
            'final_assets': df['total_assets'].iloc[-1],
            'start_date': df['date'].iloc[0],
            'end_date': df['date'].iloc[-1]
        }

def calculate_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """计算技术指标"""
    df = df.copy()
    # 移动平均线
    df['ma5'] = df['close'].rolling(5).mean()
    df['ma10'] = df['close'].rolling(10).mean()
    df['ma20'] = df['close'].rolling(20).mean()
    df['ma60'] = df['close'].rolling(60).mean()
    df['ma120'] = df['close'].rolling(120).mean()
    df['ma250'] = df['close'].rolling(250).mean()

    # RSI (简单实现)
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss
    df['rsi'] = 100 - (100 / (1 + rs))

    # 布林带
    df['bb_middle'] = df['close'].rolling(20).mean()
    bb_std = df['close'].rolling(20).std()
    df['bb_upper'] = df['bb_middle'] + 2 * bb_std
    df['bb_lower'] = df['bb_middle'] - 2 * bb_std
    df['bb_bandwidth'] = (df['bb_upper'] - df['bb_lower']) / df['bb_middle']

    # MACD (简化)
    exp1 = df['close'].ewm(span=12, adjust=False).mean()
    exp2 = df['close'].ewm(span=26, adjust=False).mean()
    df['macd'] = exp1 - exp2
    df['macd_signal'] = df['macd'].ewm(span=9, adjust=False).mean()
    df['macd_hist'] = df['macd'] - df['macd_signal']

    # 成交量变化
    df['volume_ma5'] = df['volume'].rolling(5).mean()
    df['volume_ma20'] = df['volume'].rolling(20).mean()
    df['volume_ratio'] = df['volume'] / df['volume_ma20']

    # ATR (Average True Range) for volatility
    high_low = df['high'] - df['low']
    high_close = np.abs(df['high'] - df['close'].shift())
    low_close = np.abs(df['low'] - df['close'].shift())
    true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    df['atr'] = true_range.rolling(14).mean()
    df['atr_ratio'] = df['atr'] / df['close']

    return df

# === 策略定义 ===

def strategy_ma_cross(row) -> str:
    """均线金叉死叉策略（MA5 vs MA20）"""
    if pd.isna(row['ma5']) or pd.isna(row['ma20']):
        return 'hold'
    if row['ma5'] > row['ma20']:
        return 'buy'
    elif row['ma5'] < row['ma20']:
        return 'sell'
    return 'hold'

def strategy_ma_double(row) -> str:
    """双均线组合策略（MA10 vs MA60）"""
    if pd.isna(row['ma10']) or pd.isna(row['ma60']):
        return 'hold'
    if row['ma10'] > row['ma60']:
        return 'buy'
    elif row['ma10'] < row['ma60']:
        return 'sell'
    return 'hold'

def strategy_ma_triple(row) -> str:
    """三均线系统（MA20 > MA60 > MA120 多头）"""
    if pd.isna(row['ma20']) or pd.isna(row['ma60']) or pd.isna(row['ma120']):
        return 'hold'
    # 多头排列：短 > 中 > 长
    if row['ma20'] > row['ma60'] > row['ma120']:
        return 'buy'
    # 空头排列：短 < 中 < 长
    elif row['ma20'] < row['ma60'] < row['ma120']:
        return 'sell'
    return 'hold'

def strategy_macd_cross(row) -> str:
    """MACD金叉死叉"""
    if pd.isna(row['macd']) or pd.isna(row['macd_signal']):
        return 'hold'
    if row['macd'] > row['macd_signal']:
        return 'buy'
    elif row['macd'] < row['macd_signal']:
        return 'sell'
    return 'hold'

def strategy_macd_hist(row) -> str:
    """MACD柱状图加速策略（ histogram 扩大）"""
    if pd.isna(row['macd_hist']) or pd.isna(row['macd']):
        return 'hold'
    # 柱状图由负变正，且MACD上穿信号
    if row['macd'] > row['macd_signal'] and row['macd_hist'] > 0:
        return 'buy'
    elif row['macd'] < row['macd_signal'] and row['macd_hist'] < 0:
        return 'sell'
    return 'hold'

def strategy_rsi_extreme(row) -> str:
    """RSI超买超卖"""
    if pd.isna(row['rsi']):
        return 'hold'
    if row['rsi'] < 30:
        return 'buy'
    elif row['rsi'] > 70:
        return 'sell'
    return 'hold'

def strategy_rsi_divergence(row) -> str:
    """RSI背离策略（需要前一日数据，这里简化为连续两日背离检测）"""
    # 注意：需要访问前一行数据，实际应在Backtester中实现
    # 这里用简化版：RSI超卖 + 价格新低 或 RSI超买 + 价格新高
    # 需外部传入prev_row，此处仅占位
    return 'hold'

def strategy_bollinger_band(row) -> str:
    """布林带突破"""
    if pd.isna(row['bb_upper']) or pd.isna(row['bb_lower']):
        return 'hold'
    if row['close'] < row['bb_lower']:
        return 'buy'
    elif row['close'] > row['bb_upper']:
        return 'sell'
    return 'hold'

def strategy_bollinger_squeeze(row) -> str:
    """布林带带宽收缩后突破"""
    if pd.isna(row['bb_bandwidth']) or pd.isna(row['bb_upper']):
        return 'hold'
    # 带宽处于近期低点（收缩），且价格突破上轨或下轨
    # 这里简化：带宽小于5%均值视为收缩
    bandwidth_ratio = row['bb_bandwidth']
    # 需要历史均值，暂用固定阈值
    if bandwidth_ratio < 0.03:  # 3%宽度
        if row['close'] > row['bb_upper']:
            return 'buy'
        elif row['close'] < row['bb_lower']:
            return 'sell'
    return 'hold'

def strategy_volume_confirmation(row) -> str:
    """成交量确认策略：价格突破均线 + 成交量放大"""
    if pd.isna(row['ma20']) or pd.isna(row['volume_ratio']):
        return 'hold'
    # 价格突破MA20且成交量放大
    if row['close'] > row['ma20'] and row['volume_ratio'] > 1.5:
        return 'buy'
    elif row['close'] < row['ma20'] and row['volume_ratio'] > 1.5:
        return 'sell'
    return 'hold'

def strategy_ta_confluence(row) -> str:
    """TAV框架：趋势+动量+成交量（原版）"""
    trend_up = (row['close'] > row['ma20']) and (row['ma5'] > row['ma20']) if not pd.isna(row['ma20']) else False
    momentum_good = (30 < row['rsi'] < 70) and (row['macd'] > row['macd_signal']) if not pd.isna(row['rsi']) else False
    volume_spike = row.get('volume_ratio', 1) > 1.5
    if trend_up and momentum_good and volume_spike:
        return 'buy'
    if not trend_up and row.get('signal', '') == 'sell':
        return 'sell'
    return 'hold'

def strategy_ta_strengthened(row) -> str:
    """强化版TAV：多周期均线 + RSI健康 + MACD + 成交量"""
    # 趋势：MA5>MA10>MA60 多头排列
    trend_ok = (row['ma5'] > row['ma10'] > row['ma60']) if not pd.isna(row['ma5']) else False
    # 动量：RSI 40-60 健康上升区间，且MACD金叉
    momentum_ok = (40 < row['rsi'] < 60) and (row['macd'] > row['macd_signal']) if not pd.isna(row['rsi']) else False
    # 成交量：放大1.2倍以上
    volume_ok = row.get('volume_ratio', 1) > 1.2
    # 买入条件
    if trend_ok and momentum_ok and volume_ok:
        return 'buy'
    # 卖出条件：MA20下穿MA60 或 RSI>70 或 MACD死叉
    if (row['ma20'] < row['ma60']) or (row['rsi'] > 70) or (row['macd'] < row['macd_signal']):
        return 'sell'
    return 'hold'

def strategy_atr_trailing(row) -> str:
    """ATR动态止损策略（仅卖出信号）"""
    # 这个策略主要影响卖出，买入使用其他信号
    # 返回 'hold' 保持原策略
    return 'hold'

def strategy_momentum_rotation(row) -> str:
    """动量轮动策略（需多ETF比较，单标的不适用）"""
    # 在多ETF场景中，选择近期涨幅最大的
    return 'hold'

def strategy_ma_rsi_combo(row) -> str:
    """MA + RSI 组合（经典）"""
    # 买入：MA20上行 + RSI从底部回升至30-50
    if not pd.isna(row['ma20']) and not pd.isna(row['rsi']):
        # 需要历史数据判断MA方向，这里简化
        if row['close'] > row['ma20'] and 30 < row['rsi'] < 50:
            return 'buy'
        elif row['rsi'] > 70:
            return 'sell'
    return 'hold'

# === 训练测试集划分 ===

def split_train_test(df: pd.DataFrame, train_end_date='2021-12-31', test_start_date='2022-01-01'):
    """划分训练集和测试集"""
    df['date'] = pd.to_datetime(df['date'])
    train = df[df['date'] <= train_end_date].copy()
    test = df[df['date'] >= test_start_date].copy()
    print(f"📚 训练集: {len(train)} 天 ({train['date'].iloc[0].date()} ~ {train['date'].iloc[-1].date()})")
    print(f"🔬 测试集: {len(test)} 天 ({test['date'].iloc[0].date()} ~ {test['date'].iloc[-1].date()})")
    return train, test

def run_all_strategies(df: pd.DataFrame, initial_capital=100000, dataset_name='train'):
    """运行所有策略并评估
    
    Args:
        df: 数据DataFrame
        initial_capital: 初始资金
        dataset_name: 'train' 或 'test'
    
    Returns:
        results_df: 汇总结果
        equity_curves: 各策略逐日资金曲线 {strategy_name: DataFrame}
    """
    strategies = {
        'MA Cross': strategy_ma_cross,
        'MA Double': strategy_ma_double,
        'MA Triple': strategy_ma_triple,
        'MACD Cross': strategy_macd_cross,
        'MACD Hist': strategy_macd_hist,
        'RSI Extreme': strategy_rsi_extreme,
        'MA+RSI Combo': strategy_ma_rsi_combo,
        'Bollinger Band': strategy_bollinger_band,
        'Bollinger Squeeze': strategy_bollinger_squeeze,
        'Volume Confirm': strategy_volume_confirmation,
        'TA Confluence': strategy_ta_confluence,
        'TA Strengthened': strategy_ta_strengthened
    }
    
    results = []
    equity_curves = {}
    
    for name, func in strategies.items():
        print(f"\n🧪 测试策略: {name} ({dataset_name})")
        bt = Backtester(df, initial_capital)
        bt.run(df, func)
        metrics = bt.evaluate()
        metrics['strategy'] = name
        results.append(metrics)
        
        # 保存逐日资金曲线
        if len(bt.daily_values) > 0:
            equity_df = pd.DataFrame(bt.daily_values)
            equity_df['strategy'] = name
            equity_df['dataset'] = dataset_name
            equity_curves[name] = equity_df
        
        print(f"  总收益: {metrics.get('total_return', 0):.2f}%, 夏普: {metrics.get('sharpe_ratio', 0):.2f}, 最大回撤: {metrics.get('max_drawdown', 0):.2f}%")
    
    results_df = pd.DataFrame(results)
    results_file = os.path.join(RESULTS_DIR, f"{dataset_name}_results.csv")
    results_df.to_csv(results_file, index=False, encoding='utf-8-sig')
    print(f"\n✅ {dataset_name} 策略对比完成，结果保存至: {results_file}")
    
    # 保存所有策略的逐日资金曲线
    if equity_curves:
        all_equity = pd.concat(equity_curves.values(), ignore_index=True)
        equity_file = os.path.join(RESULTS_DIR, f"equity_curves_{dataset_name}.csv")
        all_equity.to_csv(equity_file, index=False, encoding='utf-8-sig')
        print(f"✅ {dataset_name} 资金曲线数据已保存: {equity_file} ({len(all_equity)} 行)")
    
    return results_df, set(equity_curves.keys())

def main():
    print("=" * 60)
    print("🔬 A股ETF策略探索与回测（训练集+测试集）")
    print("=" * 60)
    
    # 1. 读取历史数据
    history_file = os.path.join(RAW_DIR, "etf_history_2015_2025.csv")
    if not os.path.exists(history_file):
        print(f"❌ 数据文件不存在: {history_file}")
        print("请先运行 fetch_etf_data.py 抓取数据")
        return
    
    print(f"📂 正在读取数据: {history_file}")
    df = pd.read_csv(history_file)
    print(f"✅ 总数据: {len(df)} 条记录")
    
    # 按ETF分组
    print("\n📊 ETF列表:")
    codes = df['code'].unique()
    print(f"   共 {len(codes)} 只ETF")
    print(f"   前5只: {codes[:5]}")
    
    # 选择沪深300ETF作为示例
    target_code = '510300'
    if target_code in codes:
        df_target = df[df['code'] == target_code].copy()
        print(f"\n🎯 选择标的: {target_code} (沪深300ETF)")
        print(f"   数据条数: {len(df_target)}")
    else:
        print(f"⚠️  未找到 {target_code}，使用第一只ETF: {codes[0]}")
        df_target = df[df['code'] == codes[0]].copy()
    
    # 2. 计算技术指标
    print("\n⚙️  计算技术指标...")
    df_target = calculate_indicators(df_target)
    print(f"✅ 指标计算完成，新增列: {[c for c in df_target.columns if c not in ['date','code','open','high','low','close','volume','amount','pct_change']]}")
    
    # 3. 划分训练集和测试集
    print("\n✂️  划分训练集/测试集...")
    train_df, test_df = split_train_test(df_target)
    
    # 4. 训练集回测
    print("\n" + "="*60)
    print("🏋️  训练集回测 (2015-2021)")
    print("="*60)
    train_results, train_strategies = run_all_strategies(train_df, initial_capital=100000, dataset_name='train')
    
    # 5. 测试集回测
    print("\n" + "="*60)
    print("🔬 测试集验证 (2022-2025)")
    print("="*60)
    test_results, test_strategies = run_all_strategies(test_df, initial_capital=100000, dataset_name='test')
    
    # 6. 生成汇总对比报告
    print("\n" + "="*60)
    print("📊 生成汇总报告")
    print("="*60)
    
    # 创建策略对比摘要（训练集vs测试集）
    summary_rows = []
    for strategy in train_strategies.union(test_strategies):
        train_row = train_results[train_results['strategy'] == strategy]
        test_row = test_results[test_results['strategy'] == strategy]
        
        summary_rows.append({
            'strategy': strategy,
            'train_return': train_row.iloc[0]['total_return'] if len(train_row) > 0 else None,
            'train_sharpe': train_row.iloc[0]['sharpe_ratio'] if len(train_row) > 0 else None,
            'train_maxdd': train_row.iloc[0]['max_drawdown'] if len(train_row) > 0 else None,
            'test_return': test_row.iloc[0]['total_return'] if len(test_row) > 0 else None,
            'test_sharpe': test_row.iloc[0]['sharpe_ratio'] if len(test_row) > 0 else None,
            'test_maxdd': test_row.iloc[0]['max_drawdown'] if len(test_row) > 0 else None,
        })
    
    summary_df = pd.DataFrame(summary_rows)
    summary_file = os.path.join(RESULTS_DIR, "strategy_comparison_summary.csv")
    summary_df.to_csv(summary_file, index=False, encoding='utf-8-sig')
    print(f"✅ 训练/测试对比汇总已保存: {summary_file}")
    
    # 7. 创建看板数据准备脚本的输入文件
    # 将结果复制到 dashboard 目录（后续由 prepare_dashboard.py 处理）
    print("\n📁 准备看板数据...")
    print("   请运行: python3 scripts/prepare_dashboard.py")
    
    print("\n" + "="*60)
    print("✅ 全部完成！")
    print("="*60)
    print(f"📁 结果目录: {RESULTS_DIR}")
    print("   包含:")
    print("   - train_results.csv      (训练集策略汇总)")
    print("   - test_results.csv       (测试集策略汇总)")
    print("   - equity_curves_train.csv (训练集逐日资金曲线)")
    print("   - equity_curves_test.csv  (测试集逐日资金曲线)")
    print("   - strategy_comparison_summary.csv (训练vs测试对比)")
    print("\n💡 下一步: 运行 prepare_dashboard.py 生成看板数据，然后访问 http://localhost:8081/analysis.html")

if __name__ == "__main__":
    main()
