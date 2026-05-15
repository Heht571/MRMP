<template>
  <div class="hierarchy-view-page">
    <el-card shadow="hover" class="main-card">
      <template #header>
        <div class="card-header">
          <div class="header-left">
            <el-icon class="header-icon"><Share /></el-icon>
            <span class="header-title">资源层级视图</span>
          </div>
          <div class="header-actions">
            <el-button-group>
              <el-button size="small" @click="expandAll" :disabled="forest.length === 0">
                <el-icon><Plus /></el-icon>
                展开全部
              </el-button>
              <el-button size="small" @click="collapseAll" :disabled="forest.length === 0">
                <el-icon><Minus /></el-icon>
                收起全部
              </el-button>
            </el-button-group>
            <el-dropdown @command="handleExportCommand" :disabled="forest.length === 0">
              <el-button size="small">
                <el-icon><Download /></el-icon>
                导出
                <el-icon class="el-icon--right"><ArrowDown /></el-icon>
              </el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="csv">导出为 CSV</el-dropdown-item>
                  <el-dropdown-item command="json">导出为 JSON</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
            <el-button size="small" @click="loadForest" :loading="loading">
              <el-icon><Refresh /></el-icon>
              刷新
            </el-button>
          </div>
        </div>
      </template>

      <!-- Model Selector -->
      <div class="model-selector-section">
        <div class="selector-wrapper">
          <span class="selector-label">选择资源类型：</span>
          <el-select
            v-model="selectedModelId"
            placeholder="请选择资源类型"
            filterable
            clearable
            class="model-select"
            @change="handleModelChange"
          >
            <el-option
              v-for="model in models"
              :key="model.id"
              :label="model.name"
              :value="model.id"
            >
              <div class="model-option">
                <div class="model-option-icon" :style="{ backgroundColor: model.color || '#6366f1' }">
                  {{ model.name[0] }}
                </div>
                <span class="model-option-name">{{ model.name }}</span>
                <span class="model-option-code">{{ model.code }}</span>
              </div>
            </el-option>
          </el-select>
        </div>
      </div>

      <div v-if="loading" class="loading-state">
        <el-skeleton :rows="8" animated />
      </div>

      <div v-else-if="forest.length === 0 && orphanNodes.length === 0" class="empty-state">
        <el-empty description="暂无层级数据">
          <template #image>
            <el-icon :size="80" color="#c0c4cc"><FolderOpened /></el-icon>
          </template>
        </el-empty>
      </div>

      <div v-else class="content-wrapper">
        <div class="forest-section" v-if="forest.length > 0">
          <div v-for="(tree, index) in forest" :key="tree.model_id" class="tree-block">
            <div class="tree-block-header" @click="toggleTree(index)">
              <div class="block-left">
                <div class="model-badge" :style="{ backgroundColor: tree.model_color || '#409EFF' }">
                  <el-icon><component :is="getModelIcon(tree.model_icon)" /></el-icon>
                </div>
                <div class="block-info">
                  <span class="block-title">{{ tree.model_name }}</span>
                  <span class="block-desc">{{ tree.nodes.length }} 个根节点</span>
                </div>
              </div>
              <el-icon class="expand-icon" :class="{ 'is-expanded': expandedTrees[index] }">
                <ArrowDown />
              </el-icon>
            </div>
            
            <el-collapse-transition>
              <div v-show="expandedTrees[index]" class="tree-block-content">
                <el-tree
                  :ref="el => setTreeRef(index, el)"
                  :data="tree.nodes"
                  :props="treeProps"
                  node-key="id"
                  :default-expand-all="false"
                  :expand-on-click-node="false"
                  :highlight-current="true"
                  indent="20"
                  @node-click="handleNodeClick"
                >
                  <template #default="{ node, data }">
                    <div class="custom-tree-node">
                      <div class="node-left">
                        <div class="node-dot" :style="{ backgroundColor: data.model_color || '#409EFF' }"></div>
                        <span class="node-label">{{ data.name }}</span>
                        <el-tag 
                          v-if="data.relation_name" 
                          size="small" 
                          effect="plain"
                          class="relation-tag"
                        >
                          {{ data.relation_name }}
                        </el-tag>
                      </div>
                      <div class="node-right">
                        <el-tag size="small" type="info" effect="light">{{ data.model_name }}</el-tag>
                        <el-dropdown trigger="click" @command="(cmd) => handleNodeExport(cmd, data)">
                          <el-button type="primary" link size="small" @click.stop>
                            <el-icon><Download /></el-icon>
                          </el-button>
                          <template #dropdown>
                            <el-dropdown-menu>
                              <el-dropdown-item :command="'csv'">导出 CSV</el-dropdown-item>
                              <el-dropdown-item :command="'json'">导出 JSON</el-dropdown-item>
                            </el-dropdown-menu>
                          </template>
                        </el-dropdown>
                        <el-button type="primary" link size="small" @click.stop="viewInstance(data)">
                          详情
                        </el-button>
                      </div>
                    </div>
                  </template>
                </el-tree>
              </div>
            </el-collapse-transition>
          </div>
        </div>

        <div class="orphan-section" v-if="orphanNodes.length > 0">
          <div class="orphan-header">
            <div class="orphan-title">
              <el-icon class="warning-icon"><WarningFilled /></el-icon>
              <span>待关联实例</span>
              <el-badge :value="orphanNodes.length" type="warning" />
            </div>
            <span class="orphan-hint">以下实例尚未关联到父级资源，请及时处理</span>
          </div>
          
          <div class="orphan-grid">
            <div 
              v-for="node in orphanNodes" 
              :key="node.id" 
              class="orphan-card"
              @click="viewInstance(node)"
            >
              <div class="orphan-card-header">
                <div class="orphan-dot" :style="{ backgroundColor: node.model_color || '#909399' }"></div>
                <span class="orphan-name">{{ node.name }}</span>
              </div>
              <div class="orphan-card-body">
                <div class="orphan-info-item">
                  <span class="info-label">模型</span>
                  <span class="info-value">{{ node.model_name }}</span>
                </div>
                <div class="orphan-info-item" v-if="node.code">
                  <span class="info-label">编码</span>
                  <span class="info-value">{{ node.code }}</span>
                </div>
              </div>
              <div class="orphan-card-footer">
                <el-button type="warning" size="small" plain @click.stop="showRelateDialog(node)">
                  <el-icon><Link /></el-icon>
                  关联父级
                </el-button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </el-card>

    <el-dialog 
      v-model="detailDialogVisible" 
      :title="currentInstance?.name || '实例详情'" 
      width="640px"
      class="detail-dialog"
    >
      <div class="detail-header" v-if="currentInstance">
        <div class="detail-icon" :style="{ backgroundColor: currentInstance.model_color || '#409EFF' }">
          <el-icon><component :is="getModelIcon(currentInstance.model_icon)" /></el-icon>
        </div>
        <div class="detail-info">
          <h3>{{ currentInstance.name }}</h3>
          <p>{{ currentInstance.model_name }} · {{ currentInstance.code || '无编码' }}</p>
        </div>
      </div>

      <el-divider />

      <el-descriptions :column="2" border size="small">
        <el-descriptions-item 
          v-for="(value, key) in currentInstance?.data" 
          :key="key" 
          :label="String(key)"
        >
          <el-tag v-if="String(key) === 'status'" :type="value === 'active' ? 'success' : 'info'" size="small">
            {{ value === 'active' ? '启用' : '停用' }}
          </el-tag>
          <span v-else>{{ formatValue(value) }}</span>
        </el-descriptions-item>
      </el-descriptions>

      <el-divider content-position="left">
        <el-icon><Connection /></el-icon>
        关联关系
      </el-divider>

      <div class="parents-section">
        <div v-if="parentsLoading" class="parents-loading">
          <el-skeleton :rows="2" animated />
        </div>
        <div v-else-if="parentInstances.length === 0" class="no-parents">
          <el-empty description="暂无父级资源" :image-size="60" />
        </div>
        <div v-else class="parents-list">
          <div 
            v-for="parent in parentInstances" 
            :key="parent.id" 
            class="parent-item"
            @click="navigateToInstance(parent)"
          >
            <div class="parent-left">
              <el-icon><Folder /></el-icon>
              <span>{{ parent.name }}</span>
              <el-tag size="small" type="info">{{ parent.model_name }}</el-tag>
            </div>
            <el-tag size="small" effect="plain">{{ parent.relation_name }}</el-tag>
          </div>
        </div>
      </div>
    </el-dialog>

    <el-dialog
      v-model="relateDialogVisible"
      title="关联父级资源"
      width="550px"
    >
      <el-alert
        v-if="!availableRelationDefs || availableRelationDefs.length === 0"
        title="该模型尚未定义任何关系，请先前往关系定义页面新增关系定义"
        type="error"
        :closable="false"
        style="margin-bottom: 16px;"
      />
      <el-form v-else label-width="80px">
        <el-form-item label="当前实例">
          <el-input :value="orphanInstance?.name" disabled />
        </el-form-item>
        <el-form-item label="所属模型">
          <el-input :value="orphanInstance?.model_name" disabled />
        </el-form-item>
        <el-form-item label="关联关系" required>
          <el-select v-model="selectedRelationDefId" placeholder="请选择关系" style="width: 100%" @change="handleRelationDefChange">
            <el-option
              v-for="rel in availableRelationDefs"
              :key="rel.id"
              :label="`${rel.source_model?.name} ${rel.relation_label} ${rel.target_model?.name}`"
              :value="rel.id"
            >
              <span>{{ rel.source_model?.name }}</span>
              <span style="color: #909399;"> {{ rel.relation_label }} </span>
              <span>{{ rel.target_model?.name }}</span>
            </el-option>
          </el-select>
        </el-form-item>
        <el-form-item v-if="selectedRelationDefId" label="父级资源">
          <el-select v-model="selectedParentId" placeholder="请选择父级资源" style="width: 100%" filterable :loading="parentsLoading">
            <el-option
              v-for="parent in availableParents"
              :key="parent.id"
              :label="parent.name"
              :value="parent.id"
            >
              <span>{{ parent.name }}</span>
              <el-tag size="small" type="info" style="margin-left: 8px;">{{ parent.code }}</el-tag>
            </el-option>
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="relateDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleRelate" :loading="relating" :disabled="!selectedRelationDefId || !selectedParentId">确认关联</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import {
  Refresh, FolderOpened, Share, Plus, Minus, ArrowDown,
  WarningFilled, Link, Connection, Folder, Download,
  Box, Monitor, OfficeBuilding, Cpu, Setting,
  Location, House, Grid, Coin, User, Document, MapLocation
} from '@element-plus/icons-vue'
import api from '@/api'

