"""
创建测试机器人和交易所账户
快速生成测试数据以便测试前端功能
"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timezone

from app.db.session import AsyncSessionLocal
from app.models.user import User
from app.models.exchange_account import ExchangeAccount
from app.models.bot_instance import BotInstance
from app.utils.encryption import key_encryption


async def create_test_data():
    """创建测试数据"""
    async with AsyncSessionLocal() as db:
        # 1. 获取admin用户
        result = await db.execute(
            select(User).where(User.username == "admin")
        )
        admin_user = result.scalar_one_or_none()

        if not admin_user:
            print("[ERROR] 找不到admin用户,请先运行 init_db.py")
            return

        print(f"[OK] 找到用户: {admin_user.username} (ID: {admin_user.id})")

        # 2. 检查是否已有交易所账户
        result = await db.execute(
            select(ExchangeAccount).where(
                ExchangeAccount.user_id == admin_user.id
            )
        )
        exchange_account = result.scalar_one_or_none()

        if not exchange_account:
            # 创建测试交易所账户
            print("\n[INFO] 创建测试交易所账户...")
            exchange_account = ExchangeAccount(
                user_id=admin_user.id,
                exchange_name="okx",
                api_key=key_encryption.encrypt("test-api-key-12345"),
                api_secret=key_encryption.encrypt("test-api-secret-67890"),
                passphrase=key_encryption.encrypt("test-passphrase"),
                is_active=True
            )
            db.add(exchange_account)
            await db.commit()
            await db.refresh(exchange_account)
            print(f"[OK] 交易所账户已创建 (ID: {exchange_account.id})")
        else:
            print(f"[OK] 使用现有交易所账户 (ID: {exchange_account.id})")

        # 3. 检查是否已有测试机器人
        result = await db.execute(
            select(BotInstance).where(
                BotInstance.user_id == admin_user.id,
                BotInstance.bot_name == "测试机器人"
            )
        )
        existing_bot = result.scalar_one_or_none()

        if existing_bot:
            print(f"\n[WARN] 测试机器人已存在 (ID: {existing_bot.id})")
            print(f"       访问: http://localhost:3333/bots/detail/{existing_bot.id}")
            return

        # 4. 创建测试机器人
        print("\n[INFO] 创建测试机器人...")
        test_bot = BotInstance(
            user_id=admin_user.id,
            exchange_account_id=exchange_account.id,
            bot_name="测试机器人",
            market1_symbol="BTC-USDT-SWAP",
            market2_symbol="ETH-USDT-SWAP",
            start_time=datetime(2025, 10, 1, 0, 0, 0, tzinfo=timezone.utc),
            leverage=10,
            order_type_open="market",
            order_type_close="market",
            investment_per_order=100.0,
            max_position_value=1000.0,
            max_dca_times=3,
            dca_config=[
                {"times": 1, "spread": 1.0, "multiplier": 1.0},
                {"times": 2, "spread": 2.0, "multiplier": 1.5},
                {"times": 3, "spread": 3.0, "multiplier": 2.0}
            ],
            profit_mode="position",
            profit_ratio=2.0,
            stop_loss_ratio=5.0,
            pause_after_close=True,
            status="stopped",
            current_cycle=0,
            total_profit=0.0,
            total_trades=0
        )

        db.add(test_bot)
        await db.commit()
        await db.refresh(test_bot)

        print(f"[OK] 测试机器人已创建 (ID: {test_bot.id})")
        print("\n" + "="*60)
        print("SUCCESS! 测试数据创建成功!")
        print("="*60)
        print(f"\n访问机器人详情页:")
        print(f"   http://localhost:3333/bots/detail/{test_bot.id}")
        print(f"\n提示:")
        print(f"   - 订单历史、持仓、价差图表将显示模拟数据")
        print(f"   - 可以点击'启动'按钮测试状态切换")
        print(f"   - 可以点击'编辑'按钮测试配置修改")
        print("="*60)


if __name__ == "__main__":
    print("="*60)
    print("ChainMakes - 创建测试数据")
    print("="*60)
    asyncio.run(create_test_data())
