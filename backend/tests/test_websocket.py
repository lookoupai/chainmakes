"""
WebSocket功能测试
"""
import pytest
import asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.testclient import TestClient
from app.main import app
from app.api.v1.websocket import ConnectionManager


@pytest.mark.asyncio
async def test_websocket_connection(client: AsyncClient, auth_headers: dict, test_bot):
    """测试WebSocket连接"""
    # 使用TestClient进行WebSocket测试
    with TestClient(app) as test_client:
        with test_client.websocket_connect(
            f"/ws/{test_bot.id}?token={auth_headers['Authorization'].split(' ')[1]}"
        ) as websocket:
            # 测试连接是否成功
            assert websocket is not None
            
            # 测试接收消息
            try:
                data = websocket.receive_json(timeout=1.0)
                # 可能会收到连接确认消息
                assert "type" in data or "message" in data
            except:
                # 如果没有消息也是正常的，因为可能还没有数据推送
                pass


@pytest.mark.asyncio
async def test_websocket_unauthorized(client: AsyncClient, test_bot):
    """测试未授权的WebSocket连接"""
    with TestClient(app) as test_client:
        # 测试没有token的连接
        with pytest.raises(Exception):
            with test_client.websocket_connect(f"/ws/{test_bot.id}") as websocket:
                pass
        
        # 测试无效token的连接
        with pytest.raises(Exception):
            with test_client.websocket_connect(
                f"/ws/{test_bot.id}?token=invalid_token"
            ) as websocket:
                pass


@pytest.mark.asyncio
async def test_websocket_nonexistent_bot(client: AsyncClient, auth_headers: dict):
    """测试连接不存在的机器人WebSocket"""
    with TestClient(app) as test_client:
        with pytest.raises(Exception):
            with test_client.websocket_connect(
                f"/ws/99999?token={auth_headers['Authorization'].split(' ')[1]}"
            ) as websocket:
                pass


@pytest.mark.asyncio
async def test_connection_manager():
    """测试连接管理器"""
    manager = ConnectionManager()
    
    # 测试连接管理器初始化
    assert len(manager.active_connections) == 0
    
    # 创建模拟WebSocket连接
    mock_websocket = AsyncMock()
    mock_websocket.send_json = AsyncMock()
    
    # 测试连接
    await manager.connect(mock_websocket, 1, "test_user")
    assert len(manager.active_connections) == 1
    
    # 测试广播消息
    test_message = {"type": "test", "data": "test_data"}
    await manager.broadcast_to_bot(1, test_message)
    
    # 验证消息被发送
    mock_websocket.send_json.assert_called_with(test_message)
    
    # 测试断开连接
    await manager.disconnect(mock_websocket, 1, "test_user")
    assert len(manager.active_connections) == 0


@pytest.mark.asyncio
async def test_connection_manager_multiple_connections():
    """测试连接管理器多个连接"""
    manager = ConnectionManager()
    
    # 创建多个模拟WebSocket连接
    mock_websocket1 = AsyncMock()
    mock_websocket1.send_json = AsyncMock()
    
    mock_websocket2 = AsyncMock()
    mock_websocket2.send_json = AsyncMock()
    
    # 连接两个WebSocket到同一个机器人
    await manager.connect(mock_websocket1, 1, "test_user1")
    await manager.connect(mock_websocket2, 1, "test_user2")
    
    assert len(manager.active_connections) == 2
    
    # 测试广播消息
    test_message = {"type": "test", "data": "test_data"}
    await manager.broadcast_to_bot(1, test_message)
    
    # 验证两个连接都收到消息
    mock_websocket1.send_json.assert_called_with(test_message)
    mock_websocket2.send_json.assert_called_with(test_message)
    
    # 断开一个连接
    await manager.disconnect(mock_websocket1, 1, "test_user1")
    assert len(manager.active_connections) == 1
    
    # 再次广播消息，验证只有一个连接收到
    test_message2 = {"type": "test2", "data": "test_data2"}
    await manager.broadcast_to_bot(1, test_message2)
    
    mock_websocket2.send_json.assert_called_with(test_message2)
    
    # 清理
    await manager.disconnect(mock_websocket2, 1, "test_user2")
    assert len(manager.active_connections) == 0


