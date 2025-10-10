# ChainMakes 部署指南 (无需 Docker)

本文档介绍如何在**不使用 Docker** 的情况下部署 ChainMakes 项目。

---

## 🖥️ 本地开发环境 (推荐)

### 快速启动

#### 方式1: 使用启动脚本 (最简单)

**Windows**:
```bash
# 双击运行
start.bat

# 或命令行运行
.\start.bat
```

**停止服务**:
```bash
stop.bat
```

#### 方式2: 手动启动

**后端**:
```bash
cd backend
venv\Scripts\activate          # Windows
source venv/bin/activate       # Linux/Mac
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

**前端**:
```bash
cd frontend
pnpm install  # 首次运行
pnpm dev
```

### 访问地址

- **前端**: http://localhost:3333
- **后端 API**: http://localhost:8000
- **API 文档**: http://localhost:8000/docs
- **默认账户**: admin / admin123

---

## 🌐 生产环境部署

### Windows 服务器部署

#### 方案 A: 使用 PM2 (推荐)

**1. 安装 PM2**:
```bash
npm install -g pm2
npm install -g pm2-windows-startup

# 配置开机自启
pm2-startup install
```

**2. 部署后端**:
```bash
cd backend

# 启动后端服务
pm2 start ecosystem.config.js --only backend

# 或直接启动
pm2 start "venv\Scripts\python.exe" --name chainmakes-backend -- -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

**3. 部署前端**:
```bash
cd frontend

# 构建生产版本
pnpm build

# 使用 serve 托管 (简单)
npm install -g serve
pm2 start "serve" --name chainmakes-frontend -- -s dist -p 3333

# 或使用 IIS/Nginx 托管
```

**4. PM2 常用命令**:
```bash
pm2 list              # 查看所有服务
pm2 logs              # 查看日志
pm2 restart all       # 重启所有服务
pm2 stop all          # 停止所有服务
pm2 save              # 保存当前配置
pm2 startup           # 配置开机自启
```

创建 `backend/ecosystem.config.js`:
```javascript
module.exports = {
  apps: [{
    name: 'chainmakes-backend',
    cwd: __dirname,
    interpreter: 'venv/Scripts/python.exe',
    script: '-m',
    args: 'uvicorn app.main:app --host 0.0.0.0 --port 8000',
    instances: 1,
    autorestart: true,
    watch: false,
    max_memory_restart: '1G',
    env: {
      NODE_ENV: 'production'
    }
  }]
}
```

---

#### 方案 B: 使用 NSSM (Windows 服务)

**1. 下载 NSSM**:
- 访问: https://nssm.cc/download
- 解压到任意目录

**2. 安装后端服务**:
```bash
# 打开管理员命令行
nssm install ChainMakesBackend "E:\path\to\backend\venv\Scripts\python.exe" "-m uvicorn app.main:app --host 0.0.0.0 --port 8000"
nssm set ChainMakesBackend AppDirectory "E:\path\to\backend"
nssm set ChainMakesBackend DisplayName "ChainMakes Backend"
nssm set ChainMakesBackend Description "ChainMakes 交易机器人后端服务"

# 启动服务
nssm start ChainMakesBackend

# 其他命令
nssm stop ChainMakesBackend     # 停止
nssm restart ChainMakesBackend  # 重启
nssm remove ChainMakesBackend   # 删除服务
```

**3. 前端部署**:

使用 **IIS** 托管:
```
1. 打开 IIS 管理器
2. 添加网站
3. 物理路径: E:\path\to\frontend\dist
4. 端口: 3333 或 80
5. 启动网站
```

---

### Linux 服务器部署

#### 使用 systemd

**1. 创建后端服务**:
```bash
sudo nano /etc/systemd/system/chainmakes-backend.service
```

```ini
[Unit]
Description=ChainMakes Backend Service
After=network.target

[Service]
Type=simple
User=youruser
WorkingDirectory=/path/to/chainmakes/backend
ExecStart=/path/to/chainmakes/backend/venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

# 环境变量
Environment="PATH=/path/to/chainmakes/backend/venv/bin"
Environment="PYTHONUNBUFFERED=1"

# 日志
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

**2. 启动服务**:
```bash
sudo systemctl daemon-reload
sudo systemctl start chainmakes-backend
sudo systemctl enable chainmakes-backend  # 开机自启

# 查看状态
sudo systemctl status chainmakes-backend

# 查看日志
sudo journalctl -u chainmakes-backend -f
```

**3. 部署前端 (使用 Nginx)**:
```bash
# 构建前端
cd /path/to/frontend
pnpm build