const loading = ref(false)
const parentsLoading = ref(false)
const relating = ref(false)
const forest = ref([])
const orphanNodes = ref([])
const expandedTrees = reactive({})
const treeRefs = reactive({})
const detailDialogVisible = ref(false)
const relateDialogVisible = ref(false)
const currentInstance = ref(null)
const orphanInstance = ref(null)
const parentInstances = ref([])
const availableParents = ref([])
const selectedParentId = ref(null)
const selectedRelationDefId = ref(null)
const availableRelationDefs = ref([])

// Model selector
const models = ref<any[]>([])
const selectedModelId = ref<string>('')

const treeProps = {
  children: 'children',
  label: 'name'
}

const iconMap = {
  'Box': Box,
  'Monitor': Monitor,
  'OfficeBuilding': OfficeBuilding,
  'Connection': Connection,
  'Cpu': Cpu,
  'Setting': Setting,
  'location': Location,
  'map-pin': MapLocation,
  'house': House,
  'grid': Grid,
  'coin': Coin,
  'user': User,
  'document': Document
}

const getModelIcon = (iconName) => {
  if (!iconName) return Box
  return iconMap[iconName.toLowerCase()] || Box
}

const formatValue = (value) => {
  if (value === null || value === undefined) return '-'
  if (typeof value === 'object') return JSON.stringify(value)
  return value
}

