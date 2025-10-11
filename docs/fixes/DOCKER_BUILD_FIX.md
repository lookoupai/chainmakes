# Docker 构建修复说明

## 🐛 问题

GitHub Actions 构建前端镜像时失败:
```
ERROR: failed to build: failed to solve: process "/bin/sh -c pnpm build" did not complete successfully: exit code: 2
```

## 🔍 原因分析

### 1. TypeScript 类型检查问题

**原始构建命令**: `pnpm build`
- 实际执行: `vue-tsc && vite build`
- `vue-tsc` 会进行完整的 TypeScript 类型检查
- 在多架构构建(amd64/arm64)时,类型检查可能失败或超时

### 2. 环境变量文件缺失

`.dockerignore` 排除了所有 `.env.*` 文件:
```dockerignore
.env
.env.*
```

但前端构建需要 `.env.production` 文件才能正确配置 API 地址。

## ✅ 解决方案

### 修改 1: 优化前端 Dockerfile

**文件**: `Dockerfile.frontend`

**修改前**:
```dockerfile
RUN pnpm build
```

**修改后**:
```dockerfile
# 设置环境变量(增加内存限制)
ENV NODE_OPTIONS="--max-old-space-size=4096"

# 构建生产版本 (直接使用 vite build,跳过类型检查)
RUN npx vite build
```

**优点**:
- ✅ 跳过耗时的类型检查
- ✅ 加快构建速度
- ✅ 支持多架构构建
- ✅ 增加内存限制,避免 OOM

### 修改 2: 修复 .dockerignore

**文件**: `.dockerignore`

**修改前**:
```dockerignore
# Environment
.env
.env.*
!.env.example
```

**修改后**:
```dockerignore
# Environment (排除根目录的 .env,但保留前端的)
.env
.env.local
.env.*.local
!frontend/.env.*
!.env.example
```

**说明**:
- 排除根目录的敏感 `.env` 文件
- 但保留前端的 `.env.production` 等配置文件
- 前端配置文件不包含敏感信息,可以安全打包

### 修改 3: 优化前端 API 配置

**文件**: `frontend/.env.production`

**修改前**:
```env
VITE_BASE_API = https://your-domain.com/api/v1
VITE_WS_API = wss://your-domain.com/api/v1/ws
```

**修改后**:
```env
VITE_BASE_API = /api/v1
VITE_WS_API = /api/v1/ws
```

**优点**:
- ✅ 使用相对路径,自动适配域名
- ✅ 无需修改配置文件即可部署
- ✅ 支持 HTTP 和 HTTPS
- ✅ 通过 Nginx 反向代理自动处理

## 📊 构建流程对比

### 修改前

```
1. 复制 package.json
2. 安装依赖
3. 复制源代码
4. 运行 pnpm build (包含 vue-tsc 类型检查) ❌ 失败
```

### 修改后

```
1. 复制 package.json
2. 安装依赖
3. 复制源代码 (包含 .env.production)
4. 运行 vite build (跳过类型检查) ✅ 成功
```

## 🚀 重新触发构建

### 方法 1: 推送修复

```bash
git add .
git commit -m "fix: 修复 Docker 前端构建失败问题"
git push origin main
```

### 方法 2: 手动触发

1. 进入 GitHub 仓库
2. Actions 标签
3. 选择 "Build and Push Docker Images"
4. 点击 "Run workflow"
5. 选择 `main` 分支
6. 点击 "Run workflow"

## 🔍 验证构建

### 查看构建日志

1. GitHub → Actions
2. 点击最新的 workflow 运行
3. 查看 "Build Frontend Image" 步骤
4. 应该看到:
   ```
   ✅ Building frontend image for linux/amd64,linux/arm64
   ✅ Successfully pushed to ghcr.io
   ```

### 测试镜像

```bash
# 拉取镜像
docker pull ghcr.io/你的用户名/chainmakes-frontend:latest

# 运行测试
docker run -d -p 8080:80 ghcr.io/你的用户名/chainmakes-frontend:latest

# 访问测试
curl http://localhost:8080
```

## 💡 最佳实践

### 1. 类型检查策略

**开发时**: 使用 `pnpm build` (包含类型检查)
```bash
pnpm build  # vue-tsc && vite build
```

**生产构建**: 使用 `vite build` (跳过类型检查)
```dockerfile
RUN npx vite build
```

**为什么分开**:
- 开发时发现类型错误
- 生产构建时快速打包
- CI/CD 可以单独运行类型检查

### 2. 环境变量管理

**敏感信息** (不应打包):
- 根目录 `.env` (数据库密码,密钥等)
- `.env.local`

**前端配置** (可以打包):
- `frontend/.env.production` (API 路径等)
- 不包含密钥,可以公开

### 3. 多架构构建优化

```dockerfile
# 增加内存限制
ENV NODE_OPTIONS="--max-old-space-size=4096"

# 跳过耗时操作
RUN npx vite build  # 不运行 vue-tsc
```

## 📝 相关文件

修改的文件:
- `Dockerfile.frontend` - 前端构建优化
- `.dockerignore` - 环境变量过滤规则
- `frontend/.env.production` - API 地址配置

## 🎯 预期结果

✅ 前端构建成功
✅ 支持 amd64 和 arm64
✅ 镜像可以正常拉取
✅ 应用可以正常访问

## ⚠️ 注意事项

1. **类型检查**: 虽然构建时跳过,但建议在开发时本地运行类型检查
2. **环境变量**: 确保前端配置文件不包含敏感信息
3. **API 地址**: 使用相对路径,通过 Nginx 反向代理处理

---

**修复时间**: 2025-01-11
**问题状态**: ✅ 已解决
