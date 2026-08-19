<template>
    <div class="flex flex-col w-full animate-fade-in relative">
        <!-- Header -->
        <div class="mb-4 md:mb-6 flex justify-between items-end">
            <div>
                <p class="text-xs text-slate-400 mb-1">
                    <router-link to="/accounting" class="hover:text-slate-700 transition-colors">Portal
                        Akunting</router-link> ›
                    <router-link to="/accounting/input/po"
                        class="hover:text-slate-700 transition-colors">Pembelian</router-link>
                </p>
                <h2 class="text-xl md:text-2xl font-bold text-slate-800 tracking-tight">Purchase Order</h2>
            </div>
            <button @click="tampilModalPO = true"
                class="px-4 py-2 bg-slate-900 hover:bg-slate-800 text-white text-xs font-bold rounded-xl transition-colors flex items-center gap-2 shadow-sm transform hover:-translate-y-0.5">
                <i class="pi pi-plus"></i> Buat PO Baru
            </button>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
            <!-- Stat 1 -->
            <div class="bg-white border border-slate-200 rounded-2xl p-5 shadow-sm">
                <p class="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1">BELUM DITERIMA PENUH</p>
                <h3 class="text-2xl font-black text-slate-800">{{ belumDiterima.length }}</h3>
                <p class="text-xs text-slate-500 mt-2">Menunggu barang datang</p>
            </div>
            <div class="bg-white border border-slate-200 rounded-2xl p-5 shadow-sm">
                <p class="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1">DRAFT</p>
                <h3 class="text-2xl font-black text-slate-800">{{ draftCount }}</h3>
                <p class="text-xs text-slate-500 mt-2">Belum dikirim ke suplier</p>
            </div>
        </div>
        <div class="bg-white border border-slate-200 rounded-[24px] p-4 md:p-6 shadow-sm w-full min-h-[400px]">
            <div
                class="flex flex-col xl:flex-row justify-between items-start xl:items-center gap-4 mb-6 pb-4 border-b border-slate-100">
                <div>
                    <h3 class="text-sm font-bold text-slate-800">Daftar PO</h3>
                    <p class="text-xs text-slate-500">Terbaru di atas</p>
                </div>

                <div class="flex flex-col md:flex-row items-center gap-3 w-full xl:w-auto">
                    <div class="relative w-full md:w-64">
                        <i class="pi pi-search absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 text-xs"></i>
                        <input type="text" v-model="cari" placeholder="Cari nomor/supplier"
                            class="w-full pl-9 pr-4 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs focus:outline-none focus:ring-2 focus:ring-slate-900 text-slate-700" />
                    </div>

                    <div class="flex bg-slate-50 p-1 rounded-xl w-full md:w-auto overflow-x-auto custom-scrollbar">
                        <button
                            v-for="tab in ['semua', 'DRAFT', 'TERKIRIM', 'DISETUJUI', 'DITOLAK', 'SEBAGIAN', 'SELESAI', 'BATAL']"
                            :key="tab" @click="saringStatus = tab.toLowerCase()"
                            :class="saringStatus === tab.toLowerCase() ? 'bg-white text-slate-800 shadow-[0_2px_8px_rgba(0,0,0,0.04)] font-bold' : 'text-slate-500 hover:text-slate-700'"
                            class="px-3 py-1.5 text-xs rounded-lg transition-all whitespace-nowrap capitalize">
                            {{ tab.toLowerCase() }}
                        </button>
                    </div>
                </div>
            </div>

            <div v-if="isLoadingDaftar" class="flex flex-col items-center justify-center py-12 text-center">
                <i class="pi pi-spin pi-spinner text-slate-300 text-2xl mb-3"></i>
                <p class="text-xs text-slate-500">Memuat data...</p>
            </div>

            <div v-else-if="tampil.length === 0" class="flex flex-col items-center justify-center py-12 text-center">
                <div class="w-12 h-12 bg-slate-50 rounded-full flex items-center justify-center mb-3">
                    <i class="pi pi-inbox text-slate-400 text-xl"></i>
                </div>
                <h4 class="text-sm font-bold text-slate-800 mb-1">Tidak ada PO yang cocok</h4>
                <p class="text-xs text-slate-500">Ubah kata kunci pencarian atau tab status.</p>
            </div>

            <div v-else class="overflow-x-auto">
                <table class="w-full text-left text-sm table-fixed">
                    <thead class="text-slate-500 bg-slate-50/50">
                        <tr>
                            <th class="py-3 px-4 font-semibold rounded-tl-xl w-[20%]">No. PO</th>
                            <th class="py-3 px-4 font-semibold w-[15%]">Tanggal</th>
                            <th class="py-3 px-4 font-semibold w-[25%]">Supplier</th>
                            <th class="py-3 px-4 font-semibold w-[15%] text-center">Status</th>
                            <!-- Kolom Aksi Ditambahkan -->
                            <th class="py-3 px-4 font-semibold w-[25%] text-center rounded-tr-xl">Aksi</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr v-for="po in tampil" :key="po.id"
                            class="border-b border-slate-100 hover:bg-slate-50/50 transition-colors">
                            <td class="py-3 px-4 font-bold text-slate-800">{{ po.no_po || po.nomor }}</td>
                            <td class="py-3 px-4 text-slate-600">{{ po.tanggal }}</td>
                            <td class="py-3 px-4 text-slate-700 truncate" :title="po.suplier_nama">{{ po.suplier_nama }}
                            </td>
                            <td class="py-3 px-4 text-center">
                                <span :class="badgeColor(po.status)"
                                    class="px-2.5 py-1 rounded-full text-[10px] font-bold tracking-wide uppercase">
                                    {{ po.status }}
                                </span>
                            </td>

                            <!-- Kolom Aksi -->
                            <td class="py-3 px-4 text-center">
                                <div class="flex items-center justify-center gap-1.5">

                                    <!-- Muncul KHUSUS jika status DRAFT -->
                                    <template v-if="po.status === 'DRAFT'">
                                        <button @click="handleKirim(po.id)" title="Kirim ke Suplier" class="px-2.5 py-1.5 bg-blue-50 text-blue-600 hover:bg-blue-600 hover:text-white rounded-lg text-[11px] font-bold transition-colors">
                                            <i class="pi pi-send text-[10px] mr-1"></i> Kirim
                                        </button>
                                        <button @click="handleBatal(po.id)" title="Batalkan PO" class="px-2.5 py-1.5 bg-red-50 text-red-600 hover:bg-red-600 hover:text-white rounded-lg text-[11px] font-bold transition-colors">
                                            <i class="pi pi-times text-[10px]"></i>
                                        </button>
                                    </template>

                                    <!-- Tombol Detail (muncul di semua status) -->
                                    <button class="px-2.5 py-1.5 bg-slate-100 text-slate-600 hover:bg-slate-800 hover:text-white rounded-lg text-[11px] font-bold transition-colors tooltip-trigger">
                                        <i class="pi pi-eye text-[10px] mr-1"></i> Detail
                                    </button>

                                </div>
                            </td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>

        <Dialog v-model:visible="tampilModalPO" modal header="Buat Purchase Order Baru"
            :style="{ width: '90vw', maxWidth: '1000px' }" class="p-fluid">
            <LazyFormPO v-if="tampilModalPO" @close="tampilModalPO = false" @saved="poBerhasilDisimpan" />
        </Dialog>
    </div>
