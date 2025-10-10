<template>
  <div ref="chartRef" class="spread-chart" :style="{ height: height }"></div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch } from 'vue'
import * as echarts from 'echarts'
import type { SpreadHistory } from '@/common/apis/bots/type'

interface Props {
  data: SpreadHistory[]
  height?: string
  loading?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  height: '400px',
  loading: false
})

const chartRef = ref<HTMLElement>()
let chartInstance: echarts.ECharts | null = null

// 初始化图表
const initChart = () => {
  if (!chartRef.value) return

  chartInstance = echarts.init(chartRef.value)
  updateChart()

  // 响应式处理
  window.addEventListener('resize', handleResize)
}

// 处理窗口大小变化
const handleResize = () => {
  chartInstance?.resize()
}

// 更新图表数据
const updateChart = () => {
  if (!chartInstance) return

  const timestamps = props.data.map(item => 
    new Date(item.recorded_at).toLocaleTimeString('zh-CN', { 
      hour: '2-digit', 
      minute: '2-digit',
      second: '2-digit'
    })
  )
  const spreads = props.data.map(item => item.spread_percentage)
  const market1Prices = props.data.map(item => item.market1_price)
  const market2Prices = props.data.map(item => item.market2_price)

  const option: echarts.EChartsOption = {
    title: {
      text: '价差历史曲线',
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
          const value = param.value
          
          let displayValue = value
          if (seriesName === '价差') {
            displayValue = `${value.toFixed(4)}%`
          } else {
            displayValue = `$${value.toFixed(6)}`
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
      data: ['价差', '市场1价格', '市场2价格'],
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
        name: '价差 (%)',
        position: 'left',
        axisLabel: {
          formatter: '{value}%'
        },
        splitLine: {
          lineStyle: {
            type: 'dashed'
          }
        }
      },
      {
        type: 'value',
        name: '价格 (USD)',
        position: 'right',
        axisLabel: {
          formatter: '${value}'
        },
        splitLine: {
          show: false
        }
      }
    ],
    series: [
      {
        name: '价差',
        type: 'line',
        yAxisIndex: 0,
        data: spreads,
        smooth: true,
        lineStyle: {
          width: 2,
          color: '#409EFF'
        },
        itemStyle: {
          color: '#409EFF'
        },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(64, 158, 255, 0.3)' },
            { offset: 1, color: 'rgba(64, 158, 255, 0.05)' }
          ])
        },
        emphasis: {
          focus: 'series'
        }
      },
      {
        name: '市场1价格',
        type: 'line',
        yAxisIndex: 1,
        data: market1Prices,
        smooth: true,
        lineStyle: {
          width: 1.5,
          color: '#67C23A',
          type: 'dashed'
        },
        itemStyle: {
          color: '#67C23A'
        },
        emphasis: {
          focus: 'series'
        }
      },
      {
        name: '市场2价格',
        type: 'line',
        yAxisIndex: 1,
        data: market2Prices,
        smooth: true,
        lineStyle: {
          width: 1.5,
          color: '#E6A23C',
          type: 'dashed'
        },
        itemStyle: {
          color: '#E6A23C'
        },
        emphasis: {
          focus: 'series'
        }
      }
    ],
    dataZoom: [
      {
        type: 'inside',
        start: 0,
        end: 100
      },
      {
        type: 'slider',
        show: true,
        start: 0,
        end: 100,
        height: 20,
        bottom: 10
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
.spread-chart {
  width: 100%;
}
</style>