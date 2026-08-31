<template>
    <div class="flex h-screen bg-[#F8FAFC] font-sans text-slate-700 overflow-hidden relative">
        <!-- HEADER MOBILE -->
        <header class="fixed top-0 left-0 right-0 h-16 bg-white shadow-sm z-30 flex items-center justify-between px-4 gap-3 border-b border-slate-100">
            <div class="flex items-center gap-3 min-w-0">
                <button @click="keDashboard" class="p-2 shrink-0 rounded-xl bg-slate-50 text-slate-600 hover:bg-slate-100 active:bg-slate-200 transition-colors">
                    <i class="pi pi-home text-xl"></i>
                </button>
                <span class="font-bold text-slate-800 text-base truncate">Input Transaksi</span>
            </div>
            <button @click="kembali" class="w-9 h-9 shrink-0 bg-slate-900 rounded-xl flex items-center justify-center shadow-md active:scale-95 transition-transform">
                <i class="pi pi-arrow-left text-white text-sm"></i>
            </button>
        </header>

        <!-- KONTEN UTAMA (Dengan padding khusus mobile) -->
        <main class="flex-1 overflow-y-auto p-4 pt-20 pb-24 w-full">
            <div class="mx-auto w-full">
                <router-view v-slot="{ Component }">
                    <transition name="fade" mode="out-in">
                        <component :is="Component" />
                    </transition>
                </router-view>
            </div>
        </main>

        <!-- BOTTOM NAVIGATION -->
        <nav class="fixed bottom-0 left-0 right-0 bg-white border-t border-slate-200 flex justify-around items-end z-40 shadow-[0_-5px_20px_rgba(0,0,0,0.03)] px-1 pb-1">
            <!-- Menu Transaksi -->
            <button v-for="menu in transaksi" :key="menu.id" :disabled="!menu.activate" @click="klikMenu(menu)"
                class="flex flex-col items-center justify-center w-full py-2 transition-colors group"
                :class="aktif(menu.rute) ? 'text-slate-900' : 'text-slate-400 hover:text-slate-600'">
                <div class="h-8 w-12 flex items-center justify-center rounded-full mb-0.5 transition-all" :class="aktif(menu.rute) ? 'bg-slate-100 shadow-sm' : ''">
                    <i :class="['pi', menu.ikon, 'text-[1.2rem] transition-transform']"></i>
                </div>
                <span class="text-[10px] font-medium tracking-tight leading-none">{{ menu.label }}</span>
            </button>

            <!-- Keluar -->
            <button @click="keluar" type="button" class="flex flex-col items-center justify-center w-full py-2 transition-colors text-slate-400 hover:text-rose-500">
                <div class="h-8 w-12 flex items-center justify-center rounded-full mb-0.5"><i class="pi pi-power-off text-[1.2rem]"></i></div>
                <span class="text-[10px] font-medium tracking-tight leading-none">Keluar</span>
            </button>
        </nav>
    </div>
</template>

<script setup>
import { useRouter } from 'vue-router'
import { useAuth } from '@/composables/useAuth'
import { useNavTransaksi } from '@/features/accounting/composables/useNavTransaction'

const router = useRouter()
const { logout } = useAuth()
const { transaksi, aktif } = useNavTransaksi()

const kembali = () => window.history.length > 2 ? router.back() : router.push('/')
const keDashboard = () => router.push('/')
const klikMenu = (menu) => { if (menu.activate) router.push(menu.rute) }
const keluar = async () => { await logout(); router.push('/login') }
</script>

<style scoped>
.fade-enter-active, .fade-leave-active { transition: opacity .15s ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
</style>