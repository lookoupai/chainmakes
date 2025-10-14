"""
交易机器人核心引擎
"""
import asyncio
from decimal import Decimal
from datetime import datetime
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.bot_instance import BotInstance
from app.models.order import Order
from app.models.position import Position
from app.models.spread_history import SpreadHistory
from app.models.trade_log import TradeLog
from app.exchanges.base_exchange import BaseExchange
from app.exchanges.exchange_factory import ExchangeFactory
from app.services.spread_calculator import SpreadCalculator
from app.utils.encryption import key_encryption
from app.utils.logger import setup_logger

logger = setup_logger('bot_engine')


class BotEngine:
    """
    交易机器人核心引擎
    
    负责执行价差套利交易策略,包括:
    - 监控市场价差
    - 执行开仓/加仓
    - 执行止盈/止损
    - 记录交易数据
    """
    
    def __init__(
        self,
        bot: BotInstance,
        exchange: BaseExchange,
        bot_id: int
    ):
        """
        初始化机器人引擎

        Args:
            bot: 机器人实例
            exchange: 交易所实例
            bot_id: 机器人ID（用于创建独立会话）
        """
        self.bot = bot
        self.bot_id = bot_id
        self.exchange = exchange
        self.db = None  # 将在 start() 中创建独立会话
        self.is_running = False
        self.calculator = SpreadCalculator()

        # WebSocket推送引用(延迟导入避免循环依赖)
        self._websocket_manager = None

        # 性能监控
        self._init_performance_monitoring()

        # 价格缓存机制（降低API请求频率）
        self._price_cache = {}
        self._price_cache_time = {}
        self._price_cache_ttl = 5  # 缓存5秒

        # 持仓更新频率控制
        self._position_update_counter = 0
        self._position_update_interval = 3  # 每3个循环更新一次持仓（30秒一次）
    
    async def start(self):
        """启动机器人"""
        logger.info(f"[BotEngine] Bot {self.bot_id} start() 被调用")
        logger.info(f"[BotEngine] 启动机器人: {self.bot.bot_name} (ID: {self.bot_id})")

        if self.is_running:
            logger.warning(f"[BotEngine] Bot {self.bot_id} 已在运行")
            return

        # 创建独立的数据库会话
        from app.db.session import AsyncSessionLocal
        logger.info(f"[BotEngine] Bot {self.bot_id} 创建独立数据库会话")

        async with AsyncSessionLocal() as session:
            self.db = session

            try:
                # 重新加载 bot 对象到当前会话
                from sqlalchemy import select
                result = await self.db.execute(
                    select(BotInstance).where(BotInstance.id == self.bot_id)
                )
                self.bot = result.scalar_one()
                logger.info(f"[BotEngine] Bot {self.bot_id} 已重新加载到独立会话")

                self.is_running = True
                self.bot.status = "running"
                await self.db.commit()
                logger.info(f"[BotEngine] Bot {self.bot_id} 状态已更新为 running")

                # 🔥 启动延迟：避免多个机器人同时启动时产生请求风暴
                startup_delay = 2 + (self.bot_id % 3)  # 2-4秒的随机延迟
                logger.info(f"[BotEngine] Bot {self.bot_id} 启动延迟 {startup_delay} 秒,避免API频率限制")
                await asyncio.sleep(startup_delay)

                # 设置杠杆
                logger.info(f"[BotEngine] Bot {self.bot_id} 开始设置杠杆")
                await self._set_leverage()
                
                # 设置杠杆后等待,避免请求过快
                await asyncio.sleep(1)

                # 同步交易所状态（防止后端重启后数据不一致）
                logger.info(f"[BotEngine] Bot {self.bot_id} 开始同步交易所状态")
                await self._sync_state_with_exchange()

                # 主循环
                # 调整为10秒间隔，降低API请求频率
                logger.info(f"[BotEngine] Bot {self.bot_id} 进入主循环（10秒间隔）")
                cycle_count = 0
                while self.is_running:
                    cycle_count += 1
                    logger.debug(f"[BotEngine] Bot {self.bot_id} 第 {cycle_count} 次循环开始")
                    await self._execute_cycle()
                    logger.debug(f"[BotEngine] Bot {self.bot_id} 第 {cycle_count} 次循环完成，等待10秒")
                    await asyncio.sleep(10)  # 每10秒检查一次，降低API请求频率

            except Exception as e:
                logger.error(f"[BotEngine] Bot {self.bot_id} 运行错误: {str(e)}", exc_info=True)
                try:
                    await self._log_error(f"运行错误: {str(e)}")
                    # 遇到异常时停止机器人，而不是暂停
                    self.is_running = False
                    if self.bot:
                        self.bot.status = "stopped"
                        await self.db.commit()
                        logger.info(f"[BotEngine] Bot {self.bot_id} 因异常已停止")
                except Exception as inner_e:
                    logger.error(f"[BotEngine] Bot {self.bot_id} 更新停止状态失败: {str(inner_e)}")
            finally:
                # 确保无论如何退出，都更新状态为 stopped（如果还是 running）
                try:
                    if self.db and self.bot and self.bot.status == "running":
                        self.bot.status = "stopped"
                        await self.db.commit()
                        logger.info(f"[BotEngine] Bot {self.bot_id} 最终状态已设为 stopped")
                except Exception as e:
                    logger.error(f"[BotEngine] Bot {self.bot_id} 最终状态更新失败: {str(e)}")
                logger.info(f"[BotEngine] Bot {self.bot_id} 会话即将关闭")

    async def _run(self):
        """异步任务执行的运行方法"""
        logger.info(f"[BotEngine] Bot {self.bot_id} _run() 方法被调用")
        try:
            await self.start()
        except asyncio.CancelledError:
            # 任务被取消是正常的关闭流程，不记录错误
            logger.info(f"[BotEngine] Bot {self.bot_id} 任务被取消（正常关闭）")
            raise  # 重新抛出，让 asyncio 知道任务已取消
        except Exception as e:
            logger.error(f"[BotEngine] Bot {self.bot_id} _run() 执行异常: {str(e)}", exc_info=True)
    
    async def pause(self):
        """暂停机器人"""
        logger.info(f"[BotEngine] 暂停机器人: Bot {self.bot_id}")
        self.is_running = False
        if self.db and self.bot:
            self.bot.status = "paused"
            await self.db.commit()
        
        # 停止数据同步服务
        try:
            from app.services.data_sync_service import data_sync_service
            await data_sync_service.stop_sync_for_bot(self.bot_id)
            logger.info(f"[BotEngine] 已停止机器人 {self.bot_id} 的数据同步服务")
        except Exception as e:
            logger.warning(f"[BotEngine] 停止数据同步服务失败: {str(e)}")
    
    async def stop(self):
        """停止机器人"""
        logger.info(f"[BotEngine] 停止机器人: Bot {self.bot_id}")
        self.is_running = False
        if self.db and self.bot:
            self.bot.status = "stopped"
            await self.db.commit()
    
    async def _execute_cycle(self):
        """执行一个交易循环"""
        # 开始性能计时
        self._start_cycle_timer()

        try:
            logger.debug(f"[BotEngine] Bot {self.bot.id} _execute_cycle() 开始执行")

            # 1. 获取当前市场价格
            logger.debug(f"[BotEngine] Bot {self.bot.id} 获取市场价格")
            try:
                market1_price = await self._get_market_price(self.bot.market1_symbol)
                market2_price = await self._get_market_price(self.bot.market2_symbol)
                logger.debug(f"[BotEngine] Bot {self.bot.id} 市场价格: {market1_price}, {market2_price}")
            except Exception as e:
                # 获取价格失败是常见的临时性错误，记录后跳过本次循环
                logger.warning(f"[BotEngine] Bot {self.bot.id} 获取市场价格失败: {str(e)}, 跳过本次循环")
                return

            # 2. 初始化起始价格(首次运行)
            if self.bot.market1_start_price is None or self.bot.market2_start_price is None:
                await self._initialize_start_prices(market1_price, market2_price)

            # 3. 计算当前价差
            logger.debug(f"[BotEngine] Bot {self.bot.id} 计算价差")
            current_spread = self.calculator.calculate_spread(
                market1_price,
                self.bot.market1_start_price,
                market2_price,
                self.bot.market2_start_price
            )
            logger.debug(f"[BotEngine] Bot {self.bot.id} 当前价差: {current_spread:.4f}%")

            # 4. 记录价差历史
            logger.debug(f"[BotEngine] Bot {self.bot.id} 记录价差历史")
            await self._record_spread(market1_price, market2_price, current_spread)

            # 4.5 推送价差更新
            await self._broadcast_spread_update(market1_price, market2_price, current_spread)

            # 4.6 更新持仓价格和未实现盈亏（降低频率）
            # 每3个循环才更新一次持仓，减少API请求
            self._position_update_counter += 1
            if self._position_update_counter >= self._position_update_interval:
                self._position_update_counter = 0
                try:
                    await self.update_position_prices()
                except Exception as e:
                    # 更新持仓价格失败时记录警告，但不影响主流程
                    logger.warning(f"[BotEngine] Bot {self.bot.id} 更新持仓价格失败: {str(e)}")
            else:
                logger.debug(f"[BotEngine] Bot {self.bot.id} 跳过持仓更新（{self._position_update_counter}/{self._position_update_interval}）")

            # 5. 获取当前持仓
            positions = await self._get_open_positions()

            # 6. 检查止盈止损
            if positions:
                # 计算总盈亏和投资额
                total_pnl = sum(pos.unrealized_pnl or Decimal('0') for pos in positions)
                total_investment = self._calculate_total_investment()
                pnl_ratio = (total_pnl / total_investment * 100) if total_investment > 0 else Decimal('0')

                # 判断止损是否启用
                stop_loss_enabled = self.bot.stop_loss_ratio > 0

                # 详细显示每个持仓的盈亏（INFO级别，方便追踪）
                logger.info(f"[盈亏详情] 保证金投资={total_investment:.2f} USDT, 总盈亏={total_pnl:.2f} USDT, 盈亏比例={pnl_ratio:.2f}%")
                for pos in positions:
                    # 安全处理可能为 None 的字段
                    amount_str = f"{pos.amount:.4f}" if pos.amount is not None else "0"
                    entry_price_str = f"{pos.entry_price:.2f}" if pos.entry_price is not None else "N/A"
                    current_price_str = f"{pos.current_price:.2f}" if pos.current_price is not None else "N/A"
                    unrealized_pnl_str = f"{pos.unrealized_pnl:.2f}" if pos.unrealized_pnl is not None else "0.00"

                    logger.info(
                        f"  - {pos.symbol} ({pos.side}): "
                        f"数量={amount_str}, 入场价={entry_price_str}, "
                        f"当前价={current_price_str}, 盈亏={unrealized_pnl_str} USDT"
                    )

                logger.debug(
                    f"[止盈止损] 止盈目标={self.bot.profit_ratio}%, "
                    f"止损阈值={'禁用' if not stop_loss_enabled else f'{self.bot.stop_loss_ratio}%'}"
                )

                if await self._should_take_profit(positions, current_spread):
                    logger.info(f"✅ 触发止盈: 盈亏比例 {pnl_ratio:.2f}% >= {self.bot.profit_ratio}%")
                    await self._close_all_positions()
                    return

                if stop_loss_enabled and await self._should_stop_loss(positions):
                    logger.warning(f"⚠️ 触发止损: 盈亏比例 {pnl_ratio:.2f}% <= -{self.bot.stop_loss_ratio}%")
                    await self._close_all_positions()
                    return

            # 7. 检查是否需要开仓/加仓
            if await self._should_open_position(current_spread):
                await self._open_position(market1_price, market2_price, current_spread)

            logger.debug(f"[BotEngine] Bot {self.bot.id} _execute_cycle() 执行完成")

        except Exception as e:
            # 记录错误但不停止机器人（除非是严重错误）
            logger.error(f"[BotEngine] Bot {self.bot.id} 执行循环错误: {str(e)}", exc_info=True)
            await self._log_error(f"执行循环错误: {str(e)}")

        finally:
            # 结束性能计时并记录指标
            cycle_time = self._end_cycle_timer()
            await self._log_performance_metrics(cycle_time)
    
    async def _set_leverage(self):
        """设置杠杆"""
        try:
            await self.exchange.set_leverage(self.bot.market1_symbol, self.bot.leverage)
            await self.exchange.set_leverage(self.bot.market2_symbol, self.bot.leverage)
            logger.info(f"设置杠杆: {self.bot.leverage}x")
        except Exception as e:
            logger.warning(f"设置杠杆失败: {str(e)}")

    async def _sync_state_with_exchange(self):
        """
        同步交易所状态与数据库状态

        防止后端重启后数据不一致的情况：
        1. 对比交易所实际持仓与数据库记录
        2. 修正不一致的持仓数据
        3. 修正 current_dca_count
        """
        try:
            logger.info(f"[状态同步] 开始同步机器人 {self.bot.id} 的状态")

            # 1. 获取交易所实际持仓
            exchange_positions = await self.exchange.get_all_positions()
            logger.info(f"[状态同步] 交易所持仓数量: {len(exchange_positions)}")

            # 过滤出本机器人相关的交易对
            bot_symbols = {self.bot.market1_symbol, self.bot.market2_symbol}
            relevant_exchange_positions = [
                pos for pos in exchange_positions
                if pos['symbol'] in bot_symbols
            ]
            logger.info(f"[状态同步] 本机器人相关持仓: {len(relevant_exchange_positions)}")

            # 2. 获取数据库持仓记录
            db_positions = await self._get_open_positions()
            logger.info(f"[状态同步] 数据库持仓记录: {len(db_positions)}")

            # 3. 对比并修正
            exchange_pos_map = {pos['symbol']: pos for pos in relevant_exchange_positions}
            db_pos_map = {pos.symbol: pos for pos in db_positions}

            # 3.1 检查交易所有但数据库没有的持仓（可能是崩溃后遗留）
            for symbol, exchange_pos in exchange_pos_map.items():
                if symbol not in db_pos_map:
                    logger.warning(
                        f"[状态同步] 发现交易所持仓但数据库无记录: {symbol}, "
                        f"side={exchange_pos['side']}, amount={exchange_pos['amount']}"
                    )

                    # 查询当前最大 cycle_number
                    from sqlalchemy import func
                    max_cycle_result = await self.db.execute(
                        select(func.max(Position.cycle_number))
                        .where(Position.bot_instance_id == self.bot.id)
                    )
                    max_cycle = max_cycle_result.scalar()
                    next_cycle = (max_cycle or 0) + 1

                    # 创建持仓记录
                    new_position = Position(
                        bot_instance_id=self.bot.id,
                        cycle_number=next_cycle,
                        symbol=symbol,
                        side=exchange_pos['side'],
                        amount=exchange_pos['amount'],
                        entry_price=exchange_pos['entry_price'],
                        current_price=exchange_pos.get('current_price') or exchange_pos['entry_price'],
                        unrealized_pnl=exchange_pos.get('unrealized_pnl', Decimal('0')),
                        is_open=True,
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow()
                    )
                    self.db.add(new_position)
                    logger.info(f"[状态同步] 已创建数据库持仓记录: {symbol}, cycle={next_cycle}")

            # 3.2 检查数据库有但交易所没有的持仓（可能已平仓）
            for symbol, db_pos in db_pos_map.items():
                if symbol not in exchange_pos_map:
                    logger.warning(
                        f"[状态同步] 数据库有记录但交易所无持仓: {symbol}, "
                        f"标记为已平仓"
                    )
                    db_pos.is_open = False
                    db_pos.closed_at = datetime.utcnow()
                    db_pos.updated_at = datetime.utcnow()

            # 4. 根据实际持仓修正 current_dca_count
            # 计算当前应有的 DCA 层级（基于持仓数量）
            actual_position_count = len(relevant_exchange_positions)

            if actual_position_count > 0:
                # 有持仓：计算 DCA 层级
                # 每次开仓包含 2 个持仓（market1 和 market2）
                actual_dca_count = actual_position_count // 2
                if actual_dca_count != self.bot.current_dca_count:
                    logger.warning(
                        f"[状态同步] DCA 计数不一致: "
                        f"数据库={self.bot.current_dca_count}, 实际={actual_dca_count}"
                    )
                    self.bot.current_dca_count = actual_dca_count
                    logger.info(f"[状态同步] 已修正 current_dca_count = {actual_dca_count}")
            else:
                # 无持仓：重置 DCA 状态，开始新的套利周期
                if self.bot.current_dca_count != 0 or self.bot.last_trade_spread is not None:
                    logger.warning(
                        f"[状态同步] 交易所无持仓，但数据库显示有交易状态，重置 DCA 状态"
                    )

                    # 关闭所有数据库中仍标记为开仓的持仓
                    for db_pos in db_positions:
                        if db_pos.is_open:
                            logger.info(f"[状态同步] 关闭数据库持仓: {db_pos.symbol}")
                            db_pos.is_open = False
                            db_pos.closed_at = datetime.utcnow()
                            db_pos.updated_at = datetime.utcnow()

                    # 重置 DCA 状态
                    self.bot.current_dca_count = 0
                    self.bot.last_trade_spread = None
                    self.bot.first_trade_spread = None
                    # 开始新的周期
                    self.bot.current_cycle += 1
                    logger.info(
                        f"[状态同步] 已重置 DCA 状态: "
                        f"current_dca_count=0, cycle={self.bot.current_cycle}"
                    )



            # 5. 提交所有修改
            await self.db.commit()
            logger.info(f"[状态同步] 状态同步完成")

            # 6. 记录同步结果
            await self._log_trade(
                f"状态同步完成: 交易所持仓={len(relevant_exchange_positions)}, "
                f"数据库持仓={len(db_positions)}, DCA层级={self.bot.current_dca_count}"
            )

        except Exception as e:
            logger.error(f"[状态同步] 同步失败: {str(e)}", exc_info=True)
            await self._log_error(f"状态同步失败: {str(e)}")
            # 同步失败不应该阻止机器人启动，记录错误即可

    
    async def _initialize_start_prices(self, current_market1_price: Decimal, current_market2_price: Decimal):
        """
        初始化起始价格
        
        如果 start_time 早于当前时间，尝试获取历史价格
        否则使用当前价格
        
        Args:
            current_market1_price: 当前 market1 价格
            current_market2_price: 当前 market2 价格
        """
        try:
            from datetime import datetime, timezone
            
            # 获取当前UTC时间
            now_utc = datetime.now(timezone.utc)
            
            # 确保 start_time 是 timezone-aware 的
            if self.bot.start_time.tzinfo is None:
                # 如果 start_time 没有时区信息，假设它是 UTC
                start_time_utc = self.bot.start_time.replace(tzinfo=timezone.utc)
            else:
                start_time_utc = self.bot.start_time
            
            # 计算时间差（秒）
            time_diff = (now_utc - start_time_utc).total_seconds()
            
            # 如果开始时间在未来或在5分钟以内，使用当前价格
            if time_diff < 300:  # 5分钟 = 300秒
                self.bot.market1_start_price = current_market1_price
                self.bot.market2_start_price = current_market2_price
                await self.db.commit()
                logger.info(
                    f"使用当前价格作为起始价格: "
                    f"{self.bot.market1_symbol}={current_market1_price}, "
                    f"{self.bot.market2_symbol}={current_market2_price}"
                )
                return
            
            # 开始时间在过去，尝试获取历史价格
            logger.info(
                f"检测到历史开始时间: {start_time_utc}, "
                f"距今 {time_diff/3600:.1f} 小时，尝试获取历史价格..."
            )
            
            # 将时间转换为毫秒时间戳
            timestamp_ms = int(start_time_utc.timestamp() * 1000)
            
            # 获取历史价格
            historical_price1 = await self.exchange.fetch_historical_price(
                self.bot.market1_symbol,
                timestamp_ms
            )
            
            historical_price2 = await self.exchange.fetch_historical_price(
                self.bot.market2_symbol,
                timestamp_ms
            )
            
            # 使用历史价格或回退到当前价格
            if historical_price1 and historical_price2:
                self.bot.market1_start_price = historical_price1
                self.bot.market2_start_price = historical_price2
                await self.db.commit()
                logger.info(
                    f"✅ 成功获取历史起始价格: "
                    f"{self.bot.market1_symbol}={historical_price1}, "
                    f"{self.bot.market2_symbol}={historical_price2} "
                    f"@ {start_time_utc}"
                )
            else:
                # 获取失败，使用当前价格作为备用方案
                self.bot.market1_start_price = current_market1_price
                self.bot.market2_start_price = current_market2_price
                await self.db.commit()
                logger.warning(
                    f"⚠️ 无法获取历史价格，使用当前价格: "
                    f"{self.bot.market1_symbol}={current_market1_price}, "
                    f"{self.bot.market2_symbol}={current_market2_price}"
                )
                
        except Exception as e:
            # 出错时使用当前价格作为备用方案
            logger.error(f"初始化起始价格失败: {str(e)}", exc_info=True)
            self.bot.market1_start_price = current_market1_price
            self.bot.market2_start_price = current_market2_price
            await self.db.commit()
            logger.warning(
                f"⚠️ 初始化失败，使用当前价格: "
                f"{self.bot.market1_symbol}={current_market1_price}, "
                f"{self.bot.market2_symbol}={current_market2_price}"
            )
    
    async def _get_market_price(self, symbol: str) -> Decimal:
        """
        获取市场价格（带缓存）

        使用缓存机制减少API请求频率
        """
        import time

        current_time = time.time()

        # 检查缓存
        if symbol in self._price_cache:
            cache_time = self._price_cache_time.get(symbol, 0)
            if current_time - cache_time < self._price_cache_ttl:
                # 缓存有效，直接返回
                logger.debug(f"使用缓存价格: {symbol} = {self._price_cache[symbol]}")
                return self._price_cache[symbol]

        # 缓存失效或不存在，从交易所获取
        ticker = await self.exchange.get_ticker(symbol)
        price = ticker['last_price']

        # 更新缓存
        self._price_cache[symbol] = price
        self._price_cache_time[symbol] = current_time

        logger.debug(f"获取新价格: {symbol} = {price}")
        return price
    
    async def _record_spread(
        self,
        market1_price: Decimal,
        market2_price: Decimal,
        spread: Decimal
    ):
        """记录价差历史"""
        spread_record = SpreadHistory(
            bot_instance_id=self.bot.id,
            market1_price=market1_price,
            market2_price=market2_price,
            spread_percentage=spread
        )
        self.db.add(spread_record)
        await self.db.commit()
        
        # 返回价差记录供推送使用
        return {
            "bot_instance_id": self.bot.id,
            "market1_price": float(market1_price),
            "market2_price": float(market2_price),
            "spread_percentage": float(spread),
            "recorded_at": spread_record.recorded_at.isoformat()
        }
    
    async def _should_open_position(self, current_spread: Decimal) -> bool:
        """判断是否应该开仓/加仓"""
        # 检查是否达到最大加仓次数
        if self.bot.current_dca_count >= self.bot.max_dca_times:
            return False
        
        # 获取当前DCA配置
        dca_level = self.bot.current_dca_count
        if dca_level >= len(self.bot.dca_config):
            return False
        
        dca_config = self.bot.dca_config[dca_level]
        target_spread = Decimal(str(dca_config['spread']))
        
        # 检查价差是否达到开仓阈值
        if self.bot.last_trade_spread is None:
            # 首次开仓,检查绝对价差
            return abs(current_spread) >= target_spread
        else:
            # 后续加仓,检查相对上次成交的价差
            spread_diff = abs(current_spread - self.bot.last_trade_spread)
            return spread_diff >= target_spread
    
    async def _open_position(
        self,
        market1_price: Decimal,
        market2_price: Decimal,
        current_spread: Decimal
    ):
        """执行开仓操作"""
        try:
            # 确定交易方向
            market1_change = self.calculator.calculate_price_change_percentage(
                market1_price, self.bot.market1_start_price
            )
            market2_change = self.calculator.calculate_price_change_percentage(
                market2_price, self.bot.market2_start_price
            )
            
            market1_side, market2_side = self.calculator.determine_trading_direction(
                market1_change, market2_change
            )
            
            # 如果启用反向开仓，反转交易方向
            if self.bot.reverse_opening:
                market1_side = 'sell' if market1_side == 'buy' else 'buy'
                market2_side = 'sell' if market2_side == 'buy' else 'buy'
                logger.info(
                    f"反向开仓模式: 原方向已反转 - "
                    f"{self.bot.market1_symbol}={market1_side}, "
                    f"{self.bot.market2_symbol}={market2_side}"
                )
            
            # 计算投资金额(考虑倍投和杠杆)
            # 在永续合约中：
            # - investment_per_order 是每单的保证金金额
            # - 实际合约价值 = 保证金 × 杠杆
            # - 下单数量 = 合约价值 / 价格
            dca_level = self.bot.current_dca_count
            dca_config = self.bot.dca_config[dca_level]
            multiplier = Decimal(str(dca_config['multiplier']))

            # 计算保证金金额
            margin_amount = self.bot.investment_per_order * multiplier

            # 计算合约价值（保证金 × 杠杆）
            contract_value = margin_amount * Decimal(str(self.bot.leverage))

            # 计算下单数量（合约数量）
            market1_amount = contract_value / market1_price
            market2_amount = contract_value / market2_price

            logger.info(
                f"开仓计算: 保证金={margin_amount} USDT, 杠杆={self.bot.leverage}x, "
                f"合约价值={contract_value} USDT"
            )

            # 下单
            logger.info(
                f"开仓: {self.bot.market1_symbol} {market1_side} {market1_amount}, "
                f"{self.bot.market2_symbol} {market2_side} {market2_amount}"
            )
            
            order1 = await self.exchange.create_market_order(
                self.bot.market1_symbol,
                market1_side,
                market1_amount
            )

            order2 = await self.exchange.create_market_order(
                self.bot.market2_symbol,
                market2_side,
                market2_amount
            )

            # 🔥 关键修复：市价单创建后等待成交，然后重新查询订单状态获取实际成交数量
            logger.info(f"等待订单成交...")
            await asyncio.sleep(2)  # 等待2秒让订单成交

            # 重新查询订单状态，获取实际成交数量
            try:
                order1 = await self.exchange.get_order(order1['id'], self.bot.market1_symbol)
                order2 = await self.exchange.get_order(order2['id'], self.bot.market2_symbol)
                logger.info(
                    f"订单查询成功: {self.bot.market1_symbol} filled={order1['filled']}, "
                    f"{self.bot.market2_symbol} filled={order2['filled']}"
                )
            except Exception as e:
                logger.warning(f"重新查询订单状态失败: {str(e)}, 使用原始订单数据")

            # 检查订单是否成交
            if order1['filled'] == Decimal('0') or order2['filled'] == Decimal('0'):
                logger.error(
                    f"订单未成交: {self.bot.market1_symbol} filled={order1['filled']}, "
                    f"{self.bot.market2_symbol} filled={order2['filled']}"
                )
                await self._log_error(f"开仓失败: 订单未成交")
                return

            # 保存订单记录
            await self._save_order(order1, dca_level + 1)
            await self._save_order(order2, dca_level + 1)

            # 创建或更新持仓记录（使用订单中的实际成交价，不再传入预估价格）
            await self._create_or_update_position(order1, market1_side, dca_level + 1)
            await self._create_or_update_position(order2, market2_side, dca_level + 1)
            
            # 更新机器人状态
            self.bot.current_dca_count += 1
            self.bot.last_trade_spread = current_spread
            if self.bot.first_trade_spread is None:
                self.bot.first_trade_spread = current_spread
            self.bot.total_trades += 2
            
            await self.db.commit()
            
            await self._log_trade(
                f"开仓成功: 第{self.bot.current_dca_count}次加仓, "
                f"价差: {current_spread:.4f}%"
            )
        
        except Exception as e:
            logger.error(f"开仓失败: {str(e)}", exc_info=True)
            await self._log_error(f"开仓失败: {str(e)}")
    
    async def _save_order(self, order_data: dict, dca_level: int):
        """保存订单记录"""
        order = Order(
            bot_instance_id=self.bot.id,
            cycle_number=self.bot.current_cycle,
            exchange_order_id=order_data['id'],
            symbol=order_data['symbol'],
            side=order_data['side'],
            order_type=order_data['type'],
            price=order_data.get('price'),
            amount=order_data['amount'],
            filled_amount=order_data['filled'],
            cost=order_data.get('cost'),
            status=order_data['status'],
            dca_level=dca_level,
            filled_at=datetime.utcnow() if order_data['status'] == 'closed' else None
        )
        self.db.add(order)
        await self.db.commit()
        
        # 推送订单更新
        await self._broadcast_order_update({
            "id": order.id,
            "bot_instance_id": self.bot.id,
            "cycle_number": order.cycle_number,
            "exchange_order_id": order_data['id'],
            "symbol": order_data['symbol'],
            "side": order_data['side'],
            "order_type": order_data['type'],
            "price": float(order_data.get('price')) if order_data.get('price') else None,
            "amount": float(order_data['amount']),
            "filled_amount": float(order_data['filled']),
            "cost": float(order_data.get('cost')) if order_data.get('cost') else None,
            "status": order_data['status'],
            "dca_level": dca_level,
            "created_at": order.created_at.isoformat(),
            "updated_at": order.updated_at.isoformat(),
            "filled_at": order.created_at.isoformat() if order_data['status'] == 'closed' else None
        })
    
    async def _get_open_positions(self):
        """获取当前打开的持仓"""
        result = await self.db.execute(
            select(Position)
            .where(
                Position.bot_instance_id == self.bot.id,
                Position.is_open == True
            )
        )
        return result.scalars().all()
    
    async def _should_take_profit(
        self,
        positions: list,
        current_spread: Decimal
    ) -> bool:
        """判断是否应该止盈"""
        if self.bot.profit_mode == "regression":
            # 回归止盈
            return self.calculator.should_take_profit_regression(
                current_spread,
                self.bot.first_trade_spread,
                self.bot.profit_ratio
            )
        else:
            # 仓位止盈
            total_pnl = sum(pos.unrealized_pnl or Decimal('0') for pos in positions)

            # 计算实际投资的保证金总额（考虑 DCA 倍投）
            total_investment = self._calculate_total_investment()

            return self.calculator.should_take_profit_position(
                total_pnl,
                total_investment,
                self.bot.profit_ratio
            )

    async def _should_stop_loss(self, positions: list) -> bool:
        """判断是否应该止损"""
        total_pnl = sum(pos.unrealized_pnl or Decimal('0') for pos in positions)

        # 计算实际投资的保证金总额（考虑 DCA 倍投）
        total_investment = self._calculate_total_investment()

        return self.calculator.should_stop_loss(
            total_pnl,
            total_investment,
            self.bot.stop_loss_ratio
        )

    def _calculate_total_investment(self) -> Decimal:
        """
        计算实际投资的保证金总额

        考虑 DCA 倍投配置，计算所有已开仓的实际保证金总和

        Returns:
            保证金总额（USDT）
        """
        total = Decimal('0')

        # 累加每次开仓的实际投资额
        for i in range(self.bot.current_dca_count):
            if i < len(self.bot.dca_config):
                multiplier = Decimal(str(self.bot.dca_config[i]['multiplier']))
                total += self.bot.investment_per_order * multiplier
            else:
                # 如果超出配置范围，使用基础投资额
                total += self.bot.investment_per_order

        return total
    
    async def _close_all_positions(self):
        """平仓所有持仓并计算总收益"""
        # 🔥 关键修复：先获取所有需要的数据,避免在事务中执行新查询
        positions = None
        try:
            logger.info(f"开始平仓: {self.bot.bot_name}")

            # 先获取持仓列表（在任何 commit 之前）
            positions = await self._get_open_positions()
            
            if not positions:
                logger.info(f"没有需要平仓的持仓")
                return

            # 🔥 新增：累计本次平仓的已实现盈亏
            cycle_realized_pnl = Decimal('0')

            for position in positions:
                # 平仓订单方向与持仓方向相反
                # 注意：数据库中 side 可能是 'buy'/'sell' (订单方向) 或 'long'/'short' (持仓方向)
                # 需要统一转换
                if position.side in ['buy', 'long']:
                    # 做多持仓，用 sell 平仓
                    close_side = 'sell'
                    position_side = 'long'
                else:
                    # 做空持仓，用 buy 平仓
                    close_side = 'buy'
                    position_side = 'short'

                logger.info(
                    f"准备平仓: {position.symbol}, "
                    f"数据库side={position.side}, 持仓方向={position_side}, 平仓方向={close_side}"
                )

                # 从交易所获取实际持仓数量
                try:
                    exchange_position = await self.exchange.get_position(position.symbol)

                    if exchange_position is None:
                        logger.warning(
                            f"交易所无持仓 {position.symbol}，但数据库有记录，跳过平仓"
                        )

                        # 🔥 累计该持仓的盈亏（即使交易所无持仓，数据库可能记录了盈亏）
                        if position.unrealized_pnl is not None:
                            cycle_realized_pnl += position.unrealized_pnl
                            logger.info(
                                f"持仓 {position.symbol} (交易所已平) 已实现盈亏: {position.unrealized_pnl:.2f} USDT, "
                                f"累计盈亏: {cycle_realized_pnl:.2f} USDT"
                            )

                        # 直接更新数据库状态为已关闭
                        position.is_open = False
                        position.closed_at = datetime.utcnow()
                        continue

                    # 使用交易所实际持仓数量
                    actual_amount = exchange_position['amount']

                    # 检查数量是否满足最小精度要求（OKX 合约最小为 0.01）
                    min_amount = Decimal('0.01')
                    if actual_amount < min_amount:
                        logger.warning(
                            f"持仓数量 {actual_amount} 小于最小精度 {min_amount}，"
                            f"跳过平仓 {position.symbol}"
                        )

                        # 🔥 累计该持仓的盈亏（即使金额太小无法平仓）
                        if position.unrealized_pnl is not None:
                            cycle_realized_pnl += position.unrealized_pnl
                            logger.info(
                                f"持仓 {position.symbol} (数量太小) 已实现盈亏: {position.unrealized_pnl:.2f} USDT, "
                                f"累计盈亏: {cycle_realized_pnl:.2f} USDT"
                            )

                        # 标记为已关闭（金额太小，视为已平仓）
                        position.is_open = False
                        position.closed_at = datetime.utcnow()
                        continue

                    logger.info(
                        f"平仓 {position.symbol}: 数据库数量={position.amount}, "
                        f"实际数量={actual_amount}"
                    )

                except Exception as e:
                    logger.warning(
                        f"获取交易所持仓失败 {position.symbol}: {str(e)}，"
                        f"使用数据库数量: {position.amount}"
                    )
                    actual_amount = position.amount

                # 创建平仓订单
                order = await self.exchange.create_market_order(
                    position.symbol,
                    close_side,
                    actual_amount,
                    reduce_only=True
                )

                # 🔥 关键修复：市价单创建后等待成交，然后重新查询订单状态获取实际成交价格和成本
                logger.info(f"等待平仓订单成交...")
                await asyncio.sleep(2)  # 等待2秒让订单成交

                # 重新查询订单状态，获取实际成交价格和成本
                try:
                    order = await self.exchange.get_order(order['id'], position.symbol)
                    logger.info(
                        f"平仓订单查询成功: {position.symbol} "
                        f"filled={order['filled']}, price={order.get('price')}, cost={order.get('cost')}"
                    )
                except Exception as e:
                    logger.warning(f"重新查询平仓订单状态失败: {str(e)}, 使用原始订单数据")

                # 保存平仓订单
                await self._save_order(order, 0)  # dca_level=0表示平仓

                # 🔥 累计本次持仓的已实现盈亏
                if position.unrealized_pnl is not None:
                    cycle_realized_pnl += position.unrealized_pnl
                    logger.info(
                        f"持仓 {position.symbol} 已实现盈亏: {position.unrealized_pnl:.2f} USDT, "
                        f"累计盈亏: {cycle_realized_pnl:.2f} USDT"
                    )

                # 更新持仓状态
                position.is_open = False
                position.closed_at = datetime.utcnow()

                # 推送持仓更新
                await self._broadcast_position_update({
                    "id": position.id,
                    "bot_instance_id": position.bot_instance_id,
                    "symbol": position.symbol,
                    "side": position.side,
                    "amount": float(position.amount),
                    "entry_price": float(position.entry_price),
                    "current_price": float(position.current_price),
                    "unrealized_pnl": float(position.unrealized_pnl) if position.unrealized_pnl else None,
                    "is_open": position.is_open,
                    "created_at": position.created_at.isoformat(),
                    "updated_at": position.updated_at.isoformat(),
                    "closed_at": position.closed_at.isoformat() if position.closed_at else None
                })

            # 🔥 更新总收益
            self.bot.total_profit += cycle_realized_pnl
            logger.info(
                f"💰 本次平仓盈亏: {cycle_realized_pnl:.2f} USDT, "
                f"总收益: {self.bot.total_profit:.2f} USDT"
            )

            # 更新机器人状态
            self.bot.current_cycle += 1
            self.bot.current_dca_count = 0
            self.bot.last_trade_spread = None
            self.bot.first_trade_spread = None

            await self.db.commit()

            await self._log_trade(
                f"平仓成功 - 本轮盈亏: {cycle_realized_pnl:.2f} USDT, "
                f"总收益: {self.bot.total_profit:.2f} USDT"
            )

            # 推送状态更新
            await self._broadcast_status_update({
                "bot_instance_id": self.bot.id,
                "status": self.bot.status,
                "current_cycle": self.bot.current_cycle,
                "current_dca_count": self.bot.current_dca_count,
                "total_trades": self.bot.total_trades,
                "updated_at": datetime.utcnow().isoformat()
            })

            # 检查是否需要暂停
            if self.bot.pause_after_close:
                await self.pause()

        except Exception as e:
            logger.error(f"平仓失败: {str(e)}", exc_info=True)
            # 🔥 关键修复：记录错误但不调用 _log_error (避免在异常处理中再次操作数据库)
            try:
                # 仅记录到数据库,不再 commit (会在外层 commit)
                if self.db:
                    log = TradeLog(
                        bot_instance_id=self.bot.id,
                        log_type="error",
                        message=f"平仓失败: {str(e)}"
                    )
                    self.db.add(log)
                    # 不调用 commit(),避免嵌套事务问题
            except Exception as log_error:
                logger.error(f"记录错误日志失败: {str(log_error)}")
    
    async def close_all_positions(self):
        """
        公共平仓方法，供外部调用
        
        这个方法会触发平仓所有持仓的操作，
        与内部自动平仓使用相同的逻辑
        """
        await self._close_all_positions()
    
    async def _log_trade(self, message: str):
        """记录交易日志"""
        log = TradeLog(
            bot_instance_id=self.bot.id,
            log_type="trade",
            message=message
        )
        self.db.add(log)
        await self.db.commit()
    
    def _get_websocket_manager(self):
        """获取WebSocket管理器实例"""
        if self._websocket_manager is None:
            # 延迟导入避免循环依赖
            from app.api.v1.websocket import manager
            self._websocket_manager = manager
        return self._websocket_manager
    
    async def _broadcast_spread_update(self, market1_price, market2_price, spread):
        """广播价差更新"""
        try:
            manager = self._get_websocket_manager()
            spread_data = {
                "bot_instance_id": self.bot.id,
                "market1_price": float(market1_price),
                "market2_price": float(market2_price),
                "spread_percentage": float(spread),
                "recorded_at": datetime.utcnow().isoformat()
            }
            await manager.broadcast_spread_update(self.bot.id, spread_data)
        except Exception as e:
            logger.error(f"广播价差更新失败: {str(e)}")
    
    async def _broadcast_order_update(self, order_data):
        """广播订单更新"""
        try:
            manager = self._get_websocket_manager()
            await manager.broadcast_order_update(self.bot.id, order_data)
        except Exception as e:
            logger.error(f"广播订单更新失败: {str(e)}")
    
    async def _broadcast_position_update(self, position_data):
        """广播持仓更新"""
        try:
            manager = self._get_websocket_manager()
            await manager.broadcast_position_update(self.bot.id, position_data)
        except Exception as e:
            logger.error(f"广播持仓更新失败: {str(e)}")
    
    async def _broadcast_status_update(self, status_data):
        """广播状态更新"""
        try:
            manager = self._get_websocket_manager()
            await manager.broadcast_status_update(self.bot.id, status_data)
        except Exception as e:
            logger.error(f"广播状态更新失败: {str(e)}")
    
    async def _log_error(self, message: str):
        """记录错误日志"""
        log = TradeLog(
            bot_instance_id=self.bot.id,
            log_type="error",
            message=message
        )
        self.db.add(log)
        await self.db.commit()
    
    async def _create_or_update_position(
        self,
        order_data: dict,
        side: str,
        dca_level: int
    ):
        """创建或更新持仓记录"""
        try:
            # 🔥 修复：使用订单的实际成交价格，而不是预估价格
            # 计算实际成交均价
            if order_data['filled'] > 0 and order_data.get('cost'):
                actual_price = Decimal(str(order_data['cost'])) / Decimal(str(order_data['filled']))
            elif order_data.get('price'):
                # 如果cost不可用，使用订单返回的price字段
                actual_price = Decimal(str(order_data['price']))
            else:
                # 最后的备用方案（理论上不应该走到这里）
                logger.warning(f"⚠️ 无法获取订单实际成交价，订单数据: {order_data}")
                actual_price = Decimal('0')
            
            logger.info(
                f"📊 订单实际成交价: {order_data['symbol']} = {actual_price:.2f} USDT "
                f"(成交量={order_data['filled']}, 成本={order_data.get('cost')})"
            )
            
            # 检查是否已有该交易对的持仓
            result = await self.db.execute(
                select(Position)
                .where(
                    Position.bot_instance_id == self.bot.id,
                    Position.symbol == order_data['symbol'],
                    Position.is_open == True
                )
            )
            position = result.scalar_one_or_none()
            
            if position:
                # 更新现有持仓
                if position.side == side:
                    # 同向加仓，计算新的平均价格
                    old_amount = position.amount
                    old_cost = old_amount * position.entry_price
                    new_amount = Decimal(str(order_data['filled']))
                    new_cost = new_amount * actual_price  # 使用实际成交价
                    
                    total_amount = old_amount + new_amount
                    total_cost = old_cost + new_cost
                    new_avg_price = total_cost / total_amount
                    
                    logger.info(
                        f"📈 加仓计算: 原持仓={old_amount:.4f}@{position.entry_price:.2f}, "
                        f"新增={new_amount:.4f}@{actual_price:.2f}, "
                        f"总持仓={total_amount:.4f}@{new_avg_price:.2f}"
                    )
                    
                    position.amount = total_amount
                    position.entry_price = new_avg_price
                    position.current_price = actual_price
                    position.updated_at = datetime.utcnow()
                else:
                    # 反向交易，减少持仓
                    position.amount -= Decimal(str(order_data['filled']))
                    if position.amount <= Decimal('0'):
                        # 持仓已完全平仓
                        position.is_open = False
                        position.closed_at = datetime.utcnow()
                    position.updated_at = datetime.utcnow()
                
                await self.db.commit()
                
                # 推送持仓更新
                await self._broadcast_position_update({
                    "id": position.id,
                    "bot_instance_id": position.bot_instance_id,
                    "symbol": position.symbol,
                    "side": position.side,
                    "amount": float(position.amount),
                    "entry_price": float(position.entry_price),
                    "current_price": float(position.current_price),
                    "unrealized_pnl": float(position.unrealized_pnl) if position.unrealized_pnl else None,
                    "is_open": position.is_open,
                    "created_at": position.created_at.isoformat(),
                    "updated_at": position.updated_at.isoformat(),
                    "closed_at": position.closed_at.isoformat() if position.closed_at else None
                })
            else:
                # 创建新持仓
                # 将订单方向转换为持仓方向
                # buy → long (做多), sell → short (做空)
                position_side = 'long' if side == 'buy' else 'short'

                position = Position(
                    bot_instance_id=self.bot.id,
                    cycle_number=self.bot.current_cycle,
                    symbol=order_data['symbol'],
                    side=position_side,  # 使用持仓方向，而不是订单方向
                    amount=Decimal(str(order_data['filled'])),
                    entry_price=actual_price,  # 使用实际成交价
                    current_price=actual_price,  # 使用实际成交价
                    is_open=True
                )
                self.db.add(position)
                await self.db.commit()

                logger.info(
                    f"✅ 创建持仓: {order_data['symbol']}, "
                    f"订单方向={side}, 持仓方向={position_side}, "
                    f"数量={position.amount:.4f}, 入场价={actual_price:.2f} USDT"
                )
                
                # 推送持仓更新
                await self._broadcast_position_update({
                    "id": position.id,
                    "bot_instance_id": position.bot_instance_id,
                    "symbol": position.symbol,
                    "side": position.side,
                    "amount": float(position.amount),
                    "entry_price": float(position.entry_price),
                    "current_price": float(position.current_price),
                    "unrealized_pnl": float(position.unrealized_pnl) if position.unrealized_pnl else None,
                    "is_open": position.is_open,
                    "created_at": position.created_at.isoformat(),
                    "updated_at": position.updated_at.isoformat(),
                    "closed_at": position.closed_at.isoformat() if position.closed_at else None
                })
        
        except Exception as e:
            logger.error(f"创建或更新持仓失败: {str(e)}", exc_info=True)
            await self._log_error(f"创建或更新持仓失败: {str(e)}")
    
    async def update_position_prices(self):
        """更新所有持仓的当前价格和未实现盈亏"""
        try:
            positions = await self._get_open_positions()

            for position in positions:
                # 从交易所获取实际持仓数据（包含真实的盈亏）
                try:
                    exchange_position = await self.exchange.get_position(position.symbol)

                    if exchange_position:
                        # 使用交易所返回的真实数据
                        position.current_price = exchange_position['current_price']
                        position.unrealized_pnl = exchange_position['unrealized_pnl']
                        position.updated_at = datetime.utcnow()

                        logger.debug(
                            f"更新持仓: {position.symbol}, "
                            f"价格={position.current_price}, "
                            f"盈亏={position.unrealized_pnl} USDT"
                        )
                    else:
                        # 交易所没有持仓，标记为已关闭
                        logger.warning(f"交易所无持仓 {position.symbol}，标记为已关闭")
                        position.is_open = False
                        position.closed_at = datetime.utcnow()

                except Exception as e:
                    logger.warning(
                        f"从交易所获取持仓 {position.symbol} 失败: {str(e)}，"
                        f"使用当前价格估算"
                    )
                    # 降级方案：用当前市价估算
                    try:
                        current_price = await self._get_market_price(position.symbol)
                        position.current_price = current_price
                        # 简单估算盈亏（不准确，仅作参考）
                        if position.side == 'long':
                            position.unrealized_pnl = (current_price - position.entry_price) * position.amount
                        else:
                            position.unrealized_pnl = (position.entry_price - current_price) * position.amount
                        position.updated_at = datetime.utcnow()
                    except Exception as inner_e:
                        logger.error(f"更新价格失败: {str(inner_e)}")
                        continue

                # 推送持仓更新
                await self._broadcast_position_update({
                    "id": position.id,
                    "bot_instance_id": position.bot_instance_id,
                    "symbol": position.symbol,
                    "side": position.side,
                    "amount": float(position.amount),
                    "entry_price": float(position.entry_price),
                    "current_price": float(position.current_price),
                    "unrealized_pnl": float(position.unrealized_pnl) if position.unrealized_pnl else None,
                    "is_open": position.is_open,
                    "created_at": position.created_at.isoformat(),
                    "updated_at": position.updated_at.isoformat(),
                    "closed_at": position.closed_at.isoformat() if position.closed_at else None
                })

            await self.db.commit()

        except Exception as e:
            logger.error(f"更新持仓价格失败: {str(e)}", exc_info=True)
            await self._log_error(f"更新持仓价格失败: {str(e)}")

    def _init_performance_monitoring(self):
        """初始化性能监控"""
        self.cycle_count = 0
        self.cycle_start_time = None
        self.cycle_times = []
        self.total_cycle_time = 0

    def _start_cycle_timer(self):
        """开始循环计时"""
        import time
        self.cycle_start_time = time.time()

    def _end_cycle_timer(self):
        """结束循环计时并记录"""
        import time
        if self.cycle_start_time:
            cycle_time = time.time() - self.cycle_start_time
            self.cycle_times.append(cycle_time)
            self.total_cycle_time += cycle_time
            self.cycle_count += 1

            # 保持最近100次循环的数据
            if len(self.cycle_times) > 100:
                self.cycle_times.pop(0)

            return cycle_time
        return 0

    async def _log_performance_metrics(self, cycle_time: float):
        """记录性能指标"""
        if self.cycle_count % 100 == 0:  # 每100次循环记录一次统计
            avg_time = self.total_cycle_time / self.cycle_count
            recent_avg = sum(self.cycle_times) / len(self.cycle_times)

            logger.info(
                f"[BotEngine] Bot {self.bot.id} 性能统计 - "
                f"总循环: {self.cycle_count}, "
                f"平均耗时: {avg_time:.3f}s, "
                f"最近100次平均: {recent_avg:.3f}s, "
                f"本次耗时: {cycle_time:.3f}s"
            )

            # 性能警告
            if cycle_time > 10.0:  # 单次循环超过10秒
                logger.warning(
                    f"[BotEngine] Bot {self.bot.id} 循环执行缓慢: {cycle_time:.3f}s"
                )

            if recent_avg > 5.0:  # 平均超过5秒
                logger.warning(
                    f"[BotEngine] Bot {self.bot.id} 最近循环平均执行缓慢: {recent_avg:.3f}s"
                )