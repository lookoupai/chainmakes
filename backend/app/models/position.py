"""
持仓记录数据模型
"""
from sqlalchemy import String, Boolean, DateTime, ForeignKey, Integer, DECIMAL
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.bot_instance import BotInstance


class Position(Base):
    """持仓记录模型"""
    __tablename__ = "positions"
    
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
    cycle_number: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    
    # 持仓信息
    symbol: Mapped[str] = mapped_column(String(50), nullable=False)  # 交易对
    side: Mapped[str] = mapped_column(String(10), nullable=False)  # long, short
    amount: Mapped[Decimal] = mapped_column(DECIMAL(18, 8), nullable=False)  # 持仓数量
    entry_price: Mapped[Decimal] = mapped_column(DECIMAL(18, 8), nullable=False)  # 开仓均价
    current_price: Mapped[Decimal | None] = mapped_column(DECIMAL(18, 8), nullable=True)  # 当前价格
    unrealized_pnl: Mapped[Decimal | None] = mapped_column(DECIMAL(18, 8), nullable=True)  # 未实现盈亏
    
    # 状态
    is_open: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    
    # 时间戳
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
    closed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    
    # 关系
    bot_instance: Mapped["BotInstance"] = relationship("BotInstance", back_populates="positions")
    
    def __repr__(self) -> str:
        return f"<Position(id={self.id}, symbol='{self.symbol}', side='{self.side}', is_open={self.is_open})>"