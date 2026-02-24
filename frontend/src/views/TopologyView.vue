<template>
  <PageContainer title="资源拓扑视图" description="可视化展示资源间的关联关系">
    <div class="h-[calc(100vh-200px)] relative bg-gray-50 rounded-xl border border-gray-200 overflow-hidden">
      <!-- Controls -->
      <div class="absolute top-4 left-4 z-10 flex gap-2">
        <el-select 
          v-model="rootId" 
          placeholder="选择根节点" 
          class="w-64"
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
            <div class="flex items-center justify-between">
              <span>{{ item.name }}</span>
              <span class="text-xs text-gray-400">{{ item.code }}</span>
            </div>
          </el-option>
        </el-select>
        
        <el-input-number v-model="depth" :min="1" :max="5" @change="fetchTopology" label="深度" />
        
        <el-button type="primary" @click="fetchTopology" :loading="loading">刷新</el-button>
      </div>

      <!-- Graph -->
      <VueFlow 
        v-model="elements" 
        :fit-view-on-init="true"
        class="w-full h-full"
        :default-viewport="{ zoom: 1.2 }"
        :min-zoom="0.2"
        :max-zoom="4"
      >
        <Background pattern-color="#aaa" :gap="16" />
        <Controls />
        <MiniMap />
        
        <template #node-custom="props">
          <div class="custom-node bg-white border-2 rounded-lg p-3 shadow-md min-w-[150px]" 
               :class="{'border-indigo-500': props.selected, 'border-gray-200': !props.selected}"
          >
            <div class="flex items-center gap-2 mb-2 border-b border-gray-100 pb-2">
              <div class="w-3 h-3 rounded-full" :style="{ backgroundColor: props.data.color }"></div>
              <span class="font-bold text-sm truncate">{{ props.label }}</span>
            </div>
            <div class="text-xs text-gray-500 space-y-1">
              <div class="flex justify-between">
                <span>类型:</span>
                <span class="font-medium">{{ props.data.model_name }}</span>
              </div>
              <div class="flex justify-between">
                <span>编码:</span>
                <span class="font-mono">{{ props.data.code }}</span>
              </div>
            </div>
            
            <!-- Expand/Collapse Button -->
            <div v-if="props.data.has_more || props.data.is_expanded" 
                 class="mt-2 pt-2 border-t border-gray-100 flex justify-center"
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

            <Handle type="target" :position="Position.Top" class="w-3 h-3 !bg-gray-400" />
            <Handle type="source" :position="Position.Bottom" class="w-3 h-3 !bg-gray-400" />
          </div>
        </template>
      </VueFlow>
      
      <div v-if="loading" class="absolute inset-0 bg-white/80 flex items-center justify-center z-20">
        <el-icon class="is-loading text-3xl text-indigo-600"><Loading /></el-icon>
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
import { Loading } from '@element-plus/icons-vue'
import dagre from 'dagre'
import api from '@/api'
import '@vue-flow/core/dist/style.css'
import '@vue-flow/controls/dist/style.css'
import '@vue-flow/minimap/dist/style.css'

const route = useRoute()
const { fitView } = useVueFlow()

const rootId = ref('')
const depth = ref(2) // Default depth reduced to 2 for cleaner initial view
const loading = ref(false)
const searching = ref(false)
const searchResults = ref<any[]>([])
const elements = ref<any[]>([])

// Store graph data separately to support merging
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
  dagreGraph.setGraph({ rankdir: 'TB', nodesep: 100, ranksep: 150 })
  dagreGraph.setDefaultEdgeLabel(() => ({}))

  nodes.forEach((node) => {
    dagreGraph.setNode(node.id, { width: 180, height: 100 })
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
        position: { x: nodeWithPosition.x - 90, y: nodeWithPosition.y - 50 },
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
  // Clear existing graph when doing a full fetch
  nodesMap.value.clear()
  edgesMap.value.clear()
  
  try {
    const res = await api.get('/v2/topology/', { 
      params: { root_id: rootId.value, depth: depth.value } 
    })
    
    const { nodes, edges } = res.data
    
    // Initialize nodes with refCount and is_expanded state
    nodes.forEach((n: any) => {
      // By default, nodes loaded initially are not considered "expanded" in the UI sense
      // unless we want to track them. But for simplicity, we treat initial load as base state.
      // We set refCount to 1 so they are not removed by collapse operations of other nodes.
      n.data.refCount = 1
      n.data.expandedChildren = new Set() // Store IDs of nodes expanded by this node
      n.data.expandedEdges = new Set()    // Store IDs of edges expanded by this node
      n.data.is_expanded = false
      nodesMap.value.set(n.id, n)
    })
    
    edges.forEach((e: any) => {
      e.data = e.data || {}
      e.data.refCount = 1
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

  // Decrement ref counts for children nodes
  node.data.expandedChildren.forEach((childId: string) => {
    const child = nodesMap.value.get(childId)
    if (child) {
      child.data.refCount--
      if (child.data.refCount <= 0) {
        nodesMap.value.delete(childId)
      }
    }
  })
  
  // Decrement ref counts for edges
  node.data.expandedEdges.forEach((edgeId: string) => {
    const edge = edgesMap.value.get(edgeId)
    if (edge) {
      edge.data.refCount--
      if (edge.data.refCount <= 0) {
        edgesMap.value.delete(edgeId)
      }
    }
  })

  // Clear expanded tracking
  node.data.expandedChildren.clear()
  node.data.expandedEdges.clear()
  
  // Update state
  node.data.is_expanded = false
  // Restore has_more if it was true before (logic: if we collapse, we can expand again)
  // We assume if it was expandable, it still is.
  // We don't change has_more here, just UI state.
  
  // Force update map to trigger reactivity
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
    // Fetch direct neighbors (depth=1) for this node
    const res = await api.get('/v2/topology/', { 
      params: { root_id: nodeId, depth: 1 } 
    })
    
    const { nodes, edges } = res.data
    const currentNode = nodesMap.value.get(nodeId)
    if (!currentNode) return

    // Initialize tracking sets if missing (defensive)
    if (!currentNode.data.expandedChildren) currentNode.data.expandedChildren = new Set()
    if (!currentNode.data.expandedEdges) currentNode.data.expandedEdges = new Set()
    
    // Process Nodes
    nodes.forEach((n: any) => {
      // Skip the source node itself
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
      // Track that this node was brought in by current expansion
      currentNode.data.expandedChildren.add(n.id)
    })
    
    // Process Edges
    edges.forEach((e: any) => {
      let existingEdge = edgesMap.value.get(e.id)
      if (existingEdge) {
        existingEdge.data = existingEdge.data || {}
        existingEdge.data.refCount = (existingEdge.data.refCount || 0) + 1
        edgesMap.value.set(e.id, existingEdge)
      } else {
        e.data = e.data || {}
        e.data.refCount = 1
        edgesMap.value.set(e.id, e)
      }
      // Track that this edge was brought in by current expansion
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

<style>
.vue-flow__minimap {
  transform: scale(75%);
  transform-origin: bottom right;
}
</style>
