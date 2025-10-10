"""
Pydantic数据验证模型模块
"""
from app.schemas.user import (
    UserBase,
    UserCreate,
    UserUpdate,
    UserResponse,
    UserLogin,
    Token,
    TokenData,
)
from app.schemas.exchange import (
    ExchangeAccountBase,
    ExchangeAccountCreate,
    ExchangeAccountUpdate,
    ExchangeAccountResponse,
)
from app.schemas.bot import (
    DCAConfigItem,
    BotBase,
    BotCreate,
    BotUpdate,
    BotResponse,
    BotDetailResponse,
)
from app.schemas.order import (
    OrderBase,
    OrderCreate,
    OrderUpdate,
    OrderResponse,
)
from app.schemas.position import (
    PositionBase,
    PositionResponse,
)

__all__ = [
    # User schemas
    "UserBase",
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    "UserLogin",
    "Token",
    "TokenData",
    # Exchange schemas
    "ExchangeAccountBase",
    "ExchangeAccountCreate",
    "ExchangeAccountUpdate",
    "ExchangeAccountResponse",
    # Bot schemas
    "DCAConfigItem",
    "BotBase",
    "BotCreate",
    "BotUpdate",
    "BotResponse",
    "BotDetailResponse",
    # Order schemas
    "OrderBase",
    "OrderCreate",
    "OrderUpdate",
    "OrderResponse",
    # Position schemas
    "PositionBase",
    "PositionResponse",
]