# ChainMakes VPS Docker 部署指南

本文档介绍如何在 **VPS 服务器**上使用 **Docker** 部署 ChainMakes 项目。

---

## 📋 前提条件

### VPS 服务器要求
- **操作系统**: Ubuntu 20.04+ / Debian 11+ / CentOS 8+
- **CPU**: 2核心+ (推荐 4核心)
- **内存**: 4GB+ (推荐 8GB)
- **存储**: 50GB+ SSD
- **网络**: 稳定的网络连接

### 软件要求
- Docker 20.10+
- Docker Compose 2.0+
- Git

---

## 🚀 快速部署

### 1. 安装 Docker 和 Docker Compose

#### Ubuntu/Debian

```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装依赖
sudo apt install -y curl git

# 安装 Docker
curl -fsSL https://get.docker.com | bash

# 启动 Docker
sudo systemctl start docker
sudo systemctl enable docker

# 添加当前用户到 docker 组
sudo usermod -aG docker $USER

# 重新登录生效
exit
# 重新 SSH 登录

# 验证安装
docker --version
docker compose version
```

#### CentOS/RHEL

```bash
# 安装依赖
sudo yum install -y yum-utils git

# 添加 Docker 仓库
sudo yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo

# 安装 Docker
sudo yum install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# 启动 Docker
sudo systemctl start docker
sudo systemctl enable docker

# 添加当前用户到 docker 组
sudo usermod -aG docker $USER

# 验证安装
docker --version
docker compose version
```

---

### 2. 克隆项目

```bash
# 创建项目目录
mkdir -p ~/projects
cd ~/projects

# 方式1: 从 Git 克隆 (如果代码在 Git 仓库)
git clone https://github.com/your-username/chainmakes.git
cd chainmakes

# 方式2: 上传本地代码到服务器
# 在本地电脑上执行:
# scp -r E:\down\网站源码\AI帮写的代码\chainmakes user@your-vps-ip:~/projects/
```

---

### 3. 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑配置
nano .env
```

**关键配置项**:

```env
# 应用配置
SECRET_KEY=your-very-secure-random-key-change-this-immediately
JWT_SECRET_KEY=another-secure-random-key-change-this-too

# OKX API (根据需求配置)
OKX_IS_DEMO=True  # 测试时用模拟盘
OKX_API_KEY=your-api-key
OKX_API_SECRET=your-api-secret
OKX_PASSPHRASE=your-passphrase

# CORS (修改为您的域名)
ALLOWED_ORIGINS=https://your-domain.com,https://www.your-domain.com

# 数据库 (可选升级为 PostgreSQL)
DATABASE_URL=sqlite:///./data/chainmakes.db
```

**生成安全密钥**:
```bash
# 生成随机密钥
openssl rand -hex 32
```

---

### 4. 创建必要目录

```bash
# 创建数据和日志目录
mkdir -p data logs ssl

# 设置权限
chmod 755 data logs
```

---

### 5. 部署应用

#### 基础部署 (SQLite 数据库)

```bash
# 构建并启动
docker compose up -d

# 查看日志
docker compose logs -f

# 等待服务启动 (约 30-60 秒)
```

#### 完整部署 (PostgreSQL + Redis)

```bash
# 使用完整配置
docker compose -f docker-compose.yml --profile with-postgres --profile with-redis up -d

# 查看所有服务
docker compose ps
```

---

### 6. 验证部署

```bash
# 检查服务状态
docker compose ps

# 应该看到:
# - chainmakes-backend (healthy)
# - chainmakes-frontend (running)

# 测试后端 API
curl http://localhost:8000/health

# 测试前端
curl http://localhost:80
```

---

## 🌐 域名和 HTTPS 配置

### 1. 配置域名解析

在域名服务商添加 A 记录:
```
A记录: @ -> 您的VPS IP
A记录: www -> 您的VPS IP
```

### 2. 安装 SSL 证书 (Let's Encrypt)

```bash
# 安装 certbot
sudo apt install -y certbot

# 停止 Nginx (临时)
docker compose stop frontend

# 获取证书
sudo certbot certonly --standalone -d your-domain.com -d www.your-domain.com

# 复制证书到项目目录
sudo cp /etc/letsencrypt/live/your-domain.com/fullchain.pem ./ssl/cert.pem
sudo cp /etc/letsencrypt/live/your-domain.com/privkey.pem ./ssl/key.pem
sudo chown -R $USER:$USER ./ssl

# 重启服务
docker compose start frontend
```

### 3. 更新 Nginx 配置

编辑 `nginx.conf`,取消 HTTPS 部分的注释:

```nginx
server {
    listen 443 ssl http2;
    server_name your-domain.com www.your-domain.com;

    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;

    # SSL 优化
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # ... 其他配置
}

# HTTP 跳转 HTTPS
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;
    return 301 https://$server_name$request_uri;
}
```

重启前端服务:
```bash
docker compose restart frontend
```

### 4. 自动续期证书

```bash
# 添加定时任务
sudo crontab -e

# 每月1号凌晨3点续期
0 3 1 * * certbot renew --quiet && docker compose restart frontend
```

---

## 🔧 运维管理

### 服务管理

```bash
# 启动所有服务
docker compose up -d

# 停止所有服务
docker compose stop

# 重启服务
docker compose restart

