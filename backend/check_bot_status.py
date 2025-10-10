import sqlite3
import json

conn = sqlite3.connect('trading_bot.db')
cursor = conn.cursor()

print("=" * 80)
print("机器人配置信息")
print("=" * 80)

cursor.execute('''
    SELECT id, bot_name, status, market1_symbol, market2_symbol, 
           investment_per_order, dca_config, current_dca_count, 
           last_trade_spread, first_trade_spread
    FROM bot_instances 
    ORDER BY id DESC LIMIT 5
''')

for row in cursor.fetchall():
    print(f"\n机器人ID: {row[0]}")
    print(f"名称: {row[1]}")
    print(f"状态: {row[2]}")
    print(f"市场1: {row[3]}")
    print(f"市场2: {row[4]}")
    print(f"每次投资金额: {row[5]}")
    print(f"DCA配置: {row[6]}")
    print(f"当前DCA次数: {row[7]}")
    print(f"上次交易价差: {row[8]}")
    print(f"首次交易价差: {row[9]}")
    print("-" * 80)

print("\n" + "=" * 80)
print("最近的价差历史 (最新10条)")
print("=" * 80)

cursor.execute('''
    SELECT bot_instance_id, market1_price, market2_price, 
           spread_percentage, recorded_at
    FROM spread_history 
    ORDER BY recorded_at DESC LIMIT 10
''')

for row in cursor.fetchall():
    print(f"机器人ID: {row[0]}, 价差: {row[3]:.4f}%, 时间: {row[4]}")

conn.close()