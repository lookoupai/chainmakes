"""
交易所账户数据模型
"""
from sqlalchemy import String, Boolean, DateTime, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from typing import List, TYPE_CHECKING

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.bot_instance import BotInstance


class ExchangeAccount(Base):
    """交易所账户模型"""
    __tablename__ = "exchange_accounts"
    
    # 主键
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    # 外键
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # 交易所信息
    exchange_name: Mapped[str] = mapped_column(String(50), nullable=False)  # okx, binance, bybit
    api_key: Mapped[str] = mapped_column(String(255), nullable=False)  # 加密存储
    api_secret: Mapped[str] = mapped_column(String(255), nullable=False)  # 加密存储
    passphrase: Mapped[str | None] = mapped_column(String(255), nullable=True)  # OKX需要,加密存储
    
    # 状态
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
    user: Mapped["User"] = relationship("User", back_populates="exchange_accounts")
    
    bot_instances: Mapped[List["BotInstance"]] = relationship(
        "BotInstance",
        back_populates="exchange_account",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<ExchangeAccount(id={self.id}, exchange='{self.exchange_name}', user_id={self.user_id})>"