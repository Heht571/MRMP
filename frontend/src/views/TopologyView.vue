<template>
  <PageContainer title="资源拓扑视图" description="可视化展示资源间的关联关系">
    <div class="topology-container">
      <div class="topology-controls">
        <el-select 
          v-model="rootId" 
          placeholder="选择根节点" 
          class="root-select"
          filterable
          remote
          :remote-method="searchInstances"
          :loading="searching"
          @change="fetchTopology"
        >
          <el-option 
            v-for="item in searchResults" 
            :key="item.id" 
            :label="item.name" 
            :value="item.id"
          >
            <div class="root-option">
              <span class="root-option-name">{{ item.name }}</span>
              <span class="root-option-code">{{ item.code }}</span>
            </div>
          </el-option>
        </el-select>
        
        <el-input-number v-model="depth" :min="1" :max="5" @change="fetchTopology" controls-position="right" />
        
        <el-button type="primary" @click="fetchTopology" :loading="loading">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
      </div>

      <VueFlow 
        v-model="elements" 
        :fit-view-on-init="true"
        class="topology-graph"
        :default-viewport="{ zoom: 1.0 }"
        :min-zoom="0.2"
        :max-zoom="4"
      >
        <Background pattern-color="#d0d0d0" :gap="20" />
        <Controls />
        <MiniMap />
        
        <template #node-custom="props">
          <div class="topo-node" :class="{ 'topo-node--selected': props.selected }">
            <div class="topo-node-header">
              <div class="topo-node-dot" :style="{ backgroundColor: props.data.color || '#0071e3' }"></div>
              <span class="topo-node-title">{{ props.label }}</span>
            </div>
            <div class="topo-node-body">
              <div class="topo-node-row">
                <span class="topo-node-label">类型</span>
                <span class="topo-node-value">{{ props.data.model_name }}</span>
              </div>
              <div class="topo-node-row">
                <span class="topo-node-label">编码</span>
                <span class="topo-node-mono">{{ props.data.code }}</span>
              </div>
            </div>
            
            <div v-if="props.data.has_more || props.data.is_expanded" 
                 class="topo-node-footer"
                 @click.stop
            >
              <el-button 
                size="small" 
                :type="props.data.is_expanded ? 'default' : 'primary'" 
                link 
                :loading="props.data.loading"
                @click="toggleNode(props.id)"
              >
                {{ props.data.is_expanded ? '收起' : `展开 (${props.data.visible_degree}/${props.data.degree})` }}
              </el-button>
            </div>

            <Handle type="target" :position="Position.Top" class="topo-handle" />
            <Handle type="source" :position="Position.Bottom" class="topo-handle" />
          </div>
        </template>
      </VueFlow>
      
      <div v-if="loading" class="topology-loading">
        <el-icon class="is-loading" :size="32"><Loading /></el-icon>
      </div>
    </div>
  </PageContainer>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { VueFlow, useVueFlow, Position } from '@vue-flow/core'
import { Background } from '@vue-flow/background'
import { Controls } from '@vue-flow/controls'
import { MiniMap } from '@vue-flow/minimap'
import { Handle } from '@vue-flow/core'
import { Loading, Refresh } from '@element-plus/icons-vue'
import dagre from 'dagre'
import api from '@/api'
import '@vue-flow/core/dist/style.css'
import '@vue-flow/controls/dist/style.css'
import '@vue-flow/minimap/dist/style.css'

const route = useRoute()
const { fitView } = useVueFlow()

const rootId = ref('')
const depth = ref(2)
const loading = ref(false)
const searching = ref(false)
const searchResults = ref<any[]>([])
const elements = ref<any[]>([])

const nodesMap = ref(new Map<string, any>())
const edgesMap = ref(new Map<string, any>())

const searchInstances = async (query: string) => {
  if (!query) return
  searching.value = true
  try {
    const res = await api.get('/v1/instances/', { params: { keyword: query, page_size: 10 } })
    searchResults.value = res.data.items
  } finally {
    searching.value = false
  }
}

