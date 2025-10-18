"""
交易所工厂类 - 用于创建不同交易所的实例
"""
from typing import Optional
from app.exchanges.base_exchange import BaseExchange
from app.exchanges.okx_exchange import OKXExchange
from app.exchanges.binance_exchange import BinanceExchange
from app.exchanges.mock_exchange import MockExchange
from app.utils.logger import setup_logger
from app.config import settings  # 导入配置

logger = setup_logger('exchange_factory')


class ExchangeFactory:
    """交易所工厂类"""
    
    # 支持的交易所映射
    EXCHANGES = {
        'okx': OKXExchange,
        'binance': BinanceExchange,
        'mock': MockExchange,  # 模拟交易所，用于测试
        # 'bybit': BybitExchange,      # 待实现
    }
    
    @staticmethod
    def create(
        exchange_name: str,
        api_key: str,
        api_secret: str,
        passphrase: Optional[str] = None,
        proxy: Optional[str] = None,
        is_testnet: Optional[bool] = None
    ) -> BaseExchange:
        """
        创建交易所实例
        
        Args:
            exchange_name: 交易所名称(okx/binance/bybit)
            api_key: API密钥
            api_secret: API密钥
            passphrase: API密码(某些交易所需要)
            proxy: 代理服务器地址(可选，默认从配置读取)
            is_testnet: 是否使用测试网(可选，默认从配置读取)
            
        Returns:
            交易所实例
            
        Raises:
            ValueError: 不支持的交易所
        """
        exchange_name = exchange_name.lower()
        
        if exchange_name not in ExchangeFactory.EXCHANGES:
            supported = ', '.join(ExchangeFactory.EXCHANGES.keys())
            raise ValueError(
                f"不支持的交易所: {exchange_name}. "
                f"支持的交易所: {supported}"
            )
        
        exchange_class = ExchangeFactory.EXCHANGES[exchange_name]
        logger.info(f"创建{exchange_name}交易所实例")
        
        # 对于不同交易所，传入不同的参数
        kwargs = {
            'api_key': api_key,
            'api_secret': api_secret,
            'passphrase': passphrase
        }
        
        if exchange_name == 'okx':
            # OKX 需要代理和测试网配置
            if proxy is None:
                proxy = settings.OKX_PROXY
            if is_testnet is None:
                is_testnet = settings.OKX_IS_DEMO
            
            kwargs['proxy'] = proxy
            kwargs['is_testnet'] = is_testnet
            
            logger.info(f"OKX 配置: proxy={'已配置' if proxy else '未配置'}, testnet={is_testnet}")
        
        elif exchange_name == 'binance':
            # Binance 只需要测试网配置，不需要 passphrase
            if is_testnet is None:
                is_testnet = True  # 默认使用测试网
            
            kwargs['is_testnet'] = is_testnet
            kwargs.pop('passphrase', None)  # Binance不需要passphrase
            
            logger.info(f"Binance 配置: testnet={is_testnet}")
        
        return exchange_class(**kwargs)
    
    @staticmethod
    def get_supported_exchanges() -> list[str]:
        """获取支持的交易所列表"""
        return list(ExchangeFactory.EXCHANGES.keys())