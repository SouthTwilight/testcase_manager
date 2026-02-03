import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'  // 添加 Element Plus 样式
import * as ElementPlusIconsVue from '@element-plus/icons-vue'  // 正确导入图标
import App from './App.vue'
import router from './router'

const pinia = createPinia()
const app = createApp(App)

// 注册所有 Element Plus 图标
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
    app.component(key, component)
}

app.use(pinia)
app.use(router)
app.use(ElementPlus)
app.mount('#app')
