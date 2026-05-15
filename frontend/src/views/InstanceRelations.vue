<template>
  <div class="instance-relations-page">
    <el-card shadow="never" class="table-card">
      <template #header>
        <div class="card-header">
          <span>实例关系映射</span>
          <div class="header-actions">
            <el-button type="primary" @click="showAddDialog = true">
              <el-icon><Plus /></el-icon>
              新增映射
            </el-button>
          </div>
        </div>
      </template>

      <!-- 成对显示的实例关系 -->
      <div v-if="pairedInstanceRelations.length > 0" class="relation-pairs">
        <div v-for="pair in pairedInstanceRelations" :key="pair.id" class="relation-pair-card">
          <div class="pair-header">
            <el-tag :type="pair.relation_type === 'contain' ? 'primary' : 'warning'" size="small">
              {{ pair.relation_type === 'contain' ? '层级关系' : '连接关系' }}
            </el-tag>
            <span class="pair-relation-name">{{ pair.relation_def_name }}</span>
          </div>
          <div class="pair-content">
            <!-- 正向关系 -->
            <div class="relation-direction">
              <el-tag size="small" type="primary">{{ pair.source_name }}</el-tag>
              <span class="arrow">→</span>
              <span class="label">{{ pair.relation_label }}</span>
              <span class="arrow">→</span>
              <el-tag size="small" type="success">{{ pair.target_name }}</el-tag>
            </div>
            <!-- 反向关系 -->
            <div class="relation-direction inverse" v-if="pair.inverse_source_name">
              <el-tag size="small" type="success">{{ pair.inverse_source_name }}</el-tag>
              <span class="arrow">←</span>
              <span class="label">{{ pair.inverse_label }}</span>
              <span class="arrow">←</span>
              <el-tag size="small" type="primary">{{ pair.inverse_target_name }}</el-tag>
            </div>
          </div>
          <div class="pair-footer">
            <span class="pair-time">{{ formatDate(pair.created_at) }}</span>
            <el-button type="danger" link size="small" @click="handleDeletePair(pair)">删除</el-button>
          </div>
        </div>
      </div>

      <el-empty v-if="!loading && instanceRelations.length === 0" description="暂无实例关系映射" />
    </el-card>

    <!-- 新增映射对话框 -->
    <el-dialog v-model="showAddDialog" title="新增实例映射" width="650px" destroy-on-close>
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
        <el-form-item label="关系定义" prop="relation_definition_id">
          <el-select v-model="form.relation_definition_id" placeholder="选择关系定义" style="width: 100%" @change="handleRelationChange">
            <el-option
              v-for="rel in pairedRelationDefs"
              :key="rel.id"
              :label="`${rel.source_model?.name} ${rel.relation_label} ${rel.target_model?.name}`"
              :value="rel.id"
            />
          </el-select>
        </el-form-item>

        <template v-if="selectedRelDef">
          <el-alert
            :title="`${selectedRelDef.source_model?.name} ${selectedRelDef.relation_label} ${selectedRelDef.target_model?.name}`"
            type="info"
            :closable="false"
            style="margin-bottom: 16px;"
          />
          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item label="源实例" prop="source_instance_id">
                <el-select v-model="form.source_instance_id" placeholder="选择源实例" style="width: 100%" filterable clearable>
                  <el-option v-for="inst in sourceInstances" :key="inst.id" :label="inst.name" :value="inst.id">
                    <span>{{ inst.name }}</span>
                    <el-tag size="small" style="margin-left: 8px;">{{ inst.code }}</el-tag>
                  </el-option>
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="目标实例" prop="target_instance_id">
                <el-select v-model="form.target_instance_id" placeholder="选择目标实例" style="width: 100%" filterable clearable>
                  <el-option v-for="inst in targetInstances" :key="inst.id" :label="inst.name" :value="inst.id">
                    <span>{{ inst.name }}</span>
                    <el-tag size="small" style="margin-left: 8px;">{{ inst.code }}</el-tag>
                  </el-option>
                </el-select>
              </el-form-item>
            </el-col>
          </el-row>
          <el-alert v-if="selectedRelDef?.relation_type === 'connect'" title="连接关系：系统会自动创建双向映射" type="success" :closable="false" />
        </template>
      </el-form>
      <template #footer>
        <el-button @click="showAddDialog = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">保存</el-button>
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
const instanceRelations = ref<any[]>([])
const relationDefinitions = ref<any[]>([])
const sourceInstances = ref<any[]>([])
const targetInstances = ref<any[]>([])
const showAddDialog = ref(false)
const formRef = ref(null)

const form = reactive({
  relation_definition_id: null as string | null,
  source_instance_id: null,
  target_instance_id: null
})

const rules = {
  relation_definition_id: [{ required: true, message: '请选择关系定义', trigger: 'change' }],
  source_instance_id: [{ required: true, message: '请选择源实例', trigger: 'change' }],
  target_instance_id: [{ required: true, message: '请选择目标实例', trigger: 'change' }]
}

// 只显示正向关系定义
const pairedRelationDefs = computed(() => {
  return relationDefinitions.value.filter(r => !r.code.endsWith('__inverse') && r.status === 'active')
})

const selectedRelDef = computed(() => {
  return relationDefinitions.value.find(r => r.id === form.relation_definition_id)
})

