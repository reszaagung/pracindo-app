<script setup>
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useBatchList } from '../composables/useBatchList'
import TabelBatch from '../components/TabelBatch.vue'

const router = useRouter()
const { baris, memuat, muatDaftar, hapusDraft, postingDraft } = useBatchList()

onMounted(() => {
    muatDaftar()
})
</script>

<template>
    <div class="batch-list max-w-7xl mx-auto pb-10 space-y-6">
        <header class="flex justify-between items-end border-b pb-4">
            <div>
                <h1 class="text-2xl font-bold text-gray-800">Riwayat Batch Produksi</h1>
                <p class="text-sm text-gray-500 mt-1">Daftar seluruh aktivitas pencampuran dan hasil produksi.</p>
            </div>
            <button @click="router.push({ name: 'produksi-batch-baru' })"
                class="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md shadow-sm font-medium transition-colors">
                + Input Produksi Baru
            </button>
        </header>

        <TabelBatch :baris="baris" :memuat="memuat"
            @detail="(id) => router.push({ name: 'produksi-batch-detail', params: { id } })"
            @posting="postingDraft"
            @hapus="hapusDraft" />
    </div>
</template>
