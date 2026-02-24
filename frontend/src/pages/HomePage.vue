<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex justify-between items-center bg-white p-4 rounded-xl shadow-sm border border-gray-100">
      <div>
        <h1 class="text-xl font-bold text-gray-800">仪表盘</h1>
        <p class="text-sm text-gray-500 mt-1">自定义您的专属数据视图</p>
      </div>
      <div class="flex gap-2">
        <el-button v-if="!isEditMode" @click="isEditMode = true" type="primary" plain class="bg-indigo-50 text-indigo-600 border-indigo-200">
          <el-icon class="mr-1"><Edit /></el-icon> 编辑布局
        </el-button>
        <template v-else>
          <el-button @click="handleAddWidget" type="primary" class="bg-indigo-600 border-indigo-600">
            <el-icon class="mr-1"><Plus /></el-icon> 添加组件
          </el-button>
          <el-button @click="saveLayout" type="success" class="bg-green-600 border-green-600">
            <el-icon class="mr-1"><Check /></el-icon> 保存
          </el-button>
          <el-button @click="cancelEdit">取消</el-button>
        </template>
      </div>
    </div>

    <!-- Dashboard Grid -->
    <div class="min-h-[600px] relative bg-gray-50/50 rounded-xl border-2 border-dashed border-gray-200 p-4" :class="{ 'border-indigo-300 bg-indigo-50/30': isEditMode }">
      
      <div v-if="loading" class="absolute inset-0 flex items-center justify-center bg-white/50 z-10">
        <el-icon class="is-loading text-3xl text-indigo-500"><Loading /></el-icon>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div 
          v-for="widget in widgets" 
          :key="widget.id"
          class="relative group transition-all duration-300"
          :class="[
            getWidgetClass(widget),
            isEditMode ? 'cursor-move ring-2 ring-transparent hover:ring-indigo-400' : ''
          ]"
        >
          <!-- Edit Actions -->
          <div v-if="isEditMode" class="absolute top-2 right-2 z-20 flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
            <el-button circle size="small" type="primary" @click="editWidget(widget)"><el-icon><Edit /></el-icon></el-button>
            <el-button circle size="small" type="danger" @click="removeWidget(widget)"><el-icon><Delete /></el-icon></el-button>
          </div>

          <!-- Widget Content -->
          <component 
            :is="getComponent(widget.type)" 
            :title="widget.name" 
            :config="widget.config" 
            :widget-id="widget.id"
            class="h-full"
          />
        </div>

        <!-- Add Button Placeholder -->
        <div 
          v-if="isEditMode" 
          class="h-40 border-2 border-dashed border-gray-300 rounded-lg flex flex-col items-center justify-center text-gray-400 cursor-pointer hover:border-indigo-500 hover:text-indigo-500 hover:bg-indigo-50 transition-all"
          @click="handleAddWidget"
        >
          <el-icon class="text-3xl mb-2"><Plus /></el-icon>
          <span class="text-sm">添加新组件</span>
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
      class="rounded-xl"
    >
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px" class="py-4">
        <el-form-item label="组件名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入组件标题" />
        </el-form-item>
        
        <el-form-item label="组件类型" prop="type">
          <el-select v-model="form.type" placeholder="选择类型" class="w-full">
            <el-option label="统计数值 (Stat)" value="stat" />
            <el-option label="图表 (Chart)" value="chart" />
            <el-option label="列表 (List)" value="list" />
          </el-select>
        </el-form-item>

        <el-divider content-position="left">数据配置</el-divider>
        
        <el-form-item label="数据源模型" prop="config.model_id">
          <el-select v-model="form.config.model_id" placeholder="选择模型" class="w-full" filterable>
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
            <el-select v-model="form.config.aggregation" class="w-full">
              <el-option label="计数 (Count)" value="count" />
              <el-option label="求和 (Sum)" value="sum" />
            </el-select>
          </el-form-item>
          <el-form-item label="维度字段">
            <el-select 
              v-model="form.config.dimension" 
              placeholder="选择统计维度" 
              class="w-full"
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
             <el-input-number v-model="form.layout.w" :min="1" :max="4" label="宽" class="w-full" />
           </el-col>
           <el-col :span="2" class="text-center">-</el-col>
           <el-col :span="11">
             <el-input-number v-model="form.layout.h" :min="1" :max="4" label="高" class="w-full" />
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
  
  // Tailwind grid classes mapping
  const colSpan = w === 4 ? 'col-span-4' : w === 2 ? 'md:col-span-2' : 'col-span-1'
  const rowSpan = h > 1 ? `row-span-${h}` : ''
  
  // Height calculation
  const heightClass = h === 2 ? 'h-80' : h === 3 ? 'h-96' : 'h-40'
  
  return `${colSpan} ${rowSpan} ${heightClass}`
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
  loadWidgets() // Revert changes
}

onMounted(() => {
  loadWidgets()
  loadModels()
})
</script>
