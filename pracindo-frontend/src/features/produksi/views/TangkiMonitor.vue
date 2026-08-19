<script setup>
import { onMounted, ref } from 'vue'
import { apiTangki } from '../api'
import KartuTangki from '../components/KartuTangki.vue'

const tangkiSaldos = ref([])
const memuat = ref(true)
const galatMuat = ref(null)

async function muatMonitor() {
    galatMuat.value = null
    memuat.value = true
    try {
        const res = await apiTangki.daftar({ aktif: true })
        const daftar = Array.isArray(res) ? res : (res.results || [])

        const promises = daftar.map(t =>
            apiTangki.saldo(t.id).catch(err => {
                console.error(`Gagal muat saldo tangki ${t.id}:`, err)
                return null
            })
        )
        const results = await Promise.all(promises)
        tangkiSaldos.value = results.filter(r => r !== null)
    } catch (e) {
        galatMuat.value = "Gagal memuat data dari server. Silakan periksa koneksi atau hubungi administrator."
    } finally {
        memuat.value = false
    }
}

onMounted(() => {
    muatMonitor()
})
</script>

<template>
    <div class="tangki-monitor max-w-7xl mx-auto pb-10 space-y-6">
        <header class="flex justify-between items-end border-b pb-4">
            <div>
                <h1 class="text-2xl font-bold text-gray-800">Monitor Tangki Fisik</h1>
                <p class="text-sm text-gray-500 mt-1">Pantau ketersediaan hasil produksi dan rincian batch di dalam tangki.</p>
            </div>
            <button @click="muatMonitor" :disabled="memuat"
                class="text-sm bg-white border border-gray-300 hover:bg-gray-50 text-gray-700 px-4 py-2 rounded-md shadow-sm font-medium transition-colors disabled:opacity-50 flex items-center gap-2">
                <span v-if="memuat">Memuat...</span>
                <span v-else>Segarkan Data</span>
            </button>
        </header>

        <div v-if="memuat" class="flex justify-center items-center py-20 text-gray-400">
            <div class="animate-pulse flex flex-col items-center">
                <div class="w-10 h-10 border-4 border-blue-200 border-t-blue-600 rounded-full animate-spin mb-4"></div>
                <p>Memindai saldo fisik tangki...</p>
            </div>
        </div>

        <div v-else-if="galatMuat" class="bg-red-50 border border-red-200 text-red-700 p-6 rounded-lg text-center">
            <p class="font-semibold">{{ galatMuat }}</p>
            <button @click="muatMonitor"
                class="mt-4 bg-red-600 text-white px-4 py-2 rounded-md hover:bg-red-700 text-sm">
                Coba Lagi
            </button>
        </div>

        <div v-else-if="tangkiSaldos.length === 0"
            class="text-center py-20 text-gray-500 bg-gray-50 rounded-lg border border-dashed">
            Tidak ada data tangki aktif yang ditemukan.
        </div>

        <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6 align-stretch">
            <KartuTangki v-for="t in tangkiSaldos" :key="t.tangki" :data="t" />
        </div>
    </div>
</template>
