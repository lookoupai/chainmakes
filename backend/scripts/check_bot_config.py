"""
查看机器人配置
"""
import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.session import AsyncSessionLocal
from app.models.bot_instance import BotInstance
from sqlalchemy import select


async def check_bot_config():
    """查看机器人配置"""
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(BotInstance).where(BotInstance.id == 4)
        )
        bot = result.scalar_one()
        
        print("=" * 70)
        print("机器人配置详情")
        print("=" * 70)
        print(f"机器人名称: {bot.bot_name}")
        print(f"交易对1: {bot.market1_symbol}")
        print(f"交易对2: {bot.market2_symbol}")
        print(f"\n开仓配置:")
        print(f"  DCA配置: {bot.dca_config}")
        print(f"  当前DCA次数: {bot.current_dca_count}")
        print(f"  最大DCA次数: {bot.max_dca_times}")
        print(f"  每单投资: ${bot.investment_per_order}")
        print(f"\n价差信息:")
        print(f"  首次开仓价差: {bot.first_trade_spread}")
        print(f"  上次交易价差: {bot.last_trade_spread}")
        print(f"\n止盈止损:")
        print(f"  止盈模式: {bot.profit_mode}")
        print(f"  止盈比例: {bot.profit_ratio}%")
        print(f"  止损比例: {bot.stop_loss_ratio}%")
        print(f"\n统计信息:")
        print(f"  当前状态: {bot.status}")
        print(f"  当前循环: {bot.current_cycle}")
        print(f"  总交易次数: {bot.total_trades}")
        print(f"  总收益: ${bot.total_profit}")
        print("=" * 70)


if __name__ == "__main__":
    asyncio.run(check_bot_config())