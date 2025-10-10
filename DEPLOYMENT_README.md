# ChainMakes 部署方案总览

本项目支持**两种部署方式**,适应不同的使用场景。

---

## 🎯 部署场景选择

### 场景1: 本地开发/测试 (Windows)

**适用于**:
- 本地电脑开发调试
- 功能测试验证
- 策略回测分析

**优势**:
- ✅ 无需 Docker
- ✅ 即开即用
- ✅ 修改代码即时生效
- ✅ 资源占用少

**启动方式**:
```bash
# 双击运行
start.bat

# 访问
# 前端: http://localhost:3333
# 后端: http://localhost:8000
```

📖 **详细文档**: [DEPLOYMENT_WITHOUT_DOCKER.md](./docs/DEPLOYMENT_WITHOUT_DOCKER.md)

---

### 场景2: VPS 生产环境 (Linux)

**适用于**:
- 云服务器部署
- 7x24 稳定运行
- 真实交易环境

**优势**:
- ✅ Docker 容器化
- ✅ 一键部署
- ✅ 易于维护
- ✅ 可扩展性强

**部署命令**:
```bash
# 克隆项目
git clone https://github.com/your-repo/chainmakes.git
cd chainmakes

# 配置环境
cp .env.example .env
nano .env  # 修改配置

# 启动服务
docker compose up -d

# 访问
# https://your-domain.com
```

📖 **详细文档**: [VPS_DOCKER_DEPLOYMENT.md](./docs/VPS_DOCKER_DEPLOYMENT.md)

---

## 📁 部署文件说明

### 本地开发文件
- `start.bat` - Windows 启动脚本
- `stop.bat` - Windows 停止脚本
- `docs/DEPLOYMENT_WITHOUT_DOCKER.md` - 本地部署文档

### Docker 部署文件
- `Dockerfile.backend` - 后端镜像
- `Dockerfile.frontend` - 前端镜像
- `docker-compose.yml` - 开发环境配置
- `docker-compose.prod.yml` - 生产环境配置
- `nginx.conf` - Nginx 配置
- `.env.example` - 环境变量模板
- `docs/VPS_DOCKER_DEPLOYMENT.md` - VPS 部署文档

---

## 🚀 推荐开发流程

```
1. 本地开发测试 (Windows)
   ├─ 使用 start.bat 启动
   ├─ 功能开发和调试
   ├─ OKX 模拟盘测试
   └─ 验证所有功能正常

2. 代码提交
   ├─ Git 提交代码
   └─ 推送到远程仓库

3. VPS 部署 (Linux)
   ├─ SSH 登录服务器
   ├─ 拉取最新代码
   ├─ docker compose up -d
   └─ 配置域名和 HTTPS

4. 生产运行
   ├─ 监控日志
   ├─ 定期备份
   └─ 性能优化
```

---

## 🔧 快速命令参考

### 本地开发 (Windows)
```bash
# 启动
start.bat

# 停止
stop.bat

# 手动启动后端
cd backend
venv\Scripts\activate
python -m uvicorn app.main:app --port 8000

# 手动启动前端
cd frontend
pnpm dev
```

### VPS 生产 (Linux)
```bash
# 部署
docker compose up -d

# 查看日志
docker compose logs -f

# 更新代码
git pull && docker compose up -d --build

# 重启服务
docker compose restart

# 备份数据
docker compose exec backend cp /app/data/chainmakes.db /app/data/backup_$(date +%Y%m%d).db

# 停止服务
docker compose down
```

---

## 📊 环境对比

| 特性 | 本地开发 | VPS 生产 |
|------|---------|---------|
| 部署难度 | ⭐ 简单 | ⭐⭐ 中等 |
| 运行环境 | Windows | Linux |
| Docker | 不需要 | 需要 |
| 启动方式 | start.bat | docker compose |
| 适用场景 | 开发测试 | 生产运行 |
| 资源占用 | 低 | 中等 |
| 稳定性 | 开发级 | 生产级 |
| HTTPS | 不需要 | 推荐 |
| 域名 | localhost | 必需 |
| 备份 | 手动 | 自动化 |
| 监控 | 手动 | 自动化 |

---

## 🔐 安全配置

### 首次部署必做

1. **修改默认密码**
   - 管理员密码: admin / admin123 → 自定义强密码

2. **配置环境变量**
   ```bash
   # 生成随机密钥
   openssl rand -hex 32

   # 修改 .env
   SECRET_KEY=<生成的密钥>
   JWT_SECRET_KEY=<另一个密钥>
   ```

3. **OKX API 配置**
   - 使用模拟盘测试: `OKX_IS_DEMO=True`
   - 真实盘谨慎使用: `OKX_IS_DEMO=False`

4. **CORS 配置**
   ```env
   # 开发
   ALLOWED_ORIGINS=http://localhost:3333

   # 生产
   ALLOWED_ORIGINS=https://your-domain.com
   ```

---

## 📖 相关文档

### 核心文档
- [开发交接文档](./docs/DEVELOPMENT_HANDOVER_2025-10-06.md) - 项目整体介绍
- [开发完成总结](./docs/DEVELOPMENT_SUMMARY_2025-10-06.md) - 最新开发成果
- [API 文档](./docs/API_DOCUMENTATION.md) - 后端 API 说明

### 部署文档
- [本地部署指南](./docs/DEPLOYMENT_WITHOUT_DOCKER.md) - Windows 本地开发
- [VPS 部署指南](./docs/VPS_DOCKER_DEPLOYMENT.md) - Linux 服务器生产

### 集成文档
- [OKX 集成指南](./docs/OKX_INTEGRATION_GUIDE.md) - 交易所 API 接入
- [测试指南](./docs/TESTING_GUIDE.md) - 功能测试说明

---

## ❓ 常见问题

### Q1: 我应该选择哪种部署方式?

**A**:
- 本地开发测试 → 使用 `start.bat` (无需 Docker)
- VPS 生产运行 → 使用 `docker compose` (需要 Docker)

### Q2: 本地测试通过后如何迁移到 VPS?

**A**:
1. 将代码推送到 Git 仓库
2. 在 VPS 上克隆代码
3. 配置 `.env` 文件
4. 运行 `docker compose up -d`

### Q3: 需要多少服务器配置?

**A**:
- **最低**: 2核 4GB (轻量级运行)
- **推荐**: 4核 8GB (稳定运行)
- **高性能**: 8核 16GB (多机器人并发)

### Q4: 如何从模拟盘切换到真实盘?

**A**:
修改 `.env` 文件:
```env
OKX_IS_DEMO=False  # 改为 False
OKX_API_KEY=<真实 API Key>
OKX_API_SECRET=<真实 Secret>
OKX_PASSPHRASE=<真实 Passphrase>
```

⚠️ **警告**: 真实盘交易有风险,请谨慎操作!

---

## 🆘 获取帮助

遇到部署问题?

1. 查看对应的详细文档
2. 检查日志文件
3. 运行测试脚本验证
4. 提交 GitHub Issue

---

**项目状态**: ✅ 生产就绪
**最后更新**: 2025-10-06
**版本**: v1.0.0

---

**提示**: 建议先在本地测试所有功能,确认无误后再部署到 VPS 生产环境!
