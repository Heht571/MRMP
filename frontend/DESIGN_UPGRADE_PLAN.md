# MRMP 前端 Apple 风格改造计划

## 设计系统基础（已完成 ✅）
- [x] `src/styles/design-system.scss` - 设计系统SCSS
- [x] `src/main.ts` - 引入设计系统

## 全局组件（已完成 ✅）
- [x] `src/components/Layout.vue` - 布局框架
- [x] `src/views/Login.vue` - 登录页

## 待改造文件清单

### 第一批：核心页面（优先级高）
- [x] `src/pages/HomePage.vue` - 首页仪表盘
- [x] `src/views/Instances.vue` - 资源实例列表
- [x] `src/views/Models.vue` - 元模型定义
- [x] `src/views/GlobalAttributes.vue` - 全局属性

### 第二批：关系与拓扑
- [x] `src/views/RelationDefinitions.vue` - 关系定义
- [x] `src/views/InstanceRelations.vue` - 实例关系
- [x] `src/views/HierarchyView.vue` - 层级视图
- [x] `src/views/TopologyView.vue` - 拓扑视图

### 第三批：通用组件
- [x] `src/components/PageContainer.vue` - 页面容器
- [x] `src/components/Empty.vue` - 空状态
- [x] `src/components/common/SchemaForm.vue` - 通用表单
- [x] `src/components/common/SearchBuilder.vue` - 搜索构建器
- [x] `src/components/dashboard/StatWidget.vue` - 统计组件
- [x] `src/components/dashboard/ChartWidget.vue` - 图表组件
- [x] `src/components/dashboard/ListWidget.vue` - 列表组件
- [ ] `src/App.vue` - 根组件

---

## 改造原则

1. **移除所有Tailwind类** - 用SCSS替代
2. **卡片无边框** - 使用背景对比区分
3. **Apple Blue (#0071e3)** - 作为唯一强调色
4. **圆角统一** - 按钮8px，卡片12px，输入框11px
5. **深色/浅色交替** - section-dark 类实现
6. **负字间距** - letter-spacing: -0.01em