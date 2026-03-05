"""
回测引擎
"""
import pandas as pd
from typing import Dict, Any
from datetime import datetime
from src.strategies import Strategy
from .broker import SimulatedBroker
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

class Backtester:
    """回测引擎"""
    def __init__(self, data: pd.DataFrame, strategy: Strategy, config: Dict[str, Any]):
        """
        Args:
            data: OHLCV DataFrame, 必须包含 ['date', 'open', 'high', 'low', 'close', 'volume']
            strategy: 策略实例
            config: 配置字典（风控、佣金等）
        """
        self.data = data.sort_values('date').reset_index(drop=True)
        self.strategy = strategy
        self.config = config

        # 初始化券商
        initial_capital = config.get('backtest', {}).get('initial_capital', 100000.0)
        self.broker = SimulatedBroker(initial_capital=initial_capital, config=config.get('backtest', {}))

        # 风控参数
        risk = config.get('risk_control', {})
        self.position_size = risk.get('position_size', 0.10)
        self.stop_loss = risk.get('stop_loss', -0.03)
        self.take_profit = risk.get('take_profit', 0.08)

        # 记录
        self.portfolio_history = []
        self.daily_signals = []

    def run(self) -> pd.DataFrame:
        """执行回测"""
        logger.info(f"开始回测：{len(self.data)} 个交易日")

        # 预计算指标
        self.data = self.strategy.calculate_indicators(self.data)

        for idx, row in self.data.iterrows():
            date = row['date']
            price = row['close']

            # 更新持仓价格
            self.broker.update_prices({self._get_symbol(row): price})

            # 生成信号
            signal = self.strategy.generate_signal(row)
            self.daily_signals.append({'date': date, 'signal': signal, 'price': price})

            # 检查止损/止盈
            if self._check_stop_loss(row) or self._check_take_profit(row):
                self._execute_sell(row, reason='risk_control')

            # 执行交易（如果信号是buy且无持仓，或sell且有持仓）
            if signal == 'buy' and not self._has_position():
                self._execute_buy(row)
            elif signal == 'sell' and self._has_position():
                self._execute_sell(row, reason='strategy')

            # 记录当日资产
            total_value = self.broker.get_portfolio_value({self._get_symbol(row): price})
            self.portfolio_history.append({
                'date': date,
                'cash': self.broker.cash,
                'position_value': sum(pos.market_value for pos in self.broker.positions.values()),
                'total_assets': total_value
            })

        # 最后一天强制平仓
        self._liquidate_position(row)

        logger.info(f"回测完成。最终资产: {total_value:,.2f}")
        return self._get_results_df()

    def _get_symbol(self, row) -> str:
        return row.get('symbol', self.config.get('default_symbol', 'UNKNOWN'))

    def _has_position(self) -> bool:
        return len(self.broker.positions) > 0

    def _execute_buy(self, row):
        symbol = self._get_symbol(row)
        price = row['close']
        # 仓位大小：总资产的 position_size%
        portfolio_value = self.broker.get_portfolio_value({symbol: price})
        invest_amount = portfolio_value * self.position_size
        quantity = int(invest_amount / price)
        if quantity > 0:
            self.broker.place_order(symbol, 'buy', quantity, price)

    def _execute_sell(self, row, reason='strategy'):
        symbol = self._get_symbol(row)
        pos = self.broker.get_position(symbol)
        if pos and pos.quantity > 0:
            self.broker.place_order(symbol, 'sell', pos.quantity, row['close'])

    def _check_stop_loss(self, row) -> bool:
        symbol = self._get_symbol(row)
        pos = self.broker.get_position(symbol)
        if pos and pos.avg_price > 0:
            pnl_pct = (row['close'] - pos.avg_price) / pos.avg_price
            return pnl_pct <= self.stop_loss
        return False

    def _check_take_profit(self, row) -> bool:
        symbol = self._get_symbol(row)
        pos = self.broker.get_position(symbol)
        if pos and pos.avg_price > 0:
            pnl_pct = (row['close'] - pos.avg_price) / pos.avg_price
            return pnl_pct >= self.take_profit
        return False

    def _liquidate_position(self, row):
        """最后一天平仓所有持仓"""
        for symbol, pos in list(self.broker.positions.items()):
            if pos.quantity > 0:
                self.broker.place_order(symbol, 'sell', pos.quantity, row['close'])

    def _get_results_df(self) -> pd.DataFrame:
        """生成回测结果DataFrame"""
        df = pd.DataFrame(self.portfolio_history)
        df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)
        return df

    def get_trades(self) -> pd.DataFrame:
        """获取交易记录"""
        if not self.broker.trade_history:
            return pd.DataFrame()
        return pd.DataFrame(self.broker.trade_history)

    def evaluate(self) -> Dict[str, Any]:
        """计算绩效指标"""
        df = self._get_results_df()
        if len(df) == 0:
            return {}

        initial = self.config.get('backtest', {}).get('initial_capital', 100000.0)
        final = df['total_assets'].iloc[-1]

        # 收益率
        total_return = (final - initial) / initial * 100
        years = (df.index[-1] - df.index[0]).days / 365.25
        annual_return = ((1 + total_return/100) ** (1/years) - 1) * 100 if years > 0 else 0

        # 最大回撤
        df['cummax'] = df['total_assets'].cummax()
        df['drawdown'] = (df['total_assets'] - df['cummax']) / df['cummax']
        max_drawdown = df['drawdown'].min() * 100

        # 夏普比率（无风险利率假设2%）
        df['daily_return'] = df['total_assets'].pct_change().fillna(0)
        excess_returns = df['daily_return'] - 0.02/252
        sharpe = excess_returns.mean() / excess_returns.std() * (252 ** 0.5) if excess_returns.std() > 0 else 0

        # 交易次数
        trades_df = self.get_trades()
        total_trades = len(trades_df) if not trades_df.empty else 0

        # 胜率
        if total_trades > 0 and 'pnl' in trades_df.columns:
            winning = (trades_df['pnl'] > 0).sum()
            win_rate = winning / total_trades * 100
        else:
            win_rate = 0

        return {
            'total_return_pct': total_return,
            'annual_return_pct': annual_return,
            'max_drawdown_pct': max_drawdown,
            'sharpe_ratio': sharpe,
            'total_trades': total_trades,
            'win_rate_pct': win_rate,
            'final_assets': final,
            'start_date': df.index[0].strftime('%Y-%m-%d'),
            'end_date': df.index[-1].strftime('%Y-%m-%d')
        }
