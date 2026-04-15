import { createApp } from 'vue'
import { createPinia } from 'pinia'
import {
  Checked,
  DataAnalysis,
  DocumentChecked,
  Grid,
  House,
  List,
  Lock,
  MagicStick,
  Monitor,
  Plus,
  Star,
  Tickets,
  User,
  Warning
} from '@element-plus/icons-vue'

import App from './App.vue'
import router from './router'
import './assets/main.css'

const app = createApp(App)
const pinia = createPinia()

const iconRegistry = {
  Checked,
  DataAnalysis,
  DocumentChecked,
  Grid,
  House,
  List,
  Lock,
  MagicStick,
  Monitor,
  Plus,
  Star,
  Tickets,
  User,
  Warning
}

Object.entries(iconRegistry).forEach(([key, component]) => {
  app.component(key, component)
})

app.use(pinia)
app.use(router)
app.mount('#app')