const setTreeRef = (index, el) => {
  if (el) {
    treeRefs[index] = el
  }
}

const toggleTree = (index) => {
  expandedTrees[index] = !expandedTrees[index]
}

const loadModels = async () => {
  try {
    const res = await api.get('/v2/models/')
    models.value = res.data || []
  } catch (error) {
    console.error('加载模型列表失败:', error)
  }
}

const handleModelChange = async (modelId: string) => {
  if (!modelId) {
    // Show all
    loadForest()
    return
  }

  loading.value = true
  try {
    const res = await api.get(`/v2/hierarchy/tree/${modelId}`)
    const data = res.data
    forest.value = [{
      model_id: data.root_model_id,
      model_name: data.root_model_name,
      model_code: '',
      model_color: '',
      model_icon: '',
      nodes: data.nodes || []
    }]
    orphanNodes.value = []
    expandedTrees[0] = true
  } catch (error) {
    console.error('加载层级视图失败:', error)
    ElMessage.error('加载层级视图失败')
  } finally {
    loading.value = false
  }
}

const loadForest = async () => {
  loading.value = true
  try {
    const res = await api.get('/v2/hierarchy/forest')
    forest.value = res.data.forest || []
    orphanNodes.value = res.data.orphan_nodes || []

    forest.value.forEach((_, index) => {
      expandedTrees[index] = true
    })
  } catch (error) {
    console.error('加载层级视图失败:', error)
    ElMessage.error('加载层级视图失败')
  } finally {
    loading.value = false
  }
}

