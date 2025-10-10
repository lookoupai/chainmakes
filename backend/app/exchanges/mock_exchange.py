"""
模拟交易所实现 - 用于测试和演示
"""
import asyncio
import random
from decimal import Decimal
from typing import Dict, List, Optional, Any
from datetime import datetime

from app.exchanges.base_exchange import BaseExchange
from app.utils.logger import setup_logger

logger = setup_logger('mock_exchange')


class MockExchange(BaseExchange):
    """模拟交易所实现"""
    
    def __init__(self, api_key: str, api_secret: str, passphrase: Optional[str] = None):
        """
        初始化模拟交易所
        
        Args:
            api_key: API密钥(仅用于标识)
            api_secret: API密钥(仅用于标识)
            passphrase: API密码(仅用于标识)
        """
        super().__init__(api_key, api_secret, passphrase)
        # 模拟市场价格数据
        self.market_prices = {
            'BTC-USDT': Decimal('40000'),
            'ETH-USDT': Decimal('3000'),
            'BNB-USDT': Decimal('300'),
            'ADA-USDT': Decimal('1.5'),
            'SOL-USDT': Decimal('100')
        }
        
        # 模拟持仓数据
        self.positions = {}
        
        # 模拟订单计数器
        self.order_counter = 10000
        
        # 模拟订单记录
        self.orders = {}
    
    def _init_exchange(self):
        """初始化交易所实例(模拟交易所不需要)"""
        return None
    
    async def get_ticker(self, symbol: str) -> Dict[str, Any]:
        """
        获取模拟行情数据
        
        Args:
            symbol: 交易对符号
            
        Returns:
            模拟行情数据
        """
        # 模拟价格波动
        if symbol not in self.market_prices:
            self.market_prices[symbol] = Decimal(str(random.uniform(10, 50000)))
        
        base_price = self.market_prices[symbol]
        # 添加随机波动(-10%到+10%) - 增大波动范围以便触发交易
        change_percent = Decimal(str(random.uniform(-0.10, 0.10)))
        new_price = base_price * (Decimal('1') + change_percent)
        self.market_prices[symbol] = new_price
        
        # 生成买卖价差
        spread = new_price * Decimal('0.0001')  # 0.01%价差
        bid = new_price - spread
        ask = new_price + spread
        
        return {
            'symbol': symbol,
            'last_price': new_price,
            'bid': bid,
            'ask': ask,
            'volume': Decimal(str(random.uniform(100, 10000))),
            'timestamp': int(datetime.now().timestamp() * 1000)
        }
    
    async def create_market_order(
        self,
        symbol: str,
        side: str,
        amount: Decimal,
        reduce_only: bool = False
    ) -> Dict[str, Any]:
        """
        创建模拟市价订单
        
        Args:
            symbol: 交易对符号
            side: 交易方向(buy/sell)
            amount: 订单数量
            reduce_only: 是否仅减仓
            
        Returns:
            模拟订单信息
        """
        # 生成订单ID
        order_id = f"mock_order_{self.order_counter}"
        self.order_counter += 1
        
        # 获取当前价格
        ticker = await self.get_ticker(symbol)
        price = ticker['ask'] if side == 'buy' else ticker['bid']
        
        # 计算成交金额
        cost = price * amount
        
        # 模拟订单完全成交
        order = {
            'id': order_id,
            'symbol': symbol,
            'type': 'market',
            'side': side,
            'price': price,
            'amount': amount,
            'filled': amount,
            'remaining': Decimal('0'),
            'cost': cost,
            'status': 'closed',
            'timestamp': int(datetime.now().timestamp() * 1000)
        }
        
        # 保存订单记录
        self.orders[order_id] = order
        
        # 更新持仓
        await self._update_position(symbol, side, amount, price, reduce_only)
        
        logger.info(f"创建模拟市价订单成功: {symbol} {side} {amount} @ {price}")
        return order
    
    async def create_limit_order(
        self,
        symbol: str,
        side: str,
        amount: Decimal,
        price: Decimal,
        reduce_only: bool = False
    ) -> Dict[str, Any]:
        """
        创建模拟限价订单
        
        Args:
            symbol: 交易对符号
            side: 交易方向
            amount: 订单数量
            price: 订单价格
            reduce_only: 是否仅减仓
            
        Returns:
            模拟订单信息
        """
        # 生成订单ID
        order_id = f"mock_limit_order_{self.order_counter}"
        self.order_counter += 1
        
        # 创建订单
        order = {
            'id': order_id,
            'symbol': symbol,
            'type': 'limit',
            'side': side,
            'price': price,
            'amount': amount,
            'filled': Decimal('0'),
            'remaining': amount,
            'cost': Decimal('0'),
            'status': 'open',
            'timestamp': int(datetime.now().timestamp() * 1000)
        }
        
        # 保存订单记录
        self.orders[order_id] = order
        
        # 模拟订单可能立即成交
        ticker = await self.get_ticker(symbol)
        market_price = ticker['last_price']
        
        should_fill = False
        if side == 'buy' and price >= market_price:
            should_fill = True
        elif side == 'sell' and price <= market_price:
            should_fill = True
        
        if should_fill:
            # 模拟立即成交
            order['filled'] = amount
            order['remaining'] = Decimal('0')
            order['cost'] = price * amount
            order['status'] = 'closed'
            
            # 更新持仓
            await self._update_position(symbol, side, amount, price, reduce_only)
        
        logger.info(f"创建模拟限价订单成功: {symbol} {side} {amount} @ {price}")
        return order
    
    async def cancel_order(self, order_id: str, symbol: str) -> Dict[str, Any]:
        """取消模拟订单"""
        if order_id not in self.orders:
            raise ValueError(f"订单不存在: {order_id}")
        
        order = self.orders[order_id]
        if order['status'] == 'closed':
            raise ValueError(f"订单已完成，无法取消: {order_id}")
        
        order['status'] = 'canceled'
        logger.info(f"取消模拟订单成功: {order_id}")
        return order
    
    async def get_order(self, order_id: str, symbol: str) -> Dict[str, Any]:
        """查询模拟订单状态"""
        if order_id not in self.orders:
            raise ValueError(f"订单不存在: {order_id}")
        
        return self.orders[order_id]
    
    async def get_position(self, symbol: str) -> Optional[Dict[str, Any]]:
        """获取指定交易对的模拟持仓"""
        if symbol not in self.positions:
            return None
        
        position = self.positions[symbol]
        if position['amount'] == 0:
            return None
        
        # 更新当前价格和未实现盈亏
        ticker = await self.get_ticker(symbol)
        current_price = ticker['last_price']
        
        if position['side'] == 'long':
            unrealized_pnl = (current_price - position['entry_price']) * position['amount']
        else:
            unrealized_pnl = (position['entry_price'] - current_price) * position['amount']
        
        position['current_price'] = current_price
        position['unrealized_pnl'] = unrealized_pnl
        
        return position.copy()
    
    async def get_all_positions(self) -> List[Dict[str, Any]]:
        """获取所有模拟持仓"""
        all_positions = []
        
        for symbol in list(self.positions.keys()):
            position = await self.get_position(symbol)
            if position:
                all_positions.append(position)
        
        return all_positions
    
    async def set_leverage(self, symbol: str, leverage: int) -> Dict[str, Any]:
        """设置模拟杠杆倍数"""
        logger.info(f"设置模拟杠杆成功: {symbol} {leverage}x")
        return {'symbol': symbol, 'leverage': leverage, 'status': 'success'}
    
    async def get_balance(self) -> Dict[str, Any]:
        """获取模拟账户余额"""
        return {
            'total': {'USDT': Decimal('10000')},
            'free': {'USDT': Decimal('8000')},
            'used': {'USDT': Decimal('2000')}
        }
    
    async def _update_position(
        self,
        symbol: str,
        side: str,
        amount: Decimal,
        price: Decimal,
        reduce_only: bool
    ):
        """更新模拟持仓"""
        if symbol not in self.positions:
            self.positions[symbol] = {
                'symbol': symbol,
                'side': side,
                'amount': Decimal('0'),
                'entry_price': price,
                'current_price': price,
                'unrealized_pnl': Decimal('0'),
                'leverage': 1
            }
        
        position = self.positions[symbol]
        
        if reduce_only:
            # 减仓操作
            if position['side'] != side:
                # 方向相反，减少持仓
                position['amount'] -= amount
                if position['amount'] <= 0:
                    position['amount'] = Decimal('0')
        else:
            # 开仓或加仓
            if position['amount'] == 0:
                # 新开仓
                position['side'] = side
                position['amount'] = amount
                position['entry_price'] = price
            elif position['side'] == side:
                # 同向加仓，计算新的平均价格
                old_amount = position['amount']
                old_cost = old_amount * position['entry_price']
                new_cost = amount * price
                total_amount = old_amount + amount
                total_cost = old_cost + new_cost
                
                position['amount'] = total_amount
                position['entry_price'] = total_cost / total_amount
            else:
                # 反向交易，减少持仓
                position['amount'] -= amount
                if position['amount'] <= 0:
                    position['amount'] = Decimal('0')
        
        # 更新当前价格
        position['current_price'] = price
    
    async def fetch_historical_price(
        self,
        symbol: str,
        timestamp: int
    ) -> Optional[Decimal]:
        """
        获取指定时间点的模拟历史价格
        
        Args:
            symbol: 交易对符号
            timestamp: 时间戳(毫秒)
            
        Returns:
            模拟的历史价格
        """
        try:
            # 模拟交易所：基于当前价格生成历史价格
            # 假设历史价格比当前价格低10%-20%（模拟价格上涨趋势）
            if symbol not in self.market_prices:
                self.market_prices[symbol] = Decimal(str(random.uniform(10, 50000)))
            
            current_price = self.market_prices[symbol]
            # 生成一个比当前价低的历史价格
            historical_multiplier = Decimal(str(random.uniform(0.80, 0.90)))
            historical_price = current_price * historical_multiplier
            
            logger.info(
                f"生成模拟历史价格: {symbol} @ {timestamp} = {historical_price} "
                f"(当前价: {current_price})"
            )
            return historical_price
            
        except Exception as e:
            logger.error(f"获取模拟历史价格失败 {symbol}: {str(e)}")
            return None