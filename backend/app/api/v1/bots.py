"""
交易机器人管理相关的API路由
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List
from decimal import Decimal
from datetime import datetime, timedelta

from app.dependencies import get_db, get_current_user, check_bot_ownership
from app.models.user import User
from app.models.bot_instance import BotInstance
from app.models.exchange_account import ExchangeAccount
from app.exchanges.exchange_factory import ExchangeFactory
from app.schemas.bot import (
    BotCreate,
    BotUpdate,
    BotResponse,
    BotDetailResponse
)
from app.schemas.order import OrderResponse
from app.schemas.position import PositionResponse
from app.schemas.spread import SpreadHistoryResponse
from app.services.bot_service import BotService
from app.utils.mock_data import (
    generate_mock_orders,
    generate_mock_positions,
    generate_spread_history
)
from app.models.order import Order
from app.models.position import Position
from app.models.spread_history import SpreadHistory

router = APIRouter()


@router.post("/", response_model=BotResponse, status_code=status.HTTP_201_CREATED)
async def create_bot(
    bot_data: BotCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    创建交易机器人实例
    """
    # 1) 校验交易所账户归属与可用性
    result = await db.execute(
        select(ExchangeAccount).where(
            ExchangeAccount.id == bot_data.exchange_account_id,
            ExchangeAccount.user_id == current_user.id,
            ExchangeAccount.is_active == True  # noqa: E712
        )
    )
    exchange_account = result.scalar_one_or_none()
    if not exchange_account:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无效的交易所账户，或该账户不属于当前用户/已被禁用"
        )

    # 2) 校验交易所是否受支持
    supported = set(ExchangeFactory.get_supported_exchanges())
    if exchange_account.exchange_name.lower() not in supported:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"交易所暂不支持: {exchange_account.exchange_name}. 支持: {', '.join(sorted(supported))}"
        )

    # 3) 基础参数校验
    if bot_data.market1_symbol == bot_data.market2_symbol:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="市场1与市场2不能相同"
        )
    if bot_data.order_type_open not in ("market", "limit"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="开仓订单类型仅支持: market/limit"
        )
    if bot_data.order_type_close not in ("market", "limit"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="平仓订单类型仅支持: market/limit"
        )
    if bot_data.profit_mode not in ("regression", "position"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="止盈模式仅支持: regression(回归止盈)/position(仓位止盈)"
        )

    # 4) DCA参数与资金约束校验
    if not bot_data.dca_config or len(bot_data.dca_config) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="必须至少配置一次加仓(DCA)"
        )
    if len(bot_data.dca_config) > bot_data.max_dca_times:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"DCA配置条数({len(bot_data.dca_config)})不能超过最大加仓次数({bot_data.max_dca_times})"
        )

    inv_per_order = Decimal(str(bot_data.investment_per_order))
    max_position_value = Decimal(str(bot_data.max_position_value))
    # 只计算前 max_dca_times 次的倍投
    multipliers = [Decimal(str(item.multiplier)) for item in bot_data.dca_config][: bot_data.max_dca_times]
    total_planned_investment = sum(inv_per_order * m for m in multipliers)

    if total_planned_investment > max_position_value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"计划总投资额({total_planned_investment})超过最大持仓面值({max_position_value})，请减少倍投或提高上限"
        )

    # 创建机器人实例
    # 将dca_config中的Decimal转换为float以支持JSON序列化
    dca_config_serializable = []
    for item in bot_data.dca_config:
        item_dict = item.model_dump()
        # 转换Decimal为float
        if isinstance(item_dict.get('spread'), Decimal):
            item_dict['spread'] = float(item_dict['spread'])
        if isinstance(item_dict.get('multiplier'), Decimal):
            item_dict['multiplier'] = float(item_dict['multiplier'])
        dca_config_serializable.append(item_dict)
    
    new_bot = BotInstance(
        user_id=current_user.id,
        exchange_account_id=bot_data.exchange_account_id,
        bot_name=bot_data.bot_name,
        market1_symbol=bot_data.market1_symbol,
        market2_symbol=bot_data.market2_symbol,
        start_time=bot_data.start_time,
        leverage=bot_data.leverage,
        order_type_open=bot_data.order_type_open,
        order_type_close=bot_data.order_type_close,
        investment_per_order=float(bot_data.investment_per_order),
        max_position_value=float(bot_data.max_position_value),
        max_dca_times=bot_data.max_dca_times,
        dca_config=dca_config_serializable,
        profit_mode=bot_data.profit_mode,
        profit_ratio=float(bot_data.profit_ratio),
        stop_loss_ratio=float(bot_data.stop_loss_ratio) if bot_data.stop_loss_ratio is not None else None,
        pause_after_close=bot_data.pause_after_close,
        status="stopped"
    )

    db.add(new_bot)
    await db.commit()
    await db.refresh(new_bot)

    return new_bot


