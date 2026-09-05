<template>
  <div class="p-6">
    <h2 class="text-xl font-bold mb-4">Laporan Stok Barang Jadi</h2>

    <div class="bg-white rounded shadow overflow-hidden">
      <table class="min-w-full divide-y divide-gray-200">
        <thead class="bg-gray-50">
          <tr>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Entitas</th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Produk / Item</th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Kemasan</th>
            <th class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Total Unit</th>
            <th class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Total (Kg)</th>
          </tr>
        </thead>
        <tbody class="bg-white divide-y divide-gray-200">
          <tr v-if="isLoading">
            <td colspan="5" class="px-6 py-4 text-center text-gray-500">Memuat data stok...</td>
          </tr>
          <tr v-else-if="stokData.length === 0">
            <td colspan="5" class="px-6 py-4 text-center text-gray-500">Tidak ada stok barang jadi.</td>
          </tr>
          <tr v-else v-for="(item, index) in stokData" :key="index" class="hover:bg-gray-50">
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900 font-semibold">{{ item.entitas_kode }}</td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{{ item.item_nama }}</td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{{ item.kemasan_nama }}</td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900 text-right">{{ item.qty_unit }}</td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900 text-right">{{ item.qty_kg }} Kg</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'

const stokData = ref([])
const isLoading = ref(true)

const fetchStokBarangJadi = async () => {
  try {
    // API memanggil method services.get_barang_jadi() di backend
    const response = await axios.get('/api/v1/inventory/barang-jadi/')
    stokData.value = response.data.rincian
  } catch (error) {
    console.error('Gagal memuat stok barang jadi', error)
  } finally {
    isLoading.value = false
  }
}

onMounted(() => {
  fetchStokBarangJadi()
})
</script>