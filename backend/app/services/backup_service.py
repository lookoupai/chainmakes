"""
数据备份服务 - 用于定期备份重要数据
"""
import asyncio
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pathlib import Path

from app.models.bot_instance import BotInstance
from app.models.order import Order
from app.models.position import Position
from app.models.spread_history import SpreadHistory
from app.models.trade_log import TradeLog
from app.models.exchange_account import ExchangeAccount
from app.models.user import User
from app.config import settings
from app.utils.logger import setup_logger

logger = setup_logger('backup_service')


class BackupService:
    """数据备份服务"""
    
    def __init__(self):
        self.backup_dir = Path("backups")
        self.backup_dir.mkdir(exist_ok=True)
        self.backup_task: Optional[asyncio.Task] = None
        self.is_running = False
    
    async def start_backup_scheduler(self):
        """启动备份调度器"""
        if self.is_running:
            logger.warning("备份调度器已在运行")
            return
        
        self.is_running = True
        self.backup_task = asyncio.create_task(self._backup_loop())
        logger.info("备份调度器已启动")
    
    async def stop_backup_scheduler(self):
        """停止备份调度器"""
        if not self.is_running:
            return
        
        self.is_running = False
        
        if self.backup_task and not self.backup_task.done():
            self.backup_task.cancel()
            try:
                await self.backup_task
            except asyncio.CancelledError:
                pass
        
        logger.info("备份调度器已停止")
    
    async def _backup_loop(self):
        """备份循环"""
        while self.is_running:
            try:
                # 每天凌晨2点执行备份
                now = datetime.now()
                next_backup = now.replace(hour=2, minute=0, second=0, microsecond=0)
                
                # 如果已经过了今天的2点，则设置为明天的2点
                if now >= next_backup:
                    next_backup += timedelta(days=1)
                
                # 计算等待时间
                wait_seconds = (next_backup - now).total_seconds()
                logger.info(f"下次备份时间: {next_backup}, 等待 {wait_seconds} 秒")
                
                # 等待到备份时间
                await asyncio.sleep(wait_seconds)
                
                # 执行备份
                if self.is_running:
                    await self.perform_backup()
                
            except asyncio.CancelledError:
                logger.info("备份循环被取消")
                break
            except Exception as e:
                logger.error(f"备份循环错误: {str(e)}", exc_info=True)
                # 出错后等待1小时再重试
                await asyncio.sleep(3600)
    
    async def perform_backup(self, db: Optional[AsyncSession] = None):
        """
        执行数据备份
        
        Args:
            db: 数据库会话，如果不提供则创建新会话
        """
        try:
            logger.info("开始执行数据备份")
            
            # 创建备份目录
            backup_date = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = self.backup_dir / f"backup_{backup_date}"
            backup_path.mkdir(exist_ok=True)
            
            # 如果没有提供数据库会话，创建一个
            if db is None:
                from app.db.session import async_session
                async with async_session() as session:
                    await self._backup_all_data(session, backup_path)
            else:
                await self._backup_all_data(db, backup_path)
            
            # 创建备份清单
            await self._create_backup_manifest(backup_path)
            
            # 清理旧备份（保留最近7天）
            await self._cleanup_old_backups()
            
            logger.info(f"数据备份完成: {backup_path}")
            
        except Exception as e:
            logger.error(f"数据备份失败: {str(e)}", exc_info=True)
    
    async def _backup_all_data(self, db: AsyncSession, backup_path: Path):
        """备份所有数据"""
        # 备份用户数据
        await self._backup_table_data(db, User, backup_path, "users.json")
        
        # 备份交易所账户数据
        await self._backup_table_data(db, ExchangeAccount, backup_path, "exchange_accounts.json")
        
        # 备份机器人实例数据
        await self._backup_table_data(db, BotInstance, backup_path, "bot_instances.json")
        
        # 备份订单数据
        await self._backup_table_data(db, Order, backup_path, "orders.json")
        
        # 备份持仓数据
        await self._backup_table_data(db, Position, backup_path, "positions.json")
        
        # 备份价差历史数据（只备份最近30天）
        await self._backup_spread_history(db, backup_path)
        
        # 备份交易日志数据（只备份最近30天）
        await self._backup_trade_logs(db, backup_path)
    
    async def _backup_table_data(self, db: AsyncSession, model_class, backup_path: Path, filename: str):
        """备份表数据"""
        try:
            result = await db.execute(select(model_class))
            items = result.scalars().all()
            
            # 转换为可序列化的字典列表
            data = []
            for item in items:
                item_dict = {}
                for column in item.__table__.columns:
                    value = getattr(item, column.name)
                    if isinstance(value, datetime):
                        value = value.isoformat()
                    item_dict[column.name] = value
                data.append(item_dict)
            
            # 写入JSON文件
            with open(backup_path / filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"备份 {model_class.__name__} 数据完成: {len(data)} 条记录")
            
        except Exception as e:
            logger.error(f"备份 {model_class.__name__} 数据失败: {str(e)}")
    
    async def _backup_spread_history(self, db: AsyncSession, backup_path: Path):
        """备份价差历史数据"""
        try:
            # 只备份最近30天的数据
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            
            result = await db.execute(
                select(SpreadHistory).where(
                    SpreadHistory.recorded_at >= thirty_days_ago
                )
            )
            items = result.scalars().all()
            
            # 转换为可序列化的字典列表
            data = []
            for item in items:
                item_dict = {
                    "id": item.id,
                    "bot_instance_id": item.bot_instance_id,
                    "market1_price": float(item.market1_price),
                    "market2_price": float(item.market2_price),
                    "spread_percentage": float(item.spread_percentage),
                    "recorded_at": item.recorded_at.isoformat()
                }
                data.append(item_dict)
            
            # 写入JSON文件
            with open(backup_path / "spread_history.json", 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"备份价差历史数据完成: {len(data)} 条记录")
            
        except Exception as e:
            logger.error(f"备份价差历史数据失败: {str(e)}")
    
    async def _backup_trade_logs(self, db: AsyncSession, backup_path: Path):
        """备份交易日志数据"""
        try:
            # 只备份最近30天的数据
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            
            result = await db.execute(
                select(TradeLog).where(
                    TradeLog.created_at >= thirty_days_ago
                )
            )
            items = result.scalars().all()
            
            # 转换为可序列化的字典列表
            data = []
            for item in items:
                item_dict = {
                    "id": item.id,
                    "bot_instance_id": item.bot_instance_id,
                    "log_type": item.log_type,
                    "message": item.message,
                    "created_at": item.created_at.isoformat()
                }
                data.append(item_dict)
            
            # 写入JSON文件
            with open(backup_path / "trade_logs.json", 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"备份交易日志数据完成: {len(data)} 条记录")
            
        except Exception as e:
            logger.error(f"备份交易日志数据失败: {str(e)}")
    
    async def _create_backup_manifest(self, backup_path: Path):
        """创建备份清单"""
        try:
            manifest = {
                "backup_time": datetime.now().isoformat(),
                "backup_version": "1.0",
                "files": []
            }
            
            # 添加文件信息
            for file_path in backup_path.glob("*.json"):
                file_stat = file_path.stat()
                manifest["files"].append({
                    "name": file_path.name,
                    "size": file_stat.st_size,
                    "modified": datetime.fromtimestamp(file_stat.st_mtime).isoformat()
                })
            
            # 写入清单文件
            with open(backup_path / "manifest.json", 'w', encoding='utf-8') as f:
                json.dump(manifest, f, ensure_ascii=False, indent=2)
            
        except Exception as e:
            logger.error(f"创建备份清单失败: {str(e)}")
    
    async def _cleanup_old_backups(self):
        """清理旧备份（保留最近7天）"""
        try:
            seven_days_ago = datetime.now() - timedelta(days=7)
            
            for backup_dir in self.backup_dir.iterdir():
                if not backup_dir.is_dir():
                    continue
                
                # 尝试从目录名解析备份时间
                try:
                    dir_name = backup_dir.name
                    if dir_name.startswith("backup_"):
                        date_str = dir_name[7:]  # 去掉 "backup_" 前缀
                        backup_date = datetime.strptime(date_str, "%Y%m%d_%H%M%S")
                        
                        if backup_date < seven_days_ago:
                            # 删除旧备份目录
                            import shutil
                            shutil.rmtree(backup_dir)
                            logger.info(f"删除旧备份: {backup_dir}")
                
                except Exception as e:
                    logger.warning(f"处理备份目录 {backup_dir} 失败: {str(e)}")
            
        except Exception as e:
            logger.error(f"清理旧备份失败: {str(e)}")
    
    async def restore_from_backup(self, backup_path: str, db: AsyncSession):
        """
        从备份恢复数据
        
        Args:
            backup_path: 备份目录路径
            db: 数据库会话
        """
        try:
            backup_dir = Path(backup_path)
            if not backup_dir.exists() or not backup_dir.is_dir():
                raise ValueError(f"备份目录不存在: {backup_path}")
            
            # 检查备份清单
            manifest_path = backup_dir / "manifest.json"
            if not manifest_path.exists():
                raise ValueError("备份清单文件不存在")
            
            with open(manifest_path, 'r', encoding='utf-8') as f:
                manifest = json.load(f)
            
            logger.info(f"开始从备份恢复数据: {manifest['backup_time']}")
            
            # TODO: 实现数据恢复逻辑
            # 这需要根据实际需求来实现，可能需要先清空现有数据
            
            logger.info("数据恢复完成")
            
        except Exception as e:
            logger.error(f"数据恢复失败: {str(e)}", exc_info=True)
            raise


# 全局备份服务实例
backup_service = BackupService()