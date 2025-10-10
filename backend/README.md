# 加密货币价差套利交易机器人 - 后端

## 项目简介

基于 FastAPI 的加密货币价差套利交易机器人后端系统,支持 OKX 等交易所的双币对冲套利策略。

## 技术栈

- **框架**: FastAPI 0.104+
- **数据库**: PostgreSQL (异步 SQLAlchemy 2.0)
- **缓存**: Redis
- **任务队列**: Celery
- **交易所接口**: CCXT
- **认证**: JWT
- **部署**: Docker + Docker Compose

## 项目结构

```
backend/
├── app/
│   ├── api/            # API路由
│   │   └── v1/         # API v1版本
│   ├── core/           # 核心业务逻辑
│   ├── db/             # 数据库配置
│   ├── exchanges/      # 交易所适配器
│   ├── models/         # 数据库模型
│   ├── schemas/        # Pydantic模型
│   ├── services/       # 业务服务层
│   ├── strategies/     # 交易策略
│   ├── utils/          # 工具函数
│   ├── config.py       # 配置管理
│   ├── dependencies.py # 依赖注入
│   └── main.py         # 应用入口
├── tests/              # 测试
├── logs/               # 日志文件
├── .env                # 环境变量(需创建)
├── .env.example        # 环境变量示例
├── requirements.txt    # Python依赖
└── README.md           # 本文件
```

## 快速开始

### 1. 环境要求

- Python 3.11+
- PostgreSQL 15+
- Redis 7+

### 2. 安装依赖

```bash
cd backend
pip install -r requirements.txt
```

### 3. 配置环境变量

复制 `.env.example` 为 `.env` 并修改配置:

```bash
cp .env.example .env
```

**重要配置项**:

- `DATABASE_URL`: PostgreSQL 数据库连接字符串
- `REDIS_URL`: Redis 连接字符串
- `SECRET_KEY`: JWT 密钥(生产环境必须修改)
- `ENCRYPTION_KEY`: API 密钥加密密钥(生产环境必须修改)

生成加密密钥:
```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

### 4. 初始化数据库

```bash
# 使用 Alembic 进行数据库迁移(待实现)
# alembic upgrade head
```

### 5. 启动应用

开发模式:
```bash
python -m app.main
```

或使用 uvicorn:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 6. 访问 API 文档

启动后访问:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 使用 Docker

### 开发环境

```bash
docker-compose -f docker-compose.dev.yml up
```

### 生产环境

```bash
docker-compose -f docker-compose.prod.yml up -d
```

## API 端点

### 认证 (`/api/v1/auth`)
- `POST /register` - 用户注册
- `POST /login` - 用户登录
- `POST /refresh` - 刷新令牌

### 用户 (`/api/v1/users`)
- `GET /me` - 获取当前用户信息
- `PUT /me` - 更新用户信息

### 交易所 (`/api/v1/exchanges`)
- `POST /` - 添加交易所账户
- `GET /` - 获取交易所账户列表
- `DELETE /{id}` - 删除交易所账户

### 机器人 (`/api/v1/bots`)
- `POST /` - 创建机器人
- `GET /` - 获取机器人列表
- `GET /{id}` - 获取机器人详情
- `PUT /{id}` - 更新机器人配置
- `DELETE /{id}` - 删除机器人
- `POST /{id}/start` - 启动机器人
- `POST /{id}/pause` - 暂停机器人
- `POST /{id}/stop` - 停止机器人

### 订单 (`/api/v1/orders`)
- `GET /{bot_id}/orders` - 获取机器人订单历史

### WebSocket (`/api/v1/ws`)
- `WS /bot/{bot_id}` - 实时数据推送

## 开发进度

### 已完成 ✅

- [x] 项目基础架构搭建
- [x] 数据库模型设计与实现
- [x] Pydantic 数据验证模型
- [x] 工具函数模块(日志、加密、JWT)
- [x] 依赖注入系统
- [x] API 路由框架(认证、用户、交易所、机器人、订单、WebSocket)
- [x] 环境配置管理

### 进行中 🚧

- [ ] 交易所适配器实现(CCXT 封装)
- [ ] 价差套利策略核心逻辑
- [ ] 机器人交易引擎
- [ ] Celery 异步任务
- [ ] 数据库迁移(Alembic)

### 待实现 📋

- [ ] 服务层完善
- [ ] WebSocket 实时推送完善
- [ ] 单元测试和集成测试
- [ ] 性能监控(Prometheus)
- [ ] API 文档完善
- [ ] 生产环境部署配置

## 核心功能说明

### 价差套利策略

机器人通过监控两个交易对的涨跌幅差异,在价差达到设定阈值时:
1. **做空**涨幅较高的币种
2. **做多**涨幅较低的币种
3. 等待价差回归后平仓获利

### DCA 加仓机制

- 支持最多 20 次分批加仓
- 每次加仓可设置不同的价差阈值
- 支持倍投策略提升止盈效率

### 止盈止损

两种止盈模式:
- **回归止盈**: 价差回归到开仓位置附近
- **仓位止盈**: 总持仓盈利达到目标比例

## 注意事项

⚠️ **重要提示**:

1. **生产环境必须修改**: `SECRET_KEY` 和 `ENCRYPTION_KEY`
2. **API 密钥安全**: 所有 API 密钥在数据库中加密存储
3. **交易风险**: 本系统仅供学习和研究,实盘交易风险自负
4. **数据备份**: 定期备份数据库数据

## 开发指南

### 代码规范

- 遵循 PEP 8 Python 代码规范
- 使用类型注解
- 编写文档字符串

### 添加新功能

1. 在 `models/` 添加数据模型
2. 在 `schemas/` 添加验证模型
3. 在 `api/v1/` 添加路由
4. 在 `services/` 添加业务逻辑

## 许可证

MIT License

## 联系方式

如有问题请提 Issue 或 Pull Request。