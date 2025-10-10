"""
交易所账户管理相关的API路由
"""
import asyncio
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.dependencies import get_db, get_current_user
from app.models.user import User
from app.models.exchange_account import ExchangeAccount
from app.schemas.exchange import (
    ExchangeAccountCreate,
    ExchangeAccountUpdate,
    ExchangeAccountResponse
)
from app.utils.encryption import key_encryption
from app.exchanges.exchange_factory import ExchangeFactory

router = APIRouter()


@router.post("/", response_model=ExchangeAccountResponse, status_code=status.HTTP_201_CREATED)
async def create_exchange_account(
    account_data: ExchangeAccountCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    创建交易所账户
    
    - **exchange_name**: 交易所名称(okx/binance/bybit)
    - **api_key**: API密钥
    - **api_secret**: API密钥
    - **passphrase**: API密码(仅OKX需要)
    """
    # 检查该交易所账户是否已存在
    result = await db.execute(
        select(ExchangeAccount).where(
            ExchangeAccount.user_id == current_user.id,
            ExchangeAccount.exchange_name == account_data.exchange_name
        )
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"您已添加过{account_data.exchange_name}交易所账户"
        )
    
    # 加密API密钥
    encrypted_api_key = key_encryption.encrypt(account_data.api_key)
    encrypted_api_secret = key_encryption.encrypt(account_data.api_secret)
    encrypted_passphrase = (
        key_encryption.encrypt(account_data.passphrase)
        if account_data.passphrase
        else None
    )
    
    # 创建交易所账户
    new_account = ExchangeAccount(
        user_id=current_user.id,
        exchange_name=account_data.exchange_name,
        api_key=encrypted_api_key,
        api_secret=encrypted_api_secret,
        passphrase=encrypted_passphrase
    )
    
    db.add(new_account)
    await db.commit()
    await db.refresh(new_account)
    
    return new_account


@router.get("/", response_model=List[ExchangeAccountResponse])
async def list_exchange_accounts(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取当前用户的所有交易所账户
    """
    result = await db.execute(
        select(ExchangeAccount).where(ExchangeAccount.user_id == current_user.id)
    )
    accounts = result.scalars().all()
    
    return accounts


@router.get("/{account_id}", response_model=ExchangeAccountResponse)
async def get_exchange_account(
    account_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取指定的交易所账户详情
    
    Args:
        account_id: 交易所账户ID
    
    Returns:
        交易所账户信息
    """
    result = await db.execute(
        select(ExchangeAccount).where(
            ExchangeAccount.id == account_id,
            ExchangeAccount.user_id == current_user.id
        )
    )
    account = result.scalar_one_or_none()
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="交易所账户不存在"
        )
    
    return account


@router.get("/{exchange_name}/symbols")
async def get_exchange_symbols(
    exchange_name: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取指定交易所支持的交易对列表
    
    Args:
        exchange_name: 交易所名称(mock/okx/binance等)
    
    Returns:
        交易对列表
    """
    # 对于模拟交易所，返回预定义的交易对列表
    if exchange_name.lower() == "mock":
        return {
            "symbols": [
                {"symbol": "BTC/USDT", "base": "BTC", "quote": "USDT"},
                {"symbol": "ETH/USDT", "base": "ETH", "quote": "USDT"},
                {"symbol": "BNB/USDT", "base": "BNB", "quote": "USDT"},
                {"symbol": "ADA/USDT", "base": "ADA", "quote": "USDT"},
                {"symbol": "SOL/USDT", "base": "SOL", "quote": "USDT"},
                {"symbol": "XRP/USDT", "base": "XRP", "quote": "USDT"},
                {"symbol": "DOT/USDT", "base": "DOT", "quote": "USDT"},
                {"symbol": "DOGE/USDT", "base": "DOGE", "quote": "USDT"},
                {"symbol": "MATIC/USDT", "base": "MATIC", "quote": "USDT"},
                {"symbol": "AVAX/USDT", "base": "AVAX", "quote": "USDT"}
            ]
        }
    
    # 对于真实交易所，需要查询用户的交易所账户
    result = await db.execute(
        select(ExchangeAccount).where(
            ExchangeAccount.user_id == current_user.id,
            ExchangeAccount.exchange_name == exchange_name
        )
    )
    account = result.scalar_one_or_none()
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"未找到{exchange_name}交易所账户"
        )
    
    try:
        # 解密API密钥
        api_key = key_encryption.decrypt(account.api_key)
        api_secret = key_encryption.decrypt(account.api_secret)
        passphrase = (
            key_encryption.decrypt(account.passphrase)
            if account.passphrase
            else None
        )
        
        # 创建交易所实例
        exchange = ExchangeFactory.create(
            exchange_name=exchange_name,
            api_key=api_key,
            api_secret=api_secret,
            passphrase=passphrase
        )
        
        # 获取交易所支持的市场
        markets = await exchange.exchange.load_markets()
        
        # 筛选永续合约交易对（USDT本位）
        symbols = []
        for symbol, market in markets.items():
            # OKX永续合约：type='swap' 且 quote='USDT'
            if market.get('type') == 'swap' and market.get('quote') == 'USDT':
                symbols.append({
                    "symbol": market['symbol'],  # CCXT格式: BTC/USDT:USDT
                    "base": market['base'],      # 基础货币: BTC
                    "quote": market['quote'],    # 计价货币: USDT
                    "id": market['id']           # OKX格式: BTC-USDT-SWAP
                })
        
        # 按交易量排序，返回前20个主流币种
        # 注：这里简化处理，实际应该按24h交易量排序
        popular_bases = ['BTC', 'ETH', 'BNB', 'SOL', 'XRP', 'ADA', 'DOGE', 'MATIC', 'DOT', 'AVAX',
                        'LINK', 'UNI', 'ATOM', 'LTC', 'ETC', 'FIL', 'APT', 'ARB', 'OP', 'SHIB']
        
        # 筛选主流币种
        filtered_symbols = [s for s in symbols if s['base'] in popular_bases]
        
        # 如果筛选后少于10个，就返回所有永续合约
        if len(filtered_symbols) < 10:
            filtered_symbols = symbols[:20]
        
        # 关闭交易所连接
        await exchange.close()
        
        return {
            "symbols": filtered_symbols
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取交易对列表失败: {str(e)}"
        )


@router.put("/{account_id}", response_model=ExchangeAccountResponse)
async def update_exchange_account(
    account_id: int,
    account_data: ExchangeAccountUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    更新交易所账户
    
    Args:
        account_id: 交易所账户ID
        account_data: 更新数据（只更新提供的字段）
    
    Returns:
        更新后的交易所账户信息
    """
    result = await db.execute(
        select(ExchangeAccount).where(
            ExchangeAccount.id == account_id,
            ExchangeAccount.user_id == current_user.id
        )
    )
    account = result.scalar_one_or_none()
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="交易所账户不存在"
        )
    
    # 更新提供的字段
    if account_data.api_key is not None:
        account.api_key = key_encryption.encrypt(account_data.api_key)
    
    if account_data.api_secret is not None:
        account.api_secret = key_encryption.encrypt(account_data.api_secret)
    
    if account_data.passphrase is not None:
        account.passphrase = key_encryption.encrypt(account_data.passphrase)
    
    if account_data.is_active is not None:
        account.is_active = account_data.is_active
    
    await db.commit()
    await db.refresh(account)
    
    return account


@router.patch("/{account_id}", response_model=ExchangeAccountResponse)
async def patch_exchange_account(
    account_id: int,
    account_data: ExchangeAccountUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    部分更新交易所账户（通常用于切换启用状态）
    
    Args:
        account_id: 交易所账户ID
        account_data: 更新数据（只更新提供的字段）
    
    Returns:
        更新后的交易所账户信息
    """
    result = await db.execute(
        select(ExchangeAccount).where(
            ExchangeAccount.id == account_id,
            ExchangeAccount.user_id == current_user.id
        )
    )
    account = result.scalar_one_or_none()
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="交易所账户不存在"
        )
    
    # 更新提供的字段
    if account_data.api_key is not None:
        account.api_key = key_encryption.encrypt(account_data.api_key)
    
    if account_data.api_secret is not None:
        account.api_secret = key_encryption.encrypt(account_data.api_secret)
    
    if account_data.passphrase is not None:
        account.passphrase = key_encryption.encrypt(account_data.passphrase)
    
    if account_data.is_active is not None:
        account.is_active = account_data.is_active
    
    await db.commit()
    await db.refresh(account)
    
    return account


@router.post("/{account_id}/test")
async def test_exchange_connection(
    account_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    测试交易所API连接
    
    Args:
        account_id: 交易所账户ID
    
    Returns:
        测试结果
    """
    result = await db.execute(
        select(ExchangeAccount).where(
            ExchangeAccount.id == account_id,
            ExchangeAccount.user_id == current_user.id
        )
    )
    account = result.scalar_one_or_none()
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="交易所账户不存在"
        )
    
    try:
        # 解密API密钥
        api_key = key_encryption.decrypt(account.api_key)
        api_secret = key_encryption.decrypt(account.api_secret)
        passphrase = (
            key_encryption.decrypt(account.passphrase)
            if account.passphrase
            else None
        )
        
        # 创建交易所实例
        exchange = ExchangeFactory.create(
            exchange_name=account.exchange_name,
            api_key=api_key,
            api_secret=api_secret,
            passphrase=passphrase
        )
        
        # 测试连接（获取账户余额），设置30秒超时（OKX需要通过代理，耗时较长）
        try:
            balance = await asyncio.wait_for(
                exchange.get_balance(),
                timeout=30.0
            )
            
            # 关闭交易所连接
            await exchange.close()
            
            return {
                "success": True,
                "message": f"{account.exchange_name.upper()} API连接测试成功",
                "balance": balance
            }
        except asyncio.TimeoutError:
            await exchange.close()
            return {
                "success": False,
                "message": "连接超时，请检查网络连接或API密钥是否正确"
            }
        except Exception as api_error:
            await exchange.close()
            error_msg = str(api_error)
            
            # 针对常见错误提供更友好的提示
            if "authentication" in error_msg.lower() or "invalid" in error_msg.lower():
                return {
                    "success": False,
                    "message": "API密钥验证失败，请检查API Key、Secret和Passphrase是否正确"
                }
            elif "permission" in error_msg.lower():
                return {
                    "success": False,
                    "message": "API权限不足，请确保API密钥有读取权限"
                }
            elif "network" in error_msg.lower() or "connection" in error_msg.lower():
                return {
                    "success": False,
                    "message": "网络连接失败，请检查网络连接或稍后重试"
                }
            else:
                return {
                    "success": False,
                    "message": f"连接测试失败: {error_msg}"
                }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"测试过程出错: {str(e)}"
        }


@router.delete("/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_exchange_account(
    account_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    删除交易所账户
    """
    result = await db.execute(
        select(ExchangeAccount).where(
            ExchangeAccount.id == account_id,
            ExchangeAccount.user_id == current_user.id
        )
    )
    account = result.scalar_one_or_none()
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="交易所账户不存在"
        )
    
    await db.delete(account)
    await db.commit()
    
    return None