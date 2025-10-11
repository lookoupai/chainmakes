# OKX 网络连接重试机制修复说明

## 问题描述

在使用过程中，可能会遇到以下网络连接错误：

```
aiohttp.client_exceptions.ServerDisconnectedError: Server disconnected
ccxt.base.errors.ExchangeNotAvailable: okx GET https://www.okx.com/api/v5/market/ticker?instId=LTC-USDT-SWAP
```

这些错误通常是由于：
- 网络不稳定
- OKX 服务器临时断开连接
- 请求频率过高导致临时限制

## 解决方案

### 1. 添加指数退避重试机制

已为所有关键的 OKX API 调用添加了自动重试机制，使用指数退避策略：

```python
@retry_on_network_error(max_retries=3, base_delay=1.0)
async def get_ticker(self, symbol: str):
    # 网络请求失败时会自动重试
    # 重试延迟: 1s → 2s → 4s → 8s
    ...
```

### 2. 覆盖的 API 方法

| 方法 | 重试次数 | 基础延迟 | 说明 |
|------|---------|---------|------|
| `get_ticker()` | 3次 | 1.0秒 | 获取行情数据 |
| `create_market_order()` | 3次 | 1.0秒 | 创建市价订单 |
| `create_limit_order()` | 3次 | 1.0秒 | 创建限价订单 |
| `get_position()` | 3次 | 1.0秒 | 获取持仓 |
| `get_all_positions()` | 3次 | 1.0秒 | 获取所有持仓 |
| `set_leverage()` | 2次 | 0.5秒 | 设置杠杆 |
| `get_balance()` | 3次 | 1.0秒 | 获取余额 |
| `fetch_historical_price()` | 2次 | 1.0秒 | 获取历史价格 |

### 3. 改进的错误处理

- **价格获取失败**：跳过本次循环，不停止机器人
- **持仓更新失败**：记录警告，继续执行
- **循环执行错误**：记录错误日志，机器人继续运行

## 重试行为示例

### 成功重试的情况

```
2025-10-11 02:45:54 - okx_exchange - WARNING - 网络请求失败 (尝试 1/4): Server disconnected, 1.0秒后重试...
2025-10-11 02:45:55 - okx_exchange - WARNING - 网络请求失败 (尝试 2/4): Server disconnected, 2.0秒后重试...
2025-10-11 02:45:57 - okx_exchange - INFO - 获取行情成功: LTC/USDT:USDT
```

### 所有重试失败的情况

```
2025-10-11 02:45:54 - okx_exchange - WARNING - 网络请求失败 (尝试 1/4): Server disconnected, 1.0秒后重试...
2025-10-11 02:45:55 - okx_exchange - WARNING - 网络请求失败 (尝试 2/4): Server disconnected, 2.0秒后重试...
2025-10-11 02:45:57 - okx_exchange - WARNING - 网络请求失败 (尝试 3/4): Server disconnected, 4.0秒后重试...
2025-10-11 02:46:01 - okx_exchange - ERROR - 网络请求失败，已重试 3 次: Server disconnected
2025-10-11 02:46:01 - bot_engine - WARNING - [BotEngine] Bot 11 获取市场价格失败: Server disconnected, 跳过本次循环
```

## 优势

1. **自动恢复**：临时网络问题会自动重试，无需人工干预
2. **智能退避**：使用指数退避策略，避免过度请求
3. **机器人稳定性**：单次网络错误不会导致机器人停止
4. **详细日志**：记录每次重试尝试，便于问题排查

## 配置代理（可选）

如果网络连接问题持续存在，可以在创建交易所实例时配置代理：

```python
exchange = OKXExchange(
    api_key="your_api_key",
    api_secret="your_api_secret",
    passphrase="your_passphrase",
    is_testnet=True,
    proxy="http://127.0.0.1:7890"  # 添加代理配置
)
```

支持的代理格式：
- HTTP 代理: `http://127.0.0.1:7890`
- HTTPS 代理: `https://127.0.0.1:7890`
- SOCKS5 代理: `socks5://127.0.0.1:1080`

## 测试建议

### 1. 观察日志

启动机器人后，观察日志输出：
- 正常情况下不应该看到重试日志
- 如果偶尔看到重试成功的日志，说明修复生效
- 如果频繁看到所有重试都失败，可能需要检查网络连接或配置代理

### 2. 网络测试

可以临时断开网络连接来测试重试机制：
1. 启动机器人
2. 等待几个循环周期
3. 临时断开网络连接 5-10 秒
4. 恢复网络连接
5. 观察机器人是否自动恢复正常运行

### 3. 压力测试

可以同时运行多个机器人实例来测试在高负载下的表现。

## 故障排查

### 问题：仍然频繁出现网络错误

**可能原因**：
1. 本地网络不稳定
2. OKX API 访问受限（可能需要代理）
3. 请求频率超过 OKX 限制

**解决方案**：
1. 检查本地网络连接
2. 配置代理服务器（见上文）
3. 减少机器人实例数量
4. 增加循环间隔时间（默认 5 秒）

### 问题：机器人运行缓慢

**可能原因**：
频繁的重试会增加响应时间

**解决方案**：
1. 改善网络连接质量
2. 使用更稳定的网络环境
3. 配置合适的代理服务器

## 更新日期

2025-10-11

## 相关文件

- `backend/app/exchanges/okx_exchange.py` - OKX 交易所适配器
- `backend/app/core/bot_engine.py` - 机器人核心引擎
