import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import axios from 'axios'
import './style.css'

const app = createApp(App)

// 配置axios默认值
axios.defaults.baseURL = 'http://localhost:8002'
axios.defaults.headers.common['Content-Type'] = 'application/json'

app.use(router)
app.mount('#app')
