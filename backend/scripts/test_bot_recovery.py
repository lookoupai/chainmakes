"""
测试机器人状态恢复机制

测试场景:
1. 启动一个机器人
2. 模拟应用重启 (不真正重启，只是测试恢复逻辑)
3. 验证机器人是否被正确恢复
"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.db.session import AsyncSessionLocal
from app.services.bot_manager import bot_manager
from sqlalchemy import select
from app.models.bot_instance import BotInstance


async def test_recovery():
    """测试机器人恢复机制"""
    
    print("=" * 70)
    print("测试机器人状态恢复机制")
    print("=" * 70)
    
    # 第一步：启动一个机器人
    print("\n[1] 启动机器人 ID=4...")
    async with AsyncSessionLocal() as db:
        success = await bot_manager.start_bot(4, db)
        if success:
            print("[OK] 机器人启动成功")
        else:
            print("[ERROR] 机器人启动失败")
            return
    
    # 等待机器人运行一段时间
    print("\n[2] 等待机器人运行 10 秒...")
    await asyncio.sleep(10)
    
    # 检查当前运行状态
    print("\n[3] 检查当前运行状态...")
    running_bots = await bot_manager.get_all_running_bots()
    print(f"   当前运行中的机器人: {list(running_bots.keys())}")
    
    # 检查数据库状态
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(BotInstance).where(BotInstance.id == 4)
        )
        bot = result.scalar_one_or_none()
        if bot:
            print(f"   数据库状态: {bot.status}")
            print(f"   当前循环: {bot.current_cycle}")
        
    # 第二步：模拟应用重启 - 清空运行列表但不停止机器人
    print("\n[4] 模拟应用重启 (清空 running_bots)...")
    bot_manager.running_bots.clear()
    bot_manager.bot_tasks.clear()
    print(f"   运行列表已清空: {list(bot_manager.running_bots.keys())}")
    
    # 第三步：执行恢复机制
    print("\n[5] 执行机器人恢复...")
    async with AsyncSessionLocal() as db:
        recovered_count = await bot_manager.recover_running_bots(db)
        print(f"[OK] 恢复了 {recovered_count} 个机器人")
    
    # 检查恢复后的状态
    print("\n[6] 检查恢复后的状态...")
    running_bots = await bot_manager.get_all_running_bots()
    print(f"   当前运行中的机器人: {list(running_bots.keys())}")
    
    # 等待机器人运行一段时间
    print("\n[7] 等待恢复后的机器人运行 10 秒...")
    await asyncio.sleep(10)
    
    # 检查最终状态
    print("\n[8] 检查最终状态...")
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(BotInstance).where(BotInstance.id == 4)
        )
        bot = result.scalar_one_or_none()
        if bot:
            print(f"   数据库状态: {bot.status}")
            print(f"   当前循环: {bot.current_cycle}")
            print(f"   总交易数: {bot.total_trades}")
    
    # 停止机器人
    print("\n[9] 停止机器人...")
    async with AsyncSessionLocal() as db:
        success = await bot_manager.stop_bot(4, db)
        if success:
            print("[OK] 机器人已停止")
        else:
            print("[ERROR] 机器人停止失败")
    
    print("\n" + "=" * 70)
    print("[OK] 测试完成")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(test_recovery())