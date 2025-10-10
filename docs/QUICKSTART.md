# ChainMakes 快速开始指南

## 项目简介

ChainMakes是一个加密货币价差套利交易机器人系统，支持多交易所之间的价差套利策略。本指南将帮助您快速搭建开发环境并运行项目。

## 系统要求

- Python 3.11+
- Node.js 18+
- pnpm 8+
- Git

## 快速启动

### 1. 克隆项目

```bash
git clone <repository-url>
cd chainmakes
```

### 2. 后端设置

```bash
# 进入后端目录
cd backend

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境 (Windows)
venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 初始化数据库
python scripts/init_db.py

# 启动后端服务
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. 前端设置

```bash
# 新开终端，进入前端目录
cd frontend

# 安装依赖
pnpm install

# 启动前端服务
pnpm dev
```

### 4. 访问应用

- 前端界面: http://localhost:5173
- 后端API: http://localhost:8000
- API文档: http://localhost:8000/docs

## 默认账户

系统已创建一个测试账户：

- 用户名: `admin`
- 密码: `admin123`

## 创建测试数据

运行以下脚本创建测试数据：

```bash
cd backend
venv\Scripts\activate
python scripts/create_test_data.py
```

这将创建：
- 测试用户账户
- 模拟交易所配置
- 示例交易机器人
- 模拟交易数据

## 项目结构概览

```
chainmakes/
├── backend/                 # 后端代码
│   ├── app/
│   │   ├── api/v1/         # API路由
│   │   ├── core/           # 核心功能（交易引擎等）
│   │   ├── models/         # 数据模型
│   │   ├── services/       # 业务逻辑
│   │   └── utils/          # 工具函数
│   └── scripts/            # 测试脚本
├── frontend/               # 前端代码
│   ├── src/
│   │   ├── common/         # 公共组件和工具
│   │   ├── components/     # UI组件
│   │   ├── pages/          # 页面组件
│   │   ├── apis/           # API调用
│   │   └── stores/         # 状态管理
│   └── public/             # 静态资源
└── docs/                   # 项目文档
```

## 核心功能使用

### 1. 创建交易所账户

1. 登录系统
2. 进入"交易所管理"页面
3. 点击"添加交易所"
4. 填写交易所信息和API密钥

### 2. 创建交易机器人

1. 进入"机器人管理"页面
2. 点击"创建机器人"
3. 配置机器人参数：
   - 机器人名称
   - 交易对
   - 策略类型（价差套利）
   - 价差阈值
   - 交易金额
   - 止盈止损设置

### 3. 启动机器人

1. 在机器人列表中找到创建的机器人
2. 点击"启动"按钮
3. 系统将开始监控价差并执行交易

### 4. 监控交易

1. 点击机器人名称进入详情页
2. 查看实时持仓、订单历史和价差变化
3. 可随时暂停或停止机器人

## 开发指南

### 后端开发

#### 添加新API端点

1. 在 `backend/app/api/v1/` 中创建路由文件
2. 在 `backend/app/services/` 中实现业务逻辑
3. 在 `backend/app/models/` 中定义数据模型（如需要）

示例：

```python
# backend/app/api/v1/example.py
from fastapi import APIRouter, Depends
from app.services.example_service import ExampleService

router = APIRouter()

@router.get("/example")
async def get_example():
    return ExampleService().get_data()
```

#### 添加新交易策略

1. 在 `backend/app/core/strategies/` 中创建策略类
2. 继承 `BaseStrategy` 并实现必要方法
3. 在 `backend/app/core/trading_engine.py` 中注册策略

示例：

```python
# backend/app/core/strategies/new_strategy.py
from .base import BaseStrategy

class NewStrategy(BaseStrategy):
    async def should_execute(self, data: dict) -> bool:
        # 实现策略逻辑
        return True
    
    async def execute(self, data: dict) -> dict:
        # 执行交易逻辑
        return {"status": "success"}
```

### 前端开发

#### 添加新页面

1. 在 `frontend/src/pages/` 中创建页面组件
2. 在 `frontend/src/router/config.ts` 中添加路由
3. 在侧边栏配置中添加菜单项

示例：

```typescript
// frontend/src/pages/example/index.vue
<template>
  <div class="example-page">
    <h1>示例页面</h1>
    <!-- 页面内容 -->
  </div>
</template>

<script setup lang="ts">
// 页面逻辑
</script>
```

#### 添加API调用

1. 在 `frontend/src/common/apis/` 中创建API文件
2. 定义类型和API函数
3. 在组件中使用

示例：

```typescript
// frontend/src/common/apis/example/index.ts
import { http } from '@/http'
import type { ExampleType } from './type'

export function getExample() {
  return http.request<ExampleType>({
    url: '/api/v1/example',
    method: 'GET'
  })
}
```

## 测试

### 运行后端测试

```bash
cd backend
venv\Scripts\activate
python scripts/test_auth.py
python scripts/test_websocket.py
python scripts/test_trading_engine_mock.py
```

### 运行前端测试

```bash
cd frontend
pnpm test
```

## 常见问题

### 1. 后端启动失败

- 检查Python版本是否为3.11+
- 确保虚拟环境已激活
- 检查依赖是否正确安装

### 2. 前端启动失败

- 检查Node.js版本是否为18+
- 确保pnpm已正确安装
- 删除node_modules并重新安装依赖

### 3. API连接失败

- 检查后端服务是否在8000端口运行
- 检查防火墙设置
- 查看浏览器控制台错误信息

### 4. WebSocket连接失败

- 检查WebSocket路由是否正确
- 确保后端WebSocket服务已启动
- 检查网络代理设置

## 部署

### 开发环境

按照上述快速启动步骤即可。

### 生产环境

1. 使用Docker容器化部署
2. 配置Nginx反向代理
3. 设置环境变量
4. 配置SSL证书

详细部署指南请参考 `docs/DEPLOYMENT.md`

## 贡献指南

1. Fork项目
2. 创建功能分支
3. 提交更改
4. 创建Pull Request

## 获取帮助

- 查看项目文档: `docs/` 目录
- 查看API文档: http://localhost:8000/docs
- 查看开发进度: `docs/DEVELOPMENT_PROGRESS.md`
- 查看测试报告: `docs/SYSTEM_TEST_REPORT.md`

## 许可证

本项目采用 MIT 许可证。详情请查看 LICENSE 文件。