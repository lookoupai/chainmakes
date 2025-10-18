"""
OKX 连接诊断脚本
用于诊断 OKX API 连接问题
"""
import asyncio
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from app.exchanges.okx_exchange import OKXExchange
from app.core.config import settings
from app.utils.logger import setup_logger

logger = setup_logger('okx_diagnose')


async def diagnose_connection():
    """诊断 OKX 连接"""
    
    print("=" * 60)
    print("OKX 连接诊断")
    print("=" * 60)
    
    # 1. 检查配置
    print("\n1️⃣ 检查配置:")
    print(f"   - API Key: {settings.OKX_API_KEY[:10]}..." if settings.OKX_API_KEY else "   - API Key: ❌ 未设置")
    print(f"   - API Secret: {'✅ 已设置' if settings.OKX_API_SECRET else '❌ 未设置'}")
    print(f"   - Passphrase: {'✅ 已设置' if settings.OKX_PASSPHRASE else '❌ 未设置'}")
    print(f"   - 测试网: {settings.IS_TESTNET}")
    print(f"   - 代理: {settings.PROXY or '❌ 未设置'}")
    
    if not all([settings.OKX_API_KEY, settings.OKX_API_SECRET, settings.OKX_PASSPHRASE]):
        print("\n❌ 错误: OKX API 配置不完整，请检查 .env 文件")
        return
    
    # 2. 测试网络连接
    print("\n2️⃣ 测试基础网络连接:")
    try:
        import aiohttp
        async with aiohttp.ClientSession() as session:
            test_url = "https://www.okx.com/api/v5/public/time"
            print(f"   正在请求: {test_url}")
            
            # 如果有代理，使用代理
            proxy = settings.PROXY if hasattr(settings, 'PROXY') else None
            async with session.get(test_url, proxy=proxy, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    print(f"   ✅ 网络连接正常")
                    print(f"   服务器时间: {data.get('data', [{}])[0].get('ts', 'N/A')}")
                else:
                    print(f"   ⚠️ 请求失败: HTTP {resp.status}")
    except Exception as e:
        print(f"   ❌ 网络连接失败: {str(e)}")
        print(f"   提示: 如果在中国大陆，可能需要配置代理")
        return
    
    # 3. 测试 OKX Exchange 初始化
    print("\n3️⃣ 测试 OKX Exchange 初始化:")
    try:
        exchange = OKXExchange(
            api_key=settings.OKX_API_KEY,
            api_secret=settings.OKX_API_SECRET,
            passphrase=settings.OKX_PASSPHRASE,
            is_testnet=settings.IS_TESTNET,
            proxy=settings.PROXY if hasattr(settings, 'PROXY') else None
        )
        print("   ✅ Exchange 对象创建成功")
    except Exception as e:
        print(f"   ❌ 创建失败: {str(e)}")
        return
    
    # 4. 测试获取账户余额
    print("\n4️⃣ 测试获取账户余额:")
    try:
        balance = await exchange.get_balance()
        print("   ✅ 余额获取成功")
        print(f"   USDT 可用: {balance['free'].get('USDT', 0)}")
        print(f"   USDT 总计: {balance['total'].get('USDT', 0)}")
    except Exception as e:
        print(f"   ❌ 获取余额失败: {str(e)}")
        print(f"   错误类型: {type(e).__name__}")
        
        # 检查常见错误
        error_msg = str(e).lower()
        if '401' in error_msg or 'unauthorized' in error_msg:
            print("   💡 提示: API Key 认证失败，请检查:")
            print("      - API Key、Secret、Passphrase 是否正确")
            print("      - 是否选择了正确的环境（模拟盘/实盘）")
            print("      - API Key 权限是否足够（需要交易权限）")
        elif 'timeout' in error_msg or 'connect' in error_msg:
            print("   💡 提示: 网络超时，请检查:")
            print("      - 代理配置是否正确")
            print("      - 防火墙是否阻止连接")
        return
    
    # 5. 测试获取持仓
    print("\n5️⃣ 测试获取所有持仓:")
    try:
        positions = await exchange.get_all_positions()
        print(f"   ✅ 持仓获取成功")
        print(f"   当前持仓数量: {len(positions)}")
        for pos in positions[:3]:  # 只显示前3个
            print(f"      - {pos['symbol']}: {pos['side']} {pos['amount']}")
    except Exception as e:
        print(f"   ❌ 获取持仓失败: {str(e)}")
        print(f"   错误类型: {type(e).__name__}")
        return
    
    # 6. 测试获取行情
    print("\n6️⃣ 测试获取行情数据:")
    test_symbols = ["BTC-USDT-SWAP", "ETH-USDT-SWAP"]
    for symbol in test_symbols:
        try:
            ticker = await exchange.get_ticker(symbol)
            print(f"   ✅ {symbol}: {ticker['last_price']} USDT")
        except Exception as e:
            print(f"   ❌ {symbol}: 获取失败 - {str(e)}")
    
    print("\n" + "=" * 60)
    print("✅ 诊断完成")
    print("=" * 60)
    
    # 关闭 exchange
    await exchange.exchange.close()


if __name__ == "__main__":
    try:
        asyncio.run(diagnose_connection())
    except KeyboardInterrupt:
        print("\n\n⚠️ 用户中断")
    except Exception as e:
        print(f"\n\n❌ 诊断过程出错: {str(e)}")
        import traceback
        traceback.print_exc()