</template>

<script setup>
import { onMounted, ref, defineAsyncComponent } from 'vue'
import Dialog from 'primevue/dialog'
import { usePurchaseOrder } from '@/features/accounting/composables/usePurchaseOrder'

const LazyFormPO = defineAsyncComponent(() =>
    import('@/features/accounting/views/ProcurementCreate.vue')
)

const tampilModalPO = ref(false)

const {
    daftarPO, isLoadingDaftar, cari, saringStatus, tampil,
    belumDiterima, draftCount, muatDaftarPO,
    kirimPO, batalkanPO // <-- Panggil fungsi API yang baru ditambahkan
} = usePurchaseOrder()

onMounted(() => {
    muatDaftarPO()
})

const poBerhasilDisimpan = () => {
    tampilModalPO.value = false
    muatDaftarPO()
}

// Handler Kirim PO
const handleKirim = async (id) => {
    if(confirm('Kirim PO ini ke Suplier? Status akan menjadi TERKIRIM dan item pesanan tidak bisa diubah lagi.')) {
        const res = await kirimPO(id)
        if (res.success) alert('Purchase Order berhasil dikirim.')
    }
}

// Handler Batalkan PO
const handleBatal = async (id) => {
    const alasan = prompt('Masukkan alasan membatalkan dokumen PO ini:')
    if(alasan !== null) { // Memastikan user tidak menekan 'Cancel' pada prompt
        if(alasan.trim().length < 5) {
            alert('Alasan pembatalan terlalu pendek! Minimal 5 karakter.')
            return
        }
        const res = await batalkanPO(id, alasan)
        if (res.success) alert('Purchase Order berhasil dibatalkan.')
    }
}

const badgeColor = (status) => {
    const st = String(status).toUpperCase()
    if (st === 'DRAFT') return 'bg-slate-100 text-slate-600'
    if (st === 'TERKIRIM') return 'bg-blue-50 text-blue-600'
    if (st === 'DISETUJUI') return 'bg-emerald-50 text-emerald-600 border border-emerald-200'
    if (st === 'DITOLAK') return 'bg-red-50 text-red-600'
    if (st === 'SEBAGIAN') return 'bg-amber-50 text-amber-600'
    if (st === 'SELESAI') return 'bg-emerald-50 text-emerald-600'
    if (st === 'BATAL') return 'bg-red-100 text-red-700'
    return 'bg-slate-100 text-slate-600'
}
</script>

<style scoped>
/* ... (Style tetap sama) ... */
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

.custom-scrollbar::-webkit-scrollbar {
    height: 4px;
}

.custom-scrollbar::-webkit-scrollbar-track {
    background: transparent;
}

.custom-scrollbar::-webkit-scrollbar-thumb {
    background: #cbd5e1;
    border-radius: 4px;
}
</style>
