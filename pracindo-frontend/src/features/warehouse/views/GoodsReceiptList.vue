<!--
  features/warehouse/views/GoodsReceiptList.vue
  ===============================================
  Daftar penerimaan barang. Desain Tailwind CSS Modern
  Tabel di desktop, kartu elegan di mobile.
-->
<template>
    <div class="flex flex-col w-full animate-fade-in relative">
        <!-- Header -->
        <div class="mb-4 md:mb-6 flex justify-between items-end">
            <div>
                <p class="text-xs text-slate-400 mb-1">
                    <span class="hover:text-slate-700 transition-colors">Warehouse</span> /
                    <span class="hover:text-slate-700 transition-colors font-semibold">Penerimaan Barang</span>
                </p>
                <h2 class="text-xl md:text-2xl font-bold text-slate-800 tracking-tight">Penerimaan Barang</h2>
            </div>
            <router-link :to="{ name: 'warehouse-receipt-buat' }"
                class="px-4 py-2 bg-slate-900 hover:bg-slate-800 text-white text-xs font-bold rounded-xl transition-colors flex items-center gap-2 shadow-sm transform hover:-translate-y-0.5">
                <i class="pi pi-plus"></i> Penerimaan Baru
            </router-link>
        </div>

        <!-- Notifikasi Error -->
        <div v-if="galat"
            class="mb-4 p-4 bg-red-50 border border-red-200 rounded-xl text-sm text-red-600 font-medium flex items-start gap-3 shadow-sm">
            <i class="pi pi-exclamation-triangle mt-0.5"></i>
            <span>{{ galat }}</span>
        </div>

        <!-- Area Filter & Tabel -->
        <div class="bg-white border border-slate-200 rounded-[24px] p-4 md:p-6 shadow-sm w-full min-h-[400px]">

            <!-- Header Kartu & Pencarian -->
            <div
                class="flex flex-col xl:flex-row justify-between items-start xl:items-center gap-4 mb-6 pb-4 border-b border-slate-100">
                <div>
                    <h3 class="text-sm font-bold text-slate-800">Daftar Penerimaan Suplier</h3>
                    <p class="text-xs text-slate-500">Menampilkan riwayat barang masuk</p>
                </div>

                <div class="flex items-center gap-2 w-full xl:w-auto">
                    <div class="relative w-full md:w-64">
                        <i class="pi pi-search absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 text-xs"></i>
                        <input type="text" v-model="kataKunci" @keyup.enter="cari" placeholder="Cari No. SJ / No. PO..."
                            class="w-full pl-9 pr-4 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs focus:outline-none focus:ring-2 focus:ring-slate-900 text-slate-700" />
                    </div>
                    <button @click="cari"
                        class="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-bold rounded-xl transition-colors">
                        Cari
                    </button>
                </div>
            </div>

            <!-- Loading State -->
            <div v-if="sedangProses" class="flex flex-col items-center justify-center py-12 text-center">
                <i class="pi pi-spin pi-spinner text-slate-300 text-2xl mb-3"></i>
                <p class="text-xs text-slate-500">Memuat data penerimaan...</p>
            </div>

            <!-- Empty State -->
            <div v-else-if="daftarPenerimaan.length === 0"
                class="flex flex-col items-center justify-center py-12 text-center">
                <div
                    class="w-12 h-12 bg-slate-50 rounded-full flex items-center justify-center mb-3 border border-slate-100">
                    <i class="pi pi-inbox text-slate-300 text-xl"></i>
                </div>
                <h4 class="text-sm font-bold text-slate-800 mb-1">Belum ada penerimaan</h4>
                <p class="text-xs text-slate-500">Tidak ada data yang cocok dengan kriteria Anda.</p>
            </div>

            <!-- Tampilan Tabel (Hanya untuk Layar Desktop/MD ke atas) -->
            <div v-else class="hidden md:block overflow-x-auto custom-scrollbar">
                <table class="w-full text-left text-sm table-fixed">
                    <thead class="text-slate-500 bg-slate-50/50">
                        <tr>
                            <th class="py-3 px-4 font-semibold rounded-tl-xl w-[20%]">Nomor & Tanggal</th>
                            <th class="py-3 px-4 font-semibold w-[25%]">Suplier</th>
                            <th class="py-3 px-4 font-semibold w-[20%]">Referensi PO</th>
                            <th class="py-3 px-4 font-semibold w-[20%]">No. Surat Jalan</th>
                            <th class="py-3 px-4 font-semibold w-[15%] text-center rounded-tr-xl">Status</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr v-for="p in daftarPenerimaan" :key="p.id" @click="bukaDetail(p.id)"
                            class="border-b border-slate-100 hover:bg-slate-50/50 transition-colors cursor-pointer">
                            <td class="py-3 px-4">
                                <div class="font-bold text-slate-800">{{ p.nomor }}</div>
                                <div class="text-[11px] font-medium text-slate-400 mt-0.5">
                                    <i class="pi pi-calendar text-[10px] mr-1"></i>{{ tanggal(p.tanggal) }}
                                </div>
                            </td>
                            <td class="py-3 px-4 text-slate-700 truncate font-medium" :title="p.suplier_nama">
                                {{ p.suplier_nama }}
                            </td>
                            <td class="py-3 px-4 text-slate-600">{{ p.po_nomor }}</td>
                            <td class="py-3 px-4 text-slate-600">{{ p.no_surat_jalan }}</td>
                            <td class="py-3 px-4 text-center">
                                <span v-if="p.ada_selisih"
                                    class="bg-red-50 text-red-600 border border-red-200 px-2.5 py-1 rounded-md text-[10px] font-bold tracking-wide uppercase inline-flex items-center gap-1">
                                    <i class="pi pi-exclamation-circle text-[10px]"></i> Ada Selisih
                                </span>
                                <span v-else
                                    class="bg-emerald-50 text-emerald-600 border border-emerald-200 px-2.5 py-1 rounded-md text-[10px] font-bold tracking-wide uppercase">
                                    Sesuai
                                </span>
                            </td>
                        </tr>
                    </tbody>
                </table>
            </div>

            <!-- Tampilan Card (Hanya untuk Layar Mobile) -->
            <div v-if="!sedangProses && daftarPenerimaan.length > 0" class="md:hidden flex flex-col gap-3">
                <div v-for="p in daftarPenerimaan" :key="p.id" @click="bukaDetail(p.id)"
                    class="bg-white border border-slate-100 rounded-xl p-4 shadow-sm active:scale-[0.98] transition-transform cursor-pointer">
                    <div class="flex justify-between items-start mb-3 border-b border-slate-50 pb-3">
                        <div>
                            <div class="font-bold text-slate-800 text-sm mb-1">{{ p.nomor }}</div>
                            <div class="text-[11px] text-slate-400 flex items-center gap-1">
                                <i class="pi pi-calendar text-[10px]"></i>{{ tanggal(p.tanggal) }}
                            </div>
                        </div>
                        <span v-if="p.ada_selisih"
                            class="bg-red-50 text-red-600 border border-red-200 px-2 py-0.5 rounded text-[9px] font-bold uppercase">
                            Ada Selisih
                        </span>
                    </div>
                    <div class="text-xs text-slate-600 flex flex-col gap-2">
                        <div class="flex justify-between items-center">
                            <span class="text-slate-400 font-semibold">Suplier</span>
                            <span class="font-bold text-slate-700 truncate max-w-[150px]">{{ p.suplier_nama }}</span>
                        </div>
                        <div class="flex justify-between items-center">
                            <span class="text-slate-400 font-semibold">No. PO</span>
                            <span class="font-medium bg-slate-50 px-2 py-0.5 rounded text-[11px]">{{ p.po_nomor
                                }}</span>
                        </div>
                        <div class="flex justify-between items-center">
                            <span class="text-slate-400 font-semibold">Surat Jalan</span>
                            <span class="font-medium bg-slate-50 px-2 py-0.5 rounded text-[11px]">{{ p.no_surat_jalan
                                }}</span>
                        </div>
                    </div>
                </div>
            </div>

        </div>
    </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useGoodsReceipt } from '../composables/useGoodsReceipt'
import { tanggal } from '@/utils/format'

const router = useRouter()
const { daftarPenerimaan, sedangProses, galat, muatPenerimaan } = useGoodsReceipt()

const kataKunci = ref('')

const cari = () => {
    muatPenerimaan({ search: kataKunci.value })
}

const bukaDetail = (id) => {
    router.push(`/warehouse/penerimaan/${id}`)
}

onMounted(() => {
    muatPenerimaan()
})
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
    height: 6px;
}

.custom-scrollbar::-webkit-scrollbar-track {
    background: transparent;
}

.custom-scrollbar::-webkit-scrollbar-thumb {
    background: #cbd5e1;
    border-radius: 4px;
}

.custom-scrollbar::-webkit-scrollbar-thumb:hover {
    background: #94a3b8;
}
</style>