<template>
  <PageContainer 
    title="资源实例管理" 
    description="管理各类资源的具体实例数据，支持动态表单和批量操作。"
  >
    <div class="p-4 space-y-4">
      <!-- Filter Bar -->
      <div class="bg-gray-50 p-4 rounded-xl border border-gray-200 flex flex-wrap gap-4 items-center justify-between">
        <div class="flex items-center gap-4 flex-wrap">
          <div class="flex items-center gap-2">
            <span class="text-sm font-medium text-gray-600">资源类型</span>
            <el-select 
              v-model="selectedModelId" 
              placeholder="请选择模型" 
              class="w-56" 
              @change="handleModelChange"
              filterable
            >
              <el-option 
                v-for="model in models" 
                :key="model.id" 
                :label="model.name" 
                :value="model.id" 
              >
                <div class="flex items-center gap-2">
                  <div class="w-2 h-2 rounded-full" :style="{ backgroundColor: model.color || '#ccc' }"></div>
                  <span>{{ model.name }}</span>
                </div>
              </el-option>
            </el-select>
          </div>
          
          <div class="flex items-center gap-2">
            <span class="text-sm font-medium text-gray-600">关键字</span>
            <el-input 
              v-model="filters.keyword" 
              placeholder="名称 / 编码" 
              clearable 
              class="w-64"
              @keyup.enter="handleSearch"
            >
              <template #prefix><el-icon><Search /></el-icon></template>
            </el-input>
          </div>

          <el-button type="primary" @click="handleSearch" class="bg-indigo-600 border-indigo-600 hover:bg-indigo-700">
            搜索
          </el-button>
          <el-button @click="handleReset">重置</el-button>
          
          <el-button 
            type="primary" 
            link 
            @click="showAdvancedSearch = !showAdvancedSearch"
            :disabled="!selectedModelId"
          >
            <el-icon class="mr-1"><Filter /></el-icon> 高级搜索
          </el-button>
        </div>

        <div class="flex items-center gap-2">
           <el-dropdown trigger="click" @command="handleMoreAction">
            <el-button>
              更多操作 <el-icon class="el-icon--right"><ArrowDown /></el-icon>
            </el-button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="template" :disabled="!selectedModelId">
                  <el-icon><Download /></el-icon> 下载模板
                </el-dropdown-item>
                <el-dropdown-item command="import" :disabled="!selectedModelId">
                  <el-icon><Upload /></el-icon> 导入数据
                </el-dropdown-item>
                <el-dropdown-item command="history" :disabled="!selectedModelId">
                  <el-icon><Clock /></el-icon> 导入历史
                </el-dropdown-item>
                <el-dropdown-item command="export" :disabled="!selectedModelId || instances.length === 0" divided>
                  <el-icon><Download /></el-icon> 导出数据
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>

          <el-button 
            type="primary" 
            @click="handleAdd" 
            :disabled="!selectedModelId"
            class="bg-indigo-600 border-indigo-600 hover:bg-indigo-700"
          >
            <el-icon class="mr-1"><Plus /></el-icon> 新增实例
          </el-button>
        </div>
      </div>

      <!-- Advanced Search Builder -->
      <transition name="el-zoom-in-top">
        <div v-if="showAdvancedSearch && currentModel" class="bg-white p-4 rounded-xl border border-gray-200 shadow-sm">
          <div class="text-sm font-semibold text-gray-700 mb-3 flex items-center justify-between">
            <span>高级筛选</span>
            <el-button type="primary" link size="small" @click="showAdvancedSearch = false">收起</el-button>
          </div>
          <SearchBuilder 
            :attributes="currentModel.attributes" 
            @search="handleAdvancedSearch" 
            @reset="handleAdvancedReset"
          />
        </div>
      </transition>

      <!-- Action Bar for Selection -->
      <transition name="el-fade-in">
        <div v-if="selectedRows.length > 0" class="bg-indigo-50 border border-indigo-100 rounded-lg p-3 flex items-center justify-between">
          <div class="flex items-center gap-2 text-indigo-700 text-sm">
            <el-icon><InfoFilled /></el-icon>
            已选择 <span class="font-bold">{{ selectedRows.length }}</span> 项
          </div>
          <el-button type="danger" size="small" @click="handleBatchDelete" plain>
            批量删除
          </el-button>
        </div>
      </transition>

      <!-- Table -->
      <div class="bg-white rounded-lg border border-gray-200 overflow-hidden">
        <el-table 
          :data="instances" 
          v-loading="loading" 
          stripe 
          style="width: 100%" 
          v-if="currentModel"
          @selection-change="handleSelectionChange"
          :header-cell-style="{ background: '#f8fafc', color: '#475569', fontWeight: '600' }"
          :row-class-name="'hover:bg-gray-50 transition-colors'"
        >
          <el-table-column type="selection" width="50" />
          <el-table-column prop="name" label="名称" width="180" fixed="left">
            <template #default="{ row }">
              <span class="font-medium text-gray-900">{{ row.name }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="code" label="编码" width="150">
            <template #default="{ row }">
              <span class="font-mono text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded">{{ row.code }}</span>
            </template>
          </el-table-column>
          
          <el-table-column prop="status" label="状态" width="100">
            <template #default="{ row }">
              <el-tag :type="STATUS_OPTIONS.find(o => o.value === row.status)?.color || 'info'" size="small">
                {{ STATUS_OPTIONS.find(o => o.value === row.status)?.label || row.status || '规划中' }}
              </el-tag>
            </template>
          </el-table-column>
          
          <el-table-column 
            v-for="attr in displayAttributes" 
            :key="attr.id"
            :prop="attr.name" 
            :label="attr.label" 
            :min-width="140"
          >
            <template #default="{ row }">
              <span class="text-gray-600">{{ formatAttributeValue(row.data?.[attr.name], attr) }}</span>
            </template>
          </el-table-column>
          
          <el-table-column label="操作" width="150" fixed="right">
            <template #default="{ row }">
              <div class="flex items-center gap-2">
                <el-button type="primary" link size="small" @click="handleEdit(row)">编辑</el-button>
                <el-button type="primary" link size="small" @click="handleShowAudit(row)">变更记录</el-button>
                <el-button type="primary" link size="small" @click="$router.push(`/topology?root_id=${row.id}`)">
                  <el-icon><Share /></el-icon>
                </el-button>
                <el-button type="danger" link size="small" @click="handleDelete(row)">删除</el-button>
              </div>
            </template>
          </el-table-column>
        </el-table>

        <el-empty v-else description="请先选择资源类型以查看数据" :image-size="120" />

        <!-- Pagination -->
        <div v-if="currentModel" class="p-4 flex justify-end border-t border-gray-200">
          <el-pagination
            v-model:current-page="pagination.page"
            v-model:page-size="pagination.pageSize"
            :page-sizes="[10, 20, 50, 100]"
            :total="pagination.total"
            layout="total, sizes, prev, pager, next, jumper"
            @size-change="handleSizeChange"
            @current-change="handlePageChange"
          />
        </div>
      </div>
    </div>

    <!-- Edit Dialog -->
    <el-dialog 
      v-model="dialogVisible" 
      :title="dialogTitle" 
      width="800px" 
      destroy-on-close
      class="rounded-xl"
    >
      <el-form ref="formRef" :model="formData" :rules="formRules" label-width="120px" class="py-4">
        <div class="bg-gray-50 p-4 rounded-lg border border-gray-100 mb-6">
          <div class="text-sm font-semibold text-gray-700 mb-4 border-l-4 border-indigo-500 pl-2">基础信息</div>
          <el-row :gutter="24">
            <el-col :span="8">
              <el-form-item label="名称" prop="name">
                <el-input v-model="formData.name" placeholder="请输入名称" />
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item label="编码" prop="code">
                <el-input v-model="formData.code" placeholder="请输入编码" />
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item label="状态" prop="status">
                <el-select v-model="formData.status" placeholder="请选择状态" class="w-full">
                  <el-option 
                    v-for="opt in STATUS_OPTIONS" 
                    :key="opt.value" 
                    :label="opt.label" 
                    :value="opt.value" 
                  />
                </el-select>
              </el-form-item>
            </el-col>
          </el-row>
        </div>
        
        <div v-if="formAttributes.length > 0">
          <div class="text-sm font-semibold text-gray-700 mb-4 border-l-4 border-indigo-500 pl-2">扩展属性</div>
          <el-row :gutter="24">
            <el-col 
              v-for="attr in formAttributes" 
              :key="attr.id" 
              :span="12"
            >
              <el-form-item 
                :label="attr.label" 
                :prop="'data.' + attr.name"
                :rules="attr.is_required ? [{ required: true, message: `请输入${attr.label}`, trigger: 'blur' }] : []"
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
      </el-form>

      <template #footer>
        <div class="flex justify-end gap-3">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" @click="handleSubmit" :loading="submitting" class="bg-indigo-600 border-indigo-600 hover:bg-indigo-700">确定</el-button>
        </div>
      </template>
    </el-dialog>

    <!-- Import Dialog -->
    <el-dialog v-model="importDialogVisible" title="导入数据" width="900px" destroy-on-close class="rounded-xl">
      <el-steps :active="importStep" finish-status="success" simple class="mb-6 bg-gray-50 p-2 rounded-lg">
        <el-step title="上传文件" />
        <el-step title="字段映射" />
        <el-step title="数据预览" />
        <el-step title="导入设置" />
      </el-steps>

      <div v-show="importStep === 0" class="p-4">
        <div class="border-2 border-dashed border-gray-300 rounded-xl p-8 text-center hover:border-indigo-500 transition-colors bg-gray-50">
           <el-upload
            ref="uploadRef"
            :auto-upload="false"
            :limit="1"
            accept=".xlsx,.xls"
            :on-change="handleFileChange"
            :on-exceed="handleExceed"
            drag
            action=""
            class="w-full"
          >
            <el-icon class="text-6xl text-gray-400 mb-4"><UploadFilled /></el-icon>
            <div class="text-gray-600">
              将文件拖到此处，或 <em class="text-indigo-600 font-medium not-italic">点击上传</em>
            </div>
            <template #tip>
              <div class="text-xs text-gray-400 mt-2">只能上传 xlsx/xls 文件，最大支持50000行数据</div>
            </template>
          </el-upload>
        </div>
      </div>

      <div v-show="importStep === 1">
        <el-alert title="请确认文件列与系统字段的映射关系" type="warning" :closable="false" show-icon class="mb-4" />
        <el-table :data="fieldMappingData" border style="width: 100%" height="400">
          <el-table-column prop="systemField" label="系统字段" width="180">
            <template #default="{ row }">
              <span :class="{ 'font-bold text-gray-800': row.required }">
                {{ row.systemLabel }}
                <span v-if="row.required" class="text-red-500">*</span>
              </span>
            </template>
          </el-table-column>
          <el-table-column prop="fileColumn" label="文件列">
            <template #default="{ row }">
              <el-select v-model="row.mappedColumn" placeholder="选择对应列" clearable class="w-full">
                <el-option 
                  v-for="col in previewData.fileColumns" 
                  :key="col" 
                  :label="col" 
                  :value="col" 
                />
              </el-select>
            </template>
          </el-table-column>
          <el-table-column prop="status" label="状态" width="100" align="center">
            <template #default="{ row }">
              <el-tag v-if="row.mappedColumn" type="success" size="small" effect="dark">已映射</el-tag>
              <el-tag v-else-if="row.required" type="danger" size="small" effect="dark">必填</el-tag>
              <el-tag v-else type="info" size="small">可选</el-tag>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <div v-show="importStep === 2">
        <div class="grid grid-cols-4 gap-4 mb-4">
          <div class="bg-gray-50 p-3 rounded border border-gray-200 text-center">
            <div class="text-xs text-gray-500 mb-1">总行数</div>
            <div class="text-lg font-bold text-gray-800">{{ previewData.total || 0 }}</div>
          </div>
          <div class="bg-green-50 p-3 rounded border border-green-200 text-center">
            <div class="text-xs text-green-600 mb-1">预计新增</div>
            <div class="text-lg font-bold text-green-700">{{ previewData.createCount || 0 }}</div>
          </div>
          <div class="bg-amber-50 p-3 rounded border border-amber-200 text-center">
            <div class="text-xs text-amber-600 mb-1">预计更新</div>
            <div class="text-lg font-bold text-amber-700">{{ previewData.updateCount || 0 }}</div>
          </div>
          <div class="bg-red-50 p-3 rounded border border-red-200 text-center">
            <div class="text-xs text-red-600 mb-1">错误行数</div>
            <div class="text-lg font-bold text-red-700">{{ previewData.errorCount || 0 }}</div>
          </div>
        </div>
        
        <el-alert 
          v-if="previewData.errors && previewData.errors.length > 0" 
          type="error" 
          :closable="false" 
          class="mb-4"
        >
          <template #title>发现 {{ previewData.errorCount }} 个错误</template>
          <div class="max-h-24 overflow-y-auto text-xs mt-2">
            <div v-for="(error, idx) in previewData.errors.slice(0, 10)" :key="idx">{{ error }}</div>
            <div v-if="previewData.errors.length > 10">...还有 {{ previewData.errors.length - 10 }} 个错误</div>
          </div>
        </el-alert>
        
        <el-table :data="previewData.data" border style="width: 100%" height="300" size="small">
          <el-table-column prop="name" label="名称" width="120" fixed />
          <el-table-column prop="code" label="编码" width="120" fixed>
            <template #default="{ row }">
              <span>{{ row.code }}</span>
              <el-tag v-if="row._status === 'update'" type="warning" size="small" class="ml-1 scale-75 origin-left">更</el-tag>
              <el-tag v-else type="success" size="small" class="ml-1 scale-75 origin-left">新</el-tag>
            </template>
          </el-table-column>
          <el-table-column 
            v-for="(col, idx) in previewData.columns?.slice(2)" 
            :key="idx"
            :label="col"
            min-width="100"
          >
            <template #default="{ row }">
              {{ row.data?.[getFieldName(col)] || '-' }}
            </template>
          </el-table-column>
          <el-table-column label="状态" width="80" fixed="right" align="center">
            <template #default="{ row }">
              <el-icon v-if="row._errors && row._errors.length > 0" class="text-red-500"><WarningFilled /></el-icon>
              <el-icon v-else class="text-green-500"><CircleCheckFilled /></el-icon>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <div v-show="importStep === 3" class="p-8 max-w-2xl mx-auto">
        <el-form label-position="top">
          <el-form-item label="导入模式">
            <div class="grid grid-cols-1 gap-4 w-full">
              <div 
                class="border rounded-lg p-4 cursor-pointer transition-colors hover:border-indigo-500 flex items-start gap-3"
                :class="importMode === 'upsert' ? 'border-indigo-500 bg-indigo-50' : 'border-gray-200'"
                @click="importMode = 'upsert'"
              >
                <el-radio v-model="importMode" value="upsert" class="mt-1" />
                <div>
                  <div class="font-medium text-gray-900">智能导入 (推荐)</div>
                  <div class="text-xs text-gray-500 mt-1">编码存在则更新，不存在则新增</div>
                </div>
              </div>
               <div 
                class="border rounded-lg p-4 cursor-pointer transition-colors hover:border-indigo-500 flex items-start gap-3"
                :class="importMode === 'create_only' ? 'border-indigo-500 bg-indigo-50' : 'border-gray-200'"
                @click="importMode = 'create_only'"
              >
                <el-radio v-model="importMode" value="create_only" class="mt-1" />
                <div>
                  <div class="font-medium text-gray-900">仅新增</div>
                  <div class="text-xs text-gray-500 mt-1">仅新增数据，遇到重复编码将跳过</div>
                </div>
              </div>
            </div>
          </el-form-item>
          
          <el-form-item label="错误处理">
             <el-radio-group v-model="errorHandling">
              <el-radio value="skip">跳过错误行</el-radio>
              <el-radio value="stop">遇到错误停止</el-radio>
            </el-radio-group>
          </el-form-item>
        </el-form>
      </div>

      <template #footer>
        <div class="flex justify-between w-full">
          <el-button @click="importDialogVisible = false">取消</el-button>
          <div class="flex gap-2">
            <el-button v-if="importStep > 0" @click="importStep--">上一步</el-button>
            <el-button v-if="importStep < 3" type="primary" @click="nextImportStep" :disabled="!importFile" class="bg-indigo-600 border-indigo-600">下一步</el-button>
            <el-button v-if="importStep === 3" type="primary" @click="handleImportSubmit" :loading="importing" class="bg-indigo-600 border-indigo-600">确认导入</el-button>
          </div>
        </div>
      </template>
    </el-dialog>

    <!-- Import Result Dialog -->
    <el-dialog v-model="importResultVisible" title="导入结果" width="600px" class="rounded-xl">
      <div class="text-center py-6">
        <el-icon class="text-5xl text-green-500 mb-4"><CircleCheckFilled /></el-icon>
        <h3 class="text-xl font-bold text-gray-900 mb-2">处理完成</h3>
        <p class="text-gray-500">文件处理结束，以下是详细结果</p>
      </div>
      
      <div class="grid grid-cols-4 gap-4 mb-6 text-center">
        <div class="bg-green-50 p-2 rounded">
          <div class="text-xs text-green-600">新增</div>
          <div class="font-bold text-green-700">{{ importResult.created || 0 }}</div>
        </div>
        <div class="bg-amber-50 p-2 rounded">
          <div class="text-xs text-amber-600">更新</div>
          <div class="font-bold text-amber-700">{{ importResult.updated || 0 }}</div>
        </div>
        <div class="bg-gray-50 p-2 rounded">
          <div class="text-xs text-gray-600">跳过</div>
          <div class="font-bold text-gray-700">{{ importResult.skipped || 0 }}</div>
        </div>
        <div class="bg-red-50 p-2 rounded">
          <div class="text-xs text-red-600">失败</div>
          <div class="font-bold text-red-700">{{ importResult.errors?.length || 0 }}</div>
        </div>
      </div>
      
      <el-alert 
        v-if="importResult.errors && importResult.errors.length > 0" 
        type="error" 
        :closable="false" 
        title="错误详情"
      >
        <div class="max-h-32 overflow-y-auto mt-2 text-xs">
          <div v-for="(error, idx) in importResult.errors" :key="idx" class="mb-1">{{ error }}</div>
        </div>
      </el-alert>
      
      <template #footer>
        <el-button type="primary" @click="importResultVisible = false" class="w-full bg-indigo-600 border-indigo-600">确定</el-button>
      </template>
    </el-dialog>

    <!-- Import History Dialog -->
    <el-dialog v-model="importHistoryVisible" title="导入历史" width="900px" class="rounded-xl">
      <el-table :data="importHistoryList" v-loading="importHistoryLoading" stripe>
        <el-table-column prop="file_name" label="文件名" min-width="200" />
        <el-table-column prop="started_at" label="导入时间" width="180">
          <template #default="{ row }">
            <span class="text-gray-500 text-xs">{{ formatDateTime(row.started_at) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="结果统计" width="220">
          <template #default="{ row }">
            <div class="flex gap-2 text-xs">
              <span class="text-green-600">Add:{{ row.created_count }}</span>
              <span class="text-amber-600">Upd:{{ row.updated_count }}</span>
              <span class="text-red-600">Err:{{ row.error_count }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag v-if="row.status === 'completed'" type="success" size="small" effect="dark">完成</el-tag>
            <el-tag v-else-if="row.status === 'processing'" type="warning" size="small" effect="dark">处理中</el-tag>
            <el-tag v-else-if="row.status === 'failed'" type="danger" size="small" effect="dark">失败</el-tag>
            <el-tag v-else size="small">待处理</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="80" align="center">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="showHistoryDetail(row)">详情</el-button>
          </template>
        </el-table-column>
      </el-table>
      
      <div class="mt-4 flex justify-end">
        <el-pagination
          v-model:current-page="importHistoryPage"
          :page-size="10"
          :total="importHistoryTotal"
          layout="total, prev, pager, next"
          @current-change="loadImportHistory"
        />
      </div>
    </el-dialog>

    <!-- Instance Audit Dialog -->
    <el-dialog v-model="auditDialogVisible" title="变更记录" width="800px" class="rounded-xl">
      <div class="max-h-[600px] overflow-y-auto p-4">
        <el-timeline>
          <el-timeline-item
            v-for="(activity, index) in auditList"
            :key="index"
            :timestamp="formatDateTime(activity.created_at)"
            placement="top"
            :type="activity.operate_type === 'create' ? 'success' : activity.operate_type === 'delete' ? 'danger' : 'primary'"
          >
            <el-card shadow="hover" class="border-gray-200">
              <div class="flex justify-between items-center mb-3 pb-2 border-b border-gray-100">
                <div class="flex items-center gap-2">
                  <el-tag size="small" :type="activity.operate_type === 'create' ? 'success' : activity.operate_type === 'delete' ? 'danger' : 'warning'">
                    {{ activity.operate_type.toUpperCase() }}
                  </el-tag>
                  <span class="text-sm font-medium text-gray-700">操作来源: {{ activity.origin || 'API' }}</span>
                </div>
                <span class="text-xs text-gray-500 flex items-center gap-1">
                  <el-icon><User /></el-icon> {{ activity.created_by || 'Unknown' }}
                </span>
              </div>
              
              <div v-if="activity.changes && activity.changes.length" class="bg-gray-50 rounded-lg p-2">
                <el-table :data="activity.changes" size="small" border style="width: 100%">
                  <el-table-column prop="attribute_name" label="字段" width="150">
                    <template #default="{ row }">
                      <span class="font-mono text-xs">{{ row.attribute_name }}</span>
                    </template>
                  </el-table-column>
                  <el-table-column prop="old_value" label="变更前">
                    <template #default="{ row }">
                      <span class="text-gray-500 break-all">{{ row.old_value || '-' }}</span>
                    </template>
                  </el-table-column>
                  <el-table-column prop="new_value" label="变更后">
                    <template #default="{ row }">
                      <span class="text-gray-900 font-medium break-all">{{ row.new_value || '-' }}</span>
                    </template>
                  </el-table-column>
                </el-table>
              </div>
              <div v-else class="text-gray-400 text-xs italic p-2">
                没有具体的字段变更记录
              </div>
            </el-card>
          </el-timeline-item>
        </el-timeline>
        <el-empty v-if="auditList.length === 0" description="暂无变更记录" />
      </div>
    </el-dialog>
  </PageContainer>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Plus, Download, Upload, UploadFilled, WarningFilled, CircleCheckFilled, Clock, ArrowDown, InfoFilled, Filter, Share, User } from '@element-plus/icons-vue'
import api from '@/api'
import SearchBuilder from '@/components/common/SearchBuilder.vue'

const STATUS_OPTIONS = [
  { label: '规划中', value: 'planning', color: 'info' },
  { label: '建设中', value: 'construction', color: 'warning' },
  { label: '现网', value: 'active', color: 'success' },
  { label: '已退网', value: 'retired', color: 'danger' }
]

const loading = ref(false)
const instances = ref([])
const models = ref<any[]>([])
const selectedModelId = ref(null)
const currentModel = ref<any>(null)
const selectedRows = ref<any[]>([])
const showAdvancedSearch = ref(false)

const importHistoryVisible = ref(false)
const importHistoryList = ref([])
const importHistoryLoading = ref(false)
const importHistoryPage = ref(1)
const importHistoryTotal = ref(0)
const historyDetailVisible = ref(false)
const historyDetail = ref<any>(null)

const auditDialogVisible = ref(false)
const auditList = ref<any[]>([])

const filters = reactive({
  keyword: '',
  advancedFilters: null as any
})

const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0
})

const dialogVisible = ref(false)
const currentInstance = ref<any>(null)
const formData = ref<any>({ name: '', code: '', data: {} })
const formRef = ref(null)
const submitting = ref(false)

const importDialogVisible = ref(false)
const importResultVisible = ref(false)
const uploadRef = ref(null)
const importFile = ref<File | null>(null)
const importing = ref(false)
const importStep = ref(0)
const importMode = ref('upsert')
const errorHandling = ref('skip')
const importResult = ref<any>({ success: 0, created: 0, updated: 0, deleted: 0, skipped: 0, errors: [], total: 0 })
const previewData = ref<any>({ total: 0, createCount: 0, updateCount: 0, errorCount: 0, errors: [], data: [], columns: [], fileColumns: [], sampleData: null })
const fieldMappingData = ref<any[]>([])

const dialogTitle = computed(() => currentInstance.value?.id ? '编辑实例' : '新增实例')

const displayAttributes = computed(() => {
  if (!currentModel.value?.attributes) return []
  return currentModel.value.attributes.slice(0, 5)
})

const formAttributes = computed(() => {
  if (!currentModel.value?.attributes) return []
  return currentModel.value.attributes
})

const formRules = {
  name: [{ required: true, message: '请输入名称', trigger: 'blur' }],
  code: [{ required: true, message: '请输入编码', trigger: 'blur' }]
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

const getFieldName = (label: string) => {
  if (!currentModel.value?.attributes) return label
  const attr = currentModel.value.attributes.find((a: any) => a.label === label)
  return attr?.name || label
}

const formatAttributeValue = (value: any, attr: any) => {
  if (value === null || value === undefined) return '-'
  if (attr.type === 'boolean') return value ? '是' : '否'
  if (attr.type === 'enum' && attr.enum_values) {
    const option = getEnumOptions(attr.enum_values).find(o => o.value === value)
    return option ? option.label : value
  }
  return value
}

const handleSelectionChange = (rows: any[]) => {
  selectedRows.value = rows
}

const loadModels = async () => {
  try {
    const res = await api.get('/v2/models/')
    models.value = res.data
    if (models.value.length > 0 && !selectedModelId.value) {
      selectedModelId.value = models.value[0].id
      await handleModelChange()
    }
  } catch (error) {
    console.error('加载模型列表失败:', error)
  }
}

const handleModelChange = async () => {
  if (!selectedModelId.value) {
    currentModel.value = null
    instances.value = []
    return
  }
  
  try {
    const res = await api.get(`/v2/models/${selectedModelId.value}`)
    currentModel.value = res.data
    pagination.page = 1
    await loadInstances()
  } catch (error) {
    console.error('加载模型详情失败:', error)
  }
}

const loadInstances = async () => {
  if (!selectedModelId.value) return
  
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      page_size: pagination.pageSize,
      model_id: selectedModelId.value,
    }
    if (filters.keyword) {
      (params as any).keyword = filters.keyword
    }
    if (filters.advancedFilters) {
      (params as any).filters = JSON.stringify(filters.advancedFilters)
    }
    
    const res = await api.get('/v1/instances/', { params })
    instances.value = res.data.items || res.data
    pagination.total = res.data.total || instances.value.length
  } catch (error) {
    console.error('加载实例列表失败:', error)
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  pagination.page = 1
  loadInstances()
}

const handleAdvancedSearch = (searchFilters: any[]) => {
  filters.advancedFilters = searchFilters
  pagination.page = 1
  loadInstances()
}

const handleAdvancedReset = () => {
  filters.advancedFilters = null
  pagination.page = 1
  loadInstances()
}

const handleReset = () => {
  filters.keyword = ''
  filters.advancedFilters = null
  handleSearch()
}

const handleSizeChange = () => {
  pagination.page = 1
  loadInstances()
}

const handlePageChange = () => {
  loadInstances()
}

const handleAdd = () => {
  currentInstance.value = null
  formData.value = { name: '', code: '', status: 'planning', data: {} }
  dialogVisible.value = true
}

const handleEdit = (row: any) => {
  currentInstance.value = row
  formData.value = { 
    name: row.name, 
    code: row.code,
    status: row.status || 'planning',
    version: row.version, // Add version for optimistic locking
    data: { ...row.data } || {}
  }
  dialogVisible.value = true
}

const handleDelete = async (row: any) => {
  try {
    await ElMessageBox.confirm('确定要删除该记录吗？', '提示', { type: 'warning' })
    await api.delete(`/v1/instances/${row.id}`)
    ElMessage.success('删除成功')
    loadInstances()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除失败:', error)
    }
  }
}

