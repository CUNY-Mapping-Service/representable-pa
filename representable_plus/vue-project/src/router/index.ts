import Landing from '@/views/Landing.vue'
import Overview from '@/views/Overview.vue'
import Test from '@/views/Test.vue'
import { createRouter, createWebHashHistory } from 'vue-router'

const routes = [
  { path: '/', component: Overview },
  { path: '/landing', component: Landing },
  { path: '/test', component: Test },
]

const router = createRouter({
  history: createWebHashHistory(),
  routes,
})

export default router
