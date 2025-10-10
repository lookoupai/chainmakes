"""
创建模拟交易所账户的脚本
用于测试环境快速设置
"""
import asyncio
import sys
import os
from pathlib import Path

# 设置控制台输出编码为UTF-8
if sys.platform == 'win32':
    os.system('chcp 65001 > nul')

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import AsyncSessionLocal
from app.models.user import User
from app.models.exchange_account import ExchangeAccount
from app.utils.encryption import key_encryption


async def create_mock_exchange_account():
    """为admin用户创建一个模拟交易所账户"""
    async with AsyncSessionLocal() as db:
        try:
            # 查找admin用户
            result = await db.execute(
                select(User).where(User.username == "admin")
            )
            admin_user = result.scalar_one_or_none()
            
            if not admin_user:
                print("[ERROR] 未找到admin用户，请先运行init_db.py")
                return
            
            # 检查是否已存在Mock交易所账户
            result = await db.execute(
                select(ExchangeAccount).where(
                    ExchangeAccount.user_id == admin_user.id,
                    ExchangeAccount.exchange_name == "mock"
                )
            )
            existing_account = result.scalar_one_or_none()
            
            if existing_account:
                print("[OK] Mock交易所账户已存在")
                print(f"   - ID: {existing_account.id}")
                print(f"   - Exchange: {existing_account.exchange_name}")
                return
            
            # 创建模拟交易所账户
            # 注意：模拟交易所不需要真实的API密钥，但需要加密存储
            mock_account = ExchangeAccount(
                user_id=admin_user.id,
                exchange_name="mock",
                api_key=key_encryption.encrypt("mock_api_key_12345678"),
                api_secret=key_encryption.encrypt("mock_api_secret_87654321"),
                passphrase=None,
                is_active=True
            )
            
            db.add(mock_account)
            await db.commit()
            await db.refresh(mock_account)
            
            print("[OK] 成功创建模拟交易所账户:")
            print(f"   - ID: {mock_account.id}")
            print(f"   - User: {admin_user.username}")
            print(f"   - Exchange: {mock_account.exchange_name}")
            print(f"   - Status: {'Active' if mock_account.is_active else 'Inactive'}")
            print("\n现在可以在前端创建机器人时选择这个交易所账户了!")
            
        except Exception as e:
            print(f"[ERROR] 创建失败: {e}")
            await db.rollback()
            raise


async def main():
    """主函数"""
    print("=" * 60)
    print("创建模拟交易所账户")
    print("=" * 60)
    
    await create_mock_exchange_account()
    
    print("\n" + "=" * 60)
    print("完成!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())