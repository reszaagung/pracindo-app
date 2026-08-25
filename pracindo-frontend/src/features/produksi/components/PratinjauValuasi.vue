<template>
  <div v-if="hasil" class="space-y-4">
    <div v-if="hasil.peringatan && hasil.peringatan.length" class="p-4 bg-yellow-50 border border-yellow-200 rounded-md">
      <ul class="list-disc list-inside text-sm text-yellow-800">
        <li v-for="(msg, idx) in hasil.peringatan" :key="idx">{{ msg }}</li>
      </ul>
    </div>

    <div class="overflow-x-auto border border-gray-200 rounded-lg">
      <table class="min-w-full divide-y divide-gray-200 text-sm">
        <thead class="bg-gray-50">
          <tr>
            <th class="px-4 py-3 text-left font-medium text-gray-500">Sumber</th>
            <th class="px-4 py-3 text-left font-medium text-gray-500">Bahan / WIP</th>
            <th class="px-4 py-3 text-right font-medium text-gray-500">Qty (Kg)</th>
            <th class="px-4 py-3 text-right font-medium text-gray-500">Harga/Kg</th>
            <th class="px-4 py-3 text-right font-medium text-gray-500">Nilai</th>
            <th class="px-4 py-3 text-center font-medium text-gray-500">Habis</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-gray-200 bg-white">
          <tr v-for="(baris, idx) in hasil.baris" :key="idx">
            <td class="px-4 py-2">{{ baris.sumber }}</td>
            <td class="px-4 py-2">{{ baris.label || baris.id_sumber }}</td>
            <td class="px-4 py-2 text-right">{{ formatNumber(baris.qty_kg) }}</td>
            <td class="px-4 py-2 text-right">{{ formatCurrency(baris.harga_per_kg) }}</td>
            <td class="px-4 py-2 text-right">{{ formatCurrency(baris.nilai) }}</td>
            <td class="px-4 py-2 text-center">
              <span v-if="baris.menghabiskan" class="text-red-600 font-bold" title="Menghabiskan Sisa">✓</span>
              <span v-else class="text-gray-400">-</span>
            </td>
          </tr>
        </tbody>
        <tfoot class="bg-gray-50 font-semibold text-gray-700">
          <tr>
            <td colspan="2" class="px-4 py-3 text-right">Total Input</td>
            <td class="px-4 py-3 text-right">{{ formatNumber(hasil.total_qty_input) }}</td>
            <td class="px-4 py-3 text-right">{{ formatCurrency(hasil.harga_masuk_per_kg) }}</td>
            <td class="px-4 py-3 text-right">{{ formatCurrency(hasil.total_nilai_input) }}</td>
            <td></td>
          </tr>
          <tr class="text-red-600">
            <td colspan="2" class="px-4 py-3 text-right">Tekor / Susut</td>
            <td class="px-4 py-3 text-right">{{ formatNumber(hasil.tekor_kg) }}</td>
            <td></td>
            <td class="px-4 py-3 text-right">{{ formatCurrency(hasil.nilai_susut) }}</td>
            <td></td>
          </tr>
          <tr class="text-primary-700 bg-primary-50">
            <td colspan="2" class="px-4 py-3 text-right">Hasil Valuasi</td>
            <td class="px-4 py-3 text-right">{{ formatNumber(hasil.qty_hasil) }}</td>
            <td class="px-4 py-3 text-right">{{ formatCurrency(hasil.harga_hasil_per_kg) }}</td>
            <td class="px-4 py-3 text-right">{{ formatCurrency(hasil.nilai_hasil) }}</td>
            <td></td>
          </tr>
        </tfoot>
      </table>
    </div>
  </div>
</template>

<script setup>
defineProps({
  hasil: {
    type: Object,
    default: null
  }
})

const formatNumber = (val) => {
  if (val === null || val === undefined) return '0.000'
  return Number(val).toLocaleString('id-ID', { minimumFractionDigits: 3, maximumFractionDigits: 3 })
}

const formatCurrency = (val) => {
  if (val === null || val === undefined) return '0.00'
  return Number(val).toLocaleString('id-ID', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}
</script>
