"""
模拟券商/交易所接口
处理订单执行、持仓管理、资金结算
"""
import pandas as pd
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional
from enum import Enum

class OrderStatus(Enum):
    PENDING = "pending"
    FILLED = "filled"
    CANCELLED = "cancelled"

@dataclass
class Order:
    symbol: str
    side: str  # 'buy' or 'sell'
    quantity: int
    price: float
    status: OrderStatus = OrderStatus.PENDING
    fill_price: float = 0.0
    timestamp: datetime = None

    def fill(self, price: float):
        self.fill_price = price
        self.status = OrderStatus.FILLED
        self.timestamp = datetime.now()

@dataclass
class Position:
    symbol: str
    quantity: int
    avg_price: float
    current_price: float = 0.0

    @property
    def market_value(self) -> float:
        return self.quantity * self.current_price

    @property
    def unrealized_pnl(self) -> float:
        return (self.current_price - self.avg_price) * self.quantity

class SimulatedBroker:
    """模拟券商"""
    def __init__(self, initial_capital: float = 100000.0, config: dict = None):
        self.initial_capital = initial_capital
        self.cash = initial_capital
        self.positions: dict[str, Position] = {}  # symbol -> Position
        self.orders: List[Order] = []
        self.trade_history: List[dict] = []
        self.config = config or {}
        self.commission_rate = config.get('commission_rate', 0.0003)
        self.stamp_tax_rate = config.get('stamp_tax_rate', 0.001)
        self.slippage = config.get('slippage', 0.001)

    def place_order(self, symbol: str, side: str, quantity: int, price: float) -> Order:
        """下单（市价单，立即成交）"""
        # 滑点
        fill_price = price * (1 + self.slippage) if side == 'buy' else price * (1 - self.slippage)

        order = Order(symbol=symbol, side=side, quantity=quantity, price=price)
        order.fill(fill_price)

        # 执行交易
        cost = quantity * fill_price
        commission = cost * self.commission_rate

        if side == 'buy':
            # 检查现金
            total_cost = cost + commission
            if total_cost > self.cash:
                order.status = OrderStatus.CANCELLED
                return order
            self.cash -= total_cost
            # 增加/开仓持仓
            if symbol in self.positions:
                pos = self.positions[symbol]
                total_qty = pos.quantity + quantity
                total_cost_basis = pos.avg_price * pos.quantity + fill_price * quantity
                pos.avg_price = total_cost_basis / total_qty
                pos.quantity = total_qty
            else:
                self.positions[symbol] = Position(
                    symbol=symbol,
                    quantity=quantity,
                    avg_price=fill_price
                )
        else:  # sell
            # 检查持仓
            if symbol not in self.positions or self.positions[symbol].quantity < quantity:
                order.status = OrderStatus.CANCELLED
                return order
            self.cash += cost - commission  # 印花税只在卖出收
            pos = self.positions[symbol]
            avg_price = pos.avg_price  # 保存平均成本用于计算盈亏
            pos.quantity -= quantity
            if pos.quantity == 0:
                del self.positions[symbol]

        # 记录交易
        if side == 'sell':
            # 计算已实现盈亏（使用保存的avg_price）
            pnl = (fill_price - avg_price) * quantity
        else:
            pnl = 0  # 买入交易无盈亏

        trade = {
            'timestamp': order.timestamp,
            'symbol': symbol,
            'side': side,
            'quantity': quantity,
            'price': fill_price,
            'commission': commission,
            'pnl': pnl
        }
        self.trade_history.append(trade)
        self.orders.append(order)
        return order

    def get_position(self, symbol: str) -> Optional[Position]:
        return self.positions.get(symbol)

    def get_portfolio_value(self, current_prices: dict) -> float:
        """计算总资产（现金 + 持仓市值）"""
        position_value = sum(
            pos.quantity * current_prices.get(pos.symbol, pos.current_price)
            for pos in self.positions.values()
        )
        return self.cash + position_value

    def update_prices(self, price_dict: dict):
        """更新持仓的当前价格"""
        for pos in self.positions.values():
            if pos.symbol in price_dict:
                pos.current_price = price_dict[pos.symbol]
