# OKX 交易所集成指南

## 📋 概述

ChainMakes 已集成 OKX 交易所 API,支持真实和模拟盘交易。本文档介绍如何配置和使用 OKX API。

## 🔑 获取 API 凭据

### 模拟盘 (推荐用于测试)

1. 访问 OKX 模拟盘: https://www.okx.com/trade-demo
2. 注册/登录账户
3. 进入 API 管理页面创建 API Key
4. 保存以下信息:
   - **API Key**
   - **Secret Key**
   - **Passphrase**

### 真实盘 (实盘交易)

1. 访问 OKX 官网: https://www.okx.com
2. 完成 KYC 认证
3. 进入 API 管理页面
4. 创建 API Key 并设置权限:
   - ✅ **读取权限** (必选)
   - ✅ **交易权限** (必选)
   - ❌ **提现权限** (不建议)
5. 设置 IP 白名单 (强烈建议)

## ⚙️ 配置方法

### 方式1: 环境变量 (推荐)

在 `backend/.env` 文件中添加:

```env
# OKX API 配置
OKX_API_KEY=your_api_key_here
OKX_API_SECRET=your_api_secret_here
OKX_PASSPHRASE=your_passphrase_here
OKX_IS_DEMO=True  # True=模拟盘, False=真实盘
```

### 方式2: 数据库配置

在交易所账户管理界面添加 OKX 账户:
- 交易所类型: OKX
- API Key
- API Secret
- Passphrase

## 🧪 测试连接

### 使用测试脚本

```bash
cd backend
source venv/Scripts/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows

python scripts/test_okx_api.py
```

### 测试内容

脚本会测试以下功能:
1. ✅ 获取行情数据
2. ✅ 获取账户余额
3. ✅ 获取持仓信息
4. ✅ API 连接状态

## 📖 API 使用示例

### 1. 初始化客户端

```python
from app.exchanges.okx_exchange import OKXExchange

exchange = OKXExchange(
    api_key="your_api_key",
    api_secret="your_api_secret",
    passphrase="your_passphrase"
)
```

### 2. 获取行情数据

```python
# 获取 BTC-USDT 永续合约行情
ticker = await exchange.get_ticker("BTC-USDT-SWAP")

print(f"最新价: ${ticker['last_price']}")
print(f"买一价: ${ticker['bid']}")
print(f"卖一价: ${ticker['ask']}")
```

### 3. 下市价单

```python
from decimal import Decimal

# 买入 0.001 BTC
order = await exchange.create_market_order(
    symbol="BTC-USDT-SWAP",
    side="buy",
    amount=Decimal("0.001")
)

print(f"订单ID: {order['id']}")
print(f"状态: {order['status']}")
```

### 4. 下限价单

```python
# 以 40000 价格买入 0.001 BTC
order = await exchange.create_limit_order(
    symbol="BTC-USDT-SWAP",
    side="buy",
    amount=Decimal("0.001"),
    price=Decimal("40000")
)
```

### 5. 查询持仓

```python
# 查询所有持仓
positions = await exchange.get_all_positions()

for pos in positions:
    print(f"交易对: {pos['symbol']}")
    print(f"方向: {pos['side']}")
    print(f"数量: {pos['amount']}")
    print(f"未实现盈亏: ${pos['unrealized_pnl']}")
```

### 6. 设置杠杆

```python
# 设置 BTC-USDT 永续合约 5 倍杠杆
await exchange.set_leverage("BTC-USDT-SWAP", 5)
```

### 7. 获取账户余额

```python
balance = await exchange.get_balance()

usdt_balance = balance['total'].get('USDT', 0)
print(f"USDT 余额: {usdt_balance}")
```

## 🔐 安全建议

### API 密钥安全

1. ✅ **永远不要**将 API 密钥提交到 Git 仓库
2. ✅ 使用环境变量或加密配置文件存储
3. ✅ 定期轮换 API 密钥
4. ✅ 设置 IP 白名单限制访问
5. ✅ 仅授予必要的权限

### 交易安全

1. ✅ **先在模拟盘测试**,确保策略正常运行
2. ✅ 设置合理的止损止盈参数
3. ✅ 限制单笔交易金额
4. ✅ 监控账户余额和持仓
5. ✅ 启用双重验证 (2FA)

## 🚨 常见问题

### Q1: API 连接失败

**可能原因:**
- API 凭据错误
- IP 未加入白名单
- API 权限不足
- 网络连接问题

**解决方法:**
1. 检查 API Key、Secret、Passphrase 是否正确
2. 确认 IP 地址在白名单中
3. 验证 API 权限设置
4. 检查网络连接和防火墙

### Q2: 订单失败

**可能原因:**
- 余额不足
- 交易对不存在
- 杠杆未设置
- 最小交易量限制

**解决方法:**
1. 确保账户有足够余额
2. 使用正确的交易对格式 (如 BTC-USDT-SWAP)
3. 先设置杠杆再交易
4. 查看交易所最小交易量要求

### Q3: 模拟盘和真实盘切换

**切换方法:**
修改 `.env` 文件中的 `OKX_IS_DEMO`:
- `True` = 模拟盘
- `False` = 真实盘

**注意:** 模拟盘和真实盘使用不同的 API 凭据!

## 📊 支持的交易对

### 永续合约

- BTC-USDT-SWAP
- ETH-USDT-SWAP
- BNB-USDT-SWAP
- SOL-USDT-SWAP
- 等等...

### 查询可用交易对

```python
# 使用 CCXT 库查询
markets = await exchange.exchange.load_markets()
print(markets.keys())
```

## 🔄 从模拟交易所迁移到 OKX

如果您之前使用模拟交易所 (MockExchange),切换到 OKX 很简单:

### 1. 更新配置

修改机器人的交易所设置:
```python
# 之前
from app.exchanges.mock_exchange import MockExchange
exchange = MockExchange(api_key="mock", api_secret="mock")

# 现在
from app.exchanges.okx_exchange import OKXExchange
exchange = OKXExchange(
    api_key=os.getenv("OKX_API_KEY"),
    api_secret=os.getenv("OKX_API_SECRET"),
    passphrase=os.getenv("OKX_PASSPHRASE")
)
```

### 2. 调整交易对格式

OKX 使用不同的交易对格式:
```python
# MockExchange: BTC-USDT
# OKX: BTC-USDT-SWAP (永续合约)
```

### 3. 小额测试

切换到真实 API 后:
1. 先用小额资金测试
2. 验证所有功能正常
3. 逐步增加投入

## 📚 相关文档

- [OKX API 官方文档](https://www.okx.com/docs-v5/zh/)
- [CCXT 文档](https://docs.ccxt.com/)
- [ChainMakes 开发文档](./DEVELOPMENT_HANDOVER_2025-10-06.md)
- [API 接口文档](./API_DOCUMENTATION.md)

## 💡 最佳实践

### 开发流程

1. **模拟盘开发** → 2. **模拟盘测试** → 3. **真实盘小额测试** → 4. **正式运行**

### 监控策略

- 实时监控账户余额
- 记录所有交易日志
- 设置异常告警
- 定期检查持仓

### 风险控制

- 设置最大持仓限制
- 启用止损机制
- 分散投资标的
- 控制杠杆倍数

---

**重要提示:** 加密货币交易存在风险,请理性投资,做好风险管理!
