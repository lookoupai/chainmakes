"""
机器人引擎单元测试
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.bot_engine import BotEngine
from app.models.bot import Bot
from app.models.exchange import Exchange
from app.models.order import Order
from app.models.position import Position
from app.exchanges.base import BaseExchange


@pytest.fixture
async def mock_exchange():
    """创建模拟交易所"""
    exchange = AsyncMock(spec=BaseExchange)
    exchange.get_ticker.return_value = {
        "symbol": "BTC/USDT",
        "bid": 50000.0,
        "ask": 50100.0,
        "last": 50050.0,
        "timestamp": datetime.utcnow().timestamp()
    }
    exchange.create_market_order.return_value = {
        "id": "test_order_id",
        "symbol": "BTC/USDT",
        "type": "market",
        "side": "buy",
        "amount": 0.001,
        "price": 50050.0,
        "filled": 0.001,
        "remaining": 0.0,
        "status": "closed",
        "timestamp": datetime.utcnow().timestamp()
    }
    exchange.get_order.return_value = {
        "id": "test_order_id",
        "symbol": "BTC/USDT",
        "type": "market",
        "side": "buy",
        "amount": 0.001,
        "price": 50050.0,
        "filled": 0.001,
        "remaining": 0.0,
        "status": "closed",
        "timestamp": datetime.utcnow().timestamp()
    }
    exchange.get_position.return_value = {
        "symbol": "BTC/USDT",
        "side": "long",
        "size": 0.001,
        "entry_price": 50050.0,
        "mark_price": 50100.0,
        "unrealized_pnl": 0.05,
        "percentage": 0.1
    }
    return exchange


@pytest.fixture
async def bot_engine(mock_exchange):
    """创建机器人引擎实例"""
    engine = BotEngine(bot_id=1, db_session=AsyncMock())
    engine.base_exchange = mock_exchange
    engine.quote_exchange = mock_exchange
    return engine


@pytest.mark.asyncio
async def test_calculate_spread(bot_engine):
    """测试计算价差"""
    base_price = 50000.0
    quote_price = 50100.0
    
    spread = await bot_engine._calculate_spread(base_price, quote_price)
    
    assert spread == 100.0
    assert spread > 0


@pytest.mark.asyncio
async def test_calculate_spread_percentage(bot_engine):
    """测试计算价差百分比"""
    base_price = 50000.0
    quote_price = 50100.0
    
    spread_percentage = await bot_engine._calculate_spread_percentage(base_price, quote_price)
    
    assert spread_percentage == 0.002  # (50100 - 50000) / 50000 = 0.002


@pytest.mark.asyncio
async def test_should_trigger_trade(bot_engine):
    """测试交易触发条件"""
    # 测试应该触发交易的情况
    assert await bot_engine._should_trigger_trade(0.02, 0.01, 0.05) == True
    
    # 测试不应该触发交易的情况 - 价差低于最小阈值
    assert await bot_engine._should_trigger_trade(0.005, 0.01, 0.05) == False
    
    # 测试不应该触发交易的情况 - 价差高于最大阈值
    assert await bot_engine._should_trigger_trade(0.06, 0.01, 0.05) == False


@pytest.mark.asyncio
async def test_create_order(bot_engine, mock_exchange):
    """测试创建订单"""
    order_data = {
        "symbol": "BTC/USDT",
        "type": "market",
        "side": "buy",
        "amount": 0.001,
        "price": None
    }
    
    order_id = await bot_engine._create_order(mock_exchange, order_data)
    
    assert order_id == "test_order_id"
    mock_exchange.create_market_order.assert_called_once()


@pytest.mark.asyncio
async def test_get_current_prices(bot_engine, mock_exchange):
    """测试获取当前价格"""
    base_price, quote_price = await bot_engine._get_current_prices()
    
    assert base_price == 50000.0
    assert quote_price == 50000.0  # 使用同一个模拟交易所
    mock_exchange.get_ticker.assert_called()


@pytest.mark.asyncio
async def test_should_trigger_dca(bot_engine):
    """测试DCA触发条件"""
    # 测试应该触发DCA的情况
    assert await bot_engine._should_trigger_dca(0.02, 0.015, True) == True
    
    # 测试不应该触发DCA的情况 - DCA未启用
    assert await bot_engine._should_trigger_dca(0.02, 0.015, False) == False
    
    # 测试不应该触发DCA的情况 - 价差低于DCA阈值
    assert await bot_engine._should_trigger_dca(0.01, 0.015, True) == False


@pytest.mark.asyncio
async def test_calculate_dca_amount(bot_engine):
    """测试DCA交易金额计算"""
    base_amount = 100.0
    dca_multiplier = 1.5
    dca_order_count = 2
    
    dca_amount = await bot_engine._calculate_dca_amount(
        base_amount, dca_multiplier, dca_order_count
    )
    
    assert dca_amount == 100.0 * (1.5 ** 2)  # 100 * 2.25 = 225


@pytest.mark.asyncio
async def test_create_or_update_position(bot_engine):
    """测试创建或更新持仓"""
    position_data = {
        "symbol": "BTC/USDT",
        "side": "long",
        "size": 0.001,
        "entry_price": 50000.0,
        "mark_price": 50100.0
    }
    
    await bot_engine._create_or_update_position(position_data)
    
    # 验证数据库操作被调用
    bot_engine.db_session.add.assert_called()
    bot_engine.db_session.commit.assert_called()
    bot_engine.db_session.refresh.assert_called()


@pytest.mark.asyncio
async def test_update_position_prices(bot_engine):
    """测试更新持仓价格"""
    # 模拟持仓数据
    position = MagicMock()
    position.symbol = "BTC/USDT"
    position.side = "long"
    position.size = 0.001
    position.entry_price = 50000.0
    
    bot_engine.db_session.execute.return_value.scalars.return_value.all.return_value = [position]
    
    await bot_engine.update_position_prices()
    
    # 验证持仓价格被更新
    assert position.mark_price == 50000.0  # 模拟交易所的价格
    assert position.unrealized_pnl == 0.0  # (50000 - 50000) * 0.001 = 0
    
    # 验证数据库操作被调用
    bot_engine.db_session.commit.assert_called()


@pytest.mark.asyncio
async def test_close_position(bot_engine, mock_exchange):
    """测试平仓"""
    position = MagicMock()
    position.symbol = "BTC/USDT"
    position.side = "long"
    position.size = 0.001
    
    await bot_engine._close_position(position, mock_exchange)
    
    # 验证平仓订单被创建
    mock_exchange.create_market_order.assert_called_once()
    
    # 验证持仓被删除
    bot_engine.db_session.delete.assert_called_with(position)
    bot_engine.db_session.commit.assert_called()


@pytest.mark.asyncio
async def test_run_trading_cycle(bot_engine):
    """测试交易周期运行"""
    # 模拟机器人配置
    bot_engine.min_spread_threshold = 0.01
    bot_engine.max_spread_threshold = 0.05
    bot_engine.trade_amount = 100.0
    bot_engine.dca_enabled = True
    bot_engine.dca_multiplier = 1.5
    bot_engine.dca_max_orders = 5
    bot_engine.dca_spread_threshold = 0.02
    bot_engine.dca_order_count = 0
    
    # 模拟数据库查询结果
    bot_engine.db_session.execute.return_value.scalars.return_value.first.return_value = None
    
    # 运行交易周期
    await bot_engine._run_trading_cycle()
    
    # 验证价格被获取
    bot_engine.base_exchange.get_ticker.assert_called()
    bot_engine.quote_exchange.get_ticker.assert_called()


@pytest.mark.asyncio
async def test_stop_engine(bot_engine):
    """测试停止引擎"""
    bot_engine.running = True
    
    await bot_engine.stop()
    
    assert bot_engine.running == False


@pytest.mark.asyncio
async def test_start_engine(bot_engine):
    """测试启动引擎"""
    # 模拟机器人配置
    bot_engine.min_spread_threshold = 0.01
    bot_engine.max_spread_threshold = 0.05
    bot_engine.trade_amount = 100.0
    bot_engine.dca_enabled = True
    bot_engine.dca_multiplier = 1.5
    bot_engine.dca_max_orders = 5
    bot_engine.dca_spread_threshold = 0.02
    bot_engine.dca_order_count = 0
    
    # 模拟数据库查询结果
    bot_engine.db_session.execute.return_value.scalars.return_value.first.return_value = None
    
    # 启动引擎并立即停止
    start_task = bot_engine.start()
    await asyncio.sleep(0.1)  # 让引擎运行一小段时间
    await bot_engine.stop()
    
    # 验证引擎曾经运行过
    assert not start_task.done() or start_task.exception() is None