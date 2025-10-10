# ChainMakes API 文档

## 概述

ChainMakes API提供RESTful接口和WebSocket连接，用于管理加密货币交易机器人系统。所有API请求都需要有效的JWT令牌进行身份验证。

## 基础信息

- **基础URL**: `http://localhost:8000/api/v1`
- **认证方式**: JWT Bearer Token
- **数据格式**: JSON
- **字符编码**: UTF-8

## 认证

### 获取访问令牌

```http
POST /api/v1/auth/login
```

**请求体**:
```json
{
  "username": "admin",
  "password": "admin123"
}
```

**响应**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

### 刷新令牌

```http
POST /api/v1/auth/refresh
```

**请求头**:
```
Authorization: Bearer <access_token>
```

**响应**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

## 用户管理

### 获取当前用户信息

```http
GET /api/v1/users/me
```

**请求头**:
```
Authorization: Bearer <access_token>
```

**响应**:
```json
{
  "id": 1,
  "username": "admin",
  "email": "admin@example.com",
  "is_active": true,
  "created_at": "2025-10-05T00:00:00Z"
}
```

## 交易所管理

### 获取交易所列表

```http
GET /api/v1/exchanges/
```

**请求头**:
```
Authorization: Bearer <access_token>
```

**响应**:
```json
[
  {
    "id": 1,
    "name": "Binance",
    "api_key": "encrypted_key",
    "is_active": true,
    "created_at": "2025-10-05T00:00:00Z"
  }
]
```

### 创建交易所账户

```http
POST /api/v1/exchanges/
```

**请求头**:
```
Authorization: Bearer <access_token>
```

**请求体**:
```json
{
  "name": "Binance",
  "api_key": "your_api_key",
  "api_secret": "your_api_secret",
  "is_testnet": true
}
```

**响应**:
```json
{
  "id": 2,
  "name": "Binance",
  "api_key": "encrypted_key",
  "is_active": true,
  "is_testnet": true,
  "created_at": "2025-10-05T00:00:00Z"
}
```

### 更新交易所账户

```http
PUT /api/v1/exchanges/{exchange_id}
```

**请求头**:
```
Authorization: Bearer <access_token>
```

**请求体**:
```json
{
  "name": "Binance",
  "api_key": "new_api_key",
  "api_secret": "new_api_secret",
  "is_active": true
}
```

### 删除交易所账户

```http
DELETE /api/v1/exchanges/{exchange_id}
```

**请求头**:
```
Authorization: Bearer <access_token>
```

**响应**:
```json
{
  "message": "交易所账户已删除"
}
```

## 机器人管理

### 获取机器人列表

```http
GET /api/v1/bots/
```

**请求头**:
```
Authorization: Bearer <access_token>
```

**查询参数**:
- `skip`: 跳过记录数 (默认: 0)
- `limit`: 返回记录数 (默认: 100)
- `status`: 机器人状态过滤 (可选)

**响应**:
```json
[
  {
    "id": 1,
    "bot_name": "BTC-USDT套利机器人",
    "status": "running",
    "exchange_name": "Binance",
    "symbol": "BTC/USDT",
    "created_at": "2025-10-05T00:00:00Z",
    "updated_at": "2025-10-05T00:00:00Z"
  }
]
```

### 创建机器人

```http
POST /api/v1/bots/
```

**请求头**:
```
Authorization: Bearer <access_token>
```

**请求体**:
```json
{
  "bot_name": "BTC-USDT套利机器人",
  "exchange_account_id": 1,
  "symbol": "BTC/USDT",
  "strategy_type": "spread_arbitrage",
  "config": {
    "spread_threshold": 0.01,
    "trade_amount": 100,
    "max_positions": 5,
    "stop_loss": 0.05,
    "take_profit": 0.02
  }
}
```

**响应**:
```json
{
  "id": 2,
  "bot_name": "BTC-USDT套利机器人",
  "status": "stopped",
  "exchange_name": "Binance",
  "symbol": "BTC/USDT",
  "strategy_type": "spread_arbitrage",
  "config": {
    "spread_threshold": 0.01,
    "trade_amount": 100,
    "max_positions": 5,
    "stop_loss": 0.05,
    "take_profit": 0.02
  },
  "created_at": "2025-10-05T00:00:00Z"
}
```

