"""
测试错误监控工具
用于验证错误监控功能是否正常工作
"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime

# 添加后端路径到系统路径
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from sqlalchemy import select
from app.db.session import AsyncSessionLocal
from app.models.trade_log import TradeLog
from app.models.bot_instance import BotInstance


async def create_test_errors():
    """创建测试错误日志"""
    async with AsyncSessionLocal() as db:
        try:
            # 获取第一个运行中的机器人
            result = await db.execute(
                select(BotInstance).where(BotInstance.status == "running").limit(1)
            )
            bot = result.scalar_one_or_none()
            
            if not bot:
                print("❌ 没有找到运行中的机器人，请先启动一个机器人")
                return
            
            print(f"✓ 找到机器人: [{bot.id}] {bot.bot_name}")
            print(f"\n正在创建测试错误日志...\n")
            
            # 创建不同类型的测试错误
            test_errors = [
                "API错误测试: API request timeout",
                "网络错误测试: Connection refused",
                "交易错误测试: Order execution failed",
                "余额不足测试: Insufficient balance for order",
                "持仓错误测试: Position update failed",
            ]
            
            for i, error_msg in enumerate(test_errors, 1):
                log = TradeLog(
                    bot_instance_id=bot.id,
                    log_type="error",
                    message=error_msg
                )
                db.add(log)
                await db.commit()
                
                print(f"✓ 创建测试错误 {i}/{len(test_errors)}: {error_msg}")
                await asyncio.sleep(1)  # 间隔1秒
            
            print(f"\n✅ 成功创建 {len(test_errors)} 个测试错误日志")
            print(f"\n现在可以启动错误监控工具来查看这些错误:")
            print(f"  ./启动错误监控.bat")
            print(f"\n或运行:")
            print(f"  cd backend")
            print(f"  python scripts/monitor_trading_errors.py")
            
        except Exception as e:
            print(f"❌ 创建测试错误失败: {str(e)}")
            import traceback
            traceback.print_exc()


async def main():
    """主函数"""
    print("="*80)
    print("错误监控工具测试脚本")
    print("="*80)
    print()
    
    await create_test_errors()


if __name__ == "__main__":
    asyncio.run(main())