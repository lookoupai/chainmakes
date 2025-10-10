<template>
  <div class="global-error-handler">
    <!-- 错误通知 -->
    <el-notification
      v-for="notification in notifications"
      :key="notification.id"
      :title="notification.title"
      :message="notification.message"
      :type="notification.type"
      :duration="notification.duration"
      :show-close="notification.showClose"
      @close="removeNotification(notification.id)"
      class="error-notification"
    />
    
    <!-- 网络状态指示器 -->
    <div v-if="!isOnline" class="network-status offline">
      <el-icon class="status-icon"><Connection /></el-icon>
      <span>网络连接已断开</span>
    </div>
    
    <!-- WebSocket连接状态指示器 -->
    <div v-if="wsConnectionStatus !== 'connected'" class="ws-status">
      <el-icon class="status-icon" :class="wsConnectionStatus">
        <Connection />
      </el-icon>
      <span>{{ wsStatusText }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { ElNotification } from 'element-plus'
import { Connection } from '@element-plus/icons-vue'
import { useErrorHandler, AppError, ErrorType } from '@/common/utils/error-handler'
import { useWebSocketStore } from '@/pinia/stores/websocket'

const { addErrorListener, removeErrorListener } = useErrorHandler()
const wsStore = useWebSocketStore()

// 通知列表
const notifications = ref<Array<{
  id: string
  title: string
  message: string
  type: 'success' | 'warning' | 'info' | 'error'
  duration: number
  showClose: boolean
}>>([])

// 网络状态
const isOnline = ref(navigator.onLine)

// WebSocket连接状态
const wsConnectionStatus = computed(() => wsStore.connectionStatus)

// WebSocket状态文本
const wsStatusText = computed(() => {
  switch (wsConnectionStatus.value) {
    case 'connecting':
      return '正在连接实时数据...'
    case 'connected':
      return '实时数据已连接'
    case 'disconnected':
      return '实时数据连接已断开'
    case 'error':
      return '实时数据连接错误'
    default:
      return '未知状态'
  }
})

// 错误处理函数
const handleError = (error: AppError) => {
  // 根据错误类型显示不同的通知
  let type: 'success' | 'warning' | 'info' | 'error' = 'error'
  let title = '错误'
  let duration = 5000
  let showClose = true

  switch (error.type) {
    case ErrorType.VALIDATION:
      title = '验证错误'
      type = 'warning'
      duration = 4000
      break
    case ErrorType.AUTHENTICATION:
      title = '认证失败'
      type = 'warning'
      duration = 3000
      break
    case ErrorType.AUTHORIZATION:
      title = '权限不足'
      type = 'warning'
      duration = 4000
      break
    case ErrorType.NOT_FOUND:
      title = '资源不存在'
      type = 'info'
      duration = 3000
      break
    case ErrorType.BUSINESS_LOGIC:
      title = '操作失败'
      type = 'warning'
      duration = 4000
      break
    case ErrorType.EXCHANGE_API:
      title = '交易所接口异常'
      type = 'error'
      duration = 6000
      break
    case ErrorType.WEBSOCKET:
      title = '实时连接异常'
      type = 'warning'
      duration = 4000
      break
    case ErrorType.NETWORK:
      title = '网络错误'
      type = 'error'
      duration = 5000
      break
    default:
      title = '未知错误'
      type = 'error'
      duration = 5000
  }

  // 添加通知
  addNotification({
    id: `error-${Date.now()}-${Math.random()}`,
    title,
    message: error.getUserFriendlyMessage(),
    type,
    duration,
    showClose
  })

  // 对于严重错误，显示更详细的控制台日志
  if (error.type === ErrorType.NETWORK || error.type === ErrorType.EXCHANGE_API) {
    console.error('严重错误:', error)
  }
}

// 添加通知
const addNotification = (notification: {
  id: string
  title: string
  message: string
  type: 'success' | 'warning' | 'info' | 'error'
  duration: number
  showClose: boolean
}) => {
  notifications.value.push(notification)
  
  // 自动移除通知
  if (notification.duration > 0) {
    setTimeout(() => {
      removeNotification(notification.id)
    }, notification.duration)
  }
}

// 移除通知
const removeNotification = (id: string) => {
  const index = notifications.value.findIndex(n => n.id === id)
  if (index !== -1) {
    notifications.value.splice(index, 1)
  }
}

// 网络状态变化处理
const handleOnline = () => {
  isOnline.value = true
  addNotification({
    id: `network-online-${Date.now()}`,
    title: '网络已连接',
    message: '网络连接已恢复',
    type: 'success',
    duration: 3000,
    showClose: true
  })
}

const handleOffline = () => {
  isOnline.value = false
  addNotification({
    id: `network-offline-${Date.now()}`,
    title: '网络断开',
    message: '网络连接已断开，请检查网络设置',
    type: 'error',
    duration: 0, // 不自动关闭
    showClose: true
  })
}

// 生命周期钩子
onMounted(() => {
  // 添加错误监听器
  addErrorListener(handleError)
  
  // 添加网络状态监听器
  window.addEventListener('online', handleOnline)
  window.addEventListener('offline', handleOffline)
})

onUnmounted(() => {
  // 移除错误监听器
  removeErrorListener(handleError)
  
  // 移除网络状态监听器
  window.removeEventListener('online', handleOnline)
  window.removeEventListener('offline', handleOffline)
})
</script>

<style scoped>
.global-error-handler {
  position: fixed;
  top: 0;
  right: 0;
  z-index: 9999;
  pointer-events: none;
}

.error-notification {
  pointer-events: auto;
}

.network-status {
  position: fixed;
  top: 20px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 9999;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background: var(--el-color-danger);
  color: white;
  border-radius: 4px;
  font-size: 14px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  animation: slideDown 0.3s ease-out;
}

.network-status.online {
  background: var(--el-color-success);
}

.ws-status {
  position: fixed;
  bottom: 20px;
  right: 20px;
  z-index: 9999;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 12px;
  background: var(--el-color-warning);
  color: white;
  border-radius: 4px;
  font-size: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  animation: slideUp 0.3s ease-out;
}

.ws-status.connected {
  background: var(--el-color-success);
}

.ws-status.error {
  background: var(--el-color-danger);
}

.status-icon {
  font-size: 16px;
}

.status-icon.connecting {
  animation: pulse 1.5s infinite;
}

@keyframes slideDown {
  from {
    transform: translateX(-50%) translateY(-100%);
    opacity: 0;
  }
  to {
    transform: translateX(-50%) translateY(0);
    opacity: 1;
  }
}

@keyframes slideUp {
  from {
    transform: translateY(100%);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
}

@keyframes pulse {
  0% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
  100% {
    opacity: 1;
  }
}
</style>