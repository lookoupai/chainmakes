"""
交易日志数据模型
"""
from sqlalchemy import String, DateTime, ForeignKey, Integer, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from typing import Dict, Any, TYPE_CHECKING

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.bot_instance import BotInstance


class TradeLog(Base):
    """交易日志模型"""
    __tablename__ = "trade_logs"
    
    # 主键
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    # 外键
    bot_instance_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("bot_instances.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # 日志信息
    log_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # info, warning, error, trade
    message: Mapped[str] = mapped_column(Text, nullable=False)  # 日志消息
    details: Mapped[Dict[str, Any] | None] = mapped_column(JSON, nullable=True)  # 额外详细信息
    
    # 时间戳
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # 关系
    bot_instance: Mapped["BotInstance"] = relationship("BotInstance", back_populates="trade_logs")
    
    def __repr__(self) -> str:
        return f"<TradeLog(id={self.id}, type='{self.log_type}', message='{self.message[:50]}...')>"