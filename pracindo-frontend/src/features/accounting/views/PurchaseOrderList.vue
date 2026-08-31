<template>
    <div class="flex flex-col w-full animate-fade-in relative">
        <!-- HEADER -->
        <div class="mb-4 md:mb-6 flex flex-col sm:flex-row justify-between items-start sm:items-end gap-4">
            <div>
                <p class="text-xs text-slate-400 mb-1">
                    <router-link to="/accounting" class="hover:text-slate-700 transition-colors">Portal Akunting</router-link> ›
                    <router-link to="/accounting/input/po" class="hover:text-slate-700 transition-colors">Pembelian</router-link>
                </p>
                <h2 class="text-xl md:text-2xl font-bold text-slate-800 tracking-tight">Purchase Order</h2>
            </div>
            <button @click="tampilModalPO = true"
                class="w-full sm:w-auto px-4 py-2 bg-slate-900 hover:bg-slate-800 text-white text-xs font-bold rounded-xl transition-colors flex items-center justify-center gap-2 shadow-sm transform hover:-translate-y-0.5">
                <i class="pi pi-plus"></i> Buat PO Baru
            </button>
        </div>

        <!-- KARTU STATISTIK -->
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-6">
            <div class="bg-white border border-slate-200 rounded-2xl p-5 shadow-sm">
                <p class="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1">BELUM DITERIMA PENUH</p>
                <h3 class="text-2xl font-black text-slate-800">{{ belumDiterima.length }}</h3>
                <p class="text-xs text-slate-500 mt-2">Menunggu barang datang</p>
            </div>
            <div class="bg-white border border-slate-200 rounded-2xl p-5 shadow-sm">
                <p class="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1">DRAFT</p>
                <h3 class="text-2xl font-black text-slate-800">{{ draftCount }}</h3>
                <p class="text-xs text-slate-500 mt-2">Belum diajukan / dikirim</p>
            </div>
        </div>

        <!-- PANEL TABEL UTAMA -->
        <div class="bg-white border border-slate-200 rounded-[24px] p-4 md:p-6 shadow-sm w-full min-h-[400px]">
            
            <!-- TOOLBAR PENCARIAN & FILTER -->
            <div class="flex flex-col xl:flex-row justify-between items-start xl:items-center gap-4 mb-6 pb-4 border-b border-slate-100">
                <div class="hidden xl:block">
                    <h3 class="text-sm font-bold text-slate-800">Daftar PO</h3>
                    <p class="text-xs text-slate-500">Terbaru di atas</p>
                </div>

                <div class="flex flex-col md:flex-row items-center gap-3 w-full xl:w-auto">
                    <!-- Pencarian -->
                    <div class="relative w-full md:w-64 shrink-0">
                        <i class="pi pi-search absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 text-xs"></i>
                        <input type="text" v-model="cari" placeholder="Cari nomor/supplier"
                            class="w-full pl-9 pr-4 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs focus:outline-none focus:ring-2 focus:ring-slate-900 text-slate-700" />
                    </div>

                    <!-- Filter Status -->
                    <div class="flex bg-slate-50 p-1 rounded-xl w-full overflow-x-auto custom-scrollbar">
                        <button
                            v-for="tab in ['semua', 'DRAFT', 'PENDING', 'APPROVED', 'TERKIRIM', 'DISETUJUI', 'DITOLAK', 'SEBAGIAN', 'SELESAI', 'BATAL']"
                            :key="tab" @click="saringStatus = tab.toLowerCase()"
                            :class="saringStatus === tab.toLowerCase() ? 'bg-white text-slate-800 shadow-[0_2px_8px_rgba(0,0,0,0.04)] font-bold' : 'text-slate-500 hover:text-slate-700'"
                            class="px-3 py-1.5 text-xs rounded-lg transition-all whitespace-nowrap capitalize shrink-0">
                            {{ tab.toLowerCase() }}
                        </button>
                    </div>
                </div>
            </div>

            <!-- STATE: LOADING -->
            <div v-if="isLoadingDaftar" class="flex flex-col items-center justify-center py-12 text-center">
                <i class="pi pi-spin pi-spinner text-slate-300 text-2xl mb-3"></i>
                <p class="text-xs text-slate-500">Memuat data...</p>
            </div>

            <!-- STATE: KOSONG -->
            <div v-else-if="tampil.length === 0" class="flex flex-col items-center justify-center py-12 text-center">
                <div class="w-12 h-12 bg-slate-50 rounded-full flex items-center justify-center mb-3">
                    <i class="pi pi-inbox text-slate-400 text-xl"></i>
                </div>
                <h4 class="text-sm font-bold text-slate-800 mb-1">Tidak ada PO yang cocok</h4>
                <p class="text-xs text-slate-500">Ubah kata kunci pencarian atau tab status.</p>
            </div>

            <!-- STATE: ADA DATA (TABEL RESPONSIVE) -->
            <div v-else class="overflow-x-auto custom-scrollbar pb-2">
                <table class="w-full text-left text-sm min-w-[1000px]">
                    <thead class="text-slate-500 bg-slate-50/50">
                        <tr>
                            <th class="py-3 px-4 font-semibold rounded-tl-xl w-[18%]">No. PO</th>
                            <th class="py-3 px-4 font-semibold w-[12%]">Tanggal</th>
                            <th class="py-3 px-4 font-semibold w-[20%]">Supplier</th>
                            <th class="py-3 px-4 font-semibold w-[15%] text-center">Status</th>
                            <th class="py-3 px-4 font-semibold w-[22%] text-center">Aksi</th>
                            <th class="py-3 px-4 font-semibold w-[13%] text-center rounded-tr-xl">Detail</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr v-for="po in tampil" :key="po.id" class="border-b border-slate-100 hover:bg-slate-50/50 transition-colors">
                            <td class="py-3 px-4 font-bold text-slate-800 whitespace-nowrap">{{ po.no_po || po.nomor }}</td>
                            <td class="py-3 px-4 text-slate-600 whitespace-nowrap">{{ po.tanggal }}</td>
                            <td class="py-3 px-4 text-slate-700 truncate max-w-[200px]" :title="po.suplier_nama">
                                {{ po.suplier_nama }}
                            </td>
                            <td class="py-3 px-4 text-center">
                                <span :class="badgeColor(po.status)" class="px-2.5 py-1 rounded-full text-[10px] font-bold tracking-wide uppercase whitespace-nowrap">
                                    {{ po.status }}
                                </span>
                            </td>

                            <!-- KOLOM AKSI -->
                            <td class="py-3 px-4 text-center">
                                <div class="flex items-center justify-center gap-1.5">
                                    
                                    <!-- AKSI DRAFT -->
                                    <template v-if="po.status === 'DRAFT'">
                                        <button @click="unduhDokumenPO(po.id, po.no_po)" title="Cetak Draf" class="px-2.5 py-1.5 bg-slate-100 text-slate-600 hover:bg-slate-700 hover:text-white rounded-lg text-[11px] font-bold transition-colors flex items-center">
                                            <i class="pi pi-print text-[10px] mr-1"></i> Cetak
                                        </button>
                                        <button @click="handleAjukan(po.id)" title="Ajukan ke Manajer" class="px-2.5 py-1.5 bg-blue-50 text-blue-600 hover:bg-blue-600 hover:text-white rounded-lg text-[11px] font-bold transition-colors flex items-center">
                                            <i class="pi pi-send text-[10px] mr-1"></i> Ajukan
                                        </button>
                                        <button @click="handleBatal(po.id)" title="Batalkan PO" class="px-2.5 py-1.5 bg-red-50 text-red-600 hover:bg-red-600 hover:text-white rounded-lg text-[11px] font-bold transition-colors flex items-center">
                                            <i class="pi pi-trash text-[10px]"></i>
                                        </button>
                                    </template>

                                    <!-- AKSI PENDING -->
                                    <template v-else-if="po.status === 'PENDING'">
                                        <button @click="handleSetujui(po.id)" title="Setujui PO" class="px-2.5 py-1.5 bg-emerald-50 text-emerald-600 hover:bg-emerald-600 hover:text-white rounded-lg text-[11px] font-bold transition-colors flex items-center">
                                            <i class="pi pi-check text-[10px] mr-1"></i> Setuju
                                        </button>
                                        <button @click="handleTolak(po.id)" title="Tolak PO" class="px-2.5 py-1.5 bg-orange-50 text-orange-600 hover:bg-orange-600 hover:text-white rounded-lg text-[11px] font-bold transition-colors flex items-center">
                                            <i class="pi pi-times text-[10px]"></i>
                                        </button>
                                    </template>

                                    <!-- AKSI APPROVED -->
                                    <template v-else-if="po.status === 'APPROVED'">
                                        <button @click="unduhDokumenPO(po.id, po.no_po)" title="Cetak PO" class="px-2.5 py-1.5 bg-slate-100 text-slate-600 hover:bg-slate-700 hover:text-white rounded-lg text-[11px] font-bold transition-colors flex items-center">
                                            <i class="pi pi-print text-[10px]"></i>
                                        </button>
                                        <button @click="handleKirim(po.id)" title="Kirim ke Suplier" class="px-2.5 py-1.5 bg-indigo-50 text-indigo-600 hover:bg-indigo-600 hover:text-white rounded-lg text-[11px] font-bold transition-colors flex items-center">
                                            <i class="pi pi-envelope text-[10px] mr-1"></i> Kirim
                                        </button>
                                        <button @click="handleBatal(po.id)" title="Batalkan PO" class="px-2.5 py-1.5 bg-red-50 text-red-600 hover:bg-red-600 hover:text-white rounded-lg text-[11px] font-bold transition-colors flex items-center">
                                            <i class="pi pi-trash text-[10px]"></i>
                                        </button>
                                    </template>

                                    <!-- AKSI TERKIRIM / SEBAGIAN (Bisa Cetak & Tutup S) -->
                                    <template v-else-if="['TERKIRIM', 'SEBAGIAN'].includes(po.status)">
                                        <button @click="unduhDokumenPO(po.id, po.no_po)" title="Cetak PO" class="px-2.5 py-1.5 bg-indigo-50 text-indigo-600 hover:bg-indigo-600 hover:text-white rounded-lg text-[11px] font-bold transition-colors flex items-center">
                                            <i class="pi pi-print text-[10px] mr-1"></i> Cetak
                                        </button>
                                        <button @click="handleTutupPaksa(po.id)" title="Selesaikan & Tutup Paksa PO" class="px-2.5 py-1.5 bg-orange-50 text-orange-600 hover:bg-orange-600 hover:text-white rounded-lg text-[11px] font-bold transition-colors flex items-center">
                                            <i class="pi pi-power-off text-[10px] mr-1"></i> Tutup Paksa
                                        </button>
                                    </template>

                                    <!-- AKSI SELESAI / DISETUJUI (Hanya Bisa Cetak) -->
                                    <template v-else-if="['SELESAI', 'DISETUJUI'].includes(po.status)">
                                        <button @click="unduhDokumenPO(po.id, po.no_po)" title="Cetak Dokumen PO" class="px-3 py-1.5 bg-indigo-50 text-indigo-600 hover:bg-indigo-600 hover:text-white rounded-lg text-[11px] font-bold transition-colors flex items-center">
                                            <i class="pi pi-print text-[10px] mr-1.5"></i> Cetak PO
                                        </button>
                                    </template>

                                    <span v-else class="text-xs text-slate-300">-</span>
                                </div>
                            </td>

                            <!-- KOLOM DETAIL -->
                            <td class="py-3 px-4 text-center">
                                <button @click="bukaDetail(po.id)" class="px-2.5 py-1.5 bg-slate-100 text-slate-600 hover:bg-slate-800 hover:text-white rounded-lg text-[11px] font-bold transition-colors flex items-center justify-center mx-auto whitespace-nowrap">
                                    <i class="pi pi-eye text-[10px] mr-1"></i> Detail
                                </button>
                            </td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>

        <Dialog v-model:visible="tampilModalPO" modal header="Buat Purchase Order Baru" :style="{ width: '90vw', maxWidth: '1000px' }" class="p-fluid">
            <LazyFormPO v-if="tampilModalPO" @close="tampilModalPO = false" @saved="poBerhasilDisimpan" />
        </Dialog>
        <Dialog v-model:visible="tampilModalDetail" modal :header="'Detail PO'" :style="{ width: '85vw', maxWidth: '800px' }" class="p-fluid">
            <LazyDetailPO v-if="tampilModalDetail" :poId="poIdTerpilih" />
        </Dialog>
    </div>
