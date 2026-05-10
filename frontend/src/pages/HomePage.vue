<template>
  <div class="home-page">
    <!-- Header -->
    <div class="page-header">
      <div class="header-content">
        <h1 class="page-title">仪表盘</h1>
        <p class="page-subtitle">自定义您的专属数据视图</p>
      </div>
      <div class="header-actions">
        <el-button v-if="!isEditMode" @click="isEditMode = true" type="primary">
          <el-icon><Edit /></el-icon> 编辑布局
        </el-button>
        <template v-else>
          <el-button @click="handleAddWidget" type="primary">
            <el-icon><Plus /></el-icon> 添加组件
          </el-button>
          <el-button @click="saveLayout" type="success">
            <el-icon><Check /></el-icon> 保存
          </el-button>
          <el-button @click="cancelEdit">取消</el-button>
        </template>
      </div>
    </div>

    <!-- Dashboard Grid -->
    <div class="dashboard-container" :class="{ 'edit-mode': isEditMode }">
      
      <div v-if="loading" class="loading-overlay">
        <el-icon class="is-loading loading-icon"><Loading /></el-icon>
      </div>

      <div class="dashboard-grid">
        <div 
          v-for="widget in widgets" 
          :key="widget.id"
          class="widget-wrapper"
          :class="getWidgetClass(widget)"
        >
          <!-- Edit Actions -->
          <div v-if="isEditMode" class="widget-actions">
            <el-button circle size="small" type="primary" @click="editWidget(widget)">
              <el-icon><Edit /></el-icon>
            </el-button>
            <el-button circle size="small" type="danger" @click="removeWidget(widget)">
              <el-icon><Delete /></el-icon>
            </el-button>
          </div>

          <!-- Widget Content -->
          <component 
            :is="getComponent(widget.type)" 
            :title="widget.name" 
            :config="widget.config" 
            :widget-id="widget.id"
          />
        </div>

        <!-- Add Button Placeholder -->
        <div 
          v-if="isEditMode" 
          class="add-widget-placeholder"
          @click="handleAddWidget"
        >
          <el-icon class="add-icon"><Plus /></el-icon>
          <span class="add-text">添加新组件</span>
        </div>
      </div>
      
      <el-empty v-if="!loading && widgets.length === 0 && !isEditMode" description="暂无仪表盘组件，点击编辑添加" />
    </div>

    <!-- Widget Config Dialog -->
    <el-dialog 
      v-model="dialogVisible" 
      :title="editingWidget?.id ? '编辑组件' : '添加组件'" 
      width="600px" 
      destroy-on-close
    >
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px" class="widget-form">
        <el-form-item label="组件名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入组件标题" />
        </el-form-item>
        
        <el-form-item label="组件类型" prop="type">
          <el-select v-model="form.type" placeholder="选择类型" class="full-width">
            <el-option label="统计数值 (Stat)" value="stat" />
            <el-option label="图表 (Chart)" value="chart" />
            <el-option label="列表 (List)" value="list" />
          </el-select>
        </el-form-item>

        <el-divider content-position="left">数据配置</el-divider>
        
        <el-form-item label="数据源模型" prop="config.model_id">
          <el-select v-model="form.config.model_id" placeholder="选择模型" class="full-width" filterable>
            <el-option v-for="m in models" :key="m.id" :label="m.name" :value="m.id" />
          </el-select>
        </el-form-item>

        <!-- Stat Config -->
        <template v-if="form.type === 'stat'">
          <el-form-item label="单位">
            <el-input v-model="form.config.unit" placeholder="如：个、台" />
          </el-form-item>
        </template>

        <!-- Chart Config -->
        <template v-if="form.type === 'chart'">
          <el-form-item label="图表类型">
            <el-radio-group v-model="form.config.chart_type">
              <el-radio-button label="bar">柱状图</el-radio-button>
              <el-radio-button label="line">折线图</el-radio-button>
              <el-radio-button label="pie">饼图</el-radio-button>
            </el-radio-group>
          </el-form-item>
          <el-form-item label="聚合方式">
            <el-select v-model="form.config.aggregation" class="full-width">
              <el-option label="计数 (Count)" value="count" />
              <el-option label="求和 (Sum)" value="sum" />
            </el-select>
          </el-form-item>
          <el-form-item label="维度字段">
            <el-select 
              v-model="form.config.dimension" 
              placeholder="选择统计维度" 
              class="full-width"
              filterable
              allow-create
            >
              <el-option 
                v-for="dim in availableDimensions" 
                :key="dim.value" 
                :label="dim.label" 
                :value="dim.value" 
              />
            </el-select>
          </el-form-item>
        </template>

        <el-form-item label="宽/高 (Grid)">
           <el-col :span="11">
             <el-input-number v-model="form.layout.w" :min="1" :max="4" label="宽" class="full-width" />
           </el-col>
           <el-col :span="2" class="text-center">-</el-col>
           <el-col :span="11">
             <el-input-number v-model="form.layout.h" :min="1" :max="4" label="高" class="full-width" />
           </el-col>
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { Edit, Plus, Check, Delete, Loading } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '@/api'
import ChartWidget from '@/components/dashboard/ChartWidget.vue'
import StatWidget from '@/components/dashboard/StatWidget.vue'
import ListWidget from '@/components/dashboard/ListWidget.vue'

