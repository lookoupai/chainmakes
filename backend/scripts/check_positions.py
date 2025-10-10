"""
检查持仓情况诊断脚本

用于诊断平仓精度问题
"""
import asyncio
import sys
import os
from decimal import Decimal

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.exchanges.okx_exchange import OKXExchange
from app.config import settings
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from app.models.bot_instance import BotInstance
from app.models.position import Position


async def check_positions():
    """检查持仓情况"""

    # 创建数据库连接
    engine = create_async_engine(
        settings.DATABASE_URL_ASYNC,
        echo=False
    )
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as db:
        # 查询所有运行中的机器人
        result = await db.execute(
            select(BotInstance).where(BotInstance.status == 'running')
        )
        bots = result.scalars().all()

        if not bots:
            print("没有运行中的机器人")
            return

        for bot in bots:
            print(f"\n{'='*80}")
            print(f"机器人 ID: {bot.id}")
            print(f"机器人名称: {bot.bot_name}")
            print(f"市场1: {bot.market1_symbol}")
            print(f"市场2: {bot.market2_symbol}")
            print(f"DCA 次数: {bot.current_dca_count}")
            print(f"{'='*80}\n")

            # 初始化交易所
            try:
                exchange = OKXExchange(
                    api_key=settings.OKX_API_KEY,
                    api_secret=settings.OKX_API_SECRET,
                    passphrase=settings.OKX_PASSPHRASE,
                    is_testnet=settings.OKX_IS_DEMO,  # Fixed: is_testnet instead of is_demo
                    proxy=settings.OKX_PROXY
                )
                print("✅ 交易所连接成功")
            except Exception as e:
                print(f"❌ 交易所连接失败: {str(e)}")
                import traceback
                traceback.print_exc()
                continue

            # 查询数据库中的持仓
            try:
                db_positions_result = await db.execute(
                    select(Position)
                    .where(Position.bot_instance_id == bot.id)
                    .where(Position.is_open == True)
                )
                db_positions = db_positions_result.scalars().all()

                print("📊 数据库持仓记录:")
                if not db_positions:
                    print("  无持仓记录")
                else:
                    for pos in db_positions:
                        print(f"  - {pos.symbol}: {pos.side}, 数量={pos.amount}, 入场价={pos.entry_price}")
            except Exception as e:
                print(f"  ❌ 查询数据库持仓失败: {str(e)}")
                import traceback
                traceback.print_exc()
                db_positions = []

            # 查询交易所实际持仓
            print("\n🔍 交易所实际持仓:")
            try:
                # 检查 market1
                market1_pos = await exchange.get_position(bot.market1_symbol)
                if market1_pos:
                    print(f"  - {bot.market1_symbol}:")
                    print(f"      方向: {market1_pos['side']}")
                    print(f"      数量: {market1_pos['amount']} (类型: {type(market1_pos['amount'])})")
                    print(f"      入场价: {market1_pos['entry_price']}")
                    print(f"      当前价: {market1_pos['current_price']}")
                    print(f"      未实现盈亏: {market1_pos['unrealized_pnl']}")

                    # 检查精度
                    min_amount = Decimal('0.01')
                    if market1_pos['amount'] < min_amount:
                        print(f"      ⚠️ 警告: 数量小于最小精度 {min_amount}")
                else:
                    print(f"  - {bot.market1_symbol}: 无持仓")

                # 检查 market2
                market2_pos = await exchange.get_position(bot.market2_symbol)
                if market2_pos:
                    print(f"  - {bot.market2_symbol}:")
                    print(f"      方向: {market2_pos['side']}")
                    print(f"      数量: {market2_pos['amount']} (类型: {type(market2_pos['amount'])})")
                    print(f"      入场价: {market2_pos['entry_price']}")
                    print(f"      当前价: {market2_pos['current_price']}")
                    print(f"      未实现盈亏: {market2_pos['unrealized_pnl']}")

                    # 检查精度
                    min_amount = Decimal('0.01')
                    if market2_pos['amount'] < min_amount:
                        print(f"      ⚠️ 警告: 数量小于最小精度 {min_amount}")
                else:
                    print(f"  - {bot.market2_symbol}: 无持仓")

            except Exception as e:
                print(f"  ❌ 获取持仓失败: {str(e)}")
                import traceback
                traceback.print_exc()

            # 数据对比
            print("\n🔄 数据对比:")
            db_symbols = {pos.symbol for pos in db_positions}

            for symbol in [bot.market1_symbol, bot.market2_symbol]:
                has_db = symbol in db_symbols

                try:
                    exchange_pos = await exchange.get_position(symbol)
                    has_exchange = exchange_pos is not None
                except Exception as e:
                    has_exchange = False
                    print(f"  ⚠️ 获取 {symbol} 持仓失败: {str(e)}")

                status = "✅" if has_db == has_exchange else "❌"
                print(f"  {status} {symbol}: 数据库={has_db}, 交易所={has_exchange}")

            try:
                await exchange.close()
            except Exception as e:
                print(f"  ⚠️ 关闭交易所连接失败: {str(e)}")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(check_positions())
