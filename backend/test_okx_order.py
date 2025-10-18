"""
测试OKX模拟盘下单
"""
import asyncio
import ccxt.async_support as ccxt
from dotenv import load_dotenv
import os
import sys
import io

# 设置UTF-8编码输出
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

load_dotenv()

async def test_create_order():
    """测试创建订单"""
    
    api_key = os.getenv('OKX_API_KEY')
    api_secret = os.getenv('OKX_API_SECRET')
    passphrase = os.getenv('OKX_PASSPHRASE')
    proxy = os.getenv('OKX_PROXY')
    
    config = {
        'apiKey': api_key,
        'secret': api_secret,
        'password': passphrase,
        'enableRateLimit': True,
        'sandbox': True,
        'options': {
            'defaultType': 'swap',
        }
    }
    
    if proxy:
        config['httpsProxy'] = proxy
    
    exchange = ccxt.okx(config)
    
    try:
        print("测试创建小额市价订单...")
        print("-" * 60)
        
        # 测试创建一个最小数量的订单
        symbol = 'BTC/USDT:USDT'
        side = 'buy'
        amount = 0.01  # 最小精度
        
        print(f"交易对: {symbol}")
        print(f"方向: {side}")
        print(f"数量: {amount}")
        print(f"参数: posSide=long")
        print("-" * 60)
        
        order = await exchange.create_order(
            symbol=symbol,
            type='market',
            side=side,
            amount=amount,
            params={'posSide': 'long'}
        )
        
        print("[OK] 订单创建成功！")
        print(f"订单ID: {order['id']}")
        print(f"状态: {order['status']}")
        print(f"成交数量: {order.get('filled', 0)}")
        
    except ccxt.OnMaintenance as e:
        print("[维护] OKX模拟盘正在维护")
        print(f"错误: {str(e)}")
        print("\n建议：")
        print("1. 等待10-30分钟后重试")
        print("2. 检查OKX官方公告")
        
    except ccxt.AuthenticationError as e:
        print("[认证失败] API密钥无效")
        print(f"错误: {str(e)}")
        
    except Exception as e:
        print(f"[失败] {type(e).__name__}")
        print(f"错误: {str(e)}")
        
    finally:
        await exchange.close()

if __name__ == '__main__':
    asyncio.run(test_create_order())