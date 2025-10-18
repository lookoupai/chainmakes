/** 交易所账户API相关类型定义 */

/** 交易所账户创建请求 */
export interface ExchangeAccountCreateRequest {
  exchange_name: 'okx' | 'binance' | 'bybit'
  api_key: string
  api_secret: string
  passphrase?: string  // OKX需要
  is_testnet: boolean  // true=测试网/模拟盘, false=真实环境
}

/** 交易所账户更新请求 */
export interface ExchangeAccountUpdateRequest {
  api_key?: string
  api_secret?: string
  passphrase?: string
  is_active?: boolean
  is_testnet?: boolean
}

/** 交易所账户响应数据 */
export interface ExchangeAccountResponse {
  id: number
  user_id: number
  exchange_name: string
  api_key: string  // 前端显示时应脱敏
  is_active: boolean
  is_testnet: boolean  // true=测试网/模拟盘, false=真实环境
  created_at: string
  updated_at: string
}

/** 交易所支持的交易对信息 */
export interface ExchangeSymbol {
  symbol: string
  base_currency: string
  quote_currency: string
  min_amount: number
  price_precision: number
  amount_precision: number
}

/** 交易所账户余额信息 */
export interface ExchangeBalance {
  currency: string
  free: number
  used: number
  total: number
}

/** 测试连接响应 */
export interface TestConnectionResponse {
  success: boolean
  message: string
  balance?: ExchangeBalance[]
}