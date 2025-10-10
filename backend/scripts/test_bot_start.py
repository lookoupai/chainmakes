"""
测试机器人启动和运行
"""
import asyncio
import requests
import websockets
import json
from datetime import datetime

def login():
    """登录获取token"""
    response = requests.post(
        "http://localhost:8000/api/v1/auth/login",
        json={"username": "admin", "password": "admin123"}
    )
    return response.json()["access_token"]

def start_bot(bot_id, token):
    """启动机器人"""
    response = requests.post(
        f"http://localhost:8000/api/v1/bots/{bot_id}/start",
        headers={"Authorization": f"Bearer {token}"}
    )
    return response.json()

def get_bot_status(bot_id, token):
    """获取机器人状态"""
    response = requests.get(
        f"http://localhost:8000/api/v1/bots/{bot_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    return response.json()

async def monitor_websocket(bot_id, token, duration=30):
    """监听WebSocket消息"""
    ws_url = f"ws://localhost:8000/api/v1/ws/bot/{bot_id}?token={token}"
    
    print(f"\n[WS] 连接 WebSocket...")
    
    try:
        async with websockets.connect(ws_url) as websocket:
            print("[WS] 连接成功，开始监听消息...")
            start_time = asyncio.get_event_loop().time()
            message_count = 0
            
            while True:
                elapsed = asyncio.get_event_loop().time() - start_time
                if elapsed >= duration:
                    break
                
                try:
                    remaining = duration - elapsed
                    message = await asyncio.wait_for(websocket.recv(), timeout=remaining)
                    data = json.loads(message)
                    message_count += 1
                    
                    msg_type = data.get('type')
                    timestamp = data.get('timestamp')
                    
                    if msg_type == 'spread_update':
                        spread_data = data.get('data', {})
                        print(f"\n[{message_count}] 价差更新:")
                        print(f"   市场1价格: ${spread_data.get('market1_price')}")
                        print(f"   市场2价格: ${spread_data.get('market2_price')}")
                        print(f"   价差: {spread_data.get('spread_percentage')}%")
                        print(f"   时间: {spread_data.get('recorded_at')}")
                    
                    elif msg_type == 'order_update':
                        order_data = data.get('data', {})
                        print(f"\n[{message_count}] 订单更新:")
                        print(f"   交易对: {order_data.get('symbol')}")
                        print(f"   方向: {order_data.get('side')}")
                        print(f"   数量: {order_data.get('amount')}")
                        print(f"   状态: {order_data.get('status')}")
                    
                    elif msg_type == 'position_update':
                        pos_data = data.get('data', {})
                        print(f"\n[{message_count}] 持仓更新:")
                        print(f"   交易对: {pos_data.get('symbol')}")
                        print(f"   方向: {pos_data.get('side')}")
                        print(f"   数量: {pos_data.get('amount')}")
                        print(f"   入场价: ${pos_data.get('entry_price')}")
                        print(f"   当前价: ${pos_data.get('current_price')}")
                        print(f"   未实现盈亏: ${pos_data.get('unrealized_pnl')}")
                    
                    elif msg_type == 'status_update':
                        status_data = data.get('data', {})
                        print(f"\n[{message_count}] 状态更新:")
                        print(f"   状态: {status_data.get('status')}")
                        print(f"   当前循环: {status_data.get('current_cycle')}")
                        print(f"   当前DCA: {status_data.get('current_dca_count')}")
                        print(f"   总交易: {status_data.get('total_trades')}")
                    
                    else:
                        print(f"\n[{message_count}] {msg_type}: {data.get('data')}")
                        
                except asyncio.TimeoutError:
                    print(f"\n[WS] {duration}秒内共收到 {message_count} 条消息")
                    break
    
    except Exception as e:
        print(f"[WS] WebSocket 错误: {e}")

async def main():
    """主测试流程"""
    print("=" * 70)
    print("机器人启动和运行测试")
    print("=" * 70)
    
    # 1. 登录
    print("\n[1] 登录系统...")
    token = login()
    print("[OK] 登录成功")
    
    # 2. 选择机器人
    bot_id = 4  # 使用 Mock 交易所的机器人
    print(f"\n[2] 准备启动机器人 ID={bot_id}")
    
    # 3. 检查初始状态
    print("\n[3] 检查初始状态...")
    initial_status = get_bot_status(bot_id, token)
    print(f"   机器人名称: {initial_status.get('bot_name')}")
    print(f"   当前状态: {initial_status.get('status')}")
    print(f"   当前循环: {initial_status.get('current_cycle')}")
    print(f"   DCA次数: {initial_status.get('current_dca_count')}")
    
    # 4. 启动机器人
    print("\n[4] 启动机器人...")
    try:
        start_result = start_bot(bot_id, token)
        print(f"[OK] 机器人已启动")
        print(f"   新状态: {start_result.get('status')}")
    except Exception as e:
        print(f"[FAIL] 启动失败: {e}")
        return
    
    # 5. 监听WebSocket消息（30秒）
    print("\n[5] 监听实时数据（30秒）...")
    await monitor_websocket(bot_id, token, duration=30)
    
    # 6. 检查最终状态
    print("\n[6] 检查最终状态...")
    final_status = get_bot_status(bot_id, token)
    print(f"   当前状态: {final_status.get('status')}")
    print(f"   当前循环: {final_status.get('current_cycle')}")
    print(f"   DCA次数: {final_status.get('current_dca_count')}")
    print(f"   总交易: {final_status.get('total_trades')}")
    print(f"   总收益: ${final_status.get('total_profit')}")
    
    # 7. 停止机器人
    print("\n[7] 停止机器人...")
    try:
        response = requests.post(
            f"http://localhost:8000/api/v1/bots/{bot_id}/stop",
            headers={"Authorization": f"Bearer {token}"}
        )
        print(f"[OK] 机器人已停止")
    except Exception as e:
        print(f"[WARN] 停止失败: {e}")
    
    print("\n" + "=" * 70)
    print("[OK] 测试完成")
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(main())