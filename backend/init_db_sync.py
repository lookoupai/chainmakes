"""
同步数据库初始化脚本
创建所有表并添加测试用户
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from passlib.context import CryptContext

from app.config import settings
from app.db.base import Base
from app.models.user import User
from app.models.exchange_account import ExchangeAccount
from app.models.bot_instance import BotInstance
from app.models.order import Order
from app.models.position import Position
from app.models.trade_log import TradeLog
from app.models.spread_history import SpreadHistory

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def init_database():
    """初始化数据库"""
    print("开始创建数据库表...")
    
    # 使用同步引擎
    engine = create_engine(settings.DATABASE_URL, echo=True)
    
    # 创建所有表
    Base.metadata.create_all(bind=engine)
    
    print("数据库表创建完成!")
    
    # 创建测试用户
    with Session(engine) as session:
        # 检查是否已存在测试用户
        existing_user = session.query(User).filter(User.username == "admin").first()
        
        if not existing_user:
            # 创建管理员用户
            admin_user = User(
                username="admin",
                email="admin@example.com",
                password_hash=pwd_context.hash("admin123"),
                role="admin",
                is_active=True
            )
            session.add(admin_user)
            
            # 创建普通测试用户
            test_user = User(
                username="testuser",
                email="test@example.com",
                password_hash=pwd_context.hash("test123"),
                role="user",
                is_active=True
            )
            session.add(test_user)
            
            session.commit()
            print("\n测试用户创建成功:")
            print("  管理员 - 用户名: admin, 密码: admin123")
            print("  测试用户 - 用户名: testuser, 密码: test123")
        else:
            print("\n测试用户已存在,跳过创建")
    
    print("\n数据库初始化完成!")


if __name__ == "__main__":
    init_database()