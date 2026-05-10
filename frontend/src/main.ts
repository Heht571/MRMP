import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import App from './App.vue'
import router from './router'
import './styles/design-system.scss'
// import './style.css' // Replaced by design-system.scss
import PageContainer from './components/PageContainer.vue'

const app = createApp(App)

// 注册所有图标
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

// 全局注册 PageContainer
app.component('PageContainer', PageContainer)

app.use(createPinia())
app.use(router)
app.use(ElementPlus)

app.mount('#app')
