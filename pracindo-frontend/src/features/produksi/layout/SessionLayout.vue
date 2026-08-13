<template>
    <div class="layout-nav bg-[#F8FAFC] text-slate-700">
        <!-- Header (Mobile Mode) -->
        <header
            class="layout-nav__topbar lg:hidden fixed top-0 left-0 right-0 h-16 bg-white shadow-sm z-30 flex items-center justify-between px-4 border-b border-slate-200">
            <div class="flex items-center gap-3">
                <button @click="toggleSidebar"
                    class="p-2 rounded-xl bg-slate-50 text-indigo-600 hover:bg-slate-100 transition-colors">
                    <i class="pi pi-bars text-xl"></i>
                </button>
                <span class="font-bold text-slate-800 text-base">Operasional Produksi</span>
            </div>
            <button @click="kembaliKeUtama('/')"
                class="w-9 h-9 bg-slate-800 rounded-xl flex items-center justify-center shadow-md active:scale-95 transition-transform">
                <i class="pi pi-home text-white text-sm"></i>
            </button>
        </header>

        <!-- Overlay Gelap (Mobile) -->
        <div v-if="isMobile && sidebarAktif" @click="tutupDiMobile"
            class="fixed inset-0 bg-slate-900/40 backdrop-blur-sm z-40 lg:hidden transition-opacity"></div>

        <!-- Sidebar Utama -->
        <aside :class="[
            'layout-nav__sidebar bg-white shadow-[0_8px_30px_rgb(0,0,0,0.04)] border-r border-slate-200 flex flex-col justify-between py-6 transition-transform duration-300 ease-in-out z-50',
            'fixed top-0 bottom-0 left-0 w-64',
            'lg:relative lg:translate-x-0',
            sidebarAktif ? 'translate-x-0' : '-translate-x-full'
        ]">
            <div class="flex flex-col w-full h-full">
                <div class="px-6 mb-8 hidden lg:flex items-center justify-between">
                    <h2 class="font-black text-slate-800 text-lg uppercase tracking-wider">Produksi</h2>
                    <button @click="kembaliKeUtama('/')" class="text-slate-400 hover:text-indigo-600 transition-colors"
                        title="Kembali ke Dashboard">
                        <i class="pi pi-sign-out"></i>
                    </button>
                </div>

                <nav class="flex-1 px-4 overflow-y-auto custom-scrollbar flex flex-col gap-1.5">
                    <div class="text-[10px] font-black text-slate-400 uppercase tracking-wider px-4 mt-2 mb-1">
                        Operasional Utama</div>

                    <button @click="navigasi('/produksi/mixing')"
                        :class="['w-full text-left px-4 py-3 rounded-xl font-bold text-sm transition-colors flex items-center gap-3',
                            isAktif('/produksi/mixing') ? 'bg-indigo-600 text-white shadow-md' : 'text-slate-500 hover:bg-slate-50 hover:text-slate-800']">
                        <i class="pi pi-bolt"></i> Pengadonan (Mixing)
                    </button>

                    <button @click="navigasi('/produksi/tangki')"
                        :class="['w-full text-left px-4 py-3 rounded-xl font-bold text-sm transition-colors flex items-center gap-3 mt-1',
                            isAktif('/produksi/tangki') ? 'bg-indigo-600 text-white shadow-md' : 'text-slate-500 hover:bg-slate-50 hover:text-slate-800']">
                        <i class="pi pi-database"></i> Monitor Tangki
                    </button>

                    <div class="text-[10px] font-black text-slate-400 uppercase tracking-wider px-4 mt-6 mb-1">Manajemen
                        Sesi</div>

                    <button @click="navigasi('/produksi/sesi')"
                        :class="['w-full text-left px-4 py-3 rounded-xl font-bold text-sm transition-colors flex items-center gap-3 mt-1',
                            isAktif('/produksi/sesi') ? 'bg-indigo-600 text-white shadow-md' : 'text-slate-500 hover:bg-slate-50 hover:text-slate-800']">
                        <i class="pi pi-list"></i> Daftar Sesi
                    </button>

                    <button @click="navigasi('/produksi/sesi/rnd')"
                        :class="['w-full text-left px-4 py-3 rounded-xl font-bold text-sm transition-colors flex items-center gap-3 mt-1',
                            isAktif('/produksi/sesi/rnd') ? 'bg-indigo-600 text-white shadow-md' : 'text-slate-500 hover:bg-slate-50 hover:text-slate-800']">
                        <i class="pi pi-flask"></i> Eksperimen R&D
                    </button>

                    <button @click="navigasi('/produksi/sesi/banding')"
                        :class="['w-full text-left px-4 py-3 rounded-xl font-bold text-sm transition-colors flex items-center gap-3 mt-1',
                            isAktif('/produksi/sesi/banding') ? 'bg-indigo-600 text-white shadow-md' : 'text-slate-500 hover:bg-slate-50 hover:text-slate-800']">
                        <i class="pi pi-chart-bar"></i> Banding Batch
                    </button>

                    <button @click="navigasi('/produksi/sesi/transfer-pool')"
                        :class="['w-full text-left px-4 py-3 rounded-xl font-bold text-sm transition-colors flex items-center gap-3 mt-1',
                            isAktif('/produksi/sesi/transfer-pool') ? 'bg-indigo-600 text-white shadow-md' : 'text-slate-500 hover:bg-slate-50 hover:text-slate-800']">
                        <i class="pi pi-arrow-right-arrow-left"></i> Transfer Pool
                    </button>
                </nav>

                <div class="px-6 pt-6 border-t border-slate-100 mt-4">
                    <div class="text-[10px] text-slate-400 font-semibold uppercase tracking-wider">
                        Sistem ERP • Operasional
                    </div>
                </div>
            </div>
        </aside>

        <!-- Area Konten Dinamis -->
        <main class="layout-nav__main flex-1 overflow-y-auto h-screen relative custom-scrollbar">
            <div class="p-4 pt-20 md:p-6 lg:p-8 lg:pt-8 w-full max-w-7xl mx-auto">
                <div v-if="notifikasi" :class="[
                    'mb-6 p-4 rounded-xl flex items-start justify-between gap-3 shadow-sm animate-fade-in-down border',
                    notifikasi.tipe === 'sukses' ? 'bg-emerald-50 text-emerald-800 border-emerald-200' :
                        notifikasi.tipe === 'galat' ? 'bg-red-50 text-red-800 border-red-200' : 'bg-amber-50 text-amber-800 border-amber-200'
                ]">
                    <div class="flex items-center gap-3">
                        <i
                            :class="['pi text-lg', notifikasi.tipe === 'sukses' ? 'pi-check-circle' : notifikasi.tipe === 'galat' ? 'pi-times-circle' : 'pi-exclamation-triangle']"></i>
                        <p class="text-sm font-semibold">{{ notifikasi.pesan }}</p>
                    </div>
                    <button @click="tutupNotifikasi" class="opacity-60 hover:opacity-100 transition-opacity"><i
                            class="pi pi-times"></i></button>
                </div>

                <router-view v-slot="{ Component }">
                    <transition name="fade" mode="out-in">
                        <component :is="Component" @tampil-notifikasi="setNotifikasi" />
                    </transition>
                </router-view>
            </div>
        </main>
    </div>
</template>

<script setup>
import { useNavSession } from '../composables/useSessionLayout'

// Impor semua state dan metode dari composable
const {
    route, sidebarAktif, isMobile, notifikasi,
    toggleSidebar, tutupDiMobile, navigasi, kembaliKeUtama,
    isAktif, setNotifikasi, tutupNotifikasi
} = useNavSession()
</script>

<style scoped>
.layout-nav {
    display: flex;
    height: 100vh;
    width: 100vw;
    overflow: hidden;
}

.fade-enter-active,
.fade-leave-active {
    transition: opacity 0.2s ease, transform 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
    opacity: 0;
    transform: translateY(4px);
}

.animate-fade-in-down {
    animation: fadeInDown 0.3s ease-out forwards;
}

@keyframes fadeInDown {
    from {
        opacity: 0;
        transform: translateY(-10px);
    }

    to {
        opacity: 1;
        transform: translateY(0);
    }
}

.custom-scrollbar::-webkit-scrollbar {
    width: 6px;
}

.custom-scrollbar::-webkit-scrollbar-thumb {
    background: #cbd5e1;
    border-radius: 3px;
}
</style>