// 将实例关系成对显示
const pairedInstanceRelations = computed(() => {
  const processed = new Set<string>()
  const pairs: any[] = []

  for (const ir of instanceRelations.value) {
    if (processed.has(ir.id)) continue

    const rel = relationDefinitions.value.find(r => r.id === ir.relation_definition_id)
    if (!rel || rel.code.endsWith('__inverse')) continue

    // 构建正向关系
    const pair: any = {
      id: ir.id,
      relation_def_id: rel.id,
      relation_def_name: rel.name,
      relation_type: rel.relation_type,
      relation_label: rel.relation_label,
      inverse_label: rel.inverse_label,
      source_name: ir.source_instance?.name,
      target_name: ir.target_instance?.name,
      source_id: ir.source_instance_id,
      target_id: ir.target_instance_id,
      created_at: ir.created_at,
      inverse_source_name: null,
      inverse_target_name: null,
      inverse_id: null
    }

    // 查找对应的反向关系
    // 反向关系的特征：target_instance_id = 当前正向的 source_instance_id
    // 且 relation_definition_id = 正向关系定义ID + __inverse
    const inverseRelCode = rel.code + '__inverse'
    const inverseRel = relationDefinitions.value.find(r => r.code === inverseRelCode)

    if (inverseRel) {
      const inverseIr = instanceRelations.value.find(i =>
        i.relation_definition_id === inverseRel.id &&
        i.source_instance_id === ir.target_instance_id &&
        i.target_instance_id === ir.source_instance_id
      )

      if (inverseIr) {
        pair.inverse_source_name = inverseIr.source_instance?.name
        pair.inverse_target_name = inverseIr.target_instance?.name
        pair.inverse_id = inverseIr.id
        processed.add(inverseIr.id)
      }
    }

    processed.add(ir.id)
    pairs.push(pair)
  }

  return pairs
})

const formatDate = (dateStr: string) => {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
}

const loadRelationDefinitions = async () => {
  try {
    const res = await api.get('/v2/relation-definitions/')
    relationDefinitions.value = res.data || []
  } catch (error) {
    console.error('加载关系定义失败:', error)
  }
}

const loadInstanceRelations = async () => {
  loading.value = true
  try {
    const res = await api.get('/v2/instance-relations/', { params: { limit: 1000 } })
    instanceRelations.value = res.data || []
  } catch (error) {
    console.error('加载实例关系失败:', error)
    ElMessage.error('加载实例关系失败')
  } finally {
    loading.value = false
  }
}

const handleRelationChange = async () => {
  form.source_instance_id = null
  form.target_instance_id = null
  sourceInstances.value = []
  targetInstances.value = []

  if (!selectedRelDef.value) return

  try {
    const [srcRes, tgtRes] = await Promise.all([
      api.get('/v1/instances/', { params: { model_id: selectedRelDef.value.source_model_id, page: 1, page_size: 100 } }),
      api.get('/v1/instances/', { params: { model_id: selectedRelDef.value.target_model_id, page: 1, page_size: 100 } })
    ])
    sourceInstances.value = srcRes.data.items || []
    targetInstances.value = tgtRes.data.items || []
  } catch (error) {
    console.error('加载实例列表失败:', error)
  }
}

const handleSubmit = async () => {
  try {
    await (formRef.value as any).validate()
  } catch { return }

  if (form.source_instance_id === form.target_instance_id) {
    ElMessage.warning('源实例和目标实例不能相同')
    return
  }

  submitting.value = true
  try {
    await api.post('/v2/instance-relations/', {
      relation_definition_id: form.relation_definition_id,
      source_instance_id: form.source_instance_id,
      target_instance_id: form.target_instance_id
    })
    ElMessage.success('创建成功')
    showAddDialog.value = false
    form.relation_definition_id = null
    form.source_instance_id = null
    form.target_instance_id = null
    loadInstanceRelations()
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '创建失败')
  } finally {
    submitting.value = false
  }
}

const handleDeletePair = async (pair: any) => {
  try {
    await ElMessageBox.confirm('确定要删除该映射关系吗？删除正向关系会同时删除对应的反向关系', '提示', { type: 'warning' })
    // 删除正向关系
    await api.delete(`/v2/instance-relations/${pair.id}`)
    // 如果有反向关系，也删除
    if (pair.inverse_id) {
      await api.delete(`/v2/instance-relations/${pair.inverse_id}`)
    }
    ElMessage.success('删除成功')
    loadInstanceRelations()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(error.response?.data?.detail || '删除失败')
    }
  }
}

// 保留原来的handleDelete以兼容
const handleDelete = handleDeletePair

onMounted(() => {
  loadRelationDefinitions()
  loadInstanceRelations()
})
</script>

<style scoped>
.relation-pairs {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(380px, 1fr));
  gap: 16px;
}

.relation-pair-card {
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  overflow: hidden;
  background: #fafafa;
}

.pair-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  background: white;
  border-bottom: 1px solid #e4e7ed;
}

.pair-relation-name {
  font-weight: 600;
  color: #303133;
}

.pair-content {
  padding: 16px;
  background: white;
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
  padding: 8px 16px;
  background: #f5f7fa;
  border-top: 1px solid #e4e7ed;
}

.pair-time {
  color: #909399;
  font-size: 12px;
}
</style>