### 获取机器人详情

```http
GET /api/v1/bots/{bot_id}
```

**请求头**:
```
Authorization: Bearer <access_token>
```

**响应**:
```json
{
  "id": 1,
  "bot_name": "BTC-USDT套利机器人",
  "status": "running",
  "exchange_name": "Binance",
  "symbol": "BTC/USDT",
  "strategy_type": "spread_arbitrage",
  "config": {
    "spread_threshold": 0.01,
    "trade_amount": 100,
    "max_positions": 5,
    "stop_loss": 0.05,
    "take_profit": 0.02
  },
  "performance": {
    "total_trades": 10,
    "profitable_trades": 7,
    "total_profit": 150.75,
    "current_drawdown": 0.02
  },
  "created_at": "2025-10-05T00:00:00Z",
  "updated_at": "2025-10-05T00:00:00Z"
}
```

### 更新机器人

```http
PUT /api/v1/bots/{bot_id}
```

**请求头**:
```
Authorization: Bearer <access_token>
```

**请求体**:
```json
{
  "bot_name": "更新后的机器人名称",
  "config": {
    "spread_threshold": 0.015,
    "trade_amount": 150,
    "max_positions": 3,
    "stop_loss": 0.04,
    "take_profit": 0.025
  }
}
```

### 删除机器人

```http
DELETE /api/v1/bots/{bot_id}
```

**请求头**:
```
Authorization: Bearer <access_token>
```

**响应**:
```json
{
  "message": "机器人已删除"
}
```

### 启动机器人

```http
POST /api/v1/bots/{bot_id}/start
```

**请求头**:
```
Authorization: Bearer <access_token>
```

**响应**:
```json
{
  "message": "机器人已启动",
  "status": "running"
}
```

### 停止机器人

```http
POST /api/v1/bots/{bot_id}/stop
```

**请求头**:
```
Authorization: Bearer <access_token>
```

**响应**:
```json
{
  "message": "机器人已停止",
  "status": "stopped"
}
```

### 暂停机器人

```http
POST /api/v1/bots/{bot_id}/pause
```

**请求头**:
```
Authorization: Bearer <access_token>
```

**响应**:
```json
{
  "message": "机器人已暂停",
  "status": "paused"
}
```

## 交易数据

### 获取订单历史

```http
GET /api/v1/bots/{bot_id}/orders
```

**请求头**:
```
Authorization: Bearer <access_token>
```

**查询参数**:
- `skip`: 跳过记录数 (默认: 0)
- `limit`: 返回记录数 (默认: 100)
- `status`: 订单状态过滤 (可选)
- `start_date`: 开始日期 (可选)
- `end_date`: 结束日期 (可选)

**响应**:
```json
[
  {
    "id": 1,
    "bot_instance_id": 1,
    "order_id": "12345",
    "symbol": "BTC/USDT",
    "side": "buy",
    "order_type": "limit",
    "amount": 0.001,
    "price": 50000,
    "filled": 0.001,
    "status": "filled",
    "created_at": "2025-10-05T00:00:00Z",
    "updated_at": "2025-10-05T00:00:00Z"
  }
]
```

### 获取持仓信息

```http
GET /api/v1/bots/{bot_id}/positions
```

**请求头**:
```
Authorization: Bearer <access_token>
```

**响应**:
```json
[
  {
    "id": 1,
    "bot_instance_id": 1,
    "symbol": "BTC/USDT",
    "side": "long",
    "size": 0.001,
    "entry_price": 50000,
    "current_price": 50500,
    "unrealized_pnl": 0.5,
    "created_at": "2025-10-05T00:00:00Z",
    "updated_at": "2025-10-05T00:00:00Z"
  }
]
```

### 获取价差历史

```http
GET /api/v1/bots/{bot_id}/spreads
```

**请求头**:
```
Authorization: Bearer <access_token>
```

**查询参数**:
- `skip`: 跳过记录数 (默认: 0)
- `limit`: 返回记录数 (默认: 100)
- `start_date`: 开始日期 (可选)
- `end_date`: 结束日期 (可选)

**响应**:
```json
[
  {
    "id": 1,
    "bot_instance_id": 1,
    "symbol": "BTC/USDT",
    "spread": 0.015,
    "price1": 50000,
    "price2": 50750,
    "timestamp": "2025-10-05T00:00:00Z"
  }
]
```

