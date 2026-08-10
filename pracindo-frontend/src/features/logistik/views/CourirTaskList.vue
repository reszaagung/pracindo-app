<!-- src/features/kurir/views/CourierTaskList.vue -->
<template>
    <div class="min-h-screen bg-slate-50 max-w-md mx-auto flex flex-col font-sans relative shadow-2xl">

        <!-- HEADER BIRU -->
        <div
            class="bg-[#5C6BC0] px-6 pt-10 pb-6 shrink-0 flex items-center gap-4 text-white rounded-b-3xl shadow-md relative z-20">
            <button @click="kembali"
                class="w-10 h-10 rounded-full bg-white/20 hover:bg-white/30 flex items-center justify-center backdrop-blur-sm transition-colors active:scale-95">
                <i class="pi pi-arrow-left"></i>
            </button>
            <div>
                <h1 class="text-xl font-bold tracking-wide">Paket dibawa Kurir</h1>
                <p class="text-xs text-indigo-100 mt-0.5">Daftar tugas pengiriman Anda hari ini</p>
            </div>
        </div>

        <!-- KONTEN DAFTAR TUGAS -->
        <div class="flex-1 px-5 pt-6 pb-24 overflow-y-auto custom-scrollbar relative z-10">

            <div v-if="isLoading" class="flex flex-col items-center justify-center py-10 space-y-3">
                <i class="pi pi-spin pi-spinner text-3xl text-[#FF8A65]"></i>
                <p class="text-sm font-medium text-slate-500">Memuat data perjalanan...</p>
            </div>

            <div v-else-if="daftarTugas.length === 0"
                class="flex flex-col items-center justify-center py-16 text-center">
                <div
                    class="w-20 h-20 bg-indigo-50 rounded-full flex items-center justify-center mb-4 border border-indigo-100">
                    <i class="pi pi-check-square text-4xl text-[#5C6BC0]"></i>
                </div>
                <h3 class="text-base font-bold text-slate-800">Semua Tugas Selesai!</h3>
                <p class="text-xs text-slate-500 mt-1">Anda tidak memiliki jadwal pengiriman aktif saat ini.</p>
            </div>

            <!-- List Kartu Tugas -->
            <div v-else class="flex flex-col gap-4">
                <div v-for="tugas in daftarTugas" :key="tugas.id"
                    class="bg-white border border-slate-200 rounded-[20px] p-5 shadow-sm relative overflow-hidden">

                    <!-- Garis Indikator Kiri -->
                    <div class="absolute left-0 top-0 bottom-0 w-1.5" :class="getGarisStatus(tugas.status)"></div>

                    <div class="flex justify-between items-start mb-4">
                        <div>
                            <span class="px-2.5 py-1 rounded-md text-[9px] font-black tracking-widest uppercase border"
                                :class="getBadgeStatus(tugas.status)">
                                {{ tugas.status_label || tugas.status }}
                            </span>
                            <h2 class="text-base font-black text-slate-800 mt-2">{{ tugas.nomor }}</h2>
                            <p class="text-[10px] font-bold text-slate-400 mt-0.5"><i
                                    class="pi pi-truck text-[9px] mr-1"></i> {{ tugas.kendaraan_kode || 'ArmadaInternal'
                                    }}</p>
                        </div>
                    </div>

                    <div class="space-y-3 mb-5">
                        <div class="flex gap-3 items-start p-3 bg-slate-50 rounded-xl border border-slate-100">
                            <i class="pi pi-map-marker text-[#FF8A65] mt-0.5"></i>
                            <div>
                                <p class="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-0.5">Jumlah
                                    Perhentian</p>
                                <p class="text-sm font-bold text-slate-700">{{ tugas.jumlah_perhentian || 0 }} Titik
                                    Pengiriman</p>
                            </div>
                        </div>
                    </div>

                    <!-- Tombol Aksi -->
                    <div class="flex gap-3">
                        <button v-if="tugas.status === 'DISIAPKAN'" @click="berangkatkan(tugas.id)"
                            class="flex-1 py-3 bg-[#5C6BC0] hover:bg-indigo-600 text-white text-xs font-bold rounded-xl shadow-md transition-colors flex justify-center items-center gap-2">
                            <i class="pi pi-play text-[10px]"></i> Mulai Jalan
                        </button>

                        <button v-if="tugas.status === 'BERANGKAT'" @click="bukaDetail(tugas.id)"
                            class="flex-1 py-3 bg-[#FF8A65] hover:bg-[#FF7043] text-white text-xs font-bold rounded-xl shadow-md transition-colors flex justify-center items-center gap-2">
                            <i class="pi pi-list text-[10px]"></i> Lihat Titik Tujuan
                        </button>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useCourier } from '../composables/useCourier'

const router = useRouter()
// Ekstrak state dan fungsi dari composable
const { isLoading, daftarTugas, fetchTugasSaya, berangkatkanPengiriman } = useCourier()

const kembali = () => {
    router.push('/kurir')
}

const berangkatkan = async (id) => {
    if (!confirm('Truk sudah dimuat dan siap berangkat sekarang?')) return

    try {
        await berangkatkanPengiriman(id)
        alert('Keberangkatan dicatat! Hati-hati di jalan.')
        fetchTugasSaya() // Refresh ulang data dari server
    } catch (error) {
        // Ambil pesan error dari backend logistik Django jika tersedia
        const pesan = error.response?.data?.detail || 'Gagal mencatat keberangkatan. Pastikan armada memiliki perhentian.'
        alert(pesan)
    }
}

const bukaDetail = (id) => {
    router.push(`/kurir/tugas/${id}`)
}

// Styling Dinamis
const getBadgeStatus = (status) => {
    if (status === 'DISIAPKAN') return 'bg-slate-100 text-slate-600 border-slate-200'
    if (status === 'BERANGKAT') return 'bg-blue-50 text-blue-600 border-blue-200'
    return 'bg-slate-50 text-slate-500 border-slate-200'
}

const getGarisStatus = (status) => {
    if (status === 'DISIAPKAN') return 'bg-slate-300'
    if (status === 'BERANGKAT') return 'bg-blue-500'
    return 'bg-slate-300'
}

onMounted(() => {
    fetchTugasSaya()
})
</script>

<style scoped>
.max-w-md {
    max-width: 414px !important;
}

@media (min-width: 640px) {
    .max-w-md {
        margin-top: 2rem;
        margin-bottom: 2rem;
        border-radius: 2.5rem;
        overflow: hidden;
        min-height: 800px;
    }
}

.custom-scrollbar::-webkit-scrollbar {
    width: 4px;
}

.custom-scrollbar::-webkit-scrollbar-track {
    background: transparent;
}

.custom-scrollbar::-webkit-scrollbar-thumb {
    background: #cbd5e1;
    border-radius: 999px;
}
</style>