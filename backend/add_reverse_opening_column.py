"""
添加 reverse_opening 字段到 bot_instances 表的数据库迁移脚本

使用方法：
1. 确保后端虚拟环境已激活
2. 运行: python add_reverse_opening_column.py
"""
import asyncio
import sys
import os
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent))

# 确保加载 .env 文件
from dotenv import load_dotenv
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)

from sqlalchemy import text
from app.db.session import engine
from app.utils.logger import setup_logger

logger = setup_logger('db_migration')


async def add_reverse_opening_column():
    """添加 reverse_opening 字段到 bot_instances 表"""
    
    async with engine.begin() as conn:
        try:
            # 检查列是否已存在 (SQLite 专用语法)
            check_query = text("""
                PRAGMA table_info(bot_instances)
            """)
            
            result = await conn.execute(check_query)
            columns = result.fetchall()
            
            # 检查是否已有 reverse_opening 列
            column_names = [col[1] for col in columns]
            
            if 'reverse_opening' in column_names:
                logger.info("reverse_opening 字段已存在，无需添加")
                return
            
            # 添加列（默认值为 False，NOT NULL）
            logger.info("开始添加 reverse_opening 字段...")
            
            alter_query = text("""
                ALTER TABLE bot_instances 
                ADD COLUMN reverse_opening BOOLEAN NOT NULL DEFAULT FALSE
            """)
            
            await conn.execute(alter_query)
            
            logger.info("reverse_opening 字段添加成功")
            
            # 验证添加结果 (SQLite 专用)
            verify_query = text("""
                PRAGMA table_info(bot_instances)
            """)
            
            result = await conn.execute(verify_query)
            columns = result.fetchall()
            
            # 查找 reverse_opening 列
            reverse_opening_col = None
            for col in columns:
                if col[1] == 'reverse_opening':
                    reverse_opening_col = col
                    break
            
            if reverse_opening_col:
                logger.info(f"列信息: name={reverse_opening_col[1]}, type={reverse_opening_col[2]}, notnull={reverse_opening_col[3]}, default={reverse_opening_col[4]}")
            
            # 统计现有机器人数量
            count_query = text("SELECT COUNT(*) FROM bot_instances")
            result = await conn.execute(count_query)
            count = result.scalar()
            
            logger.info(f"数据库中共有 {count} 个机器人，已全部设置为默认值 (reverse_opening=False)")
            
        except Exception as e:
            logger.error(f"添加字段失败: {str(e)}", exc_info=True)
            raise


async def main():
    """主函数"""
    logger.info("=" * 60)
    logger.info("开始数据库迁移：添加 reverse_opening 字段")
    logger.info("=" * 60)
    
    try:
        await add_reverse_opening_column()
        logger.info("=" * 60)
        logger.info("数据库迁移完成")
        logger.info("=" * 60)
    except Exception as e:
        logger.error(f"数据库迁移失败: {str(e)}")
        sys.exit(1)
    finally:
        # 关闭引擎
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
