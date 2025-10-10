
# 加密货币配对交易机器人 - 技术架构设计

## 一、系统架构概述

### 1.1 整体架构
```
┌─────────────────────────────────────────────────────────────┐
│                      Web管理界面 (前端)                        │
│                  Vue 3 + Element Plus + ECharts              │
└───────────────────────────┬─────────────────────────────────┘
                            │ HTTP/WebSocket
┌───────────────────────────┴─────────────────────────────────┐
│                       API网关层                               │
│              FastAPI + JWT认证 + WebSocket                   │
└───────────────────────────┬─────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
┌───────▼────────┐  ┌──────▼───────┐  ┌───────▼────────┐
│   交易引擎      │  │  用户管理     │  │   数据分析     │
│   服务         │  │   服务       │  │    服务        │
└───────┬────────┘  └──────────────┘  └────────────────┘
        │
┌───────▼────────┐
│  交易所接口层   │
│    (CCXT)      │
└───────┬────────┘
        │
┌───────▼────────────────────────────┐
│   交易所 (OKX/Binance/Bybit等)      │
└────────────────────────────────────┘
```

### 1.2 技术栈选择

#### 后端技术栈
- **主框架**: Python 3.11+ (FastAPI)
- **异步任务**: Celery + Redis
- **数据库**: PostgreSQL (主数据) + Redis (缓存/消息队列)
- **ORM**: SQLAlchemy 2.0
- **交易所接口**: CCXT (支持多交易所统一API)
- **认证**: JWT (JSON Web Token)
- **WebSocket**: FastAPI WebSocket支持实时推送

#### 前端技术栈
- **框架**: Vue 3 (Composition API)
- **UI库**: Element Plus
- **状态管理**: Pinia
- **图表**: ECharts
- **HTTP客户端**: Axios
- **WebSocket客户端**: native WebSocket API

#### 推荐使用开源中后台管理系统方案

**推荐方案**: 使用 **Vue3-Element-Admin** 或 **Vben Admin** 作为基础模板

**理由**:
1. **开发效率高**: 已集成完整的用户系统、权限管理、路由守卫
2. **成熟稳定**: 经过大量项目验证,代码质量高
3. **功能齐全**: 包含登录、注册、权限控制、菜单管理、多标签页等
4. **易于定制**: 组件化设计,便于根据需求修改
5. **节省时间**: 相比从零开发,可节省2-3周开发时间

**替代方案**: 如果团队更熟悉React,可选择 **Ant Design Pro**

## 二、数据库设计

### 2.1 核心数据表

