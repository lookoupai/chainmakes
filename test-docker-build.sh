#!/bin/bash

# 测试 Docker 构建脚本

echo "🔨 测试前端 Docker 构建..."

# 只构建 amd64 (更快)
docker buildx build \
  --platform linux/amd64 \
  -f Dockerfile.frontend \
  -t chainmakes-frontend:test \
  --progress=plain \
  --load \
  .

if [ $? -eq 0 ]; then
    echo "✅ 前端构建成功!"

    echo "🧪 测试运行..."
    docker run -d -p 8080:80 --name test-frontend chainmakes-frontend:test

    sleep 3

    echo "📊 测试访问..."
    curl -I http://localhost:8080

    echo "🧹 清理..."
    docker stop test-frontend
    docker rm test-frontend

    echo "✅ 测试完成!"
else
    echo "❌ 前端构建失败"
    exit 1
fi
