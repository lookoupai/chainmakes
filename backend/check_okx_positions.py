"""
检查 OKX 实际持仓
"""
import asyncio
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.config import settings
from app.exchanges.okx_exchange import OKXExchange

async def check_positions():
    # 初始化 OKX 交易所
    exchange = OKXExchange(
        api_key=settings.OKX_API_KEY,
        api_secret=settings.OKX_API_SECRET,
        passphrase=settings.OKX_PASSPHRASE,
        is_testnet=settings.OKX_IS_DEMO,
        proxy=settings.OKX_PROXY
    )

    try:
        # 获取所有持仓
        positions = await exchange.get_all_positions()

        print(f"总持仓数: {len(positions)}\n")

        for pos in positions:
            print(f"交易对: {pos['symbol']}")
            print(f"方向: {pos['side']}")
            print(f"数量: {pos['amount']}")
            print(f"开仓价: {pos['entry_price']}")

            # 计算持仓价值（考虑杠杆）
            position_value = float(pos['amount']) * float(pos['entry_price'])
            print(f"持仓价值: {position_value:.2f} USDT")

            if pos.get('leverage'):
                print(f"杠杆: {pos['leverage']}x")

            print(f"未实现盈亏: {pos.get('unrealized_pnl', 0)}")
            print("-" * 50)

    finally:
        await exchange.close()

if __name__ == "__main__":
    asyncio.run(check_positions())
