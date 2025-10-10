"""
机器人API测试
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime


@pytest.mark.asyncio
async def test_create_bot(client: AsyncClient, auth_headers: dict, test_exchange):
    """测试创建机器人"""
    bot_data = {
        "name": "Test Bot API",
        "symbol": "ETH/USDT",
        "base_exchange_id": test_exchange.id,
        "quote_exchange_id": test_exchange.id,
        "strategy_type": "spread",
        "min_spread_threshold": 0.01,
        "max_spread_threshold": 0.05,
        "trade_amount": 200.0,
        "dca_enabled": True,
        "dca_multiplier": 1.5,
        "dca_max_orders": 5,
        "dca_spread_threshold": 0.02
    }
    
    response = await client.post(
        "/api/v1/bots/",
        json=bot_data,
        headers=auth_headers
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == bot_data["name"]
    assert data["symbol"] == bot_data["symbol"]
    assert data["strategy_type"] == bot_data["strategy_type"]
    assert "id" in data


@pytest.mark.asyncio
async def test_get_bots(client: AsyncClient, auth_headers: dict, test_bot):
    """测试获取机器人列表"""
    response = await client.get(
        "/api/v1/bots/",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert any(bot["id"] == test_bot.id for bot in data)


@pytest.mark.asyncio
async def test_get_bot(client: AsyncClient, auth_headers: dict, test_bot):
    """测试获取单个机器人"""
    response = await client.get(
        f"/api/v1/bots/{test_bot.id}",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == test_bot.id
    assert data["name"] == test_bot.name


@pytest.mark.asyncio
async def test_update_bot(client: AsyncClient, auth_headers: dict, test_bot):
    """测试更新机器人"""
    update_data = {
        "name": "Updated Bot Name",
        "min_spread_threshold": 0.02
    }
    
    response = await client.put(
        f"/api/v1/bots/{test_bot.id}",
        json=update_data,
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == update_data["name"]
    assert data["min_spread_threshold"] == update_data["min_spread_threshold"]


@pytest.mark.asyncio
async def test_delete_bot(client: AsyncClient, auth_headers: dict, test_bot):
    """测试删除机器人"""
    response = await client.delete(
        f"/api/v1/bots/{test_bot.id}",
        headers=auth_headers
    )
    
    assert response.status_code == 204
    
    # 验证机器人已删除
    response = await client.get(
        f"/api/v1/bots/{test_bot.id}",
        headers=auth_headers
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_start_bot(client: AsyncClient, auth_headers: dict, test_bot):
    """测试启动机器人"""
    response = await client.post(
        f"/api/v1/bots/{test_bot.id}/start",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "started" in data["message"].lower()


@pytest.mark.asyncio
async def test_stop_bot(client: AsyncClient, auth_headers: dict, test_bot):
    """测试停止机器人"""
    # 先启动机器人
    await client.post(
        f"/api/v1/bots/{test_bot.id}/start",
        headers=auth_headers
    )
    
    # 然后停止机器人
    response = await client.post(
        f"/api/v1/bots/{test_bot.id}/stop",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "stopped" in data["message"].lower()


@pytest.mark.asyncio
async def test_get_bot_orders(client: AsyncClient, auth_headers: dict, test_bot):
    """测试获取机器人订单历史"""
    response = await client.get(
        f"/api/v1/bots/{test_bot.id}/orders",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_get_bot_positions(client: AsyncClient, auth_headers: dict, test_bot):
    """测试获取机器人持仓"""
    response = await client.get(
        f"/api/v1/bots/{test_bot.id}/positions",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_get_spread_history(client: AsyncClient, auth_headers: dict, test_bot):
    """测试获取机器人价差历史"""
    response = await client.get(
        f"/api/v1/bots/{test_bot.id}/spread-history",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_close_positions(client: AsyncClient, auth_headers: dict, test_bot):
    """测试平仓所有持仓"""
    response = await client.post(
        f"/api/v1/bots/{test_bot.id}/close-positions",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "message" in data


@pytest.mark.asyncio
async def test_unauthorized_access(client: AsyncClient, test_bot):
    """测试未授权访问"""
    response = await client.get(f"/api/v1/bots/{test_bot.id}")
    assert response.status_code == 401
    
    response = await client.get("/api/v1/bots/")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_bot_not_found(client: AsyncClient, auth_headers: dict):
    """测试机器人不存在"""
    response = await client.get(
        "/api/v1/bots/99999",
        headers=auth_headers
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_create_bot_invalid_data(client: AsyncClient, auth_headers: dict, test_exchange):
    """测试创建机器人时提供无效数据"""
    invalid_data = {
        "name": "",  # 空名称
        "symbol": "INVALID",  # 无效交易对格式
        "base_exchange_id": test_exchange.id,
        "quote_exchange_id": test_exchange.id,
        "strategy_type": "invalid_strategy",  # 无效策略类型
        "min_spread_threshold": -0.01,  # 负数阈值
        "max_spread_threshold": 0.05,
        "trade_amount": -100.0  # 负数交易金额
    }
    
    response = await client.post(
        "/api/v1/bots/",
        json=invalid_data,
        headers=auth_headers
    )
    
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data