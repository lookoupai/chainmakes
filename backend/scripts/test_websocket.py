import asyncio
import websockets
import json

async def test_websocket():
    uri = "ws://localhost:8000/api/v1/ws/bot/3"
    token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIyIiwidXNlcm5hbWUiOiJ0ZXN0dXNlciIsImV4cCI6MTc1OTY1Mjg0OCwidHlwZSI6ImFjY2VzcyJ9._tBp7CpY4G0mT4cWXwpT1ua5TSi2SGjkyGgMYbicNjk"
    
    # 构建带认证的URI
    authenticated_uri = f"{uri}?token={token}"
    
    try:
        async with websockets.connect(authenticated_uri) as websocket:
            print("WebSocket连接已建立")
            
            # 发送订阅消息
            subscribe_msg = {
                "action": "subscribe",
                "data": {
                    "bot_id": 3
                }
            }
            await websocket.send(json.dumps(subscribe_msg))
            print("发送订阅消息")
            
            # 接收消息
            timeout = 10  # 10秒超时
            try:
                while timeout > 0:
                    try:
                        message = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                        data = json.loads(message)
                        print(f"收到消息: {data}")
                        if data.get("type") == "bot_status":
                            print(f"机器人状态更新: {data.get('data', {}).get('status')}")
                        elif data.get("type") == "order_update":
                            print(f"订单更新: {data.get('data', {}).get('status')}")
                        elif data.get("type") == "position_update":
                            print(f"持仓更新: {data.get('data', {}).get('unrealized_pnl')}")
                    except asyncio.TimeoutError:
                        timeout -= 1
                        print(f"等待消息... ({timeout}秒)")
            except Exception as e:
                print(f"接收消息时出错: {e}")
            
    except Exception as e:
        print(f"WebSocket连接失败: {e}")

if __name__ == "__main__":
    asyncio.run(test_websocket())