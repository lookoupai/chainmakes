# GitHub Docker 镜像自动构建完整教程

## 📚 什么是 GHCR?

**GHCR (GitHub Container Registry)** 是 GitHub 提供的免费 Docker 镜像仓库服务,类似于 Docker Hub。

**优势**:
- ✅ 完全免费
- ✅ 不限下载次数
- ✅ 与 GitHub 仓库深度集成
- ✅ 支持私有镜像
- ✅ 自动化构建

## 🚀 完整配置步骤

### 第 1 步: 准备 GitHub 仓库

#### 1.1 创建 GitHub 仓库

1. 访问 https://github.com
2. 登录你的账号
3. 点击右上角 `+` → `New repository`
4. 填写仓库信息:
   - Repository name: `chainmakes`
   - Description: `加密货币交易机器人`
   - 选择 `Public` (公开) 或 `Private` (私有)
5. 点击 `Create repository`

#### 1.2 推送代码到 GitHub

```bash
# 在项目目录下执行
cd E:\down\网站源码\AI帮写的代码\chainmakes

# 初始化 git (如果还没有)
git init

# 添加所有文件
git add .

# 提交
git commit -m "Initial commit: Add Docker support"

# 添加远程仓库 (替换为你的用户名)
git remote add origin https://github.com/你的用户名/chainmakes.git

# 推送到 GitHub
git push -u origin main
```

### 第 2 步: 配置 GitHub Actions 权限

#### 2.1 启用 Actions 权限

1. 打开你的 GitHub 仓库页面
2. 点击 `Settings` (设置) 标签
3. 左侧菜单找到 `Actions` → `General`
4. 滚动到 **"Workflow permissions"** 部分
5. 选择 `Read and write permissions` ✅
6. 勾选 `Allow GitHub Actions to create and approve pull requests` ✅
7. 点击 `Save` 保存

**截图位置**: Settings → Actions → General → Workflow permissions

### 第 3 步: 触发自动构建

#### 方法 1: 推送代码触发 (推荐)

```bash
# 推送到 main 分支自动触发构建
git push origin main
```

#### 方法 2: 手动触发

1. 进入仓库页面
2. 点击 `Actions` 标签
3. 左侧选择 `Build and Push Docker Images`
4. 点击右侧 `Run workflow` 按钮
5. 选择分支 `main`
6. 点击绿色 `Run workflow` 按钮

#### 方法 3: 创建版本标签 (推荐生产环境)

```bash
# 创建版本标签
git tag v1.0.0
git push origin v1.0.0

# 这会触发构建并自动创建 GitHub Release
```

### 第 4 步: 查看构建进度

#### 4.1 查看 Actions 运行状态

1. 进入仓库页面
2. 点击 `Actions` 标签
3. 看到 workflow 正在运行 (黄色圆圈)
4. 点击进入查看详细日志

**构建时间**: 首次构建约 5-10 分钟

#### 4.2 构建状态说明

- 🟡 黄色圆圈 - 正在构建
- ✅ 绿色对勾 - 构建成功
- ❌ 红色叉号 - 构建失败

### 第 5 步: 查看构建的镜像

#### 5.1 在 GitHub 查看

1. 进入仓库主页
2. 右侧边栏找到 `Packages` 部分
3. 看到两个镜像:
   - `chainmakes-backend`
   - `chainmakes-frontend`
4. 点击进入查看详情和拉取命令

#### 5.2 镜像地址格式

```
ghcr.io/你的用户名/chainmakes-backend:latest
ghcr.io/你的用户名/chainmakes-frontend:latest
```

例如,如果你的 GitHub 用户名是 `zhang3`,镜像地址就是:
```
ghcr.io/zhang3/chainmakes-backend:latest
ghcr.io/zhang3/chainmakes-frontend:latest
```

### 第 6 步: 使用构建的镜像

#### 6.1 公开镜像 (推荐)

**设置镜像为公开**:
1. 进入 Package 页面
2. 点击右侧 `Package settings`
3. 滚动到底部 `Danger Zone`
4. 点击 `Change visibility`
5. 选择 `Public`
6. 确认操作

**直接拉取**:
```bash
# 无需登录,直接拉取
docker pull ghcr.io/你的用户名/chainmakes-backend:latest
docker pull ghcr.io/你的用户名/chainmakes-frontend:latest
```

#### 6.2 私有镜像

**登录 GHCR**:
```bash
# 创建 Personal Access Token (PAT)
# 1. GitHub 右上角头像 → Settings
# 2. 左下角 Developer settings
# 3. Personal access tokens → Tokens (classic)
# 4. Generate new token (classic)
# 5. 勾选 read:packages 和 write:packages
# 6. 生成并复制 token

# 使用 token 登录
echo "你的_TOKEN" | docker login ghcr.io -u 你的用户名 --password-stdin

# 拉取镜像
docker pull ghcr.io/你的用户名/chainmakes-backend:latest
```

#### 6.3 修改 docker-compose.yml 使用镜像

编辑 `docker-compose.yml`:

```yaml
services:
  backend:
    image: ghcr.io/你的用户名/chainmakes-backend:latest
    # 注释掉 build 部分
    # build:
    #   context: .
    #   dockerfile: Dockerfile.backend

  frontend:
    image: ghcr.io/你的用户名/chainmakes-frontend:latest
    # 注释掉 build 部分
    # build:
    #   context: .
    #   dockerfile: Dockerfile.frontend
```

