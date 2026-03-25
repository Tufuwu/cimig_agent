// src/router/index.ts
import { createRouter, createWebHashHistory } from 'vue-router'
import loginView from '../views/loginView.vue'
import registerView from '../views/registerView.vue'

// 定义路由数组类型
const routes = [
  {
    path: '/',
    component: loginView
  },
  {
    path: '/login',
    component: loginView
  },
  {
    path: '/register',
    component: registerView
  }
]

const router = createRouter({
  history: createWebHashHistory(),
  routes
})

export default router