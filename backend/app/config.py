"""
应用配置管理
"""
from pydantic_settings import BaseSettings
from typing import List, Optional
import os


class Settings(BaseSettings):
    """应用配置类"""
    
    # 应用信息
    APP_NAME: str = "加密货币交易机器人"
    APP_VERSION: str = "1.0.0"
    API_V1_PREFIX: str = "/api/v1"
    
    # 数据库配置 - 同步SQLite用于初始化,异步用于运行时
    # 统一使用 data 目录存储数据库,本地和 Docker 环境保持一致
    DATABASE_URL: str = "sqlite:///./data/chainmakes.db"
    DATABASE_URL_ASYNC: str = "sqlite+aiosqlite:///./data/chainmakes.db"
    DATABASE_POOL_SIZE: int = 5
    DATABASE_MAX_OVERFLOW: int = 10
    
    # Redis配置(可选,暂不使用)
    REDIS_URL: Optional[str] = None
    REDIS_PASSWORD: str = ""
    
    # JWT配置
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # 加密配置
    ENCRYPTION_KEY: str
    
    # CORS配置
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:3333"
    
    @property
    def cors_origins_list(self) -> List[str]:
        """将CORS origins字符串转换为列表"""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
    
    # 日志配置
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/app.log"
    
    # Celery配置(可选,暂不使用)
    CELERY_BROKER_URL: Optional[str] = None
    CELERY_RESULT_BACKEND: Optional[str] = None
    
    # 环境
    ENVIRONMENT: str = "development"
    
    # API限流
    RATE_LIMIT_PER_MINUTE: int = 60
    
    # OKX API 配置
    OKX_IS_DEMO: bool = True
    OKX_API_KEY: str = ""
    OKX_API_SECRET: str = ""
    OKX_PASSPHRASE: str = ""
    OKX_PROXY: str = ""
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# 创建全局配置实例
settings = Settings()