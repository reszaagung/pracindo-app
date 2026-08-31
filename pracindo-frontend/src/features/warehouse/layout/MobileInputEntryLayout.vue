<template>
    <div class="flex h-screen bg-[#F8FAFC] font-sans text-slate-700 overflow-hidden relative w-full max-w-[100vw]">
        <!-- HEADER MOBILE -->
        <header class="fixed top-0 left-0 right-0 h-16 bg-white shadow-sm z-30 flex items-center justify-between px-4 gap-3 border-b border-slate-100 w-full max-w-[100vw]">
            <div class="flex items-center gap-3 min-w-0">
                <a @click="keDashboard" class="p-2 shrink-0 rounded-xl bg-slate-50 text-slate-600 hover:bg-slate-100 active:bg-slate-200 transition-colors cursor-pointer">
                    <i class="pi pi-home text-xl"></i>
                </a>
                <span class="font-bold text-slate-800 text-sm md:text-base truncate">Input Gudang</span>
            </div>
        </header>

        <!-- KONTEN UTAMA (Dengan padding khusus mobile) -->
        <main class="flex-1 overflow-y-auto overflow-x-hidden p-3 pt-20 pb-24 w-full max-w-[100vw] text-sm">
            <div class="mx-auto w-full">
                <router-view v-slot="{ Component }">
                    <transition name="fade" mode="out-in">
                        <component :is="Component" />
                    </transition>
                </router-view>
            </div>
        </main>

        <!-- BOTTOM NAVIGATION -->
        <nav class="fixed bottom-0 left-0 right-0 bg-white border-t border-slate-200 flex justify-around items-end z-40 shadow-[0_-5px_20px_rgba(0,0,0,0.03)] px-1 pb-1 w-full max-w-[100vw]">

            <!-- Menu Input Gudang -->
            <a v-for="menu in menus" :key="menu.id" @click="klikMenu(menu)"
                class="flex flex-col items-center justify-center w-full py-2 transition-colors group cursor-pointer"
                :class="[aktif(menu.rute) ? 'text-slate-900' : 'text-slate-400 hover:text-slate-600', !menu.activate ? 'opacity-50 pointer-events-none' : '']">
                <div class="h-8 w-12 flex items-center justify-center rounded-full mb-0.5 transition-all" :class="aktif(menu.rute) ? 'bg-slate-100 shadow-sm' : ''">
                    <i :class="['pi', menu.ikon, 'text-[1.2rem] transition-transform']"></i>
                </div>
                <span class="text-[10px] font-medium tracking-tight leading-none">{{ menu.label }}</span>
            </a>

            <!-- Keluar -->
            <a @click="keluar" class="flex flex-col items-center justify-center w-full py-2 transition-colors text-slate-400 hover:text-rose-500 cursor-pointer">
                <div class="h-8 w-12 flex items-center justify-center rounded-full mb-0.5"><i class="pi pi-power-off text-[1.2rem]"></i></div>
                <span class="text-[10px] font-medium tracking-tight leading-none">Keluar</span>
            </a>
        </nav>
    </div>
</template>

<script setup>
import { useRouter } from 'vue-router'
import { useAuth } from '@/composables/useAuth'
import { useNavInputEntry } from '../composables/useNavInputEntry'

const router = useRouter()
const { logout } = useAuth()
const { menus, aktif } = useNavInputEntry()

const kembali = () => window.history.length > 2 ? router.back() : router.push('/warehouse')
const keDashboard = () => router.push('/')
const klikMenu = (menu) => { if (menu.activate) router.push(menu.rute) }
const keluar = async () => { await logout(); router.push('/login') }
</script>