```sql
-- 用户表
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    role VARCHAR(20) DEFAULT 'user' -- admin, user
);

-- 交易所账户配置表
CREATE TABLE exchange_accounts (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    exchange_name VARCHAR(50) NOT NULL, -- okx, binance, bybit
    api_key VARCHAR(255) NOT NULL,
    api_secret VARCHAR(255) NOT NULL,
    passphrase VARCHAR(255), -- OKX需要
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, exchange_name)
);

-- 交易机器人实例表
CREATE TABLE bot_instances (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    exchange_account_id INTEGER REFERENCES exchange_accounts(id) ON DELETE CASCADE,
    bot_name VARCHAR(100) NOT NULL,
    
    -- 基础配置
    market1_symbol VARCHAR(50) NOT NULL, -- 例如: GALA-USDT
    market2_symbol VARCHAR(50) NOT NULL, -- 例如: CHZ-USDT
    start_time TIMESTAMP NOT NULL, -- 统计开始时间(UTC)
    leverage INTEGER DEFAULT 10,
    
    -- 交易配置
    order_type_open VARCHAR(20) DEFAULT 'market', -- market, limit
    order_type_close VARCHAR(20) DEFAULT 'market',
    investment_per_order DECIMAL(18, 8) NOT NULL, -- 每单投资额
    max_position_value DECIMAL(18, 8) NOT NULL, -- 最大持仓面值
    
    -- DCA配置
    max_dca_times INTEGER DEFAULT 6, -- 最大加仓次数
    dca_config JSONB, -- [{times: 1, spread: 1.0, multiplier: 1.0}, ...]
    
    -- 止盈止损配置
    profit_mode VARCHAR(20) DEFAULT 'position', -- regression, position
    profit_ratio DECIMAL(10, 4) DEFAULT 1.0, -- 止盈比例(%)
    stop_loss_ratio DECIMAL(10, 4) DEFAULT 10.0, -- 止损比例(%)
    
    -- 状态控制
    status VARCHAR(20) DEFAULT 'stopped', -- running, paused, stopped
    pause_after_close BOOLEAN DEFAULT TRUE, -- 平仓后暂停
    
    -- 运行数据
    current_cycle INTEGER DEFAULT 0, -- 当前循环次数
    total_profit DECIMAL(18, 8) DEFAULT 0, -- 总收益
    total_trades INTEGER DEFAULT 0, -- 总交易次数
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 交易订单表
CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    bot_instance_id INTEGER REFERENCES bot_instances(id) ON DELETE CASCADE,
    cycle_number INTEGER NOT NULL, -- 循环编号
    
    -- 订单信息
    exchange_order_id VARCHAR(100), -- 交易所返回的订单ID
    symbol VARCHAR(50) NOT NULL,
    side VARCHAR(10) NOT NULL, -- buy, sell
    order_type VARCHAR(20) NOT NULL, -- market, limit
    
    -- 价格和数量
    price DECIMAL(18, 8),
    amount DECIMAL(18, 8) NOT NULL,
    filled_amount DECIMAL(18, 8) DEFAULT 0,
    cost DECIMAL(18, 8), -- 成交金额
    
    -- 订单状态
    status VARCHAR(20) DEFAULT 'pending', -- pending, open, closed, canceled
    dca_level INTEGER DEFAULT 1, -- 第几次加仓
    
    -- 时间戳
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    filled_at TIMESTAMP
);

-- 持仓记录表
CREATE TABLE positions (
    id SERIAL PRIMARY KEY,
    bot_instance_id INTEGER REFERENCES bot_instances(id) ON DELETE CASCADE,
    cycle_number INTEGER NOT NULL,
    
    -- 持仓信息
    symbol VARCHAR(50) NOT NULL,
    side VARCHAR(10) NOT NULL, -- long, short
    amount DECIMAL(18, 8) NOT NULL, -- 持仓数量
    entry_price DECIMAL(18, 8) NOT NULL, -- 开仓均价
    current_price DECIMAL(18, 8), -- 当前价格
    unrealized_pnl DECIMAL(18, 8), -- 未实现盈亏
    
    -- 状态
    is_open BOOLEAN DEFAULT TRUE,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    closed_at TIMESTAMP
);

-- 交易日志表
CREATE TABLE trade_logs (
    id SERIAL PRIMARY KEY,
    bot_instance_id INTEGER REFERENCES bot_instances(id) ON DELETE CASCADE,
    log_type VARCHAR(50) NOT NULL, -- info, warning, error, trade
    message TEXT NOT NULL,
    details JSONB, -- 额外详细信息
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 价差历史记录表 (用于分析和图表展示)
CREATE TABLE spread_history (
    id SERIAL PRIMARY KEY,
    bot_instance_id INTEGER REFERENCES bot_instances(id) ON DELETE CASCADE,
    
    market1_price DECIMAL(18, 8) NOT NULL,
    market2_price DECIMAL(18, 8) NOT NULL,
    spread_percentage DECIMAL(10, 4) NOT NULL, -- 价差百分比
    
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_bot_time (bot_instance_id, recorded_at)
);
```

### 2.2 索引优化

```sql
-- 提高查询性能的索引
CREATE INDEX idx_bot_instances_user_id ON bot_instances(user_id);
CREATE INDEX idx_bot_instances_status ON bot_instances(status);
CREATE INDEX idx_orders_bot_instance ON orders(bot_instance_id, cycle_number);
CREATE INDEX idx_positions_bot_instance ON positions(bot_instance_id, is_open);
CREATE INDEX idx_trade_logs_bot_time ON trade_logs(bot_instance_id, created_at DESC);
```

## 三、后端核心模块设计

