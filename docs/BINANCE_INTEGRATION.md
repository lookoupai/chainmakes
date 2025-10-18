# Binance 交易所集成说明

## 概述

本项目已成功集成 Binance（币安）交易所支持，用户现在可以同时使用 OKX 和 Binance 两个交易所进行套利交易。

## 集成完成时间

2025-01-15

## 新增文件

### 后端文件
- `backend/app/exchanges/binance_exchange.py` - Binance 交易所适配器实现
- `backend/test_binance.py` - Binance 交易所集成测试脚本
- `backend/简单测试币安.bat` - Windows 批处理测试脚本

### 修改文件
- `backend/app/exchanges/exchange_factory.py` - 注册 Binance 交易所
- `frontend/src/pages/exchanges/ExchangeList.vue` - 启用 Binance 选项

## 功能特性

### 已实现功能

1. **行情数据获取** ✅
   - 实时获取交易对价格、买卖价、成交量

2. **订单管理** ✅
   - 创建市价订单（支持开仓/平仓）
   - 创建限价订单
   - 查询订单状态
   - 取消订单

3. **持仓管理** ✅
   - 获取指定交易对持仓
   - 获取所有持仓信息
   - 持仓详情（方向、数量、均价、盈亏等）

4. **账户管理** ✅
   - 获取账户余额（总额、可用、冻结）
   - 设置杠杆倍数

5. **历史数据** ✅
   - 获取指定时间点的历史价格（用于统计起始价格）

6. **测试网支持** ✅
   - 支持 Binance 测试网（默认启用）
   - 可切换到真实交易环境

## 使用说明

### 1. 添加 Binance 交易所账户

在前端界面：
1. 进入"交易所管理"页面
2. 点击"添加交易所账户"
3. 选择"Binance"
4. 输入 API Key 和 API Secret（不需要 Passphrase）
5. **选择交易环境**：
   - **测试网/模拟盘** ⚠️ (推荐新手)：无需真实资金，安全测试
   - **真实环境** ⛔：使用真实资金交易，请谨慎操作
6. 点击"添加"

### 2. 测试连接

添加账户后，点击"测试连接"按钮验证 API 密钥是否正确。

### 3. 创建交易机器人

1. 进入"机器人管理"页面
2. 点击"创建机器人"
3. 选择 Binance 交易所账户
4. 配置交易对和策略参数
5. 启动机器人

### 4. 获取 Binance API 密钥

#### 测试网（推荐新手）
1. 访问 Binance Testnet: https://testnet.binancefuture.com/
2. 使用 GitHub 账号登录
3. 在 API Key 管理页面创建测试用 API 密钥

#### 真实环境
1. 登录 Binance 官网: https://www.binance.com/
2. 进入"API管理"
3. 创建新的 API Key
4. **重要安全设置**：
   - ✅ 启用"读取"权限
   - ✅ 启用"合约交易"权限
   - ❌ 禁用"提现"权限（安全考虑）
   - 建议设置 IP 白名单

## 技术实现

### 架构设计

```
BaseExchange (抽象基类)
    ↓
BinanceExchange (Binance 实现)
    ↓
ExchangeFactory (工厂类)
```

### 核心特性

1. **继承 BaseExchange**
   - 实现所有抽象方法
   - 统一接口标准

2. **使用 CCXT 库**
   - 跨交易所统一 API
   - 自动处理签名和认证

3. **测试网配置**
   - 通过 `sandbox=True` 参数启用
   - 默认使用测试网环境

4. **错误处理**
   - 完善的异常捕获
   - 详细的日志记录

### 与 OKX 的差异

| 特性 | OKX | Binance |
|------|-----|---------|
| API Passphrase | ✅ 需要 | ❌ 不需要 |
| 代理配置 | ✅ 支持 | ⚠️ 可选 |
| 持仓模式 | 单向持仓 | 双向持仓 |
| 交易对格式 | BTC-USDT-SWAP | BTC/USDT |
| 测试网 | 模拟盘 | Testnet |

## 测试

### 运行测试脚本

#### Windows
```bash
cd backend
简单测试币安.bat
```

#### Linux/Mac
```bash
cd backend
python test_binance.py
```

### 测试输出示例

```
============================================================
Binance 交易所集成测试
============================================================

[1] 创建 Binance 交易所实例...
[OK] Binance 交易所实例创建成功

[2] 测试获取行情数据...
[OK] BTC/USDT 行情:
   最新价: 43500.50
   买一价: 43500.00
   卖一价: 43500.80
   24h成交量: 1250000.50

[SUCCESS] Binance 交易所集成测试完成
============================================================
```

## 配置说明

### 环境变量（可选）

在 `.env` 文件中添加：

```env
# Binance API 配置（可选）
BINANCE_API_KEY=your_api_key_here
BINANCE_API_SECRET=your_api_secret_here
BINANCE_IS_TESTNET=True  # True=测试网, False=真实环境
```

### 数据库

使用现有的 `exchange_accounts` 表，无需新建表。`exchange_name` 字段支持：
- `okx`
- `binance`
- `bybit`（待实现）
- `mock`（测试用）

## 限制和注意事项

1. **测试网限制**
   - 测试网数据仅供测试，不代表真实市场
   - 测试网 API 可能不稳定

2. **API 频率限制**
   - Binance 有严格的 API 调用频率限制
   - 建议开启 `enableRateLimit=True`（已默认开启）

3. **时间同步**
   - Binance 要求服务器时间误差 < 1000ms
   - 已启用 `adjustForTimeDifference=True`

4. **持仓模式**
   - Binance 支持双向持仓模式
   - 需要在账户设置中确认持仓模式

## 扩展其他交易所

基于现有架构，可以轻松添加其他交易所（如 Bybit、Huobi 等）：

1. 创建新的交易所类继承 `BaseExchange`
2. 实现所有抽象方法
3. 在 `ExchangeFactory.EXCHANGES` 中注册
4. 前端启用对应选项

示例：
```python
# bybit_exchange.py
class BybitExchange(BaseExchange):
    def _init_exchange(self):
        return ccxt.bybit({...})
    # ... 实现其他方法
```

## 支持和反馈

如遇到问题，请检查：
1. API 密钥是否正确
2. API 权限是否足够
3. 网络连接是否正常
4. 查看日志文件获取详细错误信息

## 数据库迁移

如果你的项目已经运行过，需要执行数据库迁移来添加 `is_testnet` 字段：

```bash
cd backend
python add_is_testnet_field.py
```

迁移脚本会自动：
- 为 `exchange_accounts` 表添加 `is_testnet` 字段
- 将现有账户的 `is_testnet` 设置为 `True`（测试网）
- 验证迁移是否成功

## 更新日志

### v1.1 (2025-01-15)
- ✅ 支持每个账户独立选择实盘/模拟盘
- ✅ 前端界面添加交易环境选择
- ✅ 数据库迁移脚本

### v1.0 (2025-01-15)
- ✅ 完成 Binance 交易所基础集成
- ✅ 支持测试网和真实环境切换
- ✅ 实现所有核心交易功能
- ✅ 前端界面完整支持
- ✅ 通过集成测试

## 下一步计划

- [ ] 添加 Bybit 交易所支持
- [ ] 优化 API 调用频率控制
- [ ] 添加更多交易对筛选条件
- [ ] 支持更多订单类型（止盈止损等）
