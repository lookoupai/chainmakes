"""
测试 WebSocket 连接
"""
import asyncio
import json
import websockets
from datetime import datetime

async def test_websocket():
    """测试 WebSocket 连接"""
    # 使用 admin 用户的 token (需要先登录获取)
    token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxIiwidXNlcm5hbWUiOiJhZG1pbiIsImV4cCI6MTc1OTY4MDMwNSwidHlwZSI6ImFjY2VzcyJ9"  # 这是一个示例，实际使用时需要真实token
    bot_id = 1  # 测试机器人 ID
    
    ws_url = f"ws://localhost:8000/api/v1/ws/bot/{bot_id}?token={token}"
    
    print(f"正在连接 WebSocket: {ws_url}")
    
    try:
        async with websockets.connect(ws_url) as websocket:
            print("✅ WebSocket 连接成功!")
            
            # 接收初始消息
            try:
                initial_message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                data = json.loads(initial_message)
                print(f"\n📨 收到初始消息:")
                print(f"  类型: {data.get('type')}")
                print(f"  数据: {json.dumps(data.get('data'), indent=2, ensure_ascii=False)}")
            except asyncio.TimeoutError:
                print("⚠️  等待初始消息超时")
            
            # 发送心跳测试
            print("\n💓 发送心跳...")
            ping_message = {"type": "ping"}
            await websocket.send(json.dumps(ping_message))
            
            # 接收心跳响应
            try:
                pong_message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                pong_data = json.loads(pong_message)
                print(f"✅ 收到心跳响应: {pong_data.get('type')}")
            except asyncio.TimeoutError:
                print("⚠️  等待心跳响应超时")
            
            # 保持连接10秒，监听任何推送消息
            print("\n⏳ 保持连接10秒，监听推送消息...")
            try:
                while True:
                    message = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                    data = json.loads(message)
                    print(f"\n📨 收到推送消息:")
                    print(f"  类型: {data.get('type')}")
                    print(f"  时间: {data.get('timestamp')}")
                    print(f"  数据: {json.dumps(data.get('data'), indent=2, ensure_ascii=False)}")
            except asyncio.TimeoutError:
                print("⏱️  10秒内无新消息")
            
            print("\n✅ WebSocket 测试完成")
            
    except websockets.exceptions.InvalidStatusCode as e:
        print(f"❌ WebSocket 连接失败: HTTP {e.status_code}")
        print(f"   原因: {e}")
    except Exception as e:
        print(f"❌ WebSocket 测试失败: {type(e).__name__}: {str(e)}")

if __name__ == "__main__":
    print("=" * 60)
    print("WebSocket 连接测试")
    print("=" * 60)
    asyncio.run(test_websocket())