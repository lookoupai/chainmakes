"""
完整交易循环测试
测试: 开仓 → 加仓 → 止盈/止损平仓
"""
import asyncio
import requests
import websockets
import json
from decimal import Decimal
from datetime import datetime


BASE_URL = "http://localhost:8000"
WS_URL = "ws://localhost:8000"


def login():
    """登录获取token"""
    response = requests.post(
        f"{BASE_URL}/api/v1/auth/login",
        json={"username": "admin", "password": "admin123"}
    )
    return response.json()["access_token"]


def create_test_bot(token):
    """创建测试机器人"""
    bot_config = {
        "bot_name": f"交易循环测试机器人-{datetime.now().strftime('%H%M%S')}",
        "exchange_account_id": 3,  # Mock Exchange
        "market1_symbol": "BTC/USDT",
        "market2_symbol": "ETH/USDT",
        "start_time": datetime.now().isoformat(),  # 添加必需字段
        "leverage": 1,
        "order_type_open": "market",
        "order_type_close": "market",
        "investment_per_order": "100.00",
        "max_position_value": "1000.00",
        "max_dca_times": 3,  # 最多3次加仓
        "dca_config": [
            {"times": 1, "spread": "5.0", "multiplier": "1.0"},   # 首次开仓需要5%价差
            {"times": 2, "spread": "3.0", "multiplier": "1.5"},   # 第2次加仓需要再扩大3%
            {"times": 3, "spread": "3.0", "multiplier": "2.0"}    # 第3次加仓需要再扩大3%
        ],
        "profit_mode": "regression",  # 回归止盈模式
        "profit_ratio": "50.0",  # 价差回归50%时止盈
        "stop_loss_ratio": "20.0",  # 亏损20%时止损
        "pause_after_close": False
    }
    
    response = requests.post(
        f"{BASE_URL}/api/v1/bots",
        headers={"Authorization": f"Bearer {token}"},
        json=bot_config
    )
    
    if response.status_code not in [200, 201]:
        print(f"创建机器人失败: {response.text}")
        return None
    
    bot_data = response.json()
    # 如果dca_config不在响应中，从请求中获取
    if 'dca_config' not in bot_data:
        bot_data['dca_config'] = bot_config['dca_config']
    return bot_data


def start_bot(bot_id, token):
    """启动机器人"""
    response = requests.post(
        f"{BASE_URL}/api/v1/bots/{bot_id}/start",
        headers={"Authorization": f"Bearer {token}"}
    )
    return response.json()


def stop_bot(bot_id, token):
    """停止机器人"""
    response = requests.post(
        f"{BASE_URL}/api/v1/bots/{bot_id}/stop",
        headers={"Authorization": f"Bearer {token}"}
    )
    return response.json()


