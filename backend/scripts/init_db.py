"""
数据库初始化脚本
创建初始数据库和管理员账户
"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.config import settings
from app.db.base import Base
from app.models import User
from app.core.security import get_password_hash


async def init_database():
    """初始化数据库"""
    print("正在连接数据库...")
    
    # 创建数据库引擎
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=True,
    )
    
    # 创建所有表
    print("正在创建数据表...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    print("数据表创建完成!")
    
    # 创建管理员账户
    print("正在创建管理员账户...")
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        # 检查管理员是否已存在
        from sqlalchemy import select
        result = await session.execute(
            select(User).where(User.username == "admin")
        )
        admin = result.scalar_one_or_none()
        
        if not admin:
            # 创建管理员
            admin = User(
                username="admin",
                email="admin@example.com",
                password_hash=get_password_hash("admin123"),
                role="admin",
                is_active=True
            )
            session.add(admin)
            await session.commit()
            print("管理员账户创建成功!")
            print("用户名: admin")
            print("密码: admin123")
            print("⚠️  请在生产环境中立即修改默认密码!")
        else:
            print("管理员账户已存在,跳过创建")
    
    await engine.dispose()
    print("\n数据库初始化完成!")


if __name__ == "__main__":
    asyncio.run(init_database())