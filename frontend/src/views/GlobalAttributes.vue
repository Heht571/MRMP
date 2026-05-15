<template>
  <PageContainer title="全局属性池" description="管理系统中通用的属性定义，可被多个模型引用。">
    <template #extra>
      <el-input
        v-model="searchName"
        placeholder="搜索属性名称"
        class="w-64"
        clearable
        @clear="loadAttributes"
        @keyup.enter="loadAttributes"
      >
        <template #prefix>
          <el-icon><Search /></el-icon>
        </template>
      </el-input>
      <el-button type="primary" @click="handleAdd" class="bg-indigo-600 hover:bg-indigo-700 border-indigo-600">
        <el-icon class="mr-1"><Plus /></el-icon>
        新增属性
      </el-button>
    </template>

    <el-table 
      :data="attributes" 
      v-loading="loading" 
      stripe 
      style="width: 100%"
      :header-cell-style="{ background: '#f8fafc', color: '#475569', fontWeight: '600' }"
      :row-class-name="'hover:bg-gray-50 transition-colors'"
    >
      <el-table-column prop="name" label="属性名称" width="180">
        <template #default="{ row }">
          <span class="font-mono text-indigo-600 bg-indigo-50 px-2 py-1 rounded text-xs">{{ row.name }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="label" label="显示标签" width="150" />
      <el-table-column label="数据类型" width="120">
        <template #default="{ row }">
          <el-tag size="small" :type="getTypeTagType(row.type)" effect="light" round>{{ row.type }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="特性" min-width="240">
        <template #default="{ row }">
          <div class="flex flex-wrap gap-1">
            <el-tag v-if="row.is_choice" size="small" type="info" effect="plain">枚举</el-tag>
            <el-tag v-if="row.is_reference" size="small" type="warning" effect="plain">引用</el-tag>
            <el-tag v-if="row.is_computed" size="small" type="success" effect="plain">计算</el-tag>
            <el-tag v-if="row.is_unique" size="small" type="danger" effect="plain">唯一</el-tag>
            <el-tag v-if="row.is_indexed" size="small" effect="plain">索引</el-tag>
          </div>
        </template>
      </el-table-column>
      <el-table-column label="引用模型" width="150">
        <template #default="{ row }">
          <span v-if="row.is_reference && row.reference_model_id" class="text-gray-600 flex items-center gap-1">
            <el-icon><Link /></el-icon>
            {{ getModelName(row.reference_model_id) }}
          </span>
          <span v-else class="text-gray-300">-</span>
        </template>
      </el-table-column>
      <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip>
        <template #default="{ row }">
          <span class="text-gray-500">{{ row.description || '-' }}</span>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="150" fixed="right">
        <template #default="{ row }">
          <div class="flex items-center gap-2">
            <el-button type="primary" link size="small" @click="handleEdit(row)">编辑</el-button>
            <el-button type="danger" link size="small" @click="handleDelete(row)">删除</el-button>
          </div>
        </template>
      </el-table-column>
    </el-table>

    <!-- Dialog -->
    <el-dialog 
      v-model="dialogVisible" 
      :title="dialogTitle" 
      width="800px" 
      destroy-on-close
      class="rounded-xl overflow-hidden"
    >
      <el-form ref="formRef" :model="form" :rules="rules" label-width="120px" class="py-4">
        <el-row :gutter="24">
          <el-col :span="12">
            <el-form-item label="属性名称" prop="name">
              <el-input v-model="form.name" placeholder="英文键，如：ip_address" :disabled="isEdit">
                <template #prefix><el-icon class="text-gray-400"><Key /></el-icon></template>
              </el-input>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="显示标签" prop="label">
              <el-input v-model="form.label" placeholder="中文显示名" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="24">
          <el-col :span="12">
            <el-form-item label="数据类型" prop="type">
              <el-select v-model="form.type" placeholder="选择数据类型" class="w-full">
                <el-option label="字符串 (String)" value="string" />
                <el-option label="数字 (Number)" value="number" />
                <el-option label="枚举 (Enum)" value="enum" />
                <el-option label="布尔 (Boolean)" value="boolean" />
                <el-option label="日期 (Date)" value="date" />
                <el-option label="日期时间 (Datetime)" value="datetime" />
                <el-option label="JSON" value="json" />
                <el-option label="UUID" value="uuid" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="描述">
              <el-input v-model="form.description" placeholder="属性用途描述" />
            </el-form-item>
          </el-col>
        </el-row>

        <div class="bg-gray-50 p-4 rounded-lg border border-gray-100 mb-6">
          <div class="text-sm font-semibold text-gray-700 mb-3 flex items-center">
            <el-icon class="mr-1"><Operation /></el-icon> 属性特性
          </div>
          <el-row :gutter="24">
            <el-col :span="6"><el-form-item label="枚举类型" class="mb-0"><el-switch v-model="form.is_choice" /></el-form-item></el-col>
            <el-col :span="6"><el-form-item label="列表类型" class="mb-0"><el-switch v-model="form.is_list" /></el-form-item></el-col>
            <el-col :span="6"><el-form-item label="唯一性" class="mb-0"><el-switch v-model="form.is_unique" /></el-form-item></el-col>
            <el-col :span="6"><el-form-item label="可索引" class="mb-0"><el-switch v-model="form.is_indexed" /></el-form-item></el-col>
          </el-row>
          <el-row :gutter="24" class="mt-2">
            <el-col :span="6"><el-form-item label="可排序" class="mb-0"><el-switch v-model="form.is_sortable" /></el-form-item></el-col>
            <el-col :span="6"><el-form-item label="引用属性" class="mb-0"><el-switch v-model="form.is_reference" /></el-form-item></el-col>
            <el-col :span="6"><el-form-item label="计算属性" class="mb-0"><el-switch v-model="form.is_computed" /></el-form-item></el-col>
          </el-row>
        </div>

        <template v-if="form.is_reference">
          <div class="bg-amber-50 p-4 rounded-lg border border-amber-100 mb-6">
             <div class="text-sm font-semibold text-amber-800 mb-3">引用配置</div>
             <el-form-item label="引用模型" prop="reference_model_id" class="mb-0">
              <el-select v-model="form.reference_model_id" placeholder="选择引用模型" class="w-full">
                <el-option v-for="model in models" :key="model.id" :label="model.name" :value="model.id" />
              </el-select>
            </el-form-item>
          </div>
        </template>

        <template v-if="form.is_choice">
          <div class="bg-blue-50 p-4 rounded-lg border border-blue-100 mb-6">
            <div class="text-sm font-semibold text-blue-800 mb-3">枚举值配置</div>
            <div class="space-y-2">
              <div v-for="(item, index) in form.enum_values" :key="index" class="flex items-center gap-2">
                <el-input v-model="item.value" placeholder="值 (Value)" class="w-32" />
                <el-input v-model="item.label" placeholder="标签 (Label)" class="w-32" />
                <el-color-picker v-model="item.color" show-alpha />
                <el-button type="danger" circle size="small" @click="form.enum_values.splice(index, 1)">
                  <el-icon><Delete /></el-icon>
                </el-button>
              </div>
              <el-button type="primary" link @click="addEnumValue" size="small">
                <el-icon class="mr-1"><Plus /></el-icon> 添加枚举值
              </el-button>
            </div>
          </div>
        </template>

        <template v-if="form.is_computed">
          <div class="bg-green-50 p-4 rounded-lg border border-green-100 mb-6">
            <div class="text-sm font-semibold text-green-800 mb-3">计算配置</div>
            <el-form-item label="计算表达式">
              <el-input v-model="form.compute_expr" type="textarea" :rows="2" placeholder="如: ${attr1} + ${attr2}" />
            </el-form-item>
            <el-form-item label="计算脚本" class="mb-0">
              <el-input v-model="form.compute_script" type="textarea" :rows="4" placeholder="Python脚本" />
            </el-form-item>
          </div>
        </template>

        <el-divider content-position="left">高级规则</el-divider>

        <el-row :gutter="24">
          <el-col :span="12">
            <el-form-item label="默认值">
              <el-input v-model="form.default_value" placeholder="默认值" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="正则校验">
              <el-input v-model="form.validation_regex" placeholder="正则表达式" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="24">
          <el-col :span="12">
            <el-form-item label="最小值">
              <el-input v-model="form.min_value" placeholder="最小值" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="最大值">
              <el-input v-model="form.max_value" placeholder="最大值" />
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>

      <template #footer>
        <div class="flex justify-end gap-3">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" @click="handleSubmit" :loading="submitting" class="bg-indigo-600 border-indigo-600 hover:bg-indigo-700">确定</el-button>
        </div>
      </template>
    </el-dialog>
  </PageContainer>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Delete, Search, Key, Operation, Link } from '@element-plus/icons-vue'
import api from '@/api'

const loading = ref(false)
const submitting = ref(false)
const attributes = ref([])
const models = ref([])
const searchName = ref('')
const dialogVisible = ref(false)
const isEdit = ref(false)
const formRef = ref(null)

const form = reactive({
  name: '',
  label: '',
  description: '',
  type: 'string',
  is_choice: false,
  is_list: false,
  is_unique: false,
  is_indexed: false,
  is_sortable: false,
  is_reference: false,
  reference_model_id: null,
  is_computed: false,
  compute_expr: '',
  compute_script: '',
  default_value: '',
  enum_values: [],
  validation_regex: '',
  min_value: '',
  max_value: '',
  choice_webhook: null,
  choice_script: '',
})

const rules = {
  name: [
    { required: true, message: '请输入属性名称', trigger: 'blur' },
    { pattern: /^[a-z][a-z0-9_]*$/, message: '属性名称必须以小写字母开头，只能包含小写字母、数字和下划线', trigger: 'blur' }
  ],
  label: [{ required: true, message: '请输入显示标签', trigger: 'blur' }],
  type: [{ required: true, message: '请选择数据类型', trigger: 'change' }],
}

const dialogTitle = computed(() => isEdit.value ? '编辑属性' : '新增属性')

const getTypeTagType = (type: string) => {
  const map: Record<string, string> = {
    string: '',
    number: 'success',
    enum: 'warning',
    boolean: 'info',
    date: 'danger',
    datetime: 'danger',
    json: '',
    uuid: 'info'
  }
  return map[type] || ''
}

const getModelName = (modelId: number) => {
  const model = models.value.find((m: any) => m.id === modelId)
  return model ? (model as any).name : modelId
}

const addEnumValue = () => {
  if (!form.enum_values) {
    (form.enum_values as any) = []
  }
  (form.enum_values as any[]).push({ value: '', label: '', color: '#409EFF' })
}

const resetForm = () => {
  Object.assign(form, {
    name: '',
    label: '',
    description: '',
    type: 'string',
    is_choice: false,
    is_list: false,
    is_unique: false,
    is_indexed: false,
    is_sortable: false,
    is_reference: false,
    reference_model_id: null,
    is_computed: false,
    compute_expr: '',
    compute_script: '',
    default_value: '',
    enum_values: [],
    validation_regex: '',
    min_value: '',
    max_value: '',
    choice_webhook: null,
    choice_script: '',
  })
}

const loadAttributes = async () => {
  loading.value = true
  try {
    const params: any = {}
    if (searchName.value) {
      params.name = searchName.value
    }
    const res = await api.get('/v2/global-attributes/', { params })
    attributes.value = res.data
  } catch (error) {
    ElMessage.error('加载属性列表失败')
  } finally {
    loading.value = false
  }
}

const loadModels = async () => {
  try {
    const res = await api.get('/v2/models/')
    models.value = res.data
  } catch (error) {
    console.error('加载模型列表失败', error)
  }
}

const handleAdd = () => {
  resetForm()
  isEdit.value = false
  dialogVisible.value = true
}

const handleEdit = (row: any) => {
  isEdit.value = true
  Object.assign(form, {
    ...row,
    enum_values: row.enum_values || [],
  })
  dialogVisible.value = true
}

const handleDelete = async (row: any) => {
  try {
    await ElMessageBox.confirm(`确定要删除属性 "${row.name}" 吗？`, '提示', {
      type: 'warning',
      confirmButtonText: '删除',
      cancelButtonText: '取消',
      confirmButtonClass: 'el-button--danger'
    })
    await api.delete(`/v2/global-attributes/${row.id}`)
    ElMessage.success('删除成功')
    loadAttributes()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(error.response?.data?.detail || '删除失败')
    }
  }
}

const handleSubmit = async () => {
  try {
    await (formRef.value as any).validate()
  } catch {
    return
  }

  submitting.value = true
  try {
    const data = { ...form }
    if (!data.is_choice) {
      (data as any).enum_values = null
    }
    if (!data.is_reference) {
      (data as any).reference_model_id = null
    }
    if (!data.is_computed) {
      data.compute_expr = null
      data.compute_script = null
    }

    if (isEdit.value) {
      await api.put(`/v2/global-attributes/${(form as any).id}`, data)
      ElMessage.success('更新成功')
    } else {
      await api.post('/v2/global-attributes/', data)
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    loadAttributes()
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '操作失败')
  } finally {
    submitting.value = false
  }
}

onMounted(() => {
  loadAttributes()
  loadModels()
})
</script>
