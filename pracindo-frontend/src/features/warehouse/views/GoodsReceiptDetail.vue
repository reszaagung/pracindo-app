<!--
  features/warehouse/views/GoodsReceiptDetail.vue
  =================================================
  Detail penerimaan barang & laporan selisih otomatis dengan Tailwind CSS modern.
-->
<template>
    <div class="flex flex-col w-full animate-fade-in relative">
        <!-- Notifikasi Error -->
        <div v-if="galat"
            class="mb-4 p-4 bg-red-50 border border-red-200 rounded-xl text-sm text-red-600 font-medium flex items-start gap-3 shadow-sm">
            <i class="pi pi-exclamation-triangle mt-0.5"></i>
            <span>{{ galat }}</span>
        </div>

        <template v-if="ringkasan">
            <!-- Header -->
            <div class="mb-6 flex flex-col md:flex-row justify-between items-start md:items-end gap-4">
                <div>
                    <p class="text-xs text-slate-400 mb-1">
                        <router-link to="/warehouse" class="hover:text-slate-700 transition-colors">Penerimaan
                            Barang</router-link>
                        <span class="mx-1">/</span>
                        <span class="text-slate-600 font-semibold">{{ ringkasan.nomor }}</span>
                    </p>
                    <h2 class="text-xl md:text-2xl font-bold text-slate-800 tracking-tight">{{ ringkasan.nomor }}</h2>
                    <p class="text-xs md:text-sm text-slate-500 mt-1">
                        {{ ringkasan.suplier }} &bull; PO {{ ringkasan.po }} &bull; {{ tanggal(ringkasan.tanggal)
                        }}
                    </p>
                </div>
                <span v-if="ringkasan.ada_selisih"
                    class="bg-red-50 text-red-600 border border-red-200 px-3 py-1 rounded-full text-xs font-bold tracking-wide uppercase inline-flex items-center gap-1.5 shadow-sm">
                    <i class="pi pi-exclamation-circle"></i> Ada Selisih
                </span>
            </div>

            <!-- Panel 1: Item Diterima -->
            <div class="bg-white border border-slate-200 rounded-[24px] p-4 md:p-6 shadow-sm w-full mb-6">
                <h3
                    class="text-sm font-bold text-slate-800 mb-4 pb-3 border-b border-slate-100 flex items-center gap-2">
                    <i class="pi pi-box text-emerald-600"></i> Item Diterima
                </h3>

                <div class="overflow-x-auto custom-scrollbar">
                    <table class="w-full text-left text-sm table-auto min-w-[50rem]">
                        <thead class="text-slate-500 bg-slate-50/50">
                            <tr>
                                <th class="py-3 px-3 font-semibold rounded-l-xl">Nama Produk</th>
                                <th class="py-3 px-3 font-semibold">Kemasan</th>
                                <th class="py-3 px-3 font-semibold text-right">Koli</th>
                                <th class="py-3 px-3 font-semibold text-right">Isi/Koli</th>
                                <th class="py-3 px-3 font-semibold text-right">Deklarasi</th>
                                <th class="py-3 px-3 font-semibold text-right">Timbang</th>
                                <th class="py-3 px-3 font-semibold text-right">Ditolak</th>
                                <th class="py-3 px-3 font-semibold text-right rounded-r-xl">Selisih</th>
                            </tr>
                        </thead>
                        <tbody class="divide-y divide-slate-100">
                            <tr v-for="(it, i) in ringkasan.item" :key="i"
                                class="hover:bg-slate-50/50 transition-colors">
                                <td class="py-3.5 px-3 font-bold text-slate-800">{{ it.nama }}</td>
                                <td class="py-3.5 px-3 text-slate-600">{{ it.kemasan }}</td>
                                <td class="py-3.5 px-3 text-right text-slate-600">{{ it.koli ?? '-' }}</td>
                                <td class="py-3.5 px-3 text-right text-slate-600">{{ it.isi_per_koli ?
                                    angka(it.isi_per_koli, 3) : '-' }}</td>
                                <td class="py-3.5 px-3 text-right text-slate-600">{{ it.deklarasi ? angka(it.deklarasi,
                                    3) : '-' }}</td>
                                <td class="py-3.5 px-3 text-right font-medium text-slate-800">{{ angka(it.timbang, 3) }}
                                </td>
                                <td class="py-3.5 px-3 text-right text-rose-600 font-medium">{{ angka(it.ditolak, 3) }}
                                </td>
                                <td class="py-3.5 px-3 text-right font-bold"
                                    :class="{ 'text-rose-600': melebihiToleransi(it.persen) }">
                                    {{ it.selisih_berat != null ? angka(it.selisih_berat, 3) : '-' }}
                                    <span v-if="it.persen != null" class="text-xs font-normal block md:inline">({{
                                        angka(it.persen, 2) }}%)</span>
                                </td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>

            <!-- Panel 2: Laporan Selisih Otomatis -->
            <div v-if="ringkasan.selisih?.length"
                class="bg-white border border-slate-200 rounded-[24px] p-4 md:p-6 shadow-sm w-full">
                <h3
                    class="text-sm font-bold text-slate-800 mb-4 pb-3 border-b border-slate-100 flex items-center gap-2">
                    <i class="pi pi-exclamation-triangle text-amber-600"></i> Laporan Selisih Otomatis
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
                            <tr v-for="s in ringkasan.selisih" :key="s.nomor"
                                class="hover:bg-slate-50/50 transition-colors">
                                <td class="py-3.5 px-3 font-bold text-slate-800">{{ s.nomor }}</td>
                                <td class="py-3.5 px-3 text-slate-600">{{ s.jenis }}</td>
                                <td class="py-3.5 px-3 text-right font-bold text-rose-600">{{ angka(s.qty, 3) }}:
                                    6]</td>
                                <td class="py-3.5 px-3 text-center">
                                    <span
                                        class="px-2.5 py-1 rounded-md text-[10px] font-bold tracking-wide uppercase border bg-amber-50 text-amber-600 border-amber-200">
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
import { onMounted } from 'vue'
import { useGoodsReceipt } from '../composables/useGoodsReceipt'
import { angka, tanggal } from '@/utils/format'

const props = defineProps({
    id: { type: [String, Number], required: true }
})

const { ringkasan, galat, muatRingkasan } = useGoodsReceipt()

const melebihiToleransi = (persen) => persen != null && Math.abs(persen) > 0.5

onMounted(() => muatRingkasan(props.id))
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