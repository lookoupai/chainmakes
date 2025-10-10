"""
价差历史相关的Pydantic模型
"""
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from decimal import Decimal


class SpreadHistoryResponse(BaseModel):
    """价差历史响应模型"""
    id: int
    bot_instance_id: int
    market1_price: Decimal = Field(..., description="市场1价格")
    market2_price: Decimal = Field(..., description="市场2价格")
    spread_percentage: Decimal = Field(..., description="价差百分比")
    recorded_at: datetime = Field(..., description="记录时间")

    model_config = ConfigDict(from_attributes=True)
