<template>
  <div class="app-layout">
    <!-- Mobile Overlay -->
    <div
      class="mobile-overlay"
      :class="{ 'mobile-overlay-visible': mobileMenuVisible }"
      @click="closeMobileMenu"
    ></div>

    <!-- Sidebar -->
    <aside
      class="sidebar"
      :class="{
        'sidebar-collapsed': isCollapse,
        'sidebar-mobile-open': mobileMenuVisible
      }"
    >
      <!-- Logo -->
      <div class="sidebar-header">
        <div class="logo-container">
          <div class="logo-icon">
            <el-icon><Monitor /></el-icon>
          </div>
          <div v-show="!isCollapse" class="logo-text">
            <h1 class="logo-title">MRMP</h1>
            <span class="logo-subtitle">元资源管理平台</span>
          </div>
        </div>
        <!-- Mobile Close Button -->
        <div class="mobile-close-btn" @click="closeMobileMenu">
          <el-icon><Close /></el-icon>
        </div>
      </div>

      <!-- Menu -->
      <div class="sidebar-menu">
        <el-menu
          :default-active="activeMenu"
          :collapse="isCollapse"
          :collapse-transition="false"
          router
          class="sidebar-el-menu"
          @select="handleMenuSelect"
        >
          <div class="menu-group-title" v-if="!isCollapse">
            <span>概览</span>
          </div>

          <el-menu-item index="/" class="sidebar-menu-item">
            <el-icon><Odometer /></el-icon>
            <template #title><span>仪表盘</span></template>
          </el-menu-item>

          <div class="menu-group-title" v-if="!isCollapse">
            <span>管理</span>
          </div>

          <el-sub-menu index="meta" popper-class="sidebar-popup">
            <template #title>
              <el-icon><Collection /></el-icon>
              <span>元数据管理</span>
            </template>
            <el-menu-item index="/global-attributes" class="sidebar-submenu-item">
              <el-icon><Setting /></el-icon>
              <span>全局属性</span>
            </el-menu-item>
            <el-menu-item index="/models" class="sidebar-submenu-item">
              <el-icon><Files /></el-icon>
              <span>元模型定义</span>
            </el-menu-item>
          </el-sub-menu>

          <el-menu-item index="/instances" class="sidebar-menu-item">
            <el-icon><Box /></el-icon>
            <template #title><span>资源实例</span></template>
          </el-menu-item>

          <div class="menu-group-title" v-if="!isCollapse">
            <span>拓扑</span>
          </div>

          <el-sub-menu index="relation" popper-class="sidebar-popup">
            <template #title>
              <el-icon><Connection /></el-icon>
              <span>关系引擎</span>
            </template>
            <el-menu-item index="/relation-definitions" class="sidebar-submenu-item">
              <el-icon><Operation /></el-icon>
              <span>关系定义</span>
            </el-menu-item>
            <el-menu-item index="/instance-relations" class="sidebar-submenu-item">
              <el-icon><Link /></el-icon>
              <span>实例映射</span>
            </el-menu-item>
          </el-sub-menu>

          <el-menu-item index="/hierarchy" class="sidebar-menu-item">
            <el-icon><Share /></el-icon>
            <template #title><span>层级视图</span></template>
          </el-menu-item>

          <el-menu-item index="/topology" class="sidebar-menu-item">
            <el-icon><Share /></el-icon>
            <template #title><span>拓扑视图</span></template>
          </el-menu-item>
        </el-menu>
      </div>

      <!-- Collapse Toggle -->
      <div
        class="sidebar-toggle"
        @click="toggleCollapse"
      >
        <el-icon :class="['toggle-icon', isCollapse ? 'rotated' : '']">
          <Fold v-if="!isCollapse" />
          <Expand v-else />
        </el-icon>
      </div>
    </aside>

    <!-- Main Content Wrapper -->
    <div class="main-wrapper">
      <!-- Header -->
      <header class="header">
        <!-- Mobile Menu Toggle -->
        <div class="header-mobile-toggle" @click="openMobileMenu">
          <el-icon><Menu /></el-icon>
        </div>

        <!-- Breadcrumb -->
        <div class="header-left">
          <el-breadcrumb separator="/" class="breadcrumb">
            <el-breadcrumb-item :to="{ path: '/' }">首页</el-breadcrumb-item>
            <el-breadcrumb-item v-if="route.path !== '/'">{{ route.meta?.title || '当前页面' }}</el-breadcrumb-item>
          </el-breadcrumb>
        </div>

        <!-- Right Actions -->
        <div class="header-right">
          <el-tooltip content="文档" placement="bottom">
            <div class="header-icon">
              <el-icon><Document /></el-icon>
            </div>
          </el-tooltip>

          <el-tooltip content="消息通知" placement="bottom">
            <div class="header-icon notification-icon">
              <el-icon><Bell /></el-icon>
              <span class="notification-dot"></span>
            </div>
          </el-tooltip>

          <div class="header-divider"></div>

          <el-dropdown trigger="click">
            <div class="user-dropdown">
              <el-avatar :size="32" class="user-avatar">A</el-avatar>
              <div class="user-info">
                <span class="user-name">Admin User</span>
                <span class="user-role">系统管理员</span>
              </div>
              <el-icon class="user-arrow"><CaretBottom /></el-icon>
            </div>
            <template #dropdown>
              <el-dropdown-menu class="user-dropdown-menu">
                <el-dropdown-item>
                  <el-icon><User /></el-icon> 个人中心
                </el-dropdown-item>
                <el-dropdown-item>
                  <el-icon><Setting /></el-icon> 系统设置
                </el-dropdown-item>
                <el-dropdown-item divided class="logout-item">
                  <el-icon><SwitchButton /></el-icon> 退出登录
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </header>

      <!-- Main Content -->
      <main class="main-content">
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
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import {
  Collection, Box, User, Setting, Connection, Link, Share,
  Monitor, Odometer, Files, Operation, Document, Bell,
  CaretBottom, SwitchButton, Fold, Expand, Menu, Close
} from '@element-plus/icons-vue'

