"""
机器人相关的Pydantic模型
"""
from pydantic import BaseModel, Field, ConfigDict, field_validator
from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Dict, Any


class DCAConfigItem(BaseModel):
    """DCA配置项"""
    times: int = Field(..., ge=1, description="加仓次数")
    spread: Decimal = Field(..., ge=0, description="下单价差(%)")
    multiplier: Decimal = Field(..., ge=0, description="加仓倍投倍数")


class BotBase(BaseModel):
    """机器人基础模型"""
    bot_name: str = Field(..., min_length=1, max_length=100, description="机器人名称")
    market1_symbol: str = Field(..., description="市场1交易对", examples=["GALA-USDT"])
    market2_symbol: str = Field(..., description="市场2交易对", examples=["CHZ-USDT"])
    start_time: datetime = Field(..., description="统计开始时间(UTC)")
    leverage: int = Field(default=10, ge=1, le=125, description="杠杆倍数")


class BotCreate(BotBase):
    """机器人创建模型"""
    exchange_account_id: int = Field(..., description="交易所账户ID")
    
    # 交易配置
    order_type_open: str = Field(default="market", description="开仓订单类型")
    order_type_close: str = Field(default="market", description="平仓订单类型")
    investment_per_order: Decimal = Field(..., gt=0, description="每单投资额")
    max_position_value: Decimal = Field(..., gt=0, description="最大持仓面值")
    
    # DCA配置
    max_dca_times: int = Field(default=6, ge=1, le=20, description="最大加仓次数")
    dca_config: List[DCAConfigItem] = Field(..., description="DCA详细配置")
    
    # 止盈止损配置
    profit_mode: str = Field(default="position", description="止盈模式: regression/position")
    profit_ratio: Decimal = Field(default=Decimal("1.0"), description="止盈比例(%)")
    stop_loss_ratio: Decimal = Field(default=Decimal("10.0"), description="止损比例(%)")
    
    # 状态控制
    pause_after_close: bool = Field(default=True, description="平仓后暂停")
    
    @field_validator('profit_mode')
    @classmethod
    def validate_profit_mode(cls, v: str) -> str:
        if v not in ['regression', 'position']:
            raise ValueError('profit_mode必须是regression或position')
        return v
    
    @field_validator('order_type_open', 'order_type_close')
    @classmethod
    def validate_order_type(cls, v: str) -> str:
        if v not in ['market', 'limit']:
            raise ValueError('订单类型必须是market或limit')
        return v
    
    @field_validator('dca_config')
    @classmethod
    def validate_dca_config(cls, v: List[DCAConfigItem]) -> List[DCAConfigItem]:
        if not v:
            raise ValueError('DCA配置不能为空')
        # 检查times是否连续
        times_list = [item.times for item in v]
        expected_times = list(range(1, len(v) + 1))
        if times_list != expected_times:
            raise ValueError('DCA配置的times必须从1开始连续')
        return v


class BotUpdate(BaseModel):
    """机器人更新模型"""
    bot_name: Optional[str] = Field(None, min_length=1, max_length=100)
    investment_per_order: Optional[Decimal] = Field(None, gt=0)
    max_position_value: Optional[Decimal] = Field(None, gt=0)
    max_dca_times: Optional[int] = Field(None, ge=1, le=20)
    dca_config: Optional[List[DCAConfigItem]] = None
    profit_mode: Optional[str] = None
    profit_ratio: Optional[Decimal] = None
    stop_loss_ratio: Optional[Decimal] = None
    pause_after_close: Optional[bool] = None
    
    @field_validator('profit_mode')
    @classmethod
    def validate_profit_mode(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in ['regression', 'position']:
            raise ValueError('profit_mode必须是regression或position')
        return v


class BotResponse(BotBase):
    """机器人响应模型"""
    id: int
    user_id: int
    exchange_account_id: int
    order_type_open: str
    order_type_close: str
    investment_per_order: Decimal
    max_position_value: Decimal
    max_dca_times: int
    profit_mode: str
    profit_ratio: Decimal
    stop_loss_ratio: Decimal
    pause_after_close: bool
    status: str
    current_cycle: int
    current_dca_count: int
    total_profit: Decimal
    total_trades: int
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class BotDetailResponse(BotResponse):
    """机器人详细响应模型"""
    market1_start_price: Optional[Decimal]
    market2_start_price: Optional[Decimal]
    order_type_open: str
    order_type_close: str
    investment_per_order: Decimal
    max_position_value: Decimal
    max_dca_times: int
    dca_config: List[Dict[str, Any]]
    profit_mode: str
    profit_ratio: Decimal
    stop_loss_ratio: Decimal
    pause_after_close: bool
    current_dca_count: int
    last_trade_spread: Optional[Decimal]
    first_trade_spread: Optional[Decimal]
    
    model_config = ConfigDict(from_attributes=True)