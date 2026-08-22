<script setup>
import { useRouter } from 'vue-router'

const router = useRouter()
const goTo = (path) => router.push(path)
</script>

<template>
    <div class="min-h-screen bg-[#F8FAFC] flex flex-col items-center justify-center p-6 relative overflow-hidden">
        <!-- Efek Latar Belakang -->
        <div class="absolute top-[-10%] left-[-10%] w-96 h-96 bg-blue-400/10 rounded-full blur-3xl"></div>
        <div class="absolute bottom-[-10%] right-[-10%] w-96 h-96 bg-emerald-400/10 rounded-full blur-3xl"></div>

        <div class="max-w-4xl w-full relative z-10">
            <div class="text-center mb-12">
                <div class="w-16 h-16 bg-slate-900 text-white rounded-2xl flex items-center justify-center mx-auto mb-5 shadow-lg shadow-slate-900/20">
                    <i class="pi pi-box text-3xl"></i>
                </div>
                <h1 class="text-3xl md:text-4xl font-extrabold text-slate-800 mb-2 tracking-tight">Pracindo Retail & Keuangan</h1>
                <p class="text-slate-500 font-medium">Pilih ruang kerja yang ingin Anda akses</p>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                <!-- Portal ke Operasional Retail -->
                <button @click="goTo('/retail/pos')" class="bg-white p-6 rounded-[24px] shadow-sm border border-slate-100 hover:shadow-xl hover:border-blue-300 hover:-translate-y-1 transition-all duration-300 group text-left flex flex-col items-start gap-4">
                    <div class="w-14 h-14 bg-blue-50 text-blue-600 rounded-xl flex items-center justify-center shrink-0 group-hover:scale-110 group-hover:bg-blue-600 group-hover:text-white transition-all duration-300">
                        <i class="pi pi-desktop text-xl"></i>
                    </div>
                    <div>
                        <h2 class="text-xl font-bold text-slate-800 mb-1 group-hover:text-blue-600 transition-colors">Operasional Retail</h2>
                        <p class="text-slate-500 text-sm leading-relaxed">Akses mesin kasir (POS), pantau tagihan piutang, dan terima kiriman DO dari gudang.</p>
                    </div>
                </button>

                <!-- Portal ke Akuntansi -->
                <button @click="goTo('/akuntansi/buku-besar')" class="bg-white p-6 rounded-[24px] shadow-sm border border-slate-100 hover:shadow-xl hover:border-emerald-300 hover:-translate-y-1 transition-all duration-300 group text-left flex flex-col items-start gap-4">
                    <div class="w-14 h-14 bg-emerald-50 text-emerald-600 rounded-xl flex items-center justify-center shrink-0 group-hover:scale-110 group-hover:bg-emerald-600 group-hover:text-white transition-all duration-300">
                        <i class="pi pi-calculator text-xl"></i>
                    </div>
                    <div>
                        <h2 class="text-xl font-bold text-slate-800 mb-1 group-hover:text-emerald-600 transition-colors">Akuntansi & Jurnal</h2>
                        <p class="text-slate-500 text-sm leading-relaxed">Pusat pencatatan Buku Besar, riwayat mutasi keuangan, dan entri Jurnal Umum.</p>
                    </div>
                </button>
            </div>
        </div>
    </div>
</template>