const route = useRoute()
const isCollapse = ref(false)
const mobileMenuVisible = ref(false)

const activeMenu = computed(() => route.path)

const toggleCollapse = () => {
  isCollapse.value = !isCollapse.value
}

const openMobileMenu = () => {
  mobileMenuVisible.value = true
  document.body.style.overflow = 'hidden'
}

const closeMobileMenu = () => {
  mobileMenuVisible.value = false
  document.body.style.overflow = ''
}

const handleMenuSelect = () => {
  // Close mobile menu on menu item selection
  if (window.innerWidth < 768) {
    closeMobileMenu()
  }
}

// Handle window resize
const handleResize = () => {
  if (window.innerWidth >= 768) {
    closeMobileMenu()
  }
}

onMounted(() => {
  window.addEventListener('resize', handleResize)
  // Check initial window size
  if (window.innerWidth < 768) {
    isCollapse.value = true
  }
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  document.body.style.overflow = ''
})
</script>

<style scoped lang="scss">
.app-layout {
  display: flex;
  height: 100vh;
  width: 100vw;
  overflow: hidden;
  background: var(--color-bg-light);
}

// --- Sidebar ---
.sidebar {
  width: 256px;
  height: 100%;
  display: flex;
  flex-direction: column;
  background: var(--color-bg-dark);
  transition: width var(--transition-base), transform var(--transition-base);
  flex-shrink: 0;
  z-index: 100;

  &.sidebar-collapsed {
    width: 64px;
  }
}

.sidebar-header {
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-surface-dark-2);
  position: relative;
  z-index: 10;
}

.mobile-close-btn {
  display: none;
}

.logo-container {
  display: flex;
  align-items: center;
  gap: 12px;
}

.logo-icon {
  width: 32px;
  height: 32px;
  border-radius: var(--radius-md);
  background: var(--color-accent);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  box-shadow: 0 4px 12px rgba(0, 113, 227, 0.3);

  .el-icon {
    color: white;
    font-size: 18px;
  }
}

