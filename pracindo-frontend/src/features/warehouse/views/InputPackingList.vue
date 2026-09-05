<template>
  <div class="p-6 bg-white rounded-lg shadow">
    <div class="flex justify-between items-center mb-6">
      <h2 class="text-2xl font-bold text-gray-800">Riwayat Packing</h2>
      <button @click="$router.push({ name: 'InputPackingForm' })" class="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700">
        + Buat Packing Baru
      </button>
    </div>

    <div v-if="isLoading" class="text-center py-4 text-gray-500">Memuat data...</div>
    <div v-else-if="error" class="text-red-500 mb-4">{{ error }}</div>

    <table v-else class="min-w-full divide-y divide-gray-200 border">
      <thead class="bg-gray-50">
        <tr>
          <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Nomor</th>
          <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Tanggal</th>
          <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Batch WIP</th>
          <th class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Qty (Kg)</th>
          <th class="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase">Aksi</th>
        </tr>
      </thead>
      <tbody class="bg-white divide-y divide-gray-200">
        <tr v-for="item in packings" :key="item.id">
          <td class="px-6 py-4 whitespace-nowrap font-medium">{{ item.nomor }}</td>
          <td class="px-6 py-4 whitespace-nowrap">{{ item.tanggal }}</td>
          <td class="px-6 py-4 whitespace-nowrap">{{ item.batch_nomor }}</td>
          <td class="px-6 py-4 whitespace-nowrap text-right">{{ item.qty_kg }}</td>
          <td class="px-6 py-4 whitespace-nowrap text-center">
            <button @click="handleVoid(item)" class="text-red-600 hover:text-red-900 text-sm font-semibold">
              Void
            </button>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { usePacking } from '../composables/usePacking'

const router = useRouter()
const { packings, isLoading, error, fetchPackings, voidPacking } = usePacking()

onMounted(() => {
  fetchPackings()
})

const handleVoid = async (item) => {
  const alasan = prompt(`Masukkan alasan membatalkan packing ${item.nomor}:`)
  if (!alasan) return

  try {
    await voidPacking(item.id, alasan)
    alert('Dokumen berhasil di-void!')
    fetchPackings()
  } catch (err) {
    alert('Gagal void: ' + err)
  }
}
</script>