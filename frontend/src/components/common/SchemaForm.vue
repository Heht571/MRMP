<template>
  <el-form 
    ref="formRef" 
    :model="formData" 
    :rules="formRules" 
    label-width="120px" 
    class="py-4"
    v-loading="loading"
  >
    <!-- Basic Info Section -->
    <div class="bg-gray-50 p-4 rounded-lg border border-gray-100 mb-6">
      <div class="text-sm font-semibold text-gray-700 mb-4 border-l-4 border-indigo-500 pl-2">基础信息</div>
      <el-row :gutter="24">
        <el-col :span="12">
          <el-form-item label="名称" prop="name">
            <el-input v-model="formData.name" placeholder="请输入名称" />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="编码" prop="code">
            <el-input v-model="formData.code" placeholder="请输入编码" />
          </el-form-item>
        </el-col>
      </el-row>
    </div>
    
    <!-- Dynamic Attributes Section -->
    <div v-if="attributes.length > 0">
      <div class="text-sm font-semibold text-gray-700 mb-4 border-l-4 border-indigo-500 pl-2">扩展属性</div>
      <el-row :gutter="24">
        <el-col 
          v-for="attr in attributes" 
          :key="attr.id" 
          :span="12"
        >
          <el-form-item 
            :label="attr.label" 
            :prop="'data.' + attr.name"
            :rules="getRules(attr)"
          >
            <!-- String -->
            <el-input 
              v-if="attr.type === 'string'" 
              v-model="formData.data[attr.name]" 
              :placeholder="`请输入${attr.label}`" 
            />
            <!-- Number -->
            <el-input-number 
              v-else-if="attr.type === 'number'" 
              v-model="formData.data[attr.name]" 
              style="width: 100%"
              class="w-full"
            />
            <!-- Enum -->
            <el-select 
              v-else-if="attr.type === 'enum'" 
              v-model="formData.data[attr.name]" 
              :placeholder="`请选择${attr.label}`"
              style="width: 100%"
              class="w-full"
              clearable
            >
              <el-option 
                v-for="val in getEnumOptions(attr.enum_values)" 
                :key="val.value" 
                :label="val.label" 
                :value="val.value" 
              />
            </el-select>
            <!-- Boolean -->
            <el-switch 
              v-else-if="attr.type === 'boolean'" 
              v-model="formData.data[attr.name]" 
            />
            <!-- Date -->
            <el-date-picker 
              v-else-if="attr.type === 'date'" 
              v-model="formData.data[attr.name]" 
              type="date"
              style="width: 100%"
              class="w-full"
              value-format="YYYY-MM-DD"
            />
            <!-- Datetime -->
            <el-date-picker 
              v-else-if="attr.type === 'datetime'" 
              v-model="formData.data[attr.name]" 
              type="datetime"
              style="width: 100%"
              class="w-full"
              value-format="YYYY-MM-DD HH:mm:ss"
            />
            <!-- Default -->
            <el-input 
              v-else 
              v-model="formData.data[attr.name]" 
              :placeholder="`请输入${attr.label}`" 
            />
          </el-form-item>
        </el-col>
      </el-row>
    </div>

    <!-- Actions -->
    <div class="flex justify-end gap-3 mt-6 border-t border-gray-200 pt-4">
      <el-button @click="$emit('cancel')">取消</el-button>
      <el-button type="primary" @click="handleSubmit" :loading="submitting" class="bg-indigo-600 border-indigo-600 hover:bg-indigo-700">保存</el-button>
    </div>
  </el-form>
</template>

<script setup lang="ts">
import { ref, watch, computed, onMounted } from 'vue'
import type { FormInstance, FormRules } from 'element-plus'
import api from '@/api'

const props = defineProps<{
  modelId?: string
  modelDefinition?: any
  initialData?: any
}>()

const emit = defineEmits(['submit', 'cancel'])

const formRef = ref<FormInstance>()
const loading = ref(false)
const submitting = ref(false)
const model = ref<any>(null)
const formData = ref<any>({ name: '', code: '', data: {} })

const attributes = computed(() => {
  if (props.modelDefinition) return props.modelDefinition.attributes || []
  return model.value?.attributes || []
})

const formRules = computed(() => {
  const rules: any = {
    name: [{ required: true, message: '请输入名称', trigger: 'blur' }],
    code: [{ required: true, message: '请输入编码', trigger: 'blur' }]
  }
  return rules
})

const getRules = (attr: any) => {
  const rules = []
  if (attr.is_required) {
    rules.push({ 
      required: true, 
      message: `请输入${attr.label}`, 
      trigger: ['enum', 'date', 'datetime'].includes(attr.type) ? 'change' : 'blur' 
    })
  }
  return rules
}

const getEnumOptions = (enumValues: any) => {
  if (!enumValues) return []
  if (Array.isArray(enumValues)) {
    return enumValues.map((v: any) => {
      if (typeof v === 'object' && v !== null) {
        return { label: v.label || v.value, value: v.value }
      }
      return { label: v, value: v }
    })
  }
  return []
}

const loadModel = async () => {
  if (props.modelDefinition) {
    model.value = props.modelDefinition
    initForm()
    return
  }
  
  if (!props.modelId) return

  loading.value = true
  try {
    const res = await api.get(`/v2/models/${props.modelId}`)
    model.value = res.data
    initForm()
  } catch (error) {
    console.error('Failed to load model:', error)
  } finally {
    loading.value = false
  }
}

const initForm = () => {
  if (props.initialData) {
    formData.value = {
      name: props.initialData.name,
      code: props.initialData.code,
      data: { ...props.initialData.data } || {}
    }
  } else {
    formData.value = { name: '', code: '', data: {} }
    // Set default values from model attributes
    attributes.value.forEach((attr: any) => {
      if (attr.default_value !== undefined && attr.default_value !== null && attr.default_value !== '') {
        formData.value.data[attr.name] = attr.default_value
      }
    })
  }
}

watch(() => props.modelId, loadModel)
watch(() => props.modelDefinition, () => {
  model.value = props.modelDefinition
  initForm()
})
watch(() => props.initialData, initForm, { deep: true })

onMounted(() => {
  loadModel()
})

const handleSubmit = async () => {
  if (!formRef.value) return
  
  try {
    await formRef.value.validate()
    submitting.value = true
    emit('submit', { ...formData.value, model_id: props.modelId || model.value?.id })
    // Note: We don't set submitting = false here because the parent usually handles the async submit
    // But if we want to reset it:
    setTimeout(() => { submitting.value = false }, 1000)
  } catch (error) {
    console.error('Validation failed', error)
  }
}
</script>