</template>

<script setup>
import { onMounted, ref, defineAsyncComponent } from 'vue'
import Dialog from 'primevue/dialog'
import Select from 'primevue/select'
import { usePurchaseOrder } from '@/features/accounting/composables/usePurchaseOrder'
import api from '@/utils/api' // Digunakan untuk fungsi cetak & tutup sesi

const tampilModalDetail = ref(false)
const poIdTerpilih = ref(null)
const tampilModalPO = ref(false)

const LazyFormPO = defineAsyncComponent(() =>
    import('@/features/accounting/views/ProcurementCreate.vue')
)
const LazyDetailPO = defineAsyncComponent(() =>
    import('@/features/accounting/views/PurchaseOrderDetail.vue')
)

const {
    daftarPO, isLoadingDaftar, cari, saringStatus, tampil,
    belumDiterima, draftCount, muatDaftarPO,
    ajukanPO, setujuiPO, tolakPO, kirimPO, batalkanPO
} = usePurchaseOrder()

onMounted(() => {
    muatDaftarPO()
})

const bukaDetail = (id) => {
    poIdTerpilih.value = id
    tampilModalDetail.value = true
}

const poBerhasilDisimpan = () => {
    tampilModalPO.value = false
    muatDaftarPO()
    alert('Mantap! Purchase Order berhasil disimpan.') 
}

