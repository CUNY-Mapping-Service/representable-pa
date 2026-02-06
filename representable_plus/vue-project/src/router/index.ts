import Landing from '@/views/Landing.vue'
import Test from '@/views/Test.vue'
import { createRouter, createWebHashHistory } from 'vue-router'

const routes = [
  { path: '/', component: Landing },
  { path: '/test', component: Test },
]

const router = createRouter({
  history: createWebHashHistory(),
  routes,
})

export default router
