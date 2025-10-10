"""
用户数据模型
"""
from sqlalchemy import String, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from typing import List

from app.db.base import Base


class User(Base):
    """用户模型"""
    __tablename__ = "users"
    
    # 主键
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    # 基本信息
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # 角色和状态
    role: Mapped[str] = mapped_column(String(20), default="user", nullable=False)  # admin, user
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # 时间戳
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=datetime.utcnow, 
        onupdate=datetime.utcnow, 
        nullable=False
    )
    
    # 关系
    exchange_accounts: Mapped[List["ExchangeAccount"]] = relationship(
        "ExchangeAccount",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    
    bot_instances: Mapped[List["BotInstance"]] = relationship(
        "BotInstance",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}')>"