"""
独立的数据库初始化脚本
不依赖app模块的自动导入,避免aiosqlite依赖问题
"""
import sys
import os
from pathlib import Path

# 添加backend目录到Python路径
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import create_engine, Column, Integer, String, Boolean, Float, DateTime, Text
from sqlalchemy.orm import Session, declarative_base
from passlib.context import CryptContext
from datetime import datetime

# 创建Base
Base = declarative_base()

# 定义User模型(简化版,仅用于初始化)
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), default="user")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def init_database():
    """初始化数据库"""
    print("开始创建数据库...")
    
    # 数据库文件路径
    db_path = backend_dir / "trading_bot.db"
    db_url = f"sqlite:///{db_path}"
    
    # 创建引擎
    engine = create_engine(db_url, echo=True)
    
    # 创建所有表
    Base.metadata.create_all(bind=engine)
    
    print("\n数据库表创建完成!")
    
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
            print("\n✓ 测试用户创建成功:")
            print("  → 管理员 - 用户名: admin, 密码: admin123")
            print("  → 测试用户 - 用户名: testuser, 密码: test123")
        else:
            print("\n✓ 测试用户已存在,跳过创建")
    
    print(f"\n✓ 数据库初始化完成! 数据库文件: {db_path}")


if __name__ == "__main__":
    init_database()