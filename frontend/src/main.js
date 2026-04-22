import { createApp } from 'vue'
import { createPinia } from 'pinia'
import {
  Bell,
  ChatDotRound,
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
  Setting,
  Star,
  Tickets,
  UploadFilled,
  User,
  Warning
} from '@element-plus/icons-vue'

import App from './App.vue'
import router from './router'
import './assets/main.css'

const app = createApp(App)
const pinia = createPinia()

const iconRegistry = {
  Bell,
  ChatDotRound,
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
  Setting,
  Star,
  Tickets,
  UploadFilled,
  User,
  Warning
}

Object.entries(iconRegistry).forEach(([key, component]) => {
  app.component(key, component)
})

app.use(pinia)
app.use(router)
app.mount('#app')