# 配置 Nginx
sudo nano /etc/nginx/sites-available/chainmakes
```

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # 前端静态文件
    location / {
        root /path/to/frontend/dist;
        try_files $uri $uri/ /index.html;

        # 启用 Gzip
        gzip on;
        gzip_types text/plain text/css application/json application/javascript text/xml application/xml;
    }

    # 后端 API 代理
    location /api {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    # WebSocket 支持
    location /api/v1/ws {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

```bash
# 启用站点
sudo ln -s /etc/nginx/sites-available/chainmakes /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

---

## 🔒 生产环境配置

### 1. 环境变量配置

创建 `backend/.env.production`:
```env
# 应用配置
APP_ENV=production
DEBUG=False
SECRET_KEY=your-very-secure-secret-key-here

# 数据库配置 (可选升级为 PostgreSQL)
DATABASE_URL=sqlite:///./chainmakes.db
# DATABASE_URL=postgresql://user:password@localhost/chainmakes

# OKX API (使用真实 API)
OKX_IS_DEMO=False
OKX_API_KEY=your-real-api-key
OKX_API_SECRET=your-real-secret
OKX_PASSPHRASE=your-passphrase

# CORS 配置
ALLOWED_ORIGINS=https://your-domain.com,http://localhost:3333

# JWT 配置
JWT_SECRET_KEY=another-very-secure-secret
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### 2. 数据库迁移到 PostgreSQL (可选)

**安装 PostgreSQL**:
```bash
# Windows: 下载安装包
# https://www.postgresql.org/download/windows/

# Linux
sudo apt install postgresql postgresql-contrib
```

**创建数据库**:
```bash
sudo -u postgres psql
CREATE DATABASE chainmakes;
CREATE USER chainmakes_user WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE chainmakes TO chainmakes_user;
\q
```

**更新配置**:
```bash
# 安装驱动
pip install psycopg2-binary

# 修改 .env
DATABASE_URL=postgresql://chainmakes_user:secure_password@localhost/chainmakes
```

### 3. HTTPS 配置

**使用 Let's Encrypt (免费)**:
```bash
# 安装 certbot
sudo apt install certbot python3-certbot-nginx

# 获取证书
sudo certbot --nginx -d your-domain.com

# 自动续期
sudo certbot renew --dry-run
```

---

## 📊 监控和维护

### 日志管理

**PM2 日志**:
```bash
pm2 logs                    # 实时日志
pm2 logs --lines 200        # 最近 200 行
pm2 flush                   # 清空日志
```

**systemd 日志**:
```bash
sudo journalctl -u chainmakes-backend -f          # 实时
sudo journalctl -u chainmakes-backend --since today
sudo journalctl -u chainmakes-backend -n 100       # 最近 100 行
```

### 性能监控

**PM2 监控**:
```bash
pm2 monit                   # 实时监控
pm2 status                  # 查看状态
```

**系统资源**:
```bash
# Windows
tasklist | findstr python
tasklist | findstr node

# Linux
htop
top
```

---

## 🔧 故障排查

### 常见问题

#### 1. 端口被占用

**Windows**:
```bash
# 查看端口占用
netstat -ano | findstr :8000

# 结束进程
taskkill /F /PID <进程ID>
```

**Linux**:
```bash
# 查看端口占用
sudo lsof -i :8000

# 结束进程
sudo kill <进程ID>
```

#### 2. 服务无法启动

**检查日志**:
```bash
# PM2
pm2 logs chainmakes-backend --lines 50

# systemd
sudo journalctl -u chainmakes-backend -n 50

# 手动测试
cd backend
source venv/bin/activate
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

#### 3. 前端打包失败

```bash
# 清理缓存
cd frontend
rm -rf node_modules dist
pnpm install
pnpm build

# 检查 Node 版本
node --version  # 需要 18+
```

---

## ✅ 部署检查清单

### 上线前检查

- [ ] 修改默认管理员密码
- [ ] 配置生产环境变量
- [ ] 启用 HTTPS
- [ ] 配置 CORS 白名单
- [ ] 设置防火墙规则
- [ ] 配置自动备份
- [ ] 设置监控告警
- [ ] 测试故障恢复

### 安全检查

- [ ] API 密钥不在代码中
- [ ] 数据库访问控制
- [ ] 禁用调试模式
- [ ] 设置请求速率限制
- [ ] 日志敏感信息脱敏

---

## 📞 技术支持

如遇到部署问题,请检查:

1. **文档**: 查看本文档和项目 README
2. **日志**: 检查应用日志和系统日志
3. **测试**: 使用测试脚本验证功能
4. **配置**: 确认环境变量和配置文件

---

**最后更新**: 2025-10-06
**适用版本**: ChainMakes v1.0.0