const expandAll = () => {
  Object.keys(treeRefs).forEach(index => {
    const treeRef = treeRefs[index]
    if (treeRef && treeRef.store) {
      const nodes = treeRef.store.nodesMap
      Object.values(nodes).forEach((node: any) => {
        node.expanded = true
      })
    }
  })
}

const collapseAll = () => {
  Object.keys(treeRefs).forEach(index => {
    const treeRef = treeRefs[index]
    if (treeRef && treeRef.store) {
      const nodes = treeRef.store.nodesMap
      Object.values(nodes).forEach((node: any) => {
        node.expanded = false
      })
    }
  })
}

const handleNodeClick = (data) => {
  currentInstance.value = data
}

const viewInstance = async (instance) => {
  currentInstance.value = instance
  detailDialogVisible.value = true

  parentsLoading.value = true
  try {
    const res = await api.get(`/v2/hierarchy/parents/${instance.id}`)
    parentInstances.value = res.data || []
  } catch (error) {
    console.error('加载父级资源失败:', error)
    parentInstances.value = []
  } finally {
    parentsLoading.value = false
  }
}

const navigateToInstance = (parent) => {
  ElMessage.info('跳转到: ' + parent.name)
  detailDialogVisible.value = false
}

const showRelateDialog = async (instance) => {
  orphanInstance.value = instance
  relateDialogVisible.value = true
  selectedParentId.value = null
  selectedRelationDefId.value = null
  availableRelationDefs.value = []
  availableParents.value = []

  try {
    // 获取所有关系定义，找出当前实例模型作为目标模型（被包含/被连接）的关系
    const res = await api.get('/v2/relation-definitions/')
    const allRels = res.data || []

    // 筛选出以当前实例模型为目标模型的关系定义（contain类型）
    // 即：哪些模型"包含"当前实例
    availableRelationDefs.value = allRels.filter(r =>
      r.target_model_id === instance.model_id &&
      r.relation_type === 'contain' &&
      r.status === 'active'
    )

    if (availableRelationDefs.value.length === 0) {
      ElMessage.warning('该模型没有可用的层级关系定义')
    }
  } catch (error) {
    console.error('加载关系定义失败:', error)
    availableRelationDefs.value = []
  }
}