### 3.1 项目结构

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI应用入口
│   ├── config.py               # 配置管理
│   ├── dependencies.py         # 依赖注入
│   │
│   ├── api/                    # API路由层
│   │   ├── __init__.py
│   │   ├── v1/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py         # 认证相关API
│   │   │   ├── users.py        # 用户管理API
│   │   │   ├── exchanges.py   # 交易所账户API
│   │   │   ├── bots.py         # 机器人管理API
│   │   │   ├── orders.py       # 订单查询API
│   │   │   └── websocket.py   # WebSocket实时数据
│   │
│   ├── core/                   # 核心业务逻辑
│   │   ├── __init__.py
│   │   ├── security.py         # 安全相关(JWT, 密码)
│   │   ├── exchange_factory.py # 交易所工厂类
│   │   └── bot_engine.py       # 交易机器人引擎
│   │
│   ├── models/                 # 数据库模型(SQLAlchemy)
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── exchange_account.py
│   │   ├── bot_instance.py
│   │   ├── order.py
│   │   ├── position.py
│   │   └── trade_log.py
│   │
│   ├── schemas/                # Pydantic数据验证模型
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── exchange.py
│   │   ├── bot.py
│   │   └── order.py
│   │
│   ├── services/               # 业务服务层
│   │   ├── __init__.py
│   │   ├── auth_service.py
│   │   ├── user_service.py
│   │   ├── exchange_service.py
│   │   ├── bot_service.py
│   │   ├── order_service.py
│   │   └── spread_calculator.py
│   │
│   ├── exchanges/              # 交易所适配器
│   │   ├── __init__.py
│   │   ├── base_exchange.py    # 抽象基类
│   │   ├── okx_exchange.py     # OKX适配器
│   │   ├── binance_exchange.py # Binance适配器(预留)
│   │   └── bybit_exchange.py   # Bybit适配器(预留)
│   │
│   ├── strategies/             # 交易策略
│   │   ├── __init__.py
│   │   ├── base_strategy.py
│   │   └── spread_arbitrage.py # 价差套利策略
│   │
│   ├── tasks/                  # Celery异步任务
│   │   ├── __init__.py
│   │   ├── bot_tasks.py        # 机器人执行任务
│   │   └── monitor_tasks.py    # 监控任务
│   │
│   ├── db/                     # 数据库相关
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── session.py
│   │   └── init_db.py
│   │
│   └── utils/                  # 工具函数
│       ├── __init__.py
│       ├── logger.py
│       ├── encryption.py       # API密钥加密
│       └── validators.py
│
├── tests/                      # 测试
├── alembic/                    # 数据库迁移
├── requirements.txt
└── .env.example
```

### 3.2 核心类设计

#### 3.2.1 交易所基类 (BaseExchange)

```python
from abc import ABC, abstractmethod
from typing import Dict, List, Optional
import ccxt

class BaseExchange(ABC):
    """交易所抽象基类"""
    
    def __init__(self, api_key: str, api_secret: str, passphrase: Optional[str] = None):
        self.api_key = api_key
        self.api_secret = api_secret
        self.passphrase = passphrase
        self.exchange = self._init_exchange()
    
    @abstractmethod
    def _init_exchange(self) -> ccxt.Exchange:
        """初始化交易所实例"""
        pass
    
    @abstractmethod
    async def get_ticker(self, symbol: str) -> Dict:
        """获取行情"""
        pass
    
    @abstractmethod
    async def create_order(self, symbol: str, order_type: str, 
                          side: str, amount: float, price: Optional[float] = None) -> Dict:
        """创建订单"""
        pass
    
    @abstractmethod
    async def cancel_order(self, order_id: str, symbol: str) -> Dict:
        """取消订单"""
        pass
    
    @abstractmethod
    async def get_position(self, symbol: str) -> Dict:
        """获取持仓"""
        pass
    
    @abstractmethod
    async def set_leverage(self, symbol: str, leverage: int) -> Dict:
        """设置杠杆"""
        pass
```

#### 3.2.2 OKX交易所适配器

```python
import ccxt.async_support as ccxt
from .base_exchange import BaseExchange

class OKXExchange(BaseExchange):
    """OKX交易所适配器"""
    
    def _init_exchange(self) -> ccxt.Exchange:
        return ccxt.okx({
            'apiKey': self.api_key,
            'secret': self.api_secret,
            'password': self.passphrase,
            'enableRateLimit': True,
            'options': {
                'defaultType': 'swap',  # 永续合约
            }
        })
    
    async def get_ticker(self, symbol: str) -> Dict:
        """获取OKX行情"""
        ticker = await self.exchange.fetch_ticker(symbol)
        return {
            'symbol': symbol,
            'last_price': ticker['last'],
            'timestamp': ticker['timestamp']
        }
    
    async def create_order(self, symbol: str, order_type: str,
                          side: str, amount: float, price: Optional[float] = None) -> Dict:
        """在OKX创建订单"""
        order = await self.exchange.create_order(
            symbol=symbol,
            type=order_type,
            side=side,
            amount=amount,
            price=price
        )
        return order
    
    # ... 其他方法实现
