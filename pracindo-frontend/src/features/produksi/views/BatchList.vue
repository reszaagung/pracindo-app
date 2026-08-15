<script setup>
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useBatchList } from '../composables/useBatchList'
import TabelBatch from '../components/TabelBatch.vue'
import { JENIS_BATCH, STATUS_BATCH } from '../constants'
import { useTangki } from '../composables/useTangki'

const router = useRouter()
const { baris, memuat, filter, muatDaftar, hapusDraft, postingDraft } = useBatchList()
const { tangkiList, muatTangki } = useTangki()

onMounted(() => {
    muatTangki()
    muatDaftar()
})

async function konfirmasiHapus(id) {
    if (confirm('Yakin ingin menghapus DRAFT ini secara permanen?')) {
        await hapusDraft(id)
    }
}

async function jalankanPosting(id) {
    if (confirm('Posting dokumen DRAFT ini sekarang? Saldo tangki akan bertambah.')) {
        try {
            await postingDraft(id)
        } catch (e) {
            if (e.konflikSaldo) {
                alert('Gagal: Saldo sumber telah berubah sejak draft ini dibuat. Silakan hapus draft dan buat ulang.')
            }
        }
    }
}
</script>

<template>
    <div class="batch-list max-w-7xl mx-auto pb-10 space-y-6 animate-fade-in">
        <header class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
            <div>
                <div class="text-xs font-medium text-slate-500 mb-1">Portal Produksi &rsaquo; Batch</div>
                <h1 class="text-2xl font-bold text-slate-900 tracking-tight">Riwayat Produksi</h1>
            </div>
            <button @click="router.push({ name: 'produksi-batch-baru' })"
                class="bg-slate-900 hover:bg-slate-800 text-white font-semibold py-2.5 px-5 rounded-xl shadow-sm transition-all active:scale-95 text-sm flex items-center gap-2">
                <i class="pi pi-plus text-xs"></i>
                <span>Buat Batch Baru</span>
            </button>
        </header>

        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div class="bg-white border border-slate-200 rounded-2xl p-5 shadow-[0_2px_10px_rgb(0,0,0,0.02)]">
                <p class="text-[11px] font-bold text-slate-500 uppercase tracking-wider mb-2">Total Produksi Bulan Ini
                </p>
                <h3 class="text-2xl font-bold text-slate-900">0 Kg</h3>
                <p class="text-sm text-slate-500 mt-1">0 dokumen diposting</p>
            </div>
            <div class="bg-white border border-slate-200 rounded-2xl p-5 shadow-[0_2px_10px_rgb(0,0,0,0.02)]">
                <p class="text-[11px] font-bold text-slate-500 uppercase tracking-wider mb-2">Draft Tertunda</p>
                <h3 class="text-2xl font-bold text-slate-900">0</h3>
                <p class="text-sm text-slate-500 mt-1">Belum masuk tangki</p>
            </div>
            <div class="bg-white border border-slate-200 rounded-2xl p-5 shadow-[0_2px_10px_rgb(0,0,0,0.02)]">
                <p class="text-[11px] font-bold text-slate-500 uppercase tracking-wider mb-2">Tangki Aktif</p>
                <h3 class="text-2xl font-bold text-slate-900">{{ tangkiList.length }}</h3>
                <p class="text-sm text-slate-500 mt-1">Siap menampung hasil</p>
            </div>
        </div>

        <div
            class="bg-white border border-slate-200 rounded-2xl shadow-[0_4px_20px_rgb(0,0,0,0.03)] overflow-hidden flex flex-col min-h-[400px]">

            <div
                class="p-5 border-b border-slate-100 flex flex-col lg:flex-row justify-between items-start lg:items-center gap-4 bg-white">
                <div>
                    <h2 class="text-base font-bold text-slate-900">Daftar Batch</h2>
                    <p class="text-xs text-slate-500 mt-0.5">Terbaru di atas</p>
                </div>

                <div class="flex flex-col sm:flex-row items-center gap-3 w-full lg:w-auto">
                    <div class="relative w-full sm:w-64">
                        <i class="pi pi-search absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 text-sm"></i>
                        <input type="text" placeholder="Cari nomor/hasil..."
                            class="w-full pl-9 pr-4 py-2 bg-slate-50 border-transparent focus:bg-white focus:border-slate-300 focus:ring-2 focus:ring-slate-100 rounded-xl text-sm transition-all" />
                    </div>

                    <div class="flex bg-slate-50 p-1 rounded-xl w-full sm:w-auto overflow-x-auto hide-scrollbar">
                        <button
                            class="px-4 py-1.5 text-sm font-semibold bg-white shadow-sm rounded-lg text-slate-900 whitespace-nowrap">Semua</button>
                        <button
                            class="px-4 py-1.5 text-sm font-medium text-slate-500 hover:text-slate-700 whitespace-nowrap transition-colors">Draft</button>
                        <button
                            class="px-4 py-1.5 text-sm font-medium text-slate-500 hover:text-slate-700 whitespace-nowrap transition-colors">Posted</button>
                        <button
                            class="px-4 py-1.5 text-sm font-medium text-slate-500 hover:text-slate-700 whitespace-nowrap transition-colors">Void</button>
                    </div>
                </div>
            </div>

            <!-- Area Tabel Data -->
            <div class="flex-1 bg-white">
                <TabelBatch :baris="baris" :memuat="memuat" @hapus="konfirmasiHapus" @posting="jalankanPosting"
                    @detail="(id) => router.push({ name: 'produksi-batch-detail', params: { id } })" />
            </div>

        </div>
    </div>
</template>

<style scoped>
.animate-fade-in {
    animation: fadeIn 0.3s ease-out forwards;
}

@keyframes fadeIn {
    from {
        opacity: 0;
        transform: translateY(10px);
    }

    to {
        opacity: 1;
        transform: translateY(0);
    }
}

.hide-scrollbar::-webkit-scrollbar {
    display: none;
}

.hide-scrollbar {
    -ms-overflow-style: none;
    scrollbar-width: none;
}
</style>