const handleRelationDefChange = async (relationDefId) => {
  selectedParentId.value = null
  availableParents.value = []

  if (!relationDefId) return

  parentsLoading.value = true
  try {
    // 找到选中的关系定义
    const relationDef = availableRelationDefs.value.find(r => r.id === relationDefId)
    if (!relationDef) return

    // 获取目标模型的实例列表（作为父级）
    const res = await api.get('/v1/instances/', {
      params: {
        model_id: relationDef.target_model_id,
        page: 1,
        page_size: 100
      }
    })
    availableParents.value = res.data.items || []
  } catch (error) {
    console.error('加载父级实例列表失败:', error)
    ElMessage.error('加载父级实例列表失败')
  } finally {
    parentsLoading.value = false
  }
}

const handleRelate = async () => {
  if (!selectedRelationDefId.value) {
    ElMessage.warning('请选择关联关系')
    return
  }
  if (!selectedParentId.value) {
    ElMessage.warning('请选择父级资源')
    return
  }

  relating.value = true
  try {
    await api.post('/v2/instance-relations/', {
      relation_definition_id: selectedRelationDefId.value,
      source_instance_id: orphanInstance.value.id,
      target_instance_id: selectedParentId.value
    })

    ElMessage.success('关联成功')
    relateDialogVisible.value = false
    loadForest()
  } catch (error) {
    console.error('关联失败:', error)
    ElMessage.error(error.response?.data?.detail || '关联失败')
  } finally {
    relating.value = false
  }
}

const handleExportCommand = (command) => {
  exportForest(command)
}

const handleNodeExport = (command, data) => {
  exportInstance(data.id, command)
}

const exportForest = async (format) => {
  try {
    ElMessage.info('正在导出，请稍候...')

    const response = await api.get('/v2/hierarchy/export-forest', {
      params: { format },
      responseType: 'blob'
    })

    const blob = new Blob([response.data], {
      type: format === 'csv' ? 'text/csv;charset=utf-8' : 'application/json'
    })
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = format === 'csv' ? 'hierarchy_forest.csv' : 'hierarchy_forest.json'
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)

    ElMessage.success('导出成功')
  } catch (error) {
    console.error('导出失败:', error)
    ElMessage.error('导出失败')
  }
}

const exportInstance = async (instanceId, format) => {
  try {
    ElMessage.info('正在导出，请稍候...')

    const response = await api.get(`/v2/hierarchy/export/${instanceId}`, {
      params: { format },
      responseType: 'blob'
    })

    const blob = new Blob([response.data], {
      type: format === 'csv' ? 'text/csv;charset=utf-8' : 'application/json'
    })
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = format === 'csv' ? `instance_${instanceId}_tree.csv` : `instance_${instanceId}_tree.json`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)

    ElMessage.success('导出成功')
  } catch (error) {
    console.error('导出失败:', error)
    ElMessage.error('导出失败')
  }
}

onMounted(() => {
  loadModels()
  loadForest()
})
</script>

