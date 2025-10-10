<template>
  <div ref="chartRef" class="trading-metrics-chart" :style="{ height }"></div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch } from 'vue'
import * as echarts from 'echarts'

interface TradingMetric {
  timestamp: string
  profitLoss: number
  totalTrades: number
  currentCycle: number
  dcaCount: number
}

interface Props {
  data: TradingMetric[]
  height?: string
  loading?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  height: '350px',
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
  if (!chartInstance || props.data.length === 0) return

  const timestamps = props.data.map(item =>
    new Date(item.timestamp).toLocaleTimeString('zh-CN', {
      hour: '2-digit',
      minute: '2-digit'
    })
  )
  const profits = props.data.map(item => item.profitLoss)
  const trades = props.data.map(item => item.totalTrades)
  const cycles = props.data.map(item => item.currentCycle)

  const option: echarts.EChartsOption = {
    title: {
      text: '交易指标实时监控',
      left: 'center',
      textStyle: {
        fontSize: 16,
        fontWeight: 'bold'
      }
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross'
      },
      formatter: (params: any) => {
        if (!Array.isArray(params)) return ''

        let result = `<div style="padding: 8px;">
          <div style="margin-bottom: 6px; font-weight: bold;">${params[0].axisValue}</div>`

        params.forEach((param: any) => {
          const color = param.color
          const seriesName = param.seriesName
          let value = param.value

          let displayValue = value
          if (seriesName === '累计盈亏') {
            displayValue = `$${value.toFixed(2)}`
          } else {
            displayValue = value
          }

          result += `
            <div style="margin: 4px 0;">
              <span style="display:inline-block;width:10px;height:10px;background-color:${color};margin-right:6px;border-radius:50%;"></span>
              <span>${seriesName}: ${displayValue}</span>
            </div>`
        })

        result += '</div>'
        return result
      }
    },
    legend: {
      data: ['累计盈亏', '总交易数', '交易循环'],
      top: 30,
      left: 'center'
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      top: 80,
      containLabel: true
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: timestamps,
      axisLabel: {
        rotate: 45,
        interval: 'auto'
      }
    },
    yAxis: [
      {
        type: 'value',
        name: '盈亏 (USD)',
        position: 'left',
        axisLabel: {
          formatter: '${value}'
        },
        splitLine: {
          lineStyle: {
            type: 'dashed'
          }
        }
      },
      {
        type: 'value',
        name: '交易数/循环数',
        position: 'right',
        splitLine: {
          show: false
        }
      }
    ],
    series: [
      {
        name: '累计盈亏',
        type: 'line',
        yAxisIndex: 0,
        data: profits,
        smooth: true,
        lineStyle: {
          width: 3
        },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            {
              offset: 0,
              color: profits[profits.length - 1] >= 0
                ? 'rgba(103, 194, 58, 0.3)'
                : 'rgba(245, 108, 108, 0.3)'
            },
            {
              offset: 1,
              color: profits[profits.length - 1] >= 0
                ? 'rgba(103, 194, 58, 0.05)'
                : 'rgba(245, 108, 108, 0.05)'
            }
          ])
        },
        itemStyle: {
          color: (params) => {
            const value = params.value as number
            return value >= 0 ? '#67C23A' : '#F56C6C'
          }
        }
      },
      {
        name: '总交易数',
        type: 'line',
        yAxisIndex: 1,
        data: trades,
        smooth: true,
        lineStyle: {
          width: 2,
          color: '#409EFF',
          type: 'dashed'
        },
        itemStyle: {
          color: '#409EFF'
        }
      },
      {
        name: '交易循环',
        type: 'line',
        yAxisIndex: 1,
        data: cycles,
        smooth: true,
        lineStyle: {
          width: 2,
          color: '#E6A23C'
        },
        itemStyle: {
          color: '#E6A23C'
        }
      }
    ]
  }

  chartInstance.setOption(option)
}

// 监听数据变化
watch(
  () => props.data,
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
.trading-metrics-chart {
  width: 100%;
}
</style>
