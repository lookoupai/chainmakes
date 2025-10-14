/** 机器人API相关类型定义 */

/** DCA配置项 */
export interface DCAConfig {
  times: number        // 第几次加仓
  spread: number       // 价差百分比
  multiplier: number   // 倍投倍数
}

/** 机器人创建请求 */
export interface BotCreateRequest {
  bot_name: string
  exchange_account_id: number
  market1_symbol: string
  market2_symbol: string
  start_time: string                    // ISO 8601格式UTC时间
  leverage: number
  order_type_open: 'market' | 'limit'
  order_type_close: 'market' | 'limit'
  investment_per_order: number
  max_position_value: number
  max_dca_times: number
  dca_config: DCAConfig[]
  profit_mode: 'regression' | 'position'
  profit_ratio: number
  stop_loss_ratio: number
  reverse_opening: boolean
  pause_after_close: boolean
}

/** 机器人更新请求 */
export interface BotUpdateRequest extends Partial<BotCreateRequest> {}

/** 机器人响应数据 */
export interface BotResponse {
  id: number
  user_id: number
  exchange_account_id: number
  bot_name: string
  market1_symbol: string
  market2_symbol: string
  start_time: string
  leverage: number
  order_type_open: string
  order_type_close: string
  investment_per_order: number
  max_position_value: number
  max_dca_times: number
  dca_config: DCAConfig[]
  profit_mode: string
  profit_ratio: number
  stop_loss_ratio: number
  reverse_opening: boolean
  status: 'running' | 'paused' | 'stopped'
  pause_after_close: boolean
  current_cycle: number
  total_profit: number
  total_trades: number
  created_at: string
  updated_at: string
}

/** 持仓信息 */
export interface Position {
  id: number
  bot_instance_id: number
  cycle_number: number
  symbol: string
  side: 'long' | 'short'
  amount: number
  entry_price: number
  current_price: number
  unrealized_pnl: number
  is_open: boolean
  created_at: string
  updated_at: string
  closed_at: string | null
}

/** 订单信息 */
export interface Order {
  id: number
  bot_instance_id: number
  cycle_number: number
  exchange_order_id: string | null
  symbol: string
  side: 'buy' | 'sell'
  order_type: string
  price: number | null
  amount: number
  filled_amount: number
  cost: number | null
  status: 'pending' | 'open' | 'closed' | 'canceled'
  dca_level: number
  created_at: string
  updated_at: string
  filled_at: string | null
}

/** 价差历史数据 */
export interface SpreadHistory {
  id: number
  bot_instance_id: number
  market1_price: number
  market2_price: number
  spread_percentage: number
  recorded_at: string
}

/** 机器人列表查询参数 */
export interface BotListQuery {
  page?: number
  page_size?: number
  status?: 'running' | 'paused' | 'stopped'
}

/** 分页响应 */
export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
  total_pages: number
}