def get_bot_status(bot_id, token):
    """获取机器人状态"""
    response = requests.get(
        f"{BASE_URL}/api/v1/bots/{bot_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    return response.json()


def get_bot_orders(bot_id, token):
    """获取机器人订单"""
    response = requests.get(
        f"{BASE_URL}/api/v1/bots/{bot_id}/orders",
        headers={"Authorization": f"Bearer {token}"}
    )
    return response.json()


def get_bot_positions(bot_id, token):
    """获取机器人持仓"""
    response = requests.get(
        f"{BASE_URL}/api/v1/bots/{bot_id}/positions",
        headers={"Authorization": f"Bearer {token}"}
    )
    return response.json()


async def monitor_trading_cycle(bot_id, token, max_duration=120):
    """监控完整的交易循环"""
    ws_url = f"{WS_URL}/api/v1/ws/bot/{bot_id}?token={token}"
    
    print(f"\n[WebSocket] 连接 {ws_url}")
    
    stats = {
        "spread_updates": 0,
        "order_updates": 0,
        "position_updates": 0,
        "status_updates": 0,
        "orders_created": [],
        "positions_opened": [],
        "max_spread": 0,
        "min_spread": 999,
        "cycle_completed": False
    }
    
    try:
        # websockets库不支持extra_headers参数，直接连接即可
        async with websockets.connect(ws_url) as websocket:
            print("[WebSocket] 连接成功，监听交易循环...")
            start_time = asyncio.get_event_loop().time()
            
            while True:
                elapsed = asyncio.get_event_loop().time() - start_time
                if elapsed >= max_duration:
                    print(f"\n[WebSocket] 达到最大监听时间 {max_duration}秒")
                    break
                
                try:
                    remaining = max_duration - elapsed
                    message = await asyncio.wait_for(websocket.recv(), timeout=min(5, remaining))
                    data = json.loads(message)
                    
                    msg_type = data.get('type')
                    
                    if msg_type == 'spread_update':
                        stats["spread_updates"] += 1
                        spread_data = data.get('data', {})
                        spread = spread_data.get('spread_percentage', 0)
                        stats["max_spread"] = max(stats["max_spread"], spread)
                        stats["min_spread"] = min(stats["min_spread"], spread)
                        
                        if stats["spread_updates"] % 5 == 0:  # 每5次更新打印一次
                            print(f"[价差] {spread:.2f}% (范围: {stats['min_spread']:.2f}% - {stats['max_spread']:.2f}%)")
                    
                    elif msg_type == 'order_update':
                        stats["order_updates"] += 1
                        order_data = data.get('data', {})
                        print(f"\n[订单] {order_data.get('symbol')} {order_data.get('side')} "
                              f"数量:{order_data.get('amount')} 状态:{order_data.get('status')} "
                              f"DCA级别:{order_data.get('dca_level')}")
                        stats["orders_created"].append(order_data)
                    
                    elif msg_type == 'position_update':
                        stats["position_updates"] += 1
                        pos_data = data.get('data', {})
                        print(f"\n[持仓] {pos_data.get('symbol')} {pos_data.get('side')} "
                              f"数量:{pos_data.get('amount')} "
                              f"入场价:${pos_data.get('entry_price')} "
                              f"当前价:${pos_data.get('current_price')} "
                              f"盈亏:${pos_data.get('unrealized_pnl')} "
                              f"开放:{pos_data.get('is_open')}")
                        stats["positions_opened"].append(pos_data)
                        
                        # 如果持仓关闭，说明完成了一个循环
                        if not pos_data.get('is_open'):
                            stats["cycle_completed"] = True
                    
                    elif msg_type == 'status_update':
                        stats["status_updates"] += 1
                        status_data = data.get('data', {})
                        print(f"\n[状态] 状态:{status_data.get('status')} "
                              f"循环:{status_data.get('current_cycle')} "
                              f"DCA:{status_data.get('current_dca_count')} "
                              f"总交易:{status_data.get('total_trades')}")
                        
                        # 如果循环增加且DCA重置为0，说明完成了平仓
                        if status_data.get('current_dca_count') == 0 and stats["orders_created"]:
                            stats["cycle_completed"] = True
                    
                    # 如果完成了完整循环，等待3秒后退出
                    if stats["cycle_completed"]:
                        print("\n[SUCCESS] 检测到完整交易循环完成！等待3秒后结束监听...")
                        await asyncio.sleep(3)
                        break
                        
                except asyncio.TimeoutError:
                    continue
                except Exception as e:
                    print(f"[WebSocket] 消息处理错误: {e}")
                    continue
    
    except Exception as e:
        print(f"[WebSocket] 连接错误: {e}")
    
    return stats


async def main():
    """主测试流程"""
    print("=" * 80)
    print("完整交易循环测试")
    print("=" * 80)
    
    # 1. 登录
    print("\n[1] 登录系统...")
    token = login()
    print("[OK] 登录成功")
    
    # 2. 创建测试机器人
    print("\n[2] 创建测试机器人...")
    bot = create_test_bot(token)
    if not bot:
        print("[FAIL] 创建机器人失败")
        return
    
    bot_id = bot['id']
    print(f"[OK] 机器人创建成功 (ID: {bot_id})")
    print(f"   名称: {bot['bot_name']}")
    print(f"   DCA配置: {bot['dca_config']}")
    
    # 3. 启动机器人
    print("\n[3] 启动机器人...")
    start_result = start_bot(bot_id, token)
    print(f"[OK] 机器人已启动，状态: {start_result.get('status')}")
    
    # 4. 等待机器人启动完成
    print("\n[4] 等待机器人完全启动（3秒）...")
    await asyncio.sleep(3)
    
    # 5. 监听交易循环（最多120秒）
    print("\n[5] 监听交易循环（最多120秒）...")
    print("   等待价差达到5%以触发首次开仓...")
    stats = await monitor_trading_cycle(bot_id, token, max_duration=120)
    
    # 6. 获取最终状态
    print("\n[6] 获取最终状态...")
    final_status = get_bot_status(bot_id, token)
    orders = get_bot_orders(bot_id, token)
    positions = get_bot_positions(bot_id, token)
    
    print(f"\n机器人状态:")
    print(f"  当前状态: {final_status.get('status')}")
    print(f"  当前循环: {final_status.get('current_cycle')}")
    print(f"  DCA次数: {final_status.get('current_dca_count')}")
    print(f"  总交易: {final_status.get('total_trades')}")
    print(f"  总收益: ${final_status.get('total_profit')}")
    
    # 处理订单和持仓响应（可能是列表或分页对象）
    if isinstance(orders, dict) and 'items' in orders:
        orders_total = orders.get('total', len(orders['items']))
    elif isinstance(orders, list):
        orders_total = len(orders)
    else:
        orders_total = orders.get('total', 0) if isinstance(orders, dict) else 0
    
    if isinstance(positions, dict) and 'items' in positions:
        positions_total = positions.get('total', len(positions['items']))
    elif isinstance(positions, list):
        positions_total = len(positions)
    else:
        positions_total = positions.get('total', 0) if isinstance(positions, dict) else 0
    
    print(f"\n订单统计:")
    print(f"  总订单数: {orders_total}")
    
    print(f"\n持仓统计:")
    print(f"  总持仓数: {positions_total}")
    
    # 6. 显示测试统计
    print("\n" + "=" * 80)
    print("测试统计")
    print("=" * 80)
    print(f"价差更新次数: {stats['spread_updates']}")
    print(f"价差范围: {stats['min_spread']:.2f}% - {stats['max_spread']:.2f}%")
    print(f"订单更新次数: {stats['order_updates']}")
    print(f"持仓更新次数: {stats['position_updates']}")
    print(f"状态更新次数: {stats['status_updates']}")
    print(f"完成完整循环: {'[YES]' if stats['cycle_completed'] else '[NO]'}")
    
    # 7. 停止机器人
    print("\n[6] 停止机器人...")
    stop_bot(bot_id, token)
    print("[OK] 机器人已停止")
    
    print("\n" + "=" * 80)
    if stats['cycle_completed']:
        print("[PASS] 测试通过：完整交易循环已验证")
    elif stats['order_updates'] > 0:
        print("[WARN] 部分通过：有交易活动但未完成完整循环")
    else:
        print("[FAIL] 测试未通过：没有触发任何交易")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())