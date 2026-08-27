import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import './assets/index.css'
import PrimeVue from 'primevue/config'
import Aura from '@primevue/themes/aura'
import 'primeicons/primeicons.css'
import ToastService from 'primevue/toastservice'
import Tooltip from 'primevue/tooltip' // <-- 1. Import Tooltip dari PrimeVue
import './assets/styles/tech-theme.css'
import '@/assets/tema.css'

const app = createApp(App)

app.config.errorHandler = (err, instance, info) => {
    const nama = instance?.$options?.name || instance?.$options?.__name || 'komponen tidak dikenal'
    console.error(`[errorHandler] ${nama} (${info}):`, err)
}

app.use(createPinia())
app.use(router)
app.use(ToastService)

app.use(PrimeVue, {
    theme: {
        preset: Aura,
        options: {
            darkModeSelector: 'none'
        }
    }
})
app.directive('tooltip', Tooltip)

app.mount('#app')
