"""
测试OKX模拟盘API连接
"""
import asyncio
import ccxt.async_support as ccxt
from dotenv import load_dotenv
import os
import sys

# 设置UTF-8编码输出
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 加载环境变量
load_dotenv()

async def test_okx_connection():
    """测试OKX API连接"""
    
    # 从环境变量读取配置
    api_key = os.getenv('OKX_API_KEY')
    api_secret = os.getenv('OKX_API_SECRET')
    passphrase = os.getenv('OKX_PASSPHRASE')
    is_demo = os.getenv('OKX_IS_DEMO', 'True').lower() == 'true'
    proxy = os.getenv('OKX_PROXY')
    
    print("=" * 60)
    print("OKX API 连接测试")
    print("=" * 60)
    print(f"模拟盘模式: {is_demo}")
    print(f"API Key (前8位): {api_key[:8] if api_key else 'None'}")
    print(f"代理: {proxy if proxy else '未配置'}")
    print("=" * 60)
    
    # 配置交易所
    config = {
        'apiKey': api_key,
        'secret': api_secret,
        'password': passphrase,
        'enableRateLimit': True,
        'options': {
            'defaultType': 'swap',
        }
    }
    
    # 配置代理
    if proxy:
        config['aiohttp_proxy'] = proxy
        config['proxies'] = {
            'http': proxy,
            'https': proxy,
        }
    
    # 设置模拟盘
    if is_demo:
        config['sandbox'] = True
        print("✅ 使用模拟盘环境")
    else:
        print("⚠️ 使用真实盘环境")
    
    exchange = ccxt.okx(config)
    
    try:
        print("\n1. 测试获取账户余额...")
        balance = await exchange.fetch_balance()
        print(f"✅ 余额获取成功")
        print(f"   USDT余额: {balance.get('USDT', {}).get('free', 0)}")
        
        print("\n2. 测试获取行情数据...")
        ticker = await exchange.fetch_ticker('BTC/USDT:USDT')
        print(f"✅ 行情获取成功")
        print(f"   BTC价格: {ticker['last']}")
        
        print("\n3. 测试获取持仓...")
        positions = await exchange.fetch_positions()
        print(f"✅ 持仓查询成功")
        print(f"   持仓数量: {len([p for p in positions if float(p.get('contracts', 0)) > 0])}")
        
        print("\n" + "=" * 60)
        print("✅ 所有测试通过！API密钥有效")
        print("=" * 60)
        
    except ccxt.AuthenticationError as e:
        print("\n" + "=" * 60)
        print("❌ 认证失败：API密钥无效或已过期")
        print("=" * 60)
        print(f"错误详情: {str(e)}")
        print("\n建议操作：")
        print("1. 访问 https://www.okx.com/trade-demo")
        print("2. 登录后进入 API管理")
        print("3. 创建新的API密钥")
        print("4. 更新 backend/.env 文件中的密钥配置")
        
    except ccxt.OnMaintenance as e:
        print("\n" + "=" * 60)
        print("⚠️ OKX服务维护中")
        print("=" * 60)
        print(f"错误详情: {str(e)}")
        
    except Exception as e:
        print("\n" + "=" * 60)
        print(f"❌ 测试失败: {type(e).__name__}")
        print("=" * 60)
        print(f"错误详情: {str(e)}")
        
    finally:
        await exchange.close()

if __name__ == '__main__':
    asyncio.run(test_okx_connection())