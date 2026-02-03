<template>
  <div ref="chartRef" :style="{ height: height }"></div>
</template>

<script setup>
import { ref, onMounted, watch, nextTick } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
  type: {
    type: String,
    default: 'pie',
    validator: (value) => ['pie', 'bar'].includes(value)
  },
  data: {
    type: Array,
    default: () => []
  },
  height: {
    type: String,
    default: '300px'
  }
})

const chartRef = ref()
const chartInstance = ref(null)

const initChart = () => {
  if (!chartRef.value) return

  if (chartInstance.value) {
    chartInstance.value.dispose()
  }

  chartInstance.value = echarts.init(chartRef.value)

  const option = props.type === 'pie' ? getPieOption() : getBarOption()
  chartInstance.value.setOption(option)

  // 响应窗口大小变化
  const handleResize = () => {
    chartInstance.value?.resize()
  }

  window.addEventListener('resize', handleResize)

  // 清理函数
  return () => {
    window.removeEventListener('resize', handleResize)
    chartInstance.value?.dispose()
  }
}

const getPieOption = () => {
  return {
    tooltip: {
      trigger: 'item',
      formatter: '{a} <br/>{b}: {c} ({d}%)'
    },
    legend: {
      orient: 'vertical',
      right: 10,
      top: 'center',
      itemWidth: 12,
      itemHeight: 12,
      textStyle: {
        fontSize: 12
      }
    },
    series: [
      {
        name: '用例状态',
        type: 'pie',
        radius: ['40%', '70%'],
        avoidLabelOverlap: false,
        itemStyle: {
          borderRadius: 10,
          borderColor: '#fff',
          borderWidth: 2
        },
        label: {
          show: true,
          formatter: '{b}: {c}'
        },
        emphasis: {
          label: {
            show: true,
            fontSize: '14',
            fontWeight: 'bold'
          }
        },
        labelLine: {
          show: true
        },
        data: props.data.map(item => ({
          value: item.value,
          name: item.name,
          itemStyle: {
            color: item.color
          }
        }))
      }
    ]
  }
}

const getBarOption = () => {
  return {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'shadow'
      }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      top: '10%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: props.data.map(item => item.name),
      axisLabel: {
        color: '#666'
      }
    },
    yAxis: {
      type: 'value',
      axisLabel: {
        color: '#666'
      },
      splitLine: {
        lineStyle: {
          color: '#f0f0f0'
        }
      }
    },
    series: [
      {
        name: '用例数量',
        type: 'bar',
        barWidth: '60%',
        itemStyle: {
          color: (params) => {
            return props.data[params.dataIndex]?.color || '#1890ff'
          },
          borderRadius: [4, 4, 0, 0]
        },
        label: {
          show: true,
          position: 'top',
          formatter: '{c}'
        },
        data: props.data.map(item => item.value)
      }
    ]
  }
}

const updateChart = () => {
  if (chartInstance.value) {
    const option = props.type === 'pie' ? getPieOption() : getBarOption()
    chartInstance.value.setOption(option, true)
  }
}

onMounted(() => {
  nextTick(() => {
    initChart()
  })
})

watch([() => props.type, () => props.data], () => {
  updateChart()
}, { deep: true })
</script>

<style scoped>
/* 图表容器的样式已在父组件中定义 */
</style>