const handleAjukan = async (id) => {
    if(confirm('Ajukan PO ini untuk persetujuan Manajer?')) {
        const res = await ajukanPO(id)
        if (res.success) alert('Purchase Order berhasil diajukan.')
    }
}

const handleSetujui = async (id) => {
    if(confirm('Setujui PO ini? Dokumen otomatis akan diteruskan dan dapat diproses oleh Gudang.')) {
        const res = await setujuiPO(id)
        if (res.success) alert('Purchase Order berhasil disetujui.')
    }
}

const handleTolak = async (id) => {
    const alasan = prompt('Masukkan alasan penolakan PO ini:')
    if(alasan !== null) {
        if(alasan.trim().length < 3) {
            alert('Alasan penolakan harus diisi jelas!')
            return
        }
        const res = await tolakPO(id, alasan)
        if (res.success) alert('Purchase Order berhasil ditolak.')
    }
}

const handleKirim = async (id) => {
    if(confirm('Tandai PO ini sebagai TERKIRIM ke Suplier? Item pesanan tidak akan bisa diubah lagi.')) {
        const res = await kirimPO(id)
        if (res.success) alert('Purchase Order berhasil ditandai Terkirim.')
    }
}

const handleBatal = async (id) => {
    const alasan = prompt('Masukkan alasan membatalkan dokumen PO ini:')
    if(alasan !== null) {
        if(alasan.trim().length < 5) {
            alert('Alasan pembatalan terlalu pendek! Minimal 5 karakter.')
            return
        }
        const res = await batalkanPO(id, alasan)
        if (res.success) alert('Purchase Order berhasil dibatalkan.')
    }
}

