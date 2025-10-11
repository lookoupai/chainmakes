# OKX 实盘交易切换指南

## 📚 模拟盘 vs 实盘说明

### 当前状态

你的项目**目前使用 OKX 模拟盘 API** 进行测试。

### 关键代码逻辑

#### 1. 模拟盘/实盘控制参数

在 `backend/app/exchanges/okx_exchange.py:66-109`:

```python
def __init__(self, api_key: str, api_secret: str, passphrase: str,
             is_testnet: bool = True, proxy: str = None):
    """
    is_testnet: 是否使用模拟盘
    - True  = 模拟盘 (默认)
    - False = 真实盘
    """
    self.is_testnet = is_testnet

    # 设置模拟盘/真实盘
    if self.is_testnet:
        config['sandbox'] = True  # 模拟盘
        logger.info("✅ 使用 OKX 模拟盘环境")
    else:
        logger.info("⚠️ 使用 OKX 真实盘环境")
```

#### 2. 默认配置来源

在 `backend/app/exchanges/exchange_factory.py:70-78`:

```python
if exchange_name == 'okx':
    # 如果未明确传入,则从配置读取
    if is_testnet is None:
        is_testnet = settings.OKX_IS_DEMO  # 读取环境变量

    kwargs['is_testnet'] = is_testnet
```

**关键点**: `is_testnet` 参数**仅从环境变量 `OKX_IS_DEMO` 读取**,不在前端设置。

---

## 🎯 如何切换到实盘交易?

### ⚠️ 重要提醒

**在切换实盘前,必须确保**:

1. ✅ 已充分在模拟盘测试
2. ✅ 策略参数已优化
3. ✅ 理解真实资金风险
4. ✅ 设置合理的止损和仓位限制
5. ✅ **使用小额资金测试**

---

## 📝 完整切换步骤

### 步骤 1: 准备 OKX 实盘 API

#### 1.1 登录 OKX 官网

- 访问: https://www.okx.com
- 登录你的账户

#### 1.2 创建 API 密钥

1. 右上角 **头像** → **API**
2. 点击 **创建 V5 API Key**
3. 填写信息:
   - **API 名称**: 给个容易识别的名字,如 `TradingBot`
   - **API 密码**: 设置一个强密码 (这是 Passphrase)
   - **权限**:
     - ✅ **读取** (必选)
     - ✅ **交易** (必选)
     - ⚠️ 不要勾选 **提币** (安全考虑)
   - **IP 白名单**:
     - 建议绑定服务器 IP
     - 测试期间可暂时留空
4. 完成验证 (邮箱/手机/谷歌验证)
5. **立即复制并保存**:
   - API Key
   - Secret Key
   - Passphrase

**注意**: Secret Key **只显示一次**,请妥善保存!

#### 1.3 OKX 模拟盘 vs 实盘 API 区别

| 项目 | 模拟盘 API | 实盘 API |
|------|-----------|---------|
| 获取位置 | OKX → 模拟交易 → API | OKX → API |
| 资金 | 虚拟资金 | 真实资金 |
| 数据 | 真实行情 | 真实行情 |
| 订单 | 模拟执行 | 真实执行 |
| 费用 | 无 | 有交易手续费 |
| API 端点 | `www.okx.com/api` (sandbox=true) | `www.okx.com/api` (sandbox=false) |

**重点**: 模拟盘和实盘使用**同一个 API 端点**,区别在于 CCXT 的 `sandbox` 参数!

---

### 步骤 2: 修改环境变量

#### 2.1 编辑 `.env` 文件

```bash
vim .env
```

#### 2.2 添加实盘配置

```bash
# ========================================
# OKX 实盘配置 (⚠️ 风险警告)
# ========================================
# 切换到实盘: 设置为 false
OKX_IS_DEMO=false

# 代理配置 (国内需要)
OKX_PROXY=http://127.0.0.1:7890
```

**重要**:
- `OKX_IS_DEMO=false` 表示使用实盘
- `OKX_IS_DEMO=true` 表示使用模拟盘 (默认)

---

### 步骤 3: 在前端添加实盘 API

#### 3.1 登录系统

访问: http://localhost:3333 (或你的服务器地址)

#### 3.2 添加交易所账户

1. 点击左侧菜单 **交易所管理**
2. 点击 **添加交易所**
3. 填写信息:
   - **交易所**: 选择 `OKX`
   - **API Key**: 粘贴实盘 API Key
   - **API Secret**: 粘贴实盘 Secret Key
   - **Passphrase**: 粘贴实盘 Passphrase
4. 点击 **测试连接**
   - ✅ 成功: 显示账户余额
   - ❌ 失败: 检查 API 密钥和网络

**注意**:
- 前端只需要填写 API 密钥
- **不需要在前端选择模拟盘/实盘**
- 模拟盘/实盘由 `.env` 中的 `OKX_IS_DEMO` 控制

---

### 步骤 4: 重启服务

#### 4.1 Docker 部署

```bash
# 重启后端服务使环境变量生效
docker-compose restart backend

# 查看日志确认
docker-compose logs -f backend
```

查看日志中的提示:
- ✅ 模拟盘: `✅ 使用 OKX 模拟盘环境 (sandbox mode)`
- ⚠️ 实盘: `⚠️ 使用 OKX 真实盘环境`

