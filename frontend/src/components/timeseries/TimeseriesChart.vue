<template>
  <div class="timeseries-chart">
    <div class="chart-header">
      <div class="header-left">
        <span class="chart-title">{{ title }}</span>
        <el-tag v-if="latestValue" size="small" type="success">
          最新: {{ formatLatestValue(latestValue) }}
        </el-tag>
      </div>
      <div class="header-right">
        <el-date-picker
          v-model="dateRange"
          type="datetimerange"
          range-separator="至"
          start-placeholder="开始时间"
          end-placeholder="结束时间"
          :shortcuts="shortcuts"
          @change="handleDateRangeChange"
          style="width: 360px;"
        />
        <el-select v-model="selectedBucket" @change="handleBucketChange" style="width: 120px; margin-left: 8px;">
          <el-option label="原始" value="" />
          <el-option label="1分钟" value="1 minute" />
          <el-option label="5分钟" value="5 minute" />
          <el-option label="15分钟" value="15 minute" />
          <el-option label="1小时" value="1 hour" />
          <el-option label="1天" value="1 day" />
        </el-select>
        <el-button type="primary" link @click="refreshData" :loading="loading">
          <el-icon><Refresh /></el-icon>
        </el-button>
      </div>
    </div>

    <div v-if="loading" class="chart-loading">
      <el-icon class="is-loading"><Loading /></el-icon>
      加载中...
    </div>

    <div v-else-if="!hasData" class="chart-empty">
      <el-empty description="暂无时序数据" :image-size="80" />
    </div>

    <div v-else class="chart-container" ref="chartRef"></div>

    <div v-if="showLegend && legendData.length > 0" class="chart-legend">
      <el-checkbox-group v-model="visibleMetrics" @change="handleLegendChange">
        <el-checkbox
          v-for="metric in legendData"
          :key="metric.key"
          :label="metric.key"
          :value="metric.key"
        >
          <span class="legend-item">
            <span class="legend-color" :style="{ backgroundColor: metric.color }"></span>
            {{ metric.label }}
          </span>
        </el-checkbox>
      </el-checkbox-group>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { Refresh, Loading } from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import api from '@/api'

interface Props {
  instanceId: string
  attributeName: string
  refId?: string
  title?: string
  metrics?: string[]
  showLegend?: boolean
  height?: number
}

const props = defineProps<Props>()

const emit = defineEmits(['update:dateRange', 'dataLoaded'])

const chartRef = ref<HTMLElement>()
let chartInstance: echarts.ECharts | null = null

const loading = ref(false)
const hasData = ref(false)
const dataPoints = ref<any[]>([])
const latestValue = ref<any>(null)
const selectedBucket = ref('')
const dateRange = ref<[Date, Date] | null>(null)

const visibleMetrics = ref<string[]>([...(props.metrics || ['cpu', 'memory', 'disk', 'network'])])

const metricColors: Record<string, string> = {
  cpu: '#67c23a',
  memory: '#409eff',
  disk: '#e6a23c',
  network: '#f56c6c',
  in: '#909399',
  out: '#c71585'
}

const metricLabels: Record<string, string> = {
  cpu: 'CPU (%)',
  memory: '内存 (MB)',
  disk: '磁盘 (%)',
  network: '网络 (Mbps)',
  in: '入站 (Mbps)',
  out: '出站 (Mbps)'
}

const legendData = computed(() => {
  return (props.metrics || ['cpu', 'memory', 'disk', 'network']).map(key => ({
    key,
    label: metricLabels[key] || key,
    color: metricColors[key] || '#409eff'
  }))
})

const shortcuts = [
  {
    text: '最近1小时',
    value: () => {
      const end = new Date()
      const start = new Date(end.getTime() - 60 * 60 * 1000)
      return [start, end]
    }
  },
  {
    text: '最近6小时',
    value: () => {
      const end = new Date()
      const start = new Date(end.getTime() - 6 * 60 * 60 * 1000)
      return [start, end]
    }
  },
  {
    text: '最近24小时',
    value: () => {
      const end = new Date()
      const start = new Date(end.getTime() - 24 * 60 * 60 * 1000)
      return [start, end]
    }
  },
  {
    text: '最近7天',
    value: () => {
      const end = new Date()
      const start = new Date(end.getTime() - 7 * 24 * 60 * 60 * 1000)
      return [start, end]
    }
  },
  {
    text: '最近30天',
    value: () => {
      const end = new Date()
      const start = new Date(end.getTime() - 30 * 24 * 60 * 60 * 1000)
      return [start, end]
    }
  }
]

const initChart = () => {
  if (!chartRef.value) return
  chartInstance = echarts.init(chartRef.value)
  updateChart()
}

