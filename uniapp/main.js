// 原始main.js + Vuex注入
import App from './App'

// #ifndef VUE3
import Vue from 'vue'
import uView from 'uview-ui'
Vue.use(uView)

// 1. 引入Vuex Store（Vue2）
import store from './store'
Vue.prototype.$store = store  // 全局挂载store
Vue.config.productionTip = false
App.mpType = 'app'
const app = new Vue({
  store,  // 注入Vue实例
  ...App
})
app.$mount()
// #endif

// #ifdef VUE3
import { createSSRApp } from 'vue'
// 1. 引入Vuex Store（Vue3）
import store from './store'
export function createApp() {
  const app = createSSRApp(App)
  app.use(store)  // Vue3挂载store
  return {
    app
  }
}
// #endif