const isEditMode = ref(false)
const loading = ref(false)
const submitting = ref(false)
const widgets = ref<any[]>([])
const models = ref<any[]>([])
const dialogVisible = ref(false)
const editingWidget = ref<any>(null)
const formRef = ref(null)

const form = reactive({
  name: '',
  type: 'stat',
  config: {
    model_id: '',
    unit: '',
    chart_type: 'bar',
    aggregation: 'count',
    dimension: ''
  },
  layout: { w: 1, h: 1 }
})

const availableDimensions = computed(() => {
  const base = [
    { label: '生命周期状态 (Status)', value: 'status' },
    { label: '实例名称 (Name)', value: 'name' },
    { label: '实例编码 (Code)', value: 'code' }
  ]
  
  if (form.config.model_id) {
    const model = models.value.find(m => m.id === form.config.model_id)
    if (model && model.attributes) {
      model.attributes.forEach((attr: any) => {
        base.push({ label: `${attr.label} (${attr.name})`, value: attr.name })
      })
    }
  }
  return base
})

const rules = {
  name: [{ required: true, message: '请输入名称', trigger: 'blur' }],
  type: [{ required: true, message: '请选择类型', trigger: 'change' }],
  'config.model_id': [{ required: true, message: '请选择数据源', trigger: 'change' }]
}

const getComponent = (type: string) => {
  const map: any = {
    chart: ChartWidget,
    stat: StatWidget,
    list: ListWidget
  }
  return map[type] || StatWidget
}

const getWidgetClass = (widget: any) => {
  const w = widget.layout?.w || 1
  const h = widget.layout?.h || 1
  
  // Width classes
  const widthClass = w === 4 ? 'widget-width-full' : w === 2 ? 'widget-width-half' : 'widget-width-quarter'
  
  // Height classes  
  const heightClass = h === 2 ? 'widget-height-lg' : h === 3 ? 'widget-height-xl' : 'widget-height-md'
  
  // Edit mode class
  const editClass = isEditMode.value ? 'widget-edit-mode' : ''
  
  return `${widthClass} ${heightClass} ${editClass}`
}

const loadWidgets = async () => {
  loading.value = true
  try {
    const res = await api.get('/v2/dashboard/widgets')
    widgets.value = res.data
  } catch (error) {
    console.error('Failed to load widgets', error)
  } finally {
    loading.value = false
  }
}

const loadModels = async () => {
  try {
    const res = await api.get('/v2/models/')
    models.value = res.data
  } catch (error) {
    console.error('Failed to load models', error)
  }
}

const handleAddWidget = () => {
  editingWidget.value = null
  Object.assign(form, {
    name: '',
    type: 'stat',
    config: { model_id: '', unit: '', chart_type: 'bar', aggregation: 'count', dimension: '' },
    layout: { w: 1, h: 1 }
  })
  dialogVisible.value = true
}

const editWidget = (widget: any) => {
  editingWidget.value = widget
  Object.assign(form, {
    name: widget.name,
    type: widget.type,
    config: { ...widget.config },
    layout: { ...widget.layout }
  })
  dialogVisible.value = true
}

const removeWidget = async (widget: any) => {
  try {
    await ElMessageBox.confirm('确定要删除该组件吗？', '提示', { type: 'warning' })
    await api.delete(`/v2/dashboard/widgets/${widget.id}`)
    widgets.value = widgets.value.filter(w => w.id !== widget.id)
    ElMessage.success('删除成功')
  } catch (error) {}
}

