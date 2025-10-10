import sys
import os
import asyncio
import json

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, func
from app.models.bot_instance import BotInstance
from app.schemas.bot import BotResponse

async def test_api_response():
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
        
        # 应用分页和排序
        query = query.order_by(BotInstance.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)
        
        result = await session.execute(query)
        bots = result.scalars().all()
        
        # 将ORM对象转换为BotResponse
        bot_responses = [BotResponse.model_validate(bot) for bot in bots]
        
        # 构建响应
        response = {
            "items": bot_responses,
            "total": total,
            "page": page,
            "page_size": page_size
        }
        
        # 序列化为JSON (模拟FastAPI的响应)
        from pydantic import TypeAdapter
        
        # 将Pydantic模型转换为dict
        response_dict = {
            "items": [bot.model_dump() for bot in bot_responses],
            "total": total,
            "page": page,
            "page_size": page_size
        }
        
        json_str = json.dumps(response_dict, indent=2, default=str)
        
        print("API Response JSON:")
        print(json_str)
        print("\n" + "="*80)
        print(f"Total items: {len(response_dict['items'])}")
        print(f"First item keys: {list(response_dict['items'][0].keys()) if response_dict['items'] else 'N/A'}")

if __name__ == "__main__":
    asyncio.run(test_api_response())