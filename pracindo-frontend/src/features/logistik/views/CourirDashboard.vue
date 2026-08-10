<!--
  src/features/logistik/views/CourierDashboard.vue
  Dasbor Utama Kurir - Versi Ringkas & Tepat Guna
-->
<template>
    <div class="min-h-screen bg-slate-50 font-sans text-slate-800 flex flex-col">
        <header class="bg-blue-600 rounded-b-[32px] px-6 pt-12 pb-8 shadow-md relative overflow-hidden shrink-0">
            <div class="absolute top-0 right-0 -mr-16 -mt-16 w-64 h-64 rounded-full bg-blue-500 opacity-50"></div>

            <div class="relative z-10 flex justify-between items-center">
                <div>
                    <h1 class="text-2xl font-black text-white mb-1">Budi Santoso</h1>
                    <p class="text-blue-100 font-medium text-sm flex items-center gap-2">
                        <span>User ID: KURIR-001</span>
                        <span class="w-1.5 h-1.5 rounded-full bg-blue-300"></span>
                        <span>L 8821 XA</span>
                    </p>
                </div>
                <div
                    class="w-14 h-14 bg-white/20 backdrop-blur-sm rounded-full flex items-center justify-center border border-white/30 text-white shadow-inner">
                    <i class="pi pi-user text-2xl"></i>
                </div>
            </div>
        </header>

        <main class="flex-1 px-6 -mt-6 relative z-20 pb-8">
            <div class="grid grid-cols-2 gap-4">

                <button @click="$router.push('/kurir/tugas')"
                    class="bg-white p-5 rounded-3xl shadow-sm border border-slate-100 flex flex-col items-center justify-center gap-3 transition-transform active:scale-95 hover:shadow-md h-36">
                    <div class="w-14 h-14 bg-blue-50 rounded-2xl flex items-center justify-center text-blue-600">
                        <i class="pi pi-box text-2xl"></i>
                    </div>
                    <span class="font-bold text-slate-700 text-sm">Tugas Antar</span>
                </button>

                <button @click="$router.push('/kurir/permintaan')"
                    class="bg-white p-5 rounded-3xl shadow-sm border border-slate-100 flex flex-col items-center justify-center gap-3 transition-transform active:scale-95 hover:shadow-md h-36 relative">
                    <div v-if="adaPermintaanPrioritas" class="absolute top-3 right-3 flex h-4 w-4">
                        <span
                            class="animate-ping absolute inline-flex h-full w-full rounded-full bg-rose-400 opacity-75"></span>
                        <span
                            class="relative inline-flex rounded-full h-4 w-4 bg-rose-500 border-2 border-white"></span>
                    </div>

                    <div class="w-14 h-14 bg-rose-50 rounded-2xl flex items-center justify-center text-rose-500">
                        <i class="pi pi-directions text-2xl"></i>
                    </div>
                    <span class="font-bold text-slate-700 text-sm">Permintaan</span>
                </button>
                <button @click="$router.push('/kurir/pengeluaran')"
                    class="bg-white p-5 rounded-3xl shadow-sm border border-slate-100 flex flex-col items-center justify-center gap-3 transition-transform active:scale-95 hover:shadow-md h-36">
                    <div class="w-14 h-14 bg-amber-50 rounded-2xl flex items-center justify-center text-amber-500">
                        <i class="pi pi-receipt text-2xl"></i>
                    </div>
                    <span class="font-bold text-slate-700 text-sm">Pengeluaran</span>
                </button>

                <button @click="$router.push('/kurir/riwayat')"
                    class="bg-white p-5 rounded-3xl shadow-sm border border-slate-100 flex flex-col items-center justify-center gap-3 transition-transform active:scale-95 hover:shadow-md h-36">
                    <div class="w-14 h-14 bg-slate-50 rounded-2xl flex items-center justify-center text-slate-500">
                        <i class="pi pi-history text-2xl"></i>
                    </div>
                    <span class="font-bold text-slate-700 text-sm">Riwayat</span>
                </button>

            </div>

            <div v-if="adaPermintaanPrioritas"
                class="mt-6 bg-rose-50 border border-rose-200 rounded-2xl p-4 flex gap-3 shadow-sm">
                <i class="pi pi-exclamation-triangle text-rose-500 text-xl mt-0.5"></i>
                <div>
                    <h4 class="font-bold text-rose-700 text-sm mb-1">Perhatian!</h4>
                    <p class="text-xs text-rose-600 font-medium leading-relaxed">
                        Ada permintaan pengambilan barang dari Gudang Jakarta (Cat Kaleng & Komponen Mesin). Silakan cek
                        menu Permintaan.
                    </p>
                </div>
            </div>
        </main>
    </div>
</template>

<script setup>
import { ref } from 'vue'
const adaPermintaanPrioritas = ref(true)
</script>