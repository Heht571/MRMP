<template>
  <PageContainer title="元模型定义" description="定义系统中的资源对象模型，包括设备类型、逻辑资源等。">
    <template #extra>
      <el-button type="primary" @click="handleAdd" class="bg-indigo-600 hover:bg-indigo-700 border-indigo-600">
        <el-icon class="mr-1"><Plus /></el-icon>
        新增模型
      </el-button>
    </template>

    <el-table 
      :data="models" 
      v-loading="loading" 
      stripe 
      style="width: 100%"
      :header-cell-style="{ background: '#f8fafc', color: '#475569', fontWeight: '600' }"
      :row-class-name="'hover:bg-gray-50 transition-colors'"
    >
      <el-table-column label="模型名称" min-width="180">
        <template #default="{ row }">
          <div class="flex items-center gap-3">
            <div 
              class="w-8 h-8 rounded-lg flex items-center justify-center text-white text-sm font-bold shadow-sm"
              :style="{ backgroundColor: row.color || '#6366f1' }"
            >
              {{ (row.name || '?')[0].toUpperCase() }}
            </div>
            <div class="flex flex-col">
              <span class="font-medium text-gray-900">{{ row.name }}</span>
              <span class="text-xs text-gray-400">{{ row.code }}</span>
            </div>
          </div>
        </template>
      </el-table-column>
      <el-table-column prop="category" label="分类" width="120">
        <template #default="{ row }">
          <el-tag size="small" effect="plain" type="info" class="capitalize">{{ row.category }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="属性数" width="100" align="center">
        <template #default="{ row }">
          <div class="flex items-center justify-center gap-1 text-gray-500">
            <el-icon><Operation /></el-icon>
            <span class="font-mono">{{ row.attributes?.length || 0 }}</span>
          </div>
        </template>
      </el-table-column>
      <el-table-column label="状态" width="100" align="center">
        <template #default="{ row }">
          <div class="flex items-center justify-center gap-2">
            <span class="relative flex h-2.5 w-2.5">
              <span v-if="row.is_active" class="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
              <span class="relative inline-flex rounded-full h-2.5 w-2.5" :class="row.is_active ? 'bg-green-500' : 'bg-gray-400'"></span>
            </span>
            <span class="text-xs" :class="row.is_active ? 'text-green-600' : 'text-gray-500'">{{ row.is_active ? '启用' : '禁用' }}</span>
          </div>
        </template>
      </el-table-column>
      <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip>
        <template #default="{ row }">
          <span class="text-gray-500">{{ row.description || '-' }}</span>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="200" fixed="right">
        <template #default="{ row }">
          <div class="flex items-center gap-2">
            <el-button type="primary" link size="small" @click="handleView(row)">查看</el-button>
            <el-button type="primary" link size="small" @click="handleEdit(row)">配置</el-button>
            <el-button type="danger" link size="small" @click="handleDelete(row)">删除</el-button>
          </div>
        </template>
      </el-table-column>
    </el-table>

    <!-- Model Edit Dialog -->
    <el-dialog 
      v-model="dialogVisible" 
      :title="dialogTitle" 
      width="900px" 
      destroy-on-close
      class="rounded-xl overflow-hidden"
    >
      <el-tabs v-model="activeTab" class="px-2">
        <el-tab-pane label="基本信息" name="basic">
          <el-form ref="formRef" :model="form" :rules="rules" label-width="100px" class="py-4">
            <el-row :gutter="24">
              <el-col :span="12">
                <el-form-item label="模型名称" prop="name">
                  <el-input v-model="form.name" placeholder="如：机房、OLT、交换机" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="模型编码" prop="code">
                  <el-input v-model="form.code" placeholder="如：room、olt、switch" :disabled="!!currentModel?.id" />
                </el-form-item>
              </el-col>
            </el-row>
            <el-row :gutter="24">
              <el-col :span="12">
                <el-form-item label="分类" prop="category">
                  <el-select v-model="form.category" placeholder="选择分类" class="w-full">
                    <el-option label="机房设施" value="room" />
                    <el-option label="网络设备" value="network" />
                    <el-option label="传输设备" value="transmission" />
                    <el-option label="电源设备" value="power" />
                    <el-option label="其他" value="other" />
                  </el-select>
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="状态">
                  <el-switch v-model="form.is_active" active-text="启用" inactive-text="禁用" />
                </el-form-item>
              </el-col>
            </el-row>
            <el-row :gutter="24">
              <el-col :span="12">
                <el-form-item label="图标">
                  <el-input v-model="form.icon" placeholder="图标名称" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="颜色">
                  <el-color-picker v-model="form.color" />
                </el-form-item>
              </el-col>
            </el-row>
            <el-form-item label="描述">
              <el-input v-model="form.description" type="textarea" :rows="3" placeholder="模型描述" />
            </el-form-item>
          </el-form>
        </el-tab-pane>

        <el-tab-pane label="属性配置" name="attributes">
          <div class="bg-gray-50 rounded-lg border border-gray-200 p-4 min-h-[400px]">
            <div class="flex justify-between items-center mb-4">
              <span class="text-sm font-medium text-gray-600">拖拽调整属性顺序</span>
              <el-button type="primary" size="small" @click="showAttributeSelector" plain>
                <el-icon class="mr-1"><Plus /></el-icon>
                添加属性
              </el-button>
            </div>

            <draggable 
              v-model="form.attributes" 
              item-key="attribute_id"
              handle=".drag-handle"
              animation="200"
              ghost-class="ghost"
              class="space-y-2"
            >
              <template #item="{ element, index }">
                <div class="bg-white border border-gray-200 rounded-lg p-3 flex items-center gap-3 hover:shadow-sm hover:border-indigo-300 transition-all group">
                  <div class="drag-handle cursor-move text-gray-400 hover:text-indigo-600 p-1">
                    <el-icon><Rank /></el-icon>
                  </div>
                  <div class="w-6 h-6 rounded-full bg-gray-100 flex items-center justify-center text-xs text-gray-500 font-mono">
                    {{ index + 1 }}
                  </div>
                  <div class="flex-1">
                    <div class="flex items-center gap-2">
                      <span class="font-medium text-gray-800">{{ element.label }}</span>
                      <span class="text-xs text-gray-400 font-mono">{{ element.name }}</span>
                    </div>
                  </div>
                  <el-tag size="small" type="info">{{ element.type }}</el-tag>
                  <div class="flex items-center gap-4 ml-4">
                    <el-checkbox v-model="element.is_required" label="必填" size="small" />
                    <el-button type="danger" link size="small" @click="removeAttribute(element)" class="opacity-0 group-hover:opacity-100 transition-opacity">
                      移除
                    </el-button>
                  </div>
                </div>
              </template>
            </draggable>
            
            <el-empty v-if="form.attributes.length === 0" description="暂无属性，请点击上方按钮添加" :image-size="100" />
          </div>
        </el-tab-pane>
      </el-tabs>

      <template #footer>
        <div class="flex justify-end gap-3">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" @click="handleSubmit" :loading="submitting" class="bg-indigo-600 border-indigo-600 hover:bg-indigo-700">保存</el-button>
        </div>
      </template>
    </el-dialog>

    <!-- Attribute Selector Dialog -->
    <el-dialog v-model="attrSelectorVisible" title="选择全局属性" width="800px" class="rounded-xl">
      <el-input v-model="attrSearch" placeholder="搜索属性名称" clearable class="mb-4">
        <template #prefix><el-icon><Search /></el-icon></template>
      </el-input>
      <el-table 
        ref="attrTableRef"
        :data="filteredGlobalAttrs" 
        @selection-change="handleAttrSelection"
        max-height="400"
        stripe
        :header-cell-style="{ background: '#f8fafc', fontWeight: '600' }"
      >
        <el-table-column type="selection" width="50" />
        <el-table-column prop="name" label="属性名" width="150" />
        <el-table-column prop="label" label="显示名" width="150" />
        <el-table-column prop="type" label="类型" width="100">
          <template #default="{ row }">
            <el-tag size="small">{{ row.type }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="description" label="描述" show-overflow-tooltip />
      </el-table>
      <template #footer>
        <el-button @click="attrSelectorVisible = false">取消</el-button>
        <el-button type="primary" @click="confirmAttrSelection" class="bg-indigo-600 border-indigo-600">确定选择</el-button>
      </template>
    </el-dialog>

    <!-- Detail Dialog -->
    <el-dialog v-model="detailDialogVisible" title="模型详情" width="800px" class="rounded-xl">
      <el-descriptions :column="2" border class="mb-6">
        <el-descriptions-item label="模型名称">{{ currentModel.name }}</el-descriptions-item>
        <el-descriptions-item label="模型编码">{{ currentModel.code }}</el-descriptions-item>
        <el-descriptions-item label="分类">{{ currentModel.category }}</el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="currentModel.is_active ? 'success' : 'info'" size="small">
            {{ currentModel.is_active ? '启用' : '禁用' }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="描述" :span="2">{{ currentModel.description || '-' }}</el-descriptions-item>
      </el-descriptions>

      <div class="font-bold text-gray-800 mb-3 flex items-center gap-2">
        <el-icon><List /></el-icon> 属性列表 ({{ currentModel.attributes?.length || 0 }})
      </div>
      <el-table :data="currentModel.attributes" border size="small" style="width: 100%" stripe>
        <el-table-column prop="name" label="属性名" width="150" />
        <el-table-column prop="label" label="显示名" width="150" />
        <el-table-column prop="type" label="类型" width="100" />
        <el-table-column label="必填" width="80" align="center">
          <template #default="{ row }">
            <el-tag v-if="row.is_required" type="danger" size="small" effect="plain">是</el-tag>
            <span v-else class="text-gray-300">-</span>
          </template>
        </el-table-column>
        <el-table-column prop="sort_order" label="排序" width="80" align="center" />
      </el-table>
    </el-dialog>
  </PageContainer>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search, Rank, Operation, List } from '@element-plus/icons-vue'
import draggable from 'vuedraggable'
import api from '@/api'

const loading = ref(false)
const models = ref<any[]>([])
const globalAttrs = ref<any[]>([])
const dialogVisible = ref(false)
const detailDialogVisible = ref(false)
const attrSelectorVisible = ref(false)
const submitting = ref(false)
const currentModel = ref<any>({})
const formRef = ref(null)
const attrTableRef = ref(null)
const activeTab = ref('basic')
const attrSearch = ref('')
const selectedAttrs = ref<any[]>([])

const dialogTitle = computed(() => currentModel.value?.id ? '编辑模型' : '新增模型')

const filteredGlobalAttrs = computed(() => {
  if (!attrSearch.value) return globalAttrs.value
  const search = attrSearch.value.toLowerCase()
  return globalAttrs.value.filter(a => 
    a.name.toLowerCase().includes(search) || 
    a.label.toLowerCase().includes(search)
  )
})

const form = reactive<any>({
  name: '',
  code: '',
  category: '',
  description: '',
  icon: '',
  color: '#409EFF',
  is_active: true,
  attributes: []
})

const rules = {
  name: [{ required: true, message: '请输入模型名称', trigger: 'blur' }],
  code: [{ required: true, message: '请输入模型编码', trigger: 'blur' }, { pattern: /^[a-z_]+$/, message: '只能包含小写字母和下划线', trigger: 'blur' }],
  category: [{ required: true, message: '请选择分类', trigger: 'change' }]
}

const loadModels = async () => {
  loading.value = true
  try {
    const res = await api.get('/v2/models/')
    models.value = res.data
  } catch (error) {
    console.error('加载模型列表失败:', error)
  } finally {
    loading.value = false
  }
}

const loadGlobalAttrs = async () => {
  try {
    const res = await api.get('/v2/global-attributes/')
    globalAttrs.value = res.data
  } catch (error) {
    console.error('加载全局属性失败:', error)
  }
}

const handleAdd = () => {
  currentModel.value = {}
  Object.assign(form, {
    name: '',
    code: '',
    category: '',
    description: '',
    icon: '',
    color: '#409EFF',
    is_active: true,
    attributes: []
  })
  activeTab.value = 'basic'
  dialogVisible.value = true
}

const handleView = (row: any) => {
  currentModel.value = row
  detailDialogVisible.value = true
}

const handleEdit = async (row: any) => {
  currentModel.value = row
  try {
    const res = await api.get(`/v2/models/${row.id}`)
    const model = res.data
    
    Object.assign(form, {
      name: model.name,
      code: model.code,
      category: model.category,
      description: model.description,
      icon: model.icon || '',
      color: model.color || '#409EFF',
      is_active: model.is_active,
      attributes: (model.attributes || []).map((a: any) => ({
        attribute_id: a.attribute_id || a.id,
        name: a.name,
        label: a.label,
        type: a.type,
        is_required: a.is_required || false,
        sort_order: a.sort_order || 0
      }))
    })
    activeTab.value = 'basic'
    dialogVisible.value = true
  } catch (error) {
    console.error('加载模型详情失败:', error)
  }
}

const handleDelete = async (row: any) => {
  try {
    await ElMessageBox.confirm('确定要删除该模型吗？', '提示', { 
      type: 'warning',
      confirmButtonClass: 'el-button--danger'
    })
    await api.delete(`/v2/models/${row.id}`)
    ElMessage.success('删除成功')
    loadModels()
  } catch (error) {
    if (error !== 'cancel') console.error('删除失败:', error)
  }
}

const showAttributeSelector = () => {
  selectedAttrs.value = []
  attrSelectorVisible.value = true
}

const handleAttrSelection = (selection: any[]) => {
  selectedAttrs.value = selection
}

const confirmAttrSelection = () => {
  const existingIds = form.attributes.map((a: any) => a.attribute_id)
  for (const attr of selectedAttrs.value) {
    if (!existingIds.includes(attr.id)) {
      form.attributes.push({
        attribute_id: attr.id,
        name: attr.name,
        label: attr.label,
        type: attr.type.value || attr.type,
        is_required: false,
        sort_order: form.attributes.length * 10
      })
    }
  }
  attrSelectorVisible.value = false
  ElMessage.success(`已添加 ${selectedAttrs.value.length} 个属性`)
}

const removeAttribute = (row: any) => {
  const index = form.attributes.findIndex((a: any) => a.attribute_id === row.attribute_id)
  if (index > -1) {
    form.attributes.splice(index, 1)
  }
}

const handleSubmit = async () => {
  try {
    if (activeTab.value === 'basic') {
      await (formRef.value as any).validate()
    }
    
    submitting.value = true
    
    const data = {
      name: form.name,
      code: form.code,
      category: form.category,
      description: form.description,
      icon: form.icon,
      color: form.color,
      is_active: form.is_active,
      attributes: form.attributes.map((a: any, index: number) => ({
        attribute_id: a.attribute_id,
        is_required: a.is_required,
        sort_order: index
      }))
    }
    
    if (currentModel.value?.id) {
      await api.put(`/v2/models/${currentModel.value.id}`, data)
      ElMessage.success('更新成功')
    } else {
      await api.post('/v2/models/', data)
      ElMessage.success('创建成功')
    }
    
    dialogVisible.value = false
    loadModels()
  } catch (error: any) {
    console.error('保存失败:', error)
    ElMessage.error(error.response?.data?.detail || '保存失败')
  } finally {
    submitting.value = false
  }
}

onMounted(() => {
  loadModels()
  loadGlobalAttrs()
})
</script>

<style scoped>
.ghost {
  opacity: 0.5;
  background: #eff6ff;
  border: 1px dashed #6366f1;
}
</style>