然后启动:
```bash
docker-compose pull  # 拉取最新镜像
docker-compose up -d
```

## 🎯 工作流说明

### 触发条件

工作流会在以下情况自动运行:

1. **推送到 main 分支**
   ```bash
   git push origin main
   ```

2. **推送到 develop 分支**
   ```bash
   git push origin develop
   ```

3. **创建版本标签**
   ```bash
   git tag v1.0.0
   git push origin v1.0.0
   ```

4. **手动触发**
   - Actions 页面点击 "Run workflow"

### 镜像标签规则

根据触发方式,会自动生成不同的标签:

| 触发方式 | 生成的标签 | 示例 |
|---------|-----------|------|
| 推送到 main | `latest` | `ghcr.io/user/app:latest` |
| 推送到 develop | `develop` | `ghcr.io/user/app:develop` |
| 创建标签 v1.0.0 | `v1.0.0`, `1.0`, `1`, `latest` | `ghcr.io/user/app:v1.0.0` |
| 提交 SHA | `main-abc1234` | `ghcr.io/user/app:main-abc1234` |

### 构建架构

自动构建支持两种 CPU 架构:
- `linux/amd64` - 标准 x86_64 服务器
- `linux/arm64` - ARM 服务器 (AWS Graviton, 树莓派等)

Docker 会自动选择匹配的架构。

## 🔧 常见场景

### 场景 1: 开发测试

```bash
# 开发时推送代码
git add .
git commit -m "feat: add new feature"
git push origin main

# 等待构建完成 (5-10分钟)
# 在服务器上拉取最新镜像
docker-compose pull
docker-compose up -d
```

### 场景 2: 发布版本

```bash
# 测试通过后打标签
git tag v1.0.0
git push origin v1.0.0

# 自动构建并创建 GitHub Release
# 使用特定版本部署
docker pull ghcr.io/user/chainmakes-backend:v1.0.0
```

### 场景 3: 多环境部署

```yaml
# 生产环境使用稳定版本
services:
  backend:
    image: ghcr.io/user/chainmakes-backend:v1.0.0

# 测试环境使用最新版本
services:
  backend:
    image: ghcr.io/user/chainmakes-backend:latest
```

## 🐛 常见问题

### 1. 构建失败: Permission denied

**原因**: Actions 权限未开启

**解决**:
1. Settings → Actions → General
2. 选择 `Read and write permissions`
3. 保存并重新运行

### 2. 拉取失败: unauthorized

**原因**: 镜像是私有的

**解决方案 A**: 设置为公开
1. Package settings → Change visibility → Public

**解决方案 B**: 登录后拉取
```bash
echo "TOKEN" | docker login ghcr.io -u 用户名 --password-stdin
docker pull ghcr.io/user/app:latest
```

### 3. 构建超时

**原因**: 网络慢或依赖包大

**解决**:
- 等待完成 (首次构建较慢)
- 使用 GitHub Actions 缓存 (已配置)
- 优化 Dockerfile 减少层数

### 4. 镜像找不到

**检查清单**:
```bash
# 1. 确认构建成功
# Actions 页面查看绿色对勾

# 2. 确认镜像名称正确
# 格式: ghcr.io/用户名/仓库名-backend:latest

# 3. 确认镜像可见性
# Packages 页面查看是否 Public
```

### 5. docker-compose 无法拉取镜像

```bash
# 检查镜像名称
docker-compose config

# 手动测试拉取
docker pull ghcr.io/user/chainmakes-backend:latest

# 查看详细错误
docker-compose pull --verbose
```

## 📊 监控和维护

### 查看构建历史

1. Actions 标签
2. 查看所有 workflow 运行记录
3. 点击查看详细日志

### 镜像管理

1. Packages 页面
2. 查看所有版本
3. 删除旧版本 (可选)

### 自动化最佳实践

1. **开发分支**: 推送到 `develop` 分支测试
2. **主分支**: 推送到 `main` 分支用于生产
3. **版本标签**: 重要版本打标签 `v1.0.0`
4. **保留历史**: 保留最近 3-5 个版本

## 🎓 学习资源

- [GitHub Actions 文档](https://docs.github.com/actions)
- [GHCR 文档](https://docs.github.com/packages/working-with-a-github-packages-registry/working-with-the-container-registry)
- [Docker Buildx 文档](https://docs.docker.com/buildx/working-with-buildx/)

## 📝 总结

### 完整流程回顾

1. ✅ 推送代码到 GitHub
2. ✅ 配置 Actions 权限
3. ✅ 推送代码或打标签触发构建
4. ✅ GitHub Actions 自动构建多架构镜像
5. ✅ 镜像推送到 GHCR
6. ✅ 在服务器拉取镜像部署

### 优势

- 🚀 自动化: 推送即构建
- 🌍 多架构: 同时支持 amd64 和 arm64
- 💰 免费: GitHub 完全免费
- 🔄 版本管理: 自动标签和 Release
- ⚡ 快速: 构建缓存加速

现在你可以像专业项目一样使用 CI/CD 自动构建 Docker 镜像了! 🎉
