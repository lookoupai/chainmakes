"""
自定义异常类
"""
from typing import Any, Dict, Optional
from fastapi import HTTPException, status


class BaseCustomException(Exception):
    """基础自定义异常类"""
    
    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        error_code: Optional[str] = None
    ):
        self.message = message
        self.details = details or {}
        self.error_code = error_code
        super().__init__(self.message)


class ValidationError(BaseCustomException):
    """验证错误"""
    
    def __init__(self, message: str, field: Optional[str] = None, value: Optional[Any] = None):
        details = {}
        if field:
            details["field"] = field
        if value is not None:
            details["value"] = value
        super().__init__(message, details, "VALIDATION_ERROR")


class AuthenticationError(BaseCustomException):
    """认证错误"""
    
    def __init__(self, message: str = "认证失败"):
        super().__init__(message, {}, "AUTHENTICATION_ERROR")


class AuthorizationError(BaseCustomException):
    """授权错误"""
    
    def __init__(self, message: str = "权限不足"):
        super().__init__(message, {}, "AUTHORIZATION_ERROR")


class NotFoundError(BaseCustomException):
    """资源不存在错误"""
    
    def __init__(self, resource: str, identifier: Optional[str] = None):
        message = f"{resource}不存在"
        if identifier:
            message += f": {identifier}"
        details = {"resource": resource}
        if identifier:
            details["identifier"] = identifier
        super().__init__(message, details, "NOT_FOUND_ERROR")


class ConflictError(BaseCustomException):
    """冲突错误"""
    
    def __init__(self, message: str, resource: Optional[str] = None):
        details = {}
        if resource:
            details["resource"] = resource
        super().__init__(message, details, "CONFLICT_ERROR")


class BusinessLogicError(BaseCustomException):
    """业务逻辑错误"""
    
    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None):
        super().__init__(message, context, "BUSINESS_LOGIC_ERROR")


class ExchangeAPIError(BaseCustomException):
    """交易所API错误"""
    
    def __init__(
        self,
        message: str,
        exchange: Optional[str] = None,
        exchange_code: Optional[str] = None,
        exchange_details: Optional[Dict[str, Any]] = None
    ):
        details = {}
        if exchange:
            details["exchange"] = exchange
        if exchange_code:
            details["exchange_code"] = exchange_code
        if exchange_details:
            details["exchange_details"] = exchange_details
        super().__init__(message, details, "EXCHANGE_API_ERROR")


class InsufficientBalanceError(BusinessLogicError):
    """余额不足错误"""
    
    def __init__(self, currency: str, required: float, available: float):
        message = f"{currency}余额不足: 需要 {required}, 可用 {available}"
        context = {
            "currency": currency,
            "required": required,
            "available": available
        }
        super().__init__(message, context)


class OrderExecutionError(BusinessLogicError):
    """订单执行错误"""
    
    def __init__(
        self,
        message: str,
        symbol: Optional[str] = None,
        order_type: Optional[str] = None,
        side: Optional[str] = None
    ):
        context = {}
        if symbol:
            context["symbol"] = symbol
        if order_type:
            context["order_type"] = order_type
        if side:
            context["side"] = side
        super().__init__(message, context)


class BotEngineError(BusinessLogicError):
    """机器人引擎错误"""
    
    def __init__(
        self,
        message: str,
        bot_id: Optional[int] = None,
        operation: Optional[str] = None
    ):
        context = {}
        if bot_id:
            context["bot_id"] = bot_id
        if operation:
            context["operation"] = operation
        super().__init__(message, context)


class WebSocketError(BaseCustomException):
    """WebSocket错误"""
    
    def __init__(
        self,
        message: str,
        connection_id: Optional[str] = None,
        bot_id: Optional[int] = None
    ):
        details = {}
        if connection_id:
            details["connection_id"] = connection_id
        if bot_id:
            details["bot_id"] = bot_id
        super().__init__(message, details, "WEBSOCKET_ERROR")


class DatabaseError(BaseCustomException):
    """数据库错误"""
    
    def __init__(self, message: str, operation: Optional[str] = None):
        details = {}
        if operation:
            details["operation"] = operation
        super().__init__(message, details, "DATABASE_ERROR")


class ExternalServiceError(BaseCustomException):
    """外部服务错误"""
    
    def __init__(
        self,
        message: str,
        service: Optional[str] = None,
        status_code: Optional[int] = None,
        response: Optional[Dict[str, Any]] = None
    ):
        details = {}
        if service:
            details["service"] = service
        if status_code:
            details["status_code"] = status_code
        if response:
            details["response"] = response
        super().__init__(message, details, "EXTERNAL_SERVICE_ERROR")


# HTTP异常映射
def create_http_exception(exc: BaseCustomException) -> HTTPException:
    """将自定义异常转换为HTTP异常"""
    
    status_code_map = {
        ValidationError: status.HTTP_422_UNPROCESSABLE_ENTITY,
        AuthenticationError: status.HTTP_401_UNAUTHORIZED,
        AuthorizationError: status.HTTP_403_FORBIDDEN,
        NotFoundError: status.HTTP_404_NOT_FOUND,
        ConflictError: status.HTTP_409_CONFLICT,
        BusinessLogicError: status.HTTP_400_BAD_REQUEST,
        ExchangeAPIError: status.HTTP_502_BAD_GATEWAY,
        BotEngineError: status.HTTP_500_INTERNAL_SERVER_ERROR,
        WebSocketError: status.HTTP_500_INTERNAL_SERVER_ERROR,
        DatabaseError: status.HTTP_500_INTERNAL_SERVER_ERROR,
        ExternalServiceError: status.HTTP_502_BAD_GATEWAY,
    }
    
    status_code = status_code_map.get(type(exc), status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    content = {
        "error": {
            "code": exc.error_code,
            "message": exc.message,
            "details": exc.details
        }
    }
    
    return HTTPException(status_code=status_code, detail=content)