@router.get("/")
async def list_bots(
    page: int = 1,
    page_size: int = 10,
    status: str | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取当前用户的所有机器人（分页）
    
    Query Parameters:
        - page: 页码 (默认1)
        - page_size: 每页数量 (默认10)
        - status: 状态筛选 (running/paused/stopped)
    """
    # 构建基础查询
    query = select(BotInstance).where(BotInstance.user_id == current_user.id)
    
    # 状态筛选
    if status:
        query = query.where(BotInstance.status == status)
    
    # 获取总数
    count_result = await db.execute(
        select(func.count()).select_from(query.subquery())
    )
    total = count_result.scalar()
    
    # 应用分页和排序
    query = query.order_by(BotInstance.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    result = await db.execute(query)
    bots = result.scalars().all()
    
    # 将ORM对象转换为BotResponse
    bot_responses = [BotResponse.model_validate(bot) for bot in bots]
    
    return {
        "items": bot_responses,
        "total": total,
        "page": page,
        "page_size": page_size
    }


@router.get("/{bot_id}", response_model=BotDetailResponse)
async def get_bot(
    bot: BotInstance = Depends(check_bot_ownership)
):
    """
    获取机器人详情
    """
    return bot


@router.put("/{bot_id}", response_model=BotResponse)
async def update_bot(
    bot_update: BotUpdate,
    bot: BotInstance = Depends(check_bot_ownership),
    db: AsyncSession = Depends(get_db)
):
    """
    更新机器人配置
    """
    # 只允许在停止状态下修改配置
    if bot.status == "running":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无法修改正在运行的机器人配置,请先停止机器人"
        )
    
    # 更新字段
    update_data = bot_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if field == "dca_config" and value is not None:
            # 处理dca_config，确保转换为可序列化的字典列表
            dca_config_list = []
            for item in value:
                # 如果是Pydantic模型，转换为字典
                if hasattr(item, 'model_dump'):
                    item_dict = item.model_dump()
                # 如果已经是字典，直接使用
                elif isinstance(item, dict):
                    item_dict = item.copy()
                else:
                    item_dict = dict(item)
                
                # 确保Decimal类型转换为float
                from decimal import Decimal
                if isinstance(item_dict.get('spread'), Decimal):
                    item_dict['spread'] = float(item_dict['spread'])
                if isinstance(item_dict.get('multiplier'), Decimal):
                    item_dict['multiplier'] = float(item_dict['multiplier'])
                
                dca_config_list.append(item_dict)
            
            value = dca_config_list
        setattr(bot, field, value)
    
    await db.commit()
    await db.refresh(bot)
    
    return bot


@router.delete("/{bot_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_bot(
    bot: BotInstance = Depends(check_bot_ownership),
    db: AsyncSession = Depends(get_db)
):
    """
    删除机器人
    """
    # 只允许删除停止状态的机器人
    if bot.status == "running":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无法删除正在运行的机器人,请先停止机器人"
        )
    
    await db.delete(bot)
    await db.commit()
    
    return None


@router.post("/{bot_id}/start", response_model=BotResponse)
async def start_bot(
    bot: BotInstance = Depends(check_bot_ownership),
    db: AsyncSession = Depends(get_db)
):
    """
    启动机器人
    """
    from app.utils.logger import setup_logger
    logger = setup_logger('bots_api')
    
    logger.info(f"[API] 收到启动机器人请求: bot_id={bot.id}, 当前状态={bot.status}")
    
    if bot.status == "running":
        logger.warning(f"[API] 机器人 {bot.id} 已在运行中")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="机器人已在运行中"
        )
    
    # 使用BotService启动机器人
    logger.info(f"[API] 调用 BotService.start_bot()")
    success = await BotService.start_bot(bot.id, db)
    logger.info(f"[API] BotService.start_bot() 返回: {success}")
    
    if not success:
        logger.error(f"[API] 启动机器人 {bot.id} 失败")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="启动机器人失败"
        )
    
    # 刷新机器人状态（不需要额外的commit，BotManager已经处理了）
    await db.refresh(bot)
    logger.info(f"[API] 机器人 {bot.id} 启动成功，新状态={bot.status}")
    
    return bot


@router.post("/{bot_id}/pause", response_model=BotResponse)
async def pause_bot(
    bot: BotInstance = Depends(check_bot_ownership),
    db: AsyncSession = Depends(get_db)
):
    """
    暂停机器人
    """
    if bot.status != "running":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="机器人未在运行"
        )
    
    # 使用BotService暂停机器人
    success = await BotService.pause_bot(bot.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="暂停机器人失败"
        )
    
    bot.status = "paused"
    
    await db.commit()
    await db.refresh(bot)
    
    return bot


@router.post("/{bot_id}/stop", response_model=BotResponse)
async def stop_bot(
    bot: BotInstance = Depends(check_bot_ownership),
    db: AsyncSession = Depends(get_db)
):
    """
    停止机器人
    """
    if bot.status == "stopped":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="机器人已停止"
        )
    
    # 使用BotService停止机器人
    success = await BotService.stop_bot(bot.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="停止机器人失败"
        )
    
    bot.status = "stopped"

    await db.commit()
    await db.refresh(bot)

    return bot


@router.get("/{bot_id}/orders")
async def get_bot_orders(
    bot: BotInstance = Depends(check_bot_ownership),
    page: int = 1,
    page_size: int = 20,
    status_filter: str | None = None,
    db: AsyncSession = Depends(get_db)
):
    """
    获取机器人订单历史

    Query Parameters:
        - page: 页码 (默认1)
        - page_size: 每页数量 (默认20)
        - status_filter: 状态筛选 (pending/open/closed/canceled)

    Returns:
        分页的订单列表
    """
    # 构建查询
    query = select(Order).where(Order.bot_instance_id == bot.id)

    # 状态筛选
    if status_filter:
        query = query.where(Order.status == status_filter)

    # 获取总数
    count_result = await db.execute(
        select(func.count()).select_from(query.subquery())
    )
    total = count_result.scalar()

    # 如果数据库中没有订单,生成模拟数据
    if total == 0:
        mock_orders = generate_mock_orders(bot, count=5)
        return {
            "items": mock_orders,
            "total": len(mock_orders),
            "page": page,
            "page_size": page_size
        }

    # 应用分页和排序
    query = query.order_by(Order.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    orders = result.scalars().all()

    return {
        "items": orders,
        "total": total,
        "page": page,
        "page_size": page_size
    }


@router.get("/{bot_id}/positions", response_model=List[PositionResponse])
async def get_bot_positions(
    bot: BotInstance = Depends(check_bot_ownership),
    db: AsyncSession = Depends(get_db)
):
    """
    获取机器人当前持仓

    Returns:
        活跃持仓列表
    """
    # 查询活跃持仓
    result = await db.execute(
        select(Position).where(
            Position.bot_instance_id == bot.id,
            Position.is_open == True  # noqa: E712
        )
    )
    positions = result.scalars().all()

    # 如果没有持仓,生成模拟数据
    if not positions:
        mock_positions = generate_mock_positions(bot)
        return mock_positions

    # 返回真实持仓数据
    return positions


@router.get("/{bot_id}/spread-history")
async def get_spread_history(
    bot: BotInstance = Depends(check_bot_ownership),
    start_time: str | None = None,
    end_time: str | None = None,
    db: AsyncSession = Depends(get_db)
):
    """
    获取价差历史数据

    Query Parameters:
        - start_time: 起始时间 (ISO 8601格式, 可选)
        - end_time: 结束时间 (ISO 8601格式, 可选)
        - 默认返回最近24小时的数据

    Returns:
        价差时间序列数据
    """
    # 解析时间参数
    if not end_time:
        end_dt = datetime.utcnow()
    else:
        end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))

    if not start_time:
        start_dt = end_dt - timedelta(hours=24)
    else:
        start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))

    # 查询数据库
    result = await db.execute(
        select(SpreadHistory).where(
            SpreadHistory.bot_instance_id == bot.id,
            SpreadHistory.recorded_at >= start_dt,
            SpreadHistory.recorded_at <= end_dt
        ).order_by(SpreadHistory.recorded_at.asc())
    )
    history = result.scalars().all()

    # 如果没有历史数据,生成模拟数据
    if not history:
        hours = int((end_dt - start_dt).total_seconds() / 3600)
        mock_history = generate_spread_history(bot, hours=min(hours, 24))
        return mock_history

    # 返回真实数据
    return history


@router.post("/{bot_id}/close-positions")
async def close_positions(
    bot: BotInstance = Depends(check_bot_ownership),
    db: AsyncSession = Depends(get_db)
):
    """
    平仓所有持仓
    
    Returns:
        操作结果
    """
    if bot.status != "running" and bot.status != "paused":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="只有运行中或暂停的机器人才能平仓"
        )
    
    # 使用BotService平仓
    success = await BotService.close_all_positions(bot.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="平仓操作失败"
        )
    
    return {"message": "平仓指令已发送", "success": True}