"""
用户认证API测试
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
async def test_register_user(client: AsyncClient):
    """测试用户注册"""
    user_data = {
        "username": "newuser",
        "email": "newuser@example.com",
        "password": "newpassword123"
    }
    
    response = await client.post(
        "/api/v1/auth/register",
        json=user_data
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == user_data["username"]
    assert data["email"] == user_data["email"]
    assert "id" in data
    assert "password" not in data  # 确保密码不在响应中


@pytest.mark.asyncio
async def test_register_duplicate_username(client: AsyncClient, test_user):
    """测试注册重复用户名"""
    user_data = {
        "username": test_user.username,  # 使用已存在的用户名
        "email": "different@example.com",
        "password": "password123"
    }
    
    response = await client.post(
        "/api/v1/auth/register",
        json=user_data
    )
    
    assert response.status_code == 400
    data = response.json()
    assert "already registered" in data["detail"].lower()


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient, test_user):
    """测试注册重复邮箱"""
    user_data = {
        "username": "differentuser",
        "email": test_user.email,  # 使用已存在的邮箱
        "password": "password123"
    }
    
    response = await client.post(
        "/api/v1/auth/register",
        json=user_data
    )
    
    assert response.status_code == 400
    data = response.json()
    assert "already registered" in data["detail"].lower()


@pytest.mark.asyncio
async def test_register_invalid_data(client: AsyncClient):
    """测试注册时提供无效数据"""
    invalid_data = {
        "username": "",  # 空用户名
        "email": "invalid-email",  # 无效邮箱格式
        "password": "123"  # 密码太短
    }
    
    response = await client.post(
        "/api/v1/auth/register",
        json=invalid_data
    )
    
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient, test_user):
    """测试成功登录"""
    login_data = {
        "username": test_user.username,
        "password": "testpassword"
    }
    
    response = await client.post(
        "/api/v1/auth/login",
        data=login_data
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient, test_user):
    """测试错误密码登录"""
    login_data = {
        "username": test_user.username,
        "password": "wrongpassword"
    }
    
    response = await client.post(
        "/api/v1/auth/login",
        data=login_data
    )
    
    assert response.status_code == 401
    data = response.json()
    assert "incorrect" in data["detail"].lower()


@pytest.mark.asyncio
async def test_login_nonexistent_user(client: AsyncClient):
    """测试不存在的用户登录"""
    login_data = {
        "username": "nonexistentuser",
        "password": "password123"
    }
    
    response = await client.post(
        "/api/v1/auth/login",
        data=login_data
    )
    
    assert response.status_code == 401
    data = response.json()
    assert "incorrect" in data["detail"].lower()


@pytest.mark.asyncio
async def test_get_current_user(client: AsyncClient, auth_headers: dict, test_user):
    """测试获取当前用户信息"""
    response = await client.get(
        "/api/v1/auth/me",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == test_user.id
    assert data["username"] == test_user.username
    assert data["email"] == test_user.email


@pytest.mark.asyncio
async def test_get_current_user_unauthorized(client: AsyncClient):
    """测试未授权获取当前用户信息"""
    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 401
    
    # 测试无效token
    response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer invalid_token"}
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_change_password(client: AsyncClient, auth_headers: dict, test_user):
    """测试修改密码"""
    password_data = {
        "current_password": "testpassword",
        "new_password": "newtestpassword123"
    }
    
    response = await client.post(
        "/api/v1/auth/change-password",
        json=password_data,
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    
    # 验证新密码可以登录
    login_data = {
        "username": test_user.username,
        "password": "newtestpassword123"
    }
    
    response = await client.post(
        "/api/v1/auth/login",
        data=login_data
    )
    
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_change_password_wrong_current(client: AsyncClient, auth_headers: dict):
    """测试使用错误的当前密码修改密码"""
    password_data = {
        "current_password": "wrongpassword",
        "new_password": "newpassword123"
    }
    
    response = await client.post(
        "/api/v1/auth/change-password",
        json=password_data,
        headers=auth_headers
    )
    
    assert response.status_code == 400
    data = response.json()
    assert "incorrect" in data["detail"].lower()


@pytest.mark.asyncio
async def test_change_password_unauthorized(client: AsyncClient):
    """测试未授权修改密码"""
    password_data = {
        "current_password": "password",
        "new_password": "newpassword123"
    }
    
    response = await client.post(
        "/api/v1/auth/change-password",
        json=password_data
    )
    
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_logout(client: AsyncClient, auth_headers: dict):
    """测试登出"""
    response = await client.post(
        "/api/v1/auth/logout",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "message" in data