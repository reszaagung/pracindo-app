<script setup>
import { computed } from 'vue'
import { formatKg } from '@/utils/uang'

const props = defineProps({
    form: { type: Object, required: true },
    opsiRaw: { type: Array, default: () => [] },
    opsiBatch: { type: Array, default: () => [] },
    tangkiList: { type: Array, default: () => [] }
})

const tangkiTujuan = computed(() => {
    if (!props.form?.tangki) return 'Belum dipilih'
    const t = props.tangkiList.find(x => x.id === props.form.tangki)
    return t ? `${t.kode} - ${t.nama}` : 'Tangki'
})

const rincianBahan = computed(() => {
    if (!props.form?.baris) return []
    let total = 0
    const items = props.form.baris.map(b => {
        let qty = Number(String(b.qty_kg).replace(',', '.')) || 0
        total += qty
        let nama = 'Bahan belum dipilih'

        if (b.sumber === 'RAW' && b.raw) {
            const r = props.opsiRaw.find(x => x.produk_id === b.raw)
            if (r) nama = r.produk_nama
        } else if (b.sumber === 'WIP' && b.batch_sumber) {
            const w = props.opsiBatch.find(x => x.id === b.batch_sumber)
            if (w) nama = `Batch ${w.nomor} (${w.nama_hasil})`
        }

        return { nama, qty }
    }).filter(item => item.qty > 0)

    return items.map(item => ({
        ...item,
        persen: total > 0 ? ((item.qty / total) * 100).toFixed(1) : 0
    }))
})

const totalInput = computed(() => {
    return rincianBahan.value.reduce((sum, item) => sum + item.qty, 0)
})

const tekor = computed(() => {
    return Number(String(props.form?.tekor_kg).replace(',', '.')) || 0
})

const hasilOutput = computed(() => {
    const h = totalInput.value - tekor.value
    return h > 0 ? h : 0
})
</script>

<template>
    <section class="panel-valuasi bg-white border border-slate-200 rounded-[20px] p-5 shadow-sm">
        <h3 class="font-bold text-slate-800 border-b border-slate-100 pb-3 mb-4 flex items-center gap-2">
            <i class="pi pi-chart-pie text-blue-500"></i> Komposisi & Hasil Produksi
        </h3>

        <div v-if="rincianBahan.length === 0" class="text-slate-500 italic text-center py-6 text-sm bg-slate-50 rounded-xl border border-dashed border-slate-200">
            Isi kuantitas bahan sumber di atas untuk melihat persentase komposisi (%).
        </div>

        <div v-else class="space-y-4">
            <ul class="space-y-3">
                <li v-for="(item, i) in rincianBahan" :key="i" class="flex justify-between items-center text-sm bg-slate-50 p-2.5 rounded-lg border border-slate-100">
                    <span class="text-slate-700 font-bold line-clamp-1">{{ item.nama }}</span>
                    <div class="flex items-center gap-3 pl-4">
                        <span class="font-bold text-slate-800">{{ formatKg(item.qty) }}</span>
                        <span class="inline-block w-14 text-blue-700 font-black bg-blue-100 px-2 py-1 rounded-md text-xs text-center border border-blue-200 shadow-sm">
                            {{ item.persen }}%
                        </span>
                    </div>
                </li>
            </ul>

            <div class="border-t border-slate-100 pt-4 space-y-2 text-sm px-1">
                <div class="flex justify-between text-slate-600">
                    <span class="font-semibold">Total Bahan Diolah</span>
                    <span class="font-bold">{{ formatKg(totalInput) }}</span>
                </div>
                <div class="flex justify-between text-rose-500">
                    <span class="font-semibold">Susut / Tekor</span>
                    <span class="font-bold">- {{ formatKg(tekor) }}</span>
                </div>
            </div>

            <div class="bg-gradient-to-r from-emerald-500 to-emerald-600 p-4 rounded-xl shadow-md flex justify-between items-center text-white mt-2">
                <div>
                    <p class="text-[10px] font-black uppercase tracking-widest text-emerald-100 mb-0.5">Estimasi Hasil Output</p>
                    <p class="text-sm font-bold flex items-center gap-1.5"><i class="pi pi-database text-xs"></i> {{ tangkiTujuan }}</p>
                </div>
                <div class="text-right">
                    <span class="text-2xl font-black">{{ formatKg(hasilOutput) }}</span>
                </div>
            </div>
        </div>
    </section>
</template> 
