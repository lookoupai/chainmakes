"""
持仓相关的Pydantic模型
"""
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from decimal import Decimal
from typing import Optional


class PositionBase(BaseModel):
    """持仓基础模型"""
    symbol: str = Field(..., description="交易对")
    side: str = Field(..., description="持仓方向: long/short")
    amount: Decimal = Field(..., gt=0, description="持仓数量")
    entry_price: Decimal = Field(..., gt=0, description="开仓均价")


class PositionResponse(PositionBase):
    """持仓响应模型"""
    id: int
    bot_instance_id: int
    cycle_number: int
    current_price: Optional[Decimal]
    unrealized_pnl: Optional[Decimal]
    is_open: bool
    created_at: datetime
    updated_at: datetime
    closed_at: Optional[datetime]
    
    model_config = ConfigDict(from_attributes=True)