```

#### 3.2.3 交易机器人引擎 (BotEngine)

```python
import asyncio
from typing import Optional
from decimal import Decimal
from datetime import datetime, timezone

class BotEngine:
    """交易机器人核心引擎"""
    
    def __init__(self, bot_instance: BotInstance, exchange: BaseExchange):
        self.bot = bot_instance
        self.exchange = exchange
        self.is_running = False
        self.current_cycle = 0
        self.dca_count = 0
    
    async def start(self):
        """启动机器人"""
        self.is_running = True
        self.bot.status = 'running'
        
        while self.is_running:
            try:
                await self._execute_cycle()
                await asyncio.sleep(5)  # 每5秒检查一次
            except Exception as e:
                await self._log_error(f"执行错误: {str(e)}")
                if self.bot.pause_after_close:
                    await self.pause()
    
    async def _execute_cycle(self):
        """执行一个交易循环"""
        # 1. 获取当前市场价格
        market1_price = await self._get_market_price(self.bot.market1_symbol)
        market2_price = await self._get_market_price(self.bot.market2_symbol)
        
        # 2. 计算价差
        spread = self._calculate_spread(market1_price, market2_price)
        
        # 3. 记录价差历史
        await self._record_spread(market1_price, market2_price, spread)
        
        # 4. 检查是否需要开仓/加仓
        if await self._should_open_position(spread):
            await self._open_position(market1_price, market2_price)
        
        # 5. 检查是否需要止盈
        if await self._should_take_profit():
            await self._close_all_positions()
        
        # 6. 检查是否需要止损
        if await self._should_stop_loss():
            await self._close_all_positions()
    
    def _calculate_spread(self, price1: float, price2: float) -> float:
        """
        计算价差百分比
        公式: ((price1/start_price1) - (price2/start_price2)) * 100
        """
        # 从统计开始时间计算涨跌幅
        change1 = (price1 / self.bot.market1_start_price - 1) * 100
        change2 = (price2 / self.bot.market2_start_price - 1) * 100
        return change1 - change2
    
    async def _should_open_position(self, current_spread: float) -> bool:
        """判断是否应该开仓"""
        if self.dca_count >= self.bot.max_dca_times:
            return False
        
        # 获取当前DCA配置
        dca_config = self.bot.dca_config[self.dca_count]
        target_spread = dca_config['spread']
        
        # 检查价差是否达到开仓阈值
        if abs(current_spread - self.last_trade_spread) >= target_spread:
            return True
        
        return False
    
    async def _open_position(self, price1: float, price2: float):
        """开仓操作"""
        # 确定做多/做空方向
        if price1 > price2:  # 简化的逻辑,实际需要更复杂的判断
            market1_side = 'sell'  # 做空涨幅高的
            market2_side = 'buy'   # 做多涨幅低的
        else:
            market1_side = 'buy'
            market2_side = 'sell'
        
        # 获取投资金额(考虑倍投)
        dca_config = self.bot.dca_config[self.dca_count]
        amount = self.bot.investment_per_order * dca_config['multiplier']
        
        # 下单
        order1 = await self.exchange.create_order(
            self.bot.market1_symbol,
            self.bot.order_type_open,
            market1_side,
            amount / price1
        )
        
        order2 = await self.exchange.create_order(
            self.bot.market2_symbol,
            self.bot.order_type_open,
            market2_side,
            amount / price2
        )
        
        # 记录订单
        await self._save_orders([order1, order2])
        
        self.dca_count += 1
    
    async def _should_take_profit(self) -> bool:
        """判断是否应该止盈"""
        if self.bot.profit_mode == 'position':
            # 仓位止盈模式
            total_pnl = await self._calculate_total_pnl()
            total_investment = self._calculate_total_investment()
            profit_ratio = (total_pnl / total_investment) * 100
            
            return profit_ratio >= self.bot.profit_ratio
        else:
            # 回归止盈模式
            current_spread = await self._get_current_spread()
            spread_diff = abs(self.first_trade_spread - current_spread)
            
            return spread_diff >= self.bot.profit_ratio
    
    async def _close_all_positions(self):
        """平仓所有持仓"""
        positions = await self._get_open_positions()
        
        for position in positions:
            await self.exchange.create_order(
                position.symbol,
                self.bot.order_type_close,
                'buy' if position.side == 'short' else 'sell',
                position.amount
            )
        
        # 重置循环状态
        self.current_cycle += 1
        self.dca_count = 0
        
        if self.bot.pause_after_close:
            await self.pause()
