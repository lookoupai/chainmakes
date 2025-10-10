import sqlite3

conn = sqlite3.connect('trading_bot.db')
cursor = conn.cursor()

print("\n=== Checking Database ===\n")

# Check bots
cursor.execute('SELECT id, bot_name, status, user_id FROM bot_instances')
bots = cursor.fetchall()
print(f"Bot count: {len(bots)}")
for row in bots:
    print(f"  ID={row[0]}, Name={row[1]}, Status={row[2]}, UserID={row[3]}")

conn.close()
