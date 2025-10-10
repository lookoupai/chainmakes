"""
诊断价差计算问题
"""
import asyncio
import sys
from pathlib import Path
from decimal import Decimal

sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import select
from app.db.session import AsyncSessionLocal
from app.models.bot_instance import BotInstance
from app.models.spread_history import SpreadHistory


async def main():
    async with AsyncSessionLocal() as db:
        # 查询机器人配置
        result = await db.execute(select(BotInstance).where(BotInstance.id == 11))
        bot = result.scalar_one_or_none()
        
        if not bot:
            print("❌ 未找到 Bot ID 11")
            return
        
        print('='*80)
        print(f'机器人: {bot.bot_name}')
        print(f'状态: {bot.status}')
        print(f'Market 1: {bot.market1_symbol}')
        print(f'Market 2: {bot.market2_symbol}')
        print(f'起始价格1: {bot.market1_start_price}')
        print(f'起始价格2: {bot.market2_start_price}')
        print(f'启动时间: {bot.start_time}')
        print(f'DCA配置第1次: spread={bot.dca_config[0]["spread"]}%')
        print('='*80)
        
        # 查询最近10条价差记录
        result = await db.execute(
            select(SpreadHistory)
            .where(SpreadHistory.bot_instance_id == 11)
            .order_by(SpreadHistory.recorded_at.desc())
            .limit(10)
        )
        records = result.scalars().all()
        
        if not records:
            print("\n❌ 没有找到价差历史记录")
            return
        
        print(f'\n最近10条价差记录:')
        print('-'*80)
        print(f'{"时间":<10} | {"Market1价格":<12} | {"M1涨幅":<10} | {"Market2价格":<12} | {"M2涨幅":<10} | {"记录价差":<10}')
        print('-'*80)
        
        for r in records:
            if bot.market1_start_price and bot.market2_start_price:
                m1_change = (float(r.market1_price) / float(bot.market1_start_price) - 1) * 100
                m2_change = (float(r.market2_price) / float(bot.market2_start_price) - 1) * 100
                calculated_spread = m1_change - m2_change
                
                print(f'{r.recorded_at.strftime("%H:%M:%S"):<10} | '
                      f'{float(r.market1_price):>12.2f} | '
                      f'{m1_change:>+9.2f}% | '
                      f'{float(r.market2_price):>12.2f} | '
                      f'{m2_change:>+9.2f}% | '
                      f'{float(r.spread_percentage):>+9.4f}%')
        
        # 分析问题
        print('\n' + '='*80)
        print('问题分析:')
        print('='*80)
        
        latest = records[0]
        if bot.market1_start_price and bot.market2_start_price:
            m1_change = (float(latest.market1_price) / float(bot.market1_start_price) - 1) * 100
            m2_change = (float(latest.market2_price) / float(bot.market2_start_price) - 1) * 100
            calculated_spread = m1_change - m2_change
            
            print(f'当前 Market1 ({bot.market1_symbol}):')
            print(f'  起始价格: {float(bot.market1_start_price):.2f}')
            print(f'  当前价格: {float(latest.market1_price):.2f}')
            print(f'  涨跌幅: {m1_change:+.2f}%')
            print()
            print(f'当前 Market2 ({bot.market2_symbol}):')
            print(f'  起始价格: {float(bot.market2_start_price):.2f}')
            print(f'  当前价格: {float(latest.market2_price):.2f}')
            print(f'  涨跌幅: {m2_change:+.2f}%')
            print()
            print(f'计算价差: {m1_change:.2f}% - {m2_change:.2f}% = {calculated_spread:+.4f}%')
            print(f'数据库记录价差: {float(latest.spread_percentage):+.4f}%')
            print(f'开仓阈值: {bot.dca_config[0]["spread"]}%')
            print()
            
            if abs(calculated_spread) >= bot.dca_config[0]["spread"]:
                print(f'✅ 价差 {abs(calculated_spread):.2f}% >= 阈值 {bot.dca_config[0]["spread"]}%，应该开仓！')
                print(f'❌ 但是机器人没有开仓，说明计算逻辑有问题！')
            else:
                print(f'❌ 价差 {abs(calculated_spread):.2f}% < 阈值 {bot.dca_config[0]["spread"]}%，不满足开仓条件')
        else:
            print('❌ 起始价格未设置')


if __name__ == "__main__":
    asyncio.run(main())