```

### 3.3 API接口设计

#### 3.3.1 认证相关 API

```python
# app/api/v1/auth.py
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm

router = APIRouter(prefix="/auth", tags=["认证"])

@router.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """用户登录"""
    pass

@router.post("/register")
async def register(user_data: UserCreate):
    """用户注册"""
    pass

@router.post("/refresh")
async def refresh_token(refresh_token: str):
    """刷新访问令牌"""
    pass
```

#### 3.3.2 机器人管理 API

```python
# app/api/v1/bots.py
from fastapi import APIRouter, Depends, HTTPException
from typing import List

router = APIRouter(prefix="/bots", tags=["交易机器人"])

@router.post("/")
async def create_bot(bot_config: BotCreate, current_user: User = Depends(get_current_user)):
    """创建新的交易机器人"""
    pass

@router.get("/")
async def list_bots(current_user: User = Depends(get_current_user)) -> List[BotResponse]:
    """获取用户的所有机器人"""
    pass

@router.get("/{bot_id}")
async def get_bot(bot_id: int, current_user: User = Depends(get_current_user)):
    """获取指定机器人详情"""
    pass

@router.put("/{bot_id}")
async def update_bot(bot_id: int, bot_config: BotUpdate, 
                    current_user: User = Depends(get_current_user)):
    """更新机器人配置"""
    pass

@router.delete("/{bot_id}")
async def delete_bot(bot_id: int, current_user: User = Depends(get_current_user)):
    """删除机器人"""
    pass

@router.post("/{bot_id}/start")
async def start_bot(bot_id: int, current_user: User = Depends(get_current_user)):
    """启动机器人"""
    pass

@router.post("/{bot_id}/pause")
async def pause_bot(bot_id: int, current_user: User = Depends(get_current_user)):
    """暂停机器人"""
    pass

@router.post("/{bot_id}/stop")
async def stop_bot(bot_id: int, current_user: User = Depends(get_current_user)):
    """停止机器人"""
    pass

@router.get("/{bot_id}/orders")
async def get_bot_orders(bot_id: int, current_user: User = Depends(get_current_user)):
    """获取机器人的订单历史"""
    pass

@router.get("/{bot_id}/positions")
async def get_bot_positions(bot_id: int, current_user: User = Depends(get_current_user)):
    """获取机器人的当前持仓"""
    pass

@router.get("/{bot_id}/spread-history")
async def get_spread_history(bot_id: int, current_user: User = Depends(get_current_user)):
    """获取价差历史数据(用于图表)"""
    pass
```

#### 3.3.3 WebSocket 实时推送

```python
# app/api/v1/websocket.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[int, List[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, bot_id: int):
        await websocket.accept()
        if bot_id not in self.active_connections:
            self.active_connections[bot_id] = []
        self.active_connections[bot_id].append(websocket)
    
    async def disconnect(self, websocket: WebSocket, bot_id: int):
        self.active_connections[bot_id].remove(websocket)
    
    async def broadcast(self, bot_id: int, message: dict):
        if bot_id in self.active_connections:
            for connection in self.active_connections[bot_id]:
                await connection.send_json(message)

manager = ConnectionManager()

@router.websocket("/ws/bot/{bot_id}")
async def websocket_endpoint(websocket: WebSocket, bot_id: int):
    """WebSocket连接端点,实时推送机器人状态"""
    await manager.connect(websocket, bot_id)
    try:
        while True:
            # 接收客户端消息(如果需要)
            data = await websocket.receive_text()
            
            # 这里可以根据需要处理客户端消息
            
    except WebSocketDisconnect:
        await manager.disconnect(websocket, bot_id)
