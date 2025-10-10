"""
OKX交易所适配器实现
"""
import ccxt.async_support as ccxt
import asyncio
from typing import Dict, List, Optional, Any, Callable
from decimal import Decimal
from functools import wraps

from app.exchanges.base_exchange import BaseExchange
from app.utils.logger import setup_logger

logger = setup_logger('okx_exchange')


def retry_on_network_error(max_retries: int = 3, base_delay: float = 1.0):
    """
    网络错误重试装饰器 - 使用指数退避策略

    Args:
        max_retries: 最大重试次数
        base_delay: 基础延迟时间（秒）
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except (
                    ccxt.NetworkError,
                    ccxt.ExchangeNotAvailable,
                    ccxt.RequestTimeout,
                ) as e:
                    last_exception = e

                    if attempt < max_retries:
                        # 指数退避：1s, 2s, 4s, 8s...
                        delay = base_delay * (2 ** attempt)
                        logger.warning(
                            f"网络请求失败 (尝试 {attempt + 1}/{max_retries + 1}): {str(e)}, "
                            f"{delay:.1f}秒后重试..."
                        )
                        await asyncio.sleep(delay)
                    else:
                        logger.error(
                            f"网络请求失败，已重试 {max_retries} 次: {str(e)}"
                        )
                except Exception as e:
                    # 其他类型的错误直接抛出，不重试
                    logger.error(f"请求失败（非网络错误）: {str(e)}")
                    raise

            # 所有重试都失败了，抛出最后一次的异常
            raise last_exception

        return wrapper
    return decorator


class OKXExchange(BaseExchange):
    """OKX交易所适配器"""
    
    def __init__(self, api_key: str, api_secret: str, passphrase: str, is_testnet: bool = True, proxy: str = None):
        """
        初始化OKX交易所
        
        Args:
            api_key: API密钥
            api_secret: API密钥
            passphrase: API密码
            is_testnet: 是否使用模拟盘（True=模拟盘，False=真实盘）
            proxy: 代理服务器地址（例如: "http://127.0.0.1:7890" 或 "socks5://127.0.0.1:1080"）
        """
        self.is_testnet = is_testnet
        self.proxy = proxy
        super().__init__(api_key, api_secret, passphrase)
    
    def _init_exchange(self) -> ccxt.Exchange:
        """初始化OKX交易所实例"""
        config = {
            'apiKey': self.api_key,
            'secret': self.api_secret,
            'password': self.passphrase,
            'enableRateLimit': True,
            'options': {
                'defaultType': 'swap',  # 永续合约
                'createMarketBuyOrderRequiresPrice': False,
            }
        }
        
        # 配置代理（如果提供）
        # CCXT 需要使用 aiohttp 格式的代理配置
        if self.proxy:
            # 记录代理配置，便于调试
            logger.info(f"使用代理: {self.proxy}")
            config['aiohttp_proxy'] = self.proxy
            config['proxies'] = {
                'http': self.proxy,
                'https': self.proxy,
            }
        
        # 设置模拟盘/真实盘
        if self.is_testnet:
            # OKX 模拟盘配置
            # CCXT 会自动将 API 请求路由到模拟盘端点
            config['sandbox'] = True  # 这是关键参数
            logger.info("✅ 使用 OKX 模拟盘环境 (sandbox mode)")
        else:
            logger.info("⚠️ 使用 OKX 真实盘环境")
        
        return ccxt.okx(config)
    
    @retry_on_network_error(max_retries=3, base_delay=1.0)
    async def get_ticker(self, symbol: str) -> Dict[str, Any]:
        """
        获取OKX行情数据

        Args:
            symbol: 交易对符号(例如: BTC-USDT)

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
    
    @retry_on_network_error(max_retries=3, base_delay=1.0)
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
                # 平仓时的持仓方向与交易方向相反
                params['posSide'] = 'short' if side == 'buy' else 'long'
            else:
                # 开仓时的持仓方向与交易方向一致
                params['posSide'] = 'long' if side == 'buy' else 'short'

            order = await self.exchange.create_order(
                symbol=symbol,
                type='market',
                side=side,
                amount=float(amount),
                params=params
            )

            logger.info(f"创建市价订单成功: {symbol} {side} {amount} posSide={params['posSide']}")
            logger.debug(f"OKX 返回订单数据: {order}")
            return self._format_order(order)
        except Exception as e:
            logger.error(f"创建市价订单失败 {symbol}: {str(e)}")
            raise
    
    @retry_on_network_error(max_retries=3, base_delay=1.0)
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
                # 平仓时的持仓方向与交易方向相反
                params['posSide'] = 'short' if side == 'buy' else 'long'
            else:
                # 开仓时的持仓方向与交易方向一致
                params['posSide'] = 'long' if side == 'buy' else 'short'

            order = await self.exchange.create_order(
                symbol=symbol,
                type='limit',
                side=side,
                amount=float(amount),
                price=float(price),
                params=params
            )

            logger.info(f"创建限价订单成功: {symbol} {side} {amount} @ {price} posSide={params['posSide']}")
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
    
    @retry_on_network_error(max_retries=3, base_delay=1.0)
    async def get_position(self, symbol: str) -> Optional[Dict[str, Any]]:
        """获取指定交易对的持仓"""
        try:
            positions = await self.exchange.fetch_positions([symbol])
            if not positions:
                return None

            position = positions[0]
            if float(position.get('contracts', 0)) == 0:
                return None

            return self._format_position(position)
        except Exception as e:
            logger.error(f"获取持仓失败 {symbol}: {str(e)}")
            raise
    
    @retry_on_network_error(max_retries=3, base_delay=1.0)
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
    
    @retry_on_network_error(max_retries=2, base_delay=0.5)
    async def set_leverage(self, symbol: str, leverage: int) -> Dict[str, Any]:
        """设置杠杆倍数"""
        try:
            result = await self.exchange.set_leverage(
                leverage,
                symbol,
                params={'mgnMode': 'cross'}  # 全仓模式
            )
            logger.info(f"设置杠杆成功: {symbol} {leverage}x")
            return result
        except Exception as e:
            logger.error(f"设置杠杆失败 {symbol}: {str(e)}")
            raise
    
    @retry_on_network_error(max_retries=3, base_delay=1.0)
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

        # 获取当前价格，优先使用 markPrice，其次 lastPrice，最后使用 entryPrice
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
    
    @retry_on_network_error(max_retries=2, base_delay=1.0)
    async def fetch_historical_price(
        self,
        symbol: str,
        timestamp: int
    ) -> Optional[Decimal]:
        """
        获取指定时间点的历史价格

        Args:
            symbol: 交易对符号(例如: BTC-USDT-SWAP)
            timestamp: 时间戳(毫秒)

        Returns:
            该时间点的收盘价,如果无法获取则返回None
        """
        try:
            # CCXT fetch_ohlcv 参数:
            # symbol: 交易对
            # timeframe: K线周期 (1m, 5m, 15m, 1h, 1d等)
            # since: 起始时间戳(毫秒)
            # limit: 返回的K线数量

            # 使用5分钟K线，获取目标时间附近的数据
            ohlcv = await self.exchange.fetch_ohlcv(
                symbol=symbol,
                timeframe='5m',
                since=timestamp - 300000,  # 提前5分钟开始获取
                limit=5  # 获取5根K线
            )

            if not ohlcv:
                logger.warning(f"无法获取历史K线数据: {symbol} @ {timestamp}")
                return None

            # OHLCV 格式: [timestamp, open, high, low, close, volume]
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
                close_price = Decimal(str(closest_candle[4]))  # 收盘价
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