.logo-text {
  display: flex;
  flex-direction: column;
  white-space: nowrap;
}

.logo-title {
  font-size: 18px;
  font-weight: 700;
  color: var(--color-text-light);
  line-height: 1.2;
  letter-spacing: 0;
}

.logo-subtitle {
  font-size: 10px;
  color: rgba(255, 255, 255, 0.5);
  font-weight: 500;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  margin-top: 2px;
}

.sidebar-menu {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  padding: var(--space-md) 0;

  &::-webkit-scrollbar {
    width: 4px;
  }

  &::-webkit-scrollbar-thumb {
    background: var(--color-surface-dark-1);
    border-radius: 2px;
  }
}

.sidebar-el-menu {
  background: transparent;
  border: none;
}

.menu-group-title {
  padding: var(--space-md) var(--space-md) var(--space-sm);
  font-size: 11px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.4);
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.sidebar-menu-item {
  height: 44px !important;
  line-height: 44px !important;
  margin: 4px var(--space-sm);
  border-radius: var(--radius-md) !important;
  color: rgba(255, 255, 255, 0.7) !important;
  background: transparent !important;

  &:hover {
    background: var(--color-surface-dark-1) !important;
    color: var(--color-text-light) !important;
  }

  &.is-active {
    background: var(--color-accent) !important;
    color: var(--color-text-light) !important;
    box-shadow: 0 4px 12px rgba(0, 113, 227, 0.3);
  }
}

.sidebar-submenu-item {
  border-radius: var(--radius-sm) !important;
  color: rgba(255, 255, 255, 0.7) !important;

  &:hover {
    background: var(--color-surface-dark-1) !important;
  }
}

.sidebar-toggle {
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  border-top: 1px solid var(--color-surface-dark-1);
  transition: background var(--transition-fast);

  &:hover {
    background: var(--color-surface-dark-1);
  }
}

.toggle-icon {
  color: rgba(255, 255, 255, 0.5);
  transition: transform var(--transition-base);

  &.rotated {
    transform: rotate(180deg);
  }
}

// --- Main Wrapper ---
.main-wrapper {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
  background: var(--color-bg-light);
}

.header {
  height: 64px;
  background: var(--color-surface-light);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 var(--space-lg);
  border-bottom: none;
  box-shadow: none;
  z-index: 10;
}

.header-mobile-toggle {
  display: none;
  width: 40px;
  height: 40px;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-md);
  cursor: pointer;
  color: var(--color-text-secondary);
  margin-right: var(--space-sm);

  &:hover {
    background: var(--color-bg-light);
  }
}

.header-left {
  display: flex;
  align-items: center;
}

.breadcrumb {
  font-size: 14px;
}

.header-right {
  display: flex;
  align-items: center;
  gap: var(--space-md);
}

.header-icon {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-circle);
  cursor: pointer;
  color: var(--color-text-secondary);
  transition: background var(--transition-fast);

  &:hover {
    background: var(--color-bg-light);
  }
}

.notification-icon {
  position: relative;
}

.notification-dot {
  position: absolute;
  top: 6px;
  right: 6px;
  width: 8px;
  height: 8px;
  background: var(--color-danger);
  border-radius: var(--radius-circle);
  border: 2px solid var(--color-surface-light);
}

.header-divider {
  width: 1px;
  height: 24px;
  background: rgba(0, 0, 0, 0.1);
}

.user-dropdown {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  cursor: pointer;
  padding: var(--space-xs) var(--space-sm);
  border-radius: var(--radius-md);
  transition: background var(--transition-fast);

  &:hover {
    background: var(--color-bg-light);
  }
}

.user-avatar {
  background: var(--color-accent);
  color: var(--color-text-light);
  font-weight: 600;
  font-size: 14px;
}

.user-info {
  display: flex;
  flex-direction: column;
  text-align: right;
}