```

## 四、前端设计

### 4.1 页面结构

```
frontend/
├── src/
│   ├── views/
│   │   ├── login/              # 登录页
│   │   ├── dashboard/          # 仪表板(总览)
│   │   ├── bots/
│   │   │   ├── BotList.vue     # 机器人列表
│   │   │   ├── BotCreate.vue   # 创建机器人
│   │   │   ├── BotEdit.vue     # 编辑机器人
│   │   │   └── BotDetail.vue   # 机器人详情
│   │   ├── exchanges/          # 交易所账户管理
│   │   ├── orders/             # 订单历史
│   │   └── settings/           # 系统设置
│   │
│   ├── components/
│   │   ├── BotCard.vue         # 机器人卡片组件
│   │   ├── SpreadChart.vue     # 价差图表组件
│   │   ├── OrderTable.vue      # 订单表格组件
│   │   └── PositionPanel.vue   # 持仓面板组件
│   │
│   ├── api/
│   │   ├── auth.ts
│   │   ├── bot.ts
│   │   ├── exchange.ts
│   │   └── websocket.ts
│   │
│   ├── stores/
│   │   ├── auth.ts
│   │   ├── bot.ts
│   │   └── websocket.ts
│   │
│   ├── router/
│   │   └── index.ts
│   │
│   └── utils/
│       ├── request.ts          # Axios封装
│       └── auth.ts             # 认证工具
```

### 4.2 关键组件设计

#### 4.2.1 机器人配置表单

```vue
<!-- BotCreate.vue -->
<template>
  <el-form :model="botForm" :rules="rules" ref="formRef">
    <!-- 交易所选择 -->
    <el-form-item label="交易所" prop="exchangeAccountId">
      <el-select v-model="botForm.exchangeAccountId">
        <el-option 
          v-for="exchange in exchanges" 
          :key="exchange.id"
          :label="exchange.exchangeName"
          :value="exchange.id" />
      </el-select>
    </el-form-item>
    
    <!-- 统计开始时间 -->
    <el-form-item label="统计开始时间(UTC)" prop="startTime">
      <el-date-picker 
        v-model="botForm.startTime"
        type="datetime"
        :timezone="'UTC'" />
    </el-form-item>
    
    <!-- 市场1配置 -->
    <el-form-item label="市场1" prop="market1Symbol">
      <el-select v-model="botForm.market1Symbol" filterable>
        <el-option 
          v-for="symbol in availableSymbols"
          :key="symbol"
          :label="symbol"
          :value="symbol" />
      </el-select>
    </el-form-item>
    
    <!-- 交易方向 -->
    <el-form-item label="市场1方向" prop="market1Direction">
      <el-select v-model="botForm.market1Direction">
        <el-option label="做多(BUY)" value="buy" />
        <el-option label="做空(SELL)" value="sell" />
      </el-select>
    </el-form-item>
    
    <!-- 市场2配置(类似市场1) -->
    
    <!-- 杠杆选择 -->
    <el-form-item label="杠杆倍数" prop="leverage">
      <el-radio-group v-model="botForm.leverage">
        <el-radio :label="1">1x</el-radio>
        <el-radio :label="2">2x</el-radio>
        <el-radio :label="3">3x</el-radio>
        <el-radio :label="5">5x</el-radio>
        <el-radio :label="10">10x</el-radio>
        <el-radio :label="20">20x</el-radio>
      </el-radio-group>
    </el-form-item>
    
    <!-- DCA配置 -->
    <el-form-item label="下单次数" prop="maxDcaTimes">
      <el-input-number v-model="botForm.maxDcaTimes" :min="1" :max="10" />
    </el-form-item>
    
    <!-- DCA详细配置表格 -->
    <el-table :data="botForm.dcaConfig">
      <el-table-column label="次数" prop="times" />
      <el-table-column label="下单价差(%)">
        <template #default="{ row }">
          <el-input-number v-model="row.spread" :step="0.1" />
        </template>
      </el-table-column>
      <el-table-column label="倍投倍数">
        <template #default="{ row }">
          <el-input-number v-model="row.multiplier" :step="0.1" />
        </template>
      </el-table-column>
    </el-table>
    
    <!-- 止盈止损配置 -->
    <el-form-item label="止盈模式" prop="profitMode">
      <el-radio-group v-model="botForm.profitMode">
        <el-radio label="regression">回归止盈</el-radio>
        <el-radio label="position">仓位止盈</el-radio>
      </el-radio-group>
    </el-form-item>
    
    <el-form-item label="止盈比例(%)" prop="profitRatio">
      <el-input-number v-model="botForm.profitRatio" :step="0.1" />
    </el-form-item>
    
    <el-form-item label="止损比例(%)" prop="stopLossRatio">
      <el-input-number v-model="botForm.stopLossRatio" :step="0.1" />
    </el-form-item>
    
    <!-- 提交按钮 -->
    <el-form-item>
      <el-button type="primary" @click="submitForm">创建机器人</el-button>
      <el-button @click="resetForm">重置</el-button>
    </el-form-item>
  </el-form>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { createBot } from '@/api/bot'

