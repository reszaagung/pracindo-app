<template>
    <div class="flex h-screen bg-[#F8FAFC] font-sans text-slate-700 overflow-hidden relative">
        <header class="fixed top-0 left-0 right-0 h-16 bg-white shadow-sm z-30 flex items-center justify-between px-4 border-b border-slate-100">
            <div class="flex items-center gap-3">
                <button @click="toggleSidebar" aria-label="Buka Menu"
                    class="p-2 rounded-xl bg-slate-50 text-slate-600 hover:bg-slate-100 active:bg-slate-200 transition-colors">
                    <i class="pi pi-bars text-xl"></i>
                </button>
                <span @click="kembali" class="font-bold text-slate-800 text-base md:text-lg cursor-pointer hover:text-slate-500 transition-colors">
                    Invoice & Document
                </span>
            </div>
            <button @click="kembali" aria-label="Kembali"
                class="w-9 h-9 bg-slate-900 rounded-xl flex items-center justify-center shadow-md active:scale-95 transition-transform">
                <i class="pi pi-arrow-left text-white text-sm"></i>
            </button>
        </header>

        <div v-if="sidebarAktif" @click="tutupDiMobile" class="fixed inset-0 bg-slate-900/40 backdrop-blur-sm z-40 transition-opacity"></div>

        <aside class="bg-white rounded-3xl shadow-[0_8px_30px_rgba(0,0,0,0.04)] border border-slate-100 flex flex-col items-center py-6 flex-shrink-0 justify-between transition-transform duration-300 ease-in-out fixed top-2 bottom-2 left-2 w-[88px] z-50"
            :class="sidebarAktif ? 'translate-x-0' : '-translate-x-[150%]'">
            <div class="flex flex-col items-center w-full gap-6">
                <nav class="flex flex-col gap-3 w-full px-4 mt-8">
                    <button v-for="item in menu" :key="item.id" :disabled="!item.activate" @click="klikMenu(item)"
                        class="w-12 h-12 rounded-2xl flex items-center justify-center transition-all duration-300 mx-auto"
                        :class="item.activate ? (aktif(item.rute) ? 'bg-slate-900 text-white shadow-md' : 'text-slate-400 hover:bg-slate-50') : 'text-slate-300 cursor-default'">
                        <i :class="['pi', item.ikon, 'text-lg']"></i>
                    </button>
                </nav>
            </div>
            <div class="mt-auto flex flex-col items-center mb-4">
                <button @click="keluar" type="button" aria-label="Keluar Aplikasi"
                    class="w-10 h-10 rounded-xl overflow-hidden cursor-pointer border border-slate-200 hover:border-red-500 bg-white hover:bg-red-50 transition-all shadow-sm flex items-center justify-center">
                    <i class="pi pi-power-off text-slate-400"></i>
                </button>
            </div>
        </aside>

        <main class="flex-1 overflow-y-auto p-4 pt-20 custom-scrollbar relative">
            <div class="mx-auto w-full h-full">
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
import { useNavInvoice } from '@/features/accounting/composables/useNavInvoice'

const route = useRoute()
const router = useRouter()
const { logout } = useAuth()
const { sidebarAktif, toggleSidebar, tutupDiMobile } = useLayout()
const { menu, aktif } = useNavInvoice()

const kembali = () => router.push('/')

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
