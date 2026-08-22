<script setup>
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAkuntansi } from '../composables/useAkuntansi'
import dayjs from 'dayjs'

const router = useRouter()
const { riwayatJurnal, fetchRiwayatJurnal, isLoading } = useAkuntansi()

onMounted(() => {
    fetchRiwayatJurnal()
})

const formatTanggal = (date) => {
    return dayjs(date).format('DD MMM YYYY, HH:mm')
}
</script>

<template>
    <div class="p-6 max-w-7xl mx-auto space-y-6">
        <header class="flex justify-between items-end border-b border-slate-200 pb-4">
            <div>
                <p class="text-sm text-slate-500 mb-1">Akuntansi</p>
                <h1 class="text-2xl font-bold text-slate-800">Buku Jurnal Umum</h1>
            </div>
            <button @click="router.push('/retail/jurnal/entri')" class="bg-slate-900 text-white px-5 py-2.5 rounded-xl text-sm font-bold hover:bg-slate-800 transition-colors shadow-md flex items-center">
                <i class="pi pi-plus mr-2"></i> Tambah Jurnal
            </button>
        </header>

        <div class="bg-white rounded-[20px] shadow-[0_8px_30px_rgb(0,0,0,0.04)] border border-slate-100 overflow-hidden">
            <div v-if="isLoading" class="p-8 text-center text-slate-400">
                <i class="pi pi-spinner pi-spin text-2xl mb-2"></i>
                <p>Memuat data jurnal...</p>
            </div>

            <table v-else class="min-w-full">
                <thead class="bg-slate-50 border-b border-slate-200">
                    <tr>
                        <th class="px-6 py-4 text-left text-xs font-bold text-slate-500 uppercase">Tanggal</th>
                        <th class="px-6 py-4 text-left text-xs font-bold text-slate-500 uppercase">No. Jurnal</th>
                        <th class="px-6 py-4 text-left text-xs font-bold text-slate-500 uppercase">Akun & Keterangan</th>
                        <th class="px-6 py-4 text-right text-xs font-bold text-slate-500 uppercase w-40">Debit (Rp)</th>
                        <th class="px-6 py-4 text-right text-xs font-bold text-slate-500 uppercase w-40">Kredit (Rp)</th>
                    </tr>
                </thead>
                <tbody class="divide-y divide-slate-100">
                    <tr v-if="riwayatJurnal.length === 0" class="bg-white">
                        <td colspan="5" class="px-6 py-12 text-center text-slate-400">
                            <i class="pi pi-folder-open text-4xl mb-3 text-slate-300"></i>
                            <p>Belum ada riwayat transaksi jurnal.</p>
                        </td>
                    </tr>

                    <template v-for="jurnal in riwayatJurnal" :key="jurnal.id">
                        <!-- Header Jurnal -->
                        <tr class="bg-slate-50/50 border-t-2 border-slate-200">
                            <td class="px-6 py-3 whitespace-nowrap text-sm font-bold text-slate-700">{{ formatTanggal(jurnal.tanggal) }}</td>
                            <td class="px-6 py-3 whitespace-nowrap text-sm font-bold text-blue-600">{{ jurnal.nomor_jurnal }}</td>
                            <td colspan="3" class="px-6 py-3 text-sm text-slate-600 font-medium">
                                {{ jurnal.keterangan }}
                                <span v-if="jurnal.referensi" class="text-slate-400 text-xs ml-2 font-normal">(Ref: {{ jurnal.referensi }})</span>
                            </td>
                        </tr>
                        <!-- Detail Akun Jurnal -->
                        <tr v-for="item in jurnal.item_jurnal" :key="item.id" class="hover:bg-slate-50 transition-colors">
                            <td></td>
                            <td></td>
                            <td class="px-6 py-2 whitespace-nowrap text-sm" :class="Number(item.kredit) > 0 ? 'pl-10 text-slate-500' : 'font-bold text-slate-800'">
                                {{ item.akun_kode }} - {{ item.akun_nama }}
                            </td>
                            <td class="px-6 py-2 whitespace-nowrap text-sm text-right font-semibold text-slate-700">
                                {{ Number(item.debit) > 0 ? Number(item.debit).toLocaleString('id-ID') : '' }}
                            </td>
                            <td class="px-6 py-2 whitespace-nowrap text-sm text-right font-semibold text-slate-700">
                                {{ Number(item.kredit) > 0 ? Number(item.kredit).toLocaleString('id-ID') : '' }}
                            </td>
                        </tr>
                    </template>
                </tbody>
            </table>
        </div>
    </div>
</template>
