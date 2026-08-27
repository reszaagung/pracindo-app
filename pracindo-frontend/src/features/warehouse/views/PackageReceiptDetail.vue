<!-- features/warehouse/views/PackageReceiptDetail.vue -->
<template>
    <div class="flex flex-col w-full animate-fade-in relative">
        <div v-if="galat" class="mb-4 p-4 bg-red-50 border border-red-200 rounded-xl text-sm text-red-600 font-medium flex items-start gap-3 shadow-sm">
            <i class="pi pi-exclamation-triangle mt-0.5"></i>
            <span>{{ galat }}</span>
        </div>

        <template v-if="ringkasan">
            <!-- Header -->
            <div class="mb-6 flex flex-col md:flex-row justify-between items-start md:items-end gap-4">
                <div>
                    <p class="text-xs text-slate-400 mb-1">
                        <router-link to="/warehouse/package-receipt" class="hover:text-slate-700 transition-colors">Penerimaan Kemasan</router-link>
                        <span class="mx-1">/</span>
                        <span class="text-slate-600 font-semibold">{{ ringkasan.nomor }}</span>
                    </p>
                    <h2 class="text-xl md:text-2xl font-bold text-slate-800 tracking-tight">{{ ringkasan.nomor }}</h2>
                    <p class="text-xs md:text-sm text-slate-500 mt-1">
                        {{ ringkasan.suplier }} &bull; PO {{ ringkasan.po }} &bull; {{ ringkasan.tanggal }}
                    </p>
                </div>
                <span v-if="ringkasan.ada_selisih"
                    class="bg-red-50 text-red-600 border border-red-200 px-3 py-1 rounded-full text-xs font-bold tracking-wide uppercase inline-flex items-center gap-1.5 shadow-sm">
                    <i class="pi pi-exclamation-circle"></i> Ada Selisih
                </span>
            </div>

            <!-- Panel 1: Kemasan Diterima -->
            <div class="bg-white border border-slate-200 rounded-[24px] p-4 md:p-6 shadow-sm w-full mb-6">
                <h3 class="text-sm font-bold text-slate-800 mb-4 pb-3 border-b border-slate-100 flex items-center gap-2">
                    <i class="pi pi-box text-emerald-600"></i> Aset Kemasan Diterima
                </h3>
                <div class="overflow-x-auto custom-scrollbar">
                    <table class="w-full text-left text-sm table-auto min-w-[50rem]">
                        <thead class="text-slate-500 bg-slate-50/50">
                            <tr>
                                <th class="py-3 px-4 font-semibold rounded-l-xl w-[40%]">Nama Kemasan</th>
                                <th class="py-3 px-3 font-semibold text-right w-[20%]">Qty Diterima</th>
                                <th class="py-3 px-3 font-semibold text-right w-[20%]">Ditolak</th>
                                <th class="py-3 px-4 font-semibold text-right rounded-r-xl w-[20%]">Selisih Qty</th>
                            </tr>
                        </thead>
                        <tbody class="divide-y divide-slate-100">
                            <tr v-for="(it, i) in ringkasan.item" :key="i" class="hover:bg-slate-50/50 transition-colors">
                                <td class="py-3.5 px-4 font-bold text-slate-800">{{ it.nama }}</td>
                                <td class="py-3.5 px-3 text-right font-medium text-emerald-600">{{ angka(it.diterima) }}</td>
                                <td class="py-3.5 px-3 text-right text-rose-600 font-medium">{{ angka(it.ditolak) }}</td>
                                <td class="py-3.5 px-4 text-right font-bold" :class="{ 'text-rose-600': it.selisih !== 0 }">
                                    {{ it.selisih != null ? angka(it.selisih) : '-' }}
                                </td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>

            <!-- Panel 2: Laporan Selisih Otomatis -->
            <div v-if="ringkasan.selisih?.length" class="bg-white border border-slate-200 rounded-[24px] p-4 md:p-6 shadow-sm w-full">
                <h3 class="text-sm font-bold text-slate-800 mb-4 pb-3 border-b border-slate-100 flex items-center gap-2">
                    <i class="pi pi-exclamation-triangle text-amber-600"></i> Laporan Selisih Kemasan Otomatis
                </h3>
                <div class="overflow-x-auto custom-scrollbar">
                    <table class="w-full text-left text-sm table-auto min-w-[35rem]">
                        <thead class="text-slate-500 bg-slate-50/50">
                            <tr>
                                <th class="py-3 px-3 font-semibold rounded-l-xl">Nomor</th>
                                <th class="py-3 px-3 font-semibold">Jenis</th>
                                <th class="py-3 px-3 font-semibold text-right">Qty</th>
                                <th class="py-3 px-3 font-semibold text-center">Status</th>
                                <th class="py-3 px-3 font-semibold rounded-r-xl">Resolusi</th>
                            </tr>
                        </thead>
                        <tbody class="divide-y divide-slate-100">
                            <tr v-for="s in ringkasan.selisih" :key="s.nomor" class="hover:bg-slate-50/50 transition-colors">
                                <td class="py-3.5 px-3 font-bold text-slate-800">{{ s.nomor }}</td>
                                <td class="py-3.5 px-3 text-slate-600">{{ s.jenis }}</td>
                                <td class="py-3.5 px-3 text-right font-bold text-rose-600">{{ angka(s.qty) }}</td>
                                <td class="py-3.5 px-3 text-center">
                                    <span class="px-2.5 py-1 rounded-md text-[10px] font-bold tracking-wide uppercase border bg-amber-50 text-amber-600 border-amber-200">
                                        {{ s.status }}
                                    </span>
                                </td>
                                <td class="py-3.5 px-3 text-slate-600 font-medium">{{ s.resolusi ?? '-' }}</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </template>
    </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'

const props = defineProps({
    id: { type: [String, Number], required: true }
})

const galat = ref('')
const ringkasan = ref(null)

const angka = (num) => {
    if (num == null) return '-'
    return num.toLocaleString('id-ID')
}

onMounted(() => {
    // Simulasi Fetch Data dari Backend
    ringkasan.value = {
        nomor: 'GRN/KMS/2026/VIII/098',
        tanggal: '26 Agu 2026',
        suplier: 'PT KARDUS MAKMUR',
        po: 'PO/KMS/2026/VIII/002',
        ada_selisih: true,
        item: [
            { nama: 'KARDUS KARTON A4', diterima: 1480, ditolak: 5, selisih: -15 },
            { nama: 'LAKBAN COKLAT 50M', diterima: 200, ditolak: 0, selisih: 0 }
        ],
        selisih: [
            { nomor: 'LS-KMS-2026-001', jenis: 'Barang Kurang Kirim', qty: 15, status: 'DIBUKA', resolusi: null },
            { nomor: 'LS-KMS-2026-002', jenis: 'Barang Rusak/Ditolak', qty: 5, status: 'DIBUKA', resolusi: null }
        ]
    }
})
</script>

<style scoped>
.animate-fade-in { animation: fadeIn 0.3s ease-out forwards; }
@keyframes fadeIn {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
}
.custom-scrollbar::-webkit-scrollbar { height: 6px; }
.custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
.custom-scrollbar::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 4px; }
.custom-scrollbar::-webkit-scrollbar-thumb:hover { background: #94a3b8; }
</style>
