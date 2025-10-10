"""
修正数据库中持仓的 side 值

将 'buy'/'sell' (订单方向) 转换为 'long'/'short' (持仓方向)
"""
import sqlite3

def fix_position_sides():
    conn = sqlite3.connect('trading_bot.db')
    cursor = conn.cursor()

    # 查询所有持仓
    cursor.execute("SELECT id, symbol, side FROM positions")
    positions = cursor.fetchall()

    fixed_count = 0
    for pos_id, symbol, side in positions:
        new_side = None
        if side == 'buy':
            new_side = 'long'
            fixed_count += 1
        elif side == 'sell':
            new_side = 'short'
            fixed_count += 1

        if new_side:
            cursor.execute(
                "UPDATE positions SET side = ? WHERE id = ?",
                (new_side, pos_id)
            )
            print(f"修正持仓 {pos_id} ({symbol}): {side} → {new_side}")

    conn.commit()
    conn.close()

    print(f"\n✅ 修正完成，共修正 {fixed_count} 条记录")


if __name__ == "__main__":
    print("开始修正数据库中的持仓 side 值...")
    fix_position_sides()
