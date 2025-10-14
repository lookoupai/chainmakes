"""
交易机器人实例数据模型
"""
from sqlalchemy import String, Boolean, DateTime, ForeignKey, Integer, DECIMAL, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from decimal import Decimal
from typing import List, Dict, Any, TYPE_CHECKING

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.exchange_account import ExchangeAccount
    from app.models.order import Order
    from app.models.position import Position
    from app.models.trade_log import TradeLog
    from app.models.spread_history import SpreadHistory


class BotInstance(Base):
    """交易机器人实例模型"""
    __tablename__ = "bot_instances"
    
    # 主键
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    # 外键
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    exchange_account_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("exchange_accounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # 基本配置
    bot_name: Mapped[str] = mapped_column(String(100), nullable=False)
    
    # 市场配置
    market1_symbol: Mapped[str] = mapped_column(String(50), nullable=False)  # 例如: GALA-USDT
    market2_symbol: Mapped[str] = mapped_column(String(50), nullable=False)  # 例如: CHZ-USDT
    market1_start_price: Mapped[Decimal] = mapped_column(DECIMAL(18, 8), nullable=True)  # 开始价格
    market2_start_price: Mapped[Decimal] = mapped_column(DECIMAL(18, 8), nullable=True)  # 开始价格
    
    start_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)  # 统计开始时间(UTC)
    leverage: Mapped[int] = mapped_column(Integer, default=10, nullable=False)
    
    # 交易配置
    order_type_open: Mapped[str] = mapped_column(String(20), default="market", nullable=False)  # market, limit
    order_type_close: Mapped[str] = mapped_column(String(20), default="market", nullable=False)
    investment_per_order: Mapped[Decimal] = mapped_column(DECIMAL(18, 8), nullable=False)  # 每单投资额
    max_position_value: Mapped[Decimal] = mapped_column(DECIMAL(18, 8), nullable=False)  # 最大持仓面值
    
    # DCA配置
    max_dca_times: Mapped[int] = mapped_column(Integer, default=6, nullable=False)  # 最大加仓次数
    dca_config: Mapped[Dict[str, Any]] = mapped_column(
        JSON, 
        nullable=False,
        default=list
    )  # [{times: 1, spread: 1.0, multiplier: 1.0}, ...]
    
    # 止盈止损配置
    profit_mode: Mapped[str] = mapped_column(
        String(20), 
        default="position", 
        nullable=False
    )  # regression, position
    profit_ratio: Mapped[Decimal] = mapped_column(DECIMAL(10, 4), default=Decimal("1.0"), nullable=False)  # 止盈比例(%)
    stop_loss_ratio: Mapped[Decimal] = mapped_column(DECIMAL(10, 4), default=Decimal("10.0"), nullable=False)  # 止损比例(%)
    
    # 开仓方向配置
    reverse_opening: Mapped[bool] = mapped_column(
        Boolean, 
        default=False, 
        nullable=False
    )  # False=正向开仓(价差回归), True=反向开仓(价差扩大)
    
    # 状态控制
    status: Mapped[str] = mapped_column(
        String(20), 
        default="stopped", 
        nullable=False,
        index=True
    )  # running, paused, stopped
    pause_after_close: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)  # 平仓后暂停
    
    # 运行数据
    current_cycle: Mapped[int] = mapped_column(Integer, default=0, nullable=False)  # 当前循环次数
    current_dca_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)  # 当前加仓次数
    total_profit: Mapped[Decimal] = mapped_column(DECIMAL(18, 8), default=Decimal("0"), nullable=False)  # 总收益
    total_trades: Mapped[int] = mapped_column(Integer, default=0, nullable=False)  # 总交易次数
    
    # 价差记录
    last_trade_spread: Mapped[Decimal | None] = mapped_column(DECIMAL(10, 4), nullable=True)  # 上次成交价差
    first_trade_spread: Mapped[Decimal | None] = mapped_column(DECIMAL(10, 4), nullable=True)  # 第一次成交价差
    
    # 时间戳
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
    
    # 关系
    user: Mapped["User"] = relationship("User", back_populates="bot_instances")
    exchange_account: Mapped["ExchangeAccount"] = relationship("ExchangeAccount", back_populates="bot_instances")
    
    orders: Mapped[List["Order"]] = relationship(
        "Order",
        back_populates="bot_instance",
        cascade="all, delete-orphan"
    )
    
    positions: Mapped[List["Position"]] = relationship(
        "Position",
        back_populates="bot_instance",
        cascade="all, delete-orphan"
    )
    
    trade_logs: Mapped[List["TradeLog"]] = relationship(
        "TradeLog",
        back_populates="bot_instance",
        cascade="all, delete-orphan"
    )
    
    spread_history: Mapped[List["SpreadHistory"]] = relationship(
        "SpreadHistory",
        back_populates="bot_instance",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<BotInstance(id={self.id}, name='{self.bot_name}', status='{self.status}')>"