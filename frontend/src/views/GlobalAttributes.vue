<template>
  <PageContainer title="全局属性池" description="管理系统中通用的属性定义，可被多个模型引用。">
    <template #extra>
      <el-input
        v-model="searchName"
        placeholder="搜索属性名称"
        class="keyword-input"
        clearable
        @clear="loadAttributes"
        @keyup.enter="loadAttributes"
      >
        <template #prefix>
          <el-icon><Search /></el-icon>
        </template>
      </el-input>
      <el-button type="primary" @click="handleAdd">
        <el-icon><Plus /></el-icon>
        新增属性
      </el-button>
    </template>

    <div class="table-container">
    <el-table
      :data="attributes"
      v-loading="loading"
      stripe
      style="width: 100%"
    >
      <el-table-column prop="name" label="属性名称" width="180">
        <template #default="{ row }">
          <span style="font-family: monospace; color: var(--color-accent); background: #eff6ff; padding: 4px 8px; border-radius: var(--radius-sm); font-size: 12px;">{{ row.name }}</span>
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
          <div style="display: flex; flex-wrap: wrap; gap: 4px;">
            <el-tag v-if="row.type === 'timeseries'" size="small" type="warning" effect="plain">时序</el-tag>
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
          <span v-if="row.is_reference && row.reference_model_id" style="color: var(--color-text-secondary); display: flex; align-items: center; gap: 4px;">
            <el-icon><Link /></el-icon>
            {{ getModelName(row.reference_model_id) }}
          </span>
          <span v-else style="color: var(--color-text-tertiary);">-</span>
        </template>
      </el-table-column>
      <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip>
        <template #default="{ row }">
          <span style="color: var(--color-text-secondary);">{{ row.description || '-' }}</span>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="150" fixed="right">
        <template #default="{ row }">
          <div style="display: flex; align-items: center; gap: var(--space-sm);">
            <el-button type="primary" link size="small" @click="handleEdit(row)">编辑</el-button>
            <el-button type="danger" link size="small" @click="handleDelete(row)">删除</el-button>
          </div>
        </template>
      </el-table-column>
    </el-table>
    </div>

    <!-- Dialog -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="800px"
      destroy-on-close
    >
      <el-form ref="formRef" :model="form" :rules="rules" label-width="120px" style="padding: var(--space-md) 0;">
        <el-row :gutter="24">
          <el-col :span="12">
            <el-form-item label="属性名称" prop="name">
              <el-input v-model="form.name" placeholder="英文键，如：ip_address" :disabled="isEdit">
                <template #prefix><el-icon style="color: var(--color-text-tertiary);"><Key /></el-icon></template>
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
              <el-select v-model="form.type" placeholder="选择数据类型" style="width: 100%;">
                <el-option label="字符串 (String)" value="string" />
                <el-option label="数字 (Number)" value="number" />
                <el-option label="枚举 (Enum)" value="enum" />
                <el-option label="布尔 (Boolean)" value="boolean" />
                <el-option label="日期 (Date)" value="date" />
                <el-option label="日期时间 (Datetime)" value="datetime" />
                <el-option label="JSON" value="json" />
                <el-option label="UUID" value="uuid" />
                <el-option label="时间序列 (Timeseries)" value="timeseries" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="描述">
              <el-input v-model="form.description" placeholder="属性用途描述" />
            </el-form-item>
          </el-col>
        </el-row>

        <div class="form-section">
          <div class="section-title" style="display: flex; align-items: center;">
            <el-icon><Operation /></el-icon> 属性特性
          </div>
          <el-row :gutter="24">
            <el-col :span="6"><el-form-item label="枚举类型" style="margin-bottom: 0;"><el-switch v-model="form.is_choice" /></el-form-item></el-col>
            <el-col :span="6"><el-form-item label="列表类型" style="margin-bottom: 0;"><el-switch v-model="form.is_list" /></el-form-item></el-col>
            <el-col :span="6"><el-form-item label="唯一性" style="margin-bottom: 0;"><el-switch v-model="form.is_unique" /></el-form-item></el-col>
            <el-col :span="6"><el-form-item label="可索引" style="margin-bottom: 0;"><el-switch v-model="form.is_indexed" /></el-form-item></el-col>
          </el-row>
          <el-row :gutter="24" style="margin-top: var(--space-sm);">
            <el-col :span="6"><el-form-item label="可排序" style="margin-bottom: 0;"><el-switch v-model="form.is_sortable" /></el-form-item></el-col>
            <el-col :span="6"><el-form-item label="引用属性" style="margin-bottom: 0;"><el-switch v-model="form.is_reference" /></el-form-item></el-col>
            <el-col :span="6"><el-form-item label="计算属性" style="margin-bottom: 0;"><el-switch v-model="form.is_computed" /></el-form-item></el-col>
          </el-row>
        </div>

        <template v-if="form.is_reference">
          <div style="background: #fffbeb; padding: var(--space-md); border-radius: var(--radius-lg); border: 1px solid #fde68a; margin-bottom: var(--space-lg);">
             <div style="font-size: 14px; font-weight: 600; color: #b45309; margin-bottom: var(--space-sm);">引用配置</div>
             <el-form-item label="引用模型" prop="reference_model_id" style="margin-bottom: 0;">
              <el-select v-model="form.reference_model_id" placeholder="选择引用模型" style="width: 100%;">
                <el-option v-for="model in models" :key="model.id" :label="model.name" :value="model.id" />
              </el-select>
            </el-form-item>
          </div>
        </template>

        <template v-if="form.is_choice">
          <div style="background: #eff6ff; padding: var(--space-md); border-radius: var(--radius-lg); border: 1px solid #bfdbfe; margin-bottom: var(--space-lg);">
            <div style="font-size: 14px; font-weight: 600; color: #1d4ed8; margin-bottom: var(--space-sm);">枚举值配置</div>
            <div style="display: flex; flex-direction: column; gap: var(--space-sm);">
              <div v-for="(item, index) in form.enum_values" :key="index" style="display: flex; align-items: center; gap: var(--space-sm);">
                <el-input v-model="item.value" placeholder="值 (Value)" style="width: 120px;" />
                <el-input v-model="item.label" placeholder="标签 (Label)" style="width: 120px;" />
                <el-color-picker v-model="item.color" show-alpha />
                <el-button type="danger" circle size="small" @click="form.enum_values.splice(index, 1)">
                  <el-icon><Delete /></el-icon>
                </el-button>
              </div>
              <el-button type="primary" link @click="addEnumValue" size="small">
                <el-icon><Plus /></el-icon> 添加枚举值
              </el-button>
            </div>
          </div>
        </template>

        <template v-if="form.is_computed">
          <div style="background: #f0fdf4; padding: var(--space-md); border-radius: var(--radius-lg); border: 1px solid #bbf7d0; margin-bottom: var(--space-lg);">
            <div style="font-size: 14px; font-weight: 600; color: #15803d; margin-bottom: var(--space-sm);">计算配置</div>
            <el-form-item label="计算表达式">
              <el-input v-model="form.compute_expr" type="textarea" :rows="2" placeholder="如: ${attr1} + ${attr2}" />
            </el-form-item>
            <el-form-item label="计算脚本" style="margin-bottom: 0;">
              <el-input v-model="form.compute_script" type="textarea" :rows="4" placeholder="Python脚本" />
            </el-form-item>
          </div>
        </template>

        <template v-if="form.type === 'timeseries'">
          <div style="background: #fdf4ff; padding: var(--space-md); border-radius: var(--radius-lg); border: 1px solid #f0abfc; margin-bottom: var(--space-lg);">
            <div style="font-size: 14px; font-weight: 600; color: #a21caf; margin-bottom: var(--space-sm);">时序数据配置</div>
            <el-row :gutter="24">
              <el-col :span="12">
                <el-form-item label="时序单位" style="margin-bottom: 0;">
                  <el-input v-model="form.timeseries_unit" placeholder="如: cpu, memory, disk, network" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="采样间隔(秒)" style="margin-bottom: 0;">
                  <el-input-number v-model="form.timeseries_interval" :min="1" :step="10" style="width: 100%;" />
                </el-form-item>
              </el-col>
            </el-row>
            <el-row :gutter="24" style="margin-top: var(--space-sm);">
              <el-col :span="12">
                <el-form-item label="保留天数" style="margin-bottom: 0;">
                  <el-input-number v-model="form.timeseries_retention" :min="1" :max="365" style="width: 100%;" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="默认聚合" style="margin-bottom: 0;">
                  <el-select v-model="form.timeseries_aggregation" style="width: 100%;">
                    <el-option label="平均值 (avg)" value="avg" />
                    <el-option label="最小值 (min)" value="min" />
                    <el-option label="最大值 (max)" value="max" />
                    <el-option label="求和 (sum)" value="sum" />
                    <el-option label="最新值 (last)" value="last" />
                  </el-select>
                </el-form-item>
              </el-col>
            </el-row>
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
        <div style="display: flex; justify-content: flex-end; gap: var(--space-sm);">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" @click="handleSubmit" :loading="submitting">确定</el-button>
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
  timeseries_unit: '',
  timeseries_interval: 60,
  timeseries_retention: 30,
  timeseries_aggregation: 'avg',
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
    uuid: 'info',
    timeseries: 'warning'
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
    timeseries_unit: '',
    timeseries_interval: 60,
    timeseries_retention: 30,
    timeseries_aggregation: 'avg',
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
