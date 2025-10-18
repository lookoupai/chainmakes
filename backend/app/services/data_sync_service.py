"""
数据同步服务 - 用于定期同步交易所数据
"""
import asyncio
from typing import Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func
from datetime import datetime, timedelta

from app.models.bot_instance import BotInstance
from app.models.exchange_account import ExchangeAccount
from app.models.order import Order
from app.models.position import Position
from app.exchanges.exchange_factory import ExchangeFactory
from app.utils.encryption import decrypt_key
from app.utils.logger import setup_logger

logger = setup_logger('data_sync_service')


class DataSyncService:
    """数据同步服务"""
    
    def __init__(self):
        self.sync_tasks: Dict[int, asyncio.Task] = {}
        self.is_running = False
    
    async def start_sync_for_bot(self, bot_id: int, db: AsyncSession):
        """
        为特定机器人启动数据同步
        
        Args:
            bot_id: 机器人ID
            db: 数据库会话
        """
        try:
            # 如果已有同步任务，先停止
            if bot_id in self.sync_tasks:
                await self.stop_sync_for_bot(bot_id)
            
            # 获取机器人信息
            result = await db.execute(
                select(BotInstance).where(BotInstance.id == bot_id)
            )
            bot = result.scalar_one_or_none()
            
            if not bot:
                logger.error(f"机器人不存在: {bot_id}")
                return
            
            # 获取交易所账户信息
            result = await db.execute(
                select(ExchangeAccount).where(
                    ExchangeAccount.id == bot.exchange_account_id
                )
            )
            exchange_account = result.scalar_one_or_none()
            
            if not exchange_account:
                logger.error(f"交易所账户不存在: {bot.exchange_account_id}")
                return
            
            # 创建交易所实例
            exchange = ExchangeFactory.create(
                exchange_name=exchange_account.exchange_name,
                api_key=decrypt_key(exchange_account.api_key),
                api_secret=decrypt_key(exchange_account.api_secret),
                passphrase=decrypt_key(exchange_account.passphrase) if exchange_account.passphrase else None,
                is_testnet=exchange_account.is_testnet
            )
            
            # 创建同步任务
            task = asyncio.create_task(
                self._sync_loop(bot_id, exchange, db)
            )
            self.sync_tasks[bot_id] = task
            
            logger.info(f"启动机器人 {bot_id} 数据同步")
            
        except Exception as e:
            logger.error(f"启动机器人 {bot_id} 数据同步失败: {str(e)}", exc_info=True)
    
    async def stop_sync_for_bot(self, bot_id: int):
        """
        停止特定机器人的数据同步
        
        Args:
            bot_id: 机器人ID
        """
        if bot_id in self.sync_tasks:
            task = self.sync_tasks[bot_id]
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
            del self.sync_tasks[bot_id]
            logger.info(f"停止机器人 {bot_id} 数据同步")
    
    async def stop_all_sync(self):
        """停止所有数据同步任务"""
        for bot_id in list(self.sync_tasks.keys()):
            await self.stop_sync_for_bot(bot_id)
        logger.info("所有数据同步任务已停止")
    
    async def _sync_loop(self, bot_id: int, exchange, db: AsyncSession):
        """数据同步循环"""
        while True:
            try:
                # 同步订单和持仓
                await self._sync_orders(bot_id, exchange, db)
                await self._sync_positions(bot_id, exchange, db)
                
                # 每30秒同步一次
                await asyncio.sleep(30)
                
            except asyncio.CancelledError:
                logger.info(f"机器人 {bot_id} 数据同步任务被取消")
                break
            except Exception as e:
                logger.error(f"机器人 {bot_id} 数据同步错误: {str(e)}", exc_info=True)
                # 出错后等待60秒再重试
                await asyncio.sleep(60)
    
    async def _sync_orders(self, bot_id: int, exchange, db: AsyncSession):
        """同步订单数据"""
        try:
            # 获取数据库中的订单
            result = await db.execute(
                select(Order).where(
                    Order.bot_instance_id == bot_id,
                    Order.status.in_(["open", "pending"])
                )
            )
            open_orders = result.scalars().all()
            
            # 检查每个未完成订单的状态
            for order in open_orders:
                try:
                    # 从交易所获取订单状态
                    exchange_order = await exchange.get_order(
                        order.exchange_order_id,
                        order.symbol
                    )
                    
                    # 如果状态有变化，更新数据库
                    if exchange_order['status'] != order.status:
                        order.status = exchange_order['status']
                        order.filled_amount = exchange_order['filled']
                        order.cost = exchange_order['cost']
                        
                        if exchange_order['status'] == 'closed':
                            order.filled_at = datetime.utcnow()
                        
                        order.updated_at = datetime.utcnow()
                        
                        logger.info(
                            f"更新订单状态: {order.exchange_order_id} -> {exchange_order['status']}"
                        )
                
                except Exception as e:
                    logger.warning(
                        f"获取订单 {order.exchange_order_id} 状态失败: {str(e)}"
                    )
            
            await db.commit()
            
        except Exception as e:
            logger.error(f"同步订单数据失败: {str(e)}", exc_info=True)
            await db.rollback()
    
    async def _sync_positions(self, bot_id: int, exchange, db: AsyncSession):
        """同步持仓数据"""
        try:
            # 从交易所获取所有持仓
            exchange_positions = await exchange.get_all_positions()
            
            # 转换为字典，方便查找
            exchange_pos_map = {
                pos['symbol']: pos for pos in exchange_positions
            }
            
            # 获取数据库中的持仓
            result = await db.execute(
                select(Position).where(
                    Position.bot_instance_id == bot_id,
                    Position.is_open == True
                )
            )
            db_positions = result.scalars().all()
            
            # 处理每个数据库持仓
            for db_pos in db_positions:
                symbol = db_pos.symbol
                
                if symbol in exchange_pos_map:
                    # 交易所中有该持仓，更新数据
                    exchange_pos = exchange_pos_map[symbol]

                    # 检测数量不一致并记录（在更新前）
                    old_amount = db_pos.amount
                    if old_amount != exchange_pos['amount']:
                        logger.warning(
                            f"修正持仓数量: {symbol}, "
                            f"数据库={old_amount} -> 交易所={exchange_pos['amount']}"
                        )

                    # 同步持仓数量（重要：修正数据库与交易所不一致的情况）
                    db_pos.amount = exchange_pos['amount']
                    db_pos.current_price = exchange_pos['current_price']
                    db_pos.unrealized_pnl = exchange_pos['unrealized_pnl']
                    db_pos.updated_at = datetime.utcnow()

                    # 如果交易所中持仓已平仓，更新数据库
                    if exchange_pos['amount'] == 0:
                        db_pos.is_open = False
                        db_pos.closed_at = datetime.utcnow()

                        logger.info(f"持仓已平仓: {symbol}")
                else:
                    # 交易所中没有该持仓，可能已平仓
                    db_pos.is_open = False
                    db_pos.closed_at = datetime.utcnow()
                    
                    logger.info(f"持仓已平仓(交易所中不存在): {symbol}")
            
            # 检查是否有新的持仓（交易所中有但数据库中没有）
            db_symbols = {pos.symbol for pos in db_positions}
            for symbol, exchange_pos in exchange_pos_map.items():
                if symbol not in db_symbols and exchange_pos['amount'] > 0:
                    # 查询该机器人当前最大的 cycle_number
                    max_cycle_result = await db.execute(
                        select(func.max(Position.cycle_number))
                        .where(Position.bot_instance_id == bot_id)
                    )
                    max_cycle = max_cycle_result.scalar()
                    next_cycle = (max_cycle or 0) + 1

                    # 创建新持仓记录
                    new_position = Position(
                        bot_instance_id=bot_id,
                        cycle_number=next_cycle,
                        symbol=symbol,
                        side=exchange_pos['side'],
                        amount=exchange_pos['amount'],
                        entry_price=exchange_pos['entry_price'],
                        current_price=exchange_pos['current_price'],
                        unrealized_pnl=exchange_pos['unrealized_pnl'],
                        is_open=True,
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow()
                    )
                    db.add(new_position)

                    logger.info(f"发现新持仓: {symbol}, 分配周期号: {next_cycle}")
            
            await db.commit()
            
        except Exception as e:
            logger.error(f"同步持仓数据失败: {str(e)}", exc_info=True)
            await db.rollback()
    
    async def sync_historical_data(self, bot_id: int, exchange, db: AsyncSession, days: int = 7):
        """
        同步历史数据（用于初始化）
        
        Args:
            bot_id: 机器人ID
            exchange: 交易所实例
            db: 数据库会话
            days: 同步最近几天的数据
        """
        try:
            # 获取机器人信息
            result = await db.execute(
                select(BotInstance).where(BotInstance.id == bot_id)
            )
            bot = result.scalar_one_or_none()
            
            if not bot:
                logger.error(f"机器人不存在: {bot_id}")
                return
            
            # 计算时间范围
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(days=days)
            
            # TODO: 实现历史数据同步逻辑
            # 这需要根据不同交易所的API来实现
            
            logger.info(f"同步机器人 {bot_id} 历史数据完成")
            
        except Exception as e:
            logger.error(f"同步历史数据失败: {str(e)}", exc_info=True)


# 全局数据同步服务实例
data_sync_service = DataSyncService()