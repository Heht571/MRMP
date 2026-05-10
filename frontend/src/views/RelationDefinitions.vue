<template>
  <div class="relation-definitions-page">
    <el-card shadow="never" class="table-card">
      <template #header>
        <div class="card-header">
          <span>关系定义管理</span>
          <el-button type="primary" @click="handleAdd">
            <el-icon><Plus /></el-icon>
            新增关系
          </el-button>
        </div>
      </template>

      <el-table :data="relations" v-loading="loading" stripe style="width: 100%">
        <el-table-column prop="name" label="关系名称" min-width="120" />
        <el-table-column prop="code" label="关系编码" width="120" />
        <el-table-column label="源模型" width="120">
           <template #default="{ row }">
             <el-tag size="small">{{ row.source_model?.name || '-' }}</el-tag>
           </template>
         </el-table-column>
         <el-table-column label="目标模型" width="120">
           <template #default="{ row }">
             <el-tag size="small" type="success">{{ row.target_model?.name || '-' }}</el-tag>
           </template>
         </el-table-column>
        <el-table-column prop="relation_label" label="关系标签" width="100">
          <template #default="{ row }">
            <span>{{ row.relation_label }}</span>
            <span v-if="row.inverse_label" class="inverse-label">({{ row.inverse_label }})</span>
          </template>
        </el-table-column>
        <el-table-column prop="mapping_type" label="映射类型" width="100">
          <template #default="{ row }">
            <el-tag size="small" type="info">{{ mappingTypeLabel(row.mapping_type) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="层级" width="60" align="center">
          <template #default="{ row }">
            <el-icon v-if="row.is_hierarchical" color="#67C23A"><Check /></el-icon>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="80" align="center">
          <template #default="{ row }">
            <el-tag :type="statusType(row.status)" size="small">
              {{ statusLabel(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="description" label="描述" min-width="150" show-overflow-tooltip />
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="handleEdit(row)">编辑</el-button>
            <el-button 
              v-if="row.status === 'active'" 
              type="warning" 
              link 
              size="small" 
              @click="handleDeactivate(row)"
            >停用</el-button>
            <el-button 
              v-else 
              type="success" 
              link 
              size="small" 
              @click="handleActivate(row)"
            >激活</el-button>
            <el-button type="danger" link size="small" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="700px" destroy-on-close>
      <el-form ref="formRef" :model="form" :rules="rules" label-width="120px">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="关系名称" prop="name">
              <el-input v-model="form.name" placeholder="如：机房包含机柜" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="关系编码" prop="code">
              <el-input v-model="form.code" placeholder="如：room_contains_cabinet" :disabled="!!currentRelation?.id" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="源模型" prop="source_model_id">
               <el-select v-model="form.source_model_id" placeholder="选择源模型" style="width: 100%" :disabled="!!currentRelation?.id">
                 <el-option 
                   v-for="model in models" 
                   :key="model.id" 
                   :label="model.name" 
                   :value="model.id"
                 />
               </el-select>
             </el-form-item>
           </el-col>
           <el-col :span="12">
             <el-form-item label="目标模型" prop="target_model_id">
               <el-select v-model="form.target_model_id" placeholder="选择目标模型" style="width: 100%" :disabled="!!currentRelation?.id">
                <el-option 
                  v-for="model in models" 
                  :key="model.id" 
                  :label="model.name" 
                  :value="model.id"
                />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="关系类型" prop="relation_type">
              <el-select v-model="form.relation_type" placeholder="选择关系类型" style="width: 100%">
                <el-option label="包含 (contain) - 层级关系，父→子" value="contain" />
                <el-option label="连接 (connect) - 对等关系，双向" value="connect" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="映射类型" prop="mapping_type">
              <el-select v-model="form.mapping_type" placeholder="选择映射类型" style="width: 100%">
                <el-option label="一对一" value="one_to_one" />
                <el-option label="一对多" value="one_to_many" />
                <el-option label="多对一" value="many_to_one" />
                <el-option label="多对多" value="many_to_many" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="最小基数">
              <el-input-number v-model="form.min_cardinality" :min="0" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="最大基数">
              <el-input-number v-model="form.max_cardinality" :min="-1" style="width: 100%" />
              <div class="form-tip">-1 表示无限制</div>
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="描述">
          <el-input v-model="form.description" type="textarea" :rows="2" placeholder="关系描述" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Check } from '@element-plus/icons-vue'
import api from '@/api'

const loading = ref(false)
const relations = ref<any[]>([])
const models = ref<any[]>([])
const dialogVisible = ref(false)
const submitting = ref(false)
const currentRelation = ref<any>({})
const formRef = ref(null)

const dialogTitle = computed(() => currentRelation.value?.id ? '编辑关系' : '新增关系')

const form = reactive<any>({
  name: '',
  code: '',
  source_model_id: null,
  target_model_id: null,
  relation_type: 'contain',
  mapping_type: 'one_to_many',
  min_cardinality: 0,
  max_cardinality: -1,
  description: ''
})

const rules = {
  name: [{ required: true, message: '请输入关系名称', trigger: 'blur' }],
  code: [{ required: true, message: '请输入关系编码', trigger: 'blur' }, { pattern: /^[a-z_]+$/, message: '只能包含小写字母和下划线', trigger: 'blur' }],
  source_model_id: [{ required: true, message: '请选择源模型', trigger: 'change' }],
  target_model_id: [{ required: true, message: '请选择目标模型', trigger: 'change' }],
  relation_type: [{ required: true, message: '请选择关系类型', trigger: 'change' }],
  mapping_type: [{ required: true, message: '请选择映射类型', trigger: 'change' }]
}

const mappingTypeLabel = (type) => {
  const map = {
    'one_to_one': '一对一',
    'one_to_many': '一对多',
    'many_to_one': '多对一',
    'many_to_many': '多对多'
  }
  return map[type] || type
}

const statusLabel = (status) => {
  const map = {
    'draft': '草稿',
    'active': '启用',
    'inactive': '停用'
  }
  return map[status] || status
}

const statusType = (status) => {
  const map = {
    'draft': 'info',
    'active': 'success',
    'inactive': 'warning'
  }
  return map[status] || 'info'
}

const loadRelations = async () => {
  loading.value = true
  try {
    const res = await api.get('/v2/relation-definitions/')
    relations.value = res.data
  } catch (error) {
    console.error('加载关系列表失败:', error)
    ElMessage.error('加载关系列表失败')
  } finally {
    loading.value = false
  }
}

const loadModels = async () => {
  try {
    const res = await api.get('/v2/models/')
    models.value = res.data
  } catch (error) {
    console.error('加载模型列表失败:', error)
  }
}

const handleAdd = () => {
  currentRelation.value = {}
  Object.assign(form, {
    name: '',
    code: '',
    source_model_id: null,
    target_model_id: null,
    relation_type: 'contain',
    mapping_type: 'one_to_many',
    min_cardinality: 0,
    max_cardinality: -1,
    description: ''
  })
  dialogVisible.value = true
}

const handleEdit = (row) => {
  currentRelation.value = row
  Object.assign(form, {
    name: row.name,
    code: row.code,
    source_model_id: row.source_model_id,
    target_model_id: row.target_model_id,
    relation_type: row.relation_type || 'contain',
    mapping_type: row.mapping_type,
    min_cardinality: row.min_cardinality,
    max_cardinality: row.max_cardinality,
    description: row.description || ''
  })
  dialogVisible.value = true
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm('确定要删除该关系定义吗？相关的实例映射也会被删除。', '提示', { type: 'warning' })
    await api.delete(`/v2/relation-definitions/${row.id}`)
    ElMessage.success('删除成功')
    loadRelations()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除失败:', error)
      ElMessage.error('删除失败')
    }
  }
}

const handleActivate = async (row) => {
  try {
    await api.post(`/v2/relation-definitions/${row.id}/activate`)
    ElMessage.success('激活成功')
    loadRelations()
  } catch (error) {
    console.error('激活失败:', error)
    ElMessage.error('激活失败')
  }
}

const handleDeactivate = async (row) => {
  try {
    await api.post(`/v2/relation-definitions/${row.id}/deactivate`)
    ElMessage.success('停用成功')
    loadRelations()
  } catch (error) {
    console.error('停用失败:', error)
    ElMessage.error('停用失败')
  }
}

const handleSubmit = async () => {
  try {
    await formRef.value.validate()
    submitting.value = true
    
    if (currentRelation.value?.id) {
      await api.put(`/v2/relation-definitions/${currentRelation.value.id}`, form)
      ElMessage.success('更新成功')
    } else {
      await api.post('/v2/relation-definitions/', form)
      ElMessage.success('创建成功')
    }
    
    dialogVisible.value = false
    loadRelations()
  } catch (error) {
    console.error('保存失败:', error)
    ElMessage.error(error.response?.data?.detail || '保存失败')
  } finally {
    submitting.value = false
  }
}

onMounted(() => {
  loadRelations()
  loadModels()
})
</script>

<style scoped>
.relation-definitions-page {
  padding: 20px;
}

.table-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.inverse-label {
  color: #909399;
  font-size: 12px;
  margin-left: 4px;
}

.form-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}
</style>