## WebSocket API

### 连接机器人实时数据

```
WS /api/v1/ws/bot/{bot_id}
```

**请求头**:
```
Authorization: Bearer <access_token>
```

**消息格式**:

**机器人状态更新**:
```json
{
  "type": "bot_status",
  "data": {
    "bot_id": 1,
    "status": "running",
    "timestamp": "2025-10-05T00:00:00Z"
  }
}
```

**价格更新**:
```json
{
  "type": "price_update",
  "data": {
    "symbol": "BTC/USDT",
    "price": 50500,
    "timestamp": "2025-10-05T00:00:00Z"
  }
}
```

**订单更新**:
```json
{
  "type": "order_update",
  "data": {
    "order_id": "12345",
    "status": "filled",
    "filled": 0.001,
    "timestamp": "2025-10-05T00:00:00Z"
  }
}
```

**持仓更新**:
```json
{
  "type": "position_update",
  "data": {
    "symbol": "BTC/USDT",
    "side": "long",
    "size": 0.001,
    "unrealized_pnl": 0.5,
    "timestamp": "2025-10-05T00:00:00Z"
  }
}
```

## 错误处理

### 错误响应格式

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "请求参数验证失败",
    "details": {
      "field": "price",
      "reason": "价格必须大于0"
    }
  }
}
```

### 常见错误代码

| 错误代码 | HTTP状态码 | 描述 |
|---------|-----------|------|
| VALIDATION_ERROR | 400 | 请求参数验证失败 |
| UNAUTHORIZED | 401 | 未授权访问 |
| FORBIDDEN | 403 | 权限不足 |
| NOT_FOUND | 404 | 资源不存在 |
| CONFLICT | 409 | 资源冲突 |
| INTERNAL_ERROR | 500 | 服务器内部错误 |
| SERVICE_UNAVAILABLE | 503 | 服务不可用 |

## 限流

API实施限流机制，限制每个用户的请求频率：

- 每分钟最多100个请求
- 超出限制将返回429状态码

## 数据类型

### 机器人状态

- `stopped`: 已停止
- `running`: 运行中
- `paused`: 已暂停
- `error`: 错误状态

### 订单状态

- `pending`: 待执行
- `partial`: 部分成交
- `filled`: 完全成交
- `cancelled`: 已取消
- `failed`: 执行失败

### 订单类型

- `market`: 市价单
- `limit`: 限价单
- `stop`: 止损单
- `stop_limit`: 止损限价单

## 示例代码

### Python示例

```python
import requests

# 登录获取令牌
response = requests.post('http://localhost:8000/api/v1/auth/login', json={
    'username': 'admin',
    'password': 'admin123'
})
token = response.json()['access_token']

# 设置请求头
headers = {'Authorization': f'Bearer {token}'}

# 获取机器人列表
response = requests.get('http://localhost:8000/api/v1/bots/', headers=headers)
bots = response.json()
print(bots)
```

### JavaScript示例

```javascript
// 登录获取令牌
const response = await fetch('http://localhost:8000/api/v1/auth/login', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    username: 'admin',
    password: 'admin123'
  })
});
const data = await response.json();
const token = data.access_token;

// 设置请求头
const headers = {
  'Authorization': `Bearer ${token}`,
  'Content-Type': 'application/json'
};

// 获取机器人列表
const botsResponse = await fetch('http://localhost:8000/api/v1/bots/', { headers });
const bots = await botsResponse.json();
console.log(bots);
```

### WebSocket示例

```javascript
// 连接WebSocket
const ws = new WebSocket('ws://localhost:8000/api/v1/ws/bot/1', [], {
  headers: {
    'Authorization': `Bearer ${token}`
  }
});

// 处理消息
ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  console.log('收到消息:', message);
};

// 发送消息
ws.send(JSON.stringify({
  type: 'subscribe',
  data: {
    events: ['price_update', 'order_update']
  }
}));
```

## 更新日志

### v1.0.0 (2025-10-05)

- 初始版本发布
- 实现基础认证和机器人管理
- 支持价差套利策略
- 提供WebSocket实时数据推送
- 完整的错误处理机制

---

如有任何问题或建议，请联系开发团队或查看项目文档。