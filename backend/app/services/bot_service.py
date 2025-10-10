"""
机器人管理服务层
"""
# 修改时间: 2025-10-06
from typing import Optional, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.bot_instance import BotInstance
from app.models.exchange_account import ExchangeAccount
from app.services.bot_manager import bot_manager
from app.utils.logger import setup_logger

logger = setup_logger('bot_service')


class BotService:
    """
    机器人管理服务
    
    负责管理机器人的生命周期,包括启动、暂停、停止等操作
    """
    
    @classmethod
    async def start_bot(cls, bot_id: int, db: AsyncSession) -> bool:
        """
        启动机器人
        
        Args:
            bot_id: 机器人ID
            db: 数据库会话
            
        Returns:
            是否成功启动
        """
        try:
            logger.info(f"[BotService] 收到启动请求: bot_id={bot_id}")

            # 验证机器人是否存在
            bot = await cls.get_bot(bot_id, db)
            if not bot:
                logger.error(f"[BotService] 机器人 {bot_id} 不存在")
                return False

            logger.info(f"[BotService] 机器人 {bot_id} 当前状态: {bot.status}")

            if bot.status == "running":
                logger.warning(f"[BotService] 机器人 {bot_id} 状态已是 RUNNING")
                return False

            # 使用机器人管理器启动机器人
            logger.info(f"[BotService] 调用 bot_manager.start_bot()")
            success = await bot_manager.start_bot(bot_id, db)
            logger.info(f"[BotService] bot_manager.start_bot() 返回: {success}")

            if success:
                logger.info(f"[BotService] 机器人 {bot_id} 启动成功")
            else:
                logger.warning(f"[BotService] 机器人 {bot_id} 启动失败")

            return success
        
        except Exception as e:
            logger.error(f"[BotService] 启动机器人 {bot_id} 失败: {str(e)}", exc_info=True)
            return False
    
    @classmethod
    async def pause_bot(cls, bot_id: int) -> bool:
        """
        暂停机器人
        
        Args:
            bot_id: 机器人ID
            
        Returns:
            是否成功暂停
        """
        try:
            # 创建一个新的数据库会话
            from app.db.session import AsyncSessionLocal
            async with AsyncSessionLocal() as db:
                success = await bot_manager.pause_bot(bot_id, db)
            
            if success:
                logger.info(f"机器人 {bot_id} 已暂停")
            else:
                logger.warning(f"机器人 {bot_id} 暂停失败")
            
            return success
        
        except Exception as e:
            logger.error(f"暂停机器人 {bot_id} 失败: {str(e)}")
            return False
    
    @classmethod
    async def stop_bot(cls, bot_id: int) -> bool:
        """
        停止机器人
        
        Args:
            bot_id: 机器人ID
            
        Returns:
            是否成功停止
        """
        try:
            # 创建一个新的数据库会话
            from app.db.session import AsyncSessionLocal
            async with AsyncSessionLocal() as db:
                success = await bot_manager.stop_bot(bot_id, db)
            
            if success:
                logger.info(f"机器人 {bot_id} 已停止")
            else:
                logger.warning(f"机器人 {bot_id} 停止失败")
            
            return success
        
        except Exception as e:
            logger.error(f"停止机器人 {bot_id} 失败: {str(e)}")
            return False
    
    @classmethod
    async def close_all_positions(cls, bot_id: int) -> bool:
        """
        平仓所有持仓
        
        Args:
            bot_id: 机器人ID
            
        Returns:
            是否成功发送平仓指令
        """
        try:
            # 创建一个新的数据库会话
            from app.db.session import AsyncSessionLocal
            async with AsyncSessionLocal() as db:
                success = await bot_manager.close_bot_positions(bot_id, db)
            
            if success:
                logger.info(f"机器人 {bot_id} 平仓指令已发送")
            else:
                logger.warning(f"机器人 {bot_id} 平仓失败")
            
            return success
        
        except Exception as e:
            logger.error(f"机器人 {bot_id} 平仓失败: {str(e)}")
            return False
    
    @classmethod
    async def get_running_bot(cls, bot_id: int):
        """
        获取运行中的机器人引擎
        
        Args:
            bot_id: 机器人ID
            
        Returns:
            机器人引擎实例,如果不存在返回None
        """
        return await bot_manager.get_running_bot(bot_id)
    
    @classmethod
    async def get_all_running_bots(cls):
        """
        获取所有运行中的机器人
        
        Returns:
            机器人ID到引擎实例的映射
        """
        return await bot_manager.get_all_running_bots()

    @classmethod
    async def get_bot(cls, bot_id: int, db: AsyncSession) -> Optional[BotInstance]:
        """
        获取机器人实例

        Args:
            bot_id: 机器人ID
            db: 数据库会话

        Returns:
            机器人实例，如果不存在则返回None
        """
        try:
            result = await db.execute(
                select(BotInstance).where(BotInstance.id == bot_id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"[BotService] 获取机器人 {bot_id} 失败: {str(e)}")
            return None

    @classmethod
    async def stop_all_bots(cls):
        """停止所有运行中的机器人"""
        await bot_manager.cleanup()
        logger.info("所有机器人已停止")