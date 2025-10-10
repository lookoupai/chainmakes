# ChainMakes 部署指南

## 概述

本指南详细说明如何将ChainMakes加密货币交易机器人系统部署到生产环境。我们提供多种部署方案，包括Docker容器化部署、传统服务器部署和云平台部署。

## 系统要求

### 最低配置
- **CPU**: 2核心
- **内存**: 4GB RAM
- **存储**: 20GB SSD
- **网络**: 100Mbps
- **操作系统**: Ubuntu 20.04+ / CentOS 8+ / Windows Server 2019+

### 推荐配置
- **CPU**: 4核心
- **内存**: 8GB RAM
- **存储**: 50GB SSD
- **网络**: 1Gbps
- **操作系统**: Ubuntu 22.04 LTS

### 软件依赖
- Docker 20.10+
- Docker Compose 2.0+
- Nginx 1.18+
- Python 3.11+
- Node.js 18+
- PostgreSQL 13+ (生产环境)
- Redis 6+ (缓存和会话存储)

## 部署方案

### 方案一：Docker容器化部署（推荐）

#### 1. 准备环境

```bash
# 安装Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# 安装Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 创建项目目录
sudo mkdir -p /opt/chainmakes
sudo chown $USER:$USER /opt/chainmakes
cd /opt/chainmakes
```

#### 2. 配置环境变量

创建 `.env` 文件：

```bash
# 数据库配置
POSTGRES_DB=chainmakes
POSTGRES_USER=chainmakes
POSTGRES_PASSWORD=your_secure_password
DATABASE_URL=postgresql://chainmakes:your_secure_password@postgres:5432/chainmakes

# Redis配置
REDIS_URL=redis://redis:6379/0

# JWT配置
JWT_SECRET_KEY=your_jwt_secret_key_here
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30

# 应用配置
ENVIRONMENT=production
DEBUG=false
API_HOST=0.0.0.0
API_PORT=8000

# 前端配置
FRONTEND_URL=https://your-domain.com
BACKEND_URL=https://api.your-domain.com

# 交易所API配置（加密存储）
EXCHANGE_ENCRYPTION_KEY=your_encryption_key_here
```

#### 3. 创建Docker Compose配置

创建 `docker-compose.prod.yml`：

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:13
    environment:
      POSTGRES_DB: ${POSTGRES_DB}
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped
    networks:
      - chainmakes-network

  redis:
    image: redis:6-alpine
    restart: unless-stopped
    networks:
      - chainmakes-network

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile.prod
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - JWT_SECRET_KEY=${JWT_SECRET_KEY}
      - JWT_ALGORITHM=${JWT_ALGORITHM}
      - JWT_ACCESS_TOKEN_EXPIRE_MINUTES=${JWT_ACCESS_TOKEN_EXPIRE_MINUTES}
      - ENVIRONMENT=${ENVIRONMENT}
      - DEBUG=${DEBUG}
      - EXCHANGE_ENCRYPTION_KEY=${EXCHANGE_ENCRYPTION_KEY}
    depends_on:
      - postgres
      - redis
    restart: unless-stopped
    networks:
      - chainmakes-network

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.prod
    environment:
      - VITE_API_BASE_URL=${BACKEND_URL}
    restart: unless-stopped
    networks:
      - chainmakes-network

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./nginx/ssl:/etc/nginx/ssl
    depends_on:
      - backend
      - frontend
    restart: unless-stopped
    networks:
      - chainmakes-network

volumes:
  postgres_data:

networks:
  chainmakes-network:
    driver: bridge
```

#### 4. 配置Nginx

创建 `nginx/nginx.conf`：

```nginx
events {
    worker_connections 1024;
}

