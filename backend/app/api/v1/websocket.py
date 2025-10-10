"""
WebSocket实时数据推送相关的API路由
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, Depends
from typing import Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import json
import asyncio

from app.dependencies import get_db
from app.models.user import User
from app.models.bot_instance import BotInstance
from app.utils.security import verify_token
from app.utils.logger import setup_logger

logger = setup_logger('websocket')

router = APIRouter()


class ConnectionManager:
    """WebSocket连接管理器"""
    
    def __init__(self):
        # 按机器人ID分组的连接
        self.active_connections: Dict[int, List[WebSocket]] = {}
        # 连接到用户和机器人的映射
        self.connection_user_map: Dict[WebSocket, Dict[str, int]] = {}
    
    async def connect(self, websocket: WebSocket, bot_id: int, user_id: int):
        """连接WebSocket"""
        await websocket.accept()
        if bot_id not in self.active_connections:
            self.active_connections[bot_id] = []
        self.active_connections[bot_id].append(websocket)
        
        # 记录连接映射
        self.connection_user_map[websocket] = {
            "user_id": user_id,
            "bot_id": bot_id
        }
        
        logger.info(f"WebSocket连接建立: 用户{user_id} -> 机器人{bot_id}")
    
    async def disconnect(self, websocket: WebSocket):
        """断开WebSocket连接"""
        if websocket in self.connection_user_map:
            user_bot = self.connection_user_map[websocket]
            bot_id = user_bot["bot_id"]
            user_id = user_bot["user_id"]
            
            if bot_id in self.active_connections:
                if websocket in self.active_connections[bot_id]:
                    self.active_connections[bot_id].remove(websocket)
                if not self.active_connections[bot_id]:
                    del self.active_connections[bot_id]
            
            del self.connection_user_map[websocket]
            logger.info(f"WebSocket连接断开: 用户{user_id} -> 机器人{bot_id}")
    
    async def send_personal_message(self, websocket: WebSocket, message: dict):
        """向特定连接发送消息"""
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"发送WebSocket消息失败: {str(e)}")
            # 连接可能已断开,尝试清理
            await self.disconnect(websocket)
    
    async def broadcast_to_bot(self, bot_id: int, message: dict):
        """向指定机器人的所有连接广播消息"""
        if bot_id in self.active_connections:
            # 创建副本以避免在迭代时修改列表
            connections = self.active_connections[bot_id].copy()
            for connection in connections:
                await self.send_personal_message(connection, message)
    
    async def broadcast_spread_update(self, bot_id: int, spread_data: dict):
        """广播价差更新"""
        message = {
            "type": "spread_update",
            "timestamp": spread_data.get("recorded_at"),
            "data": spread_data
        }
        await self.broadcast_to_bot(bot_id, message)
    
    async def broadcast_order_update(self, bot_id: int, order_data: dict):
        """广播订单更新"""
        message = {
            "type": "order_update",
            "timestamp": order_data.get("created_at"),
            "data": order_data
        }
        await self.broadcast_to_bot(bot_id, message)
    
    async def broadcast_position_update(self, bot_id: int, position_data: dict):
        """广播持仓更新"""
        message = {
            "type": "position_update",
            "timestamp": position_data.get("updated_at"),
            "data": position_data
        }
        await self.broadcast_to_bot(bot_id, message)
    
    async def broadcast_status_update(self, bot_id: int, status_data: dict):
        """广播状态更新"""
        message = {
            "type": "status_update",
            "timestamp": status_data.get("updated_at"),
            "data": status_data
        }
        await self.broadcast_to_bot(bot_id, message)


# 全局连接管理器实例
manager = ConnectionManager()


@router.websocket("/bot/{bot_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    bot_id: int,
    token: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """
    WebSocket连接端点,实时推送机器人状态
    
    消息格式:
    {
        "type": "spread_update" | "order_update" | "position_update" | "status_update",
        "timestamp": "ISO时间戳",
        "data": {...}
    }
    
    查询参数:
    - token: JWT访问令牌
    """
    # 验证用户身份
    try:
        logger.info(f"[WebSocket] 收到连接请求: bot_id={bot_id}, token={'有' if token else '无'}")
        
        if not token:
            logger.warning(f"[WebSocket] 缺少访问令牌")
            await websocket.close(code=4001, reason="缺少访问令牌")
            return
        
        # 验证JWT令牌
        from app.utils.security import verify_token
        payload = verify_token(token, "access")
        logger.info(f"[WebSocket] JWT验证结果: payload={payload}")
        
        if not payload:
            logger.warning(f"[WebSocket] 无效的访问令牌")
            await websocket.close(code=4002, reason="无效的访问令牌")
            return
        
        user_id_str = payload.get("sub")
        logger.info(f"[WebSocket] 从JWT获取的user_id_str: {user_id_str}, 类型: {type(user_id_str)}")
        
        if not user_id_str:
            logger.warning(f"[WebSocket] 令牌格式错误: 缺少sub字段")
            await websocket.close(code=4003, reason="令牌格式错误")
            return
        
        # 转换用户ID为整数
        try:
            user_id = int(user_id_str)
            logger.info(f"[WebSocket] 转换后的user_id: {user_id}, 类型: {type(user_id)}")
        except (ValueError, TypeError) as e:
            logger.error(f"[WebSocket] 无效的用户ID: {user_id_str}, 错误: {e}")
            await websocket.close(code=4003, reason="无效的用户ID")
            return
        
        # 验证机器人存在且属于当前用户
        logger.info(f"[WebSocket] 开始查询机器人: bot_id={bot_id}, user_id={user_id}")
        result = await db.execute(
            select(BotInstance).where(
                BotInstance.id == bot_id,
                BotInstance.user_id == user_id
            )
        )
        bot = result.scalar_one_or_none()
        logger.info(f"[WebSocket] 机器人查询结果: bot={'存在' if bot else '不存在'}")
        
        if not bot:
            logger.warning(f"[WebSocket] 机器人不存在或无权限访问: bot_id={bot_id}, user_id={user_id}")
            await websocket.close(code=4004, reason="机器人不存在或无权限访问")
            return
        
        logger.info(f"[WebSocket] 认证成功: user_id={user_id}, bot_id={bot_id}")
        
    except Exception as e:
        logger.error(f"[WebSocket] 认证失败: {str(e)}", exc_info=True)
        await websocket.close(code=4000, reason="认证失败")
        return
    
    # 建立连接
    await manager.connect(websocket, bot_id, user_id)
    
    # 发送初始状态
    try:
        await manager.send_personal_message(websocket, {
            "type": "connection_established",
            "timestamp": asyncio.get_event_loop().time(),
            "data": {
                "bot_id": bot_id,
                "bot_name": bot.bot_name,
                "status": bot.status
            }
        })
    except Exception as e:
        logger.error(f"发送初始状态失败: {str(e)}")
    
    # 创建心跳处理任务
    async def handle_client_messages():
        """处理客户端消息的独立任务"""
        try:
            while True:
                try:
                    # 接收客户端消息(心跳或订阅特定事件)
                    data = await websocket.receive_text()
                    message = json.loads(data)

                    # 处理心跳 - 立即响应
                    if message.get("type") == "ping":
                        await websocket.send_json({
                            "type": "pong",
                            "timestamp": asyncio.get_event_loop().time()
                        })
                        logger.debug(f"已响应心跳: bot_id={bot_id}")

                    # TODO: 处理其他客户端消息,例如订阅特定事件

                except json.JSONDecodeError:
                    logger.warning(f"收到无效的JSON消息: {data}")
                except Exception as e:
                    logger.error(f"处理客户端消息失败: {str(e)}")
                    break

        except WebSocketDisconnect:
            logger.info(f"WebSocket客户端主动断开连接: 机器人{bot_id}")
        except Exception as e:
            logger.error(f"消息处理任务异常: {str(e)}")

    # 启动消息处理任务
    message_task = asyncio.create_task(handle_client_messages())

    try:
        # 等待任务完成
        await message_task
    except asyncio.CancelledError:
        logger.info(f"WebSocket连接任务被取消: 机器人{bot_id}")
    except Exception as e:
        logger.error(f"WebSocket连接异常: {str(e)}")
    finally:
        # 取消任务并清理连接
        if not message_task.done():
            message_task.cancel()
            try:
                await message_task
            except asyncio.CancelledError:
                pass
        await manager.disconnect(websocket)


# 导出管理器供其他模块使用
__all__ = ["manager"]