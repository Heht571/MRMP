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

      <div v-if="pairedRelations.length > 0" class="relation-pairs">
        <div v-for="pair in pairedRelations" :key="pair.id" class="relation-pair-card">
          <div class="pair-header">
            <el-tag :type="pair.relation_type === 'contain' ? 'primary' : 'warning'" size="small">
              {{ pair.relation_type === 'contain' ? '层级关系' : '连接关系' }}
            </el-tag>
            <el-tag size="small" type="info">{{ mappingTypeLabel(pair.mapping_type) }}</el-tag>
          </div>
          <div class="pair-content">
            <div class="relation-direction">
              <el-tag size="small" type="primary">{{ pair.source_model?.name }}</el-tag>
              <span class="arrow">→</span>
              <span class="label">{{ pair.relation_label }}</span>
              <span class="arrow">→</span>
              <el-tag size="small" type="success">{{ pair.target_model?.name }}</el-tag>
            </div>
            <div class="relation-direction inverse">
              <el-tag size="small" type="success">{{ pair.target_model?.name }}</el-tag>
              <span class="arrow">←</span>
              <span class="label">{{ pair.inverse_label }}</span>
              <span class="arrow">←</span>
              <el-tag size="small" type="primary">{{ pair.source_model?.name }}</el-tag>
            </div>
          </div>
          <div class="pair-footer">
            <span class="pair-name">{{ pair.name.replace('（反向）', '') }}</span>
            <div class="pair-actions">
              <el-button type="primary" link size="small" @click="handleEdit(pair)">编辑</el-button>
              <el-button type="danger" link size="small" @click="handleDeletePair(pair)">删除</el-button>
            </div>
          </div>
        </div>
      </div>

      <el-empty v-if="!loading && relations.length === 0" description="暂无关系定义" />
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
                <el-option v-for="model in models" :key="model.id" :label="model.name" :value="model.id" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="目标模型" prop="target_model_id">
              <el-select v-model="form.target_model_id" placeholder="选择目标模型" style="width: 100%" :disabled="!!currentRelation?.id">
                <el-option v-for="model in models" :key="model.id" :label="model.name" :value="model.id" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="关系类型" prop="relation_type">
              <el-select v-model="form.relation_type" placeholder="选择关系类型" style="width: 100%">
                <el-option label="包含 (contain)" value="contain" />
                <el-option label="连接 (connect)" value="connect" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="映射类型" prop="mapping_type">
              <el-select v-model="form.mapping_type" placeholder="选择映射类型" style="width: 100%">
                <el-option label="一对一 (one_to_one)" value="one_to_one" />
                <el-option label="一对多 (one_to_many)" value="one_to_many" />
                <el-option label="多对一 (many_to_one)" value="many_to_one" />
                <el-option label="多对多 (many_to_many)" value="many_to_many" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="描述">
          <el-input v-model="form.description" type="textarea" :rows="2" placeholder="关系描述" />
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
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import api from '@/api'

const loading = ref(false)
const submitting = ref(false)
const relations = ref([])
const models = ref([])
const dialogVisible = ref(false)
const isEdit = ref(false)
const currentRelation = ref(null)
const formRef = ref(null)

const form = reactive({
  name: '',
  code: '',
  source_model_id: null,
  target_model_id: null,
  relation_type: 'contain',
  mapping_type: 'one_to_many',
  description: ''
})

const rules = {
  name: [{ required: true, message: '请输入关系名称', trigger: 'blur' }],
  code: [{ required: true, message: '请输入关系编码', trigger: 'blur' }],
  source_model_id: [{ required: true, message: '请选择源模型', trigger: 'change' }],
  target_model_id: [{ required: true, message: '请选择目标模型', trigger: 'change' }],
  relation_type: [{ required: true, message: '请选择关系类型', trigger: 'change' }],
  mapping_type: [{ required: true, message: '请选择映射类型', trigger: 'change' }]
}

const dialogTitle = computed(() => isEdit.value ? '编辑关系' : '新增关系')

const pairedRelations = computed(() => {
  const processed = new Set()
  const pairs = []

  for (const rel of relations.value) {
    if (processed.has(rel.id)) continue
    if (rel.code.endsWith('__inverse')) continue

    const inverseCode = rel.code + '__inverse'
    const inverse = relations.value.find(r => r.code === inverseCode)

    if (inverse) {
      pairs.push({ ...rel, inverse_relation: inverse })
      processed.add(rel.id)
      processed.add(inverse.id)
    } else {
      pairs.push(rel)
      processed.add(rel.id)
    }
  }
  return pairs
})

const mappingTypeLabel = (type: string) => {
  const map: Record<string, string> = {
    one_to_one: '1:1',
    one_to_many: '1:N',
    many_to_one: 'N:1',
    many_to_many: 'N:N'
  }
  return map[type] || type
}

const statusLabel = (status: string) => {
  const map: Record<string, string> = { draft: '草稿', active: '启用', inactive: '停用' }
  return map[status] || status
}

const loadRelations = async () => {
  loading.value = true
  try {
    const res = await api.get('/v2/relation-definitions/')
    relations.value = res.data || []
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
    models.value = res.data || []
  } catch (error) {
    console.error('加载模型列表失败:', error)
  }
}

const handleAdd = () => {
  isEdit.value = false
  currentRelation.value = null
  Object.assign(form, { name: '', code: '', source_model_id: null, target_model_id: null, relation_type: 'contain', mapping_type: 'one_to_many', description: '' })
  dialogVisible.value = true
}

const handleEdit = (row: any) => {
  isEdit.value = true
  currentRelation.value = row
  Object.assign(form, { name: row.name, code: row.code, source_model_id: row.source_model_id, target_model_id: row.target_model_id, relation_type: row.relation_type, mapping_type: row.mapping_type, description: row.description || '' })
  dialogVisible.value = true
}

const handleSubmit = async () => {
  try {
    await (formRef.value as any).validate()
  } catch { return }

  submitting.value = true
  try {
    if (isEdit.value) {
      await api.put(`/v2/relation-definitions/${currentRelation.value.id}`, form)
      ElMessage.success('更新成功')
    } else {
      await api.post('/v2/relation-definitions/', form)
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    loadRelations()
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '操作失败')
  } finally {
    submitting.value = false
  }
}

const handleDeletePair = async (pair: any) => {
  try {
    await ElMessageBox.confirm('确定要删除该关系定义吗？', '提示', { type: 'warning' })
    await api.delete(`/v2/relation-definitions/${pair.id}`)
    ElMessage.success('删除成功')
    loadRelations()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(error.response?.data?.detail || '删除失败')
    }
  }
}

onMounted(() => {
  loadRelations()
  loadModels()
})
</script>

<style scoped>
.relation-pairs {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 16px;
  margin-bottom: 16px;
}

.relation-pair-card {
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  padding: 16px;
  background: #fafafa;
}

.pair-header {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
}

.pair-content {
  background: white;
  border-radius: 6px;
  padding: 12px;
  margin-bottom: 12px;
}

.relation-direction {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 8px;
}

.relation-direction.inverse {
  border-top: 1px dashed #e4e7ed;
  margin-top: 8px;
  padding-top: 8px;
}

.arrow {
  color: #909399;
  font-weight: bold;
}

.label {
  color: #606266;
  font-weight: 500;
}

.pair-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.pair-name {
  font-weight: 600;
  color: #303133;
}
</style>