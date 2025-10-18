import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
import sys

sys.path.insert(0, '.')

from app.models.order import Order
from app.models.position import Position

async def check_data():
    engine = create_async_engine('sqlite+aiosqlite:///../trading_bot.db')
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # 查询最近的订单
        result = await session.execute(
            select(Order).order_by(Order.created_at.desc()).limit(10)
        )
        orders = result.scalars().all()
        
        print('最近10个订单:')
        for order in orders:
            print(f'ID={order.id}, Symbol={order.symbol}, Side={order.side}, DCA={order.dca_level}, Amount={order.amount}, Price={order.price}, Cost={order.cost}, Status={order.status}')
        
        print('\n最近的持仓记录:')
        result = await session.execute(
            select(Position).order_by(Position.created_at.desc()).limit(10)
        )
        positions = result.scalars().all()
        
        for pos in positions:
            print(f'ID={pos.id}, Symbol={pos.symbol}, Side={pos.side}, Amount={pos.amount}, Entry={pos.entry_price}, IsOpen={pos.is_open}')

asyncio.run(check_data())
