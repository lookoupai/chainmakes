/** 机器人管理API */

import type {
  BotCreateRequest,
  BotUpdateRequest,
  BotResponse,
  BotListQuery,
  PaginatedResponse,
  Position,
  Order,
  SpreadHistory
} from './type'
import { request } from '@/http/axios'

/** 统一解包响应, 兼容被拦截器包裹为 {code,data,message} 的情况 */
const unwrap = <T,>(res: any): T => {
  if (res && typeof res === 'object' && 'code' in res && 'data' in res) {
    return res.data as T
  }
  return res as T
}

/** 获取机器人列表 */
export async function getBotList(params?: BotListQuery) {
  const res = await request<PaginatedResponse<BotResponse> | { code: number; data: PaginatedResponse<BotResponse> }>({
    url: '/bots/',
    method: 'get',
    params
  })
  return unwrap<PaginatedResponse<BotResponse>>(res)
}

/** 获取机器人详情 */
export async function getBotDetail(botId: number) {
  const res = await request<BotResponse | { code: number; data: BotResponse }>({
    url: `/bots/${botId}`,
    method: 'get'
  })
  return unwrap<BotResponse>(res)
}

/** 创建机器人 */
export async function createBot(data: BotCreateRequest) {
  const res = await request<BotResponse | { code: number; data: BotResponse }>({
    url: '/bots/',
    method: 'post',
    data
  })
  return unwrap<BotResponse>(res)
}

/** 更新机器人配置 */
export async function updateBot(botId: number, data: BotUpdateRequest) {
  const res = await request<BotResponse | { code: number; data: BotResponse }>({
    url: `/bots/${botId}`,
    method: 'put',
    data
  })
  return unwrap<BotResponse>(res)
}

/** 删除机器人 */
export async function deleteBot(botId: number) {
  const res = await request<any | { code: number; data: any }>({
    url: `/bots/${botId}`,
    method: 'delete'
  })
  return unwrap<any>(res)
}

/** 启动机器人 */
export async function startBot(botId: number) {
  const res = await request<BotResponse | { code: number; data: BotResponse }>({
    url: `/bots/${botId}/start`,
    method: 'post'
  })
  return unwrap<BotResponse>(res)
}

/** 暂停机器人 */
export async function pauseBot(botId: number) {
  const res = await request<BotResponse | { code: number; data: BotResponse }>({
    url: `/bots/${botId}/pause`,
    method: 'post'
  })
  return unwrap<BotResponse>(res)
}

/** 停止机器人 */
export async function stopBot(botId: number) {
  const res = await request<BotResponse | { code: number; data: BotResponse }>({
    url: `/bots/${botId}/stop`,
    method: 'post'
  })
  return unwrap<BotResponse>(res)
}

/** 获取机器人的订单历史 */
export async function getBotOrders(botId: number, params?: { page?: number; page_size?: number }) {
  const res = await request<PaginatedResponse<Order> | { code: number; data: PaginatedResponse<Order> }>({
    url: `/bots/${botId}/orders`,
    method: 'get',
    params
  })
  return unwrap<PaginatedResponse<Order>>(res)
}

/** 获取机器人的当前持仓 */
export async function getBotPositions(botId: number) {
  const res = await request<Position[] | { code: number; data: Position[] }>({
    url: `/bots/${botId}/positions`,
    method: 'get'
  })
  return unwrap<Position[]>(res)
}

/** 获取机器人的价差历史数据 */
export async function getBotSpreadHistory(
  botId: number,
  params?: {
    start_time?: string
    end_time?: string
    limit?: number
  }
) {
  const res = await request<SpreadHistory[] | { code: number; data: SpreadHistory[] }>({
    url: `/bots/${botId}/spread-history`,
    method: 'get',
    params
  })
  return unwrap<SpreadHistory[]>(res)
}

/** 手动平仓 */
export async function closeBotPositions(botId: number) {
  const res = await request<any | { code: number; data: any }>({
    url: `/bots/${botId}/close-positions`,
    method: 'post'
  })
  return unwrap<any>(res)
}