<!--
  features/inventory/views/StockDetail.vue
  ==========================================
  Mutasi plus kepemilikan dengan desain Tailwind CSS modern.
-->
<template>
    <div class="flex flex-col w-full animate-fade-in relative">
        <!-- Notifikasi Galat -->
        <div v-if="galat"
            class="mb-4 p-4 bg-red-50 border border-red-200 rounded-xl text-sm text-red-600 font-medium flex items-start gap-3 shadow-sm">
            <i class="pi pi-exclamation-triangle mt-0.5"></i>
            <span>{{ galat }}</span>
        </div>

        <template v-if="stokDetail">
            <!-- Header Rincian -->
            <div class="mb-6 flex flex-col md:flex-row justify-between items-start md:items-end gap-4">
                <div>
                    <p class="text-xs text-slate-400 mb-1">
                        <router-link to="/inventory" class="hover:text-slate-700 transition-colors">Stok</router-link>
                        <span class="mx-1">/</span>
                        <span class="text-slate-600 font-semibold">{{ stokDetail.produk_kode }}</span>
                    </p>
                    <h1 class="text-xl md:text-2xl font-bold text-slate-800 tracking-tight">{{ stokDetail.produk_kode
                        }}</h1>
                    <p class="text-xs md:text-sm text-slate-500 mt-1">
                        {{ stokDetail.grup_bahan_kode }} &bull; Lapis {{ stokDetail.lapis_label }}
                        <template v-if="stokDetail.tangki_kode"> &bull; Tangki {{ stokDetail.tangki_kode
                            }}</template>:
                        7]
                    </p>
                </div>
                <div class="text-right">
                    <span class="text-[10px] text-slate-400 font-bold uppercase tracking-wider block mb-0.5">Total
                        Qty</span>
                    <span class="text-2xl font-black text-slate-800">{{ angka(stokDetail.qty, 3) }}</span>
                </div>
            </div>

            <!-- Panel Khusus Lapis POOL -->
            <div v-if="stokDetail.lapis === 'POOL'"
                class="bg-blue-50 border border-blue-200 rounded-[24px] p-6 mb-6 flex flex-col md:flex-row justify-between items-start md:items-center gap-4 shadow-sm">
                <p class="text-sm text-blue-900 m-0 max-w-xl">
                    Lapis POOL tidak punya pemilik — yang ada adalah <strong>posisi klaim</strong> tiap entitas atas
                    pool ini:
                    7].
                </p>
                <router-link :to="`/inventory/klaim/${stokDetail.grup_bahan}`"
                    class="px-5 py-2.5 bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold rounded-xl transition-colors shadow-md flex items-center gap-2 whitespace-nowrap">
                    <span>Lihat Posisi Klaim</span>
                    <i class="pi pi-arrow-right text-xs"></i>
                </router-link>
            </div>

            <!-- Panel Kepemilikan (RAW / JADI) -->
            <div v-else class="bg-white border border-slate-200 rounded-[24px] p-4 md:p-6 shadow-sm w-full mb-6">
                <h3
                    class="text-sm font-bold text-slate-800 mb-4 pb-3 border-b border-slate-100 flex items-center gap-2">
                    <i class="pi pi-users text-emerald-600"></i> Kepemilikan Entitas
                </h3>
                <div class="overflow-x-auto custom-scrollbar">
                    <table class="w-full text-left text-sm table-auto">
                        <thead class="text-slate-500 bg-slate-50/50">
                            <tr>
                                <th class="py-3 px-4 font-semibold rounded-l-xl">Entitas</th>
                                <th class="py-3 px-4 font-semibold text-right rounded-r-xl">Qty</th>
                            </tr>
                        </thead>
                        <tbody class="divide-y divide-slate-100">
                            <tr v-for="k in stokDetail.kepemilikan" :key="k.entitas"
                                class="hover:bg-slate-50/50 transition-colors">
                                <td class="py-3 px-4 font-bold text-slate-800">{{ k.entitas_kode }}</td>
                                <td class="py-3 px-4 text-right font-medium text-slate-700">{{ angka(k.qty, 3) }}:
                                    7]</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
                <p v-if="!stokDetail.kepemilikan?.length" class="py-6 text-center text-slate-400 text-xs">Belum ada
                    kepemilikan
                    tercatat.</p>
            </div>

            <!-- Panel Riwayat Mutasi -->
            <div class="bg-white border border-slate-200 rounded-[24px] p-4 md:p-6 shadow-sm w-full">
                <h3
                    class="text-sm font-bold text-slate-800 mb-4 pb-3 border-b border-slate-100 flex items-center gap-2">
                    <i class="pi pi-history text-slate-600"></i> Riwayat Mutasi
                </h3>
                <div class="overflow-x-auto custom-scrollbar">
                    <table class="w-full text-left text-sm table-auto min-w-[50rem]">
                        <thead class="text-slate-500 bg-slate-50/50">
                            <tr>
                                <th class="py-3 px-3 font-semibold rounded-l-xl">Tanggal</th>
                                <th class="py-3 px-3 font-semibold">Jenis</th>
                                <th class="py-3 px-3 font-semibold text-right">Masuk</th>
                                <th class="py-3 px-3 font-semibold text-right">Keluar</th>
                                <th class="py-3 px-3 font-semibold text-right">Saldo Akhir</th>
                                <th class="py-3 px-3 font-semibold rounded-r-xl">Referensi</th>
                            </tr>
                        </thead>
                        <tbody class="divide-y divide-slate-100">
                            <tr v-for="m in daftarMutasi" :key="m.id" class="hover:bg-slate-50/50 transition-colors">
                                <td class="py-3 px-3 font-medium text-slate-600">{{ tanggal(m.tanggal) }}</td>
                                <td class="py-3 px-3 text-slate-800 font-semibold">{{ m.jenis_label }}</td>
                                <td class="py-3 px-3 text-right text-emerald-600 font-medium">{{ m.masuk ?
                                    angka(m.masuk, 3) : '—'
                                    }}</td>
                                <td class="py-3 px-3 text-right text-rose-600 font-medium">{{ m.keluar ? angka(m.keluar,
                                    3) : '—'
                                    }}</td>
                                <td class="py-3 px-3 text-right font-black text-slate-800">{{ angka(m.saldo_akhir, 3)
                                    }}
                                </td>
                                <td class="py-3 px-3 text-slate-500 text-xs">{{ m.referensi || '—' }}</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
                <p v-if="!daftarMutasi.length" class="py-8 text-center text-slate-400 text-xs">Belum ada mutasi:
                    7].</p>
            </div>
        </template>
    </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useStock } from '../composables/useStock'
import { angka, tanggal } from '@/utils/format'

const props = defineProps({ id: { type: [String, Number], required: true } })
const { stokDetail, daftarMutasi, galat, muatStokDetail, muatMutasi } = useStock()

onMounted(() => {
    muatStokDetail(props.id)
    muatMutasi({ stok: props.id })
})
</script>