"""
FastAPI应用主入口
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import settings
from app.db.session import engine
from app.db.base import Base
from app.api.v1 import auth, users, exchanges, bots, orders, websocket
from app.core.error_handlers import setup_exception_handlers


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时执行
    print("[INFO] 应用启动中...")
    
    # 创建数据库表(如果不存在)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all, checkfirst=True)
    
    # 恢复运行中的机器人
    try:
        from app.services.bot_manager import bot_manager
        from app.db.session import AsyncSessionLocal
        
        print("[INFO] 恢复运行中的机器人...")
        async with AsyncSessionLocal() as db:
            recovered_count = await bot_manager.recover_running_bots(db)
            print(f"[INFO] 成功恢复 {recovered_count} 个机器人")
    except Exception as e:
        print(f"[ERROR] 恢复机器人失败: {str(e)}")
        import traceback
        traceback.print_exc()
    
    yield
    
    # 关闭时执行
    print("[INFO] 应用关闭中...")
    
    # 停止所有运行中的机器人
    try:
        from app.services.bot_manager import bot_manager
        print("[INFO] 停止所有运行中的机器人...")
        await bot_manager.cleanup()
        print("[INFO] 所有机器人已停止")
    except Exception as e:
        print(f"[ERROR] 停止机器人失败: {str(e)}")
    
    await engine.dispose()


# 创建FastAPI应用实例
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 设置异常处理器
setup_exception_handlers(app)

# 注册路由
app.include_router(auth.router, prefix=f"{settings.API_V1_PREFIX}/auth", tags=["认证"])
app.include_router(users.router, prefix=f"{settings.API_V1_PREFIX}/users", tags=["用户"])
app.include_router(exchanges.router, prefix=f"{settings.API_V1_PREFIX}/exchanges", tags=["交易所"])
app.include_router(bots.router, prefix=f"{settings.API_V1_PREFIX}/bots", tags=["机器人"])
app.include_router(orders.router, prefix=f"{settings.API_V1_PREFIX}/orders", tags=["订单"])
app.include_router(websocket.router, prefix=f"{settings.API_V1_PREFIX}/ws", tags=["WebSocket"])


@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "加密货币交易机器人API",
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )