import asyncio
import sys
import os
from datetime import datetime
from decimal import Decimal

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.session import AsyncSessionLocal
from app.models.bot_instance import BotInstance
from app.models.exchange_account import ExchangeAccount
from app.services.bot_service import BotService
from app.utils.logger import setup_logger
from sqlalchemy import select

logger = setup_logger('test_trading_engine')

async def test_bot_start_stop():
    """测试机器人启动和停止"""
    print("测试机器人启动和停止")
    
    async with AsyncSessionLocal() as db:
        # 获取测试机器人
        result = await db.execute(
            select(BotInstance).where(BotInstance.id == 3)
        )
        bot = result.scalar_one_or_none()
        
        if not bot:
            print("测试机器人不存在")
            return
        
        print(f"当前机器人状态: {bot.status}")
        
        # 测试启动机器人
        print("尝试启动机器人...")
        success = await BotService.start_bot(bot.id, db)
        
        if success:
            print("机器人启动成功")
            # 等待5秒让机器人运行
            await asyncio.sleep(5)
            
            # 检查机器人状态
            await db.refresh(bot)
            print(f"运行后机器人状态: {bot.status}")
            
            # 测试停止机器人
            print("尝试停止机器人...")
            success = await BotService.stop_bot(bot.id)
            
            if success:
                print("机器人停止成功")
                # 检查机器人状态
                await db.refresh(bot)
                print(f"停止后机器人状态: {bot.status}")
            else:
                print("机器人停止失败")
        else:
            print("机器人启动失败")

async def test_bot_pause_resume():
    """测试机器人暂停和恢复"""
    print("\n测试机器人暂停和恢复")
    
    async with AsyncSessionLocal() as db:
        # 获取测试机器人
        result = await db.execute(
            select(BotInstance).where(BotInstance.id == 3)
        )
        bot = result.scalar_one_or_none()
        
        if not bot:
            print("测试机器人不存在")
            return
        
        # 确保机器人处于停止状态
        if bot.status != "stopped":
            await BotService.stop_bot(bot.id)
            await asyncio.sleep(1)
        
        # 启动机器人
        print("启动机器人...")
        success = await BotService.start_bot(bot.id, db)
        
        if success:
            print("机器人启动成功")
            # 等待3秒让机器人运行
            await asyncio.sleep(3)
            
            # 测试暂停机器人
            print("尝试暂停机器人...")
            success = await BotService.pause_bot(bot.id)
            
            if success:
                print("机器人暂停成功")
                # 检查机器人状态
                await db.refresh(bot)
                print(f"暂停后机器人状态: {bot.status}")
                
                # 等待2秒
                await asyncio.sleep(2)
                
                # 重新启动机器人（恢复）
                print("尝试恢复机器人...")
                success = await BotService.start_bot(bot.id, db)
                
                if success:
                    print("机器人恢复成功")
                    # 等待2秒
                    await asyncio.sleep(2)
                else:
                    print("机器人恢复失败")
            else:
                print("机器人暂停失败")
            
            # 停止机器人
            await BotService.stop_bot(bot.id)
        else:
            print("机器人启动失败")

async def test_close_positions():
    """测试平仓功能"""
    print("\n测试平仓功能")
    
    async with AsyncSessionLocal() as db:
        # 获取测试机器人
        result = await db.execute(
            select(BotInstance).where(BotInstance.id == 3)
        )
        bot = result.scalar_one_or_none()
        
        if not bot:
            print("测试机器人不存在")
            return
        
        # 确保机器人处于停止状态
        if bot.status != "stopped":
            await BotService.stop_bot(bot.id)
            await asyncio.sleep(1)
        
        # 启动机器人
        print("启动机器人...")
        success = await BotService.start_bot(bot.id, db)
        
        if success:
            print("机器人启动成功")
            # 等待5秒让机器人运行
            await asyncio.sleep(5)
            
            # 测试平仓
            print("尝试平仓...")
            success = await BotService.close_all_positions(bot.id)
            
            if success:
                print("平仓指令发送成功")
            else:
                print("平仓指令发送失败")
            
            # 停止机器人
            await BotService.stop_bot(bot.id)
        else:
            print("机器人启动失败")

async def main():
    """主测试函数"""
    print("开始测试交易引擎和策略执行")
    print("=" * 50)
    
    try:
        # 测试机器人启动和停止
        await test_bot_start_stop()
        
        # 测试机器人暂停和恢复
        await test_bot_pause_resume()
        
        # 测试平仓功能
        await test_close_positions()
        
        print("\n" + "=" * 50)
        print("交易引擎测试完成")
        
    except Exception as e:
        logger.error(f"测试过程中出错: {str(e)}", exc_info=True)
        print(f"测试过程中出错: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())