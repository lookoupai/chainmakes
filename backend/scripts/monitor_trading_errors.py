"""
交易错误监控脚本
用于实时监控机器人运行中的错误，并将错误信息单独记录到文件中
方便调试和问题追踪
"""
import asyncio
import sys
import logging
from pathlib import Path
from datetime import datetime
from collections import defaultdict
from typing import Dict, List

# 首先配置日志级别（必须在导入任何模块之前）
logging.basicConfig(level=logging.WARNING)
logging.getLogger('sqlalchemy').setLevel(logging.WARNING)

# 添加后端路径到系统路径
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from sqlalchemy import select, and_, desc
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.config import settings
from app.models.trade_log import TradeLog
from app.models.bot_instance import BotInstance

# 创建专用的静默数据库引擎（关闭echo）
silent_engine = create_async_engine(
    settings.DATABASE_URL_ASYNC,
    echo=False,  # 关闭SQL日志
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,
)

# 创建静默会话工厂
AsyncSessionLocal = async_sessionmaker(
    silent_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


class TradingErrorMonitor:
    """交易错误监控器"""
    
    def __init__(self):
        self.error_log_file = backend_path / "logs" / "trading_errors.log"
        self.summary_file = backend_path / "logs" / "error_summary.txt"
        self.last_check_time = datetime.utcnow()
        self.error_stats: Dict[int, Dict] = defaultdict(lambda: {
            "total_errors": 0,
            "error_types": defaultdict(int),
            "latest_errors": []
        })
        
        # 确保日志目录存在
        self.error_log_file.parent.mkdir(exist_ok=True)
        
        # 初始化日志文件
        self._init_log_files()
    
    def _init_log_files(self):
        """初始化日志文件"""
        with open(self.error_log_file, 'a', encoding='utf-8') as f:
            f.write(f"\n{'='*80}\n")
            f.write(f"错误监控开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"{'='*80}\n\n")
    
    async def monitor(self):
        """持续监控错误日志"""
        print(f"[监控器] 开始监控交易错误...")
        print(f"[监控器] 错误日志文件: {self.error_log_file}")
        print(f"[监控器] 错误摘要文件: {self.summary_file}")
        print(f"[监控器] 按 Ctrl+C 停止监控\n")
        
        cycle_count = 0
        
        try:
            while True:
                cycle_count += 1
                await self._check_new_errors()
                
                # 每10个周期(50秒)生成一次摘要
                if cycle_count % 10 == 0:
                    await self._generate_summary()
                
                await asyncio.sleep(5)  # 每5秒检查一次
                
        except KeyboardInterrupt:
            print("\n[监控器] 监控已停止")
            await self._generate_summary()
            print(f"[监控器] 最终报告已保存到: {self.summary_file}")
    
    async def _check_new_errors(self):
        """检查新的错误日志"""
        async with AsyncSessionLocal() as db:
            try:
                # 查询自上次检查后的所有错误日志
                result = await db.execute(
                    select(TradeLog, BotInstance)
                    .join(BotInstance, TradeLog.bot_instance_id == BotInstance.id)
                    .where(
                        and_(
                            TradeLog.log_type == "error",
                            TradeLog.created_at > self.last_check_time
                        )
                    )
                    .order_by(desc(TradeLog.created_at))
                )
                
                logs_with_bots = result.all()
                
                if logs_with_bots:
                    print(f"\n{'='*80}")
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] 发现 {len(logs_with_bots)} 个新错误!")
                    print(f"{'='*80}")
                    
                    for log, bot in logs_with_bots:
                        await self._process_error(log, bot)
                else:
                    # 没有错误，显示正常状态
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] ✓ 无新错误", end='\r')
                
                # 更新检查时间
                self.last_check_time = datetime.utcnow()
                
            except Exception as e:
                print(f"\n[监控器错误] 检查日志失败: {str(e)}")
    
    async def _process_error(self, log: TradeLog, bot: BotInstance):
        """处理单个错误日志"""
        bot_id = bot.id
        bot_name = bot.bot_name
        error_message = log.message
        timestamp = log.created_at
        
        # 分类错误类型
        error_type = self._classify_error(error_message)
        
        # 更新统计
        stats = self.error_stats[bot_id]
        stats["total_errors"] += 1
        stats["error_types"][error_type] += 1
        stats["latest_errors"].append({
            "time": timestamp,
            "type": error_type,
            "message": error_message
        })
        
        # 只保留最近20条
        if len(stats["latest_errors"]) > 20:
            stats["latest_errors"].pop(0)
        
        # 打印到控制台
        print(f"\n┌─ 机器人 [{bot_id}] {bot_name}")
        print(f"├─ 时间: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"├─ 类型: {error_type}")
        print(f"└─ 错误: {error_message}")
        
        # 写入日志文件
        with open(self.error_log_file, 'a', encoding='utf-8') as f:
            f.write(f"{'─'*80}\n")
            f.write(f"时间: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"机器人ID: {bot_id}\n")
            f.write(f"机器人名称: {bot_name}\n")
            f.write(f"错误类型: {error_type}\n")
            f.write(f"错误信息: {error_message}\n")
            f.write(f"{'─'*80}\n\n")
    
    def _classify_error(self, error_message: str) -> str:
        """分类错误类型"""
        error_lower = error_message.lower()
        
        if "api" in error_lower or "request" in error_lower:
            return "API错误"
        elif "network" in error_lower or "timeout" in error_lower or "connection" in error_lower:
            return "网络错误"
        elif "order" in error_lower or "trade" in error_lower:
            return "交易错误"
        elif "balance" in error_lower or "insufficient" in error_lower:
            return "余额不足"
        elif "position" in error_lower:
            return "持仓错误"
        elif "price" in error_lower or "spread" in error_lower:
            return "价格/价差错误"
        elif "database" in error_lower or "db" in error_lower:
            return "数据库错误"
        else:
            return "其他错误"
    
    async def _generate_summary(self):
        """生成错误摘要"""
        async with AsyncSessionLocal() as db:
            try:
                # 获取所有运行中的机器人
                result = await db.execute(
                    select(BotInstance).where(BotInstance.status == "running")
                )
                running_bots = result.scalars().all()
                
                # 生成摘要报告
                summary_lines = []
                summary_lines.append("="*80)
                summary_lines.append(f"错误监控摘要报告")
                summary_lines.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                summary_lines.append("="*80)
                summary_lines.append("")
                
                # 运行状态
                summary_lines.append(f"运行中的机器人: {len(running_bots)} 个")
                for bot in running_bots:
                    summary_lines.append(f"  - [{bot.id}] {bot.bot_name}")
                summary_lines.append("")
                
                # 错误统计
                if self.error_stats:
                    summary_lines.append("错误统计:")
                    summary_lines.append("-"*80)
                    
                    for bot_id, stats in self.error_stats.items():
                        summary_lines.append(f"\n机器人 ID: {bot_id}")
                        summary_lines.append(f"  总错误数: {stats['total_errors']}")
                        summary_lines.append(f"  错误类型分布:")
                        
                        for error_type, count in stats['error_types'].items():
                            percentage = (count / stats['total_errors']) * 100
                            summary_lines.append(f"    - {error_type}: {count} 次 ({percentage:.1f}%)")
                        
                        # 显示最近3条错误
                        if stats['latest_errors']:
                            summary_lines.append(f"\n  最近的错误 (最多3条):")
                            for error in stats['latest_errors'][-3:]:
                                summary_lines.append(f"    [{error['time'].strftime('%H:%M:%S')}] {error['type']}")
                                summary_lines.append(f"      {error['message'][:100]}")
                        
                        summary_lines.append("-"*80)
                else:
                    summary_lines.append("✓ 未检测到任何错误!")
                
                summary_lines.append("")
                summary_lines.append("="*80)
                
                # 写入摘要文件
                summary_text = "\n".join(summary_lines)
                with open(self.summary_file, 'w', encoding='utf-8') as f:
                    f.write(summary_text)
                
                # 打印摘要到控制台
                print(f"\n{summary_text}")
                
            except Exception as e:
                print(f"\n[监控器错误] 生成摘要失败: {str(e)}")


async def main():
    """主函数"""
    monitor = TradingErrorMonitor()
    await monitor.monitor()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[监控器] 程序已退出")