const handleSubmit = async () => {
  try {
    await (formRef.value as any).validate()
  } catch { return }

  submitting.value = true
  try {
    const payload = { ...form }
    
    if (editingWidget.value) {
      const res = await api.put(`/v2/dashboard/widgets/${editingWidget.value.id}`, payload)
      const idx = widgets.value.findIndex(w => w.id === editingWidget.value.id)
      if (idx !== -1) widgets.value[idx] = res.data
      ElMessage.success('更新成功')
    } else {
      const res = await api.post('/v2/dashboard/widgets', payload)
      widgets.value.push(res.data)
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
  } catch (error) {
    ElMessage.error('保存失败')
  } finally {
    submitting.value = false
  }
}

const saveLayout = () => {
  isEditMode.value = false
  ElMessage.success('布局已保存')
}

const cancelEdit = () => {
  isEditMode.value = false
  loadWidgets()
}

onMounted(() => {
  loadWidgets()
  loadModels()
})
</script>

<style scoped lang="scss">
.home-page {
  display: flex;
  flex-direction: column;
  gap: var(--space-lg);
}

// --- Page Header ---
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: var(--color-surface-light);
  padding: var(--space-md) var(--space-lg);
  border-radius: var(--radius-xl);
}

.header-content {
  display: flex;
  flex-direction: column;
}

.page-title {
  font-size: 20px;
  font-weight: 600;
  color: var(--color-text-dark);
  margin: 0;
}

.page-subtitle {
  font-size: 14px;
  color: var(--color-text-tertiary);
  margin-top: var(--space-xs);
}

.header-actions {
  display: flex;
  gap: var(--space-sm);
}

// --- Dashboard Container ---
.dashboard-container {
  min-height: 600px;
  position: relative;
  background: var(--color-bg-light);
  border-radius: var(--radius-xl);
  padding: var(--space-md);

  &.edit-mode {
    border: 2px dashed var(--color-accent);
    background: rgba(0, 113, 227, 0.03);
  }
}

.loading-overlay {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.8);
  z-index: 10;

  .loading-icon {
    font-size: 32px;
    color: var(--color-accent);
  }
}

// --- Dashboard Grid ---
.dashboard-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: var(--space-md);
}

// --- Widget Sizes ---
.widget-wrapper {
  position: relative;
  transition: all var(--transition-base);

  &.widget-width-full {
    grid-column: span 4;
  }

  &.widget-width-half {
    grid-column: span 2;
  }

  &.widget-width-quarter {
    grid-column: span 1;
  }

  &.widget-height-md {
    height: 160px;
  }

  &.widget-height-lg {
    height: 320px;
  }

  &.widget-height-xl {
    height: 384px;
  }

  &.widget-edit-mode {
    cursor: move;

    &:hover {
      .widget-actions {
        opacity: 1;
      }
    }
  }
}

.widget-actions {
  position: absolute;
  top: var(--space-sm);
  right: var(--space-sm);
  z-index: 20;
  display: flex;
  gap: var(--space-xs);
  opacity: 0;
  transition: opacity var(--transition-fast);
}

// --- Add Widget Placeholder ---
.add-widget-placeholder {
  height: 160px;
  border: 2px dashed var(--color-text-tertiary);
  border-radius: var(--radius-lg);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: var(--color-text-tertiary);
  cursor: pointer;
  transition: all var(--transition-fast);

  &:hover {
    border-color: var(--color-accent);
    color: var(--color-accent);
    background: rgba(0, 113, 227, 0.05);
  }

  .add-icon {
    font-size: 32px;
    margin-bottom: var(--space-sm);
  }

  .add-text {
    font-size: 14px;
  }
}

// --- Widget Form ---
.widget-form {
  padding: var(--space-md) 0;

  .full-width {
    width: 100%;
  }
}

// --- Responsive ---
@media (max-width: 1024px) {
  .dashboard-grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .widget-width-full {
    grid-column: span 2;
  }
}

@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
    align-items: flex-start;
    gap: var(--space-md);
  }

  .dashboard-grid {
    grid-template-columns: 1fr;
  }

  .widget-width-full,
  .widget-width-half,
  .widget-width-quarter {
    grid-column: span 1;
  }
}
</style>