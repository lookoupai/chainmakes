/**
 * WebSocket composable测试
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { ref } from 'vue'
import { useWebSocket } from '@/common/composables/useWebSocket'

// Mock WebSocket
class MockWebSocket {
  static CONNECTING = 0
  static OPEN = 1
  static CLOSING = 2
  static CLOSED = 3

  readyState = MockWebSocket.CONNECTING
  url = ''
  
  onopen: ((event: Event) => void) | null = null
  onclose: ((event: CloseEvent) => void) | null = null
  onmessage: ((event: MessageEvent) => void) | null = null
  onerror: ((event: Event) => void) | null = null

  constructor(url: string) {
    this.url = url
    
    // Simulate connection
    setTimeout(() => {
      this.readyState = MockWebSocket.OPEN
      if (this.onopen) {
        this.onopen(new Event('open'))
      }
    }, 10)
  }

  send(data: string) {
    if (this.readyState !== MockWebSocket.OPEN) {
      throw new Error('WebSocket is not open')
    }
    
    // Simulate echo response
    setTimeout(() => {
      if (this.onmessage) {
        this.onmessage(new MessageEvent('message', { data }))
      }
    }, 5)
  }

  close() {
    this.readyState = MockWebSocket.CLOSED
    if (this.onclose) {
      this.onclose(new CloseEvent('close'))
    }
  }
}

// Mock global WebSocket
global.WebSocket = MockWebSocket as any

describe('useWebSocket', () => {
  let botId: number
  let options: any
  let reconnectInterval: number

  beforeEach(() => {
    botId = 1
    reconnectInterval = 100
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('initializes with correct default values', () => {
    const { isConnected, error } = useWebSocket(botId, {})
    
    expect(isConnected.value).toBe(false)
    expect(error.value).toBe(null)
  })

  it('connects to WebSocket', async () => {
    const { isConnected, connect, disconnect } = useWebSocket(botId, {})
    
    connect()
    
    // WebSocket should be in CONNECTING state
    expect(isConnected.value).toBe(false)
    
    // Advance time to trigger connection
    vi.advanceTimersByTime(10)
    
    // Should be connected now
    expect(isConnected.value).toBe(true)
    
    disconnect()
  })

  it('disconnects from WebSocket', async () => {
    const { isConnected, connect, disconnect } = useWebSocket(botId, {})
    
    connect()
    vi.advanceTimersByTime(10)
    
    expect(isConnected.value).toBe(true)
    
    disconnect()
    
    expect(isConnected.value).toBe(false)
  })

  it('reconnects on connection loss', async () => {
    const { isConnected, connect } = useWebSocket(botId, { reconnectInterval })
    
    connect()
    vi.advanceTimersByTime(10)
    
    expect(isConnected.value).toBe(true)
    
    // Simulate connection loss
    const mockWs = (global.WebSocket as any).mock.instances[0]
    mockWs.readyState = MockWebSocket.CLOSED
    if (mockWs.onclose) {
      mockWs.onclose(new CloseEvent('close'))
    }
    
    expect(isConnected.value).toBe(false)
    
    // Advance time to trigger reconnection
    vi.advanceTimersByTime(reconnectInterval)
    
    // Should be reconnected
    expect(isConnected.value).toBe(true)
  })

  it('handles spread update messages', async () => {
    const onSpreadUpdate = vi.fn()
    const { connect, disconnect } = useWebSocket(botId, { onSpreadUpdate })
    
    connect()
    vi.advanceTimersByTime(10)
    
    const mockWs = (global.WebSocket as any).mock.instances[0]
    const spreadData = {
      type: 'spread_update',
      data: {
        bot_id: botId,
        base_price: 50000,
        quote_price: 50100,
        spread: 100,
        spread_percentage: 0.002
      }
    }
    
    if (mockWs.onmessage) {
      mockWs.onmessage(new MessageEvent('message', { 
        data: JSON.stringify(spreadData) 
      }))
    }
    
    expect(onSpreadUpdate).toHaveBeenCalledWith(spreadData.data)
    
    disconnect()
  })

  it('handles order update messages', async () => {
    const onOrderUpdate = vi.fn()
    const { connect, disconnect } = useWebSocket(botId, { onOrderUpdate })
    
    connect()
    vi.advanceTimersByTime(10)
    
    const mockWs = (global.WebSocket as any).mock.instances[0]
    const orderData = {
      type: 'order_update',
      data: {
        id: 1,
        bot_id: botId,
        symbol: 'BTC/USDT',
        type: 'market',
        side: 'buy',
        amount: 0.001,
        price: 50000,
        status: 'filled'
      }
    }
    
    if (mockWs.onmessage) {
      mockWs.onmessage(new MessageEvent('message', { 
        data: JSON.stringify(orderData) 
      }))
    }
    
    expect(onOrderUpdate).toHaveBeenCalledWith(orderData.data)
    
    disconnect()
  })

  it('handles position update messages', async () => {
    const onPositionUpdate = vi.fn()
    const { connect, disconnect } = useWebSocket(botId, { onPositionUpdate })
    
    connect()
    vi.advanceTimersByTime(10)
    
    const mockWs = (global.WebSocket as any).mock.instances[0]
    const positionData = {
      type: 'position_update',
      data: {
        id: 1,
        bot_id: botId,
        symbol: 'BTC/USDT',
        side: 'long',
        size: 0.001,
        entry_price: 50000,
        mark_price: 50100,
        unrealized_pnl: 0.1
      }
    }
    
    if (mockWs.onmessage) {
      mockWs.onmessage(new MessageEvent('message', { 
        data: JSON.stringify(positionData) 
      }))
    }
    
    expect(onPositionUpdate).toHaveBeenCalledWith(positionData.data)
    
    disconnect()
  })

  it('handles status update messages', async () => {
    const onStatusUpdate = vi.fn()
    const { connect, disconnect } = useWebSocket(botId, { onStatusUpdate })
    
    connect()
    vi.advanceTimersByTime(10)
    
    const mockWs = (global.WebSocket as any).mock.instances[0]
    const statusData = {
      type: 'status_update',
      data: {
        bot_id: botId,
        status: 'running',
        last_update: new Date().toISOString()
      }
    }
    
    if (mockWs.onmessage) {
      mockWs.onmessage(new MessageEvent('message', { 
        data: JSON.stringify(statusData) 
      }))
    }
    
    expect(onStatusUpdate).toHaveBeenCalledWith(statusData.data)
    
    disconnect()
  })

  it('handles connection errors', async () => {
    const onError = vi.fn()
    const { connect, disconnect } = useWebSocket(botId, { onError })
    
    connect()
    
    const mockWs = (global.WebSocket as any).mock.instances[0]
    if (mockWs.onerror) {
      mockWs.onerror(new Event('error'))
    }
    
    expect(onError).toHaveBeenCalled()
    
    disconnect()
  })

  it('sends ping messages periodically', async () => {
    const { connect, disconnect } = useWebSocket(botId, { pingInterval: 50 })
    
    connect()
    vi.advanceTimersByTime(10)
    
    const mockWs = (global.WebSocket as any).mock.instances[0]
    const sendSpy = vi.spyOn(mockWs, 'send')
    
    // Advance time to trigger ping
    vi.advanceTimersByTime(50)
    
    expect(sendSpy).toHaveBeenCalledWith(JSON.stringify({ type: 'ping' }))
    
    disconnect()
  })

  it('limits reconnection attempts', async () => {
    const { connect, disconnect } = useWebSocket(botId, { 
      reconnectInterval, 
      maxReconnectAttempts: 2 
    })
    
    connect()
    vi.advanceTimersByTime(10)
    
    const mockWs = (global.WebSocket as any).mock.instances[0]
    
    // Simulate connection loss
    mockWs.readyState = MockWebSocket.CLOSED
    if (mockWs.onclose) {
      mockWs.onclose(new CloseEvent('close'))
    }
    
    // Try to reconnect max times
    for (let i = 0; i < 2; i++) {
      vi.advanceTimersByTime(reconnectInterval)
      
      // Simulate connection loss again
      const currentWs = (global.WebSocket as any).mock.instances[i + 1]
      if (currentWs) {
        currentWs.readyState = MockWebSocket.CLOSED
        if (currentWs.onclose) {
          currentWs.onclose(new CloseEvent('close'))
        }
      }
    }
    
    // Should not try to reconnect again
    vi.advanceTimersByTime(reconnectInterval * 2)
    
    expect((global.WebSocket as any).mock.instances.length).toBe(3) // Initial + 2 reconnects
    
    disconnect()
  })

  it('processes message queue after reconnection', async () => {
    const onSpreadUpdate = vi.fn()
    const { connect, disconnect } = useWebSocket(botId, { 
      onSpreadUpdate,
      reconnectInterval 
    })
    
    connect()
    vi.advanceTimersByTime(10)
    
    // Simulate connection loss
    const mockWs = (global.WebSocket as any).mock.instances[0]
    mockWs.readyState = MockWebSocket.CLOSED
    if (mockWs.onclose) {
      mockWs.onclose(new CloseEvent('close'))
    }
    
    // Send message while disconnected
    const spreadData = {
      type: 'spread_update',
      data: {
        bot_id: botId,
        base_price: 50000,
        quote_price: 50100,
        spread: 100,
        spread_percentage: 0.002
      }
    }
    
    // Reconnect
    vi.advanceTimersByTime(reconnectInterval)
    
    // Process queued message
    const reconnectedWs = (global.WebSocket as any).mock.instances[1]
    if (reconnectedWs.onmessage) {
      reconnectedWs.onmessage(new MessageEvent('message', { 
        data: JSON.stringify(spreadData) 
      }))
    }
    
    expect(onSpreadUpdate).toHaveBeenCalledWith(spreadData.data)
    
    disconnect()
  })
})