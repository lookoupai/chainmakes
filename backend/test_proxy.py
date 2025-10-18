"""
测试代理连接
"""
import asyncio
import aiohttp
import sys
import io

# 设置UTF-8编码输出
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

async def test_proxy():
    """测试代理是否可用"""
    proxy = "http://127.0.0.1:10808"
    url = "https://www.okx.com/api/v5/public/time"
    
    print(f"测试代理: {proxy}")
    print(f"目标URL: {url}")
    print("-" * 60)
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, proxy=proxy, timeout=aiohttp.ClientTimeout(total=10)) as response:
                data = await response.json()
                print(f"[OK] 代理连接成功")
                print(f"响应状态: {response.status}")
                print(f"响应数据: {data}")
    except Exception as e:
        print(f"[FAIL] 代理连接失败: {type(e).__name__}")
        print(f"错误详情: {str(e)}")

if __name__ == '__main__':
    asyncio.run(test_proxy())