// === FUNGSI TUTUP SESI PO MENGGANTUNG ===
const handleTutupSesi = async (id) => {
    if(confirm('Anda yakin ingin MENUTUP SESI dokumen ini?\nSisa barang yang belum dikirim tidak akan ditagihkan lagi ke Gudang.')) {
        try {
            await api.post(`akunting/purchase-order/${id}/tutup-sesi/`)
            alert('Sesi Purchase Order berhasil ditutup dan status menjadi SELESAI.')
            muatDaftarPO() // Refresh tabel agar statusnya berubah
        } catch (error) {
            console.error('Gagal menutup sesi PO:', error)
            alert(error.response?.data?.detail || 'Terjadi kesalahan saat menutup sesi PO.')
        }
    }
}

// === FUNGSI UNDUH DOKUMEN WORD ===
const unduhDokumenPO = async (id, no_po) => {
    try {
        const fallbackName = no_po ? no_po.replace(/\//g, '_') : id
        
        const response = await api.get(`akunting/purchase-order/${id}/cetak/`, {
            responseType: 'blob' 
        })
        
        const url = window.URL.createObjectURL(new Blob([response.data]))
        const link = document.createElement('a')
        link.href = url
        link.setAttribute('download', `PO_${fallbackName}.docx`)
        document.body.appendChild(link)
        link.click()
        
        document.body.removeChild(link)
        window.URL.revokeObjectURL(url)
        
    } catch (error) {
        console.error('Gagal mengunduh dokumen:', error)
        alert('Gagal mencetak dokumen. Pastikan backend sudah merender template Word-nya.')
    }
}

const badgeColor = (status) => {
    const st = String(status).toUpperCase()
    if (st === 'DRAFT') return 'bg-slate-100 text-slate-600'
    if (st === 'PENDING') return 'bg-amber-100 text-amber-700'
    if (st === 'APPROVED') return 'bg-teal-50 text-teal-700 border border-teal-200'
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