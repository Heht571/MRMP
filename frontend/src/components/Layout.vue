<template>
  <div class="h-screen w-full flex overflow-hidden bg-gray-50">
    <!-- Sidebar -->
    <aside 
      class="flex-shrink-0 flex flex-col transition-all duration-300 ease-in-out bg-slate-900 text-white"
      :class="isCollapse ? 'w-16' : 'w-64'"
    >
      <!-- Logo -->
      <div class="h-16 flex items-center justify-center bg-slate-950 shadow-md z-10 relative overflow-hidden">
        <div class="flex items-center gap-3 transition-all duration-300">
          <div class="w-8 h-8 rounded-lg bg-indigo-500 flex items-center justify-center flex-shrink-0 shadow-lg shadow-indigo-500/30">
            <el-icon class="text-white text-lg font-bold"><Monitor /></el-icon>
          </div>
          <div v-show="!isCollapse" class="flex flex-col whitespace-nowrap transition-opacity duration-300">
            <h1 class="font-bold text-lg tracking-wide leading-none text-gray-100">MRMP</h1>
            <span class="text-[10px] text-gray-400 font-medium tracking-wider uppercase mt-1">元资源管理平台</span>
          </div>
        </div>
      </div>

      <!-- Menu -->
      <div class="flex-1 overflow-y-auto overflow-x-hidden custom-scrollbar py-4">
        <el-menu
          :default-active="activeMenu"
          :collapse="isCollapse"
          :collapse-transition="false"
          router
          background-color="transparent"
          text-color="#94a3b8"
          active-text-color="#fff"
          class="border-none !bg-transparent w-full"
        >
          <div class="px-3 mb-2" v-if="!isCollapse">
            <span class="text-xs font-semibold text-gray-500 uppercase tracking-wider pl-3">概览</span>
          </div>

          <el-menu-item index="/" class="menu-item-custom mb-1 mx-2 rounded-lg">
            <el-icon><Odometer /></el-icon>
            <template #title><span>仪表盘</span></template>
          </el-menu-item>

          <div class="px-3 mt-6 mb-2" v-if="!isCollapse">
            <span class="text-xs font-semibold text-gray-500 uppercase tracking-wider pl-3">管理</span>
          </div>

          <el-sub-menu index="meta" popper-class="submenu-popup">
            <template #title>
              <el-icon><Collection /></el-icon>
              <span>元数据管理</span>
            </template>
            <el-menu-item index="/global-attributes" class="submenu-item-custom">
              <el-icon class="text-xs"><Setting /></el-icon>
              <span>全局属性</span>
            </el-menu-item>
            <el-menu-item index="/models" class="submenu-item-custom">
              <el-icon><Files /></el-icon>
              <span>元模型定义</span>
            </el-menu-item>
          </el-sub-menu>

          <el-menu-item index="/instances" class="menu-item-custom mb-1 mx-2 rounded-lg">
            <el-icon><Box /></el-icon>
            <template #title><span>资源实例</span></template>
          </el-menu-item>

          <div class="px-3 mt-6 mb-2" v-if="!isCollapse">
            <span class="text-xs font-semibold text-gray-500 uppercase tracking-wider pl-3">拓扑</span>
          </div>

          <el-sub-menu index="relation" popper-class="submenu-popup">
            <template #title>
              <el-icon><Connection /></el-icon>
              <span>关系引擎</span>
            </template>
            <el-menu-item index="/relation-definitions" class="submenu-item-custom">
              <el-icon><Operation /></el-icon>
              <span>关系定义</span>
            </el-menu-item>
            <el-menu-item index="/instance-relations" class="submenu-item-custom">
              <el-icon><Link /></el-icon>
              <span>实例映射</span>
            </el-menu-item>
          </el-sub-menu>

          <el-menu-item index="/hierarchy" class="menu-item-custom mb-1 mx-2 rounded-lg">
            <el-icon><Share /></el-icon>
            <template #title><span>层级视图</span></template>
          </el-menu-item>

          <el-menu-item index="/topology" class="menu-item-custom mb-1 mx-2 rounded-lg">
            <el-icon><Share /></el-icon>
            <template #title><span>拓扑视图</span></template>
          </el-menu-item>
        </el-menu>
      </div>

      <!-- Collapse Toggle -->
      <div 
        class="h-12 flex items-center justify-center cursor-pointer hover:bg-slate-800 transition-colors border-t border-slate-800"
        @click="toggleCollapse"
      >
        <el-icon :class="['text-gray-400 transition-transform duration-300', isCollapse ? 'rotate-180' : '']">
          <Fold v-if="!isCollapse" />
          <Expand v-else />
        </el-icon>
      </div>
    </aside>

    <!-- Main Content Wrapper -->
    <div class="flex-1 flex flex-col min-w-0 bg-gray-50">
      <!-- Header -->
      <header class="h-16 bg-white border-b border-gray-200 flex items-center justify-between px-6 shadow-sm z-10">
        <!-- Breadcrumb -->
        <div class="flex items-center">
          <el-breadcrumb separator="/" class="text-sm">
            <el-breadcrumb-item :to="{ path: '/' }">首页</el-breadcrumb-item>
            <el-breadcrumb-item v-if="route.path !== '/'">{{ route.meta?.title || '当前页面' }}</el-breadcrumb-item>
          </el-breadcrumb>
        </div>

        <!-- Right Actions -->
        <div class="flex items-center gap-4">
          <el-tooltip content="文档" placement="bottom">
            <div class="w-8 h-8 flex items-center justify-center rounded-full hover:bg-gray-100 cursor-pointer text-gray-500 transition-colors">
              <el-icon><Document /></el-icon>
            </div>
          </el-tooltip>
          
          <el-tooltip content="消息通知" placement="bottom">
            <div class="w-8 h-8 flex items-center justify-center rounded-full hover:bg-gray-100 cursor-pointer text-gray-500 transition-colors relative">
              <el-icon><Bell /></el-icon>
              <span class="absolute top-2 right-2 w-2 h-2 bg-red-500 rounded-full border-2 border-white"></span>
            </div>
          </el-tooltip>

          <div class="h-6 w-px bg-gray-200 mx-1"></div>

          <el-dropdown trigger="click">
            <div class="flex items-center gap-2 cursor-pointer hover:bg-gray-50 py-1 px-2 rounded-md transition-colors">
              <el-avatar :size="32" class="bg-indigo-100 text-indigo-600 font-semibold border border-indigo-200">A</el-avatar>
              <div class="flex flex-col text-right hidden md:flex">
                <span class="text-sm font-medium text-gray-700 leading-none">Admin User</span>
                <span class="text-xs text-gray-500 mt-1">系统管理员</span>
              </div>
              <el-icon class="text-gray-400"><CaretBottom /></el-icon>
            </div>
            <template #dropdown>
              <el-dropdown-menu class="w-40">
                <el-dropdown-item>
                  <el-icon><User /></el-icon> 个人中心
                </el-dropdown-item>
                <el-dropdown-item>
                  <el-icon><Setting /></el-icon> 系统设置
                </el-dropdown-item>
                <el-dropdown-item divided class="text-red-500">
                  <el-icon><SwitchButton /></el-icon> 退出登录
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </header>

      <!-- Main Content -->
      <main class="flex-1 overflow-x-hidden overflow-y-auto bg-gray-50 p-6 relative scroll-smooth">
        <router-view v-slot="{ Component }">
          <transition name="fade-transform" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRoute } from 'vue-router'
