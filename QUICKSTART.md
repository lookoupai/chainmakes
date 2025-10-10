# ChainMakes 快速启动指南

## 项目简介

ChainMakes 是一个加密货币价差套利交易机器人系统,采用双币对冲策略,通过监控两个市场的价差变化来实现自动化套利交易。

## 技术栈

- **后端**: Python 3.11+ / FastAPI / SQLAlchemy 2.0
- **数据库**: PostgreSQL 15 + Redis 7
- **交易所接口**: CCXT
- **部署**: Docker + Docker Compose

## 快速开始

### 1. 环境准备

确保已安装:
- Docker 20.10+
- Docker Compose 2.0+
- Git

### 2. 克隆项目

```bash
git clone <repository-url>
cd chainmakes
```

### 3. 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 生成安全密钥
cd backend
python scripts/generate_keys.py

# 将生成的密钥填入 .env 文件
```

编辑 `.env` 文件,至少修改以下配置:
```env
SECRET_KEY=<生成的密钥>
ENCRYPTION_KEY=<生成的加密密钥>
POSTGRES_PASSWORD=<设置强密码>
REDIS_PASSWORD=<设置强密码>
```

### 4. 启动开发环境

```bash
# 返回项目根目录
cd ..

# 启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f backend
```

### 5. 初始化数据库

```bash
# 进入后端容器
docker-compose exec backend bash

# 运行数据库初始化脚本
python scripts/init_db.py

# 或使用 Alembic 迁移
alembic upgrade head
```

默认管理员账户:
- 用户名: `admin`
- 密码: `admin123`
- ⚠️ **请立即修改默认密码!**

### 6. 访问API

API文档地址: http://localhost:8000/docs

主要端点:
- `/api/v1/auth/login` - 用户登录
- `/api/v1/bots` - 机器人管理
- `/api/v1/exchanges` - 交易所账户管理

### 7. 测试API

```bash
# 登录获取令牌
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123"

# 使用返回的token访问受保护端点
curl -X GET "http://localhost:8000/api/v1/users/me" \
  -H "Authorization: Bearer <your-token>"
```

## 使用流程

### 1. 添加交易所账户

通过API添加交易所API密钥:
```json
POST /api/v1/exchanges/
{
  "exchange_name": "okx",
  "api_key": "your-api-key",
  "api_secret": "your-api-secret",
  "passphrase": "your-passphrase"
}
```

### 2. 创建交易机器人

配置机器人参数:
```json
POST /api/v1/bots/
{
  "bot_name": "BTC-ETH套利",
  "exchange_account_id": 1,
  "market1_symbol": "BTC-USDT",
  "market2_symbol": "ETH-USDT",
  "start_time": "2025-01-01T00:00:00Z",
  "leverage": 10,
  "investment_per_order": 100,
  "max_position_value": 1000,
  "max_dca_times": 6,
  "dca_config": [
    {"times": 1, "spread": 1.0, "multiplier": 1.0},
    {"times": 2, "spread": 2.0, "multiplier": 2.0}
  ],
  "profit_mode": "position",
  "profit_ratio": 1.0,
  "stop_loss_ratio": 10.0
}
```

### 3. 启动机器人

```bash
POST /api/v1/bots/{bot_id}/start
```

### 4. 监控运行状态

```bash
# 查看机器人详情
GET /api/v1/bots/{bot_id}

# 查看持仓
GET /api/v1/bots/{bot_id}/positions

# 查看订单历史
GET /api/v1/bots/{bot_id}/orders

# 查看价差历史
GET /api/v1/bots/{bot_id}/spread-history
```

## 生产部署

### 1. 准备生产配置

```bash
# 复制生产环境配置
cp .env.example .env.production

# 编辑生产配置
vim .env.production
```

重要配置项:
```env
ENVIRONMENT=production
DEBUG=False
SECRET_KEY=<强密钥>
ENCRYPTION_KEY=<强加密密钥>
POSTGRES_PASSWORD=<强密码>
REDIS_PASSWORD=<强密码>
```

### 2. 启动生产环境

```bash
docker-compose -f docker-compose.prod.yml up -d
```

### 3. 配置Nginx (可选)

如果需要HTTPS,配置SSL证书:
```bash
# 将SSL证书放入 nginx/ssl/
cp your-cert.pem nginx/ssl/
cp your-key.pem nginx/ssl/

# 编辑nginx配置
vim nginx/nginx.conf
```

## 常见问题

### 数据库连接失败

检查PostgreSQL是否正常运行:
```bash
docker-compose ps postgres
docker-compose logs postgres
```

### Redis连接失败

检查Redis配置:
```bash
docker-compose ps redis
docker-compose logs redis
```

### 机器人无法启动

1. 检查交易所API密钥是否正确
2. 查看机器人日志: `docker-compose logs backend`
3. 确认数据库中配置参数正确

### API请求失败

1. 检查JWT令牌是否有效
2. 确认请求头包含正确的Authorization
3. 查看API日志排查问题

## 开发指南

### 目录结构

```
chainmakes/
├── backend/                  # 后端代码
│   ├── app/
│   │   ├── api/             # API路由
│   │   ├── core/            # 核心业务逻辑
│   │   ├── models/          # 数据库模型
│   │   ├── schemas/         # 数据验证
│   │   ├── services/        # 业务服务
│   │   ├── exchanges/       # 交易所适配器
│   │   └── utils/           # 工具函数
│   ├── alembic/             # 数据库迁移
│   └── scripts/             # 工具脚本
├── docs/                    # 项目文档
└── docker-compose.yml       # Docker配置
```

### 添加新功能

1. 在对应模块创建新文件
2. 添加必要的测试
3. 更新API文档
4. 提交代码审查

### 运行测试

```bash
docker-compose exec backend pytest
```

## 安全建议

1. ✅ 使用强密码和密钥
2. ✅ 定期更新依赖包
3. ✅ 启用HTTPS
4. ✅ 限制API访问频率
5. ✅ 定期备份数据库
6. ✅ 监控异常交易行为
7. ⚠️ 生产环境禁用DEBUG模式
8. ⚠️ 使用防火墙保护数据库端口

## 技术支持

- 文档: `docs/` 目录
- 问题反馈: 提交Issue
- 技术讨论: 加入社区

## 许可证

MIT License