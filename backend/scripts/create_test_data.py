"""
创建测试数据脚本
"""
import asyncio
import sys
import os
from datetime import datetime, timedelta
from random import uniform, randint, choice
from decimal import Decimal

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.session import AsyncSessionLocal
from app.models.user import User
from app.models.exchange_account import ExchangeAccount
from app.models.bot_instance import BotInstance
from app.models.order import Order
from app.models.position import Position
from app.utils.security import get_password_hash


async def create_test_user():
    """创建测试用户"""
    async with AsyncSessionLocal() as db:
        # 检查是否已存在测试用户
        from sqlalchemy import select
        result = await db.execute(select(User).where(User.username == "testuser"))
        existing_user = result.scalar_one_or_none()
        
        if existing_user:
            print("测试用户已存在")
            return existing_user
        
        # 创建新用户
        user = User(
            username="testuser",
            email="test@example.com",
            password_hash=get_password_hash("testpassword"),
            role="user",
            is_active=True
        )
        
        db.add(user)
        await db.commit()
        await db.refresh(user)
        
        print(f"创建测试用户: {user.username}")
        return user


async def create_test_exchange(user_id: int):
    """创建测试交易所"""
    async with AsyncSessionLocal() as db:
        # 检查是否已存在测试交易所
        from sqlalchemy import select
        result = await db.execute(select(ExchangeAccount).where(ExchangeAccount.exchange_name == "Test Exchange"))
        existing_exchange = result.scalar_one_or_none()
        
        if existing_exchange:
            print("测试交易所已存在")
            return existing_exchange
        
        # 创建新交易所
        exchange = ExchangeAccount(
            user_id=user_id,
            exchange_name="Test Exchange",
            api_key="test_api_key",
            api_secret="test_api_secret",
            is_active=True
        )
        
        db.add(exchange)
        await db.commit()
        await db.refresh(exchange)
        
        print(f"创建测试交易所: {exchange.exchange_name}")
        return exchange


async def create_test_bot(user_id: int, exchange_id: int):
    """创建测试机器人"""
    async with AsyncSessionLocal() as db:
        # 检查是否已存在测试机器人
        from sqlalchemy import select
        result = await db.execute(select(BotInstance).where(BotInstance.bot_name == "Test Bot"))
        existing_bot = result.scalar_one_or_none()
        
        if existing_bot:
            print("测试机器人已存在")
            return existing_bot
        
        # 创建新机器人
        bot = BotInstance(
            user_id=user_id,
            exchange_account_id=exchange_id,
            bot_name="Test Bot",
            market1_symbol="BTC/USDT",
            market2_symbol="BTC/USDT",
            start_time=datetime.utcnow(),
            leverage=1,
            order_type_open="market",
            order_type_close="market",
            investment_per_order=Decimal("100.0"),
            max_position_value=Decimal("1000.0"),
            max_dca_times=5,
            dca_config={},
            profit_mode="position",
            profit_ratio=Decimal("1.0"),
            stop_loss_ratio=Decimal("10.0"),
            status="stopped",
            pause_after_close=False,
            current_cycle=0,
            current_dca_count=0,
            total_profit=Decimal("0"),
            total_trades=0,
            created_at=datetime.utcnow()
        )
        
        db.add(bot)
        await db.commit()
        await db.refresh(bot)
        
        print(f"创建测试机器人: {bot.bot_name}")
        return bot


async def create_test_orders(bot_id: int, count: int = 10):
    """创建测试订单"""
    async with AsyncSessionLocal() as db:
        for i in range(count):
            # 生成随机订单数据
            side = choice(["buy", "sell"])
            order_type = choice(["market", "limit"])
            amount = round(uniform(0.001, 0.01), 6)
            price = round(uniform(45000, 55000), 2)
            filled = round(uniform(0, amount), 6)
            status = "closed" if filled >= amount else choice(["open", "partially_filled"])
            
            order = Order(
                bot_instance_id=bot_id,
                cycle_number=randint(1, 5),
                symbol="BTC/USDT",
                order_type=order_type,
                side=side,
                amount=Decimal(str(amount)),
                price=Decimal(str(price)) if order_type == "limit" else None,
                filled_amount=Decimal(str(filled)),
                status=status,
                created_at=datetime.utcnow() - timedelta(minutes=randint(1, 60))
            )
            
            db.add(order)
        
        await db.commit()
        print(f"创建 {count} 个测试订单")


async def create_test_positions(bot_id: int, count: int = 3):
    """创建测试持仓"""
    async with AsyncSessionLocal() as db:
        for i in range(count):
            # 生成随机持仓数据
            side = choice(["long", "short"])
            size = round(uniform(0.001, 0.01), 6)
            entry_price = round(uniform(45000, 55000), 2)
            mark_price = round(uniform(entry_price * 0.95, entry_price * 1.05), 2)
            unrealized_pnl = round((mark_price - entry_price) * size, 2)
            
            position = Position(
                bot_instance_id=bot_id,
                cycle_number=randint(1, 5),
                symbol="BTC/USDT",
                side=side,
                amount=Decimal(str(size)),
                entry_price=Decimal(str(entry_price)),
                current_price=Decimal(str(mark_price)),
                unrealized_pnl=Decimal(str(unrealized_pnl)),
                is_open=True,
                created_at=datetime.utcnow() - timedelta(hours=randint(1, 24)),
                updated_at=datetime.utcnow()
            )
            
            db.add(position)
        
        await db.commit()
        print(f"创建 {count} 个测试持仓")


async def main():
    """主函数"""
    print("开始创建测试数据...")
    
    # 创建测试用户
    user = await create_test_user()
    
    # 创建测试交易所
    exchange = await create_test_exchange(user.id)
    
    # 创建测试机器人
    bot = await create_test_bot(user.id, exchange.id)
    
    # 创建测试订单
    await create_test_orders(bot.id, 20)
    
    # 创建测试持仓
    await create_test_positions(bot.id, 5)
    
    print("测试数据创建完成!")
    print(f"测试用户: {user.username}")
    print(f"测试交易所: {exchange.exchange_name}")
    print(f"测试机器人: {bot.bot_name}")
    print(f"机器人ID: {bot.id}")


if __name__ == "__main__":
    asyncio.run(main())