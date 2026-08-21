<template>
    <div class="p-6 h-screen overflow-y-auto bg-gray-50">
        <h1 class="text-2xl font-bold mb-6 text-gray-800">Manajemen Shift & Keuangan</h1>
        <div class="grid grid-cols-2 gap-6">
            <div class="bg-white p-6 rounded-xl shadow-sm border border-gray-200">
                <h2 class="text-lg font-bold text-gray-800 mb-4">Status Shift Saat Ini</h2>
                <div v-if="sesiAktif" class="space-y-4">
                    <div class="flex justify-between border-b pb-2">
                        <span class="text-gray-600">Kasir Aktif</span>
                        <span class="font-semibold">{{ sesiAktif.nama_kasir }}</span>
                    </div>
                    <div class="flex justify-between border-b pb-2">
                        <span class="text-gray-600">Waktu Buka</span>
                        <span class="font-semibold">{{ sesiAktif.waktu }}</span>
                    </div>
                    <div class="flex justify-between border-b pb-2">
                        <span class="text-gray-600">Modal Awal</span>
                        <span class="font-semibold text-blue-600">Rp {{ sesiAktif.saldo_awal }}</span>
                    </div>
                    <div class="flex justify-between border-b pb-2">
                        <span class="text-gray-600">Total Penjualan</span>
                        <span class="font-semibold text-green-600">Rp {{ sesiAktif.total_penjualan }}</span>
                    </div>
                    <button @click="prosesTutup"
                        class="w-full mt-6 bg-red-600 text-white font-bold py-3 rounded-lg hover:bg-red-700 transition-colors shadow">
                        TUTUP SHIFT & SETOR
                    </button>
                </div>
                <div v-else class="text-center py-8">
                    <p class="text-gray-500 mb-4">Tidak ada shift yang sedang aktif.</p>
                    <button class="bg-blue-600 text-white font-bold py-2 px-6 rounded-lg hover:bg-blue-700">
                        Buka Shift Baru
                    </button>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useRetail } from '../composables/useRetail'

const { sesiAktif, fetchSesi, tutupShift } = useRetail()

onMounted(() => {
    fetchSesi()
})

const prosesTutup = async () => {
    if (confirm('Yakin ingin menutup shift dan menyetor pendapatan?')) {
        await tutupShift()
        alert('Shift berhasil ditutup!')
    }
}
</script>