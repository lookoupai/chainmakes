import sqlite3
import json

conn = sqlite3.connect('trading_bot.db')
cursor = conn.cursor()

# 查询机器人配置
cursor.execute("""
    SELECT id, bot_name, leverage, investment_per_order,
           market1_symbol, market2_symbol, current_dca_count,
           market1_start_price, market2_start_price
    FROM bot_instances
    WHERE id = 11
""")

bot = cursor.fetchone()
if bot:
    print(f"机器人 ID: {bot[0]}")
    print(f"名称: {bot[1]}")
    print(f"杠杆: {bot[2]}x")
    print(f"每单投资: {bot[3]} USDT")
    print(f"Market 1: {bot[4]}")
    print(f"Market 2: {bot[5]}")
    print(f"当前 DCA 次数: {bot[6]}")
    print(f"起始价格 1: {bot[7]}")
    print(f"起始价格 2: {bot[8]}")

# 查询持仓
cursor.execute("""
    SELECT symbol, side, amount, entry_price, current_price, unrealized_pnl
    FROM positions
    WHERE bot_instance_id = 11 AND is_open = 1
""")

positions = cursor.fetchall()
print(f"\n当前持仓:")
for pos in positions:
    symbol, side, amount, entry_price, current_price, pnl = pos
    position_value = float(amount) * float(entry_price)
    print(f"  {symbol}: {side}")
    print(f"    数量: {amount}")
    print(f"    开仓价: {entry_price}")
    print(f"    持仓价值: {position_value:.2f} USDT")
    print(f"    未实现盈亏: {pnl}")

conn.close()
