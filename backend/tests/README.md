# 测试文档

## 概述

本目录包含ChainMakes项目的所有测试代码，包括单元测试和集成测试。

## 测试结构

```
tests/
├── __init__.py              # 测试模块初始化
├── conftest.py              # pytest配置和共享fixtures
├── test_auth_api.py         # 用户认证API测试
├── test_bots_api.py         # 机器人API测试
├── test_exchanges_api.py    # 交易所API测试
├── test_bot_engine.py       # 机器人引擎测试
├── test_mock_exchange.py    # 模拟交易所测试
├── test_websocket.py        # WebSocket功能测试
└── README.md                # 本文档
```

## 运行测试

### 安装测试依赖

```bash
pip install -r requirements-test.txt
```

### 运行所有测试

```bash
# 使用pytest直接运行
pytest

# 或使用测试脚本
python run_tests.py
```

### 运行特定类型的测试

```bash
# 只运行单元测试
python run_tests.py --unit

# 只运行集成测试
python run_tests.py --integration
```

### 生成覆盖率报告

```bash
# 生成终端覆盖率报告
python run_tests.py --cov

# 生成HTML覆盖率报告
python run_tests.py --cov --html
```

### 运行特定测试文件

```bash
# 运行特定测试文件
python run_tests.py --file tests/test_bots_api.py

# 或使用pytest
pytest tests/test_bots_api.py
```

### 运行特定测试函数

```bash
# 运行特定测试函数
python run_tests.py --function test_create_bot

# 或使用pytest
pytest tests/test_bots_api.py::test_create_bot
```

### 详细输出

```bash
# 显示详细输出
python run_tests.py --verbose

# 或使用pytest
pytest -v
```

## 测试标记

我们使用pytest标记来分类测试：

- `asyncio`: 异步测试
- `unit`: 单元测试
- `integration`: 集成测试
- `slow`: 慢速测试

### 运行特定标记的测试

```bash
# 只运行单元测试
pytest -m unit

# 只运行集成测试
pytest -m integration

# 跳过慢速测试
pytest -m "not slow"
```

## Fixtures

测试中使用的主要fixtures：

- `client`: 测试HTTP客户端
- `db_session`: 测试数据库会话
- `test_user`: 测试用户
- `test_exchange`: 测试交易所
- `test_bot`: 测试机器人
- `auth_headers`: 认证头

## 编写新测试

### 添加新的API测试

1. 在相应的测试文件中添加新的测试函数
2. 使用`@pytest.mark.asyncio`装饰器标记异步测试
3. 使用适当的fixtures
4. 遵循命名约定：`test_<功能>_<场景>`

示例：

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

### 添加新的单元测试

1. 在相应的测试文件中添加新的测试函数
2. 使用`unittest.mock`模拟依赖
3. 测试单个函数或方法的行为

示例：

```python
@pytest.mark.asyncio
async def test_calculate_spread(bot_engine):
    """测试计算价差"""
    base_price = 50000.0
    quote_price = 50100.0
    
    spread = await bot_engine._calculate_spread(base_price, quote_price)
    
    assert spread == 100.0
    assert spread > 0
```

## 测试覆盖率

我们的目标是保持至少80%的测试覆盖率。可以通过以下命令查看覆盖率报告：

```bash
python run_tests.py --cov --html
```

然后在浏览器中打开`htmlcov/index.html`查看详细报告。

## 持续集成

测试将在每次提交时自动运行，确保代码质量。请确保在提交代码前运行所有测试并通过。

## 故障排除

### 测试数据库问题

如果遇到数据库相关错误，尝试删除测试数据库文件：

```bash
rm test_trading_bot.db
```

### 异步测试问题

确保所有异步测试函数都使用了`@pytest.mark.asyncio`装饰器。

### 依赖问题

确保安装了所有测试依赖：

```bash
pip install -r requirements-test.txt
```

## 最佳实践

1. 保持测试简单和专注
2. 使用描述性的测试名称
3. 测试正常情况和异常情况
4. 使用适当的fixtures
5. 保持测试独立性
6. 定期运行测试以确保代码质量