# 停止并删除容器
docker compose down

# 查看日志
docker compose logs -f                    # 所有服务
docker compose logs -f backend           # 仅后端
docker compose logs -f frontend          # 仅前端
docker compose logs -f --tail=100 backend # 最近100行
```

### 更新部署

```bash
# 拉取最新代码
git pull

# 重新构建并启动
docker compose up -d --build

# 或者分步骤
docker compose build
docker compose up -d
```

### 数据备份

```bash
# 备份 SQLite 数据库
docker compose exec backend cp /app/data/chainmakes.db /app/data/chainmakes_backup_$(date +%Y%m%d).db

# 下载到本地
docker cp chainmakes-backend:/app/data/chainmakes_backup_*.db ./backups/

# 备份 PostgreSQL (如果使用)
docker compose exec postgres pg_dump -U chainmakes chainmakes > backup_$(date +%Y%m%d).sql
```

### 监控和日志

```bash
# 查看容器资源使用
docker stats

# 查看磁盘使用
df -h
du -sh data/ logs/

# 清理日志 (保留最近7天)
find logs/ -name "*.log" -mtime +7 -delete

# Docker 清理
docker system prune -a --volumes  # 谨慎使用!
```

---

## 🛡️ 安全加固

### 防火墙配置

```bash
# 安装 ufw
sudo apt install -y ufw

# 配置防火墙规则
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# 启用防火墙
sudo ufw enable

# 查看状态
sudo ufw status
```

### 修改默认端口 (可选)

编辑 `docker-compose.yml`:

```yaml
services:
  backend:
    ports:
      - "127.0.0.1:8000:8000"  # 仅本地访问

  frontend:
    ports:
      - "80:80"
      - "443:443"
```

### 限制 SSH 访问

```bash
# 编辑 SSH 配置
sudo nano /etc/ssh/sshd_config

# 修改配置
Port 2222  # 修改端口
PermitRootLogin no  # 禁止 root 登录
PasswordAuthentication no  # 仅允许密钥登录

# 重启 SSH
sudo systemctl restart sshd

# 更新防火墙
sudo ufw allow 2222/tcp
```

---

## 📊 性能优化

### Docker 资源限制

编辑 `docker-compose.yml`:

```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '1'
          memory: 1G

  frontend:
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 512M
```

### 数据库优化 (PostgreSQL)

```bash
# 编辑 PostgreSQL 配置
docker compose exec postgres bash -c "cat >> /var/lib/postgresql/data/postgresql.conf << EOF
shared_buffers = 256MB
effective_cache_size = 1GB
maintenance_work_mem = 64MB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100
random_page_cost = 1.1
work_mem = 2MB
EOF"

# 重启数据库
docker compose restart postgres
```

---

## 🚨 故障排查

### 常见问题

#### 1. 容器无法启动

```bash
# 查看详细日志
docker compose logs backend

# 检查端口占用
sudo netstat -tulpn | grep :8000

# 检查磁盘空间
df -h
```

#### 2. 数据库连接失败

```bash
# 检查 PostgreSQL
docker compose exec postgres psql -U chainmakes -d chainmakes -c "SELECT 1;"

# 查看数据库日志
docker compose logs postgres
```

#### 3. 内存不足

```bash
# 查看内存使用
free -h

# 添加 swap
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

#### 4. Nginx 配置错误

```bash
# 测试配置
docker compose exec frontend nginx -t

# 重新加载配置
docker compose exec frontend nginx -s reload
```

---

## 📈 监控方案 (可选)

### 使用 Prometheus + Grafana

创建 `docker-compose.monitoring.yml`:

```yaml
version: '3.8'

services:
  prometheus:
    image: prom/prometheus:latest
    container_name: prometheus
    restart: unless-stopped
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus-data:/prometheus
    networks:
      - chainmakes-network

  grafana:
    image: grafana/grafana:latest
    container_name: grafana
    restart: unless-stopped
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana-data:/var/lib/grafana
    networks:
      - chainmakes-network

networks:
  chainmakes-network:
    external: true

volumes:
  prometheus-data:
  grafana-data:
```

启动监控:
```bash
docker compose -f docker-compose.monitoring.yml up -d
```

---

## ✅ 部署检查清单

部署前:
- [ ] VPS 服务器已准备
- [ ] Docker 已安装
- [ ] 域名已解析
- [ ] 环境变量已配置
- [ ] 数据目录已创建

部署后:
- [ ] 所有容器运行正常
- [ ] API 健康检查通过
- [ ] 前端可正常访问
- [ ] WebSocket 连接正常
- [ ] HTTPS 证书有效
- [ ] 防火墙配置正确
- [ ] 备份策略已设置

安全:
- [ ] 修改了默认密码
- [ ] SSH 密钥登录
- [ ] 防火墙已启用
- [ ] 定期安全更新

---

## 📞 技术支持

如遇到部署问题:

1. 检查 Docker 日志: `docker compose logs -f`
2. 验证网络连接: `ping your-domain.com`
3. 测试服务端口: `curl http://localhost:8000/health`
4. 查看系统资源: `docker stats`

---

**部署完成后,访问**: https://your-domain.com

**默认账户**: admin / admin123 (请立即修改!)

---

**最后更新**: 2025-10-06
**适用版本**: ChainMakes v1.0.0
