/**
 * 前端错误处理工具
 */

// 错误类型枚举
export enum ErrorType {
  NETWORK = 'NETWORK',
  VALIDATION = 'VALIDATION',
  AUTHENTICATION = 'AUTHENTICATION',
  AUTHORIZATION = 'AUTHORIZATION',
  NOT_FOUND = 'NOT_FOUND',
  BUSINESS_LOGIC = 'BUSINESS_LOGIC',
  EXCHANGE_API = 'EXCHANGE_API',
  WEBSOCKET = 'WEBSOCKET',
  UNKNOWN = 'UNKNOWN'
}

// 错误接口
export interface ApiError {
  code: string
  message: string
  details: Record<string, any>
}

// 自定义错误类
export class AppError extends Error {
  public readonly type: ErrorType
  public readonly code: string
  public readonly details: Record<string, any>
  public readonly originalError?: any

  constructor(
    message: string,
    type: ErrorType = ErrorType.UNKNOWN,
    code = 'UNKNOWN_ERROR',
    details: Record<string, any> = {},
    originalError?: any
  ) {
    super(message)
    this.name = 'AppError'
    this.type = type
    this.code = code
    this.details = details
    this.originalError = originalError

    // 确保错误堆栈正确
    if (Error.captureStackTrace) {
      Error.captureStackTrace(this, AppError)
    }
  }

  // 静态工厂方法
  static fromApiError(error: ApiError): AppError {
    const type = this.getErrorTypeFromCode(error.code)
    return new AppError(error.message, type, error.code, error.details)
  }

  static fromHttpError(response: Response, data?: any): AppError {
    const status = response.status
    let type = ErrorType.UNKNOWN
    let message = '请求失败'
    let code = `HTTP_${status}`
    let details: Record<string, any> = { status }

    if (data && data.error) {
      message = data.error.message || message
      code = data.error.code || code
      details = { ...details, ...data.error.details }
    }

    // 根据状态码确定错误类型
    if (status === 400) {
      type = ErrorType.VALIDATION
    } else if (status === 401) {
      type = ErrorType.AUTHENTICATION
    } else if (status === 403) {
      type = ErrorType.AUTHORIZATION
    } else if (status === 404) {
      type = ErrorType.NOT_FOUND
    } else if (status === 409) {
      type = ErrorType.BUSINESS_LOGIC
    } else if (status === 422) {
      type = ErrorType.VALIDATION
    } else if (status >= 500) {
      type = ErrorType.NETWORK
    }

    return new AppError(message, type, code, details)
  }

  static fromNetworkError(error: any): AppError {
    let message = '网络连接失败'
    let details: Record<string, any> = {}

    if (error.message) {
      details.originalMessage = error.message
    }

    if (error.code === 'NETWORK_ERROR') {
      message = '网络连接失败，请检查网络设置'
    } else if (error.code === 'TIMEOUT') {
      message = '请求超时，请稍后重试'
    } else if (error.code === 'ECONNREFUSED') {
      message = '无法连接到服务器'
    }

    return new AppError(message, ErrorType.NETWORK, error.code || 'NETWORK_ERROR', details, error)
  }

  static fromValidationError(errors: any[]): AppError {
    const details = { errors }
    const message = '数据验证失败'
    return new AppError(message, ErrorType.VALIDATION, 'VALIDATION_ERROR', details)
  }

  private static getErrorTypeFromCode(code: string): ErrorType {
    if (code.includes('VALIDATION')) return ErrorType.VALIDATION
    if (code.includes('AUTHENTICATION')) return ErrorType.AUTHENTICATION
    if (code.includes('AUTHORIZATION')) return ErrorType.AUTHORIZATION
    if (code.includes('NOT_FOUND')) return ErrorType.NOT_FOUND
    if (code.includes('BUSINESS_LOGIC')) return ErrorType.BUSINESS_LOGIC
    if (code.includes('EXCHANGE_API')) return ErrorType.EXCHANGE_API
    if (code.includes('WEBSOCKET')) return ErrorType.WEBSOCKET
    if (code.includes('HTTP_')) {
      const status = parseInt(code.split('_')[1])
      if (status === 400 || status === 422) return ErrorType.VALIDATION
      if (status === 401) return ErrorType.AUTHENTICATION
      if (status === 403) return ErrorType.AUTHORIZATION
      if (status === 404) return ErrorType.NOT_FOUND
      if (status === 409) return ErrorType.BUSINESS_LOGIC
      if (status >= 500) return ErrorType.NETWORK
    }
    return ErrorType.UNKNOWN
  }

