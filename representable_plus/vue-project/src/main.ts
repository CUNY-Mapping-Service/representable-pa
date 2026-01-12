import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { vOnClickOutside } from '@vueuse/components';

import App from './App.vue'
import router from './router'

const app = createApp(App)

app.use(createPinia())
app.use(router)

app.directive('click-outside', vOnClickOutside)
app.mount('#app')
