/**
 * 机器人列表组件测试
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { ElMessage } from 'element-plus'
import BotList from '@/pages/bots/BotList.vue'

// Mock API
vi.mock('@/common/apis/bots', () => ({
  getBots: vi.fn(() => Promise.resolve({
    data: [
      {
        id: 1,
        name: 'Test Bot 1',
        symbol: 'BTC/USDT',
        strategy_type: 'spread',
        is_active: true,
        created_at: '2023-01-01T00:00:00Z'
      },
      {
        id: 2,
        name: 'Test Bot 2',
        symbol: 'ETH/USDT',
        strategy_type: 'spread',
        is_active: false,
        created_at: '2023-01-02T00:00:00Z'
      }
    ]
  })),
  deleteBot: vi.fn(() => Promise.resolve({}))
}))

// Mock Element Plus
vi.mock('element-plus', () => ({
  ElMessage: {
    success: vi.fn(),
    error: vi.fn()
  },
  ElMessageBox: {
    confirm: vi.fn(() => Promise.resolve())
  }
}))

// Mock Vue Router
vi.mock('vue-router', () => ({
  useRouter: () => ({
    push: vi.fn()
  })
}))

describe('BotList', () => {
  let wrapper: any

  beforeEach(() => {
    wrapper = mount(BotList, {
      global: {
        stubs: {
          'el-table': true,
          'el-table-column': true,
          'el-button': true,
          'el-tag': true,
          'el-switch': true,
          'el-pagination': true,
          'el-dialog': true,
          'el-form': true,
          'el-form-item': true,
          'el-input': true,
          'el-select': true,
          'el-option': true
        }
      }
    })
  })

  it('renders correctly', () => {
    expect(wrapper.exists()).toBe(true)
    expect(wrapper.find('.bot-list').exists()).toBe(true)
  })

  it('loads bots on mount', async () => {
    await wrapper.vm.$nextTick()
    expect(wrapper.vm.bots.length).toBe(2)
    expect(wrapper.vm.bots[0].name).toBe('Test Bot 1')
    expect(wrapper.vm.bots[1].name).toBe('Test Bot 2')
  })

  it('filters bots by search query', async () => {
    await wrapper.vm.$nextTick()
    wrapper.vm.searchQuery = 'Test Bot 1'
    await wrapper.vm.$nextTick()
    
    const filteredBots = wrapper.vm.filteredBots
    expect(filteredBots.length).toBe(1)
    expect(filteredBots[0].name).toBe('Test Bot 1')
  })

  it('shows create bot dialog', async () => {
    wrapper.vm.showCreateDialog = true
    await wrapper.vm.$nextTick()
    
    expect(wrapper.find('.create-dialog').exists()).toBe(true)
  })

  it('deletes a bot', async () => {
    await wrapper.vm.$nextTick()
    await wrapper.vm.deleteBot(1)
    
    expect(ElMessage.success).toHaveBeenCalledWith('机器人删除成功')
  })

  it('toggles bot status', async () => {
    await wrapper.vm.$nextTick()
    const bot = wrapper.vm.bots[0]
    const originalStatus = bot.is_active
    
    await wrapper.vm.toggleBotStatus(bot)
    
    expect(bot.is_active).toBe(!originalStatus)
  })

  it('navigates to bot detail page', async () => {
    const mockRouter = {
      push: vi.fn()
    }
    wrapper.vm.$router = mockRouter
    
    await wrapper.vm.viewBot(1)
    
    expect(mockRouter.push).toHaveBeenCalledWith('/bots/1')
  })

  it('navigates to edit bot page', async () => {
    const mockRouter = {
      push: vi.fn()
    }
    wrapper.vm.$router = mockRouter
    
    await wrapper.vm.editBot(1)
    
    expect(mockRouter.push).toHaveBeenCalledWith('/bots/1/edit')
  })

  it('handles error when loading bots', async () => {
    // Mock API error
    const { getBots } = await import('@/common/apis/bots')
    ;(getBots as any).mockRejectedValueOnce(new Error('API Error'))
    
    await wrapper.vm.loadBots()
    
    expect(ElMessage.error).toHaveBeenCalledWith('加载机器人列表失败')
  })

  it('handles error when deleting bot', async () => {
    // Mock API error
    const { deleteBot } = await import('@/common/apis/bots')
    ;(deleteBot as any).mockRejectedValueOnce(new Error('API Error'))
    
    await wrapper.vm.deleteBot(1)
    
    expect(ElMessage.error).toHaveBeenCalledWith('删除机器人失败')
  })

  it('formats date correctly', () => {
    const date = '2023-01-01T00:00:00Z'
    const formattedDate = wrapper.vm.formatDate(date)
    
    expect(formattedDate).toMatch(/\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}/)
  })

  it('gets strategy type label', () => {
    expect(wrapper.vm.getStrategyTypeLabel('spread')).toBe('价差套利')
    expect(wrapper.vm.getStrategyTypeLabel('dca')).toBe('定投策略')
    expect(wrapper.vm.getStrategyTypeLabel('unknown')).toBe('未知策略')
  })
})