"""
修复机器人起始价格
根据TradingView的涨跌幅反推正确的起始价格
"""
import asyncio
import sys
from pathlib import Path
from decimal import Decimal

sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import select
from app.db.session import AsyncSessionLocal
from app.models.bot_instance import BotInstance


async def main():
    print("="*80)
    print("修复机器人起始价格")
    print("="*80)
    print()
    
    # 从TradingView获取的数据
    print("从TradingView获取的涨跌幅:")
    print("  SOL: +5.7%")
    print("  LTC: +8.2%")
    print()
    
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(BotInstance).where(BotInstance.id == 11))
        bot = result.scalar_one_or_none()
        
        if not bot:
            print("❌ 未找到 Bot ID 11")
            return
        
        print(f"当前配置:")
        print(f"  起始价格1 (SOL): {bot.market1_start_price}")
        print(f"  起始价格2 (LTC): {bot.market2_start_price}")
        print()
        
        # 当前价格（从最近的记录获取）
        current_sol = 225.37
        current_ltc = 117.20
        
        print(f"当前价格:")
        print(f"  SOL: {current_sol}")
        print(f"  LTC: {current_ltc}")
        print()
        
        # 根据涨跌幅反推起始价格
        # 当前价格 = 起始价格 × (1 + 涨跌幅)
        # 起始价格 = 当前价格 / (1 + 涨跌幅)
        
        sol_start = current_sol / (1 + 0.057)
        ltc_start = current_ltc / (1 + 0.082)
        
        print(f"根据TradingView涨跌幅反推的起始价格:")
        print(f"  SOL: {sol_start:.2f}")
        print(f"  LTC: {ltc_start:.2f}")
        print()
        
        # 计算价差验证
        spread = 5.7 - 8.2
        print(f"价差验证: 5.7% - 8.2% = {spread}% (绝对值 {abs(spread)}%)")
        print(f"开仓阈值: 0.8%")
        print(f"是否应该开仓: {'✅ 是' if abs(spread) >= 0.8 else '❌ 否'}")
        print()
        
        # 询问是否更新
        print("="*80)
        response = input("是否更新起始价格？(yes/no): ").strip().lower()
        
        if response in ['yes', 'y', '是']:
            bot.market1_start_price = Decimal(str(sol_start))
            bot.market2_start_price = Decimal(str(ltc_start))
            await db.commit()
            print()
            print("✅ 起始价格已更新！")
            print(f"  新的SOL起始价格: {bot.market1_start_price}")
            print(f"  新的LTC起始价格: {bot.market2_start_price}")
            print()
            print("请重启机器人，机器人将使用新的起始价格计算价差。")
        else:
            print()
            print("❌ 已取消更新")


if __name__ == "__main__":
    asyncio.run(main())