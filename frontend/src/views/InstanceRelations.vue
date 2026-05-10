<template>
  <div class="instance-relations-page">
    <el-card shadow="never" class="table-card">
      <template #header>
        <div class="card-header">
          <span>实例关系映射</span>
          <div class="header-actions">
            <el-select v-model="selectedRelationDef" placeholder="全部关系定义" style="width: 280px; margin-right: 12px;" clearable @change="handleRelationDefChange">
              <el-option
                v-for="rel in relationDefinitions"
                :key="rel.id"
                :label="`${rel.name} (${rel.source_model?.name} → ${rel.target_model?.name})`"
                :value="rel.id"
              />
            </el-select>
            <el-button type="primary" @click="handleAdd">
              <el-icon><Plus /></el-icon>
              新增��射
            </el-button>
          </div>
        </div>
      </template>

      <el-table :data="instanceRelations" v-loading="loading" stripe style="width: 100%">
        <el-table-column label="关系定义" width="180">
          <template #default="{ row }">
            <el-tag size="small" type="info">{{ row.relation_definition_name || '未知' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="源实例(子)" min-width="150">
          <template #default="{ row }">
            <div>
              <div>{{ row.source_instance?.name }}</div>
              <el-tag size="small" type="info">{{ row.source_instance?.model_name }}</el-tag>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="关系" width="80" align="center">
          <template #default>
            <el-icon><Right /></el-icon>
          </template>
        </el-table-column>
        <el-table-column label="目标实例(父)" min-width="150">
          <template #default="{ row }">
            <div>
              <div>{{ row.target_instance?.name }}</div>
              <el-tag size="small" type="success">{{ row.target_instance?.model_name }}</el-tag>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="attributes" label="关系属性" min-width="150">
          <template #default="{ row }">
            <template v-if="row.attributes && Object.keys(row.attributes).length > 0">
              <el-tag v-for="(value, key) in row.attributes" :key="key" size="small" style="margin-right: 4px;">
                {{ key }}: {{ value }}
              </el-tag>
            </template>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="160">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="{ row }">
            <el-button type="danger" link size="small" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-container" v-if="total > pageSize">
        <el-pagination
          v-model:current-page="currentPage"
          :page-size="pageSize"
          :total="total"
          layout="total, prev, pager, next"
          @current-change="handlePageChange"
        />
      </div>
    </el-card>

    <el-dialog v-model="dialogVisible" title="新增实例映射" width="600px" destroy-on-close>
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
        <el-form-item label="关系定义">
          <el-input :value="currentRelationDef?.name" disabled />
        </el-form-item>
        <el-alert
          v-if="currentRelationDef?.relation_type === 'connect'"
          title="双向关系：创建'A连接B'会自动创建'B连接A'，删除时也会同步删除反向关系"
          type="success"
          :closable="false"
          style="margin-bottom: 16px;"
        />
        <el-alert
          v-else
          :title="`映射说明: ${currentRelationDef?.source_model?.name || '源模型'} ${currentRelationDef?.relation_label || '→'} ${currentRelationDef?.target_model?.name || '目标模型'}`"
          type="info"
          :closable="false"
          style="margin-bottom: 16px;"
        />
        <el-form-item label="源实例(子)" prop="source_instance_id">
          <el-select 
            v-model="form.source_instance_id" 
            placeholder="选择源实例" 
            style="width: 100%"
            filterable
          >
            <el-option 
              v-for="instance in sourceInstances" 
              :key="instance.id" 
              :label="instance.name" 
              :value="instance.id"
            >
              <span>{{ instance.name }}</span>
              <el-tag size="small" style="margin-left: 8px;">{{ instance.code }}</el-tag>
            </el-option>
          </el-select>
        </el-form-item>
        <el-form-item label="目标实例(父)" prop="target_instance_id">
          <el-select 
            v-model="form.target_instance_id" 
            placeholder="选择目标实例" 
            style="width: 100%"
            filterable
          >
            <el-option 
              v-for="instance in targetInstances" 
              :key="instance.id" 
              :label="instance.name" 
              :value="instance.id"
            >
              <span>{{ instance.name }}</span>
              <el-tag size="small" style="margin-left: 8px;">{{ instance.code }}</el-tag>
            </el-option>
          </el-select>
        </el-form-item>
        <el-form-item label="关系属性">
          <div class="attribute-item" v-for="(value, key) in form.attributes" :key="key">
            <el-input v-model="form.attributes[key]" :placeholder="`属性值: ${key}`" style="width: 200px;" />
            <el-button type="danger" link @click="removeAttribute(key)">删除</el-button>
          </div>
          <div class="add-attribute">
            <el-input v-model="newAttrKey" placeholder="属性名" style="width: 120px;" />
            <el-input v-model="newAttrValue" placeholder="属性值" style="width: 120px; margin-left: 8px;" />
            <el-button type="primary" link @click="addAttribute">添加</el-button>
          </div>
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
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Right } from '@element-plus/icons-vue'
import api from '@/api'

const loading = ref(false)
const instanceRelations = ref([])
const relationDefinitions = ref([])
const sourceInstances = ref([])
const targetInstances = ref([])
const selectedRelationDef = ref(null)
const dialogVisible = ref(false)
const submitting = ref(false)
const formRef = ref(null)
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)
const newAttrKey = ref('')
const newAttrValue = ref('')

