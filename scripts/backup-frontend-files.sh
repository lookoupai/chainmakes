#!/bin/bash
# ChainMakes前端文件备份脚本
# 用于在集成Vue3-Element-Admin模板前备份已创建的文件

echo "开始备份前端已创建的文件..."

# 创建备份目录
mkdir -p frontend-backup/api
mkdir -p frontend-backup/stores
mkdir -p frontend-backup/utils

# 备份API文件
if [ -f "frontend/src/api/auth.js" ]; then
  cp frontend/src/api/auth.js frontend-backup/api/
  echo "✓ 已备份 api/auth.js"
fi

# 备份stores文件
if [ -f "frontend/src/stores/auth.js" ]; then
  cp frontend/src/stores/auth.js frontend-backup/stores/
  echo "✓ 已备份 stores/auth.js"
fi

# 备份utils文件
if [ -f "frontend/src/utils/request.js" ]; then
  cp frontend/src/utils/request.js frontend-backup/utils/
  echo "✓ 已备份 utils/request.js"
fi

echo "备份完成! 文件保存在 frontend-backup/ 目录"
echo ""
echo "下一步: 等待 frontend-temp/ 克隆完成后,"
echo "运行以下命令完成模板集成:"
echo ""
echo "  cd frontend-temp"
echo "  rm -rf ../frontend/src"
echo "  cp -r ./* ../frontend/"
echo "  cd ../frontend"
echo "  pnpm install"
echo ""