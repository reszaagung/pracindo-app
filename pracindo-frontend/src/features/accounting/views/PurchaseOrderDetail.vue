<template>
    <div class="flex flex-col w-full min-h-[400px] relative">
        <div v-if="loading" class="absolute inset-0 flex flex-col items-center justify-center bg-white/80 z-10">
            <i class="pi pi-spin pi-spinner text-emerald-600 text-3xl mb-3"></i>
            <p class="text-sm font-semibold text-slate-500 animate-pulse">Memuat rincian dokumen...</p>
        </div>

        <div v-else-if="error" class="flex flex-col items-center justify-center py-12 text-center">
            <i class="pi pi-exclamation-triangle text-red-400 text-4xl mb-4"></i>
            <h4 class="text-lg font-bold text-slate-800 mb-2">Gagal Memuat Data</h4>
            <p class="text-sm text-slate-500">{{ error }}</p>
        </div>

        <div v-else-if="data" class="flex flex-col gap-6 animate-fade-in">
            <!-- Header Info -->
            <div class="flex flex-col md:flex-row justify-between items-start md:items-center bg-slate-50 p-5 rounded-2xl border border-slate-100 gap-4">
                <div>
                    <p class="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1">PURCHASE ORDER</p>
                    <h2 class="text-2xl font-black text-slate-800 tracking-tight">{{ data.nomor }}</h2>
                    <p class="text-sm text-slate-500 font-medium mt-1">
                        <i class="pi pi-calendar text-[11px] mr-1"></i> {{ data.tanggal }}
                        <span class="mx-2 text-slate-300">|</span>
                        <i class="pi pi-building text-[11px] mr-1"></i> Entitas: {{ data.entitas }}
                    </p>
                </div>

                <div class="flex flex-col items-start md:items-end w-full md:w-auto">
                    <span :class="badgeColor(data.status)" class="px-3 py-1.5 rounded-full text-xs font-bold tracking-wide uppercase mb-2">
                        {{ data.status }}
                    </span>
                    <p class="text-sm font-bold text-slate-700">
                        <i class="pi pi-users text-[11px] mr-1 text-slate-400"></i> {{ data.suplier }}
                    </p>
                </div>
            </div>

            <!-- Tabel Item Barang -->
            <div>
                <h3 class="text-sm font-bold text-slate-800 mb-3 flex items-center gap-2">
                    <i class="pi pi-box text-blue-500"></i> Rincian Pesanan
                </h3>
                <div class="overflow-x-auto border border-slate-200 rounded-xl">
                    <table class="w-full text-left text-sm table-fixed">
                        <thead class="text-slate-500 bg-slate-50/80 border-b border-slate-200">
                            <tr>
                                <th class="py-3 px-4 font-semibold w-[35%]">Produk</th>
                                <th class="py-3 px-4 font-semibold w-[15%] text-right">Qty Pesan</th>
                                <th class="py-3 px-4 font-semibold w-[20%] text-right">Harga Satuan</th>
                                <th class="py-3 px-4 font-semibold w-[20%] text-right">Subtotal</th>
                                <th class="py-3 px-4 font-semibold w-[10%] text-center">Status</th>
                            </tr>
                        </thead>
                        <tbody class="divide-y divide-slate-100">
                            <tr v-for="(item, index) in data.item" :key="index" class="hover:bg-slate-50/50 transition-colors">
                                <td class="py-3 px-4">
                                    <p class="font-bold text-slate-800">{{ item.nama }}</p>
                                    <p class="text-[10px] text-slate-400 font-mono mt-0.5">{{ item.produk }}</p>
                                </td>
                                <td class="py-3 px-4 text-right font-medium text-slate-700">
                                    {{ formatNum(item.pesan) }} <span class="text-xs text-slate-400">Kg</span>
                                </td>
                                <td class="py-3 px-4 text-right font-medium text-slate-600">
                                    Rp {{ formatRupiah(item.harga) }}
                                </td>
                                <td class="py-3 px-4 text-right font-bold text-slate-800">
                                    Rp {{ formatRupiah(item.amount) }}
                                </td>
                                <td class="py-3 px-4 text-center">
                                    <i v-if="Number(item.diterima) >= Number(item.pesan)" class="pi pi-check-circle text-emerald-500" title="Diterima Penuh"></i>
                                    <i v-else-if="Number(item.diterima) > 0" class="pi pi-clock text-amber-500" :title="`Sisa: ${item.sisa} Kg`"></i>
                                    <i v-else class="pi pi-circle text-slate-300" title="Belum Diterima"></i>
                                </td>
                            </tr>
                        </tbody>
                        <tfoot class="bg-slate-50/80 border-t border-slate-200">
                            <tr>
                                <td colspan="3" class="py-3 px-4 text-right text-xs font-bold text-slate-500 uppercase tracking-wider">
                                    Total Nilai PO
                                </td>
                                <td class="py-3 px-4 text-right text-lg font-black text-emerald-700">
                                    Rp {{ formatRupiah(data.total_nilai) }}
                                </td>
                                <td></td>
                            </tr>
                        </tfoot>
                    </table>
                </div>
            </div>

            <!-- Info Penerimaan Gudang (Jika Ada) -->
            <div v-if="data.penerimaan && data.penerimaan.length > 0" class="bg-emerald-50/50 border border-emerald-100 rounded-xl p-5">
                <h3 class="text-sm font-bold text-emerald-800 mb-3 flex items-center gap-2">
                    <i class="pi pi-truck text-emerald-600"></i> Riwayat Penerimaan Gudang
                </h3>
                <div class="flex flex-col gap-2">
                    <div v-for="pn in data.penerimaan" :key="pn.nomor" class="flex justify-between items-center bg-white p-3 rounded-lg border border-emerald-100 shadow-sm">
                        <div>
                            <p class="font-bold text-slate-700 text-sm">{{ pn.nomor }}</p>
                            <p class="text-xs text-slate-500 mt-0.5">Surat Jalan: {{ pn.surat_jalan || '-' }}</p>
                        </div>
                        <div class="text-right">
                            <span class="text-xs font-semibold text-slate-600">{{ pn.tanggal }}</span>
                            <span v-if="pn.ada_selisih" class="block mt-1 text-[10px] bg-red-100 text-red-600 px-2 py-0.5 rounded uppercase font-bold">
                                Ada Selisih
                            </span>
                        </div>
                    </div>
                </div>
            </div>

            <div v-else class="bg-slate-50 border border-slate-100 rounded-xl p-4 text-center">
                <p class="text-xs text-slate-500 italic"><i class="pi pi-info-circle mr-1"></i> Belum ada penerimaan barang di gudang untuk dokumen ini.</p>
            </div>

        </div>
    </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '@/utils/api'
