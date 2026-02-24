<template>
  <div class="h-full w-full flex flex-col bg-white rounded-lg shadow-sm overflow-hidden">
    <div class="px-4 py-3 border-b border-gray-100 flex justify-between items-center">
      <h3 class="font-medium text-gray-700">{{ title }}</h3>
      <div class="flex gap-2">
        <slot name="actions"></slot>
      </div>
    </div>
    <div class="flex-1 p-4 relative min-h-0">
      <v-chart class="chart" :option="chartOption" autoresize />
      <div v-if="loading" class="absolute inset-0 bg-white/80 flex items-center justify-center z-10">
        <el-icon class="is-loading text-indigo-500 text-2xl"><Loading /></el-icon>
      </div>
      <div v-if="!loading && !hasData" class="absolute inset-0 flex items-center justify-center text-gray-400 text-sm">
        暂无数据
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { BarChart, LineChart, PieChart } from 'echarts/charts'
import {
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent
} from 'echarts/components'
import VChart from 'vue-echarts'
import { Loading } from '@element-plus/icons-vue'
import api from '@/api'

use([
  CanvasRenderer,
  BarChart,
  LineChart,
  PieChart,
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent
])

const props = defineProps<{
  title: string
  config: any
  widgetId?: string
}>()

const loading = ref(false)
const hasData = ref(false)
const chartData = ref<any[]>([])

const chartOption = computed(() => {
  const { chart_type } = props.config
  
  if (!hasData.value) return {}

  const xAxisData = chartData.value.map(item => item.name)
  const seriesData = chartData.value.map(item => item.value)

  const baseOption = {
    tooltip: {
      trigger: 'axis'
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    }
  }

  if (chart_type === 'pie') {
    return {
      tooltip: {
        trigger: 'item'
      },
      series: [
        {
          type: 'pie',
          radius: ['40%', '70%'],
          avoidLabelOverlap: false,
          itemStyle: {
            borderRadius: 10,
            borderColor: '#fff',
            borderWidth: 2
          },
          label: {
            show: false,
            position: 'center'
          },
          emphasis: {
            label: {
              show: true,
              fontSize: 20,
              fontWeight: 'bold'
            }
          },
          labelLine: {
            show: false
          },
          data: chartData.value
        }
      ]
    }
  }

  return {
    ...baseOption,
    xAxis: {
      type: 'category',
      data: xAxisData
    },
    yAxis: {
      type: 'value'
    },
    series: [
      {
        data: seriesData,
        type: chart_type || 'bar',
        itemStyle: {
          color: '#6366f1'
        },
        smooth: true
      }
    ]
  }
})

const loadData = async () => {
  if (!props.widgetId) return
  
  loading.value = true
  try {
    const res = await api.get(`/v2/dashboard/widgets/${props.widgetId}/data`)
    
    if (res.data && res.data.labels && res.data.datasets && res.data.datasets.length > 0) {
      const labels = res.data.labels
      const values = res.data.datasets[0].data
      
      chartData.value = labels.map((label: string, index: number) => ({
        name: label,
        value: values[index]
      }))
      hasData.value = true
    } else {
      hasData.value = false
    }
  } catch (error) {
    console.error('Failed to load chart data', error)
    hasData.value = false
  } finally {
    loading.value = false
  }
}

watch(() => props.config, loadData, { deep: true })

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.chart {
  height: 100%;
  width: 100%;
}
</style>
