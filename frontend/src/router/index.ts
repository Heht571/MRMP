import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import Layout from '@/components/Layout.vue'

const routes: Array<RouteRecordRaw> = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { title: '登录' }
  },
  {
    path: '/',
    component: Layout,
    children: [
      {
        path: '',
        name: 'Dashboard',
        component: () => import('@/pages/HomePage.vue'),
        meta: { title: '仪表盘', icon: 'Odometer' }
      },
      {
        path: 'global-attributes',
        name: 'GlobalAttributes',
        component: () => import('@/views/GlobalAttributes.vue'),
        meta: { title: '全局属性', icon: 'Setting' }
      },
      {
        path: 'models',
        name: 'Models',
        component: () => import('@/views/Models.vue'),
        meta: { title: '元模型管理', icon: 'Collection' }
      },
      {
        path: 'instances',
        name: 'Instances',
        component: () => import('@/views/Instances.vue'),
        meta: { title: '资源实例', icon: 'Box' }
      },
      {
        path: 'relation-definitions',
        name: 'RelationDefinitions',
        component: () => import('@/views/RelationDefinitions.vue'),
        meta: { title: '关系定义', icon: 'Connection' }
      },
      {
        path: 'instance-relations',
        name: 'InstanceRelations',
        component: () => import('@/views/InstanceRelations.vue'),
        meta: { title: '实例映射', icon: 'Link' }
      },
      {
        path: 'topology',
        name: 'TopologyView',
        component: () => import('@/views/TopologyView.vue'),
        meta: { title: '拓扑视图', icon: 'Share' }
      },
      {
        path: 'hierarchy',
        name: 'HierarchyView',
        component: () => import('@/views/HierarchyView.vue'),
        meta: { title: '资源层级', icon: 'Share' }
      },
      {
        path: 'schema-form-demo',
        name: 'SchemaFormDemo',
        component: () => import('@/views/SchemaFormDemo.vue'),
        meta: { title: '动态表单演示', icon: 'Document' }
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token')
  if (to.name !== 'Login' && !token) {
    next({ name: 'Login' })
  } else {
    next()
  }
})

export default router
