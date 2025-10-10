/**
 * 测试设置文件
 */
import { vi } from 'vitest'
import { config } from '@vue/test-utils'

// Mock Element Plus
config.global.stubs = {
  'el-button': true,
  'el-input': true,
  'el-form': true,
  'el-form-item': true,
  'el-select': true,
  'el-option': true,
  'el-table': true,
  'el-table-column': true,
  'el-tag': true,
  'el-switch': true,
  'el-pagination': true,
  'el-dialog': true,
  'el-card': true,
  'el-row': true,
  'el-col': true,
  'el-divider': true,
  'el-tooltip': true,
  'el-popover': true,
  'el-dropdown': true,
  'el-dropdown-menu': true,
  'el-dropdown-item': true,
  'el-menu': true,
  'el-menu-item': true,
  'el-submenu': true,
  'el-breadcrumb': true,
  'el-breadcrumb-item': true,
  'el-page-header': true,
  'el-result': true,
  'el-empty': true,
  'el-alert': true,
  'el-message-box': true,
  'el-notification': true,
  'el-loading': true,
  'el-icon': true,
  'el-avatar': true,
  'el-image': true,
  'el-backtop': true,
  'el-scrollbar': true,
  'el-calendar': true,
  'el-carousel': true,
  'el-carousel-item': true,
  'el-collapse': true,
  'el-collapse-item': true,
  'el-cascader': true,
  'el-cascader-panel': true,
  'el-color-picker': true,
  'el-transfer': true,
  'el-container': true,
  'el-header': true,
  'el-aside': true,
  'el-main': true,
  'el-footer': true,
  'el-timeline': true,
  'el-timeline-item': true,
  'el-link': true,
  'el-divider': true,
  'el-radio': true,
  'el-radio-group': true,
  'el-radio-button': true,
  'el-checkbox': true,
  'el-checkbox-group': true,
  'el-checkbox-button': true,
  'el-upload': true,
  'el-rate': true,
  'el-steps': true,
  'el-step': true,
  'el-progress': true,
  'el-tree': true,
  'el-tree-node': true,
  'el-alert': true,
  'el-switch': true,
  'el-slider': true,
  'el-time-picker': true,
  'el-time-select': true,
  'el-date-picker': true,
  'el-datetime-picker': true,
  'el-popconfirm': true,
  'el-tabs': true,
  'el-tab-pane': true,
  'el-anchor': true,
  'el-anchor-link': true,
  'el-backtop': true,
  'el-statistic': true,
  'el-tour': true,
  'el-watermark': true,
  'el-segmented': true,
  'el-space': true,
  'el-skeleton': true,
  'el-skeleton-item': true,
  'el-descriptions': true,
  'el-descriptions-item': true,
  'el-result': true,
  'el-statistic': true,
  'el-image-viewer': true,
  'el-config-provider': true,
  'el-icon': true,
  'el-affix': true,
  'el-anchor': true,
  'el-anchor-link': true,
  'el-breadcrumb': true,
  'el-breadcrumb-item': true,
  'el-page-header': true,
  'el-result': true,
  'el-empty': true,
  'el-alert': true,
  'el-message-box': true,
  'el-notification': true,
  'el-loading': true
}

// Mock Vue Router
vi.mock('vue-router', () => ({
  useRouter: () => ({
    push: vi.fn(),
    replace: vi.fn(),
    go: vi.fn(),
    back: vi.fn(),
    forward: vi.fn()
  }),
  useRoute: () => ({
    params: {},
    query: {},
    path: '/',
    name: 'home',
    meta: {}
  })
}))

// Mock Pinia
vi.mock('pinia', () => ({
  createPinia: vi.fn(),
  defineStore: vi.fn(),
  storeToRefs: vi.fn()
}))

// Mock Element Plus Message
vi.mock('element-plus', () => ({
  ElMessage: {
    success: vi.fn(),
    error: vi.fn(),
    warning: vi.fn(),
    info: vi.fn()
  },
  ElMessageBox: {
    confirm: vi.fn(() => Promise.resolve()),
    alert: vi.fn(() => Promise.resolve()),
    prompt: vi.fn(() => Promise.resolve({ value: 'test' }))
  },
  ElNotification: {
    success: vi.fn(),
    error: vi.fn(),
    warning: vi.fn(),
    info: vi.fn()
  },
  ElLoading: {
    service: vi.fn(() => ({
      close: vi.fn()
    }))
  }
}))

// Mock Axios
vi.mock('@/http/axios', () => ({
  default: {
    get: vi.fn(() => Promise.resolve({ data: {} })),
    post: vi.fn(() => Promise.resolve({ data: {} })),
    put: vi.fn(() => Promise.resolve({ data: {} })),
    delete: vi.fn(() => Promise.resolve({ data: {} })),
    interceptors: {
      request: { use: vi.fn() },
      response: { use: vi.fn() }
    }
  }
}))

// Mock Window APIs
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(), // deprecated
    removeListener: vi.fn(), // deprecated
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
})

// Mock ResizeObserver
global.ResizeObserver = vi.fn().mockImplementation(() => ({
  observe: vi.fn(),
  unobserve: vi.fn(),
  disconnect: vi.fn(),
}))

// Mock IntersectionObserver
global.IntersectionObserver = vi.fn().mockImplementation(() => ({
  observe: vi.fn(),
  unobserve: vi.fn(),
  disconnect: vi.fn(),
}))

// Mock localStorage
const localStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
}
vi.stubGlobal('localStorage', localStorageMock)

// Mock sessionStorage
const sessionStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
}
vi.stubGlobal('sessionStorage', sessionStorageMock)

// Mock console methods for cleaner test output
global.console = {
  ...console,
  warn: vi.fn(),
  error: vi.fn(),
  log: vi.fn(),
  info: vi.fn(),
  debug: vi.fn(),
}