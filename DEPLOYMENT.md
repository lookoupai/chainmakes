# ChainMakes Docker 部署指南

简单、统一的 Docker 部署方案,一个配置文件搞定所有环境。

## 🚀 快速开始 (3 步)

### 1. 配置环境变量

```bash
cp .env.example .env
vim .env
```

必须修改:
- `SECRET_KEY` / `ENCRYPTION_KEY` - 随机密钥

可选配置:
- `OKX_IS_DEMO` - 模拟盘/实盘切换
  - `true` = 模拟盘 (默认,推荐)
  - `false` = 实盘 (真实资金,有风险!)
- `OKX_PROXY` - 代理地址 (国内需要,海外留空)
  - 🌍 海外: `OKX_PROXY=` (留空)
  - 🇨🇳 国内: `OKX_PROXY=http://127.0.0.1:7890`

**注意**: 交易所 API 密钥在前端页面添加,不在 .env 中配置!

### 2. 启动服务

```bash
docker-compose up -d
```

### 3. 访问应用

- 前端: http://your-ip
- API: http://your-ip:8000/docs

完成! 🎉

---

## 📖 常用命令

```bash
# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f
docker-compose logs -f backend  # 只看后端日志

# 重启服务
docker-compose restart

# 停止服务
docker-compose down

# 更新并重启
docker-compose pull
docker-compose up -d

# 完全重新构建
docker-compose build --no-cache
docker-compose up -d
```

---

## 🔧 可选功能

### 使用 PostgreSQL

1. 修改 `.env`:
```bash
DATABASE_URL=postgresql://chainmakes:yourpassword@postgres:5432/chainmakes
DATABASE_URL_ASYNC=postgresql+asyncpg://chainmakes:yourpassword@postgres:5432/chainmakes
POSTGRES_PASSWORD=yourpassword
```

2. 启动:
```bash
docker-compose --profile postgres up -d
```

### 使用 Redis

```bash
docker-compose --profile redis up -d
```

### 同时使用两者

```bash
docker-compose --profile postgres --profile redis up -d
```

---

## 🌐 生产环境配置

### HTTPS 配置 (Let's Encrypt)

```bash
# 1. 安装 certbot
sudo apt install certbot

# 2. 获取证书
sudo certbot certonly --standalone -d yourdomain.com

# 3. 创建 ssl 目录并复制证书
mkdir -p ssl
sudo cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem ssl/cert.pem
sudo cp /etc/letsencrypt/live/yourdomain.com/privkey.pem ssl/key.pem

# 4. 修改 nginx.conf 启用 HTTPS
# 5. 重启前端服务
docker-compose restart frontend
```

### 使用预构建镜像 (推荐)

编辑 `docker-compose.yml`,取消注释:

```yaml
services:
  backend:
    image: ghcr.io/yourusername/chainmakes-backend:latest
    # build:
    #   context: .
    #   dockerfile: Dockerfile.backend
```

然后:
```bash
docker-compose pull
docker-compose up -d
```

---

## 🔍 健康检查

```bash
# 检查后端
curl http://localhost:8000/health

# 检查前端
curl http://localhost/health

# 查看容器健康状态
docker ps
```

---

## 📦 数据备份

### 备份 SQLite 数据库

```bash
# 备份
docker cp chainmakes-backend:/app/data/chainmakes.db ./backup-$(date +%Y%m%d).db

# 恢复
docker cp ./backup-20250111.db chainmakes-backend:/app/data/chainmakes.db
docker-compose restart backend
```

### 备份 PostgreSQL

```bash
# 备份
docker exec chainmakes-postgres pg_dump -U chainmakes chainmakes > backup.sql

# 恢复
docker exec -i chainmakes-postgres psql -U chainmakes chainmakes < backup.sql
```

---

## 🐛 常见问题

### 1. 端口被占用

```bash
# 查看占用端口的进程
lsof -i :8000
lsof -i :80

# 或修改 .env 中的端口
FRONTEND_PORT=8080
```

### 2. OKX API 连接失败

**国内**:
```bash
# 确保代理正在运行
curl -x http://127.0.0.1:7890 https://www.okx.com

# 查看后端日志
docker-compose logs backend | grep -i proxy
```

**海外**:
```bash
# 确保 OKX_PROXY 为空
grep OKX_PROXY .env
# 应显示: OKX_PROXY=

# 测试直连
docker exec chainmakes-backend curl https://www.okx.com
```

### 3. 前端无法连接后端

```bash
# 检查后端是否启动
docker-compose ps backend

# 检查网络
docker exec chainmakes-frontend curl http://backend:8000/health

# 检查 CORS 配置
grep CORS_ORIGINS .env
```

### 4. 内存不足

```bash
# 查看资源使用
docker stats

# 限制内存 (编辑 docker-compose.yml)
services:
  backend:
    deploy:
      resources:
        limits:
          memory: 1G
```

### 5. 容器启动失败

```bash
# 查看详细错误
docker-compose logs backend
docker-compose logs frontend

# 检查配置文件
docker-compose config

# 重新构建
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

---

## 🤖 GitHub Actions 自动构建

项目已配置自动构建多架构镜像 (amd64/arm64)。

### 触发构建

```bash
# 推送到主分支触发
git push origin main

# 或创建版本标签
git tag v1.0.0
git push origin v1.0.0
```

### 使用构建的镜像

```bash
# 拉取镜像
docker pull ghcr.io/yourusername/chainmakes-backend:latest
docker pull ghcr.io/yourusername/chainmakes-frontend:latest

# 修改 docker-compose.yml 使用镜像
# 然后启动
docker-compose up -d
```

---

## 📊 监控和日志

### 日志配置

编辑 `docker-compose.yml`:

```yaml
services:
  backend:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

### 查看日志

```bash
# 实时日志
docker-compose logs -f

# 最近 100 行
docker-compose logs --tail=100

# 特定时间范围
docker-compose logs --since 2025-01-11T10:00:00

# 保存日志到文件
docker-compose logs > logs.txt
```

---

## 🔐 安全建议

1. **修改默认密钥**
   - 生成随机密钥: `openssl rand -hex 32`
   - 不要使用示例中的默认值

2. **限制端口访问**
   - 使用防火墙限制 8000 端口只能内部访问
   - 只开放 80/443 端口给外部

3. **定期更新**
   ```bash
   docker-compose pull
   docker-compose up -d
   ```

4. **备份数据**
   - 定期备份数据库
   - 保存配置文件

5. **使用 HTTPS**
   - 生产环境必须使用 SSL 证书

---

## 📚 更多资源

- [Docker 文档](https://docs.docker.com/)
- [OKX API 文档](https://www.okx.com/docs-v5/)
- [Let's Encrypt](https://letsencrypt.org/)

---

**最后更新**: 2025-01-11
