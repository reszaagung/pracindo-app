<template>
    <div class="flex h-screen bg-[#F8FAFC] font-sans text-slate-700 overflow-hidden relative">
        <!-- Header Mobile -->
        <header class="lg:hidden fixed top-0 left-0 right-0 h-16 bg-white shadow-sm z-30 flex items-center justify-between px-4 border-b border-slate-100">
            <div class="flex items-center gap-3">
                <button @click="toggleSidebar" class="p-2 rounded-xl bg-slate-50 text-slate-600 hover:bg-slate-100 transition-colors">
                    <i class="pi pi-bars text-xl"></i>
                </button>
                <span class="font-bold text-slate-800 text-base md:text-lg">Modul Akuntansi</span>
            </div>
            <button @click="kembali" class="w-9 h-9 bg-slate-900 rounded-xl flex items-center justify-center shadow-md">
                <i class="pi pi-arrow-left text-white text-sm"></i>
            </button>
        </header>

        <div v-if="isMobile && sidebarAktif" @click="tutupDiMobile" class="fixed inset-0 bg-slate-900/40 backdrop-blur-sm z-40 lg:hidden"></div>

        <!-- Sidebar Navigasi Akuntansi -->
        <aside class="bg-white rounded-3xl shadow-[0_8px_30px_rgb(0,0,0,0.04)] border border-slate-100 flex flex-col items-center py-6 flex-shrink-0 justify-between transition-transform duration-300 ease-in-out"
            :class="['lg:relative lg:translate-x-0 lg:w-[88px] lg:h-[calc(100vh-2rem)] lg:m-4 lg:z-20', 'fixed top-2 bottom-2 left-2 w-[88px] z-50', sidebarAktif ? 'translate-x-0' : '-translate-x-[150%]']">
            <div class="flex flex-col items-center w-full gap-6 lg:gap-8">
                <div @click="kembali" class="mb-2 cursor-pointer hidden lg:block">
                    <div class="w-12 h-12 bg-slate-900 rounded-2xl flex items-center justify-center shadow-md hover:scale-105 transition-transform">
                        <i class="pi pi-arrow-left text-white text-xl"></i>
                    </div>
                </div>
                <nav class="flex flex-col gap-3 lg:gap-4 w-full px-4">
                    <button v-for="menu in menuAkuntansi" :key="menu.id" @click="klikMenu(menu)"
                        class="w-12 h-12 rounded-2xl flex items-center justify-center transition-all duration-300 relative mx-auto group"
                        :class="aktif(menu.rute) ? 'bg-slate-900 text-white shadow-md' : 'text-slate-400 hover:bg-slate-50 hover:text-slate-600'">
                        <i :class="['pi', menu.ikon, 'text-lg lg:text-xl']"></i>
                        <span class="absolute left-16 bg-slate-800 text-white text-xs font-semibold px-3 py-1.5 rounded-lg opacity-0 group-hover:opacity-100 pointer-events-none whitespace-nowrap z-50 shadow-lg transition-opacity">
                            {{ menu.label }}
                        </span>
                    </button>
                </nav>
            </div>
        </aside>

        <main class="flex-1 overflow-y-auto p-4 pt-20 md:p-6 md:pt-24 lg:p-8 custom-scrollbar">
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
import { watch } from 'vue'
import { useRoute } from 'vue-router'
import { useLayout } from '@/composables/useLayout'
import { useNavAkuntingLayout } from '../composables/useNavAkuntingLayout'

const route = useRoute()
const { sidebarAktif, isMobile, toggleSidebar, tutupDiMobile } = useLayout()
const { menuAkuntansi, aktif, kembali, klikMenu } = useNavAkuntingLayout()
watch(() => route.fullPath, tutupDiMobile)
</script>

<style scoped>
.fade-enter-active, .fade-leave-active { transition: opacity .15s ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
.custom-scrollbar::-webkit-scrollbar { width: 6px; }
.custom-scrollbar::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 3px; }
</style>
