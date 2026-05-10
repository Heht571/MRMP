<template>
  <div class="stat-widget">
    <div class="widget-header">
      <el-icon class="cursor-pointer more-icon hover"><MoreFilled /></el-icon>
    </div>

    <div class="widget-title-wrapper">
      <span class="widget-title">{{ title }}</span>
    </div>

    <div class="widget-value-wrapper">
      <span class="widget-value">{{ value }}</span>
      <span v-if="unit" class="widget-unit">{{ unit }}</span>
    </div>

    <div v-if="trend" class="widget-trend" :class="trend > 0 ? 'trend-up' : 'trend-down'">
      <el-icon v-if="trend > 0"><CaretTop /></el-icon>
      <el-icon v-else><CaretBottom /></el-icon>
      <span>{{ Math.abs(trend) }}%</span>
      <span class="trend-label">较上周</span>
    </div>

    <div class="widget-footer"></div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { CaretTop, CaretBottom, MoreFilled } from '@element-plus/icons-vue'
import api from '@/api'

const props = defineProps<{
  title: string
  config: any
  widgetId?: string
}>()

const value = ref(0)
const trend = ref(0)
const unit = ref('')

const loadData = async () => {
  if (!props.widgetId) {
    value.value = 0
    return
  }
  
  try {
    const res = await api.get(`/v2/dashboard/widgets/${props.widgetId}/data`)
    if (res.data) {
      value.value = res.data.value
      trend.value = res.data.trend || 0
      unit.value = res.data.unit || props.config.unit || ''
    }
  } catch (error) {
    console.error('Failed to load stat data', error)
  }
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.stat-widget {
  height: 100%;
  width: 100%;
  background: var(--color-surface-light);
  border-radius: var(--radius-lg);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  border: 1px solid rgba(0, 0, 0, 0.06);
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  padding: var(--space-md);
  position: relative;
  overflow: hidden;
  transition: border-color var(--transition-base);
}

.stat-widget:hover {
  border-color: var(--color-accent);
}

.widget-header {
  position: absolute;
  top: 0;
  right: 0;
  padding: var(--space-sm);
  opacity: 0;
  transition: opacity var(--transition-base);
}

.stat-widget:hover .widget-header {
  opacity: 1;
}

.more-icon {
  cursor: pointer;
  color: var(--color-text-tertiary);
}

.more-icon:hover {
  color: var(--color-accent);
}

.widget-title-wrapper {
  margin-bottom: var(--space-sm);
}

.widget-title {
  font-size: 14px;
  font-weight: 500;
  color: var(--color-text-secondary);
}

.widget-value-wrapper {
  display: flex;
  align-items: flex-end;
  gap: var(--space-sm);
}

.widget-value {
  font-size: 36px;
  font-weight: 700;
  color: var(--color-text-dark);
}

.widget-unit {
  font-size: 12px;
  color: var(--color-text-tertiary);
  margin-bottom: 4px;
}

.widget-trend {
  display: flex;
  align-items: center;
  font-size: 12px;
  margin-top: var(--space-sm);
}

.trend-up {
  color: var(--color-success);
}

.trend-down {
  color: var(--color-danger);
}

.trend-label {
  color: var(--color-text-tertiary);
  margin-left: 4px;
}

.widget-footer {
  position: absolute;
  bottom: 0;
  left: 0;
  width: 100%;
  height: 4px;
  background: linear-gradient(90deg, var(--color-accent), #a855f7);
  opacity: 0;
  transition: opacity var(--transition-base);
}

.stat-widget:hover .widget-footer {
  opacity: 1;
}
</style>
