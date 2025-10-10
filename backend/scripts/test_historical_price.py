"""
测试历史价格获取功能
"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime, timedelta, timezone

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.exchanges.okx_exchange import OKXExchange
from app.exchanges.mock_exchange import MockExchange
from app.config import get_settings
from app.utils.logger import setup_logger

logger = setup_logger('test_historical_price')


async def test_okx_historical_price():
    """测试 OKX 交易所历史价格获取"""
    logger.info("=" * 60)
    logger.info("测试 OKX 交易所历史价格获取")
    logger.info("=" * 60)
    
    try:
        settings = get_settings()
        
        # 初始化 OKX 交易所
        exchange = OKXExchange(
            api_key=settings.OKX_API_KEY,
            api_secret=settings.OKX_API_SECRET,
            passphrase=settings.OKX_PASSPHRASE,
            is_testnet=settings.OKX_IS_DEMO,
            proxy=settings.OKX_PROXY
        )
        
        # 测试不同的时间点
        test_cases = [
            {
                "name": "1小时前",
                "time": datetime.now(timezone.utc) - timedelta(hours=1),
                "symbol": "BTC-USDT-SWAP"
            },
            {
                "name": "6小时前",
                "time": datetime.now(timezone.utc) - timedelta(hours=6),
                "symbol": "BTC-USDT-SWAP"
            },
            {
                "name": "1天前",
                "time": datetime.now(timezone.utc) - timedelta(days=1),
                "symbol": "ETH-USDT-SWAP"
            },
            {
                "name": "7天前",
                "time": datetime.now(timezone.utc) - timedelta(days=7),
                "symbol": "BTC-USDT-SWAP"
            }
        ]
        
        for test in test_cases:
            logger.info(f"\n测试场景: {test['name']}")
            logger.info(f"交易对: {test['symbol']}")
            logger.info(f"目标时间: {test['time']}")
            
            timestamp_ms = int(test['time'].timestamp() * 1000)
            
            # 获取历史价格
            price = await exchange.fetch_historical_price(
                test['symbol'],
                timestamp_ms
            )
            
            if price:
                logger.info(f"✅ 成功获取历史价格: {price}")
            else:
                logger.error(f"❌ 获取历史价格失败")
        
        # 获取当前价格作为对比
        logger.info("\n获取当前价格作为对比:")
        ticker = await exchange.get_ticker("BTC-USDT-SWAP")
        logger.info(f"当前 BTC 价格: {ticker['last_price']}")
        
        await exchange.close()
        logger.info("\n✅ OKX 测试完成")
        
    except Exception as e:
        logger.error(f"❌ OKX 测试失败: {str(e)}", exc_info=True)


async def test_mock_historical_price():
    """测试模拟交易所历史价格获取"""
    logger.info("\n" + "=" * 60)
    logger.info("测试模拟交易所历史价格获取")
    logger.info("=" * 60)
    
    try:
        # 初始化模拟交易所
        exchange = MockExchange(
            api_key="mock_key",
            api_secret="mock_secret"
        )
        
        # 测试场景
        test_time = datetime.now(timezone.utc) - timedelta(days=1)
        timestamp_ms = int(test_time.timestamp() * 1000)
        
        logger.info(f"目标时间: {test_time}")
        
        # 获取历史价格
        btc_price = await exchange.fetch_historical_price(
            "BTC-USDT",
            timestamp_ms
        )
        
        eth_price = await exchange.fetch_historical_price(
            "ETH-USDT",
            timestamp_ms
        )
        
        logger.info(f"模拟 BTC 历史价格: {btc_price}")
        logger.info(f"模拟 ETH 历史价格: {eth_price}")
        
        # 获取当前价格
        btc_ticker = await exchange.get_ticker("BTC-USDT")
        eth_ticker = await exchange.get_ticker("ETH-USDT")
        
        logger.info(f"当前 BTC 价格: {btc_ticker['last_price']}")
        logger.info(f"当前 ETH 价格: {eth_ticker['last_price']}")
        
        logger.info("✅ 模拟交易所测试完成")
        
    except Exception as e:
        logger.error(f"❌ 模拟交易所测试失败: {str(e)}", exc_info=True)


async def main():
    """主测试函数"""
    logger.info("开始测试历史价格获取功能\n")
    
    # 测试 OKX
    await test_okx_historical_price()
    
    # 等待一下
    await asyncio.sleep(2)
    
    # 测试模拟交易所
    await test_mock_historical_price()
    
    logger.info("\n" + "=" * 60)
    logger.info("所有测试完成")
    logger.info("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())