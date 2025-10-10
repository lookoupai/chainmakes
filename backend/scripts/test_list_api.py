import sys
import os
import asyncio

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, func
from app.models.bot_instance import BotInstance

async def test_list_bots():
    # 创建异步引擎
    database_url = "sqlite+aiosqlite:///./trading_bot.db"
    engine = create_async_engine(database_url, echo=False)
    
    # 创建会话
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        # 模拟API查询
        user_id = 1
        page = 1
        page_size = 10
        
        # 构建查询
        query = select(BotInstance).where(BotInstance.user_id == user_id)
        
        # 获取总数
        count_result = await session.execute(
            select(func.count()).select_from(query.subquery())
        )
        total = count_result.scalar()
        
        print(f"Total bots for user_id={user_id}: {total}")
        
        # 应用分页和排序
        query = query.order_by(BotInstance.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)
        
        result = await session.execute(query)
        bots = result.scalars().all()
        
        print(f"\nBots returned: {len(bots)}")
        for bot in bots:
            print(f"  - ID: {bot.id}, Name: {bot.bot_name}, Status: {bot.status}")
            print(f"    Type of bot object: {type(bot)}")
            print(f"    Bot dict keys: {bot.__dict__.keys()}")
        
        # 测试响应格式
        response = {
            "items": bots,
            "total": total,
            "page": page,
            "page_size": page_size
        }
        
        print(f"\nResponse structure:")
        print(f"  items: {len(response['items'])} bots")
        print(f"  total: {response['total']}")
        print(f"  page: {response['page']}")
        print(f"  page_size: {response['page_size']}")

if __name__ == "__main__":
    asyncio.run(test_list_bots())