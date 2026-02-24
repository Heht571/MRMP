<template>
  <PageContainer title="Dynamic Form Demo" description="演示基于模型元数据自动生成表单的能力">
    <div class="p-4 space-y-4">
      <el-card class="rounded-xl shadow-sm border-gray-200">
        <template #header>
          <div class="flex justify-between items-center">
            <span class="font-medium">选择模型进行测试</span>
            <el-select 
              v-model="selectedModelId" 
              placeholder="请选择模型" 
              class="w-64"
              @change="handleModelChange"
            >
              <el-option
                v-for="model in models"
                :key="model.id"
                :label="model.name"
                :value="model.id"
              />
            </el-select>
          </div>
        </template>
        
        <div v-if="selectedModelId" class="mt-4">
          <SchemaForm 
            :model-id="selectedModelId" 
            @submit="handleSubmit" 
            @cancel="handleCancel"
          />
        </div>
        <div v-else class="text-center text-gray-500 py-12 bg-gray-50 rounded-lg border border-dashed border-gray-300">
          请在上方选择一个模型以预览动态表单效果
        </div>
      </el-card>
      
      <el-card v-if="submittedData" class="rounded-xl shadow-sm border-gray-200 bg-gray-50">
        <template #header>
          <div class="font-medium text-gray-700">提交数据预览</div>
        </template>
        <pre class="text-xs font-mono bg-gray-800 text-green-400 p-4 rounded overflow-auto max-h-60">{{ JSON.stringify(submittedData, null, 2) }}</pre>
      </el-card>
    </div>
  </PageContainer>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import SchemaForm from '@/components/common/SchemaForm.vue'
import PageContainer from '@/components/PageContainer.vue'
import api from '@/api'
import { ElMessage } from 'element-plus'

const models = ref<any[]>([])
const selectedModelId = ref('')
const submittedData = ref<any>(null)

const loadModels = async () => {
  try {
    const res = await api.get('/v2/models/')
    models.value = res.data
  } catch (error) {
    console.error('Failed to load models:', error)
  }
}

const handleModelChange = () => {
  submittedData.value = null
}

const handleSubmit = (data: any) => {
  console.log('Form Submitted:', data)
  submittedData.value = data
  ElMessage.success('表单数据已捕获 (请查看下方预览)')
}

const handleCancel = () => {
  ElMessage.info('操作已取消')
  selectedModelId.value = ''
  submittedData.value = null
}

onMounted(() => {
  loadModels()
})
</script>
