# ChainMakes - 加密货币价差套利交易机器人系统

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![Vue](https://img.shields.io/badge/Vue-3.3+-brightgreen.svg)](https://vuejs.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

一个功能完整的加密货币价差套利交易机器人系统，支持多交易所价差监控和自动化交易。

项目模仿 [https://app.chainmakes.com/](https://app.chainmakes.com/)

感谢站长发视频分享逻辑思路 [https://www.youtube.com/playlist?list=PLHG3GUeIjEW3jM_6Y4hq_CBr-BrP-jZpv](https://www.youtube.com/playlist?list=PLHG3GUeIjEW3jM_6Y4hq_CBr-BrP-jZpv)

个人不会代码，全程让AI分析编写和修复问题，无法保证稳定运行，有兴趣的可以找站长购买 [@river2liu](https://t.me/river2liu)


## ✨ 主要特性

- 🤖 **智能交易机器人** - 自动监控价差并执行套利交易
- 💱 **多交易所支持** - 支持OKX、Binance等主流交易所
- 📊 **实时监控** - WebSocket实时推送市场数据和交易状态
- 🔒 **安全可靠** - API密钥加密存储、JWT认证
- 📈 **数据可视化** - 实时图表展示价差变化和持仓情况
- 🎯 **策略配置** - 灵活的DCA策略和风险控制参数
- 🧪 **模拟交易** - Mock交易所支持，安全测试策略

## 🚀 快速启动

### 系统要求

- Python 3.11+
- Node.js 18+
- pnpm 8+

### 本地开发环境

#### 1. 启动后端

双击运行 `启动后端.bat` 或手动执行：

```cmd
cd backend
venv\Scripts\activate
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

#### 2. 启动前端

双击运行 `启动前端.bat` 或手动执行：

```cmd
cd frontend
pnpm dev
```

#### 3. 访问系统

- 前端界面: http://localhost:3333
- 后端API: http://localhost:8000
- API文档: http://localhost:8000/docs

**默认账户：**
- 用户名: `admin`
- 密码: `admin123`

### Docker 部署 (推荐)

```bash
# 1. 配置环境变量
cp .env.example .env
vim .env  # 修改 SECRET_KEY 和 ENCRYPTION_KEY

# 2. 启动服务
docker-compose up -d

# 3. 查看日志
docker-compose logs -f

# 4. 停止服务
docker-compose down
```

**重要**:
- 交易所 API 密钥在前端页面添加,不在 `.env` 中配置
- 国内用户如需代理访问 OKX,在 `.env` 设置 `OKX_PROXY=http://127.0.0.1:7890`
- 海外用户无需配置代理

详细部署说明请参考 [DEPLOYMENT.md](DEPLOYMENT.md)

### ⚠️ 重要安全提醒

**在上传到GitHub之前，请确保：**

1. **环境变量安全**：
   ```bash
   # 确保 .env 文件已被 gitignore 忽略
   echo ".env" >> .gitignore

   # 只上传 .env.example 作为模板
   cp .env .env.example
   # 编��� .env.example，将所有敏感值替换为占位符
   ```

2. **数据库文件**：
   ```bash
   # 删除本地的数据库文件（不要上传）
   rm -f backend/*.db
   ```

3. **日志文件清理**：
   ```bash
   # 清理所有日志文件
   rm -rf backend/logs/*.log
   ```

4. **敏感配置检查**：
   - 检查是否有硬编码的API密钥、密码或私钥
   - 确保所有配置文件中的敏感信息已移除
   - 验证交易所配置不包含真实账户信息

## 📖 文档

- [快速启动指南](快速启动指南.txt) - 最简单的启动方式
- [手动启动说明](手动启动说明.md) - 详细的手动启动步骤
- [部署指南](DEPLOYMENT_README.md) - 生产环境部署
- [API文档](docs/API_DOCUMENTATION.md) - 完整的API接口说明
- [开发进度](docs/DEVELOPMENT_PROGRESS_2025-10-06.md) - 最新开发状态

## 🏗️ 项目结构

```
chainmakes/
├── backend/                 # 后端服务
│   ├── app/
│   │   ├── api/v1/         # API路由
│   │   ├── core/           # 核心业务（交易引擎）
│   │   ├── models/         # 数据模型
│   │   ├── services/       # 业务逻辑
│   │   ├── exchanges/      # 交易所适配器
│   │   └── utils/          # 工具函数
│   └── scripts/            # 工具脚本
├── frontend/               # 前端应用
│   ├── src/
│   │   ├── common/         # 公共组件
│   │   ├── pages/          # 页面组件
│   │   ├── layouts/        # 布局组件
│   │   └── pinia/          # 状态管理
│   └── public/             # 静态资源
├── docs/                   # 项目文档
├── 启动后端.bat            # 后端启动脚本
└── 启动前端.bat            # 前端启动脚本
```

## 💡 核心功能

### 1. 交易所管理
- 添加/编辑/删除交易所账户
- API密钥加密存储
- 连接测试功能
- 支持Mock模拟交易所

### 2. 交易机器人
- 创建价差套利机器人
- 灵活的DCA（定投）策略配置
- 杠杆交易支持
- 止盈止损设置
- 实时监控和控制

### 3. 实时监控
- WebSocket实时数据推送
- 价差变化图表
- 持仓情况展示
- 订单历史查询

### 4. 风险控制
- 最大持仓限制
- 止损比例设置
- DCA次数限制
- 每单投资金额控制

## 🔧 开发

### 后端开发

```bash
cd backend
venv\Scripts\activate
pip install -r requirements.txt

# 运行测试
pytest

# 数据库迁移
alembic upgrade head
```

### 前端开发

```bash
cd frontend
pnpm install
pnpm dev

# 构建生产版本
pnpm build
```

## 🐛 常见问题

### 端口被占用

```cmd
# 查看占用进程
netstat -ano | findstr :8000
netstat -ano | findstr :3333

# 结束进程
taskkill /F /PID <进程号>
```

### 虚拟环境问题

```cmd
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### 前端依赖问题

```cmd
cd frontend
rmdir /s /q node_modules
pnpm install
```

更多问题请查看 [手动启动说明.md](手动启动说明.md)

## 📝 使用示例

### 1. 创建交易所账户

```python
POST /api/v1/exchanges/
{
  "exchange_name": "okx",
  "api_key": "your-api-key",
  "api_secret": "your-secret",
  "passphrase": "your-passphrase"
}
```

### 2. 创建交易机器人

```python
POST /api/v1/bots/
{
  "bot_name": "BTC-ETH套利",
  "exchange_account_id": 1,
  "market1_symbol": "BTC-USDT",
  "market2_symbol": "ETH-USDT",
  "leverage": 10,
  "investment_per_order": 100
}
```

### 3. 启动机器人

```python
POST /api/v1/bots/{bot_id}/start
```

## 🔐 安全建议

### 基本安全措施
- ✅ 使用强密码和API密钥
- ✅ 定期更新依赖包
- ✅ 生产环境禁用DEBUG模式
- ✅ 限制API访问频率
- ✅ 定期备份数据库
- ✅ 使用防火墙保护服务
- ✅ 定期轮换API密钥和密码
- ✅ 使用IP白名单限制访问
- ✅ 启用双因素认证（2FA）
- ✅ 监控异常交易活动

### 🚨 严禁事项
- ❌ **绝对不要**将API密钥、私钥或任何敏感信息提交到代码库
- ❌ **绝对不要**在生产环境使用默认密码
- ❌ **绝对不要**在公共WiFi下管理交易所账户
- ❌ **绝对不要**将.env文件上传到任何公共平台
- ❌ **绝对不要**在日志中记录敏感信息

### 生产环境要求
- 🔒 生产环境必须使用HTTPS和SSL证书
- 🖥️ 建议使用专门的交易服务器，避免在个人电脑上运行
- 🌐 配置反向代理（Nginx/Caddy）
- 🔐 启用数据库加密
- 📊 设置日志监控和告警
- 🚪 使用强密码策略和账户锁定机制

### 数据保护
- 💾 定期备份交易数据到安全位置
- 🔒 对敏感配置文件进行加密存储
- 🗑️ 安全删除不再使用的数据和日志
- 📋 建立数据访问权限管理制度

## 🤝 贡献

欢迎提交Issue和Pull Request！

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 📮 联系方式

- 问题反馈: 提交 [Issue](../../issues)
- 功能建议: 提交 [Pull Request](../../pulls)

---

**⚠️ 风险提示**

加密货币交易存在高风险，本系统仅供学习和研究使用。请在充分了解风险的情况下使用，作者不对任何交易损失负责。建议先在模拟环境中充分测试后再用于实盘交易。

---

**最后更新**: 2025-10-11

---

**🔒 GitHub上传安全清单**

在上传前请再次确认：
- [ ] .env 文件已添加到 .gitignore
- [ ] 所有 API 密钥和密码已移除
- [ ] 数据库文件 (*.db) 已删除
- [ ] 日志文件已清理
- [ ] 私钥和证书文件已排除
- [ ] 配置文件中的敏感信息已清理
- [ ] 代码中没有硬编码的敏感信息
- [ ] 只上传 .env.example 作为配置模板

**记住：安全第一，预防为主！**