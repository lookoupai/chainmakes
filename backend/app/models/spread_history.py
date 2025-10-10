"""
价差历史记录数据模型
"""
from sqlalchemy import DateTime, ForeignKey, Integer, DECIMAL, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.bot_instance import BotInstance


class SpreadHistory(Base):
    """价差历史记录模型 - 用于分析和图表展示"""
    __tablename__ = "spread_history"
    
    # 主键
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    # 外键
    bot_instance_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("bot_instances.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # 价格数据
    market1_price: Mapped[Decimal] = mapped_column(DECIMAL(18, 8), nullable=False)
    market2_price: Mapped[Decimal] = mapped_column(DECIMAL(18, 8), nullable=False)
    spread_percentage: Mapped[Decimal] = mapped_column(DECIMAL(10, 4), nullable=False)  # 价差百分比
    
    # 时间戳
    recorded_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    
    # 关系
    bot_instance: Mapped["BotInstance"] = relationship("BotInstance", back_populates="spread_history")
    
    # 复合索引
    __table_args__ = (
        Index('idx_bot_time', 'bot_instance_id', 'recorded_at'),
    )
    
    def __repr__(self) -> str:
        return f"<SpreadHistory(id={self.id}, bot_id={self.bot_instance_id}, spread={self.spread_percentage}%)>"