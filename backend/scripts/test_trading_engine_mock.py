import asyncio
import sys
import os
from datetime import datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.session import AsyncSessionLocal
from app.models.bot_instance import BotInstance
from app.models.exchange_account import ExchangeAccount
from app.core.bot_engine import BotEngine
from app.exchanges.base_exchange import BaseExchange
from app.utils.logger import setup_logger
from sqlalchemy import select

logger = setup_logger('test_trading_engine_mock')

class MockExchange(BaseExchange):
    """模拟交易所类"""
    
    def __init__(self, api_key: str, api_secret: str, passphrase: str = None):
        self.api_key = api_key
        self.api_secret = api_secret
        self.passphrase = passphrase
        self.connected = False
    
    async def _init_exchange(self):
        """初始化交易所"""
        self.connected = True
        logger.info("模拟交易所初始化成功")
    
    async def connect(self):
        """连接交易所"""
        await self._init_exchange()
        logger.info("模拟交易所连接成功")
    
    async def close(self):
        """关闭连接"""
        self.connected = False
        logger.info("模拟交易所连接关闭")
    
    async def get_ticker(self, symbol: str) -> dict:
        """获取市场价格"""
        # 返回模拟价格
        base_price = Decimal("50000.00")
        if "BTC" in symbol:
            # 添加一些随机波动
            variation = Decimal(str((hash(datetime.utcnow().isoformat()) % 1000) / 100000))
            price = base_price + variation
        else:
            price = Decimal("3000.00")
        
        return {
            "symbol": symbol,
            "last_price": price,
            "bid": price - Decimal("1.0"),
            "ask": price + Decimal("1.0")
        }
    
    async def create_market_order(self, symbol: str, side: str, amount: Decimal, reduce_only: bool = False) -> dict:
        """创建市价单"""
        # 返回模拟订单
        order_id = f"mock_order_{hash(datetime.utcnow().isoformat()) % 10000}"
        price = await self.get_ticker(symbol)
        
        return {
            "id": order_id,
            "symbol": symbol,
            "side": side,
            "type": "market",
            "amount": float(amount),
            "filled": float(amount),
            "price": float(price["last_price"]),
            "cost": float(amount * price["last_price"]),
            "status": "closed",
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def create_limit_order(self, symbol: str, side: str, amount: Decimal, price: Decimal, reduce_only: bool = False) -> dict:
        """创建限价单"""
        order_id = f"mock_limit_order_{hash(datetime.utcnow().isoformat()) % 10000}"
        return {
            "id": order_id,
            "symbol": symbol,
            "side": side,
            "type": "limit",
            "amount": float(amount),
            "filled": 0.0,
            "price": float(price),
            "cost": 0.0,
            "status": "open",
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def cancel_order(self, order_id: str, symbol: str) -> dict:
        """取消订单"""
        return {
            "id": order_id,
            "symbol": symbol,
            "status": "canceled",
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def get_order(self, order_id: str, symbol: str) -> dict:
        """获取订单信息"""
        return {
            "id": order_id,
            "symbol": symbol,
            "status": "closed",
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def get_balance(self) -> dict:
        """获取账户余额"""
        return {
            "USDT": {
                "free": 10000.0,
                "used": 0.0,
                "total": 10000.0
            },
            "BTC": {
                "free": 0.1,
                "used": 0.0,
                "total": 0.1
            }
        }
    
    async def get_position(self, symbol: str) -> dict:
        """获取持仓信息"""
        return {
            "symbol": symbol,
            "size": 0.0,
            "side": "long",
            "entry_price": 0.0,
            "mark_price": 0.0,
            "unrealized_pnl": 0.0
        }
    
    async def get_all_positions(self) -> list:
        """获取所有持仓"""
        return []
    
    async def set_leverage(self, symbol: str, leverage: int):
        """设置杠杆"""
        logger.info(f"模拟设置杠杆: {symbol} = {leverage}x")

async def test_bot_engine():
    """测试机器人引擎"""
    print("测试机器人引擎（使用模拟交易所）")
    
    async with AsyncSessionLocal() as db:
        # 获取测试机器人
        result = await db.execute(
            select(BotInstance).where(BotInstance.id == 3)
        )
        bot = result.scalar_one_or_none()
        
        if not bot:
            print("测试机器人不存在")
            return
        
        print(f"当前机器人状态: {bot.status}")
        print(f"机器人配置: {bot.bot_name}, 市场1: {bot.market1_symbol}, 市场2: {bot.market2_symbol}")
        
        # 创建模拟交易所
        mock_exchange = MockExchange("test_key", "test_secret")
        await mock_exchange.connect()
        
        # 创建机器人引擎
        engine = BotEngine(bot, mock_exchange, db)
        
        try:
            print("启动机器人引擎...")
            # 启动机器人任务
            task = asyncio.create_task(engine.start())
            
            # 让机器人运行10秒
            await asyncio.sleep(10)
            
            print("停止机器人引擎...")
            await engine.stop()
            
            # 等待任务完成
            try:
                await task
            except asyncio.CancelledError:
                print("机器人任务已取消")
            
            # 检查机器人状态
            await db.refresh(bot)
            print(f"测试后机器人状态: {bot.status}")
            print(f"总交易次数: {bot.total_trades}")
            print(f"当前循环: {bot.current_cycle}")
            
        except Exception as e:
            logger.error(f"测试过程中出错: {str(e)}", exc_info=True)
            print(f"测试过程中出错: {str(e)}")
        finally:
            await mock_exchange.close()

async def test_bot_engine_with_dca():
    """测试机器人引擎的DCA功能"""
    print("\n测试机器人引擎DCA功能")
    
    async with AsyncSessionLocal() as db:
        # 获取测试机器人
        result = await db.execute(
            select(BotInstance).where(BotInstance.id == 3)
        )
        bot = result.scalar_one_or_none()
        
        if not bot:
            print("测试机器人不存在")
            return
        
        # 修改机器人配置，添加DCA配置
        bot.dca_config = [
            {"spread": 0.5, "multiplier": 1.0},
            {"spread": 1.0, "multiplier": 2.0},
            {"spread": 1.5, "multiplier": 3.0}
        ]
        await db.commit()
        
        # 创建模拟交易所
        mock_exchange = MockExchange("test_key", "test_secret")
        await mock_exchange.connect()
        
        # 创建机器人引擎
        engine = BotEngine(bot, mock_exchange, db)
        
        try:
            print("启动机器人引擎（测试DCA）...")
            # 启动机器人任务
            task = asyncio.create_task(engine.start())
            
            # 让机器人运行15秒，可能有多次加仓
            await asyncio.sleep(15)
            
            print("停止机器人引擎...")
            await engine.stop()
            
            # 等待任务完成
            try:
                await task
            except asyncio.CancelledError:
                print("机器人任务已取消")
            
            # 检查机器人状态
            await db.refresh(bot)
            print(f"测试后机器人状态: {bot.status}")
            print(f"总交易次数: {bot.total_trades}")
            print(f"当前循环: {bot.current_cycle}")
            print(f"当前DCA次数: {bot.current_dca_count}")
            
        except Exception as e:
            logger.error(f"测试过程中出错: {str(e)}", exc_info=True)
            print(f"测试过程中出错: {str(e)}")
        finally:
            await mock_exchange.close()

async def main():
    """主测试函数"""
    print("开始测试交易引擎（使用模拟交易所）")
    print("=" * 50)
    
    try:
        # 测试基本机器人引擎功能
        await test_bot_engine()
        
        # 测试DCA功能
        await test_bot_engine_with_dca()
        
        print("\n" + "=" * 50)
        print("交易引擎测试完成")
        
    except Exception as e:
        logger.error(f"测试过程中出错: {str(e)}", exc_info=True)
        print(f"测试过程中出错: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())