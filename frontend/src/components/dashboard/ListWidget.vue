<template>
  <div class="list-widget">
    <div class="widget-header">
      <h3 class="widget-title">{{ title }}</h3>
      <el-button type="primary" link size="small" @click="handleMore">更多</el-button>
    </div>

    <div class="widget-content">
      <ul class="item-list">
        <li v-for="(item, index) in list" :key="index" class="item-row">
          <div class="item-left">
            <div class="item-avatar" :class="item.status === 'error' ? 'avatar-error' : 'avatar-success'">
              {{ item.name.substring(0, 1).toUpperCase() }}
            </div>
            <div>
              <div class="item-name">{{ item.name }}</div>
              <div class="item-code">{{ item.code }}</div>
            </div>
          </div>
          <div class="item-right">
            <div class="item-status" :class="item.status === 'error' ? 'status-error' : 'status-success'">
              {{ item.status === 'error' ? '异常' : '正常' }}
            </div>
            <div class="item-time">{{ formatTime(item.updated_at) }}</div>
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

<style scoped>
.list-widget {
  height: 100%;
  width: 100%;
  background: var(--color-surface-light);
  border-radius: var(--radius-lg);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  border: 1px solid rgba(0, 0, 0, 0.06);
  display: flex;
  flex-direction: column;
  padding: var(--space-md);
}

.widget-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-sm);
  padding-bottom: var(--space-sm);
  border-bottom: 1px solid rgba(0, 0, 0, 0.06);
}

.widget-title {
  font-weight: 500;
  color: var(--color-text-dark);
  margin: 0;
}

.widget-content {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
}

.item-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
}

.item-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--space-sm);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: background var(--transition-base);
}

.item-row:hover {
  background: var(--color-bg-light);
}

.item-row:hover .item-name {
  color: var(--color-accent);
}

.item-left {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
}

.item-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 700;
  color: white;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.avatar-error {
  background: var(--color-danger);
}

.avatar-success {
  background: var(--color-success);
}

.item-name {
  font-size: 14px;
  font-weight: 500;
  color: var(--color-text-dark);
  transition: color var(--transition-base);
}

.item-code {
  font-size: 12px;
  color: var(--color-text-tertiary);
}

.item-right {
  text-align: right;
}

.item-status {
  font-size: 12px;
  font-weight: 500;
}

.status-error {
  color: var(--color-danger);
}

.status-success {
  color: var(--color-success);
}

.item-time {
  font-size: 10px;
  color: var(--color-text-tertiary);
}

.custom-scrollbar {
  scrollbar-width: thin;
}
</style>
