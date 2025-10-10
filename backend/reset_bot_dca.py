"""
重置机器人 DCA 状态
"""
import sqlite3

conn = sqlite3.connect('trading_bot.db')
cursor = conn.cursor()

# 重置机器人 11 的 DCA 状态
cursor.execute("""
    UPDATE bot_instances
    SET current_dca_count = 0,
        last_trade_spread = NULL,
        first_trade_spread = NULL,
        current_cycle = current_cycle + 1
    WHERE id = 11
""")

conn.commit()
print(f"已重置机器人 11 的 DCA 状态")
print(f"- current_dca_count: 0")
print(f"- last_trade_spread: NULL")
print(f"- first_trade_spread: NULL")
print(f"下次开仓将使用 300 USDT (multiplier=1.0)")

conn.close()