  // 判断是否为特定类型的错误
  isType(type: ErrorType): boolean {
    return this.type === type
  }

  // 获取用户友好的错误消息
  getUserFriendlyMessage(): string {
    switch (this.type) {
      case ErrorType.NETWORK:
        return '网络连接失败，请检查网络设置后重试'
      case ErrorType.VALIDATION:
        return '输入数据不正确，请检查后重试'
      case ErrorType.AUTHENTICATION:
        return '登录已过期，请重新登录'
      case ErrorType.AUTHORIZATION:
        return '您没有权限执行此操作'
      case ErrorType.NOT_FOUND:
        return '请求的资源不存在'
      case ErrorType.BUSINESS_LOGIC:
        return this.message || '操作失败，请稍后重试'
      case ErrorType.EXCHANGE_API:
        return '交易所接口异常，请稍后重试'
      case ErrorType.WEBSOCKET:
        return '实时连接异常，请刷新页面重试'
      default:
        return this.message || '发生未知错误，请稍后重试'
    }
  }
}

// 错误处理器类
export class ErrorHandler {
  private static instance: ErrorHandler
  private errorListeners: Array<(error: AppError) => void> = []

  private constructor() {}

  static getInstance(): ErrorHandler {
    if (!ErrorHandler.instance) {
      ErrorHandler.instance = new ErrorHandler()
    }
    return ErrorHandler.instance
  }

  // 添加错误监听器
  addErrorListener(listener: (error: AppError) => void): void {
    this.errorListeners.push(listener)
  }

  // 移除错误监听器
  removeErrorListener(listener: (error: AppError) => void): void {
    const index = this.errorListeners.indexOf(listener)
    if (index !== -1) {
      this.errorListeners.splice(index, 1)
    }
  }

  // 处理错误
  handleError(error: any): AppError {
    let appError: AppError

    if (error instanceof AppError) {
      appError = error
    } else if (error.response) {
      // HTTP错误
      appError = AppError.fromHttpError(error.response, error.response.data)
    } else if (error.request) {
      // 网络错误
      appError = AppError.fromNetworkError(error)
    } else if (error.error && error.error.code) {
      // API错误
      appError = AppError.fromApiError(error.error)
    } else {
      // 未知错误
      appError = new AppError(
        error.message || '发生未知错误',
        ErrorType.UNKNOWN,
        'UNKNOWN_ERROR',
        {},
        error
      )
    }

    // 通知所有监听器
    this.notifyListeners(appError)

    // 记录错误
    this.logError(appError)

    return appError
  }

  // 通知所有监听器
  private notifyListeners(error: AppError): void {
    this.errorListeners.forEach(listener => {
      try {
        listener(error)
      } catch (e) {
        console.error('Error in error listener:', e)
      }
    })
  }

  // 记录错误
  private logError(error: AppError): void {
    const logData = {
      type: error.type,
      code: error.code,
      message: error.message,
      details: error.details,
      stack: error.stack,
      timestamp: new Date().toISOString()
    }

    if (error.type === ErrorType.NETWORK || error.type === ErrorType.UNKNOWN) {
      console.error('Application Error:', logData)
    } else {
      console.warn('Application Error:', logData)
    }
  }
}

// 全局错误处理器实例
export const errorHandler = ErrorHandler.getInstance()

// 全局错误处理函数
export function handleError(error: any): AppError {
  return errorHandler.handleError(error)
}

// Vue错误处理插件
export function createErrorHandlerPlugin() {
  return {
    install(app: any) {
      // 全局错误处理
      app.config.errorHandler = (err: any, vm: any, info: string) => {
        const error = handleError(err)
        console.error('Vue Error:', err, info)
      }

      // 添加全局属性
      app.config.globalProperties.$handleError = handleError
      app.config.globalProperties.$errorHandler = errorHandler
    }
  }
}

// 组合式API
export function useErrorHandler() {
  const handleError = (error: any) => {
    return errorHandler.handleError(error)
  }

  const addErrorListener = (listener: (error: AppError) => void) => {
    errorHandler.addErrorListener(listener)
  }

  const removeErrorListener = (listener: (error: AppError) => void) => {
    errorHandler.removeErrorListener(listener)
  }

  return {
    handleError,
    addErrorListener,
    removeErrorListener
  }
}