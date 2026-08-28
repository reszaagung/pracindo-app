<template>
    <div class="flex h-screen bg-[#F8FAFC] font-sans text-slate-700 overflow-hidden relative">
        <aside class="bg-white rounded-3xl shadow-[0_8px_30px_rgb(0,0,0,0.04)] border border-slate-100 flex flex-col items-center py-6 flex-shrink-0 justify-between w-[88px] h-[calc(100vh-2rem)] m-4 z-20">
            <div class="flex flex-col items-center w-full gap-8">
                <div @click="kembali" class="mb-2 cursor-pointer">
                    <div class="w-12 h-12 bg-slate-900 rounded-2xl flex items-center justify-center shadow-md hover:scale-105 transition-transform">
                        <i class="pi pi-arrow-left text-white text-xl"></i>
                    </div>
                </div>
                <nav class="flex flex-col gap-4 w-full px-4">
                    <button v-for="menu in menus" :key="menu.id" :disabled="!menu.activate" @click="klikMenu(menu)"
                        class="w-12 h-12 rounded-2xl flex items-center justify-center transition-all duration-300 relative mx-auto group"
                        :class="menu.activate ? (aktif(menu.rute) ? 'bg-slate-900 text-white shadow-md' : 'text-slate-400 hover:bg-slate-50 hover:text-slate-600') : 'text-slate-300 cursor-default'">
                        <i :class="['pi', menu.ikon, 'text-xl', 'transition-transform', menu.activate ? 'group-hover:scale-110' : '']"></i>
                        <span class="absolute left-16 bg-slate-800 text-white text-xs font-semibold px-3 py-1.5 rounded-lg opacity-0 group-hover:opacity-100 pointer-events-none whitespace-nowrap z-50 shadow-lg transition-opacity">
                            {{ menu.label }}<template v-if="!menu.activate"> (segera)</template>
                        </span>
                    </button>
                </nav>
            </div>
            <div class="mt-auto flex flex-col items-center gap-4 relative mb-4">
                <div class="group relative flex flex-col items-center">
                    <button @click="keDashboard" type="button" class="w-10 h-10 rounded-xl overflow-hidden cursor-pointer border border-slate-200 hover:border-slate-400 bg-white hover:bg-slate-50 transition-all shadow-sm flex items-center justify-center">
                        <i class="pi pi-home text-slate-400 group-hover:text-slate-600 transition-colors"></i>
                    </button>
                    <span class="absolute -top-10 bg-slate-800 text-white text-[11px] font-semibold px-2 py-1 rounded opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none whitespace-nowrap z-50 shadow-lg">Ke Dashboard</span>
                </div>
                <div class="group relative flex flex-col items-center">
                    <button @click="keluar" type="button" class="w-10 h-10 rounded-xl overflow-hidden cursor-pointer border border-rose-100 hover:border-rose-400 bg-white hover:bg-rose-50 transition-all shadow-sm flex items-center justify-center">
                        <i class="pi pi-power-off text-rose-400 group-hover:text-rose-600 transition-colors"></i>
                    </button>
                    <span class="absolute -top-10 bg-rose-600 text-white text-[11px] font-semibold px-2 py-1 rounded opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none whitespace-nowrap z-50 shadow-lg">Keluar</span>
                </div>
            </div>
        </aside>
        <main class="flex-1 overflow-y-auto p-8 custom-scrollbar">
            <div class="mx-auto w-full">
                <router-view v-slot="{ Component }">
                    <transition name="fade" mode="out-in">
                        <component :is="Component" />
                    </transition>
                </router-view>
            </div>
        </main>
    </div>
</template>

<script setup>
import { useRouter } from 'vue-router'
import { useAuth } from '@/composables/useAuth'
import { useNavDistribution } from '../composables/useNavDistribution'

const router = useRouter()
const { logout } = useAuth()
const { menus, aktif } = useNavDistribution()

const kembali = () => {
    if (window.history.length > 2) {
        router.back()
    } else {
        router.push('/warehouse')
    }
}

const keDashboard = () => router.push('/')

const klikMenu = (menu) => {
    if (!menu.activate) return
    router.push(menu.rute)
}

const keluar = async () => {
    await logout()
    router.push('/login')
}
</script>
