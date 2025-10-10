<template>
  <div ref="chartRef" class="position-analysis-chart" :style="{ height }"></div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch } from 'vue'
import * as echarts from 'echarts'
import type { Position } from '@/common/apis/bots/type'

interface Props {
  positions: Position[]
  height?: string
  loading?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  height: '300px',
  loading: false
})

const chartRef = ref<HTMLElement>()
let chartInstance: echarts.ECharts | null = null

// 初始化图表
const initChart = () => {
  if (!chartRef.value) return

  chartInstance = echarts.init(chartRef.value)
  updateChart()

  window.addEventListener('resize', handleResize)
}

// 处理窗口大小变化
const handleResize = () => {
  chartInstance?.resize()
}

// 更新图表数据
const updateChart = () => {
  if (!chartInstance) return

  if (props.positions.length === 0) {
    // 无持仓时显示空状态
    const option: echarts.EChartsOption = {
      title: {
        text: '当前无持仓',
        left: 'center',
        top: 'center',
        textStyle: {
          fontSize: 14,
          color: '#999'
        }
      }
    }
    chartInstance.setOption(option)
    return
  }

  // 计算持仓统计
  const longPositions = props.positions.filter(p => p.side === 'long')
  const shortPositions = props.positions.filter(p => p.side === 'short')

  const longValue = longPositions.reduce((sum, p) => sum + (p.amount * p.entry_price), 0)
  const shortValue = shortPositions.reduce((sum, p) => sum + (p.amount * p.entry_price), 0)

  const longPnl = longPositions.reduce((sum, p) => sum + (p.unrealized_pnl || 0), 0)
  const shortPnl = shortPositions.reduce((sum, p) => sum + (p.unrealized_pnl || 0), 0)

  const option: echarts.EChartsOption = {
    title: {
      text: '持仓分布分析',
      left: 'center',
      textStyle: {
        fontSize: 16,
        fontWeight: 'bold'
      }
    },
    tooltip: {
      trigger: 'item',
      formatter: (params: any) => {
        const { name, value, percent } = params
        return `
          <div style="padding: 8px;">
            <div style="font-weight: bold; margin-bottom: 4px;">${name}</div>
            <div>持仓价值: $${value.toFixed(2)}</div>
            <div>占比: ${percent}%</div>
          </div>
        `
      }
    },
    legend: {
      orient: 'vertical',
      left: 'left',
      top: 'center',
      data: ['做多持仓', '做空持仓']
    },
    series: [
      {
        type: 'pie',
        radius: ['40%', '70%'],
        center: ['60%', '50%'],
        avoidLabelOverlap: false,
        itemStyle: {
          borderRadius: 10,
          borderColor: '#fff',
          borderWidth: 2
        },
        label: {
          show: true,
          formatter: (params: any) => {
            const pnl = params.name === '做多持仓' ? longPnl : shortPnl
            const pnlText = pnl >= 0 ? `+$${pnl.toFixed(2)}` : `-$${Math.abs(pnl).toFixed(2)}`
            return `{name|${params.name}}\n{value|$${params.value.toFixed(2)}}\n{pnl|${pnlText}}`
          },
          rich: {
            name: {
              fontSize: 14,
              fontWeight: 'bold',
              lineHeight: 20
            },
            value: {
              fontSize: 12,
              color: '#666',
              lineHeight: 18
            },
            pnl: {
              fontSize: 12,
              fontWeight: 'bold',
              lineHeight: 18
            }
          }
        },
        emphasis: {
          label: {
            show: true,
            fontSize: 16,
            fontWeight: 'bold'
          }
        },
        labelLine: {
          show: true
        },
        data: [
          {
            value: longValue,
            name: '做多持仓',
            itemStyle: {
              color: '#67C23A'
            }
          },
          {
            value: shortValue,
            name: '做空持仓',
            itemStyle: {
              color: '#F56C6C'
            }
          }
        ]
      }
    ]
  }

  chartInstance.setOption(option)
}

// 监听数据变化
watch(
  () => props.positions,
  () => {
    updateChart()
  },
  { deep: true }
)

// 监听加载状态
watch(
  () => props.loading,
  (loading) => {
    if (chartInstance) {
      if (loading) {
        chartInstance.showLoading()
      } else {
        chartInstance.hideLoading()
      }
    }
  }
)

// 生命周期
onMounted(() => {
  initChart()
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  chartInstance?.dispose()
  chartInstance = null
})

// 暴露方法供父组件调用
defineExpose({
  resize: () => chartInstance?.resize(),
  getInstance: () => chartInstance
})
</script>

<style scoped lang="scss">
.position-analysis-chart {
  width: 100%;
}
</style>
