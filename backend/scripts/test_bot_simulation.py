import asyncio
import sys
import os
from datetime import datetime
from decimal import Decimal
import random

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.session import AsyncSessionLocal
from app.models.bot_instance import BotInstance
from app.models.order import Order
from app.models.position import Position
from app.api.v1.websocket import manager
from sqlalchemy import select

async def simulate_bot_activity():
    """模拟机器人活动并推送WebSocket消息"""
    async with AsyncSessionLocal() as db:
        # 获取测试机器人
        result = await db.execute(select(BotInstance).where(BotInstance.id == 3))
        bot = result.scalar_one_or_none()
        
        if not bot:
            print("机器人不存在")
            return
        
        print(f"开始模拟机器人活动: {bot.bot_name}")
        
        # 模拟订单更新
        order_data = {
            "id": 999,
            "bot_instance_id": bot.id,
            "symbol": "BTC/USDT",
            "side": "buy",
            "order_type": "market",
            "amount": "0.001",
            "filled_amount": "0.001",
            "status": "closed",
            "created_at": datetime.utcnow().isoformat()
        }
        
        await manager.broadcast_order_update(bot.id, order_data)
        print("推送订单更新")
        
        # 等待1秒
        await asyncio.sleep(1)
        
        # 模拟持仓更新
        position_data = {
            "id": 999,
            "bot_instance_id": bot.id,
            "symbol": "BTC/USDT",
            "side": "long",
            "amount": "0.001",
            "entry_price": "50000.00",
            "current_price": "51000.00",
            "unrealized_pnl": "10.00",
            "updated_at": datetime.utcnow().isoformat()
        }
        
        await manager.broadcast_position_update(bot.id, position_data)
        print("推送持仓更新")
        
        # 等待1秒
        await asyncio.sleep(1)
        
        # 模拟状态更新
        status_data = {
            "id": bot.id,
            "bot_name": bot.bot_name,
            "status": "running",
            "total_profit": "10.00",
            "total_trades": 1,
            "updated_at": datetime.utcnow().isoformat()
        }
        
        await manager.broadcast_status_update(bot.id, status_data)
        print("推送状态更新")
        
        print("模拟活动完成")

async def test_websocket_with_simulation():
    """测试WebSocket与模拟活动"""
    import websockets
    import json
    
    uri = "ws://localhost:8000/api/v1/ws/bot/3"
    token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIyIiwidXNlcm5hbWUiOiJ0ZXN0dXNlciIsImV4cCI6MTc1OTY1Mjg0OCwidHlwZSI6ImFjY2VzcyJ9._tBp7CpY4G0mT4cWXwpT1ua5TSi2SGjkyGgMYbicNjk"
    authenticated_uri = f"{uri}?token={token}"
    
    async with websockets.connect(authenticated_uri) as websocket:
        print("WebSocket连接已建立")
        
        # 启动模拟活动任务
        simulation_task = asyncio.create_task(simulate_bot_activity())
        
        # 接收消息
        timeout = 15  # 15秒超时
        try:
            while timeout > 0:
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                    data = json.loads(message)
                    print(f"收到消息: {data.get('type', 'unknown')}")
                    if data.get("type") == "connection_established":
                        print("连接确认消息")
                    elif data.get("type") == "order_update":
                        print(f"订单更新: {data.get('data', {}).get('status')}")
                    elif data.get("type") == "position_update":
                        print(f"持仓更新: {data.get('data', {}).get('unrealized_pnl')}")
                    elif data.get("type") == "status_update":
                        print(f"状态更新: {data.get('data', {}).get('status')}")
                except asyncio.TimeoutError:
                    timeout -= 1
                    if timeout % 3 == 0:
                        print(f"等待消息... ({timeout}秒)")
        except Exception as e:
            print(f"接收消息时出错: {e}")
        
        # 等待模拟任务完成
        await simulation_task

if __name__ == "__main__":
    asyncio.run(test_websocket_with_simulation())