<template>
  <div class="chart-widget">
    <div class="widget-header">
      <h3 class="widget-title">{{ title }}</h3>
      <div class="header-actions">
        <slot name="actions"></slot>
      </div>
    </div>
    <div class="widget-content">
      <v-chart class="chart" :option="chartOption" autoresize />
      <div v-if="loading" class="loading-overlay">
        <el-icon class="is-loading loading-icon"><Loading /></el-icon>
      </div>
      <div v-if="!loading && !hasData" class="empty-overlay">
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
.chart-widget {
  height: 100%;
  width: 100%;
  background: var(--color-surface-light);
  border-radius: var(--radius-lg);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  border: 1px solid rgba(0, 0, 0, 0.06);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.widget-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--space-sm) var(--space-md);
  border-bottom: 1px solid rgba(0, 0, 0, 0.06);
}

.widget-title {
  font-weight: 500;
  color: var(--color-text-dark);
  margin: 0;
}

.header-actions {
  display: flex;
  gap: var(--space-sm);
}

.widget-content {
  flex: 1;
  padding: var(--space-md);
  position: relative;
  min-height: 0;
}

.loading-overlay {
  position: absolute;
  inset: 0;
  background: rgba(255, 255, 255, 0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10;
}

.loading-icon {
  font-size: 24px;
  color: var(--color-accent);
}

.empty-overlay {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--color-text-tertiary);
  font-size: 14px;
}

.chart {
  height: 100%;
  width: 100%;
}
</style>
