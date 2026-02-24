<template>
  <div class="h-full w-full bg-white rounded-lg shadow-sm border border-gray-100 flex flex-col justify-center items-center p-4 relative overflow-hidden group hover:border-indigo-200 transition-colors">
    <div class="absolute top-0 right-0 p-2 opacity-0 group-hover:opacity-100 transition-opacity">
      <el-icon class="cursor-pointer text-gray-400 hover:text-indigo-600"><MoreFilled /></el-icon>
    </div>
    
    <div class="text-gray-500 text-sm font-medium mb-2">{{ title }}</div>
    
    <div class="flex items-end gap-2">
      <span class="text-3xl font-bold text-gray-900">{{ value }}</span>
      <span v-if="unit" class="text-xs text-gray-400 mb-1">{{ unit }}</span>
    </div>
    
    <div v-if="trend" class="mt-2 flex items-center text-xs" :class="trend > 0 ? 'text-green-500' : 'text-red-500'">
      <el-icon v-if="trend > 0"><CaretTop /></el-icon>
      <el-icon v-else><CaretBottom /></el-icon>
      <span>{{ Math.abs(trend) }}%</span>
      <span class="text-gray-400 ml-1">较上周</span>
    </div>
    
    <div class="absolute bottom-0 left-0 w-full h-1 bg-gradient-to-r from-indigo-500 to-purple-500 opacity-0 group-hover:opacity-100 transition-opacity"></div>
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