const botForm = reactive({
  exchangeAccountId: null,
  market1Symbol: '',
  market2Symbol: '',
  startTime: new Date(),
  leverage: 10,
  maxDcaTimes: 6,
  dcaConfig: [],
  profitMode: 'position',
  profitRatio: 1.0,
  stopLossRatio: 10.0
})

const submitForm = async () => {
  // 表单验证和提交
  await createBot(botForm)
}
</script>
```

#### 4.2.2 价差图表组件

```vue
<!-- SpreadChart.vue -->
<template>
  <div ref="chartRef" style="width: 100%; height: 400px;"></div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import * as echarts from 'echarts'

const props = defineProps<{
  data: Array<{timestamp: string, spread: number}>
}>()

const chartRef = ref<HTMLElement>()
let chartInstance: echarts.ECharts

onMounted(() => {
  chartInstance = echarts.init(chartRef.value!)
  updateChart()
})

watch(() => props.data, () => {
  updateChart()
})

const updateChart = () => {
  const option = {
    title: { text: '价差历史' },
    tooltip: { trigger: 'axis' },
    xAxis: {
      type: 'category',
      data: props.data.map(d => d.timestamp)
    },
    yAxis: {
      type: 'value',
      name: '价差(%)'
    },
    series: [{
      name: '价差',
      type: 'line',
      data: props.data.map(d => d.spread),
      smooth: true
    }]
  }
  chartInstance.setOption(option)
}
</script>
```

#### 4.2.3 实时WebSocket连接

```typescript
// stores/websocket.ts
import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useWebSocketStore = defineStore('websocket', () => {
  const connections = ref<Map<number, WebSocket>>(new Map())
  
  const connect = (botId: number) => {
    const ws = new WebSocket(`ws://localhost:8000/api/v1/ws/bot/${botId}`)
    
    ws.onopen = () => {
      console.log(`WebSocket连接已建立: Bot ${botId}`)
    }
    
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data)
      // 处理实时数据更新
      handleRealtimeUpdate(botId, data)
    }
    
    ws.onerror = (error) => {
      console.error('WebSocket错误:', error)
    }
    
    ws.onclose = () => {
      console.log(`WebSocket连接已关闭: Bot ${botId}`)
      connections.value.delete(botId)
    }
    
    connections.value.set(botId, ws)
  }
  
  const disconnect = (botId: number) => {
    const ws = connections.value.get(botId)
    if (ws) {
      ws.close()
      connections.value.delete(botId)
    }
  }
  
  const handleRealtimeUpdate = (botId: number, data: any) => {
    // 根据数据类型更新对应的store
    switch(data.type) {
      case 'spread_update':
        // 更新价差数据
        break
      case 'order_update':
        // 更新订单状态
        break
      case 'position_update':
        // 更新持仓信息
        break
    }
  }
  
  return { connect, disconnect }
})
```

## 五、部署方案

### 5.1 开发环境

```yaml
# docker-compose.dev.yml
version: '3.8'

services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: trading_bot
      POSTGRES_USER: admin
      POSTGRES_PASSWORD: password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
  
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
  
  backend:
    build: ./backend
    command: uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
    volumes:
      - ./backend:/app
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql://admin:password@postgres:5432/trading_bot
      REDIS_URL: redis://redis:6379
    depends_on:
      - postgres
      - redis
  
  celery:
    build: ./backend
    command: celery -A app.tasks worker --loglevel=info
    volumes:
      - ./backend:/app
    environment:
      DATABASE_URL: postgresql://admin:password@postgres:5432/trading_bot
      REDIS_URL: redis://redis:6379
    depends_on:
      - postgres
      - redis
  
  frontend:
    build: ./frontend
    command: npm run dev
    volumes:
      - ./frontend:/app
      - /app/node_modules
    ports:
      - "3000:3000"
    depends_on:
      - backend

volumes:
  postgres_data:
