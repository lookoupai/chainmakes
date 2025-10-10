"""
机器人管理服务 - 负责启动机器人并管理其生命周期
"""
import asyncio
from typing import Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.bot_instance import BotInstance
from app.models.exchange_account import ExchangeAccount
from app.exchanges.exchange_factory import ExchangeFactory
from app.core.bot_engine import BotEngine
from app.services.data_sync_service import data_sync_service
from app.utils.encryption import decrypt_key
from app.utils.logger import setup_logger

logger = setup_logger('bot_manager')


class BotManager:
    """机器人管理器"""
    
    def __init__(self):
        # 存储运行中的机器人实例
        self.running_bots: Dict[int, BotEngine] = {}
        # 存储机器人任务
        self.bot_tasks: Dict[int, asyncio.Task] = {}
    
    async def start_bot(self, bot_id: int, db: AsyncSession) -> bool:
        """
        启动机器人
        
        Args:
            bot_id: 机器人ID
            db: 数据库会话
            
        Returns:
            是否启动成功
        """
        try:
            logger.info(f"[BotManager] 尝试启动机器人 {bot_id}")
            logger.info(f"[BotManager] 当前运行中的机器人: {list(self.running_bots.keys())}")
            
            # 检查机器人是否已在运行
            if bot_id in self.running_bots:
                logger.warning(f"[BotManager] 机器人 {bot_id} 已在运行中")
                return False
            
            # 获取机器人信息
            result = await db.execute(
                select(BotInstance).where(BotInstance.id == bot_id)
            )
            bot = result.scalar_one_or_none()
            
            if not bot:
                logger.error(f"[BotManager] 机器人不存在: {bot_id}")
                return False
            
            logger.info(f"[BotManager] 机器人 {bot_id} 当前数据库状态: {bot.status}")
            
            # 获取交易所账户信息
            result = await db.execute(
                select(ExchangeAccount).where(ExchangeAccount.id == bot.exchange_account_id)
            )
            exchange_account = result.scalar_one_or_none()
            
            if not exchange_account:
                logger.error(f"交易所账户不存在: {bot.exchange_account_id}")
                return False
            
            # 创建交易所实例
            logger.info(f"[BotManager] 创建交易所实例: {exchange_account.exchange_name}")
            exchange = ExchangeFactory.create(
                exchange_name=exchange_account.exchange_name,
                api_key=decrypt_key(exchange_account.api_key),
                api_secret=decrypt_key(exchange_account.api_secret),
                passphrase=decrypt_key(exchange_account.passphrase) if exchange_account.passphrase else None
            )
            
            # 创建机器人引擎（不传递 db 会话，BotEngine 会创建独立会话）
            logger.info(f"[BotManager] 创建 BotEngine 实例")
            bot_engine = BotEngine(bot, exchange, bot_id)
            
            # 保存机器人实例
            self.running_bots[bot_id] = bot_engine
            logger.info(f"[BotManager] 机器人 {bot_id} 已加入 running_bots")
            
            # 创建并启动机器人任务
            logger.info(f"[BotManager] 创建异步任务并启动机器人")
            task = asyncio.create_task(bot_engine._run())
            self.bot_tasks[bot_id] = task
            logger.info(f"[BotManager] 异步任务已创建: {task}")
            logger.info(f"[BotManager] 任务状态: done={task.done()}, cancelled={task.cancelled()}")

            # 添加任务完成回调，用于异常处理
            task.add_done_callback(self._task_done_callback(bot_id))
            
            # 启动数据同步（使用独立会话）
            try:
                from app.db.session import AsyncSessionLocal
                async with AsyncSessionLocal() as sync_db:
                    await data_sync_service.start_sync_for_bot(bot_id, sync_db)
            except Exception as e:
                logger.warning(f"[BotManager] 启动数据同步失败（非关键错误）: {str(e)}")
            
            logger.info(f"[BotManager] 机器人 {bot_id} 启动成功")
            return True
            
        except Exception as e:
            logger.error(f"启动机器人 {bot_id} 失败: {str(e)}", exc_info=True)
            return False
    
    async def stop_bot(self, bot_id: int, db: AsyncSession) -> bool:
        """
        停止机器人（自动平仓所有持仓）

        Args:
            bot_id: 机器人ID
            db: 数据库会话

        Returns:
            是否停止成功
        """
        try:
            logger.info(f"[BotManager] 尝试停止机器人 {bot_id}")

            # 检查机器人是否在运行
            if bot_id not in self.running_bots:
                logger.warning(f"[BotManager] 机器人 {bot_id} 未在运行")
                return False

            # 获取机器人引擎
            bot_engine = self.running_bots[bot_id]

            # 🔥 关键修复：停止前先平仓所有持仓
            logger.info(f"[BotManager] 停止前先平仓所有持仓")
            try:
                await bot_engine.close_all_positions()
                logger.info(f"[BotManager] 机器人 {bot_id} 平仓完成")
            except Exception as e:
                logger.error(f"[BotManager] 平仓失败: {str(e)}", exc_info=True)
                # 即使平仓失败也继续停止流程

            # 停止机器人（设置标志，循环会自动退出）
            logger.info(f"[BotManager] 设置机器人 {bot_id} 停止标志")
            bot_engine.is_running = False
            
            # 取消任务
            if bot_id in self.bot_tasks:
                task = self.bot_tasks[bot_id]
                logger.info(f"[BotManager] 等待任务完成: {task}")
                if not task.done():
                    # 给任务足够时间自然结束（考虑平仓需要时间）
                    # 平仓可能需要：获取持仓(1-2s) + 每个持仓平仓(2-3s) + 数据库更新(1s)
                    try:
                        await asyncio.wait_for(task, timeout=15.0)  # 增加到15秒
                        logger.info(f"[BotManager] 任务已正常完成")
                    except asyncio.TimeoutError:
                        logger.warning(f"[BotManager] 任务在15秒内未完成，强制取消")
                        task.cancel()
                        try:
                            await task
                        except asyncio.CancelledError:
                            pass
                del self.bot_tasks[bot_id]
            
            # 关闭交易所连接
            try:
                await bot_engine.exchange.close()
            except Exception as e:
                logger.warning(f"[BotManager] 关闭交易所连接失败: {str(e)}")
            
            # 从运行列表中移除
            del self.running_bots[bot_id]
            
            # 更新数据库状态
            try:
                result = await db.execute(
                    select(BotInstance).where(BotInstance.id == bot_id)
                )
                bot = result.scalar_one_or_none()
                if bot:
                    bot.status = "stopped"
                    await db.commit()
            except Exception as e:
                logger.warning(f"[BotManager] 更新数据库状态失败: {str(e)}")
            
            logger.info(f"[BotManager] 机器人 {bot_id} 停止成功")
            return True
            
        except Exception as e:
            logger.error(f"[BotManager] 停止机器人 {bot_id} 失败: {str(e)}", exc_info=True)
            return False
    
    async def pause_bot(self, bot_id: int, db: AsyncSession) -> bool:
        """
        暂停机器人
        
        Args:
            bot_id: 机器人ID
            db: 数据库会话
            
        Returns:
            是否暂停成功
        """
        try:
            # 检查机器人是否在运行
            if bot_id not in self.running_bots:
                logger.warning(f"机器人 {bot_id} 未在运行")
                return False
            
            # 获取机器人引擎
            bot_engine = self.running_bots[bot_id]
            
            # 暂停机器人
            await bot_engine.pause()
            
            logger.info(f"机器人 {bot_id} 暂停成功")
            return True
            
        except Exception as e:
            logger.error(f"暂停机器人 {bot_id} 失败: {str(e)}", exc_info=True)
            return False
    
    async def close_bot_positions(self, bot_id: int, db: AsyncSession) -> bool:
        """
        平仓机器人所有持仓

        Args:
            bot_id: 机器人ID
            db: 数据库会话

        Returns:
            是否平仓成功
        """
        try:
            # 检查机器人是否在运行
            if bot_id in self.running_bots:
                # 机器人正在运行，使用引擎平仓
                logger.info(f"机器人 {bot_id} 正在运行，使用引擎平仓")
                bot_engine = self.running_bots[bot_id]
                await bot_engine.close_all_positions()
                logger.info(f"机器人 {bot_id} 平仓成功")
                return True

            # 机器人未运行，直接通过交易所API平仓
            logger.warning(f"机器人 {bot_id} 未在运行，尝试直接通过交易所API平仓")

            # 获取机器人信息
            result = await db.execute(
                select(BotInstance).where(BotInstance.id == bot_id)
            )
            bot = result.scalar_one_or_none()

            if not bot:
                logger.error(f"机器人 {bot_id} 不存在")
                return False

            # 获取交易所账户
            result = await db.execute(
                select(ExchangeAccount).where(ExchangeAccount.id == bot.exchange_account_id)
            )
            exchange_account = result.scalar_one_or_none()

            if not exchange_account:
                logger.error(f"交易所账户不存在: {bot.exchange_account_id}")
                return False

            # 创建交易所实例
            from app.utils.encryption import decrypt_key
            exchange = ExchangeFactory.create(
                exchange_name=exchange_account.exchange_name,
                api_key=decrypt_key(exchange_account.api_key),
                api_secret=decrypt_key(exchange_account.api_secret),
                passphrase=decrypt_key(exchange_account.passphrase) if exchange_account.passphrase else None
            )

            # 获取交易所持仓
            positions = await exchange.get_all_positions()
            bot_symbols = {bot.market1_symbol, bot.market2_symbol}
            relevant_positions = [pos for pos in positions if pos['symbol'] in bot_symbols]

            logger.info(f"发现 {len(relevant_positions)} 个需要平仓的持仓")

            # 平仓每个持仓
            for pos in relevant_positions:
                try:
                    # 确定平仓方向
                    if pos['side'] == 'long':
                        close_side = 'sell'
                    else:
                        close_side = 'buy'

                    logger.info(
                        f"平仓 {pos['symbol']}: 方向={pos['side']}, "
                        f"数量={pos['amount']}, 平仓方向={close_side}"
                    )

                    # 创建平仓订单
                    order = await exchange.create_market_order(
                        pos['symbol'],
                        close_side,
                        pos['amount'],
                        reduce_only=True
                    )

                    logger.info(f"平仓订单已创建: {order['id']}")

                except Exception as e:
                    logger.error(f"平仓 {pos['symbol']} 失败: {str(e)}", exc_info=True)
                    # 继续尝试平仓其他持仓

            # 更新数据库中的持仓状态
            from datetime import datetime
            db_positions = await db.execute(
                select(Position).where(
                    Position.bot_instance_id == bot_id,
                    Position.is_open == True
                )
            )
            for db_pos in db_positions.scalars().all():
                db_pos.is_open = False
                db_pos.closed_at = datetime.utcnow()

            await db.commit()

            # 关闭交易所连接
            await exchange.close()

            logger.info(f"机器人 {bot_id} 直接平仓成功")
            return True

        except Exception as e:
            logger.error(f"机器人 {bot_id} 平仓失败: {str(e)}", exc_info=True)
            return False
    
    async def get_running_bot(self, bot_id: int) -> Optional[BotEngine]:
        """
        获取运行中的机器人实例
        
        Args:
            bot_id: 机器人ID
            
        Returns:
            机器人引擎实例，如果不存在则返回None
        """
        return self.running_bots.get(bot_id)
    
    async def get_all_running_bots(self) -> Dict[int, BotEngine]:
        """
        获取所有运行中的机器人
        
        Returns:
            运行中的机器人字典 {bot_id: BotEngine}
        """
        return self.running_bots.copy()
    
    async def recover_running_bots(self, db: AsyncSession) -> int:
        """
        恢复所有状态为 running 的机器人
        
        在应用启动时调用，自动恢复之前运行中的机器人
        
        Args:
            db: 数据库会话
            
        Returns:
            成功恢复的机器人数量
        """
        try:
            logger.info("[BotManager] 开始恢复运行中的机器人...")
            
            # 查询所有状态为 running 的机器人
            result = await db.execute(
                select(BotInstance).where(BotInstance.status == "running")
            )
            running_bots = result.scalars().all()
            
            if not running_bots:
                logger.info("[BotManager] 没有需要恢复的机器人")
                return 0
            
            logger.info(f"[BotManager] 发现 {len(running_bots)} 个需要恢复的机器人")
            
            recovered_count = 0
            for bot in running_bots:
                try:
                    logger.info(f"[BotManager] 恢复机器人: {bot.id} - {bot.bot_name}")
                    
                    # 使用 start_bot 方法启动机器人
                    success = await self.start_bot(bot.id, db)
                    
                    if success:
                        recovered_count += 1
                        logger.info(f"[BotManager] 机器人 {bot.id} 恢复成功")
                    else:
                        logger.warning(f"[BotManager] 机器人 {bot.id} 恢复失败")
                        # 更新数据库状态为 stopped
                        bot.status = "stopped"
                        await db.commit()
                        
                except Exception as e:
                    logger.error(f"[BotManager] 恢复机器人 {bot.id} 时出错: {str(e)}", exc_info=True)
                    # 更新数据库状态为 stopped
                    try:
                        bot.status = "stopped"
                        await db.commit()
                    except:
                        pass
            
            logger.info(f"[BotManager] 机器人恢复完成: {recovered_count}/{len(running_bots)} 成功")
            return recovered_count
            
        except Exception as e:
            logger.error(f"[BotManager] 恢复运行中的机器人失败: {str(e)}", exc_info=True)
            return 0
    
    def _task_done_callback(self, bot_id: int):
        """异步任务完成回调函数"""
        def callback(task: asyncio.Task):
            logger.info(f"[BotManager] 机器人 {bot_id} 任务完成: done={task.done()}")

            try:
                # 检查任务是否有异常
                if task.done():
                    # 先检查是否被取消
                    if task.cancelled():
                        logger.info(f"[BotManager] 机器人 {bot_id} 任务被取消（正常关闭）")
                    else:
                        # 获取异常（如果有）
                        exception = task.exception()
                        if exception:
                            logger.error(
                                f"[BotManager] 机器人 {bot_id} 任务异常: {str(exception)}",
                                exc_info=exception
                            )
                            # 从运行列表中移除
                            self.running_bots.pop(bot_id, None)
                            self.bot_tasks.pop(bot_id, None)

                            # 🔥 关键修复：更新数据库状态为 stopped
                            async def update_db_status():
                                try:
                                    from app.db.session import AsyncSessionLocal
                                    async with AsyncSessionLocal() as db:
                                        result = await db.execute(
                                            select(BotInstance).where(BotInstance.id == bot_id)
                                        )
                                        bot = result.scalar_one_or_none()
                                        if bot:
                                            bot.status = "stopped"
                                            await db.commit()
                                            logger.info(f"[BotManager] 已更新机器人 {bot_id} 数据库状态为 stopped")
                                except Exception as e:
                                    logger.error(f"[BotManager] 更新数据库状态失败: {str(e)}")

                            # 在新的事件循环中执行数据库更新
                            asyncio.create_task(update_db_status())
            except asyncio.CancelledError:
                # 任务被取消是正常的
                logger.info(f"[BotManager] 机器人 {bot_id} 任务被取消（正常关闭）")
            except Exception as e:
                logger.error(f"[BotManager] 处理任务回调时异常: {str(e)}")

        return callback

    async def cleanup(self):
        """清理所有运行中的机器人"""
        logger.info("开始清理所有运行中的机器人")

        for bot_id in list(self.running_bots.keys()):
            try:
                # 创建一个虚拟的数据库会话
                from app.db.session import AsyncSessionLocal
                async with AsyncSessionLocal() as db:
                    await self.stop_bot(bot_id, db)
            except Exception as e:
                logger.error(f"清理机器人 {bot_id} 失败: {str(e)}")

        # 停止所有数据同步
        await data_sync_service.stop_all_sync()

        logger.info("所有机器人清理完成")


# 全局机器人管理器实例
bot_manager = BotManager()