import { 
  Collection, Box, User, Setting, Connection, Link, Share, 
  Monitor, Odometer, Files, Operation, Document, Bell, 
  CaretBottom, SwitchButton, Fold, Expand 
} from '@element-plus/icons-vue'

const route = useRoute()
const isCollapse = ref(false)

const activeMenu = computed(() => route.path)

const toggleCollapse = () => {
  isCollapse.value = !isCollapse.value
}
</script>

<style>
/* Custom Menu Styling to override Element Plus defaults for the Sidebar */
.menu-item-custom.is-active {
  @apply bg-indigo-600 text-white !important;
  box-shadow: 0 4px 6px -1px rgba(79, 70, 229, 0.3);
}

.menu-item-custom:hover:not(.is-active) {
  @apply bg-slate-800 text-white !important;
}

.el-menu-item {
  height: 44px !important;
  line-height: 44px !important;
  margin-bottom: 4px;
}

.el-sub-menu__title:hover {
  @apply bg-slate-800 text-white !important;
}

/* Scrollbar hidden for sidebar but scrollable */
.custom-scrollbar::-webkit-scrollbar {
  width: 4px;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  @apply bg-slate-700 rounded;
}
.custom-scrollbar:hover::-webkit-scrollbar-thumb {
  @apply bg-slate-600;
}
</style>