const currentRelationDef = computed(() => {
  return relationDefinitions.value.find(r => r.id === selectedRelationDef.value)
})

const form = reactive({
  source_instance_id: null,
  target_instance_id: null,
  attributes: {}
})

const rules = {
  source_instance_id: [{ required: true, message: '请选择源实例', trigger: 'change' }],
  target_instance_id: [{ required: true, message: '请选择目标实例', trigger: 'change' }]
}

const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const loadRelationDefinitions = async () => {
  try {
    const res = await api.get('/v2/relation-definitions/', { params: { status: 'active' } })
    relationDefinitions.value = res.data
  } catch (error) {
    console.error('加载关系定义失败:', error)
  }
}

const handleRelationDefChange = () => {
  currentPage.value = 1
  loadInstanceRelations()
}

const loadInstanceRelations = async () => {
  loading.value = true
  try {
    const params: any = {
      skip: (currentPage.value - 1) * pageSize.value,
      limit: pageSize.value
    }
    if (selectedRelationDef.value) {
      params.relation_definition_id = selectedRelationDef.value
    }
    const res = await api.get('/v2/instance-relations/', { params })
    instanceRelations.value = res.data
    total.value = res.data.length
  } catch (error) {
    console.error('加载实例关系失败:', error)
    ElMessage.error('加载实例关系失败')
  } finally {
    loading.value = false
  }
}

const loadSourceInstances = async () => {
  if (!currentRelationDef.value?.source_model_id) return
  
  try {
    const res = await api.get('/instances/', {
      params: {
        model_id: currentRelationDef.value.source_model_id,
        page: 1,
        page_size: 1000
      }
    })
    sourceInstances.value = res.data.items || []
  } catch (error) {
    console.error('加载源实例失败:', error)
  }
}

const loadTargetInstances = async () => {
  if (!currentRelationDef.value?.target_model_id) return

  try {
    const res = await api.get('/instances/', {
      params: {
        model_id: currentRelationDef.value.target_model_id,
        page: 1,
        page_size: 1000
      }
    })
    targetInstances.value = res.data.items || []
  } catch (error) {
    console.error('加载目标实例失败:', error)
  }
}

const handlePageChange = (page) => {
  currentPage.value = page
  loadInstanceRelations()
}

const handleAdd = async () => {
  if (!selectedRelationDef.value) {
    ElMessage.warning('请先选择一个关系定义')
    return
  }
  Object.assign(form, {
    source_instance_id: null,
    target_instance_id: null,
    attributes: {}
  })
  newAttrKey.value = ''
  newAttrValue.value = ''

  await Promise.all([loadSourceInstances(), loadTargetInstances()])
  dialogVisible.value = true
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm('确定要删除该映射关系吗？', '提示', { type: 'warning' })
    await api.delete(`/v2/instance-relations/${row.id}`)
    ElMessage.success('删除成功')
    loadInstanceRelations()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除失败:', error)
      ElMessage.error('删除失败')
    }
  }
}

const addAttribute = () => {
  if (newAttrKey.value && newAttrValue.value) {
    form.attributes[newAttrKey.value] = newAttrValue.value
    newAttrKey.value = ''
    newAttrValue.value = ''
  }
}

const removeAttribute = (key) => {
  delete form.attributes[key]
}

const handleSubmit = async () => {
  try {
    await formRef.value.validate()
    submitting.value = true
    
    await api.post('/v2/instance-relations/', {
      relation_definition_id: selectedRelationDef.value,
      ...form
    })
    
    ElMessage.success('创建成功')
    dialogVisible.value = false
    loadInstanceRelations()
  } catch (error) {
    console.error('保存失败:', error)
    ElMessage.error(error.response?.data?.detail || '保存失败')
  } finally {
    submitting.value = false
  }
}

onMounted(() => {
  loadRelationDefinitions()
  loadInstanceRelations()
})
</script>

<style scoped>
.instance-relations-page {
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

.header-actions {
  display: flex;
  align-items: center;
}

.pagination-container {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}

.attribute-item {
  display: flex;
  align-items: center;
  margin-bottom: 8px;
}

.add-attribute {
  display: flex;
  align-items: center;
  margin-top: 8px;
}
</style>
