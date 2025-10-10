/**
 * WebSocket状态管理
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export type ConnectionStatus = 'disconnected' | 'connecting' | 'connected' | 'error'

export const useWebSocketStore = defineStore('websocket', () => {
  // 连接状态
  const connectionStatus = ref<ConnectionStatus>('disconnected')
  
  // 连接错误
  const connectionError = ref<string | null>(null)
  
  // 最后连接时间
  const lastConnectedAt = ref<Date | null>(null)
  
  // 重连次数
  const reconnectAttempts = ref(0)
  
  // 最大重连次数
  const maxReconnectAttempts = ref(5)
  
  // 连接的机器人ID列表
  const connectedBots = ref<Set<number>>(new Set())
  
  // 计算属性
  const isConnected = computed(() => connectionStatus.value === 'connected')
  const isConnecting = computed(() => connectionStatus.value === 'connecting')
  const hasError = computed(() => connectionStatus.value === 'error')
  const canReconnect = computed(() => 
    connectionStatus.value === 'disconnected' || 
    (connectionStatus.value === 'error' && reconnectAttempts.value < maxReconnectAttempts.value)
  )
  
  // 设置连接状态
  const setConnectionStatus = (status: ConnectionStatus, error?: string) => {
    connectionStatus.value = status
    connectionError.value = error || null
    
    if (status === 'connected') {
      lastConnectedAt.value = new Date()
      reconnectAttempts.value = 0
    } else if (status === 'error') {
      reconnectAttempts.value++
    }
  }
  
  // 添加连接的机器人
  const addConnectedBot = (botId: number) => {
    connectedBots.value.add(botId)
  }
  
  // 移除连接的机器人
  const removeConnectedBot = (botId: number) => {
    connectedBots.value.delete(botId)
    
    // 如果没有连接的机器人，设置状态为断开连接
    if (connectedBots.value.size === 0) {
      setConnectionStatus('disconnected')
    }
  }
  
  // 清空所有连接的机器人
  const clearConnectedBots = () => {
    connectedBots.value.clear()
    setConnectionStatus('disconnected')
  }
  
  // 重置重连次数
  const resetReconnectAttempts = () => {
    reconnectAttempts.value = 0
  }
  
  // 设置最大重连次数
  const setMaxReconnectAttempts = (max: number) => {
    maxReconnectAttempts.value = max
  }
  
  // 获取连接状态文本
  const getStatusText = () => {
    switch (connectionStatus.value) {
      case 'disconnected':
        return '已断开连接'
      case 'connecting':
        return '正在连接...'
      case 'connected':
        return '已连接'
      case 'error':
        return `连接错误 (${reconnectAttempts.value}/${maxReconnectAttempts.value})`
      default:
        return '未知状态'
    }
  }
  
  // 获取状态颜色
  const getStatusColor = () => {
    switch (connectionStatus.value) {
      case 'disconnected':
        return '#909399'
      case 'connecting':
        return '#E6A23C'
      case 'connected':
        return '#67C23A'
      case 'error':
        return '#F56C6C'
      default:
        return '#909399'
    }
  }
  
  return {
    // 状态
    connectionStatus,
    connectionError,
    lastConnectedAt,
    reconnectAttempts,
    maxReconnectAttempts,
    connectedBots,
    
    // 计算属性
    isConnected,
    isConnecting,
    hasError,
    canReconnect,
    
    // 方法
    setConnectionStatus,
    addConnectedBot,
    removeConnectedBot,
    clearConnectedBots,
    resetReconnectAttempts,
    setMaxReconnectAttempts,
    getStatusText,
    getStatusColor
  }
})