import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.session import AsyncSessionLocal
from app.models.user import User
from app.utils.security import verify_password, get_password_hash
from sqlalchemy import select

async def test_auth():
    async with AsyncSessionLocal() as db:
        # 检查用户是否存在
        result = await db.execute(select(User).where(User.username == 'testuser'))
        user = result.scalar_one_or_none()
        
        if user:
            print(f'用户存在: {user.username}')
            print(f'密码哈希: {user.password_hash[:50]}...')
            print(f'密码验证结果: {verify_password("testpassword", user.password_hash)}')
            
            # 更新密码哈希
            user.password_hash = get_password_hash("testpassword")
            await db.commit()
            print('密码已更新')
        else:
            print('用户不存在')

if __name__ == "__main__":
    asyncio.run(test_auth())