```

### 5.2 生产环境

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - backend
      - frontend
  
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: ${POSTGRES_DB}
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: always
  
  redis:
    image: redis:7-alpine
    command: redis-server --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis_data:/data
    restart: always
  
  backend:
    build: ./backend
    command: gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
    environment:
      DATABASE_URL: ${DATABASE_URL}
      REDIS_URL: ${REDIS_URL}
      SECRET_KEY: ${SECRET_KEY}
    restart: always
  
  celery:
    build: ./backend
    command: celery -A app.tasks worker --loglevel=info --concurrency=4
    environment:
      DATABASE_URL: ${DATABASE_URL}
      REDIS_URL: ${REDIS_URL}
    restart: always
  
  celery-beat:
    build: ./backend
    command: celery -A app.tasks beat --loglevel=info
    environment:
      DATABASE_URL: ${DATABASE_URL}
      REDIS_URL: ${REDIS_URL}
    restart: always

volumes:
  postgres_data:
  redis_data:
```

## 六、安全考虑

### 6.1 API密钥加密

```python
from cryptography.fernet import Fernet
import os

class KeyEncryption:
    """API密钥加密工具"""
    
    def __init__(self):
        # 从环境变量获取加密密钥
        self.key = os.getenv('ENCRYPTION_KEY').encode()
        self.cipher = Fernet(self.key)
    
    def encrypt(self, api_key: str) -> str:
        """加密API密钥"""
        return self.cipher.encrypt(api_key.encode()).decode()
    
    def decrypt(self, encrypted_key: str) -> str:
        """解密API密钥"""
        return self.cipher.decrypt(encrypted_key.encode()).decode()
```

### 6.2 JWT认证

```python
from datetime import datetime, timedelta
from jose import JWTError, jwt

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
```

### 6.3 权限控制

```python
from fastapi import Depends, HTTPException, status

async def get_current_user(token: str = Depends(oauth2_scheme)):
    """获取当前登录用户"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无法验证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = await get_user_by_id(user_id)
    if user is None:
        raise credentials_exception
    return user

async def check_bot_ownership(bot_id: int, user: User = Depends(get_current_user)):
    """检查用户是否拥有该机器人"""
    bot = await get_bot_by_id(bot_id)
    if bot.user_id != user.id:
        raise HTTPException(status_code=403, detail="无权访问此机器人")
    return bot
```

## 七、监控和日志

### 7.1 日志系统

```python
import logging
from logging.handlers import RotatingFileHandler

def setup_logger(name: str) -> logging.Logger:
    """配置日志记录器"""
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # 文件处理器(自动轮转)
    file_handler = RotatingFileHandler(
        f'logs/{name}.log',
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(logging.DEBUG)
    
    # 格式化
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)
    
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    return logger
```

### 7.2 性能监控

使用Prometheus + Grafana进行系统监控:
- API响应时间
- 数据库查询性能
- Celery任务执行情况
- 机器人运行状态
- 交易所API调用频率

## 八、测试策略

### 8.1 单元测试

```python
# tests/test_spread_calculator.py
import pytest
from app.services.spread_calculator import SpreadCalculator

def test_calculate_spread():
    calculator = SpreadCalculator()
    spread = calculator.calculate(
        market1_price=100,
        market1_start_price=95,
        market2_price=50,
        market2_start_price=48
    )
    # (100/95 - 1) - (50/48 - 1) = 0.0526 - 0.0417 = 0.0109 = 1.09%
    assert abs(spread - 1.09) < 0.01
```

### 8.2 集成测试

```python
# tests/test_bot_api.py
from httpx import AsyncClient
import pytest

@pytest.mark.asyncio
async def test_create_bot(client: AsyncClient, auth_headers):
    response = await client.post(
        "/api/v1/bots/",
        json={
            "market1_symbol": "BTC-USDT",
            "market2_symbol": "ETH-USDT",
            "leverage": 10,
            # ...
        },
        headers=auth_headers
    )
    assert response.status_code == 201
```

### 8.3 回测系统

```python
class BacktestEngine:
    """回测引擎,用于策略验证"""
    
    def __init__(self, strategy, historical_data):
        self.strategy = strategy
        self.data = historical_data
    
    async def run(self):
        """运行回测"""
        for tick in self.data:
            await self.strategy.on_tick(tick)
        
        return self.calculate_metrics()
```

## 九、扩展性考虑

### 9.1 多交易所支持

通过工厂模式轻松添加新交易所:

```python
class ExchangeFactory:
    @staticmethod
    def create(exchange_name: str, credentials: dict) -> BaseExchange:
        exchanges = {
            'okx': OKXExchange,
            'binance': BinanceExchange,
            'bybit': BybitExchange,
        }
        
        exchange_class = exchanges.get(exchange_name.lower())
        if not exchange_class:
