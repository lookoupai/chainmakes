"""
Binance交易所适配器实现
"""
import ccxt.async_support as ccxt
import asyncio
from typing import Dict, List, Optional, Any
from decimal import Decimal

from app.exchanges.base_exchange import BaseExchange
from app.utils.logger import setup_logger

logger = setup_logger('binance_exchange')


class BinanceExchange(BaseExchange):
    """Binance交易所适配器"""
    
    def __init__(self, api_key: str, api_secret: str, passphrase: Optional[str] = None, is_testnet: bool = True):
        """
        初始化Binance交易所
        
        Args:
            api_key: API密钥
            api_secret: API密钥
            passphrase: API密码（Binance不需要，保留参数是为了接口统一）
            is_testnet: 是否使用测试网
        """
        self.is_testnet = is_testnet
        super().__init__(api_key, api_secret, passphrase)
    
    def _init_exchange(self) -> ccxt.Exchange:
        """初始化Binance交易所实例"""
        config = {
            'apiKey': self.api_key,
            'secret': self.api_secret,
            'enableRateLimit': True,
            'options': {
                'defaultType': 'future',  # 使用USDT永续合约
                'adjustForTimeDifference': True,  # 自动调整时间差
            }
        }
        
        # 设置测试网/真实网
        if self.is_testnet:
            config['sandbox'] = True
            logger.info("✅ 使用 Binance 测试网环境 (sandbox mode)")
        else:
            logger.info("⚠️ 使用 Binance 真实交易环境")
        
        return ccxt.binance(config)
    
    async def get_ticker(self, symbol: str) -> Dict[str, Any]:
        """
        获取Binance行情数据

        Args:
            symbol: 交易对符号(例如: BTC/USDT)

        Returns:
            行情数据
        """
        try:
            ticker = await self.exchange.fetch_ticker(symbol)
            return {
                'symbol': symbol,
                'last_price': Decimal(str(ticker['last'])),
                'bid': Decimal(str(ticker['bid'])) if ticker['bid'] else None,
                'ask': Decimal(str(ticker['ask'])) if ticker['ask'] else None,
                'volume': Decimal(str(ticker['baseVolume'])) if ticker['baseVolume'] else None,
                'timestamp': ticker['timestamp']
            }
        except Exception as e:
            logger.error(f"获取行情失败 {symbol}: {str(e)}")
            raise
    
    async def create_market_order(
        self,
        symbol: str,
        side: str,
        amount: Decimal,
        reduce_only: bool = False
    ) -> Dict[str, Any]:
        """
        创建市价订单

        Args:
            symbol: 交易对符号
            side: 交易方向(buy/sell)
            amount: 订单数量
            reduce_only: 是否仅减仓
        """
        try:
            params = {}
            if reduce_only:
                params['reduceOnly'] = True
            
            order = await self.exchange.create_order(
                symbol=symbol,
                type='market',
                side=side,
                amount=float(amount),
                params=params
            )
            
            logger.info(f"创建市价订单成功: {symbol} {side} {amount}")
            logger.debug(f"Binance 返回订单数据: {order}")
            return self._format_order(order)
        except Exception as e:
            logger.error(f"创建市价订单失败 {symbol}: {str(e)}")
            raise
    
    async def create_limit_order(
        self,
        symbol: str,
        side: str,
        amount: Decimal,
        price: Decimal,
        reduce_only: bool = False
    ) -> Dict[str, Any]:
        """创建限价订单"""
        try:
            params = {}
            if reduce_only:
                params['reduceOnly'] = True
            
            order = await self.exchange.create_order(
                symbol=symbol,
                type='limit',
                side=side,
                amount=float(amount),
                price=float(price),
                params=params
            )
            
            logger.info(f"创建限价订单成功: {symbol} {side} {amount} @ {price}")
            return self._format_order(order)
        except Exception as e:
            logger.error(f"创建限价订单失败 {symbol}: {str(e)}")
            raise
    
    async def cancel_order(self, order_id: str, symbol: str) -> Dict[str, Any]:
        """取消订单"""
        try:
            result = await self.exchange.cancel_order(order_id, symbol)
            logger.info(f"取消订单成功: {order_id}")
            return result
        except Exception as e:
            logger.error(f"取消订单失败 {order_id}: {str(e)}")
            raise
    
    async def get_order(self, order_id: str, symbol: str) -> Dict[str, Any]:
        """查询订单状态"""
        try:
            order = await self.exchange.fetch_order(order_id, symbol)
            return self._format_order(order)
        except Exception as e:
            logger.error(f"查询订单失败 {order_id}: {str(e)}")
            raise
    
    async def get_position(self, symbol: str) -> Optional[Dict[str, Any]]:
        """获取指定交易对的持仓"""
        try:
            positions = await self.exchange.fetch_positions([symbol])
            if not positions:
                return None
            
            # Binance可能返回多个持仓（多空双向持仓模式）
            for position in positions:
                if float(position.get('contracts', 0)) > 0:
                    return self._format_position(position)
            
            return None
        except Exception as e:
            logger.error(f"获取持仓失败 {symbol}: {str(e)}")
            raise
    
    async def get_all_positions(self) -> List[Dict[str, Any]]:
        """获取所有持仓"""
        try:
            positions = await self.exchange.fetch_positions()
            return [
                self._format_position(pos)
                for pos in positions
                if float(pos.get('contracts', 0)) > 0
            ]
        except Exception as e:
            logger.error(f"获取所有持仓失败: {str(e)}")
            raise
    
    async def set_leverage(self, symbol: str, leverage: int) -> Dict[str, Any]:
        """设置杠杆倍数"""
        try:
            result = await self.exchange.set_leverage(leverage, symbol)
            logger.info(f"设置杠杆成功: {symbol} {leverage}x")
            return result
        except Exception as e:
            logger.error(f"设置杠杆失败 {symbol}: {str(e)}")
            raise
    
    async def get_balance(self) -> Dict[str, Any]:
        """获取账户余额"""
        try:
            balance = await self.exchange.fetch_balance()
            return {
                'total': balance.get('total', {}),
                'free': balance.get('free', {}),
                'used': balance.get('used', {})
            }
        except Exception as e:
            logger.error(f"获取余额失败: {str(e)}")
            raise
    
    async def fetch_historical_price(
        self,
        symbol: str,
        timestamp: int
    ) -> Optional[Decimal]:
        """
        获取指定时间点的历史价格

        Args:
            symbol: 交易对符号(例如: BTC/USDT)
            timestamp: 时间戳(毫秒)

        Returns:
            该时间点的收盘价,如果无法获取则返回None
        """
        try:
            # 使用5分钟K线，获取目标时间附近的数据
            ohlcv = await self.exchange.fetch_ohlcv(
                symbol=symbol,
                timeframe='5m',
                since=timestamp - 300000,  # 提前5分钟开始获取
                limit=5
            )
            
            if not ohlcv:
                logger.warning(f"无法获取历史K线数据: {symbol} @ {timestamp}")
                return None
            
            # 找到最接近目标时间的K线
            closest_candle = None
            min_time_diff = float('inf')
            
            for candle in ohlcv:
                candle_time = candle[0]
                time_diff = abs(candle_time - timestamp)
                
                if time_diff < min_time_diff:
                    min_time_diff = time_diff
                    closest_candle = candle
            
            if closest_candle:
                close_price = Decimal(str(closest_candle[4]))
                logger.info(
                    f"获取历史价格成功: {symbol} @ {timestamp} = {close_price} "
                    f"(时间差: {min_time_diff/1000:.0f}秒)"
                )
                return close_price
            
            logger.warning(f"未找到合适的历史K线: {symbol} @ {timestamp}")
            return None
            
        except Exception as e:
            logger.error(f"获取历史价格失败 {symbol} @ {timestamp}: {str(e)}")
            return None
    
    def _format_order(self, order: Dict) -> Dict[str, Any]:
        """格式化订单数据"""
        def safe_decimal(value, default=None):
            """安全转换为 Decimal"""
            if value is None or value == '':
                return default
            try:
                return Decimal(str(value))
            except (ValueError, TypeError, Exception) as e:
                logger.warning(f"Decimal 转换失败: {value} -> {e}")
                return default
        
        return {
            'id': order['id'],
            'symbol': order['symbol'],
            'type': order['type'],
            'side': order['side'],
            'price': safe_decimal(order.get('price')),
            'amount': safe_decimal(order.get('amount'), Decimal('0')),
            'filled': safe_decimal(order.get('filled'), Decimal('0')),
            'remaining': safe_decimal(order.get('remaining'), Decimal('0')),
            'cost': safe_decimal(order.get('cost')),
            'status': order['status'],
            'timestamp': order['timestamp']
        }
    
    def _format_position(self, position: Dict) -> Dict[str, Any]:
        """格式化持仓数据"""
        side = 'long' if position['side'] == 'long' else 'short'
        
        # 获取当前价格
        current_price = position.get('markPrice') or position.get('lastPrice') or position.get('entryPrice', 0)
        
        return {
            'symbol': position['symbol'],
            'side': side,
            'amount': Decimal(str(position['contracts'])),
            'entry_price': Decimal(str(position['entryPrice'])),
            'current_price': Decimal(str(current_price)) if current_price else None,
            'unrealized_pnl': Decimal(str(position.get('unrealizedPnl', 0))),
            'liquidation_price': Decimal(str(position.get('liquidationPrice', 0))) if position.get('liquidationPrice') else None,
            'leverage': position.get('leverage'),
            'percentage': Decimal(str(position.get('percentage', 0)))
        }
