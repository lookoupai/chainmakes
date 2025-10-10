# 🚨 关键修复速查表

**日期**: 2025-10-10
**状态**: ✅ 所有关键问题已修复
**优先级**: 🔴🔴 必读

---

## ⚠️ 最严重的Bug（已修复）

### Bug #12: 盈亏计算严重错误

**问题**: 自己计算盈亏不准确，导致错误的止盈/止损决策

**实际案例**:
```
错误计算显示: 盈利 10.18% → 触发止盈
真实盈亏显示: 亏损 -0.54% → 不应该止盈
结果: 在亏损时错误平仓！
```

**修复**:
- 文件: `backend/app/core/bot_engine.py` 第 1031-1097 行
- 方法: `update_position_prices()`
- 修改: **使用交易所返回的真实 `unrealizedPnl`**

**关键代码**:
```python
# ❌ 错误做法（修复前）
unrealized_pnl = (current_price - entry_price) * amount

# ✅ 正确做法（修复后）
exchange_position = await self.exchange.get_position(position.symbol)
position.unrealized_pnl = exchange_position['unrealized_pnl']  # 使用交易所真实值
```

**为什么自己算不准确**:
- 未考虑杠杆
- 未考虑资金费率（每8小时结算）
- 未考虑交易手续费
- 合约计算复杂，简单相减完全不准

---

## 🔴 其他高优先级修复

### 1. 持仓方向混淆

**问题**: 数据库存储 `side='buy'/'sell'`（订单方向），但 OKX 需要 `'long'/'short'`（持仓方向）

**修复**:
- 开仓时转换: `bot_engine.py:987-1009`
- 平仓时兼容: `bot_engine.py:731-747`

```python
# 开仓时转换
position_side = 'long' if side == 'buy' else 'short'

# 平仓时兼容
if position.side in ['buy', 'long']:
    close_side = 'sell'
else:
    close_side = 'buy'
```

**数据库修正**: 运行 `python scripts/fix_position_side.py`

---

### 2. 合约仓位计算错误

**问题**: 未考虑杠杆，导致配对仓位不对等

**修复**: `bot_engine.py:493-521`

```python
# ❌ 错误
market1_amount = investment_per_order / market1_price

# ✅ 正确
margin = investment_per_order * multiplier
contract_value = margin * leverage  # 关键：乘以杠杆
market1_amount = contract_value / market1_price
```

---

### 3. 平仓精度问题

**问题**: 使用数据库数量，可能与交易所不一致

**修复**: `bot_engine.py:720-828`

```python
# 从交易所获取实际数量
exchange_position = await self.exchange.get_position(position.symbol)
actual_amount = exchange_position['amount']

# 使用实际数量平仓
order = await self.exchange.create_market_order(
    position.symbol,
    close_side,
    actual_amount,  # 不再用数据库的量
    reduce_only=True
)
```

---

## 🟡 中优先级修复

### 4. 数据同步缺失 amount 更新

**修复**: `data_sync_service.py:196-219`

```python
# 新增：同步持仓数量
db_pos.amount = exchange_pos['amount']
db_pos.current_price = exchange_pos['current_price']
db_pos.unrealized_pnl = exchange_pos['unrealized_pnl']
```

---

### 5. 止盈止损计算（DCA 倍投）

**问题**: 未考虑 DCA 倍投的 multiplier

**修复**: `bot_engine.py:680-700`

```python
def _calculate_total_investment(self):
    total = Decimal('0')
    for i in range(self.bot.current_dca_count):
        multiplier = Decimal(str(self.bot.dca_config[i]['multiplier']))
        total += self.bot.investment_per_order * multiplier
    return total
```

---

## 📋 完整修复列表

| # | 问题 | 严重性 | 文件 | 状态 |
|---|------|--------|------|------|
| 1 | OKX 双向持仓参数 | 🔴 | okx_exchange.py:108-129 | ✅ |
| 2 | Decimal 转换 | 🟡 | okx_exchange.py:240-264 | ✅ |
| 3 | 缺少 current_price | 🟡 | okx_exchange.py:267-284 | ✅ |
| 4 | 缺少 cycle_number | 🟡 | data_sync_service.py:217-245 | ✅ |
| 5 | 合约仓位计算 | 🔴 | bot_engine.py:493-521 | ✅ |
| 6 | 止盈止损计算 | 🔴 | bot_engine.py:680-700 | ✅ |
| 7 | 状态未重置 | 🟡 | bot_engine.py:312-336 | ✅ |
| 8 | 停止不平仓 | 🟡 | BotDetail.vue:542-577 | ✅ |
| 9 | 平仓精度 | 🟡 | bot_engine.py:720-828 | ✅ |
| 10 | 数据同步缺失 | 🟡 | data_sync_service.py:196-219 | ✅ |
| 11 | 持仓方向混淆 | 🔴 | bot_engine.py:731-747, 987-1009 | ✅ |
| 12 | **盈亏计算错误** | 🔴🔴 | **bot_engine.py:1031-1097** | ✅ |
| 13 | 优雅关闭 | 🟢 | bot_engine.py:121-131 | ✅ |

---

## 🔧 辅助工具

### 诊断脚本
```bash
# 检查持仓状态
python scripts/check_positions.py

# 修正持仓方向
python scripts/fix_position_side.py
```

### 查看详细盈亏日志
启动机器人后，日志会显示：
```
[盈亏详情] 保证金投资=300.00 USDT, 总盈亏=-1.63 USDT, 盈亏比例=-0.54%
  - SOL/USDT:USDT (long): 数量=16.94, 入场价=221.77, 当前价=218.87, 盈亏=-49.15 USDT
  - LTC/USDT:USDT (short): 数量=28.8, 入场价=131.11, 当前价=129.46, 盈亏=47.52 USDT
```

---

## ⚠️ 重要提醒

### 关于盈亏计算
**永远不要自己计算合约盈亏！**

合约交易盈亏涉及：
- 杠杆倍数
- 资金费率（每8小时结算）
- 开仓/平仓手续费
- 标记价格 vs 最新价格
- 风险限额调整

**正确做法**：
```python
# ✅ 使用交易所提供的 unrealizedPnl
exchange_pos = await exchange.get_position(symbol)
unrealized_pnl = exchange_pos['unrealized_pnl']
```

### 关于持仓方向
- **订单方向**: `'buy'` / `'sell'`（下单用）
- **持仓方向**: `'long'` / `'short'`（存储用）

数据库存储持仓时，必须用 `'long'/'short'`！

---

## 📚 详细文档

完整详细说明请查看：
- [开发进度 2025-10-10](DEVELOPMENT_PROGRESS_2025-10-10.md)
- [OKX 集成指南](OKX_INTEGRATION_GUIDE.md)
- [技术架构文档](technical-architecture.md)

---

**文档版本**: v1.0
**最后更新**: 2025-10-10 16:00
**维护者**: AI 开发助手
