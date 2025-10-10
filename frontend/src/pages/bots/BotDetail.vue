<template>
  <div class="app-container">
    <el-page-header @back="handleBack" class="mb-4">
      <template #content>
        <span class="page-title">机器人详情</span>
      </template>
    </el-page-header>

    <div v-loading="loading">
      <!-- 基本信息卡片 -->
      <el-card class="mb-3">
        <template #header>
          <div class="card-header">
            <div class="title-with-status">
              <span class="title">{{ botInfo?.bot_name }}</span>
              <el-tag :type="getStatusType(botInfo?.status)" size="large" class="ml-3">
                {{ getStatusText(botInfo?.status) }}
              </el-tag>
            </div>
            <div class="actions">
              <el-button-group>
                <el-button
                  v-if="botInfo?.status === 'stopped' || botInfo?.status === 'paused'"
                  type="success"
                  @click="handleStart"
                >
                  启动
                </el-button>
                <el-button
                  v-if="botInfo?.status === 'running'"
                  type="warning"
                  @click="handlePause"
                >
                  暂停
                </el-button>
                <el-button
                  v-if="botInfo?.status === 'running' || botInfo?.status === 'paused'"
                  type="danger"
                  @click="handleStop"
                >
                  停止
                </el-button>
                <el-button @click="handleEdit">编辑配置</el-button>
              </el-button-group>
            </div>
          </div>
        </template>

        <el-descriptions :column="3" border>
          <el-descriptions-item label="实例ID">
            {{ botInfo?.id }}
          </el-descriptions-item>
          <el-descriptions-item label="当前循环">
            第 {{ botInfo?.current_cycle }} 轮
          </el-descriptions-item>
          <el-descriptions-item label="总交易次数">
            {{ botInfo?.total_trades }} 笔
          </el-descriptions-item>

          <el-descriptions-item label="市场1">
            {{ botInfo?.market1_symbol }}
          </el-descriptions-item>
          <el-descriptions-item label="市场2">
            {{ botInfo?.market2_symbol }}
          </el-descriptions-item>
          <el-descriptions-item label="杠杆">
            {{ botInfo?.leverage }}x
          </el-descriptions-item>

          <el-descriptions-item label="每单投资">
            ${{ botInfo?.investment_per_order }}
          </el-descriptions-item>
          <el-descriptions-item label="最大持仓">
            ${{ botInfo?.max_position_value }}
          </el-descriptions-item>
          <el-descriptions-item label="加仓次数">
            {{ botInfo?.max_dca_times }}次
          </el-descriptions-item>

          <el-descriptions-item label="止盈模式">
            {{ botInfo?.profit_mode === 'position' ? '仓位止盈' : '回归止盈' }}
          </el-descriptions-item>
          <el-descriptions-item label="止盈比例">
            {{ botInfo?.profit_ratio }}%
          </el-descriptions-item>
          <el-descriptions-item label="止损比例">
            {{ botInfo?.stop_loss_ratio }}%
          </el-descriptions-item>

          <el-descriptions-item label="总收益" :span="3">
            <span :class="['profit-value', botInfo && botInfo.total_profit >= 0 ? 'profit' : 'loss']">
              ${{ botInfo?.total_profit.toFixed(2) }}
            </span>
          </el-descriptions-item>

          <el-descriptions-item label="统计开始时间" :span="3">
            {{ formatDateTime(botInfo?.start_time) }}
          </el-descriptions-item>
        </el-descriptions>
      </el-card>

      <!-- 实时数据可视化 -->
      <el-row :gutter="16" class="mb-3">
        <!-- 价差历史曲线 -->
        <el-col :span="16">
          <el-card>
            <template #header>
              <div class="card-header">
                <span class="title">价差历史曲线</span>
                <el-button size="small" @click="handleRefreshChart">
                  <el-icon><Refresh /></el-icon>
                  刷新
                </el-button>
              </div>
            </template>
            <spread-chart
              :data="spreadHistory"
              :loading="chartLoading"
              height="400px"
            />
          </el-card>
        </el-col>

        <!-- 持仓分布 -->
        <el-col :span="8">
          <el-card>
            <position-analysis-chart
              :positions="positions"
              height="400px"
            />
          </el-card>
        </el-col>
      </el-row>

      <!-- 交易指标监控 -->
      <el-card class="mb-3">
        <trading-metrics-chart
          :data="tradingMetrics"
          height="350px"
        />
      </el-card>

      <!-- 当前持仓 -->
      <el-card class="mb-3">
        <template #header>
          <div class="card-header">
            <span class="title">当前持仓</span>
            <el-button
              v-if="positions.length > 0"
              type="danger"
              size="small"
              plain
              @click="handleClosePositions"
            >
              平仓所有持仓
            </el-button>
          </div>
        </template>

        <el-table :data="positions" border stripe>
          <el-table-column prop="symbol" label="交易对" width="150" />
          <el-table-column prop="side" label="方向" width="100">
            <template #default="{ row }">
              <el-tag :type="row.side === 'long' ? 'success' : 'danger'">
                {{ row.side === 'long' ? '做多' : '做空' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="amount" label="数量" width="120">
            <template #default="{ row }">
              {{ row.amount.toFixed(4) }}
            </template>
          </el-table-column>
          <el-table-column prop="entry_price" label="开仓均价" width="130">
            <template #default="{ row }">
              ${{ row.entry_price.toFixed(6) }}
            </template>
          </el-table-column>
          <el-table-column prop="current_price" label="当前价格" width="130">
            <template #default="{ row }">
              ${{ row.current_price.toFixed(6) }}
            </template>
          </el-table-column>
          <el-table-column prop="unrealized_pnl" label="未实现盈亏" width="150">
            <template #default="{ row }">
              <span :class="['profit-value', row.unrealized_pnl >= 0 ? 'profit' : 'loss']">
                ${{ row.unrealized_pnl.toFixed(2) }}
              </span>
            </template>
          </el-table-column>
          <el-table-column prop="cycle_number" label="循环轮次" width="100" />
          <el-table-column prop="created_at" label="开仓时间" width="180">
            <template #default="{ row }">
              {{ formatDateTime(row.created_at) }}
            </template>
          </el-table-column>
        </el-table>

        <el-empty v-if="positions.length === 0" description="当前无持仓" />
      </el-card>

      <!-- 订单历史 -->
      <el-card>
        <template #header>
          <span class="title">订单历史</span>
        </template>

        <el-table :data="orders" border stripe max-height="400">
          <el-table-column prop="exchange_order_id" label="订单ID" width="200" show-overflow-tooltip />
          <el-table-column prop="symbol" label="交易对" width="150" />
          <el-table-column prop="side" label="方向" width="100">
            <template #default="{ row }">
              <el-tag :type="row.side === 'buy' ? 'success' : 'danger'" size="small">
                {{ row.side === 'buy' ? '买入' : '卖出' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="order_type" label="类型" width="100" />
          <el-table-column prop="amount" label="数量" width="120">
            <template #default="{ row }">
              {{ row.amount.toFixed(4) }}
            </template>
          </el-table-column>
          <el-table-column prop="price" label="价格" width="130">
            <template #default="{ row }">
              {{ row.price ? `$${row.price.toFixed(6)}` : '-' }}
            </template>
          </el-table-column>
          <el-table-column prop="cost" label="成交额" width="130">
            <template #default="{ row }">
              {{ row.cost ? `$${row.cost.toFixed(2)}` : '-' }}
            </template>
          </el-table-column>
          <el-table-column prop="status" label="状态" width="100">
            <template #default="{ row }">
              <el-tag :type="getOrderStatusType(row.status)" size="small">
                {{ getOrderStatusText(row.status) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="dca_level" label="加仓次数" width="100" />
          <el-table-column prop="cycle_number" label="循环轮次" width="100" />
          <el-table-column prop="created_at" label="创建时间" width="180">
            <template #default="{ row }">
              {{ formatDateTime(row.created_at) }}
            </template>
          </el-table-column>
        </el-table>

        <!-- 订单分页 -->
        <el-pagination
          v-if="ordersTotal > 0"
          v-model:current-page="ordersPage"
          v-model:page-size="ordersPageSize"
          :total="ordersTotal"
          :page-sizes="[10, 20, 50]"
          layout="total, sizes, prev, pager, next"
          class="mt-4"
          @size-change="fetchOrders"
          @current-change="fetchOrders"
        />
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import SpreadChart from '@/common/components/SpreadChart.vue'
import TradingMetricsChart from '@/common/components/TradingMetricsChart.vue'
import PositionAnalysisChart from '@/common/components/PositionAnalysisChart.vue'
import { useWebSocket } from '@/common/composables/useWebSocket'
import type { BotResponse, Position, Order, SpreadHistory } from '@/common/apis/bots/type'
import {
  getBotDetail,
  getBotPositions,
  getBotOrders,
  getBotSpreadHistory,
  startBot,
  pauseBot,
  stopBot,
  closeBotPositions
} from '@/common/apis/bots'

const route = useRoute()
const router = useRouter()

const loading = ref(false)
const chartLoading = ref(false)
const botInfo = ref<BotResponse>()
const positions = ref<Position[]>([])
const orders = ref<Order[]>([])
const ordersTotal = ref(0)
const ordersPage = ref(1)
const ordersPageSize = ref(10)
const spreadHistory = ref<SpreadHistory[]>([])

// 交易指标数据
const tradingMetrics = ref<Array<{
  timestamp: string
  profitLoss: number
  totalTrades: number
  currentCycle: number
  dcaCount: number
}>>([])

// WebSocket连接
const { isConnected, connect: connectWebSocket, disconnect: disconnectWebSocket } = useWebSocket(
  Number(route.params.id),
  {
    onConnectionEstablished: (data) => {
      console.log('WebSocket连接已建立:', data)
    },
    onSpreadUpdate: (data) => {
      // 更新价差历史图表
      if (data && data.bot_instance_id === Number(route.params.id)) {
        spreadHistory.value.push({
          recorded_at: data.recorded_at,
          market1_price: data.market1_price,
          market2_price: data.market2_price,
          spread_percentage: data.spread_percentage
        })
        
        // 限制图表数据点数量
        if (spreadHistory.value.length > 1000) {
          spreadHistory.value = spreadHistory.value.slice(-1000)
        }
      }
    },
    onOrderUpdate: (data) => {
      // 更新订单列表
      if (data && data.bot_instance_id === Number(route.params.id)) {
        // 检查订单是否已存在
        const existingIndex = orders.value.findIndex(order => order.exchange_order_id === data.exchange_order_id)
        if (existingIndex >= 0) {
          // 更新现有订单
          orders.value[existingIndex] = { ...orders.value[existingIndex], ...data }
        } else {
          // 添加新订单到列表开头
          orders.value.unshift(data)
          // 限制订单数量
          if (orders.value.length > ordersPageSize.value) {
            orders.value = orders.value.slice(0, ordersPageSize.value)
          }
        }
      }
    },
    onPositionUpdate: (data) => {
      // 更新持仓列表
      if (data && data.bot_instance_id === Number(route.params.id)) {
        if (data.is_open) {
          // 更新或添加持仓
          const existingIndex = positions.value.findIndex(pos => pos.id === data.id)
          if (existingIndex >= 0) {
            positions.value[existingIndex] = { ...positions.value[existingIndex], ...data }
          } else {
            positions.value.push(data)
          }
        } else {
          // 移除已平仓的持仓
          positions.value = positions.value.filter(pos => pos.id !== data.id)
        }
      }
    },
    onStatusUpdate: (data) => {
      // 更新机器人状态
      if (data && data.bot_instance_id === Number(route.params.id) && botInfo.value) {
        botInfo.value.status = data.status
        botInfo.value.current_cycle = data.current_cycle
        botInfo.value.current_dca_count = data.current_dca_count
        botInfo.value.total_trades = data.total_trades

        // 更新交易指标数据
        tradingMetrics.value.push({
          timestamp: new Date().toISOString(),
          profitLoss: botInfo.value.total_profit,
          totalTrades: data.total_trades,
          currentCycle: data.current_cycle,
          dcaCount: data.current_dca_count
        })

        // 限制数据点数量
        if (tradingMetrics.value.length > 200) {
          tradingMetrics.value = tradingMetrics.value.slice(-200)
        }
      }
    },
    onError: (error) => {
      console.error('WebSocket连接错误:', error)
    },
    onClose: (event) => {
      console.log('WebSocket连接已关闭:', event)
    }
  }
)

// 状态显示
const getStatusType = (status?: string) => {
  const types: Record<string, any> = {
    running: 'success',
    paused: 'warning',
    stopped: 'info'
  }
  return types[status || ''] || 'info'
}

const getStatusText = (status?: string) => {
  const texts: Record<string, string> = {
    running: '运行中',
    paused: '已暂停',
    stopped: '已停止'
  }
  return texts[status || ''] || status
}

const getOrderStatusType = (status: string) => {
  const types: Record<string, any> = {
    pending: 'info',
    open: 'warning',
    closed: 'success',
    canceled: 'danger'
  }
  return types[status] || 'info'
}

const getOrderStatusText = (status: string) => {
  const texts: Record<string, string> = {
    pending: '待处理',
    open: '进行中',
    closed: '已完成',
    canceled: '已取消'
  }
  return texts[status] || status
}

const formatDateTime = (dateString?: string) => {
  if (!dateString) return '-'
  return new Date(dateString).toLocaleString('zh-CN')
}

// 获取机器人详情
const fetchBotDetail = async () => {
  const botId = Number(route.params.id)
  if (!botId) {
    ElMessage.error('机器人ID无效')
    router.push('/bots/list')
    return
  }

  loading.value = true
  try {
    botInfo.value = await getBotDetail(botId)
  } catch (error) {
    ElMessage.error('获取机器人详情失败')
    console.error(error)
  } finally {
    loading.value = false
  }
}

// 获取持仓
const fetchPositions = async () => {
  const botId = Number(route.params.id)
  try {
    positions.value = await getBotPositions(botId)
  } catch (error) {
    console.error('获取持仓失败:', error)
  }
}

// 获取订单历史
const fetchOrders = async () => {
  const botId = Number(route.params.id)
  try {
    const response = await getBotOrders(botId, {
      page: ordersPage.value,
      page_size: ordersPageSize.value
    })
    orders.value = response.items
    ordersTotal.value = response.total
  } catch (error) {
    console.error('获取订单失败:', error)
  }
}

// 获取价差历史
const fetchSpreadHistory = async () => {
  const botId = Number(route.params.id)
  chartLoading.value = true
  try {
    spreadHistory.value = await getBotSpreadHistory(botId, {
      limit: 1000
    })
  } catch (error) {
    console.error('获取价差历史失败:', error)
  } finally {
    chartLoading.value = false
  }
}

// 刷新所有数据
const refreshAllData = () => {
  fetchBotDetail()
  fetchPositions()
  fetchOrders()
  fetchSpreadHistory()
}

// 操作处理
const handleBack = () => {
  router.push('/bots/list')
}

const handleEdit = () => {
  router.push(`/bots/edit/${route.params.id}`)
}

const handleStart = async () => {
  try {
    await startBot(Number(route.params.id))
    ElMessage.success('机器人已启动')
    refreshAllData()
  } catch (error) {
    ElMessage.error('启动失败')
    console.error(error)
  }
}

const handlePause = async () => {
  try {
    await pauseBot(Number(route.params.id))
    ElMessage.success('机器人已暂停')
    refreshAllData()
  } catch (error) {
    ElMessage.error('暂停失败')
    console.error(error)
  }
}

const handleStop = async () => {
  try {
    await ElMessageBox.confirm(
      '停止后机器人将关闭所有持仓,确定要停止吗?',
      '确认停止',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    const botId = Number(route.params.id)

    // 先平仓所有持仓
    try {
      await closeBotPositions(botId)
      ElMessage.info('正在平仓所有持仓...')
      // 等待2秒让平仓完成
      await new Promise((resolve) => setTimeout(resolve, 2000))
    } catch (error) {
      console.error('平仓失败:', error)
      ElMessage.warning('平仓失败，但仍会停止机器人')
    }

    // 再停止机器人
    await stopBot(botId)
    ElMessage.success('机器人已停止')
    refreshAllData()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('停止失败')
      console.error(error)
    }
  }
}

const handleClosePositions = async () => {
  try {
    await ElMessageBox.confirm(
      '确定要平仓所有持仓吗?',
      '确认平仓',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    await closeBotPositions(Number(route.params.id))
    ElMessage.success('平仓指令已发送')
    setTimeout(() => {
      refreshAllData()
    }, 2000)
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('平仓失败')
      console.error(error)
    }
  }
}

const handleRefreshChart = () => {
  fetchSpreadHistory()
}

// 自动刷新
let refreshTimer: number | null = null

const startAutoRefresh = () => {
  // 每10秒刷新一次数据
  refreshTimer = window.setInterval(() => {
    if (botInfo.value?.status === 'running') {
      fetchPositions()
      fetchSpreadHistory()
    }
  }, 10000)
}

const stopAutoRefresh = () => {
  if (refreshTimer) {
    clearInterval(refreshTimer)
    refreshTimer = null
  }
}

// 监听机器人状态变化，决定是否建立WebSocket连接
watch(
  () => botInfo.value?.status,
  (newStatus) => {
    if (newStatus === 'running' && !isConnected.value) {
      // 机器人运行中且WebSocket未连接，则建立连接
      connectWebSocket()
    } else if (newStatus !== 'running' && isConnected.value) {
      // 机器人非运行状态且WebSocket已连接，则断开连接
      disconnectWebSocket()
    }
  },
  { immediate: true }
)

// 生命周期
onMounted(() => {
  refreshAllData()
  startAutoRefresh()
})

onUnmounted(() => {
  stopAutoRefresh()
  disconnectWebSocket()
})
</script>

<style scoped lang="scss">
.app-container {
  padding: 20px;
}

.page-title {
  font-size: 20px;
  font-weight: 600;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;

  .title-with-status {
    display: flex;
    align-items: center;
  }

  .title {
    font-size: 16px;
    font-weight: 600;
  }
}

.profit-value {
  font-weight: 600;
  font-size: 16px;

  &.profit {
    color: var(--el-color-success);
  }

  &.loss {
    color: var(--el-color-danger);
  }
}
</style>