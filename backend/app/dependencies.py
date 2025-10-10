"""
FastAPI依赖注入模块
"""
import logging
from typing import AsyncGenerator
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import AsyncSessionLocal
from app.models.user import User
from app.models.bot_instance import BotInstance
from app.utils.security import verify_token

# 配置日志
logger = logging.getLogger(__name__)

# OAuth2密码流 - 使用auto_error=False来手动处理认证错误
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    数据库会话依赖注入
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    获取当前登录用户
    
    Args:
        token: JWT访问令牌
        db: 数据库会话
        
    Returns:
        当前用户对象
        
    Raises:
        HTTPException: 认证失败
    """
    # 添加调试日志
    logger.warning(f"========== GET_CURRENT_USER CALLED ==========")
    logger.warning(f"Token received: {token[:50] if token else 'None'}...")
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无法验证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # 检查token是否存在
    if token is None:
        logger.warning("No token provided!")
        raise credentials_exception
    
    # 验证令牌
    payload = verify_token(token, "access")
    logger.warning(f"Token payload: {payload}")
    if payload is None:
        logger.warning("Token verification failed!")
        raise credentials_exception
    
    # 兼容sub为字符串/数字, 强制转为int
    user_id_raw = payload.get("uid") or payload.get("sub")
    try:
        user_id = int(user_id_raw)
    except (TypeError, ValueError):
        logger.warning(f"Invalid 'sub' in token: {user_id_raw!r}")
        raise credentials_exception
    
    # 从数据库获取用户
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if user is None:
        raise credentials_exception
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用户账户已被禁用"
        )
    
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    获取当前活跃用户
    
    Args:
        current_user: 当前用户
        
    Returns:
        活跃用户对象
        
    Raises:
        HTTPException: 用户未激活
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用户账户未激活"
        )
    return current_user


async def check_admin_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    检查是否为管理员用户
    
    Args:
        current_user: 当前用户
        
    Returns:
        管理员用户对象
        
    Raises:
        HTTPException: 权限不足
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足,需要管理员权限"
        )
    return current_user


async def check_bot_ownership(
    bot_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> BotInstance:
    """
    检查用户是否拥有指定的机器人
    
    Args:
        bot_id: 机器人ID
        current_user: 当前用户
        db: 数据库会话
        
    Returns:
        机器人实例
        
    Raises:
        HTTPException: 机器人不存在或无权访问
    """
    result = await db.execute(
        select(BotInstance).where(BotInstance.id == bot_id)
    )
    bot = result.scalar_one_or_none()
    
    if bot is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="机器人不存在"
        )
    
    if bot.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问此机器人"
        )
    
    return bot