import { bacaError } from '@/utils/error'

const props = defineProps({
    poId: {
        type: [Number, String],
        required: true
    }
})

const data = ref(null)
const loading = ref(true)
const error = ref('')

onMounted(async () => {
    loading.value = true
    error.value = ''
    try {
        const response = await api.get(`akunting/purchase-order/${props.poId}/ringkasan/`)
        data.value = response.data
    } catch (err) {
        error.value = bacaError(err, 'Gagal memuat rincian PO.')
    } finally {
        loading.value = false
    }
})

// Utility Format
const formatNum = (num) => Number(num).toLocaleString('id-ID', { maximumFractionDigits: 2 })
const formatRupiah = (num) => Number(num).toLocaleString('id-ID')

const badgeColor = (status) => {
    const st = String(status).toUpperCase()
    if (st === 'DRAFT') return 'bg-slate-200 text-slate-700'
    if (st === 'PENDING') return 'bg-amber-100 text-amber-700'
    if (st === 'APPROVED') return 'bg-teal-100 text-teal-800'
    if (st === 'TERKIRIM') return 'bg-blue-100 text-blue-700'
    if (st === 'SEBAGIAN') return 'bg-orange-100 text-orange-700'
    if (st === 'SELESAI') return 'bg-emerald-100 text-emerald-700'
    if (st === 'BATAL' || st === 'DITOLAK') return 'bg-red-100 text-red-700'
    return 'bg-slate-100 text-slate-600'
}
</script>