const handleBatchDelete = async () => {
  if (selectedRows.value.length === 0) {
    ElMessage.warning('请选择要删除的记录')
    return
  }
  
  try {
    await ElMessageBox.confirm(
      `确定要删除选中的 ${selectedRows.value.length} 条记录吗？此操作不可恢复！`, 
      '批量删除确认', 
      { 
        type: 'warning',
        confirmButtonText: '确定删除',
        cancelButtonText: '取消',
        confirmButtonClass: 'el-button--danger'
      }
    )
    
    const ids = selectedRows.value.map(row => row.id)
    await api.post('/v1/instances/batch-delete', ids)
    ElMessage.success(`成功删除 ${selectedRows.value.length} 条记录`)
    selectedRows.value = []
    loadInstances()
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('批量删除失败:', error)
      ElMessage.error(error.response?.data?.detail || '批量删除失败')
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
    const payload = {
      model_id: selectedModelId.value,
      name: formData.value.name,
      code: formData.value.code,
      status: formData.value.status,
      version: formData.value.version, // Pass version to backend
      data: { ...formData.value.data }
    }
    
    if (currentInstance.value?.id) {
      await api.put(`/v1/instances/${currentInstance.value.id}`, payload)
      ElMessage.success('更新成功')
    } else {
      await api.post('/v1/instances/', payload)
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    loadInstances()
  } catch (error: any) {
    console.error('保存失败:', error)
    if (error.response?.status === 409) {
      ElMessage.error('数据已被他人修改，请刷新页面后重试')
      loadInstances() // Auto refresh
    } else {
      ElMessage.error(error.response?.data?.detail || '保存失败')
    }
  } finally {
    submitting.value = false
  }
}

const handleMoreAction = (command: string) => {
  if (command === 'template') handleDownloadTemplate()
  if (command === 'import') handleImport()
  if (command === 'history') handleShowImportHistory()
  if (command === 'export') handleExport()
}

const handleDownloadTemplate = () => {
  window.open(`http://localhost:8000/api/v1/instances/template/${selectedModelId.value}`, '_blank')
}

const handleImport = () => {
  importFile.value = null
  importStep.value = 0
  previewData.value = { total: 0, createCount: 0, updateCount: 0, errorCount: 0, errors: [], data: [], columns: [], fileColumns: [], sampleData: null }
  fieldMappingData.value = []
  importDialogVisible.value = true
}

const handleFileChange = async (file: any) => {
  importFile.value = file.raw
}

const handleExceed = () => {
  ElMessage.warning('只能上传一个文件')
}

const initFieldMapping = () => {
  const mapping: any[] = [
    { systemField: 'name', systemLabel: '名称', mappedColumn: null, required: true },
    { systemField: 'code', systemLabel: '编码', mappedColumn: null, required: true }
  ]
  
  if (currentModel.value?.attributes) {
    currentModel.value.attributes.forEach((attr: any) => {
      mapping.push({
        systemField: attr.name,
        systemLabel: attr.label,
        mappedColumn: null,
        required: attr.is_required
      })
    })
  }
  
  if (previewData.value.fileColumns) {
    mapping.forEach(item => {
      const matched = previewData.value.fileColumns.find((col: string) => {
        const colClean = col.trim().replace(/\*$/, '')
        return colClean === item.systemLabel || colClean === item.systemField
      })
      if (matched) {
        item.mappedColumn = matched
      }
    })
  }
  
  fieldMappingData.value = mapping
}

const nextImportStep = async () => {
  if (importStep.value === 0 && importFile.value) {
    await doPreview()
  }
  
  if (importStep.value === 1) {
    const requiredMapped = fieldMappingData.value.filter((f: any) => f.required).every((f: any) => f.mappedColumn)
    if (!requiredMapped) {
      ElMessage.warning('请映射所有必填字段')
      return
    }
  }
  
  importStep.value++
}

const doPreview = async () => {
  if (!importFile.value) return
  
  try {
    const formDataObj = new FormData()
    formDataObj.append('file', importFile.value)
    
    const res = await api.post(`/v1/instances/preview/${selectedModelId.value}`, formDataObj, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    
    previewData.value = res.data
    
    if (res.data.data && res.data.data.length > 0) {
      const firstRow = res.data.data[0]
      previewData.value.sampleData = {
        '名称': firstRow.name,
        '编码': firstRow.code,
        ...firstRow.data
      }
    }
    
    previewData.value.fileColumns = res.data.columns || []
    
    initFieldMapping()
    
  } catch (error: any) {
    console.error('预览失败:', error)
    ElMessage.error(error.response?.data?.detail || '预览失败')
  }
}

const handleImportSubmit = async () => {
  if (!importFile.value) {
    ElMessage.warning('请选择要导入的文件')
    return
  }
  
  importing.value = true
  try {
    const formDataObj = new FormData()
    formDataObj.append('file', importFile.value)
    
    const res = await api.post(`/v1/instances/import/${selectedModelId.value}?mode=${importMode.value}`, formDataObj, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    
    importResult.value = res.data
    importDialogVisible.value = false
    importResultVisible.value = true
    
    if (res.data.success > 0) {
      loadInstances()
    }
  } catch (error: any) {
    console.error('导入失败:', error)
    ElMessage.error(error.response?.data?.detail || '导入失败')
  } finally {
    importing.value = false
  }
}

const handleExport = () => {
  let url = `http://localhost:8000/api/v1/instances/export/${selectedModelId.value}`
  const params = []
  
  if (filters.keyword) {
    params.push(`keyword=${encodeURIComponent(filters.keyword)}`)
  }
  
  if (selectedRows.value.length > 0) {
    const ids = selectedRows.value.map(r => r.id).join(',')
    params.push(`ids=${ids}`)
  }
  
  if (params.length > 0) {
    url += '?' + params.join('&')
  }
  
  window.open(url, '_blank')
}

const handleShowImportHistory = () => {
  importHistoryPage.value = 1
  loadImportHistory()
  importHistoryVisible.value = true
}

const loadImportHistory = async (page = 1) => {
  importHistoryLoading.value = true
  try {
    const res = await api.get(`/v1/instances/import-history/${selectedModelId.value}`, {
      params: { page, page_size: 10 }
    })
    importHistoryList.value = res.data.items
    importHistoryTotal.value = res.data.total
  } catch (error) {
    console.error('加载导入历史失败:', error)
    ElMessage.error('加载导入历史失败')
  } finally {
    importHistoryLoading.value = false
  }
}

const showHistoryDetail = async (row: any) => {
  try {
    const res = await api.get(`/v1/instances/import-history-detail/${row.id}`)
    historyDetail.value = res.data
    historyDetailVisible.value = true
  } catch (error) {
    console.error('加载详情失败:', error)
    ElMessage.error('加载详情失败')
  }
}

const handleShowAudit = async (row: any) => {
  try {
    const res = await api.get(`/v1/instances/${row.id}/history`)
    auditList.value = res.data.items || []
    auditDialogVisible.value = true
  } catch (error) {
    console.error('加载审计记录失败:', error)
    ElMessage.error('加载审计记录失败')
  }
}

const formatDateTime = (dateStr: string) => {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

onMounted(() => {
  loadModels()
})
</script>
