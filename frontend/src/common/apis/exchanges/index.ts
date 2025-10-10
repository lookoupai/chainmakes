/** 交易所账户管理API */

import type {
  ExchangeAccountCreateRequest,
  ExchangeAccountUpdateRequest,
  ExchangeAccountResponse,
  ExchangeSymbol,
  TestConnectionResponse
} from './type'
import { request } from '@/http/axios'

/** 统一解包响应, 兼容被拦截器包裹为 {code,data,message} 的情况 */
const unwrap = <T,>(res: any): T => {
  if (res && typeof res === 'object' && 'code' in res && 'data' in res) {
    return res.data as T
  }
  return res as T
}

/** 获取交易所账户列表 */
export async function getExchangeAccounts() {
  const res = await request<ExchangeAccountResponse[] | { code: number; data: ExchangeAccountResponse[] }>({
    url: '/exchanges/',
    method: 'get'
  })
  return unwrap<ExchangeAccountResponse[]>(res)
}

/** 获取交易所账户详情 */
export async function getExchangeAccountDetail(accountId: number) {
  const res = await request<ExchangeAccountResponse | { code: number; data: ExchangeAccountResponse }>({
    url: `/exchanges/${accountId}`,
    method: 'get'
  })
  return unwrap<ExchangeAccountResponse>(res)
}

/** 添加交易所账户 */
export async function createExchangeAccount(data: ExchangeAccountCreateRequest) {
  const res = await request<ExchangeAccountResponse | { code: number; data: ExchangeAccountResponse }>({
    url: '/exchanges/',
    method: 'post',
    data
  })
  return unwrap<ExchangeAccountResponse>(res)
}

/** 更新交易所账户 */
export async function updateExchangeAccount(accountId: number, data: ExchangeAccountUpdateRequest) {
  const res = await request<ExchangeAccountResponse | { code: number; data: ExchangeAccountResponse }>({
    url: `/exchanges/${accountId}`,
    method: 'put',
    data
  })
  return unwrap<ExchangeAccountResponse>(res)
}

/** 删除交易所账户 */
export async function deleteExchangeAccount(accountId: number) {
  const res = await request<any | { code: number; data: any }>({
    url: `/exchanges/${accountId}`,
    method: 'delete'
  })
  return unwrap<any>(res)
}

/** 测试交易所API连接 */
export async function testExchangeConnection(accountId: number) {
  const res = await request<TestConnectionResponse | { code: number; data: TestConnectionResponse }>({
    url: `/exchanges/${accountId}/test`,
    method: 'post'
  })
  return unwrap<TestConnectionResponse>(res)
}

/** 获取交易所支持的交易对列表 */
export async function getExchangeSymbols(exchangeName: string) {
  const res = await request<ExchangeSymbol[] | { code: number; data: ExchangeSymbol[] }>({
    url: `/exchanges/${exchangeName}/symbols`,
    method: 'get'
  })
  return unwrap<ExchangeSymbol[]>(res)
}

/** 启用/禁用交易所账户 */
export async function toggleExchangeAccount(accountId: number, isActive: boolean) {
  const res = await request<ExchangeAccountResponse | { code: number; data: ExchangeAccountResponse }>({
    url: `/exchanges/${accountId}`,
    method: 'patch',
    data: { is_active: isActive }
  })
  return unwrap<ExchangeAccountResponse>(res)
}