const updateChart = () => {
  if (!chartInstance) return

  const series: any[] = []
  const xAxisData = dataPoints.value.map(dp => {
    const ts = dp.bucket ? new Date(dp.bucket) : new Date(dp.timestamp)
    return selectedBucket.value
      ? ts.toLocaleString('zh-CN', { hour12: false })
      : ts.toLocaleTimeString('zh-CN', { hour12: false })
  })

  visibleMetrics.value.forEach(metric => {
    const color = metricColors[metric] || '#409eff'

    if (selectedBucket.value) {
      series.push({
        name: `${metricLabels[metric] || metric} (均值)`,
        type: 'line',
        data: dataPoints.value.map(dp => dp[`${metric}_avg`] ?? dp.values?.[metric] ?? null),
        smooth: true,
        showSymbol: false,
        lineStyle: { width: 2, color },
        itemStyle: { color }
      })
    } else {
      series.push({
        name: metricLabels[metric] || metric,
        type: 'line',
        data: dataPoints.value.map(dp => dp.values?.[metric] ?? null),
        smooth: true,
        showSymbol: false,
        lineStyle: { width: 2, color },
        itemStyle: { color }
      })
    }
  })

  const option: echarts.EChartsOption = {
    tooltip: {
      trigger: 'axis',
      confine: true,
      formatter: (params: any) => {
        if (!params || params.length === 0) return ''
        let html = `<div style="font-weight: 600; margin-bottom: 4px;">${params[0].axisValue}</div>`
        params.forEach((p: any) => {
          if (p.value !== null && p.value !== undefined) {
            html += `<div style="display: flex; align-items: center; gap: 4px;">
              <span style="display: inline-block; width: 10px; height: 10px; border-radius: 50%; background: ${p.color};"></span>
              ${p.seriesName}: <b>${typeof p.value === 'number' ? p.value.toFixed(2) : p.value}</b>
            </div>`
          }
        })
        return html
      }
    },
    legend: { show: false },
    grid: {
      left: 60,
      right: 30,
      top: 20,
      bottom: 40
    },
    xAxis: {
      type: 'category',
      data: xAxisData,
      boundaryGap: false,
      axisLabel: { rotate: 45, fontSize: 11 }
    },
    yAxis: {
      type: 'value',
      splitLine: { lineStyle: { type: 'dashed', color: '#eee' } }
    },
    series
  }

  chartInstance.setOption(option)
}

const loadData = async () => {
  if (!dateRange.value) return

  loading.value = true
  const [startTime, endTime] = dateRange.value

  try {
    const url = `/api/v1/instances/${props.instanceId}/timeseries/${props.attributeName}`
    const params: Record<string, string> = {
      start_time: startTime.toISOString(),
      end_time: endTime.toISOString()
    }

    if (selectedBucket.value) {
      params.bucket = selectedBucket.value
    }

    const res = await api.get(url, { params })

    dataPoints.value = res.data.data || []
    hasData.value = dataPoints.value.length > 0

    if (hasData.value) {
      latestValue.value = dataPoints.value[dataPoints.value.length - 1].values
    }

    nextTick(() => {
      updateChart()
    })

    emit('dataLoaded', dataPoints.value)

  } catch (error: any) {
    console.error('Load timeseries data failed:', error)
    ElMessage.error(error?.response?.data?.detail || '加载时序数据失败')
  } finally {
    loading.value = false
  }
}

const refreshData = () => loadData()

const handleDateRangeChange = () => loadData()
const handleBucketChange = () => loadData()
const handleLegendChange = () => updateChart()

const formatLatestValue = (values: any) => {
  const firstMetric = props.metrics?.[0] || 'cpu'
  const val = values?.[firstMetric]
  return val !== undefined ? val.toFixed(2) : '-'
}

const handleResize = () => chartInstance?.resize()

watch([() => props.instanceId, () => props.attributeName], () => {
  if (props.instanceId && props.attributeName) {
    loadData()
  }
})

onMounted(() => {
  const end = new Date()
  const start = new Date(end.getTime() - 24 * 60 * 60 * 1000)
  dateRange.value = [start, end]

  nextTick(() => {
    initChart()
    if (props.instanceId && props.attributeName) {
      loadData()
    }
  })

  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  chartInstance?.dispose()
})

defineExpose({ refreshData, loadData })
</script>

<style scoped lang="scss">
.timeseries-chart {
  background: #fff;
  border-radius: 8px;
  padding: 16px;
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.chart-title {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.header-right {
  display: flex;
  align-items: center;
}

.chart-loading,
.chart-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 300px;
  color: #909399;
}

.chart-container {
  width: 100%;
  height: v-bind(height + 'px');
}

.chart-legend {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid #eee;
}

.legend-item {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.legend-color {
  display: inline-block;
  width: 12px;
  height: 3px;
  border-radius: 2px;
}

:deep(.el-checkbox) {
  margin-right: 16px;
}
</style>