<style scoped>
.hierarchy-view-page {
  padding: 20px;
  min-height: calc(100vh - 100px);
  background: linear-gradient(135deg, #f5f7fa 0%, #e4e7ed 100%);
}

.main-card {
  border-radius: 12px;
  border: none;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.header-icon {
  font-size: 22px;
  color: #409EFF;
}

.header-title {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.empty-state {
  padding: 80px 0;
  text-align: center;
}

.loading-state {
  padding: 20px;
}

.content-wrapper {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.tree-block {
  background: #fff;
  border-radius: 10px;
  border: 1px solid #ebeef5;
  overflow: hidden;
  transition: box-shadow 0.3s;
}

.tree-block:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.06);
}

.tree-block-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  background: linear-gradient(90deg, #f8fafc 0%, #fff 100%);
  cursor: pointer;
  border-bottom: 1px solid #ebeef5;
  transition: background 0.3s;
}

.tree-block-header:hover {
  background: linear-gradient(90deg, #f0f7ff 0%, #fff 100%);
}

.block-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.model-badge {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 18px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
}

.block-info {
  display: flex;
  flex-direction: column;
}

.block-title {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.block-desc {
  font-size: 12px;
  color: #909399;
  margin-top: 2px;
}

.expand-icon {
  color: #909399;
  transition: transform 0.3s;
}

.expand-icon.is-expanded {
  transform: rotate(180deg);
}

.tree-block-content {
  padding: 16px 20px;
}

.custom-tree-node {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
  padding: 6px 0;
}

.node-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.node-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.node-label {
  font-size: 14px;
  color: #303133;
}

.relation-tag {
  font-size: 11px;
  color: #909399;
  background: #f4f4f5;
  border: none;
}

.node-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.orphan-section {
  background: linear-gradient(135deg, #fffbeb 0%, #fff8e6 100%);
  border-radius: 12px;
  border: 1px solid #f5dab1;
  padding: 20px;
}

.orphan-header {
  margin-bottom: 16px;
}

.orphan-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
  color: #b88230;
  margin-bottom: 4px;
}

.warning-icon {
  font-size: 20px;
  color: #e6a23c;
}

.orphan-hint {
  font-size: 12px;
  color: #c0a070;
}

.orphan-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 16px;
}

.orphan-card {
  background: #fff;
  border-radius: 10px;
  border: 1px solid #ebeef5;
  padding: 16px;
  cursor: pointer;
  transition: all 0.3s;
}

.orphan-card:hover {
  border-color: #e6a23c;
  box-shadow: 0 4px 12px rgba(230, 162, 60, 0.15);
  transform: translateY(-2px);
}

.orphan-card-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 12px;
}

.orphan-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
}

.orphan-name {
  font-size: 15px;
  font-weight: 600;
  color: #303133;
}

.orphan-card-body {
  margin-bottom: 12px;
}

.orphan-info-item {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  margin-bottom: 4px;
}

.info-label {
  color: #909399;
}

.info-value {
  color: #606266;
}

.orphan-card-footer {
  padding-top: 12px;
  border-top: 1px solid #ebeef5;
}

.detail-dialog .detail-header {
  display: flex;
  align-items: center;
  gap: 16px;
  padding-bottom: 16px;
}

.detail-icon {
  width: 56px;
  height: 56px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 24px;
}

.detail-info h3 {
  margin: 0;
  font-size: 18px;
  color: #303133;
}

.detail-info p {
  margin: 4px 0 0;
  font-size: 13px;
  color: #909399;
}

.parents-section {
  min-height: 80px;
}

.parents-loading {
  padding: 10px;
}

.no-parents {
  padding: 20px 0;
}

.parents-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.parent-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: #f5f7fa;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.3s;
}

.parent-item:hover {
  background: #eef5ff;
}

.parent-left {
  display: flex;
  align-items: center;
  gap: 10px;
  color: #303133;
}

:deep(.el-tree-node__content) {
  height: auto;
  padding: 4px 0;
}

:deep(.el-tree-node__expand-icon) {
  color: #909399;
}

:deep(.el-tree--highlight-current .el-tree-node.is-current > .el-tree-node__content) {
  background-color: #ecf5ff;
  border-radius: 6px;
}

.model-selector-section {
  padding: 16px 20px;
  background: linear-gradient(90deg, #f8fafc 0%, #fff 100%);
  border-bottom: 1px solid #ebeef5;
}

.selector-wrapper {
  display: flex;
  align-items: center;
  gap: 12px;
}

.selector-label {
  font-size: 14px;
  color: #606266;
  font-weight: 500;
  white-space: nowrap;
}

.model-select {
  width: 300px;
}

.model-option {
  display: flex;
  align-items: center;
  gap: 10px;
}

.model-option-icon {
  width: 24px;
  height: 24px;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 12px;
  font-weight: 600;
  flex-shrink: 0;
}

.model-option-name {
  flex: 1;
}

.model-option-code {
  font-size: 12px;
  color: #909399;
  font-family: monospace;
}

@media (max-width: 768px) {
  .selector-wrapper {
    flex-direction: column;
    align-items: stretch;
  }

  .model-select {
    width: 100%;
  }

  .header-actions {
    flex-wrap: wrap;
    gap: 8px;
  }
}
</style>
