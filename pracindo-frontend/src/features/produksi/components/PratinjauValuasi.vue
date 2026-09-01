<!-- src/features/produksi/components/PratinjauValuasi.vue -->
<template>
  <div v-if="hasil" class="space-y-6 animate-fade-in">
    <!-- Peringatan (Warning Box) -->
    <div v-if="hasil.peringatan && hasil.peringatan.length"
         class="p-4 bg-amber-50 border border-amber-200 rounded-xl flex items-start gap-3 shadow-sm">
      <i class="pi pi-exclamation-triangle text-amber-500 mt-0.5"></i>
      <div class="text-sm text-amber-700 font-medium">
        <ul class="list-disc list-inside space-y-1">
          <li v-for="(msg, idx) in hasil.peringatan" :key="idx">{{ msg }}</li>
        </ul>
      </div>
    </div>

    <!-- Tabel Rincian Valuasi -->
    <div class="bg-white border border-slate-200 rounded-[24px] shadow-sm overflow-hidden">
      <!-- Header Tabel -->
      <div class="p-4 md:p-5 border-b border-slate-100 flex items-center gap-3 bg-slate-50/50">
        <div class="w-8 h-8 rounded-full bg-blue-100 text-blue-600 flex items-center justify-center">
          <i class="pi pi-calculator text-sm"></i>
        </div>
        <div>
          <h3 class="text-sm font-bold text-slate-800">Pratinjau Kalkulasi Cost Nom</h3>
          <p class="text-[11px] text-slate-500">Rincian nilai bahan baku yang terserap ke dalam produk jadi</p>
        </div>
      </div>

      <!-- Area Scroll Tabel -->
      <div class="overflow-x-auto custom-scrollbar">
        <table class="w-full text-left text-sm table-auto min-w-[50rem]">
          <thead class="bg-slate-50 text-slate-500 border-b border-slate-100">
            <tr>
              <th class="py-3 px-5 font-bold uppercase tracking-wider text-[11px]">Sumber</th>
              <th class="py-3 px-5 font-bold uppercase tracking-wider text-[11px]">Bahan / WIP</th>
              <th class="py-3 px-5 font-bold uppercase tracking-wider text-[11px] text-right">Qty (Kg)</th>
              <th class="py-3 px-5 font-bold uppercase tracking-wider text-[11px] text-right">Harga/Kg</th>
              <th class="py-3 px-5 font-bold uppercase tracking-wider text-[11px] text-right">Nilai Total</th>
              <th class="py-3 px-5 font-bold uppercase tracking-wider text-[11px] text-center">Status</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-100">
            <tr v-for="(baris, idx) in hasil.baris" :key="idx" class="hover:bg-slate-50/50 transition-colors">
              <td class="py-3 px-5 text-slate-600 font-medium">
                <span class="bg-slate-100 border border-slate-200 px-2 py-0.5 rounded text-[10px] uppercase font-bold text-slate-500">
                  {{ baris.sumber }}
                </span>
              </td>
              <td class="py-3 px-5 font-bold text-slate-800">{{ baris.label || baris.id_sumber }}</td>
              <td class="py-3 px-5 text-right font-bold text-slate-700">{{ formatNumber(baris.qty_kg) }}</td>
              <td class="py-3 px-5 text-right font-medium text-slate-500">Rp {{ formatCurrency(baris.harga_per_kg) }}</td>
              <td class="py-3 px-5 text-right font-bold text-slate-700">Rp {{ formatCurrency(baris.nilai) }}</td>
              <td class="py-3 px-5 text-center">
                <span v-if="baris.menghabiskan" class="inline-flex items-center gap-1 bg-rose-50 text-rose-600 border border-rose-200 px-2.5 py-1 rounded-md text-[9px] font-bold uppercase tracking-wide" title="Sisa stok batch/pembelian ini akan dihabiskan">
                  <i class="pi pi-check-circle text-[10px]"></i> Habis
                </span>
                <span v-else class="text-slate-300 font-black">-</span>
              </td>
            </tr>
          </tbody>

          <!-- Ringkasan / Footer Tabel -->
          <tfoot class="bg-slate-50/80 border-t border-slate-200">
            <!-- Total Input Baris -->
            <tr>
              <td colspan="2" class="py-3 px-5 text-right font-semibold text-slate-500 text-[11px] uppercase tracking-wider">Total Input</td>
              <td class="py-3 px-5 text-right font-bold text-slate-700">{{ formatNumber(hasil.total_qty_input) }}</td>
              <td class="py-3 px-5 text-right font-medium text-slate-500">Rp {{ formatCurrency(hasil.harga_masuk_per_kg) }}</td>
              <td class="py-3 px-5 text-right font-bold text-slate-700">Rp {{ formatCurrency(hasil.total_nilai_input) }}</td>
              <td></td>
            </tr>

            <!-- Susut / Tekor (Ditampilkan hanya jika ada tekor) -->
            <tr v-if="hasil.tekor_kg > 0" class="border-t border-slate-100 bg-rose-50/30">
              <td colspan="2" class="py-3 px-5 text-right font-bold text-rose-500 text-[11px] uppercase tracking-wider">
                <i class="pi pi-arrow-down-right text-[10px] mr-1"></i> Tekor / Susut
              </td>
              <td class="py-3 px-5 text-right font-bold text-rose-600">{{ formatNumber(hasil.tekor_kg) }}</td>
              <td class="py-3 px-5 text-right font-medium text-slate-400">N/A</td>
              <td class="py-3 px-5 text-right font-bold text-rose-500 text-xs italic">Beban diserap &rarr;</td>
              <td></td>
            </tr>

            <!-- Final Valuasi (Harga Hasil) -->
            <tr class="border-t border-emerald-200 bg-emerald-50/50">
              <td colspan="2" class="py-4 px-5 text-right font-black text-emerald-700 text-xs uppercase tracking-wider">
                <i class="pi pi-check-circle text-emerald-600 mr-1"></i> Hasil Valuasi (Yield)
              </td>
              <td class="py-4 px-5 text-right font-black text-emerald-700 text-base">
                {{ formatNumber(hasil.qty_hasil) }} <span class="text-xs font-semibold">Kg</span>
              </td>
              <td class="py-4 px-5 text-right font-black text-emerald-700">Rp {{ formatCurrency(hasil.harga_hasil_per_kg) }}</td>
              <td class="py-4 px-5 text-right font-black text-emerald-700 text-base">Rp {{ formatCurrency(hasil.nilai_hasil) }}</td>
              <td></td>
            </tr>
          </tfoot>
        </table>
      </div>
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

// Mempertahankan fungsi bawaan aslinya
const formatNumber = (val) => {
  if (val === null || val === undefined) return '0.000'
  return Number(val).toLocaleString('id-ID', { minimumFractionDigits: 3, maximumFractionDigits: 3 })
}

const formatCurrency = (val) => {
  if (val === null || val === undefined) return '0.00'
  return Number(val).toLocaleString('id-ID', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}
</script>

<style scoped>
.animate-fade-in { animation: fadeIn 0.3s ease-out forwards; }
@keyframes fadeIn {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
}
.custom-scrollbar::-webkit-scrollbar { height: 6px; }
.custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
.custom-scrollbar::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 4px; }
.custom-scrollbar::-webkit-scrollbar-thumb:hover { background: #94a3b8; }
</style>
