<template>
    <div class="flex h-screen bg-[#F8FAFC] font-sans text-slate-700 overflow-hidden relative">
        <header class="lg:hidden fixed top-0 left-0 right-0 h-16 bg-white shadow-sm z-30 flex items-center justify-between px-4 border-b border-slate-100">
            <div class="flex items-center gap-3">
                <button @click="toggleSidebar" aria-label="Buka Menu" class="p-2 rounded-xl bg-slate-50 text-slate-600 hover:bg-slate-100 active:bg-slate-200 transition-colors">
                    <i class="pi pi-bars text-xl"></i>
                </button>
                <span @click="kembali" class="font-bold text-slate-800 text-base md:text-lg cursor-pointer hover:text-slate-500 transition-colors">
                    Inventory Monitor
                </span>
            </div>
            <button @click="kembali" aria-label="Kembali" class="w-9 h-9 bg-slate-900 rounded-xl flex items-center justify-center shadow-md active:scale-95 transition-transform">
                <i class="pi pi-arrow-left text-white text-sm"></i>
            </button>
        </header>

        <div v-if="sidebarAktif" @click="tutupDiMobile" class="fixed inset-0 bg-slate-900/40 backdrop-blur-sm z-40 lg:hidden transition-opacity"></div>

        <aside class="bg-white rounded-3xl shadow-[0_8px_30px_rgba(0,0,0,0.04)] border border-slate-100 flex flex-col items-center py-6 flex-shrink-0 justify-between transition-transform duration-300 ease-in-out"
            :class="['lg:relative lg:translate-x-0 lg:w-[88px] lg:h-[calc(100vh-2rem)] lg:m-4 lg:z-20', 'fixed top-2 bottom-2 left-2 w-[88px] z-50', sidebarAktif ? 'translate-x-0' : '-translate-x-[150%]']">

            <div class="flex flex-col items-center w-full gap-6 lg:gap-8">
                <div @click="kembali" title="Kembali ke Dashboard Utama" class="mb-2 cursor-pointer hidden lg:block">
                    <div class="w-12 h-12 bg-slate-900 rounded-2xl flex items-center justify-center shadow-md hover:scale-105 transition-transform">
                        <i class="pi pi-arrow-left text-white text-xl"></i>
                    </div>
                </div>

                <nav class="flex flex-col gap-3 lg:gap-4 w-full px-4">
                    <button v-for="item in menu" :key="item.id" :disabled="!item.activate" @click="klikMenu(item)"
                        class="w-12 h-12 rounded-2xl flex items-center justify-center transition-all duration-300 relative mx-auto group"
                        :class="[item.activate ? (aktif(item.rute) ? 'bg-slate-900 text-white shadow-md' : 'text-slate-400 hover:bg-slate-50 hover:text-slate-600') : 'text-slate-300 cursor-default']">
                        <i :class="['pi', item.ikon, 'text-lg lg:text-xl', 'transition-transform', item.activate ? 'group-hover:scale-110' : '']"></i>
                        <span class="absolute left-16 bg-slate-800 text-white text-[11px] lg:text-xs font-semibold px-3 py-1.5 rounded-lg opacity-0 group-hover:opacity-100 pointer-events-none whitespace-nowrap z-50 shadow-lg transition-opacity">
                            {{ item.label }}<template v-if="!item.activate"> - Segera</template>
                        </span>
                    </button>
                </nav>
            </div>

            <div class="mt-auto flex flex-col items-center gap-4 relative mb-4">
                <div class="group relative flex flex-col items-center">
                    <button @click="keDashboard" type="button" class="w-10 h-10 rounded-xl overflow-hidden cursor-pointer border border-slate-200 hover:border-slate-400 bg-white hover:bg-slate-50 transition-all shadow-sm flex items-center justify-center">
                        <i class="pi pi-home text-slate-400 group-hover:text-slate-600 transition-colors"></i>
                    </button>
                    <span class="absolute -top-10 bg-slate-800 text-white text-[11px] font-semibold px-2 py-1 rounded opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none whitespace-nowrap z-50 shadow-lg">
                        Ke Dashboard
                    </span>
                </div>
                <div class="group relative flex flex-col items-center">
                    <button @click="keluar" type="button" aria-label="Keluar Aplikasi" class="w-10 h-10 rounded-xl overflow-hidden cursor-pointer border border-rose-100 hover:border-rose-400 bg-white hover:bg-rose-50 transition-all shadow-sm flex items-center justify-center">
                        <i class="pi pi-power-off text-rose-400 group-hover:text-rose-600 transition-colors"></i>
                    </button>
                    <span class="absolute -top-10 bg-rose-600 text-white text-[11px] font-semibold px-2 py-1 rounded opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none whitespace-nowrap z-50 shadow-lg">
                        Keluar
                    </span>
                </div>
            </div>
        </aside>

        <main class="flex-1 overflow-y-auto p-4 pt-20 md:p-6 md:pt-24 lg:p-8 custom-scrollbar relative">
            <div class="mx-auto w-full h-full max-w-7xl">
                <router-view v-slot="{ Component, route }">
                    <transition name="fade" mode="out-in">
                        <div :key="route.fullPath" class="w-full h-full">
                            <component :is="Component" />
                        </div>
                    </transition>
                </router-view>
            </div>
        </main>
    </div>
</template>

<script setup>
import { watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuth } from '@/composables/useAuth'
import { useLayout } from '@/composables/useLayout'
import { useNavMonitorLayout } from '../composables/useNavMonitorLayout'

const route = useRoute()
const router = useRouter()
const { logout } = useAuth()
const { sidebarAktif, toggleSidebar, tutupDiMobile } = useLayout()
const { menu, aktif } = useNavMonitorLayout()

const kembali = () => {
    if (window.history.length > 2) {
        router.back()
    } else {
        router.push('/')
    }
}

const keDashboard = () => {
    router.push('/')
    tutupDiMobile()
}

const klikMenu = (item) => {
    if (!item.activate) return
    router.push(item.rute)
    tutupDiMobile()
}

const keluar = async () => {
    await logout()
    router.push('/login')
}

watch(() => route.fullPath, tutupDiMobile)
</script>

<style scoped>
.fade-enter-active, .fade-leave-active { transition: opacity 0.25s ease-out, transform 0.25s ease-out; }
.fade-enter-from { opacity: 0; transform: translateY(10px); }
.fade-leave-to { opacity: 0; transform: translateY(-10px); }
.custom-scrollbar::-webkit-scrollbar { width: 6px; }
.custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
.custom-scrollbar::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 999px; }
.custom-scrollbar::-webkit-scrollbar-thumb:hover { background: #94a3b8; }
@media (prefers-reduced-motion: reduce) {
    .fade-enter-active, .fade-leave-active { transition: none; }
}
</style>
