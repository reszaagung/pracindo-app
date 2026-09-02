<template>
  <div class="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden w-full mt-4">
    <div class="p-4 pb-3 flex items-center gap-3 border-b border-slate-100 bg-slate-50">
      <div class="w-8 h-8 rounded-lg bg-blue-100 text-blue-600 flex items-center justify-center">
        <i class="pi pi-calculator"></i>
      </div>
      <div>
        <h3 class="font-bold text-slate-800 text-sm">Pratinjau Kalkulasi Cost Nom</h3>
        <p class="text-[11px] text-slate-500">Rincian nilai bahan baku yang terserap ke dalam produk jadi</p>
      </div>
    </div>

    <div class="overflow-x-auto">
      <table class="w-full text-sm text-left whitespace-nowrap">
        <thead class="bg-slate-50/50 text-slate-500 text-[11px] uppercase font-semibold border-b border-slate-100">
          <tr>
            <th class="px-4 py-3">Sumber</th>
            <th class="px-4 py-3">Bahan / WIP</th>
            <!-- Ditambahkan style inline agar menang melawan CSS global -->
            <th class="px-4 py-3 text-right" style="text-align: right;">Qty (Kg)</th>
            <th class="px-4 py-3 text-right" style="text-align: right;">Harga/Kg</th>
            <th class="px-4 py-3 text-right" style="text-align: right;">Nilai Total</th>
            <th class="px-4 py-3 text-center" style="text-align: center;">Status</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-slate-100">
          <!-- Rincian Bahan Baku / WIP -->
          <tr v-for="(item, idx) in rincian" :key="idx" class="hover:bg-slate-50/50">
            <td class="px-4 py-2.5">
              <span class="text-[10px] font-bold px-2 py-1 rounded tracking-wider"
                :class="item.batch_nomor ? 'bg-purple-100 text-purple-700' : 'bg-slate-100 text-slate-600'">
                {{ item.batch_nomor ? 'WIP' : 'RAW' }}
              </span>
            </td>
            <td class="px-4 py-2.5 font-medium text-slate-700">
              {{ item.produk_kode || item.batch_nomor || '-' }}
            </td>
            <td class="px-4 py-2.5 text-right font-mono text-slate-600">{{ formatKg(item.qty_kg) }}</td>
            <td class="px-4 py-2.5 text-right text-slate-500">{{ formatRupiah(item.harga_per_kg) }}</td>
            <td class="px-4 py-2.5 text-right font-medium text-slate-700">{{ formatRupiah(item.subtotal) }}</td>
            <td class="px-4 py-2.5 text-center">
              <i v-if="item.cukup" class="pi pi-check-circle text-emerald-500"></i>
              <i v-else class="pi pi-times-circle text-red-500" title="Saldo Tidak Cukup"></i>
            </td>
          </tr>

          <tr v-if="rincian.length === 0">
            <td colspan="6" class="px-4 py-6 text-center text-slate-400 text-xs italic">
              Belum ada rincian bahan baku valid untuk dikalkulasi.
            </td>
          </tr>

          <!-- Baris Total Input -->
          <tr class="bg-slate-50 text-slate-700 border-t-2 border-slate-200">
            <td colspan="2" class="px-4 py-3">
              <div class="text-right uppercase text-xs tracking-wider text-slate-500 font-bold">Total Input</div>
            </td>
            <td class="px-4 py-3 text-right font-mono font-semibold">{{ formatKg(hasil?.total_qty_masuk) }}</td>
            <td class="px-4 py-3 text-right text-slate-400">-</td>
            <td class="px-4 py-3 text-right font-bold text-slate-800">{{ formatRupiah(hasil?.total_nilai_masuk) }}</td>
            <td></td>
          </tr>
          
          <!-- Baris Hasil Valuasi (Yield) -->
          <tr class="bg-emerald-50 text-emerald-800 border-t border-emerald-100">
            <!-- Pindahkan flex ke dalam div agar tidak merusak struktur colspan tabel -->
            <td colspan="2" class="px-4 py-3.5">
              <div class="flex items-center justify-end gap-2 uppercase text-xs tracking-wider font-bold">
                <i class="pi pi-check-circle"></i> Hasil Valuasi (Yield)
              </div>
            </td>
            <td class="px-4 py-3.5 text-right font-mono font-bold">
              {{ formatKg(hasil?.proyeksi_output_kg) }} <span class="text-[10px] font-normal opacity-75">Kg</span>
            </td>
            <td class="px-4 py-3.5 text-right font-bold text-emerald-700">{{ formatRupiah(hasil?.wip_cost_per_kg) }}</td>
            <td class="px-4 py-3.5 text-right font-bold text-emerald-700">{{ formatRupiah(hasil?.total_nilai_masuk) }}</td>
            <td></td>
          </tr>
        </tbody>
      </table>
    </div>
    
    <div v-if="peringatan.length > 0" class="p-3 bg-red-50 border-t border-red-100">
      <p v-for="(msg, i) in peringatan" :key="i" class="text-xs text-red-600 flex items-center gap-1.5 mb-1 last:mb-0">
        <i class="pi pi-exclamation-triangle"></i> {{ msg }}
      </p>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  hasil: {
    type: Object,
    default: () => ({})
  }
})

const rincian = computed(() => props.hasil?.rincian || [])
const peringatan = computed(() => props.hasil?.peringatan || [])

function formatKg(v) {
  return Number(v || 0).toLocaleString('id-ID', { minimumFractionDigits: 3, maximumFractionDigits: 3 })
}

function formatRupiah(v) {
  return `Rp ${Number(v || 0).toLocaleString('id-ID', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
}
</script>