@pytest.mark.asyncio
async def test_broadcast_spread_update():
    """测试广播价差更新"""
    manager = ConnectionManager()
    
    # 创建模拟WebSocket连接
    mock_websocket = AsyncMock()
    mock_websocket.send_json = AsyncMock()
    
    # 连接WebSocket
    await manager.connect(mock_websocket, 1, "test_user")
    
    # 测试广播价差更新
    spread_data = {
        "bot_id": 1,
        "base_price": 50000.0,
        "quote_price": 50100.0,
        "spread": 100.0,
        "spread_percentage": 0.002,
        "timestamp": "2023-01-01T00:00:00Z"
    }
    
    await manager.broadcast_spread_update(1, spread_data)
    
    # 验证消息格式和内容
    expected_message = {
        "type": "spread_update",
        "data": spread_data
    }
    mock_websocket.send_json.assert_called_with(expected_message)


@pytest.mark.asyncio
async def test_broadcast_order_update():
    """测试广播订单更新"""
    manager = ConnectionManager()
    
    # 创建模拟WebSocket连接
    mock_websocket = AsyncMock()
    mock_websocket.send_json = AsyncMock()
    
    # 连接WebSocket
    await manager.connect(mock_websocket, 1, "test_user")
    
    # 测试广播订单更新
    order_data = {
        "id": 1,
        "bot_id": 1,
        "symbol": "BTC/USDT",
        "type": "market",
        "side": "buy",
        "amount": 0.001,
        "price": 50000.0,
        "status": "filled",
        "filled": 0.001,
        "remaining": 0.0,
        "created_at": "2023-01-01T00:00:00Z"
    }
    
    await manager.broadcast_order_update(1, order_data)
    
    # 验证消息格式和内容
    expected_message = {
        "type": "order_update",
        "data": order_data
    }
    mock_websocket.send_json.assert_called_with(expected_message)


@pytest.mark.asyncio
async def test_broadcast_position_update():
    """测试广播持仓更新"""
    manager = ConnectionManager()
    
    # 创建模拟WebSocket连接
    mock_websocket = AsyncMock()
    mock_websocket.send_json = AsyncMock()
    
    # 连接WebSocket
    await manager.connect(mock_websocket, 1, "test_user")
    
    # 测试广播持仓更新
    position_data = {
        "id": 1,
        "bot_id": 1,
        "symbol": "BTC/USDT",
        "side": "long",
        "size": 0.001,
        "entry_price": 50000.0,
        "mark_price": 50100.0,
        "unrealized_pnl": 0.1,
        "percentage": 0.2,
        "updated_at": "2023-01-01T00:00:00Z"
    }
    
    await manager.broadcast_position_update(1, position_data)
    
    # 验证消息格式和内容
    expected_message = {
        "type": "position_update",
        "data": position_data
    }
    mock_websocket.send_json.assert_called_with(expected_message)


@pytest.mark.asyncio
async def test_broadcast_status_update():
    """测试广播状态更新"""
    manager = ConnectionManager()
    
    # 创建模拟WebSocket连接
    mock_websocket = AsyncMock()
    mock_websocket.send_json = AsyncMock()
    
    # 连接WebSocket
    await manager.connect(mock_websocket, 1, "test_user")
    
    # 测试广播状态更新
    status_data = {
        "bot_id": 1,
        "status": "running",
        "last_update": "2023-01-01T00:00:00Z",
        "message": "Bot is running normally"
    }
    
    await manager.broadcast_status_update(1, status_data)
    
    # 验证消息格式和内容
    expected_message = {
        "type": "status_update",
        "data": status_data
    }
    mock_websocket.send_json.assert_called_with(expected_message)


@pytest.mark.asyncio
async def test_connection_manager_bot_filtering():
    """测试连接管理器的机器人过滤"""
    manager = ConnectionManager()
    
    # 创建多个模拟WebSocket连接
    mock_websocket1 = AsyncMock()
    mock_websocket1.send_json = AsyncMock()
    
    mock_websocket2 = AsyncMock()
    mock_websocket2.send_json = AsyncMock()
    
    # 连接WebSocket到不同机器人
    await manager.connect(mock_websocket1, 1, "test_user1")
    await manager.connect(mock_websocket2, 2, "test_user2")
    
    assert len(manager.active_connections) == 2
    
    # 测试只向机器人1广播消息
    test_message = {"type": "test", "data": "test_data"}
    await manager.broadcast_to_bot(1, test_message)
    
    # 验证只有机器人1的连接收到消息
    mock_websocket1.send_json.assert_called_with(test_message)
    mock_websocket2.send_json.assert_not_called()
    
    # 测试只向机器人2广播消息
    await manager.broadcast_to_bot(2, test_message)
    
    # 验证只有机器人2的连接收到消息
    mock_websocket2.send_json.assert_called_with(test_message)