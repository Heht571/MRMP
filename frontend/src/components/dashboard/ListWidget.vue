<template>
  <div class="h-full w-full bg-white rounded-lg shadow-sm border border-gray-100 flex flex-col p-4">
    <div class="flex items-center justify-between mb-3 border-b border-gray-100 pb-2">
      <h3 class="font-medium text-gray-700">{{ title }}</h3>
      <el-button type="primary" link size="small" @click="handleMore">更多</el-button>
    </div>
    
    <div class="flex-1 overflow-y-auto overflow-x-hidden custom-scrollbar">
      <ul class="space-y-2">
        <li v-for="(item, index) in list" :key="index" class="flex items-center justify-between p-2 hover:bg-gray-50 rounded-md transition-colors cursor-pointer group">
          <div class="flex items-center gap-3">
            <div class="w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold text-white shadow-sm" :class="item.status === 'error' ? 'bg-red-500' : 'bg-green-500'">
              {{ item.name.substring(0, 1).toUpperCase() }}
            </div>
            <div>
              <div class="text-sm font-medium text-gray-800 group-hover:text-indigo-600 transition-colors">{{ item.name }}</div>
              <div class="text-xs text-gray-400">{{ item.code }}</div>
            </div>
          </div>
          <div class="text-right">
            <div class="text-xs font-medium" :class="item.status === 'error' ? 'text-red-500' : 'text-green-600'">
              {{ item.status === 'error' ? '异常' : '正常' }}
            </div>
            <div class="text-[10px] text-gray-400">{{ formatTime(item.updated_at) }}</div>
          </div>
        </li>
      </ul>
      
      <el-empty v-if="list.length === 0" description="暂无数据" :image-size="60" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/api'

const router = useRouter()
const props = defineProps<{
  title: string
  config: any
  widgetId?: string
}>()

const list = ref<any[]>([])

const loadData = async () => {
  if (!props.widgetId) return
  
  try {
    const res = await api.get(`/v2/dashboard/widgets/${props.widgetId}/data`)
    if (res.data && res.data.data) {
      list.value = res.data.data
    }
  } catch (error) {
    console.error('Failed to load list data', error)
  }
}

const handleMore = () => {
  if (props.config.model_id) {
    router.push({ path: '/instances', query: { model_id: props.config.model_id } })
  }
}

const formatTime = (time: string) => {
  const date = new Date(time)
  return `${date.getHours()}:${date.getMinutes().toString().padStart(2, '0')}`
}

onMounted(() => {
  loadData()
})
</script>
