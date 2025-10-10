"""
完整的 WebSocket 测试：先登录获取token，然后测试 WebSocket 连接
"""
import asyncio
import json
import websockets
import requests
from datetime import datetime

def login_and_get_token():
    """登录并获取访问令牌"""
    login_url = "http://localhost:8000/api/v1/auth/login"
    
    # 使用 JSON 格式
    login_data = {
        "username": "admin",
        "password": "admin123"
    }
    
    print("正在登录...")
    try:
        response = requests.post(login_url, json=login_data)
        response.raise_for_status()
        
        data = response.json()
        token = data.get("access_token")
        
        if token:
            print(f"✅ 登录成功，获取到 token: {token[:50]}...")
            return token
        else:
            print(f"❌ 登录响应中没有 access_token: {data}")
            return None
            
    except Exception as e:
        print(f"❌ 登录失败: {type(e).__name__}: {str(e)}")
        return None

async def test_websocket(token, bot_id=1):
    """测试 WebSocket 连接"""
    ws_url = f"ws://localhost:8000/api/v1/ws/bot/{bot_id}?token={token}"
    
    print(f"\n正在连接 WebSocket (Bot ID: {bot_id})...")
    print(f"URL: ws://localhost:8000/api/v1/ws/bot/{bot_id}?token=...")
    
    try:
        async with websockets.connect(ws_url) as websocket:
            print("✅ WebSocket 连接成功!")
            
            # 接收初始消息
            print("\n等待初始消息...")
            try:
                initial_message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                data = json.loads(initial_message)
                print(f"📨 收到初始消息:")
                print(f"   类型: {data.get('type')}")
                print(f"   时间: {data.get('timestamp')}")
                if data.get('data'):
                    print(f"   数据: {json.dumps(data.get('data'), indent=6, ensure_ascii=False)}")
            except asyncio.TimeoutError:
                print("⚠️  等待初始消息超时")
            
            # 发送心跳测试
            print("\n💓 发送心跳测试...")
            ping_message = {"type": "ping"}
            await websocket.send(json.dumps(ping_message))
            print(f"   发送: {ping_message}")
            
            # 接收心跳响应
            try:
                pong_message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                pong_data = json.loads(pong_message)
                print(f"✅ 收到心跳响应:")
                print(f"   类型: {pong_data.get('type')}")
                print(f"   时间: {pong_data.get('timestamp')}")
            except asyncio.TimeoutError:
                print("⚠️  等待心跳响应超时")
            
            # 保持连接10秒，监听任何推送消息
            print("\n⏳ 保持连接10秒，监听实时推送消息...")
            start_time = asyncio.get_event_loop().time()
            message_count = 0
            
            try:
                while True:
                    elapsed = asyncio.get_event_loop().time() - start_time
                    if elapsed >= 10:
                        break
                    
                    remaining = 10 - elapsed
                    message = await asyncio.wait_for(websocket.recv(), timeout=remaining)
                    data = json.loads(message)
                    message_count += 1
                    
                    print(f"\n📨 收到推送消息 #{message_count}:")
                    print(f"   类型: {data.get('type')}")
                    print(f"   时间: {data.get('timestamp')}")
                    if data.get('data'):
                        print(f"   数据: {json.dumps(data.get('data'), indent=6, ensure_ascii=False)}")
                        
            except asyncio.TimeoutError:
                print(f"\n⏱️  {10}秒内共收到 {message_count} 条消息")
            
            print("\n✅ WebSocket 测试完成")
            return True
            
    except websockets.exceptions.InvalidStatusCode as e:
        print(f"❌ WebSocket 连接失败: HTTP {e.status_code}")
        if e.status_code == 403:
            print("   可能原因: Token 无效或已过期")
        elif e.status_code == 404:
            print("   可能原因: 机器人不存在或无权访问")
        return False
    except Exception as e:
        print(f"❌ WebSocket 测试失败: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """主函数"""
    print("=" * 70)
    print("WebSocket 完整连接测试")
    print("=" * 70)
    
    # 步骤 1: 登录获取 token
    token = login_and_get_token()
    if not token:
        print("\n❌ 无法获取访问令牌，测试终止")
        return
    
    # 步骤 2: 测试 WebSocket 连接
    print("\n" + "=" * 70)
    print("开始测试 WebSocket 连接")
    print("=" * 70)
    
    success = await test_websocket(token, bot_id=1)
    
    print("\n" + "=" * 70)
    if success:
        print("✅ 所有测试通过")
    else:
        print("❌ 测试失败")
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(main())