const getLayoutedElements = (nodes: any[], edges: any[]) => {
  const dagreGraph = new dagre.graphlib.Graph()
  dagreGraph.setGraph({ rankdir: 'TB', nodesep: 80, ranksep: 120 })
  dagreGraph.setDefaultEdgeLabel(() => ({}))

  nodes.forEach((node) => {
    dagreGraph.setNode(node.id, { width: 200, height: 100 })
  })

  edges.forEach((edge) => {
    dagreGraph.setEdge(edge.source, edge.target)
  })

  dagre.layout(dagreGraph)

  return [
    ...nodes.map((node) => {
      const nodeWithPosition = dagreGraph.node(node.id)
      return {
        ...node,
        position: { x: nodeWithPosition.x - 100, y: nodeWithPosition.y - 50 },
      }
    }),
    ...edges,
  ]
}

const updateGraph = () => {
  const nodes = Array.from(nodesMap.value.values())
  const edges = Array.from(edgesMap.value.values())
  elements.value = getLayoutedElements(nodes, edges)
}

const fetchTopology = async () => {
  if (!rootId.value) return
  
  loading.value = true
  nodesMap.value.clear()
  edgesMap.value.clear()
  
  try {
    const res = await api.get('/v2/topology/', { 
      params: { root_id: rootId.value, depth: depth.value } 
    })
    
    const { nodes, edges } = res.data
    
    nodes.forEach((n: any) => {
      n.data.refCount = 1
      n.data.expandedChildren = new Set()
      n.data.expandedEdges = new Set()
      n.data.is_expanded = false
      nodesMap.value.set(n.id, n)
    })
    
    edges.forEach((e: any) => {
      e.data = e.data || {}
      e.data.refCount = 1
      e.animated = true
      e.style = { stroke: '#0071e3', strokeWidth: 1.5 }
      edgesMap.value.set(e.id, e)
    })
    
    updateGraph()
    
    setTimeout(() => {
      fitView()
    }, 100)
    
  } catch (error) {
    console.error('Failed to fetch topology:', error)
  } finally {
    loading.value = false
  }
}

const toggleNode = (nodeId: string) => {
  const node = nodesMap.value.get(nodeId)
  if (!node) return
  
  if (node.data.is_expanded) {
    collapseNode(nodeId)
  } else {
    expandNode(nodeId)
  }
}

const collapseNode = (nodeId: string) => {
  const node = nodesMap.value.get(nodeId)
  if (!node || !node.data.is_expanded) return

  node.data.expandedChildren.forEach((childId: string) => {
    const child = nodesMap.value.get(childId)
    if (child) {
      child.data.refCount--
      if (child.data.refCount <= 0) {
        nodesMap.value.delete(childId)
      }
    }
  })
  
  node.data.expandedEdges.forEach((edgeId: string) => {
    const edge = edgesMap.value.get(edgeId)
    if (edge) {
      edge.data.refCount--
      if (edge.data.refCount <= 0) {
        edgesMap.value.delete(edgeId)
      }
    }
  })

  node.data.expandedChildren.clear()
  node.data.expandedEdges.clear()
  
  node.data.is_expanded = false
  
  nodesMap.value.set(nodeId, { ...node })
  updateGraph()
}

