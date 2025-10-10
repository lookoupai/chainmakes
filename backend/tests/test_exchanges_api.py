"""
交易所API测试
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
async def test_create_exchange(client: AsyncClient, auth_headers: dict):
    """测试创建交易所"""
    exchange_data = {
        "name": "Test Exchange API",
        "exchange_type": "mock",
        "api_key": "test_api_key_123",
        "api_secret": "test_api_secret_456",
        "passphrase": "test_passphrase",
        "is_testnet": True,
        "is_active": True
    }
    
    response = await client.post(
        "/api/v1/exchanges/",
        json=exchange_data,
        headers=auth_headers
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == exchange_data["name"]
    assert data["exchange_type"] == exchange_data["exchange_type"]
    assert data["is_testnet"] == exchange_data["is_testnet"]
    assert data["is_active"] == exchange_data["is_active"]
    assert "api_secret" not in data  # 确保API密钥不在响应中
    assert "passphrase" not in data  # 确保密码不在响应中
    assert "id" in data


@pytest.mark.asyncio
async def test_get_exchanges(client: AsyncClient, auth_headers: dict, test_exchange):
    """测试获取交易所列表"""
    response = await client.get(
        "/api/v1/exchanges/",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert any(exchange["id"] == test_exchange.id for exchange in data)


@pytest.mark.asyncio
async def test_get_exchange(client: AsyncClient, auth_headers: dict, test_exchange):
    """测试获取单个交易所"""
    response = await client.get(
        f"/api/v1/exchanges/{test_exchange.id}",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == test_exchange.id
    assert data["name"] == test_exchange.name
    assert "api_secret" not in data  # 确保API密钥不在响应中


@pytest.mark.asyncio
async def test_update_exchange(client: AsyncClient, auth_headers: dict, test_exchange):
    """测试更新交易所"""
    update_data = {
        "name": "Updated Exchange Name",
        "is_active": False
    }
    
    response = await client.put(
        f"/api/v1/exchanges/{test_exchange.id}",
        json=update_data,
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == update_data["name"]
    assert data["is_active"] == update_data["is_active"]


@pytest.mark.asyncio
async def test_delete_exchange(client: AsyncClient, auth_headers: dict, test_exchange):
    """测试删除交易所"""
    response = await client.delete(
        f"/api/v1/exchanges/{test_exchange.id}",
        headers=auth_headers
    )
    
    assert response.status_code == 204
    
    # 验证交易所已删除
    response = await client.get(
        f"/api/v1/exchanges/{test_exchange.id}",
        headers=auth_headers
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_validate_exchange_credentials(client: AsyncClient, auth_headers: dict, test_exchange):
    """测试验证交易所凭证"""
    response = await client.post(
        f"/api/v1/exchanges/{test_exchange.id}/validate",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "valid" in data
    assert "message" in data


@pytest.mark.asyncio
async def test_get_exchange_balance(client: AsyncClient, auth_headers: dict, test_exchange):
    """测试获取交易所余额"""
    response = await client.get(
        f"/api/v1/exchanges/{test_exchange.id}/balance",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "balances" in data
    assert isinstance(data["balances"], list)


@pytest.mark.asyncio
async def test_get_exchange_symbols(client: AsyncClient, auth_headers: dict, test_exchange):
    """测试获取交易所交易对"""
    response = await client.get(
        f"/api/v1/exchanges/{test_exchange.id}/symbols",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "symbols" in data
    assert isinstance(data["symbols"], list)


@pytest.mark.asyncio
async def test_unauthorized_access(client: AsyncClient, test_exchange):
    """测试未授权访问"""
    response = await client.get(f"/api/v1/exchanges/{test_exchange.id}")
    assert response.status_code == 401
    
    response = await client.get("/api/v1/exchanges/")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_exchange_not_found(client: AsyncClient, auth_headers: dict):
    """测试交易所不存在"""
    response = await client.get(
        "/api/v1/exchanges/99999",
        headers=auth_headers
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_create_exchange_invalid_data(client: AsyncClient, auth_headers: dict):
    """测试创建交易所时提供无效数据"""
    invalid_data = {
        "name": "",  # 空名称
        "exchange_type": "invalid_exchange",  # 无效交易所类型
        "api_key": "",  # 空API密钥
        "api_secret": "",  # 空API密钥
        "is_testnet": True,
        "is_active": True
    }
    
    response = await client.post(
        "/api/v1/exchanges/",
        json=invalid_data,
        headers=auth_headers
    )
    
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data


@pytest.mark.asyncio
async def test_create_duplicate_exchange(client: AsyncClient, auth_headers: dict, test_exchange):
    """测试创建重复交易所"""
    exchange_data = {
        "name": test_exchange.name,  # 使用已存在的名称
        "exchange_type": test_exchange.exchange_type,
        "api_key": "different_api_key",
        "api_secret": "different_api_secret",
        "is_testnet": True,
        "is_active": True
    }
    
    response = await client.post(
        "/api/v1/exchanges/",
        json=exchange_data,
        headers=auth_headers
    )
    
    assert response.status_code == 400
    data = response.json()
    assert "already exists" in data["detail"].lower()


@pytest.mark.asyncio
async def test_update_nonexistent_exchange(client: AsyncClient, auth_headers: dict):
    """测试更新不存在的交易所"""
    update_data = {
        "name": "Updated Exchange Name"
    }
    
    response = await client.put(
        "/api/v1/exchanges/99999",
        json=update_data,
        headers=auth_headers
    )
    
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_nonexistent_exchange(client: AsyncClient, auth_headers: dict):
    """测试删除不存在的交易所"""
    response = await client.delete(
        "/api/v1/exchanges/99999",
        headers=auth_headers
    )
    
    assert response.status_code == 404