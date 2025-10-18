"""
测试 Binance 交易所集成
"""
import asyncio
import os
import sys

# 设置UTF-8编码
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.exchanges.exchange_factory import ExchangeFactory


async def test_binance_integration():
    """测试币安交易所基本功能"""
    print("=" * 60)
    print("Binance 交易所集成测试")
    print("=" * 60)
    
    # 从环境变量读取API密钥（需要在.env文件中配置）
    api_key = os.getenv("BINANCE_API_KEY", "your_api_key_here")
    api_secret = os.getenv("BINANCE_API_SECRET", "your_api_secret_here")
    
    if api_key == "your_api_key_here":
        print("\n警告: 未配置 Binance API 密钥")
        print("请在 .env 文件中添加:")
        print("BINANCE_API_KEY=your_api_key")
        print("BINANCE_API_SECRET=your_api_secret")
        print("\n使用测试网进行模拟测试...")
    
    try:
        # 创建币安交易所实例（默认使用测试网）
        print("\n[1] 创建 Binance 交易所实例...")
        exchange = ExchangeFactory.create(
            exchange_name='binance',
            api_key=api_key,
            api_secret=api_secret,
            is_testnet=True  # 使用测试网
        )
        print("[OK] Binance 交易所实例创建成功")
        
        # 测试获取行情
        print("\n[2] 测试获取行情数据...")
        symbol = "BTC/USDT"
        ticker = await exchange.get_ticker(symbol)
        print(f"[OK] {symbol} 行情:")
        print(f"   最新价: {ticker['last_price']}")
        print(f"   买一价: {ticker['bid']}")
        print(f"   卖一价: {ticker['ask']}")
        print(f"   24h成交量: {ticker['volume']}")
        
        # 如果配置了真实API密钥，测试账户相关功能
        if api_key != "your_api_key_here":
            # 测试获取余额
            print("\n[3] 测试获取账户余额...")
            balance = await exchange.get_balance()
            print("[OK] 账户余额:")
            
            # 只显示有余额的币种
            total_balance = balance.get('total', {})
            has_balance = False
            for currency, amount in total_balance.items():
                if float(amount) > 0:
                    has_balance = True
                    free = balance['free'].get(currency, 0)
                    used = balance['used'].get(currency, 0)
                    print(f"   {currency}: 总计={amount}, 可用={free}, 冻结={used}")
            
            if not has_balance:
                print("   账户暂无余额")
            
            # 测试获取持仓
            print("\n[4] 测试获取持仓信息...")
            positions = await exchange.get_all_positions()
            if positions:
                print(f"[OK] 当前持仓数量: {len(positions)}")
                for pos in positions:
                    print(f"   {pos['symbol']}: {pos['side']} {pos['amount']} @ {pos['entry_price']}")
            else:
                print("   当前无持仓")
            
            # 测试设置杠杆
            print("\n[5] 测试设置杠杆...")
            try:
                result = await exchange.set_leverage(symbol, 5)
                print(f"[OK] 设置杠杆成功: {symbol} 5x")
            except Exception as e:
                print(f"[WARN] 设置杠杆失败（可能需要先持有该币种）: {str(e)}")
            
            # 测试获取历史价格
            print("\n[6] 测试获取历史价格...")
            import time
            timestamp = int(time.time() * 1000) - 3600000  # 1小时前
            historical_price = await exchange.fetch_historical_price(symbol, timestamp)
            if historical_price:
                print(f"[OK] 1小时前的价格: {historical_price}")
            else:
                print("[WARN] 无法获取历史价格")
        else:
            print("\n[SKIP] 跳过需要真实API密钥的测试")
        
        # 关闭连接
        await exchange.close()
        print("\n" + "=" * 60)
        print("[SUCCESS] Binance 交易所集成测试完成")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n[ERROR] 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_binance_integration())
