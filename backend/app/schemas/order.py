"""
订单相关的Pydantic模型
"""
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from decimal import Decimal
from typing import Optional


class OrderBase(BaseModel):
    """订单基础模型"""
    symbol: str = Field(..., description="交易对")
    side: str = Field(..., description="交易方向: buy/sell")
    order_type: str = Field(..., description="订单类型: market/limit")
    amount: Decimal = Field(..., gt=0, description="订单数量")
    price: Optional[Decimal] = Field(None, description="订单价格")


class OrderCreate(OrderBase):
    """订单创建模型"""
    bot_instance_id: int = Field(..., description="机器人实例ID")
    cycle_number: int = Field(..., description="循环编号")
    dca_level: int = Field(default=1, ge=1, description="DCA层级")


class OrderUpdate(BaseModel):
    """订单更新模型"""
    status: Optional[str] = Field(None, description="订单状态")
    filled_amount: Optional[Decimal] = Field(None, description="已成交数量")
    cost: Optional[Decimal] = Field(None, description="成交金额")
    filled_at: Optional[datetime] = Field(None, description="成交时间")


class OrderResponse(OrderBase):
    """订单响应模型"""
    id: int
    bot_instance_id: int
    cycle_number: int
    exchange_order_id: Optional[str]
    status: str
    filled_amount: Decimal
    cost: Optional[Decimal]
    dca_level: int
    created_at: datetime
    updated_at: datetime
    filled_at: Optional[datetime]
    
    model_config = ConfigDict(from_attributes=True)