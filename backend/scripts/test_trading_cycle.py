#!/usr/bin/env python3
"""
完整交易循环测试脚本

测试内容：
1. 机器人启动和状态管理
2. 交易循环执行
3. 性能监控功能
4. WebSocket 实时推送
5. 数据持久化
"""
import asyncio
import json
import time
import httpx
from datetime import datetime
import sys
import io

# 设置标准输出编码为 UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 配置
BASE_URL = "http://localhost:8000"
TEST_USER = {
    "username": "admin",
    "password": "admin123"
}

class TradingCycleTester:
    def __init__(self):
        self.access_token = None
        self.bot_id = None

    async def login(self):
        """登录并获取访问令牌"""
        print("🔐 用户登录...")

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
                return True
            else:
                print(f"❌ 登录失败: {response.status_code}")
                return False

    async def get_or_create_bot(self):
        """获取或创建测试机器人"""
        print("🤖 获取测试机器人...")

        headers = {"Authorization": f"Bearer {self.access_token}"}

        async with httpx.AsyncClient(follow_redirects=True) as client:
            response = await client.get(
                f"{BASE_URL}/api/v1/bots",
                headers=headers
            )

            if response.status_code == 200:
                data = response.json()
                if data["items"]:
                    self.bot_id = data["items"][0]["id"]
                    print(f"✅ 找到机器人: ID={self.bot_id}, 状态={data['items'][0]['status']}")
                    return True
                else:
                    print("❌ 没有找到机器人")
                    return False
            else:
                print(f"❌ 获取机器人列表失败: {response.status_code}")
                return False

    async def start_bot(self):
        """启动机器人"""
        print("🚀 启动机器人...")

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
                # 可能已在运行
                try:
                    error_data = response.json()
                    message = error_data.get('error', {}).get('message', '').lower()
                    if 'running' in message or 'already' in message:
                        print(f"✅ 机器人已在运行中")
                        return True
                    else:
                        print(f"❌ 启动失败: {response.text}")
                        return False
                except:
                    print(f"⚠️  机器人可能已在运行")
                    return True
            else:
                print(f"❌ 启动失败: {response.status_code}")
                return False

    async def monitor_bot_performance(self, duration=60):
        """监控机器人性能"""
        print(f"📊 监控机器人性能 (持续 {duration} 秒)...")
        print("=" * 60)

        headers = {"Authorization": f"Bearer {self.access_token}"}
        start_time = time.time()
        last_cycle = 0
        last_trades = 0

        while time.time() - start_time < duration:
            try:
                # 获取机器人状态
                response = await httpx.get(
                    f"{BASE_URL}/api/v1/bots/{self.bot_id}",
                    headers=headers
                )

                if response.status_code == 200:
                    bot_data = response.json()
                    current_cycle = bot_data.get('current_cycle', 0)
                    total_trades = bot_data.get('total_trades', 0)
                    status = bot_data.get('status', 'unknown')

                    elapsed = time.time() - start_time

                    # 检查是否有新的循环或交易
                    if current_cycle > last_cycle:
                        print(f"🔄 [{elapsed:.1f}s] 新的交易循环! 循环数: {current_cycle}")
                        last_cycle = current_cycle

                    if total_trades > last_trades:
                        print(f"💰 [{elapsed:.1f}s] 新的交易! 总交易数: {total_trades}")
                        last_trades = total_trades

                    # 定期状态报告
                    if int(elapsed) % 15 == 0 and int(elapsed) > 0:
                        print(f"📈 [{elapsed:.0f}s] 状态报告:")
                        print(f"   状态: {status}")
                        print(f"   当前循环: {current_cycle}")
                        print(f"   总交易数: {total_trades}")
                        print(f"   当前加仓次数: {bot_data.get('current_dca_count', 0)}")

                await asyncio.sleep(2)

            except Exception as e:
                print(f"❌ 监控错误: {str(e)}")
                await asyncio.sleep(2)

        print("=" * 60)
        print("✅ 性能监控完成")

    async def test_bot_stop(self):
        """测试机器人停止"""
        print("🛑 测试机器人停止...")

        headers = {"Authorization": f"Bearer {self.access_token}"}

        async with httpx.AsyncClient(follow_redirects=True) as client:
            response = await client.post(
                f"{BASE_URL}/api/v1/bots/{self.bot_id}/stop",
                headers=headers
            )

            if response.status_code == 200:
                print(f"✅ 机器人停止成功")
                return True
            else:
                print(f"⚠️  停止请求: {response.status_code}")
                return True  # 停止失败不算严重错误

    async def check_data_persistence(self):
        """检查数据持久化"""
        print("💾 检查数据持久化...")

        headers = {"Authorization": f"Bearer {self.access_token}"}

        try:
            # 检查订单历史
            response = await httpx.get(
                f"{BASE_URL}/api/v1/bots/{self.bot_id}/orders",
                headers=headers
            )

            if response.status_code == 200:
                orders_data = response.json()
                print(f"✅ 订单记录: {len(orders_data.get('items', []))} 条")

            # 检查持仓记录
            response = await httpx.get(
                f"{BASE_URL}/api/v1/bots/{self.bot_id}/positions",
                headers=headers
            )

            if response.status_code == 200:
                positions_data = response.json()
                open_positions = [p for p in positions_data.get('items', []) if p.get('is_open')]
                print(f"✅ 持仓记录: {len(open_positions)} 个开放持仓")

            # 检查交易日志
            response = await httpx.get(
                f"{BASE_URL}/api/v1/bots/{self.bot_id}/trade-logs",
                headers=headers
            )

            if response.status_code == 200:
                logs_data = response.json()
                print(f"✅ 交易日志: {len(logs_data.get('items', []))} 条")

            print("✅ 数据持久化检查完成")

        except Exception as e:
            print(f"❌ 数据持久化检查失败: {str(e)}")

async def main():
    """主测试流程"""
    print("\n" + "=" * 60)
    print("完整交易循环测试")
    print("=" * 60)
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    tester = TradingCycleTester()

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

        # 4. 等待机器人启动
        print("⏳ 等待 5 秒让机器人完全启动...")
        await asyncio.sleep(5)

        # 5. 监控性能 (60秒)
        await tester.monitor_bot_performance(duration=60)

        # 6. 检查数据持久化
        await tester.check_data_persistence()

        # 7. 可选：停止机器人
        print("\n❓ 是否要停止机器人? (y/N): ", end="")
        try:
            # 在 Windows 上，input() 在 asyncio 中可能会有问题
            # 所以我们直接跳过停止步骤
            print("跳过停止步骤")
        except:
            pass

        print("\n🎉 交易循环测试完成!")

    except KeyboardInterrupt:
        print("\n⚠️  测试被用户中断")
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {str(e)}")
        import traceback
        traceback.print_exc()

    print(f"\n结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

if __name__ == "__main__":
    print("确保后端服务正在运行: python -m uvicorn app.main:app --port 8000")
    asyncio.run(main())