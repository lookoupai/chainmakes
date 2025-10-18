"""
交易所账户相关的Pydantic模型
"""
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional


class ExchangeAccountBase(BaseModel):
    """交易所账户基础模型"""
    exchange_name: str = Field(..., description="交易所名称", examples=["okx", "binance", "bybit"])


class ExchangeAccountCreate(ExchangeAccountBase):
    """交易所账户创建模型"""
    api_key: str = Field(..., description="API密钥")
    api_secret: str = Field(..., description="API密钥")
    passphrase: Optional[str] = Field(None, description="API密码(OKX需要)")
    is_testnet: bool = Field(True, description="是否使用测试网/模拟盘(True=测试网, False=真实环境)")


class ExchangeAccountUpdate(BaseModel):
    """交易所账户更新模型"""
    api_key: Optional[str] = Field(None, description="API密钥")
    api_secret: Optional[str] = Field(None, description="API密钥")
    passphrase: Optional[str] = Field(None, description="API密码")
    is_active: Optional[bool] = Field(None, description="是否启用")
    is_testnet: Optional[bool] = Field(None, description="是否使用测试网/模拟盘")


class ExchangeAccountResponse(ExchangeAccountBase):
    """交易所账户响应模型"""
    id: int
    user_id: int
    is_active: bool
    is_testnet: bool
    created_at: datetime
    updated_at: datetime
    # 不返回敏感的API密钥信息
    
    model_config = ConfigDict(from_attributes=True)