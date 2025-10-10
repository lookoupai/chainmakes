"""
全局异常处理器
"""
import logging
from typing import Union
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from httpx import HTTPError as HTTPXError

from app.core.exceptions import (
    BaseCustomException,
    create_http_exception,
    DatabaseError,
    ExternalServiceError
)

logger = logging.getLogger(__name__)


async def custom_exception_handler(request: Request, exc: BaseCustomException) -> JSONResponse:
    """处理自定义异常"""
    logger.error(
        f"Custom exception: {exc.error_code} - {exc.message}",
        extra={
            "details": exc.details,
            "path": str(request.url),
            "method": request.method
        }
    )
    
    http_exc = create_http_exception(exc)
    return JSONResponse(
        status_code=http_exc.status_code,
        content=http_exc.detail
    )


async def http_exception_handler(request: Request, exc: Union[HTTPException, StarletteHTTPException]) -> JSONResponse:
    """处理HTTP异常"""
    logger.warning(
        f"HTTP exception: {exc.status_code} - {exc.detail}",
        extra={
            "path": str(request.url),
            "method": request.method
        }
    )
    
    # 如果已经是格式化的错误响应，直接返回
    if isinstance(exc.detail, dict) and "error" in exc.detail:
        return JSONResponse(
            status_code=exc.status_code,
            content=exc.detail
        )
    
    # 否则格式化错误响应
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": f"HTTP_{exc.status_code}",
                "message": str(exc.detail),
                "details": {}
            }
        }
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """处理请求验证异常"""
    logger.warning(
        f"Validation error: {exc.errors()}",
        extra={
            "path": str(request.url),
            "method": request.method
        }
    )
    
    # 格式化验证错误
    formatted_errors = []
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error["loc"])
        formatted_errors.append({
            "field": field,
            "message": error["msg"],
            "type": error["type"],
            "value": error.get("input")
        })
    
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "请求参数验证失败",
                "details": {
                    "errors": formatted_errors
                }
            }
        }
    )


async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError) -> JSONResponse:
    """处理SQLAlchemy异常"""
    logger.error(
        f"Database error: {str(exc)}",
        extra={
            "path": str(request.url),
            "method": request.method,
            "exception_type": type(exc).__name__
        },
        exc_info=True
    )
    
    # 处理完整性约束错误
    if isinstance(exc, IntegrityError):
        return JSONResponse(
            status_code=409,
            content={
                "error": {
                    "code": "INTEGRITY_ERROR",
                    "message": "数据完整性约束违反",
                    "details": {
                        "original_error": str(exc.orig) if hasattr(exc, 'orig') else None
                    }
                }
            }
        )
    
    # 处理其他数据库错误
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "DATABASE_ERROR",
                "message": "数据库操作失败",
                "details": {}
            }
        }
    )


async def httpx_exception_handler(request: Request, exc: HTTPXError) -> JSONResponse:
    """处理HTTP客户端异常"""
    logger.error(
        f"HTTP client error: {str(exc)}",
        extra={
            "path": str(request.url),
            "method": request.method,
            "exception_type": type(exc).__name__
        }
    )
    
    return JSONResponse(
        status_code=502,
        content={
            "error": {
                "code": "EXTERNAL_SERVICE_ERROR",
                "message": "外部服务请求失败",
                "details": {
                    "service_error": str(exc)
                }
            }
        }
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """处理通用异常"""
    logger.error(
        f"Unhandled exception: {str(exc)}",
        extra={
            "path": str(request.url),
            "method": request.method,
            "exception_type": type(exc).__name__
        },
        exc_info=True
    )
    
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "服务器内部错误",
                "details": {}
            }
        }
    )


def setup_exception_handlers(app):
    """设置异常处理器"""
    app.add_exception_handler(BaseCustomException, custom_exception_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(SQLAlchemyError, sqlalchemy_exception_handler)
    app.add_exception_handler(HTTPXError, httpx_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler)