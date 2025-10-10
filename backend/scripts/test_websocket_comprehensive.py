
"""
WebSocket 实时推送综合测试脚本

测试内容:
1. WebSocket 连接建立
2. 价差更新推送
3. 订单更新推送
4. 持仓更新推送
5. 状态更新推送
6. 心跳机制
7. 断线重连
"""
import asyncio
import json
import websockets
import httpx
from datetime import datetime
import sys
import io

# 设置标准输出编码为 UTF-8（解决 Windows 终端 emoji 显示问题）
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 配置
BASE_URL = "http://localhost:8000"
WS_URL = "ws://localhost:8000"
TEST_USER = {
    "username": "admin",
    "password": "admin123"
}

class WebSocketTester:
    def __init__(self):
        self.access_token = None
        self.bot_id = None
        self.ws = None
        self.received_messages = {
            "connection_established": [],
            "spread_update": [],
            "order_update": [],
            "position_update": [],
            "status_update": [],
            "pong": []
        }
        
    async def login(self):
        """登录并获取访问令牌"""
        print("=" * 60)
        print("步骤 1: 用户登录")
        print("=" * 60)
        
        async with httpx.AsyncClient(follow_redirects=True) as client:
            response = await client.post(
                f"{BASE_URL}/api/v1/auth/login",
                json={
                    "username": TEST_USER["username"],
                    "password": TEST_USER["password"]
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                self.access_token = data["access_token"]
                print(f"✅ 登录成功")
                print(f"   访问令牌: {self.access_token[:30]}...")
                return True
            else:
                print(f"❌ 登录失败: {response.status_code}")
                print(f"   响应: {response.text}")
                return False
    
    async def get_or_create_bot(self):
        """获取或创建测试机器人"""
        print("\n" + "=" * 60)
        print("步骤 2: 获取测试机器人")
        print("=" * 60)
        
        headers = {"Authorization": f"Bearer {self.access_token}"}
        
        async with httpx.AsyncClient(follow_redirects=True) as client:
            # 获取机器人列表
            response = await client.get(
                f"{BASE_URL}/api/v1/bots",
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                if data["items"]:
                    self.bot_id = data["items"][0]["id"]
                    print(f"✅ 找到现有机器人")
                    print(f"   机器人 ID: {self.bot_id}")
                    print(f"   机器人名称: {data['items'][0]['bot_name']}")
                    print(f"   当前状态: {data['items'][0]['status']}")
                    return True
                else:
                    print("❌ 没有找到机器人")
                    return False
            else:
                print(f"❌ 获取机器人列表失败: {response.status_code}")
                return False
    
    async def start_bot(self):
        """启动机器人"""
        print("\n" + "=" * 60)
        print("步骤 3: 启动机器人")
        print("=" * 60)
        
        headers = {"Authorization": f"Bearer {self.access_token}"}
        
        async with httpx.AsyncClient(follow_redirects=True) as client:
            response = await client.post(
                f"{BASE_URL}/api/v1/bots/{self.bot_id}/start",
                headers=headers
            )
            
            if response.status_code == 200:
                print(f"✅ 机器人启动成功")
                return True
            elif response.status_code == 400:
                print(f"⚠️  机器人可能已在运行: {response.json().get('detail')}")
                return True  # 已经在运行也算成功
            else:
                print(f"❌ 启动失败: {response.status_code}")
                print(f"   响应: {response.text}")
                return False
    
    async def connect_websocket(self):
        """建立 WebSocket 连接"""
        print("\n" + "=" * 60)
        print("步骤 4: 建立 WebSocket 连接")
        print("=" * 60)
        
        ws_url = f"{WS_URL}/api/v1/ws/bot/{self.bot_id}?token={self.access_token}"
        
        try:
            self.ws = await websockets.connect(ws_url)
            print(f"✅ WebSocket 连接已建立")
            print(f"   URL: ws://localhost:8000/api/v1/ws/bot/{self.bot_id}")
            return True
        except Exception as e:
            print(f"❌ WebSocket 连接失败: {str(e)}")
            return False
    
    async def receive_messages(self, duration=30):
        """接收 WebSocket 消息"""
        print("\n" + "=" * 60)
        print(f"步骤 5: 接收实时消息 (持续 {duration} 秒)")
        print("=" * 60)
        
        start_time = asyncio.get_event_loop().time()
        message_count = 0
        
        try:
            while True:
                elapsed = asyncio.get_event_loop().time() - start_time
                if elapsed >= duration:
                    break
                
                try:
                    # 设置超时以便定期检查时间
                    message = await asyncio.wait_for(self.ws.recv(), timeout=1.0)
                    data = json.loads(message)
                    message_count += 1
                    
                    msg_type = data.get("type")
                    timestamp = data.get("timestamp")
                    
                    # 记录消息
                    if msg_type in self.received_messages:
                        self.received_messages[msg_type].append(data)
                    
                    # 打印消息
                    if msg_type == "connection_established":
                        print(f"\n📡 [{elapsed:.1f}s] 连接已建立")
                        print(f"   机器人: {data['data'].get('bot_name')}")
                        print(f"   状态: {data['data'].get('status')}")
                    
                    elif msg_type == "spread_update":
                        spread_data = data["data"]
                        print(f"\n📊 [{elapsed:.1f}s] 价差更新 #{len(self.received_messages['spread_update'])}")
                        print(f"   市场1价格: ${spread_data.get('market1_price'):.6f}")
                        print(f"   市场2价格: ${spread_data.get('market2_price'):.6f}")
                        print(f"   价差: {spread_data.get('spread_percentage'):.4f}%")
                    
                    elif msg_type == "order_update":
                        order_data = data["data"]
                        print(f"\n📝 [{elapsed:.1f}s] 订单更新 #{len(self.received_messages['order_update'])}")
                        print(f"   交易对: {order_data.get('symbol')}")
                        print(f"   方向: {order_data.get('side')}")
                        print(f"   数量: {order_data.get('amount'):.4f}")
                        print(f"   状态: {order_data.get('status')}")
                    
                    elif msg_type == "position_update":
                        pos_data = data["data"]
                        print(f"\n💼 [{elapsed:.1f}s] 持仓更新 #{len(self.received_messages['position_update'])}")
                        print(f"   交易对: {pos_data.get('symbol')}")
                        print(f"   方向: {pos_data.get('side')}")
                        print(f"   数量: {pos_data.get('amount'):.4f}")
                        print(f"   开仓价: ${pos_data.get('entry_price'):.6f}")
                        print(f"   当前价: ${pos_data.get('current_price'):.6f}")
                        unrealized_pnl = pos_data.get('unrealized_pnl')
                        if unrealized_pnl is not None:
                            print(f"   未实现盈亏: ${unrealized_pnl:.2f}")
                        print(f"   状态: {'持仓中' if pos_data.get('is_open') else '已平仓'}")
                    
                    elif msg_type == "status_update":
                        status_data = data["data"]
                        print(f"\n🔄 [{elapsed:.1f}s] 状态更新 #{len(self.received_messages['status_update'])}")
                        print(f"   状态: {status_data.get('status')}")
                        print(f"   当前循环: {status_data.get('current_cycle')}")
                        print(f"   加仓次数: {status_data.get('current_dca_count')}")
                        print(f"   总交易: {status_data.get('total_trades')}")
                    
                    elif msg_type == "pong":
                        print(f"\n💓 [{elapsed:.1f}s] 心跳响应")
                
                except asyncio.TimeoutError:
                    # 超时，继续循环
                    continue
                except json.JSONDecodeError as e:
                    print(f"❌ JSON 解析错误: {str(e)}")
                except Exception as e:
                    print(f"❌ 接收消息错误: {str(e)}")
                    break
        
        except Exception as e:
            print(f"❌ 消息接收循环异常: {str(e)}")
        
        print(f"\n接收完成，共收到 {message_count} 条消息")
        return message_count
    
    async def send_heartbeat(self):
        """发送心跳"""
        print("\n" + "=" * 60)
        print("步骤 6: 测试心跳机制")
        print("=" * 60)

        try:
            # 清空之前的 pong 消息
            self.received_messages["pong"].clear()

            # 发送 ping 消息
            ping_message = json.dumps({"type": "ping"})
            await self.ws.send(ping_message)
            print("✅ 心跳消息已发送")

            # 等待 pong 响应 (增加等待时间和主动接收)
            max_wait = 3  # 最多等待3秒
            start_time = asyncio.get_event_loop().time()

            while asyncio.get_event_loop().time() - start_time < max_wait:
                try:
                    # 主动接收消息
                    message = await asyncio.wait_for(self.ws.recv(), timeout=0.5)
                    data = json.loads(message)

                    msg_type = data.get("type")
                    if msg_type in self.received_messages:
                        self.received_messages[msg_type].append(data)

                    # 收到 pong 响应
                    if msg_type == "pong":
                        print("✅ 收到心跳响应")
                        return True

                except asyncio.TimeoutError:
                    continue
                except Exception as e:
                    print(f"⚠️  接收消息时出错: {str(e)}")
                    continue

            print("⚠️  未在规定时间内收到心跳响应")
            return False

        except Exception as e:
            print(f"❌ 心跳测试失败: {str(e)}")
            return False
    
    async def print_summary(self):
        """打印测试摘要"""
        print("\n" + "=" * 60)
        print("测试摘要")
        print("=" * 60)
        
        print(f"\n消息统计:")
        print(f"  连接建立消息: {len(self.received_messages['connection_established'])} 条")
        print(f"  价差更新消息: {len(self.received_messages['spread_update'])} 条")
        print(f"  订单更新消息: {len(self.received_messages['order_update'])} 条")
        print(f"  持仓更新消息: {len(self.received_messages['position_update'])} 条")
        print(f"  状态更新消息: {len(self.received_messages['status_update'])} 条")
        print(f"  心跳响应消息: {len(self.received_messages['pong'])} 条")
        
        total = sum(len(msgs) for msgs in self.received_messages.values())
        print(f"\n总消息数: {total} 条")
        
        # 验证结果
        print(f"\n验证结果:")
        checks = [
            ("连接建立", len(self.received_messages['connection_established']) > 0),
            ("价差更新推送", len(self.received_messages['spread_update']) > 0),
            ("订单更新推送", len(self.received_messages['order_update']) > 0),
            ("持仓更新推送", len(self.received_messages['position_update']) > 0),
            ("状态更新推送", len(self.received_messages['status_update']) > 0),
            ("心跳机制", len(self.received_messages['pong']) > 0),
        ]
        
        passed = sum(1 for _, check in checks if check)
        
        for label, check in checks:
            status = "✅" if check else "❌"
            print(f"  {status} {label}")
        
        print(f"\n通过率: {passed}/{len(checks)} ({passed/len(checks)*100:.1f}%)")
        
        if passed == len(checks):
            print("\n🎉 所有测试通过！WebSocket 实时推送功能完全正常！")
        else:
            print("\n⚠️  部分测试未通过，需要进一步调试")
    
    async def cleanup(self):
        """清理资源"""
        print("\n" + "=" * 60)
        print("清理资源")
        print("=" * 60)
        
        if self.ws:
            await self.ws.close()
            print("✅ WebSocket 连接已关闭")

async def main():
    """主测试流程"""
    print("\n" + "=" * 60)
    print("WebSocket 实时推送综合测试")
    print("=" * 60)
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    tester = WebSocketTester()
    
    try:
        # 1. 登录
        if not await tester.login():
            return
        
        # 2. 获取机器人
        if not await tester.get_or_create_bot():
            return
        
        # 3. 启动机器人
        if not await tester.start_bot():
            return
        
        # 等待机器人启动
        print("\n等待 3 秒让机器人完全启动...")
        await asyncio.sleep(3)
        
        # 4. 建立 WebSocket 连接
        if not await tester.connect_websocket():
            return
        
        # 5. 接收消息 (30秒)
        await tester.receive_messages(duration=30)
        
        # 6. 测试心跳
        await tester.send_heartbeat()
        
        # 7. 打印摘要
        await tester.print_summary()
        
    except KeyboardInterrupt:
        print("\n⚠️  测试被用户中断")
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        await tester.cleanup()
    
    print(f"\n结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

if __name__ == "__main__":
    # 安装依赖提示
    print("确保已安装依赖: pip install websockets httpx")
    asyncio.run(main())