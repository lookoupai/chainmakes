"""
交易所抽象基类
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from decimal import Decimal
import ccxt.async_support as ccxt


class BaseExchange(ABC):
    """
    交易所抽象基类
    
    所有交易所适配器都需要继承此类并实现抽象方法
    """
    
    def __init__(self, api_key: str, api_secret: str, passphrase: Optional[str] = None):
        """
        初始化交易所
        
        Args:
            api_key: API密钥
            api_secret: API密钥
            passphrase: API密码(某些交易所需要,如OKX)
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.passphrase = passphrase
        self.exchange = self._init_exchange()
    
    @abstractmethod
    def _init_exchange(self) -> ccxt.Exchange:
        """
        初始化CCXT交易所实例
        
        Returns:
            CCXT交易所对象
        """
        pass
    
    @abstractmethod
    async def get_ticker(self, symbol: str) -> Dict[str, Any]:
        """
        获取行情数据
        
        Args:
            symbol: 交易对符号(例如: BTC-USDT)
            
        Returns:
            行情数据字典,包含:
            - symbol: 交易对
            - last_price: 最新价格
            - timestamp: 时间戳
            - bid: 买一价
            - ask: 卖一价
            - volume: 24小时交易量
        """
        pass
    
    @abstractmethod
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
            reduce_only: 是否仅减仓(平仓)
            
        Returns:
            订单信息字典
        """
        pass
    
    @abstractmethod
    async def create_limit_order(
        self,
        symbol: str,
        side: str,
        amount: Decimal,
        price: Decimal,
        reduce_only: bool = False
    ) -> Dict[str, Any]:
        """
        创建限价订单
        
        Args:
            symbol: 交易对符号
            side: 交易方向(buy/sell)
            amount: 订单数量
            price: 订单价格
            reduce_only: 是否仅减仓
            
        Returns:
            订单信息字典
        """
        pass
    
    @abstractmethod
    async def cancel_order(self, order_id: str, symbol: str) -> Dict[str, Any]:
        """
        取消订单
        
        Args:
            order_id: 订单ID
            symbol: 交易对符号
            
        Returns:
            取消结果
        """
        pass
    
    @abstractmethod
    async def get_order(self, order_id: str, symbol: str) -> Dict[str, Any]:
        """
        查询订单状态
        
        Args:
            order_id: 订单ID
            symbol: 交易对符号
            
        Returns:
            订单详细信息
        """
        pass
    
    @abstractmethod
    async def get_position(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        获取持仓信息
        
        Args:
            symbol: 交易对符号
            
        Returns:
            持仓信息字典,如果没有持仓返回None
            包含:
            - symbol: 交易对
            - side: 持仓方向(long/short)
            - amount: 持仓数量
            - entry_price: 开仓均价
            - unrealized_pnl: 未实现盈亏
            - liquidation_price: 强平价格
        """
        pass
    
    @abstractmethod
    async def get_all_positions(self) -> List[Dict[str, Any]]:
        """
        获取所有持仓
        
        Returns:
            持仓列表
        """
        pass
    
    @abstractmethod
    async def set_leverage(self, symbol: str, leverage: int) -> Dict[str, Any]:
        """
        设置杠杆倍数
        
        Args:
            symbol: 交易对符号
            leverage: 杠杆倍数
            
        Returns:
            设置结果
        """
        pass
    
    @abstractmethod
    async def get_balance(self) -> Dict[str, Any]:
        """
        获取账户余额
        
        Returns:
            余额信息字典
        """
        pass
    
    @abstractmethod
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
        pass
    
    async def close(self):
        """关闭交易所连接"""
        if self.exchange:
            await self.exchange.close()
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器退出"""
        await self.close()