"""
交易订单数据模型
"""
from sqlalchemy import String, DateTime, ForeignKey, Integer, DECIMAL
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.bot_instance import BotInstance


class Order(Base):
    """交易订单模型"""
    __tablename__ = "orders"
    
    # 主键
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    # 外键
    bot_instance_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("bot_instances.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # 循环信息
    cycle_number: Mapped[int] = mapped_column(Integer, nullable=False, index=True)  # 循环编号
    
    # 订单信息
    exchange_order_id: Mapped[str | None] = mapped_column(String(100), nullable=True)  # 交易所返回的订单ID
    symbol: Mapped[str] = mapped_column(String(50), nullable=False)  # 交易对
    side: Mapped[str] = mapped_column(String(10), nullable=False)  # buy, sell
    order_type: Mapped[str] = mapped_column(String(20), nullable=False)  # market, limit
    
    # 价格和数量
    price: Mapped[Decimal | None] = mapped_column(DECIMAL(18, 8), nullable=True)  # 订单价格
    amount: Mapped[Decimal] = mapped_column(DECIMAL(18, 8), nullable=False)  # 订单数量
    filled_amount: Mapped[Decimal] = mapped_column(DECIMAL(18, 8), default=Decimal("0"), nullable=False)  # 已成交数量
    cost: Mapped[Decimal | None] = mapped_column(DECIMAL(18, 8), nullable=True)  # 成交金额
    
    # 订单状态
    status: Mapped[str] = mapped_column(
        String(20), 
        default="pending", 
        nullable=False,
        index=True
    )  # pending, open, closed, canceled
    dca_level: Mapped[int] = mapped_column(Integer, default=1, nullable=False)  # 第几次加仓
    
    # 时间戳
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
    filled_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)  # 成交时间
    
    # 关系
    bot_instance: Mapped["BotInstance"] = relationship("BotInstance", back_populates="orders")
    
    def __repr__(self) -> str:
        return f"<Order(id={self.id}, symbol='{self.symbol}', side='{self.side}', status='{self.status}')>"