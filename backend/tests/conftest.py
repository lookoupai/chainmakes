"""
pytest配置文件
"""
import asyncio
import pytest
from typing import AsyncGenerator, Generator
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.db.base import Base
from app.db.session import get_db
from app.core.config import settings

# 测试数据库URL
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test_trading_bot.db"

# 创建测试数据库引擎
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False
)

# 创建测试会话
TestSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=test_engine,
    class_=AsyncSession
)


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """创建事件循环"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """创建测试数据库会话"""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with TestSessionLocal() as session:
        yield session
    
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """创建测试客户端"""
    app.dependency_overrides[get_db] = lambda: db_session
    
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
    
    app.dependency_overrides.clear()


@pytest.fixture
async def test_user(db_session: AsyncSession):
    """创建测试用户"""
    from app.models.user import User
    from app.core.security import get_password_hash
    
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password=get_password_hash("testpassword"),
        is_active=True,
        is_superuser=False
    )
    
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    
    return user


@pytest.fixture
async def test_exchange(db_session: AsyncSession):
    """创建测试交易所"""
    from app.models.exchange import Exchange
    
    exchange = Exchange(
        name="Test Exchange",
        exchange_type="mock",
        api_key="test_api_key",
        api_secret="test_api_secret",
        is_active=True
    )
    
    db_session.add(exchange)
    await db_session.commit()
    await db_session.refresh(exchange)
    
    return exchange


@pytest.fixture
async def test_bot(db_session: AsyncSession, test_user, test_exchange):
    """创建测试机器人"""
    from app.models.bot import Bot
    from datetime import datetime
    
    bot = Bot(
        name="Test Bot",
        symbol="BTC/USDT",
        base_exchange_id=test_exchange.id,
        quote_exchange_id=test_exchange.id,
        strategy_type="spread",
        min_spread_threshold=0.01,
        max_spread_threshold=0.05,
        trade_amount=100.0,
        dca_enabled=True,
        dca_multiplier=1.5,
        dca_max_orders=5,
        dca_spread_threshold=0.02,
        is_active=True,
        owner_id=test_user.id,
        created_at=datetime.utcnow()
    )
    
    db_session.add(bot)
    await db_session.commit()
    await db_session.refresh(bot)
    
    return bot


@pytest.fixture
async def auth_headers(test_user):
    """创建认证头"""
    from app.core.security import create_access_token
    
    access_token = create_access_token(
        data={"sub": test_user.username}
    )
    
    return {"Authorization": f"Bearer {access_token}"}