const expandNode = async (nodeId: string) => {
  const node = nodesMap.value.get(nodeId)
  if (node) {
    node.data.loading = true
    nodesMap.value.set(nodeId, { ...node })
    updateGraph()
  }

  try {
    const res = await api.get('/v2/topology/', { 
      params: { root_id: nodeId, depth: 1 } 
    })
    
    const { nodes, edges } = res.data
    const currentNode = nodesMap.value.get(nodeId)
    if (!currentNode) return

    if (!currentNode.data.expandedChildren) currentNode.data.expandedChildren = new Set()
    if (!currentNode.data.expandedEdges) currentNode.data.expandedEdges = new Set()
    
    nodes.forEach((n: any) => {
      if (n.id === nodeId) return

      let existingNode = nodesMap.value.get(n.id)
      if (existingNode) {
        existingNode.data.refCount = (existingNode.data.refCount || 0) + 1
        nodesMap.value.set(n.id, existingNode)
      } else {
        n.data.refCount = 1
        n.data.expandedChildren = new Set()
        n.data.expandedEdges = new Set()
        n.data.is_expanded = false
        nodesMap.value.set(n.id, n)
      }
      currentNode.data.expandedChildren.add(n.id)
    })
    
    edges.forEach((e: any) => {
      let existingEdge = edgesMap.value.get(e.id)
      if (existingEdge) {
        existingEdge.data = existingEdge.data || {}
        existingEdge.data.refCount = (existingEdge.data.refCount || 0) + 1
        edgesMap.value.set(e.id, existingEdge)
      } else {
        e.data = e.data || {}
        e.data.refCount = 1
        e.animated = true
        e.style = { stroke: '#0071e3', strokeWidth: 1.5 }
        edgesMap.value.set(e.id, e)
      }
      currentNode.data.expandedEdges.add(e.id)
    })
    
    currentNode.data.is_expanded = true
    updateGraph()
    
  } catch (error) {
    console.error('Failed to expand node:', error)
  } finally {
    const updatedNode = nodesMap.value.get(nodeId)
    if (updatedNode) {
      updatedNode.data.loading = false
      nodesMap.value.set(nodeId, { ...updatedNode })
      updateGraph()
    }
  }
}

onMounted(() => {
  if (route.query.root_id) {
    rootId.value = route.query.root_id as string
    fetchTopology()
  }
})
</script>

<style scoped>
.topology-container {
  position: relative;
  height: calc(100vh - 200px);
  background: var(--color-bg-light);
  border-radius: var(--radius-xl);
  overflow: hidden;
}

.topology-controls {
  position: absolute;
  top: var(--space-md);
  left: var(--space-md);
  z-index: 10;
  display: flex;
  gap: var(--space-sm);
  align-items: center;
}

.root-select {
  width: 260px;
}

.root-option {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
}

.root-option-name {
  font-weight: 500;
}

.root-option-code {
  font-size: 12px;
  color: var(--color-text-tertiary);
  font-family: monospace;
}

.topology-graph {
  width: 100%;
  height: 100%;
}

.topology-loading {
  position: absolute;
  inset: 0;
  background: rgba(255,255,255,0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 20;
}

.topo-node {
  background: var(--color-surface-light);
  border: 2px solid rgba(0,0,0,0.08);
  border-radius: var(--radius-lg);
  padding: 12px 16px;
  min-width: 180px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.08);
  transition: border-color 0.2s, box-shadow 0.2s;
}

.topo-node--selected {
  border-color: var(--color-accent);
  box-shadow: 0 4px 20px rgba(0,113,227,0.2);
}

.topo-node-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
  padding-bottom: 8px;
  border-bottom: 1px solid rgba(0,0,0,0.06);
}

.topo-node-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
}

.topo-node-title {
  font-weight: 600;
  font-size: 13px;
  color: var(--color-text-dark);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.topo-node-body {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.topo-node-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 11px;
}

.topo-node-label {
  color: var(--color-text-tertiary);
}

.topo-node-value {
  font-weight: 500;
  color: var(--color-text-secondary);
}

.topo-node-mono {
  font-family: monospace;
  font-size: 11px;
  color: var(--color-text-secondary);
}

.topo-node-footer {
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px solid rgba(0,0,0,0.06);
  display: flex;
  justify-content: center;
}

.topo-handle {
  width: 8px;
  height: 8px;
  background: var(--color-accent);
  border: 2px solid white;
}
</style>

<style>
.vue-flow__minimap {
  transform: scale(75%);
  transform-origin: bottom right;
}
</style>
