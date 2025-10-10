"""
数据库初始化脚本
用于创建所有数据表和初始化测试用户
"""
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from app.config import settings
from app.db.base import Base
from app.models.user import User
from app.utils.security import get_password_hash


async def init_database():
    """初始化数据库表结构"""
    print("创建数据库引擎...")
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=True,
    )
    
    print("创建所有数据表...")
    async with engine.begin() as conn:
        # 删除所有表(开发环境)
        if settings.ENVIRONMENT == "development":
            await conn.run_sync(Base.metadata.drop_all)
        
        # 创建所有表
        await conn.run_sync(Base.metadata.create_all)
    
    print("✅ 数据库表创建成功!")
    
    # 创建测试用户
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
    AsyncSessionLocal = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    
    async with AsyncSessionLocal() as session:
        # 检查是否已存在管理员用户
        from sqlalchemy import select
        result = await session.execute(select(User).where(User.username == "admin"))
        existing_user = result.scalar_one_or_none()
        
        if not existing_user:
            print("\n创建测试管理员用户...")
            admin_user = User(
                username="admin",
                email="admin@example.com",
                password_hash=get_password_hash("admin123"),
                role="admin",
                is_active=True
            )
            session.add(admin_user)
            await session.commit()
            print("✅ 测试用户创建成功!")
            print("   用户名: admin")
            print("   密码: admin123")
        else:
            print("\n⚠️  管理员用户已存在,跳过创建")
    
    await engine.dispose()


if __name__ == "__main__":
    print("=" * 50)
    print("开始初始化数据库...")
    print("=" * 50)
    asyncio.run(init_database())
    print("\n" + "=" * 50)
    print("数据库初始化完成!")
    print("=" * 50)