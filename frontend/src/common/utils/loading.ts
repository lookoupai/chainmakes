/**
 * 加载状态管理工具
 */
import { ref, computed, reactive } from 'vue'

// 全局加载状态
const globalLoading = ref(false)
const loadingText = ref('加载中...')

// 局部加载状态映射
const loadingStates = reactive<Record<string, boolean>>({})

// 加载队列
const loadingQueue = ref<Set<string>>(new Set())

/**
 * 全局加载状态管理
 */
export function useGlobalLoading() {
  const setLoading = (loading: boolean, text = '加载中...') => {
    globalLoading.value = loading
    loadingText.value = text
  }

  const showLoading = (text = '加载中...') => {
    setLoading(true, text)
  }

  const hideLoading = () => {
    setLoading(false)
  }

  return {
    isLoading: computed(() => globalLoading.value),
    loadingText: computed(() => loadingText.value),
    setLoading,
    showLoading,
    hideLoading
  }
}

/**
 * 局部加载状态管理
 */
export function useLoading(key: string) {
  const setLoading = (loading: boolean) => {
    loadingStates[key] = loading
  }

  const isLoading = computed(() => loadingStates[key] || false)

  return {
    isLoading,
    setLoading
  }
}

/**
 * 异步操作包装器，自动管理加载状态
 */
export async function withLoading<T>(
  key: string,
  asyncFn: () => Promise<T>,
  loadingText = '加载中...'
): Promise<T> {
  // 设置加载状态
  loadingStates[key] = true
  loadingQueue.value.add(key)
  
  // 如果是第一个加载项，显示全局加载
  if (loadingQueue.value.size === 1) {
    globalLoading.value = true
    loadingText.value = loadingText
  }

  try {
    const result = await asyncFn()
    return result
  } finally {
    // 清除加载状态
    loadingStates[key] = false
    loadingQueue.value.delete(key)
    
    // 如果没有其他加载项，隐藏全局加载
    if (loadingQueue.value.size === 0) {
      globalLoading.value = false
    }
  }
}

/**
 * 全局加载状态管理器
 */
class LoadingManager {
  private static instance: LoadingManager
  private loadingCount = 0
  private loadingTexts: string[] = []

  private constructor() {}

  static getInstance(): LoadingManager {
    if (!LoadingManager.instance) {
      LoadingManager.instance = new LoadingManager()
    }
    return LoadingManager.instance
  }

  show(text = '加载中...'): void {
    this.loadingCount++
    if (this.loadingCount === 1) {
      globalLoading.value = true
      loadingText.value = text
    }
    this.loadingTexts.push(text)
  }

  hide(): void {
    this.loadingCount = Math.max(0, this.loadingCount - 1)
    if (this.loadingCount === 0) {
      globalLoading.value = false
      this.loadingTexts = []
    } else {
      // 显示上一个加载文本
      loadingText.value = this.loadingTexts[this.loadingTexts.length - 1] || '加载中...'
    }
  }

  isLoading(): boolean {
    return this.loadingCount > 0
  }

  getText(): string {
    return loadingText.value
  }
}

// 全局加载管理器实例
export const loadingManager = LoadingManager.getInstance()

/**
 * 创建加载指令
 */
export function createLoadingDirective() {
  return {
    mounted(el: HTMLElement, binding: any) {
      if (binding.value) {
        el.classList.add('loading')
        el.setAttribute('disabled', 'disabled')
      }
    },
    updated(el: HTMLElement, binding: any) {
      if (binding.value) {
        el.classList.add('loading')
        el.setAttribute('disabled', 'disabled')
      } else {
        el.classList.remove('loading')
        el.removeAttribute('disabled')
      }
    }
  }
}

/**
 * 防抖加载
 */
export function useDebouncedLoading(key: string, delay = 300) {
  let timeoutId: number | null = null

  const setLoading = (loading: boolean) => {
    if (timeoutId) {
      clearTimeout(timeoutId)
      timeoutId = null
    }

    if (loading) {
      timeoutId = window.setTimeout(() => {
        loadingStates[key] = true
      }, delay)
    } else {
      loadingStates[key] = false
    }
  }

  const isLoading = computed(() => loadingStates[key] || false)

  return {
    isLoading,
    setLoading
  }
}

/**
 * 批量加载状态管理
 */
export function useBatchLoading(keys: string[]) {
  const loadingStatesMap = reactive<Record<string, boolean>>({})

  keys.forEach(key => {
    loadingStatesMap[key] = false
  })

  const setLoading = (key: string, loading: boolean) => {
    if (keys.includes(key)) {
      loadingStatesMap[key] = loading
    }
  }

  const setAllLoading = (loading: boolean) => {
    keys.forEach(key => {
      loadingStatesMap[key] = loading
    })
  }

  const isLoading = computed(() => {
    return keys.some(key => loadingStatesMap[key])
  })

  const isAllLoading = computed(() => {
    return keys.every(key => loadingStatesMap[key])
  })

  const loadedCount = computed(() => {
    return keys.filter(key => !loadingStatesMap[key]).length
  })

  const progress = computed(() => {
    return (loadedCount.value / keys.length) * 100
  })

  return {
    loadingStates: computed(() => loadingStatesMap),
    isLoading,
    isAllLoading,
    loadedCount,
    progress,
    setLoading,
    setAllLoading
  }
}

/**
 * 加载状态组合式API
 */
export function useLoadingState() {
  return {
    global: useGlobalLoading(),
    create: (key: string) => useLoading(key),
    createDebounced: (key: string, delay?: number) => useDebouncedLoading(key, delay),
    createBatch: (keys: string[]) => useBatchLoading(keys),
    with: <T>(key: string, asyncFn: () => Promise<T>, text?: string) => 
      withLoading(key, asyncFn, text),
    manager: loadingManager
  }
}