http {
    upstream backend {
        server backend:8000;
    }

    upstream frontend {
        server frontend:3000;
    }

    # HTTP重定向到HTTPS
    server {
        listen 80;
        server_name your-domain.com api.your-domain.com;
        return 301 https://$server_name$request_uri;
    }

    # 前端HTTPS配置
    server {
        listen 443 ssl http2;
        server_name your-domain.com;

        ssl_certificate /etc/nginx/ssl/cert.pem;
        ssl_certificate_key /etc/nginx/ssl/key.pem;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers HIGH:!aNULL:!MD5;

        location / {
            proxy_pass http://frontend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
    }

    # 后端API HTTPS配置
    server {
        listen 443 ssl http2;
        server_name api.your-domain.com;

        ssl_certificate /etc/nginx/ssl/cert.pem;
        ssl_certificate_key /etc/nginx/ssl/key.pem;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers HIGH:!aNULL:!MD5;

        location /api/ {
            proxy_pass http://backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        location /api/v1/ws/ {
            proxy_pass http://backend;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
    }
}
```

#### 5. 创建后端Dockerfile

创建 `backend/Dockerfile.prod`：

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 创建非root用户
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app
USER app

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### 6. 创建前端Dockerfile

创建 `frontend/Dockerfile.prod`：

```dockerfile
# 构建阶段
FROM node:18-alpine as build-stage

WORKDIR /app

# 复制package文件
COPY package*.json ./

# 安装依赖
RUN npm ci --only=production

# 复制源代码
COPY . .

# 构建应用
RUN npm run build

# 生产阶段
FROM nginx:alpine as production-stage

# 复制构建结果
COPY --from=build-stage /app/dist /usr/share/nginx/html

# 复制nginx配置
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 3000

CMD ["nginx", "-g", "daemon off;"]
```

#### 7. 部署应用

```bash
# 克隆代码
git clone <repository-url> .
git checkout main

# 构建并启动服务
docker-compose -f docker-compose.prod.yml up -d

# 初始化数据库
docker-compose -f docker-compose.prod.yml exec backend python scripts/init_db.py

# 检查服务状态
docker-compose -f docker-compose.prod.yml ps
```

### 方案二：传统服务器部署

#### 1. 安装依赖

```bash
# 安装Python 3.11
sudo apt update
sudo apt install python3.11 python3.11-venv python3.11-dev

# 安装Node.js 18
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# 安装PostgreSQL
sudo apt install postgresql postgresql-contrib

# 安装Redis
sudo apt install redis-server

# 安装Nginx
sudo apt install nginx
```

#### 2. 配置数据库

```bash
# 创建数据库用户和数据库
sudo -u postgres psql
CREATE USER chainmakes WITH PASSWORD 'your_password';
CREATE DATABASE chainmakes OWNER chainmakes;
GRANT ALL PRIVILEGES ON DATABASE chainmakes TO chainmakes;
\q
```

#### 3. 部署后端

```bash
# 创建应用目录
sudo mkdir -p /opt/chainmakes/backend
sudo chown $USER:$USER /opt/chainmakes/backend
cd /opt/chainmakes/backend

# 克隆代码
git clone <repository-url> .

# 创建虚拟环境
python3.11 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑.env文件，设置生产环境配置

# 初始化数据库
python scripts/init_db.py

# 创建systemd服务
sudo tee /etc/systemd/system/chainmakes-backend.service > /dev/null <<EOF
[Unit]
Description=ChainMakes Backend
After=network.target

[Service]
Type=exec
User=$USER
WorkingDirectory=/opt/chainmakes/backend
Environment=PATH=/opt/chainmakes/backend/venv/bin
ExecStart=/opt/chainmakes/backend/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# 启动服务
sudo systemctl enable chainmakes-backend
sudo systemctl start chainmakes-backend
```

#### 4. 部署前端

```bash
# 创建前端目录
sudo mkdir -p /opt/chainmakes/frontend
sudo chown $USER:$USER /opt/chainmakes/frontend
cd /opt/chainmakes/frontend

# 克隆代码
git clone <repository-url> .

# 安装依赖
npm install

# 构建生产版本
npm run build

# 配置Nginx
sudo tee /etc/nginx/sites-available/chainmakes > /dev/null <<EOF
server {
    listen 80;
    server_name your-domain.com;

    location / {
        root /opt/chainmakes/frontend/dist;
        try_files \$uri \$uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    location /api/v1/ws/ {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

# 启用站点
sudo ln -s /etc/nginx/sites-available/chainmakes /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 方案三：云平台部署

#### AWS部署

1. **使用ECS Fargate**

```bash
# 创建ECS集群
aws ecs create-cluster --cluster-name chainmakes

# 创建任务定义
aws ecs register-task-definition --cli-input-json file://task-definition.json

# 创建服务
aws ecs create-service \
  --cluster chainmakes \
  --service-name chainmakes-service \
  --task-definition chainmakes:1 \
  --desired-count 1 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-123456],securityGroups=[sg-123456],assignPublicIp=ENABLED}"
```

2. **使用Elastic Beanstalk**

```bash
# 安装EB CLI
pip install awsebcli

# 初始化应用
eb init chainmakes

# 创建环境
eb create production

# 部署应用
eb deploy
```

#### Google Cloud Platform部署

1. **使用Cloud Run**

```bash
# 构建并推送容器镜像
gcloud builds submit --tag gcr.io/PROJECT_ID/chainmakes-backend

# 部署后端服务
gcloud run deploy chainmakes-backend \
  --image gcr.io/PROJECT_ID/chainmakes-backend \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated

# 部署前端服务
gcloud builds submit --tag gcr.io/PROJECT_ID/chainmakes-frontend
gcloud run deploy chainmakes-frontend \
  --image gcr.io/PROJECT_ID/chainmakes-frontend \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

## 安全配置

### 1. SSL/TLS证书

```bash
# 使用Let's Encrypt获取免费证书
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com -d api.your-domain.com

# 设置自动续期
sudo crontab -e
# 添加以下行
0 12 * * * /usr/bin/certbot renew --quiet
```

### 2. 防火墙配置

```bash
# 配置UFW防火墙
sudo ufw enable
sudo ufw allow ssh
sudo ufw allow 'Nginx Full'
sudo ufw status
```

### 3. 数据库安全

```bash
# 配置PostgreSQL安全设置
sudo nano /etc/postgresql/13/main/postgresql.conf
# 设置listen_addresses = 'localhost'

sudo nano /etc/postgresql/13/main/pg_hba.conf
# 配置访问控制

sudo systemctl restart postgresql
```

## 监控和日志

### 1. 应用监控

```bash
# 安装Prometheus和Grafana
docker run -d \
  --name prometheus \
  -p 9090:9090 \
  -v /opt/chainmakes/monitoring/prometheus.yml:/etc/prometheus/prometheus.yml \
  prom/prometheus

docker run -d \
  --name grafana \
  -p 3000:3000 \
  grafana/grafana
```

### 2. 日志管理

```bash
# 配置日志轮转
sudo tee /etc/logrotate.d/chainmakes > /dev/null <<EOF
/opt/chainmakes/backend/logs/*.log {
    daily
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    create 644 $USER $USER
}
EOF
```

### 3. 健康检查

```bash
# 创建健康检查脚本
cat > /opt/chainmakes/healthcheck.sh <<EOF
#!/bin/bash
# 检查后端服务
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "Backend is healthy"
else
    echo "Backend is down, restarting..."
    sudo systemctl restart chainmakes-backend
fi

# 检查前端服务
if curl -f http://localhost:80 > /dev/null 2>&1; then
    echo "Frontend is healthy"
else
    echo "Frontend is down, restarting..."
    sudo systemctl restart nginx
fi
EOF

chmod +x /opt/chainmakes/healthcheck.sh

# 添加到crontab
echo "*/5 * * * * /opt/chainmakes/healthcheck.sh" | crontab -
```

## 备份策略

### 1. 数据库备份

```bash
# 创建备份脚本
cat > /opt/chainmakes/backup.sh <<EOF
#!/bin/bash
DATE=\$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/opt/chainmakes/backups"
mkdir -p \$BACKUP_DIR

# 备份数据库
pg_dump chainmakes > \$BACKUP_DIR/db_backup_\$DATE.sql

# 备份应用配置
tar -czf \$BACKUP_DIR/config_backup_\$DATE.tar.gz /opt/chainmakes/backend/.env

# 删除7天前的备份
find \$BACKUP_DIR -name "*.sql" -mtime +7 -delete
find \$BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete
EOF

chmod +x /opt/chainmakes/backup.sh

# 添加到crontab（每天凌晨2点备份）
echo "0 2 * * * /opt/chainmakes/backup.sh" | crontab -
```

### 2. 文件备份

```bash
# 使用rsync同步到远程服务器
rsync -avz /opt/chainmakes/ user@backup-server:/backup/chainmakes/
```

## 性能优化

### 1. 数据库优化

```sql
-- 创建索引
CREATE INDEX idx_orders_bot_id ON orders(bot_instance_id);
CREATE INDEX idx_positions_bot_id ON positions(bot_instance_id);
CREATE INDEX idx_spread_history_bot_id ON spread_history(bot_instance_id);

-- 配置PostgreSQL参数
-- 在postgresql.conf中设置
shared_buffers = 256MB
effective_cache_size = 1GB
maintenance_work_mem = 64MB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100
random_page_cost = 1.1
effective_io_concurrency = 200
```

### 2. 应用优化

```python
# 在uvicorn启动时添加性能参数
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4 --worker-class uvicorn.workers.UvicornWorker
```

### 3. 缓存配置

```python
# 在应用中配置Redis缓存
REDIS_URL = "redis://localhost:6379/0"
CACHE_TTL = 300  # 5分钟
```

## 故障排除

### 常见问题

1. **服务无法启动**
   - 检查端口是否被占用
   - 查看服务日志
   - 验证环境变量配置

2. **数据库连接失败**
   - 检查数据库服务状态
   - 验证连接字符串
   - 检查防火墙设置

3. **WebSocket连接失败**
   - 检查Nginx配置
   - 验证SSL证书
   - 查看浏览器控制台错误

### 日志查看

```bash
# 查看systemd服务日志
sudo journalctl -u chainmakes-backend -f

# 查看Nginx日志
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log

# 查看应用日志
tail -f /opt/chainmakes/backend/logs/app.log
```

## 更新和维护

### 应用更新

```bash
# 拉取最新代码
git pull origin main

# 更新后端
cd /opt/chainmakes/backend
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart chainmakes-backend

# 更新前端
cd /opt/chainmakes/frontend
npm install
npm run build
sudo systemctl restart nginx
```

### 数据库迁移

```bash
# 运行数据库迁移
cd /opt/chainmakes/backend
source venv/bin/activate
alembic upgrade head
```

---

如有任何问题或需要进一步支持，请联系运维团队或查看项目文档。