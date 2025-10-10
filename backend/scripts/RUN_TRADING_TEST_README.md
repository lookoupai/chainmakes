# 完整交易循环测试指南

## 问题诊断

当前测试遇到的核心问题：

1. **Uvicorn 自动重载干扰**：测试脚本修改会触发 Uvicorn 检测到文件变化，导致服务重载，所有运行中的机器人被强制停止
2. **机器人循环执行正常**：从日志可见机器人能够正常启动、初始化价格、执行循环
3. **WebSocket 连接成功**：客户端能够成功建立 WebSocket 连接
4. **没有交易触发**：Mock Exchange 生成的价差为 0%，无法达到 5% 的开仓阈值

## 解决方案

### 方案 1：停用 Uvicorn 自动重载（推荐用于测试）

```bash
# 在 backend 目录下
cd backend
venv\Scripts\activate

# 停止当前的 uvicorn 进程（Ctrl+C）
# 然后以非重载模式启动
python -m uvicorn app.main:app --port 8000
# 注意：移除了 --reload 参数
```

然后在另一个终端运行测试：
```bash
cd backend
venv\Scripts\python.exe scripts/test_complete_trading_cycle.py
```

### 方案 2：调整 Mock Exchange 价格波动

当前 Mock Exchange 的价格波动范围太小（±2%），导致两个市场价格几乎相同，价差接近 0。

修改 `backend/app/exchanges/mock_exchange.py`:

```python
# 第 67 行附近
# 原代码：
change_percent = Decimal(str(random.uniform(-0.02, 0.02)))  # ±2%

# 修改为：
change_percent = Decimal(str(random.uniform(-0.10, 0.10)))  # ±10%
```

这样可以产生更大的价格波动，更容易触发 5% 的开仓条件。

### 方案 3：降低开仓阈值（快速验证）

修改测试脚本中的 DCA 配置：

```python
"dca_config": [
    {"times": 1, "spread": "1.0", "multiplier": "1.0"},   # 1% 就开仓
    {"times": 2, "spread": "0.5", "multiplier": "1.5"},   # 0.5% 加仓
    {"times": 3, "spread": "0.5", "multiplier": "2.0"}
],
```

## 测试验证清单

- [ ] 后端以非重载模式运行
- [ ] 机器人成功创建并启动
- [ ] WebSocket 连接建立
- [ ] 收到价差更新消息（spread_update）
- [ ] 价差达到阈值触发开仓
- [ ] 收到订单创建消息（order_update）
- [ ] 收到持仓更新消息（position_update）
- [ ] 价差变化触发加仓
- [ ] 止盈/止损触发平仓
- [ ] 完成完整交易循环

## 当前测试结果

### 机器人状态（Bot ID: 8）
- ✅ 创建成功
- ✅ 启动成功
- ✅ 初始化价格完成
- ✅ 第1次循环执行
- ❌ 被 Uvicorn 重载强制停止
- ❌ 未触发任何交易（价差 0%）

### WebSocket 连接
- ✅ 连接建立成功
- ✅ JWT 认证通过
- ❌ 监听 120 秒未收到消息
- ⚠️ 机器人已停止，无消息推送

### 数据统计
- 价差更新次数: 0
- 订单创建次数: 0
- 持仓更新次数: 0
- 总订单数: 0
- 总持仓数: 0

## 下一步行动

1. **立即执行**：使用方案 1 + 方案 2
   - 停止当前 Uvicorn（移除 --reload）
   - 修改 Mock Exchange 价格波动范围到 ±10%
   - 重新运行测试脚本

2. **预期结果**：
   - 机器人持续运行不被中断
   - 价差在 -10% 到 +10% 范围波动
   - 达到 5% 时触发首次开仓
   - WebSocket 接收到交易消息

3. **如果仍未触发交易**：
   - 检查 `_should_open_position()` 逻辑
   - 添加更详细的判断日志
   - 手动验证价差计算公式

## 技术要点

### 价差计算公式
```python
spread = (market1_price - market2_price) / market2_price * 100
```

当前情况：
- market1_price = 26034.86 (BTC/USDT)
- market2_price = 13950.53 (ETH/USDT)
- spread = (26034.86 - 13950.53) / 13950.53 * 100 = 86.6%

**问题发现**：价差应该是 86%，但日志显示为 0%！

这说明初始价格记录后，后续循环使用的是相同的价格（±2% 波动太小导致计算结果接近 0）。

## 结论

测试框架本身是正确的，关键问题：

1. **环境问题**：Uvicorn 自动重载
2. **配置问题**：Mock Exchange 波动范围过小
3. **设计问题**：两个交易对价格量级差异太大（BTC vs ETH）

建议立即修改 Mock Exchange 或改用相同交易对（BTC/USDT 市场1 vs BTC/USDT 市场2）。