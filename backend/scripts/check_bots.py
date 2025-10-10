import sqlite3
import sys
import os

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'trading_bot.db')

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute('SELECT id, bot_name, status, market1_symbol, market2_symbol, created_at FROM bot_instances')
rows = cursor.fetchall()

print(f"Found {len(rows)} bots in database:")
print("-" * 80)

for row in rows:
    print(f"ID: {row[0]}")
    print(f"Name: {row[1]}")
    print(f"Status: {row[2]}")
    print(f"Market1: {row[3]}")
    print(f"Market2: {row[4]}")
    print(f"Created: {row[5]}")
    print("-" * 80)

conn.close()