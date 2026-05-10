<template>
  <div class="search-builder">
    <div v-for="(filter, index) in filters" :key="index" class="filter-row">
      <!-- 字段选择 -->
      <el-select
        v-model="filter.field"
        placeholder="选择属性"
        class="field-select"
        @change="handleFieldChange(filter)"
      >
        <el-option
          v-for="attr in attributes"
          :key="attr.name"
          :label="attr.label"
          :value="attr.name"
        />
      </el-select>

      <!-- 操作符选择 -->
      <el-select v-model="filter.operator" placeholder="操作符" class="operator-select">
        <el-option
          v-for="op in getOperators(filter.field)"
          :key="op.value"
          :label="op.label"
          :value="op.value"
        />
      </el-select>

      <!-- 值输入 -->
      <div class="value-input">
        <template v-if="!['is_null', 'not_null'].includes(filter.operator)">
          <!-- 枚举类型 -->
          <el-select
            v-if="getFieldType(filter.field) === 'enum'"
            v-model="filter.value"
            placeholder="选择值"
            class="full-width"
            clearable
          >
            <el-option
              v-for="opt in getEnumOptions(filter.field)"
              :key="opt.value"
              :label="opt.label"
              :value="opt.value"
            />
          </el-select>

          <!-- 布尔类型 -->
          <el-select
            v-else-if="getFieldType(filter.field) === 'boolean'"
            v-model="filter.value"
            placeholder="选择值"
            class="full-width"
          >
            <el-option label="是" :value="true" />
            <el-option label="否" :value="false" />
          </el-select>

          <!-- 数字类型 -->
          <el-input-number
            v-else-if="getFieldType(filter.field) === 'number'"
            v-model="filter.value"
            class="full-width"
            controls-position="right"
          />

          <!-- 日期类型 -->
          <el-date-picker
            v-else-if="['date', 'datetime'].includes(getFieldType(filter.field))"
            v-model="filter.value"
            type="date"
            class="full-width"
            value-format="YYYY-MM-DD"
          />

          <!-- 默认文本 -->
          <el-input
            v-else
            v-model="filter.value"
            placeholder="输入值"
          />
        </template>
      </div>

      <!-- 删除按钮 -->
      <el-button
        type="danger"
        circle
        size="small"
        icon="Delete"
        @click="removeFilter(index)"
        :disabled="filters.length === 1 && !filter.field"
      />
    </div>

    <!-- 底部操作栏 -->
    <div class="filter-actions">
      <el-button type="primary" link icon="Plus" @click="addFilter">添加条件</el-button>
      <div class="action-buttons">
        <el-button @click="resetFilters">重置</el-button>
        <el-button type="primary" @click="handleSearch">查询</el-button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, computed } from 'vue'

const props = defineProps<{
  attributes: any[]
}>()

const emit = defineEmits(['search', 'reset'])

interface Filter {
  field: string
  operator: string
  value: any
}

const filters = ref<Filter[]>([
  { field: '', operator: 'eq', value: '' }
])

const baseAttributes = [
  { name: 'name', label: '名称', type: 'string' },
  { name: 'code', label: '编码', type: 'string' },
  { name: 'created_at', label: '创建时间', type: 'datetime' },
  { name: 'updated_at', label: '更新时间', type: 'datetime' }
]

const allAttributes = computed(() => {
  return [...baseAttributes, ...props.attributes]
})

const getFieldType = (fieldName: string) => {
  const attr = allAttributes.value.find(a => a.name === fieldName)
  return attr?.type || 'string'
}

const getEnumOptions = (fieldName: string) => {
  const attr = props.attributes.find(a => a.name === fieldName)
  if (!attr?.enum_values) return []
  return attr.enum_values.map((v: any) => {
    if (typeof v === 'object') return { label: v.label || v.value, value: v.value }
    return { label: v, value: v }
  })
}

const getOperators = (fieldName: string) => {
  const type = getFieldType(fieldName)
  const common = [
    { label: '等于', value: 'eq' },
    { label: '不等于', value: 'ne' },
    { label: '为空', value: 'is_null' },
    { label: '不为空', value: 'not_null' }
  ]
  
  if (type === 'number' || type === 'date' || type === 'datetime') {
    return [
      ...common,
      { label: '大于', value: 'gt' },
      { label: '小于', value: 'lt' },
      { label: '大于等于', value: 'gte' },
      { label: '小于等于', value: 'lte' }
    ]
  }
  
  if (type === 'string') {
    return [
      ...common,
      { label: '包含', value: 'ilike' }
    ]
  }
  
  return common
}

const handleFieldChange = (filter: Filter) => {
  filter.value = ''
  filter.operator = 'eq'
}

const addFilter = () => {
  filters.value.push({ field: '', operator: 'eq', value: '' })
}

const removeFilter = (index: number) => {
  if (filters.value.length === 1) {
    filters.value[0] = { field: '', operator: 'eq', value: '' }
  } else {
    filters.value.splice(index, 1)
  }
}

const resetFilters = () => {
  filters.value = [{ field: '', operator: 'eq', value: '' }]
  emit('reset')
}

const handleSearch = () => {
  const validFilters = filters.value.filter(f => f.field)
  emit('search', validFilters)
}
</script>

<style scoped>
.search-builder {
  padding: var(--space-md);
}

.filter-row {
  display: flex;
  gap: var(--space-sm);
  margin-bottom: var(--space-sm);
  align-items: center;
}

.field-select {
  width: 160px;
}

.operator-select {
  width: 128px;
}

.value-input {
  flex: 1;
}

.full-width {
  width: 100%;
}

.filter-actions {
  display: flex;
  justify-content: space-between;
  margin-top: var(--space-sm);
}

.action-buttons {
  display: flex;
  gap: var(--space-sm);
}
</style>
