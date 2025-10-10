import { ref, onUnmounted } from 'vue'
import { useUserStore } from '@/pinia/stores/user'

export interface WebSocketMessage {
  type: 'spread_update' | 'order_update' | 'position_update' | 'status_update' | 'connection_established' | 'pong'
  timestamp: string | number
  data: any
}

export function useWebSocket(botId: number, options: {
  onSpreadUpdate?: (data: any) => void
  onOrderUpdate?: (data: any) => void
  onPositionUpdate?: (data: any) => void
  onStatusUpdate?: (data: any) => void
  onConnectionEstablished?: (data: any) => void
  onError?: (error: Event) => void
  onClose?: (event: CloseEvent) => void
} = {}) {
  const socket = ref<WebSocket | null>(null)
  const isConnected = ref(false)
  const connectionError = ref<string | null>(null)
  const userStore = useUserStore()
  
  // 心跳定时器
  let heartbeatTimer: number | null = null
  
  // 重连计数器
  let reconnectCount = 0
  const maxReconnectAttempts = 5
  
  // 连接WebSocket
  const connect = () => {
    if (socket.value && socket.value.readyState === WebSocket.OPEN) {
      return
    }
    
    try {
      // 获取访问令牌
      const token = userStore.accessToken
      if (!token) {
        connectionError.value = '未找到访问令牌'
        return
      }
      
      // 构建WebSocket URL
      const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
      const wsHost = window.location.host
      const wsUrl = `${wsProtocol}//${wsHost}/api/v1/websocket/bot/${botId}?token=${token}`
      
      // 创建WebSocket连接
      socket.value = new WebSocket(wsUrl)
      
      // 连接打开
      socket.value.onopen = () => {
        console.log(`WebSocket连接已建立: 机器人 ${botId}`)
        isConnected.value = true
        connectionError.value = null
        reconnectCount = 0
        
        // 启动心跳
        startHeartbeat()
      }
      
      // 接收消息
      socket.value.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data)
          
          // 根据消息类型调用相应的回调
          switch (message.type) {
            case 'connection_established':
              options.onConnectionEstablished?.(message.data)
              break
            case 'spread_update':
              options.onSpreadUpdate?.(message.data)
              break
            case 'order_update':
              options.onOrderUpdate?.(message.data)
              break
            case 'position_update':
              options.onPositionUpdate?.(message.data)
              break
            case 'status_update':
              options.onStatusUpdate?.(message.data)
              break
            case 'pong':
              // 心跳响应，无需处理
              break
            default:
              console.warn('未知的WebSocket消息类型:', message.type)
          }
        } catch (error) {
          console.error('解析WebSocket消息失败:', error)
        }
      }
      
      // 连接错误
      socket.value.onerror = (error) => {
        console.error('WebSocket连接错误:', error)
        connectionError.value = 'WebSocket连接错误'
        options.onError?.(error)
      }
      
      // 连接关闭
      socket.value.onclose = (event) => {
        console.log(`WebSocket连接已关闭: 机器人 ${botId}, 代码: ${event.code}, 原因: ${event.reason}`)
        isConnected.value = false
        stopHeartbeat()
        options.onClose?.(event)
        
        // 尝试重连
        if (reconnectCount < maxReconnectAttempts && event.code !== 1000) {
          reconnectCount++
          console.log(`尝试重连 (${reconnectCount}/${maxReconnectAttempts})...`)
          setTimeout(connect, 2000 * reconnectCount) // 递增延迟重连
        }
      }
    } catch (error) {
      console.error('创建WebSocket连接失败:', error)
      connectionError.value = '创建WebSocket连接失败'
    }
  }
  
  // 断开连接
  const disconnect = () => {
    if (socket.value) {
      socket.value.close(1000, '用户主动断开')
      socket.value = null
    }
    isConnected.value = false
    stopHeartbeat()
  }
  
  // 发送消息
  const sendMessage = (message: any) => {
    if (socket.value && socket.value.readyState === WebSocket.OPEN) {
      socket.value.send(JSON.stringify(message))
    } else {
      console.warn('WebSocket未连接，无法发送消息')
    }
  }
  
  // 启动心跳
  const startHeartbeat = () => {
    stopHeartbeat()
    heartbeatTimer = window.setInterval(() => {
      sendMessage({ type: 'ping' })
    }, 30000) // 每30秒发送一次心跳
  }
  
  // 停止心跳
  const stopHeartbeat = () => {
    if (heartbeatTimer) {
      clearInterval(heartbeatTimer)
      heartbeatTimer = null
    }
  }
  
  // 组件卸载时断开连接
  onUnmounted(() => {
    disconnect()
  })
  
  return {
    isConnected,
    connectionError,
    connect,
    disconnect,
    sendMessage
  }
}