"""
重置机器人状态为 stopped
"""
import asyncio
from sqlalchemy import select, update
from app.db.session import AsyncSessionLocal
from app.models.bot_instance import BotInstance

async def reset_bot_status(bot_id: int):
    """重置指定机器人的状态为 stopped"""
    async with AsyncSessionLocal() as db:
        # 更新机器人状态
        stmt = (
            update(BotInstance)
            .where(BotInstance.id == bot_id)
            .values(status="stopped")
        )
        await db.execute(stmt)
        await db.commit()
        
        # 验证更新
        result = await db.execute(
            select(BotInstance).where(BotInstance.id == bot_id)
        )
        bot = result.scalar_one_or_none()
        
        if bot:
            print(f"机器人 {bot_id} ({bot.bot_name}) 状态已重置为: {bot.status}")
        else:
            print(f"机器人 {bot_id} 不存在")

async def main():
    """重置所有机器人状态"""
    print("重置机器人状态...")
    
    # 重置机器人 ID 4
    await reset_bot_status(4)
    
    print("\n完成！")

if __name__ == "__main__":
    asyncio.run(main())