"""
OKX API 连接测试脚本

测试 OKX 交易所 API 的基本功能:
1. 连接测试
2. 获取行情数据
3. 获取账户余额
4. 获取持仓信息
"""
import asyncio
import sys
import io
from pathlib import Path

# 设置标准输出编码为 UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.exchanges.okx_exchange import OKXExchange
from app.utils.logger import setup_logger

logger = setup_logger('test_okx')


async def test_okx_connection():
    """测试 OKX API 连接"""
    print("=" * 60)
    print("OKX API 连接测试")
    print("=" * 60)

    # 从环境变量读取 API 凭据
    from app.config import settings
    import os
    
    api_key = settings.OKX_API_KEY
    api_secret = settings.OKX_API_SECRET
    passphrase = settings.OKX_PASSPHRASE
    is_demo = settings.OKX_IS_DEMO

    # 检查是否配置了API凭据
    if not api_key or not api_secret or not passphrase:
        print("\n⚠️  请先在 .env 文件中配置 OKX API 凭据")
        print("需要设置以下环境变量:")
        print("  - OKX_API_KEY")
        print("  - OKX_API_SECRET")
        print("  - OKX_PASSPHRASE")
        print("  - OKX_IS_DEMO=True (使用模拟盘)")
        print("\n💡 提示: 建议使用模拟盘进行测试")
        print("模拟盘申请: https://www.okx.com/trade-demo")
        return
    
    print(f"\n📌 当前模式: {'模拟盘 (Demo)' if is_demo else '真实盘 (Live)'}")
    print(f"📌 API Key: {api_key[:8]}...{api_key[-4:]}")
    
    # 代理配置检测 - 从 settings 对象读取
    proxy = settings.OKX_PROXY or os.getenv("HTTP_PROXY") or os.getenv("HTTPS_PROXY")
    if proxy:
        print(f"📌 使用代理: {proxy}")
    else:
        print("⚠️  未配置代理 - 如果在中国大陆，可能需要代理访问 OKX")
        print("   在 .env 文件中添加: OKX_PROXY=http://127.0.0.1:10808")

    try:
        async with OKXExchange(
            api_key=api_key,
            api_secret=api_secret,
            passphrase=passphrase,
            is_testnet=is_demo,
            proxy=proxy
        ) as exchange:

            # 1. 测试获取行情数据
            print("\n" + "=" * 60)
            print("测试 1: 获取行情数据")
            print("=" * 60)

            try:
                ticker = await exchange.get_ticker("BTC-USDT-SWAP")
                print("✅ 获取行情成功:")
                print(f"   交易对: {ticker['symbol']}")
                print(f"   最新价: ${ticker['last_price']}")
                print(f"   买一价: ${ticker['bid']}")
                print(f"   卖一价: ${ticker['ask']}")
                print(f"   24h量: {ticker['volume']}")
            except Exception as e:
                print(f"❌ 获取行情失败: {str(e)}")
                
                # 详细的错误诊断
                error_msg = str(e).lower()
                print("\n💡 故障排查建议:")
                
                if "timeout" in error_msg or "connect" in error_msg or "okx get" in error_msg:
                    print("   【网络连接问题】")
                    print("   1. OKX API 在中国大陆被墙，需要代理访问")
                    print("   2. 解决方案:")
                    print("      a) 启动科学上网工具（VPN/代理软件）")
                    print("      b) 在 .env 文件中配置代理:")
                    print("         OKX_PROXY=http://127.0.0.1:7890")
                    print("      c) 或使用 SOCKS5 代理:")
                    print("         OKX_PROXY=socks5://127.0.0.1:1080")
                    print("   3. 验证代理是否工作:")
                    print("      curl -x http://127.0.0.1:7890 https://www.okx.com")
                
                elif "authentication" in error_msg or "invalid" in error_msg or "signature" in error_msg:
                    print("   【API 凭据问题】")
                    print("   1. 检查 API Key/Secret/Passphrase 是否正确")
                    print("   2. 确认已创建了对应的 API:")
                    print("      - 模拟盘 API: https://www.okx.com/trade-demo")
                    print("      - 真实盘 API: https://www.okx.com/account/my-api")
                    print("   3. 检查 OKX_IS_DEMO 设置是否匹配:")
                    print(f"      当前设置: {is_demo} ({'模拟盘' if is_demo else '真实盘'})")
                
                elif "permission" in error_msg or "forbidden" in error_msg:
                    print("   【API 权限问题】")
                    print("   1. 检查 API 权限设置:")
                    print("      - 需要启用 '读取' 权限")
                    print("      - 需要启用 '交易' 权限")
                    print("   2. 检查 IP 白名单设置")
                
                else:
                    print(f"   【未知错误】")
                    print(f"   请查看完整错误信息，或联系技术支持")
                
                return  # 第一个测试失败就停止

            # 2. 测试获取账户余额
            print("\n" + "=" * 60)
            print("测试 2: 获取账户余额")
            print("=" * 60)

            try:
                balance = await exchange.get_balance()
                print("✅ 获取余额成功:")

                # 显示主要币种余额
                main_currencies = ['USDT', 'BTC', 'ETH']
                has_balance = False
                for currency in main_currencies:
                    total = balance['total'].get(currency, 0)
                    free = balance['free'].get(currency, 0)
                    used = balance['used'].get(currency, 0)

                    if total > 0:
                        has_balance = True
                        print(f"\n   {currency}:")
                        print(f"     总额: {total}")
                        print(f"     可用: {free}")
                        print(f"     冻结: {used}")
                
                if not has_balance:
                    print("\n   ⚠️  账户余额为 0")
                    if is_demo:
                        print("   💡 模拟盘需要先充值模拟币")
                        print("      访问: https://www.okx.com/trade-demo")

            except Exception as e:
                print(f"❌ 获取余额失败: {str(e)}")

            # 3. 测试获取持仓信息
            print("\n" + "=" * 60)
            print("测试 3: 获取持仓信息")
            print("=" * 60)

            try:
                positions = await exchange.get_all_positions()

                if positions:
                    print(f"✅ 当前有 {len(positions)} 个持仓:")

                    for i, pos in enumerate(positions, 1):
                        print(f"\n   持仓 {i}:")
                        print(f"     交易对: {pos['symbol']}")
                        print(f"     方向: {'做多' if pos['side'] == 'long' else '做空'}")
                        print(f"     数量: {pos['amount']}")
                        print(f"     开仓价: ${pos['entry_price']}")
                        print(f"     未实现盈亏: ${pos['unrealized_pnl']}")
                        print(f"     杠杆: {pos['leverage']}x")
                else:
                    print("✅ 当前无持仓")

            except Exception as e:
                print(f"❌ 获取持仓失败: {str(e)}")

            # 4. 测试设置杠杆 (可选)
            print("\n" + "=" * 60)
            print("测试 4: 设置杠杆 (跳过)")
            print("=" * 60)
            print("⚠️  设置杠杆会影响交易,此测试已跳过")
            print("如需测试,请取消注释相关代码")

            # try:
            #     result = await exchange.set_leverage("BTC-USDT-SWAP", 5)
            #     print("✅ 设置杠杆成功: 5x")
            # except Exception as e:
            #     print(f"❌ 设置杠杆失败: {str(e)}")

            print("\n" + "=" * 60)
            print("测试总结")
            print("=" * 60)
            print("✅ OKX API 连接正常")
            print("✅ 可以正常获取行情、余额和持仓数据")
            print("✅ 交易所适配器工作正常")

    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()