#### 4.2 本地开发

```bash
# 停止后端
# Ctrl+C

# 重新启动
cd backend
venv\Scripts\activate
uvicorn app.main:app --reload
```

---

### 步骤 5: 小额测试

#### 5.1 创建测试机器人

1. **交易机器人** → **创建机器人**
2. 设置**极小**的参数:
   - **每单投资**: $10 (最小金额)
   - **最大持仓**: $50
   - **杠杆**: 1x (不使用杠杆)
   - **止损比例**: 5%
3. 选择流动性好的交易对: `BTC-USDT`

#### 5.2 观察运行

- 查看是否能正常开仓
- 检查订单是否在 OKX 官网显示
- 验证持仓数据是否一致
- 确认平仓功能正常

#### 5.3 验证成功标准

✅ 能正常连接 OKX API
✅ 能正常下单 (在 OKX 官网看到订单)
✅ 持仓数据准确
✅ 能正常平仓
✅ 余额变化正确

---

## 🔧 常见问题

### 1. 切换实盘后,测试连接失败

**可能原因**:
- API 权限不足
- IP 不在白名单
- 代理配置问题

**解决方法**:
```bash
# 检查环境变量
docker-compose exec backend env | grep OKX

# 查看日志
docker-compose logs backend | grep -i "okx\|sandbox"

# 确认显示: "⚠️ 使用 OKX 真实盘环境"
```

### 2. 实盘和模拟盘 API 密钥搞混了

**检查方法**:
- 模拟盘 API: OKX → 模拟交易 → API 管理
- 实盘 API: OKX → API 管理

**建议**:
- 给 API 密钥命名区分,如 `TradingBot-Demo` 和 `TradingBot-Real`

### 3. 切换后订单没有执行

**检查清单**:
```bash
# 1. 确认环境变量
grep OKX_IS_DEMO .env
# 应该显示: OKX_IS_DEMO=false

# 2. 确认服务已重启
docker-compose ps

# 3. 查看后端日志
docker-compose logs backend | tail -50
```

### 4. 想切回模拟盘

**步骤**:
```bash
# 1. 修改 .env
vim .env
# 改为: OKX_IS_DEMO=true

# 2. 重启后端
docker-compose restart backend

# 3. 在前端重新添加模拟盘 API
# (去 OKX 模拟交易获取 API)
```

---

## 📊 实盘和模拟盘共存方案

如果想同时使用模拟盘和实盘,有两种方案:

### 方案 1: 使用两套环境 (推荐)

```bash
# 开发/测试环境 - 模拟盘
OKX_IS_DEMO=true

# 生产环境 - 实盘
OKX_IS_DEMO=false
```

### 方案 2: 代码层面控制 (需要修改代码)

在前端添加"模拟盘/实盘"切换开关,然后修改:

1. 前端表单添加 `is_demo` 字段
2. 数据库 `exchange_account` 表添加 `is_demo` 列
3. API 调用时传递 `is_testnet` 参数

**注意**: 这需要改动较多代码,不推荐初期使用。

---

## ⚠️ 风险警告

### 实盘交易风险

1. **资金风险**: 使用真实资金,可能亏损
2. **杠杆风险**: 杠杆会放大盈亏
3. **网络风险**: 网络中断可能导致无法及时止损
4. **策略风险**: 策略可能不适应市场变化
5. **API 风险**: API 密钥泄露可能导致资金损失

### 安全建议

1. **小额起步**: 用少量资金测试
2. **设置止损**: 严格的止损策略
3. **限制仓位**: 不要满仓操作
4. **分散风险**: 不要把所有资金放在一个策略
5. **定期检查**: 每天查看运行状态
6. **保护 API**:
   - 不要分享 API 密钥
   - 绑定 IP 白名单
   - 不开启提币权限
   - 定期更换密钥

### 推荐做法

1. **第一周**: 模拟盘测试
2. **第二周**: $50-100 实盘小额测试
3. **第三周**: 如果稳定,逐步增加到 $500
4. **一个月后**: 根据收益情况决定是否增加资金

---

## 📝 总结

### 核心要点

1. **模拟盘/实盘由 `.env` 的 `OKX_IS_DEMO` 控制**
2. **前端只需填写 API 密钥,不需要选择模拟/实盘**
3. **切换实盘只需两步**:
   - 设置 `OKX_IS_DEMO=false`
   - 在前端填写实盘 API 密钥
4. **必须重启后端服务**才能生效
5. **用小额资金测试**

### 快速切换流程

```bash
# 切换到实盘
echo "OKX_IS_DEMO=false" >> .env
docker-compose restart backend

# 切换回模拟盘
echo "OKX_IS_DEMO=true" >> .env
docker-compose restart backend
```

### 验证当前环境

```bash
# 方法 1: 查看环境变量
docker-compose exec backend env | grep OKX_IS_DEMO

# 方法 2: 查看日志
docker-compose logs backend | grep -i sandbox

# 模拟盘显示: "✅ 使用 OKX 模拟盘环境"
# 实盘显示: "⚠️ 使用 OKX 真实盘环境"
```

---

**最后提醒**: 实盘交易有风险,入市需谨慎!建议充分测试后再使用实盘,并始终保持风险意识。

---

**文档更新**: 2025-01-11