.user-name {
  font-size: 14px;
  font-weight: 500;
  color: var(--color-text-dark);
  line-height: 1.2;
}

.user-role {
  font-size: 12px;
  color: var(--color-text-tertiary);
  margin-top: 2px;
}

.user-arrow {
  color: var(--color-text-tertiary);
}

.user-dropdown-menu {
  :deep(.el-dropdown-menu__item) {
    display: flex;
    align-items: center;
    gap: var(--space-sm);
    padding: var(--space-sm) var(--space-md);
  }

  :deep(.logout-item) {
    color: var(--color-danger);
  }
}

.main-content {
  flex: 1;
  overflow-x: hidden;
  overflow-y: auto;
  padding: var(--space-lg);
  background: var(--color-bg-light);
}

// --- Transitions ---
.fade-transform-enter-active,
.fade-transform-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}

.fade-transform-enter-from {
  opacity: 0;
  transform: translateX(-10px);
}

.fade-transform-leave-to {
  opacity: 0;
  transform: translateX(10px);
}

// --- Mobile Overlay ---
.mobile-overlay {
  display: none;
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  z-index: 90;
  opacity: 0;
  transition: opacity var(--transition-base);
}

// ============================================
// Responsive Styles
// ============================================

// Tablet (768px - 1024px)
@media screen and (max-width: 1024px) {
  .sidebar {
    width: 64px;

    &.sidebar-collapsed {
      width: 64px;
    }
  }

  .logo-text,
  .menu-group-title {
    display: none;
  }

  .sidebar-header {
    justify-content: center;
  }

  .sidebar-toggle {
    display: none;
  }
}

// Mobile (< 768px)
@media screen and (max-width: 768px) {
  .app-layout {
    flex-direction: column;
  }

  // Mobile Overlay
  .mobile-overlay {
    display: block;
    pointer-events: none;

    &.mobile-overlay-visible {
      pointer-events: auto;
      opacity: 1;
    }
  }

  // Sidebar - hidden by default on mobile
  .sidebar {
    position: fixed;
    top: 0;
    left: 0;
    height: 100%;
    width: 280px;
    transform: translateX(-100%);
    z-index: 100;

    &.sidebar-mobile-open {
      transform: translateX(0);
    }

    &.sidebar-collapsed {
      width: 280px;
    }
  }

  .sidebar-header {
    justify-content: space-between;
    padding: 0 var(--space-md);
  }

  .mobile-close-btn {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 32px;
    height: 32px;
    border-radius: var(--radius-md);
    cursor: pointer;
    color: rgba(255, 255, 255, 0.7);

    &:hover {
      background: var(--color-surface-dark-1);
    }
  }

  .logo-text {
    display: flex;
  }

  .menu-group-title {
    display: block;
  }

  .sidebar-toggle {
    display: flex;
  }

  // Header
  .header {
    height: 56px;
    padding: 0 var(--space-md);
    position: sticky;
    top: 0;
    background: var(--color-surface-light);
    box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08);
  }

  .header-mobile-toggle {
    display: flex;
  }

  .header-left {
    flex: 1;
    min-width: 0;
  }

  .breadcrumb {
    font-size: 13px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .header-right {
    gap: var(--space-sm);
  }

  .header-icon {
    width: 36px;
    height: 36px;
  }

  .header-divider {
    display: none;
  }

  .user-info {
    display: none;
  }

  .user-arrow {
    display: none;
  }

  .user-dropdown {
    padding: var(--space-xs);
  }

  // Main Content
  .main-content {
    padding: var(--space-md);
    overflow-x: hidden;
  }
}

// Small Mobile (< 480px)
@media screen and (max-width: 480px) {
  .header {
    padding: 0 var(--space-sm);
  }

  .header-mobile-toggle {
    width: 36px;
    height: 36px;
  }

  .main-content {
    padding: var(--space-sm);
  }

  .logo-title {
    font-size: 16px;
  }

  .logo-subtitle {
    display: none;
  }
}
</style>
