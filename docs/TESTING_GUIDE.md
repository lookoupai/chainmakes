# ChainMakes 测试指南

## 概述

本文档描述了ChainMakes项目的测试策略、测试结构和如何运行测试。

## 测试架构

### 后端测试

后端使用pytest框架进行测试，包括：
- 单元测试：测试单个函数和类的功能
- 集成测试：测试API端点和数据库交互
- WebSocket测试：测试实时通信功能

### 前端测试

前端使用Vitest框架进行测试，包括：
- 组件测试：测试Vue组件的渲染和交互
- Composable测试：测试可复用逻辑函数
- 单元测试：测试工具函数和API调用

## 测试覆盖范围

### 后端测试覆盖

1. **API测试**
   - 用户认证API（注册、登录、修改密码）
   - 机器人管理API（创建、更新、删除、启停）
   - 交易所管理API（创建、更新、删除、验证）
   - 机器人详情API（订单历史、持仓、价差历史）

2. **业务逻辑测试**
   - 机器人引擎核心逻辑
   - 价差计算和交易触发条件
   - DCA策略实现
   - 持仓管理

3. **WebSocket测试**
   - 连接管理和认证
   - 实时数据推送
   - 错误处理和重连机制

4. **交易所集成测试**
   - 模拟交易所功能
   - 订单创建和管理
   - 持仓查询
   - 价格数据获取

### 前端测试覆盖

1. **组件测试**
   - 机器人列表组件
   - 机器人详情组件
   - 创建/编辑机器人表单
   - 交易所管理组件

2. **Composable测试**
   - WebSocket连接管理
   - API请求封装
   - 状态管理

3. **工具函数测试**
   - 数据格式化
   - 验证函数
   - 计算函数

## 运行测试

### 后端测试

1. **安装测试依赖**
   ```bash
   cd backend
   venv\Scripts\activate
   pip install -r requirements-test.txt
   ```

2. **运行所有测试**
   ```bash
   pytest
   ```

3. **运行特定测试文件**
   ```bash
   pytest tests/test_bots_api.py
   ```

4. **运行特定测试函数**
   ```bash
   pytest tests/test_bots_api.py::test_create_bot
   ```

5. **生成覆盖率报告**
   ```bash
   pytest --cov=app --cov-report=html
   ```

6. **使用测试脚本**
   ```bash
   python run_tests.py --cov --html
   ```

### 前端测试

1. **安装测试依赖**
   ```bash
   cd frontend
   pnpm install
   ```

2. **运行所有测试**
   ```bash
   pnpm test
   ```

3. **运行特定测试文件**
   ```bash
   pnpm test BotList.test.ts
   ```

4. **运行测试并监听变化**
   ```bash
   pnpm test:watch
   ```

5. **生成覆盖率报告**
   ```bash
   pnpm test:coverage
   ```

## 测试配置

### 后端测试配置

- **配置文件**: `backend/pytest.ini`
- **测试fixtures**: `backend/tests/conftest.py`
- **测试数据库**: 使用SQLite内存数据库

### 前端测试配置

- **配置文件**: `frontend/vitest.config.ts`
- **测试设置**: `frontend/tests/setup.ts`
- **模拟环境**: jsdom

## 编写新测试

### 后端测试示例

```python
@pytest.mark.asyncio
async def test_create_bot_with_valid_data(client: AsyncClient, auth_headers: dict, test_exchange):
    """测试使用有效数据创建机器人"""
    bot_data = {
        "name": "Test Bot",
        "symbol": "BTC/USDT",
        "base_exchange_id": test_exchange.id,
        "quote_exchange_id": test_exchange.id,
        "strategy_type": "spread",
        "min_spread_threshold": 0.01,
        "max_spread_threshold": 0.05,
        "trade_amount": 100.0
    }
    
    response = await client.post(
        "/api/v1/bots/",
        json=bot_data,
        headers=auth_headers
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == bot_data["name"]
```

### 前端测试示例

```typescript
import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import BotList from '@/pages/bots/BotList.vue'

describe('BotList', () => {
  it('renders correctly', () => {
    const wrapper = mount(BotList)
    expect(wrapper.exists()).toBe(true)
  })
  
  it('loads bots on mount', async () => {
    const wrapper = mount(BotList)
    await wrapper.vm.$nextTick()
    expect(wrapper.vm.bots.length).toBeGreaterThan(0)
  })
})
```

## 测试最佳实践

1. **测试命名**
   - 使用描述性的测试名称
   - 遵循`test_<功能>_<场景>`的命名约定

2. **测试结构**
   - 使用AAA模式（Arrange, Act, Assert）
   - 保持测试简单和专注
   - 每个测试只验证一个功能点

3. **测试数据**
   - 使用工厂模式创建测试数据
   - 避免硬编码测试数据
   - 使用fixtures共享测试数据

4. **模拟和存根**
   - 模拟外部依赖
   - 使用存根隔离测试
   - 避免测试外部系统

5. **断言**
   - 使用具体的断言
   - 验证状态而不是实现
   - 提供有意义的错误消息

## 持续集成

测试将在以下情况下自动运行：
- 每次提交代码时
- 创建拉取请求时
- 合并到主分支时

### 测试要求

- 所有测试必须通过
- 代码覆盖率不低于80%
- 不能有测试警告或错误

## 故障排除

### 常见问题

1. **测试数据库问题**
   ```bash
   rm backend/test_trading_bot.db
   ```

2. **依赖问题**
   ```bash
   pip install -r requirements-test.txt
   pnpm install
   ```

3. **异步测试问题**
   - 确保使用`@pytest.mark.asyncio`装饰器
   - 使用`await`等待异步操作

4. **前端测试问题**
   - 检查组件导入路径
   - 确保正确模拟依赖

## 测试报告

### 覆盖率报告

- 后端覆盖率：`backend/htmlcov/index.html`
- 前端覆盖率：`frontend/coverage/index.html`

### 测试结果

测试结果会在控制台显示，包括：
- 通过的测试数量
- 失败的测试数量
- 跳过的测试数量
- 执行时间

## 未来改进

1. **性能测试**
   - API响应时间测试
   - 负载测试
   - 压力测试

2. **端到端测试**
   - 使用Playwright或Cypress
   - 完整用户流程测试
   - 跨浏览器测试

3. **视觉回归测试**
   - UI组件截图对比
   - 响应式设计测试

4. **契约测试**
   - API契约验证
   - 前后端接口一致性测试