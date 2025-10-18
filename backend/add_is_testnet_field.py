"""
数据库迁移脚本: 为 exchange_accounts 表添加 is_testnet 字段
"""
import sqlite3
import os

# 数据库文件路径
import sys
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "chainmakes.db")


def migrate_database():
    """执行数据库迁移"""
    print("=" * 60)
    print("数据库迁移: 添加 is_testnet 字段")
    print("=" * 60)
    
    if not os.path.exists(DB_PATH):
        print(f"\n[ERROR] 数据库文件不存在: {DB_PATH}")
        print("请先运行应用以创建数据库，或检查路径是否正确")
        return False
    
    try:
        # 连接数据库
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 检查字段是否已存在
        cursor.execute("PRAGMA table_info(exchange_accounts)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'is_testnet' in columns:
            print("\n[INFO] is_testnet 字段已存在，无需迁移")
            conn.close()
            return True
        
        print("\n[1] 开始添加 is_testnet 字段...")
        
        # 添加新字段，默认值为 1 (True，测试网)
        cursor.execute("""
            ALTER TABLE exchange_accounts 
            ADD COLUMN is_testnet BOOLEAN NOT NULL DEFAULT 1
        """)
        
        print("[OK] is_testnet 字段添加成功")
        
        # 提交更改
        conn.commit()
        
        # 验证字段是否添加成功
        cursor.execute("PRAGMA table_info(exchange_accounts)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'is_testnet' in columns:
            print("\n[2] 验证字段添加...")
            print("[OK] is_testnet 字段验证成功")
            
            # 查询现有账户数量
            cursor.execute("SELECT COUNT(*) FROM exchange_accounts")
            count = cursor.fetchone()[0]
            print(f"\n[3] 现有交易所账户数量: {count}")
            
            if count > 0:
                print("[INFO] 所有现有账户的 is_testnet 默认设置为 True (测试网)")
                print("[INFO] 如需修改，请在前端界面编辑交易所账户")
        else:
            print("\n[ERROR] 字段验证失败")
            return False
        
        # 关闭连接
        conn.close()
        
        print("\n" + "=" * 60)
        print("[SUCCESS] 数据库迁移完成")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n[ERROR] 数据库迁移失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = migrate_database()
    exit(0 if success else 1)
