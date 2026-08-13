<script setup>
import { ref, onMounted } from 'vue'
import { apiGetList } from '@/utils/apiClient'

const emit = defineEmits(['tampil-notifikasi'])

const daftarSesi = ref([])
const memuat = ref(false)
const galatServer = ref(null)

const muatData = async () => {
    memuat.value = true
    galatServer.value = null
    try {
        daftarSesi.value = await apiGetList('/api/v1/produksi/sesi/')
    } catch (e) {
        galatServer.value = e.message || 'Gagal memuat daftar sesi.'
        emit('tampil-notifikasi', galatServer.value, 'galat')
    } finally {
        memuat.value = false
    }
}

const formatAngka = (n) => Number(n || 0).toLocaleString('id-ID', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
const formatTanggal = (tgl) => new Date(tgl).toLocaleDateString('id-ID', { day: '2-digit', month: 'short', year: 'numeric' })

onMounted(() => {
    muatData()
})
</script>

<template>
    <div class="animate-fade-in">
        <header class="mb-6 flex flex-col sm:flex-row sm:justify-between sm:items-end gap-4">
            <div>
                <h1 class="text-2xl font-black text-slate-800">Daftar Sesi Produksi</h1>
                <p class="text-sm text-slate-500 mt-1">Pantau riwayat dan status *batch* pengadonan.</p>
            </div>
            <div class="flex gap-2">
                <button @click="muatData"
                    class="px-4 py-2 bg-white border border-slate-200 rounded-xl text-sm font-bold text-slate-600 hover:bg-slate-50 shadow-sm flex items-center gap-2">
                    <i class="pi pi-refresh" :class="{ 'pi-spin': memuat }"></i>
                </button>
                <router-link to="/produksi/mixing"
                    class="px-4 py-2 bg-indigo-600 text-white rounded-xl text-sm font-bold hover:bg-indigo-700 shadow-sm flex items-center gap-2">
                    <i class="pi pi-plus"></i> Sesi Baru
                </router-link>
            </div>
        </header>

        <div class="bg-white rounded-[24px] border border-slate-200 shadow-sm overflow-hidden">
            <div class="overflow-x-auto">
                <table class="w-full text-left border-collapse">
                    <thead>
                        <tr
                            class="bg-slate-50/80 border-b border-slate-200 text-slate-500 text-[11px] uppercase tracking-wider font-bold">
                            <th class="p-4 pl-6">Tanggal</th>
                            <th class="p-4">Jenis Sesi</th>
                            <th class="p-4">Resep / Produk Target</th>
                            <th class="p-4 text-right">Target Output</th>
                            <th class="p-4">Status</th>
                        </tr>
                    </thead>
                    <tbody class="text-sm">
                        <tr v-if="memuat" class="border-b border-slate-100">
                            <td colspan="5" class="p-8 text-center text-slate-400">
                                <i class="pi pi-spin pi-spinner text-2xl"></i>
                                <p class="mt-2 text-xs">Memuat data sesi...</p>
                            </td>
                        </tr>
                        <tr v-else-if="daftarSesi.length === 0" class="border-b border-slate-100">
                            <td colspan="5" class="p-8 text-center text-slate-500">
                                Belum ada sesi produksi yang tercatat.
                            </td>
                        </tr>
                        <tr v-else v-for="sesi in daftarSesi" :key="sesi.id"
                            class="border-b border-slate-100 hover:bg-slate-50 transition-colors">
                            <td class="p-4 pl-6 font-medium text-slate-700 whitespace-nowrap">
                                {{ formatTanggal(sesi.tanggal) }}
                            </td>
                            <td class="p-4">
                                <span :class="[
                                    'px-2 py-1 rounded text-[10px] font-black tracking-wider uppercase',
                                    sesi.jenis_sesi === 'PRODUKSI' ? 'bg-indigo-50 text-indigo-700 border border-indigo-100' : 'bg-amber-50 text-amber-700 border border-amber-100'
                                ]">
                                    {{ sesi.jenis_sesi }}
                                </span>
                            </td>
                            <td class="p-4 text-slate-600 font-medium">
                                {{ sesi.resep_kode || sesi.produk_jadi_kode || 'Manual/Eksperimen' }}
                            </td>
                            <td class="p-4 text-right font-bold text-slate-700 tabular-nums">
                                {{ formatAngka(sesi.qty_target) }} <span
                                    class="text-slate-400 font-normal text-xs">kg</span>
                            </td>
                            <td class="p-4">
                                <div class="flex items-center gap-2">
                                    <span class="w-2 h-2 rounded-full bg-slate-300"
                                        :class="{ 'bg-emerald-500': sesi.status === 'SELESAI', 'bg-blue-500': sesi.status === 'BERJALAN' }"></span>
                                    <span class="text-xs font-semibold text-slate-600">{{ sesi.status || 'DRAFT'
                                        }}</span>
                                </div>
                            </td>
                        </tr>
                    </tbody>
                </table>
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
    }

    to {
        opacity: 1;
    }
}
</style>