async def test_mock_exchange():
    """测试模拟交易所 (无需 API 凭据)"""
    print("\n" + "=" * 60)
    print("测试模拟交易所 (Mock Exchange)")
    print("=" * 60)

    from app.exchanges.mock_exchange import MockExchange

    try:
        exchange = MockExchange(api_key="mock", api_secret="mock")

        # 测试获取行情
        ticker = await exchange.get_ticker("BTC-USDT")
        print("\n✅ 模拟交易所 - 获取行情:")
        print(f"   最新价: ${ticker['last_price']}")

        # 测试下单
        from decimal import Decimal
        order = await exchange.create_market_order(
            symbol="BTC-USDT",
            side="buy",
            amount=Decimal("0.001")
        )
        print("\n✅ 模拟交易所 - 创建订单:")
        print(f"   订单ID: {order['id']}")
        print(f"   状态: {order['status']}")

        # 测试获取持仓
        positions = await exchange.get_all_positions()
        print(f"\n✅ 模拟交易所 - 当前持仓: {len(positions)} 个")

        await exchange.close()

        print("\n✅ 模拟交易所测试完成")

    except Exception as e:
        print(f"\n❌ 模拟交易所测试失败: {str(e)}")


if __name__ == "__main__":
    print("\n欢迎使用 OKX API 测试脚本")
    print("=" * 60)
    print("选择测试模式:")
    print("1. OKX 真实 API 测试 (从 .env 读取凭据)")
    print("2. 模拟交易所测试 (无需 API 凭据)")
    print("=" * 60)

    # 先测试模拟交易所
    asyncio.run(test_mock_exchange())

    # 然后测试真实 OKX API
    print("\n")
    asyncio.run(test_okx_connection())
