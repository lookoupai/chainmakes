"""
模拟数据生成工具
用于在真实数据不存在时生成合理的测试数据
"""
import random
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List
from app.models.bot_instance import BotInstance
from app.models.order import Order
from app.models.position import Position
from app.models.spread_history import SpreadHistory


def generate_mock_orders(bot: BotInstance, count: int = 5) -> List[dict]:
    """
    生成模拟订单数据

    Args:
        bot: 机器人实例
        count: 生成订单数量

    Returns:
        订单字典列表
    """
    # 使用bot_id作为随机种子,保证数据可复现
    random.seed(bot.id)

    orders = []
    base_time = bot.start_time if bot.start_time else datetime.utcnow() - timedelta(days=7)

    # 模拟基础价格
    base_price_m1 = Decimal("50000")  # 市场1基础价格
    base_price_m2 = Decimal("3000")   # 市场2基础价格

    for i in range(count):
        # 轮流生成买单和卖单
        is_buy = i % 2 == 0
        # 交替使用两个市场
        use_market1 = i % 2 == 0

        symbol = bot.market1_symbol if use_market1 else bot.market2_symbol
        base_price = base_price_m1 if use_market1 else base_price_m2

        # 价格随机波动 ±2%
        price_multiplier = Decimal(str(random.uniform(0.98, 1.02)))
        order_price = base_price * price_multiplier

        # DCA层级 (1-3)
        dca_level = (i % 3) + 1

        # 根据DCA层级计算投资额
        if dca_level <= len(bot.dca_config):
            multiplier = Decimal(str(bot.dca_config[dca_level - 1].get('multiplier', 1.0)))
        else:
            multiplier = Decimal("1.0")

        investment = Decimal(str(bot.investment_per_order)) * multiplier
        amount = investment / order_price

        # 订单状态 (70%已完成, 20%进行中, 10%已取消)
        rand = random.random()
        if rand < 0.7:
            status = "closed"
            filled_amount = amount
            filled_at = base_time + timedelta(hours=i * 2, minutes=random.randint(0, 59))
        elif rand < 0.9:
            status = "open"
            filled_amount = amount * Decimal(str(random.uniform(0.3, 0.8)))
            filled_at = None
        else:
            status = "canceled"
            filled_amount = Decimal("0")
            filled_at = None

        created_at = base_time + timedelta(hours=i * 2)

        order = {
            "id": i + 1,  # 添加ID字段
            "bot_instance_id": bot.id,
            "cycle_number": (i // 2) + 1,  # 每2个订单算一个循环
            "exchange_order_id": f"MOCK-{bot.id}-{i+1:04d}",
            "symbol": symbol,
            "side": "buy" if is_buy else "sell",
            "order_type": bot.order_type_open,
            "price": float(order_price),
            "amount": float(amount),
            "filled_amount": float(filled_amount),
            "cost": float(order_price * filled_amount) if status == "closed" else None,
            "status": status,
            "dca_level": dca_level,
            "created_at": created_at.isoformat(),
            "updated_at": created_at.isoformat(),
            "filled_at": filled_at.isoformat() if filled_at else None
        }
        orders.append(order)

    # 重置随机种子
    random.seed()

    return orders


def generate_mock_positions(bot: BotInstance) -> List[dict]:
    """
    生成模拟持仓数据

    Args:
        bot: 机器人实例

    Returns:
        持仓字典列表
    """
    random.seed(bot.id)

    positions = []

    # 模拟基础价格
    base_price_m1 = Decimal("50000")
    base_price_m2 = Decimal("3000")

    # 生成2个持仓: 一个做多,一个做空
    for i, (symbol, base_price, side) in enumerate([
        (bot.market1_symbol, base_price_m1, "long"),
        (bot.market2_symbol, base_price_m2, "short")
    ]):
        # 开仓价格
        entry_price = base_price * Decimal(str(random.uniform(0.98, 1.02)))

        # 当前价格 (相对开仓价波动 ±2%)
        current_price = entry_price * Decimal(str(random.uniform(0.98, 1.02)))

        # 持仓数量
        investment = Decimal(str(bot.investment_per_order))
        amount = investment / entry_price

        # 计算未实现盈亏
        if side == "long":
            unrealized_pnl = (current_price - entry_price) * amount
        else:
            unrealized_pnl = (entry_price - current_price) * amount

        created_at = bot.start_time if bot.start_time else datetime.utcnow() - timedelta(hours=12)

        position = {
            "id": i + 1,  # 添加ID字段
            "bot_instance_id": bot.id,
            "cycle_number": bot.current_cycle if bot.current_cycle > 0 else 1,
            "symbol": symbol,
            "side": side,
            "amount": float(amount),
            "entry_price": float(entry_price),
            "current_price": float(current_price),
            "unrealized_pnl": float(unrealized_pnl),
            "is_open": True,
            "created_at": created_at.isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "closed_at": None
        }
        positions.append(position)

    random.seed()

    return positions


def generate_spread_history(
    bot: BotInstance,
    hours: int = 24,
    interval_minutes: int = 15
) -> List[dict]:
    """
    生成价差历史曲线数据

    使用随机游走算法模拟真实的价差波动

    Args:
        bot: 机器人实例
        hours: 生成多少小时的数据
        interval_minutes: 数据点时间间隔(分钟)

    Returns:
        价差历史字典列表
    """
    random.seed(bot.id)

    history = []

    # 计算数据点数量
    total_points = (hours * 60) // interval_minutes

    # 起始时间
    start_time = datetime.utcnow() - timedelta(hours=hours)

    # 初始价差 (随机在 -1% ~ +1% 之间)
    current_spread = random.uniform(-1.0, 1.0)

    # 模拟基础价格
    base_price_m1 = 50000.0
    base_price_m2 = 3000.0

    # 计算开始时的价格 (根据bot.start_time的价格)
    market1_start_price = base_price_m1
    market2_start_price = base_price_m2

    for i in range(total_points):
        # 随机游走: 每次在当前基础上随机增减
        drift = random.uniform(-0.3, 0.3)  # 漂移量
        current_spread += drift

        # 限制价差在合理范围内 (-3% ~ +3%)
        current_spread = max(-3.0, min(3.0, current_spread))

        # 根据价差反推当前价格
        # spread = (price1/start1 - 1) * 100 - (price2/start2 - 1) * 100
        # 假设市场2保持相对稳定,主要是市场1在波动
        change_m2 = random.uniform(-0.5, 0.5)  # 市场2涨跌幅 ±0.5%
        change_m1 = current_spread + change_m2  # 市场1涨跌幅

        market1_price = market1_start_price * (1 + change_m1 / 100)
        market2_price = market2_start_price * (1 + change_m2 / 100)

        recorded_at = start_time + timedelta(minutes=i * interval_minutes)

        data_point = {
            "id": i + 1,  # 添加ID字段
            "bot_instance_id": bot.id,
            "market1_price": round(market1_price, 2),
            "market2_price": round(market2_price, 2),
            "spread_percentage": round(current_spread, 4),
            "recorded_at": recorded_at.isoformat()
        }
        history.append(data_point)

    random.seed()

    return history
