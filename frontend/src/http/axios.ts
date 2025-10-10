import type { AxiosInstance, AxiosRequestConfig } from "axios"
import { getToken } from "@@/utils/cache/cookies"
import axios from "axios"
import { get, merge } from "lodash-es"
import { useUserStore } from "@/pinia/stores/user"
import { ElMessage } from "element-plus"
import { errorHandler, AppError } from "@/common/utils/error-handler"

/** 退出登录并强制刷新页面（会重定向到登录页） */
function logout() {
  useUserStore().logout()
  location.reload()
}

/** 创建请求实例 */
function createInstance() {
  // 创建一个 axios 实例命名为 instance
  const instance = axios.create()
  // 请求拦截器
  instance.interceptors.request.use(
    // 发送之前
    config => config,
    // 发送失败
    error => Promise.reject(error)
  )
  // 响应拦截器（可根据具体业务作出相应的调整）
  instance.interceptors.response.use(
    (response) => {
      // apiData 是 api 返回的数据
      const apiData = response.data
      // 二进制数据则直接返回
      const responseType = response.config.responseType
      if (responseType === "blob" || responseType === "arraybuffer") return apiData
      
      // FastAPI 后端适配: 直接返回数据,包装成标准格式
      const url = response.config.url || ''
      
      // 认证接口特殊处理
      if (url.includes('auth/login') || url.includes('auth/register') || url.includes('auth/refresh')) {
        return apiData
      }
      
      // 检查是否有错误响应格式
      if (apiData && apiData.error) {
        // 使用全局错误处理器处理API错误
        const appError = AppError.fromApiError(apiData.error)
        errorHandler.handleError(appError)
        
        // 对于认证错误，执行登出
        if (appError.isType('AUTHENTICATION')) {
          logout()
        }
        
        return Promise.reject(appError)
      }
      
      // 如果没有 code 字段,包装成标准格式
      if (apiData.code === undefined) {
        // FastAPI 直接返回数据对象,包装为标准响应
        return {
          code: 0,
          data: apiData,
          message: 'success'
        }
      }
      
      // 有 code 字段,按原逻辑处理
      const code = apiData.code
      switch (code) {
        case 0:
          // 本系统采用 code === 0 来表示没有业务错误
          return apiData
        case 401:
          // Token 过期时
          logout()
          return Promise.reject(new AppError("登录已过期", "AUTHENTICATION", "AUTH_EXPIRED"))
        default:
          // 不是正确的 code
          const appError = new AppError(apiData.message || "Error", "UNKNOWN", apiData.code || "UNKNOWN_ERROR")
          errorHandler.handleError(appError)
          return Promise.reject(appError)
      }
    },
    (error) => {
      // 使用全局错误处理器处理HTTP错误
      const appError = errorHandler.handleError(error)
      
      // 对于认证错误，执行登出
      if (appError.isType('AUTHENTICATION')) {
        logout()
      }
      
      // 显示用户友好的错误消息
      ElMessage.error(appError.getUserFriendlyMessage())
      
      return Promise.reject(appError)
    }
  )
  return instance
}

/** 创建请求方法 */
function createRequest(instance: AxiosInstance) {
  return <T>(config: AxiosRequestConfig): Promise<T> => {
    const token = getToken()
    // 默认配置
    const defaultConfig: AxiosRequestConfig = {
      // 接口地址
      baseURL: import.meta.env.VITE_BASE_API,
      // 请求头
      headers: {
        // 携带 Token
        "Authorization": token ? `Bearer ${token}` : undefined,
        "Content-Type": "application/json"
      },
      // 请求体
      data: {},
      // 请求超时
      timeout: 5000,
      // 跨域请求时是否携带 Cookies
      withCredentials: false
    }
    // 将默认配置 defaultConfig 和传入的自定义配置 config 进行合并成为 mergeConfig
    const mergeConfig = merge(defaultConfig, config)
    return instance(mergeConfig)
  }
}

/** 用于请求的实例 */
const instance = createInstance()

/** 用于请求的方法 */
export const request = createRequest(instance)

/** 默认导出 */
export default request
