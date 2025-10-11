# 机器人详情查询API实现计划

## 任务概述
实现机器人详情页所需的三个查询API,使前端能够正常显示订单历史、持仓信息和价差曲线。

## 上下文
- **当前阶段**: Day 1-2 核心API完善
- **技术栈**: FastAPI + SQLAlchemy + Vue3 + Element Plus
- **方案**: 模拟数据快速验证方案

## 执行步骤

### 步骤1: 实现订单历史查询API
**文件**: `backend/app/api/v1/bots.py`
**路由**: `GET /api/v1/bots/{bot_id}/orders`
**参数**:
- page (默认1)
- page_size (默认20)
- status (可选: pending/open/closed/canceled)

**实现逻辑**:
1. 验证bot归属权限 (使用check_bot_ownership)
2. 查询orders表,筛选bot_instance_id
3. 应用状态筛选和分页
4. 如果无数据,生成3-5条模拟订单
5. 返回分页结果

**返回格式**:
```json
{
  "items": [Order],
  "total": 100,
  "page": 1,
  "page_size": 20
}
```

---

### 步骤2: 实现持仓查询API
**文件**: `backend/app/api/v1/bots.py`
**路由**: `GET /api/v1/bots/{bot_id}/positions`

**实现逻辑**:
1. 验证bot归属权限
2. 查询positions表,筛选is_open=True
3. 模拟当前价格 (entry_price * random(0.98, 1.02))
4. 计算未实现盈亏
5. 如果无持仓,生成2条模拟持仓

**返回格式**:
```json
[
  {
    "id": 1,
    "symbol": "BTC-USDT-SWAP",
    "side": "long",
    "amount": 0.1,
    "entry_price": 50000,
    "current_price": 50500,
    "unrealized_pnl": 50
  }
]
```

---

### 步骤3: 实现价差历史查询API
**文件**: `backend/app/api/v1/bots.py`
**路由**: `GET /api/v1/bots/{bot_id}/spread-history`
**参数**:
- start_time (可选,ISO格式)
- end_time (可选,ISO格式)
- 默认返回最近24小时

**实现逻辑**:
1. 验证bot归属权限
2. 查询spread_history表
3. 如果无数据,生成100个数据点
   - 使用随机游走算法
   - 时间间隔15分钟
   - 价差范围-2%~+2%
4. 返回时间序列数据

**返回格式**:
```json
[
  {
    "recorded_at": "2025-10-05T10:00:00Z",
    "spread_percentage": 1.25,
    "market1_price": 50500,
    "market2_price": 49800
  }
]
```

---

### 步骤4: 添加Schema定义
**新文件**: `backend/app/schemas/spread.py`

```python
from pydantic import BaseModel
from datetime import datetime
from decimal import Decimal

class SpreadHistoryResponse(BaseModel):
    id: int
    bot_instance_id: int
    market1_price: Decimal
    market2_price: Decimal
    spread_percentage: Decimal
    recorded_at: datetime

    model_config = ConfigDict(from_attributes=True)
```

---

### 步骤5: 创建模拟数据生成工具
**新文件**: `backend/app/utils/mock_data.py`

**函数清单**:
- `generate_mock_orders(bot: BotInstance, count: int) -> List[Order]`
- `generate_mock_positions(bot: BotInstance) -> List[Position]`
- `generate_spread_history(bot: BotInstance, hours: int) -> List[SpreadHistory]`

**设计原则**:
- 使用bot_id作为随机种子,保证数据可复现
- 生成数据符合bot配置 (投资额、杠杆等)
- 时间戳基于bot.start_time计算

---

### 步骤6: 前端API封装
**文件**: `frontend/src/common/apis/bots/index.ts`

**新增函数**:
```typescript
export const getBotOrders = (
  botId: number,
  params?: { page?: number; page_size?: number; status?: string }
) => {
  return request({
    url: `/api/v1/bots/${botId}/orders`,
    method: 'get',
    params
  }).then(unwrap)
}

export const getBotPositions = (botId: number) => {
  return request({
    url: `/api/v1/bots/${botId}/positions`,
    method: 'get'
  }).then(unwrap)
}

export const getSpreadHistory = (
  botId: number,
  params?: { start_time?: string; end_time?: string }
) => {
  return request({
    url: `/api/v1/bots/${botId}/spread-history`,
    method: 'get',
    params
  }).then(unwrap)
}
```

---

### 步骤7: 前端BotDetail.vue数据绑定
**文件**: `frontend/src/pages/bots/BotDetail.vue`

**修改内容**:
1. 在setup()中定义响应式变量
2. 创建loadOrders, loadPositions, loadSpreadHistory函数
3. 在onMounted钩子中调用
4. 绑定数据到表格和图表组件
5. 添加加载状态和错误处理

---

## 预期成果
- ✅ 三个API端点正常工作
- ✅ 前端详情页显示模拟数据
- ✅ 订单表格支持分页
- ✅ 价差图表显示24小时曲线
- ✅ 所有数据实时刷新

## 技术要点
- **SOLID**: 单一职责,每个API只负责一种查询
- **DRY**: 分页逻辑复用
- **KISS**: 模拟数据生成逻辑简单直接

## 开发时间
预计 6-8 小时

---

**创建时间**: 2025-10-05
**执行人**: AI Assistant
**状态**: 执行中
