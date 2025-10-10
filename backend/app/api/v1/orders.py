"""
订单相关的API路由
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.dependencies import get_db, check_bot_ownership
from app.models.bot_instance import BotInstance
from app.models.order import Order
from app.schemas.order import OrderResponse

router = APIRouter()


@router.get("/{bot_id}/orders", response_model=List[OrderResponse])
async def get_bot_orders(
    bot: BotInstance = Depends(check_bot_ownership),
    db: AsyncSession = Depends(get_db)
):
    """
    获取机器人的订单历史
    """
    result = await db.execute(
        select(Order)
        .where(Order.bot_instance_id == bot.id)
        .order_by(Order.created_at.desc())
    )
    orders = result.scalars().all()
    
    return orders