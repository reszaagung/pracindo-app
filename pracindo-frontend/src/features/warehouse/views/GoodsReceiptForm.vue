<!-- features/warehouse/views/GoodsReceiptForm.vue -->
<template>
    <div class="flex flex-col w-full animate-fade-in relative">
        <!-- STATE 1: SUKSES DISIMPAN -->
        <template v-if="hasil">
            <section class="bg-white border border-emerald-200 rounded-[24px] p-6 md:p-8 shadow-sm w-full">
                <div class="flex items-center gap-3 mb-2">
                    <div class="w-10 h-10 bg-emerald-100 text-emerald-600 rounded-full flex items-center justify-center">
                        <i class="pi pi-check text-xl"></i>
                    </div>
                    <h1 class="text-xl md:text-2xl font-bold text-slate-800 tracking-tight">Penerimaan Tersimpan</h1>
                </div>
                <p class="text-sm text-slate-600 mb-4 ml-13">{{ hasil.pesan }}</p>

                <div class="bg-slate-50 border border-slate-100 rounded-xl p-4 mb-6 ml-0 md:ml-13">
                    <p class="text-xs text-slate-400 font-bold uppercase tracking-wider mb-1">Nomor Dokumen</p>
                    <p class="text-lg font-black text-slate-800">{{ hasil.penerimaan?.nomor }}</p>
                </div>

                <div v-if="hasil.laporan_selisih?.length" class="mb-8 ml-0 md:ml-13">
                    <h3 class="text-sm font-bold text-slate-800 mb-3 flex items-center gap-2">
                        <i class="pi pi-exclamation-triangle text-amber-500"></i> Laporan Selisih Otomatis Terbit
                    </h3>
                    <div class="overflow-x-auto custom-scrollbar border border-slate-200 rounded-xl">
                        <table class="w-full text-left text-sm table-auto">
                            <thead class="bg-slate-50 text-slate-500">
                                <tr>
                                    <th class="py-2.5 px-4 font-semibold">Nomor Laporan</th>
                                    <th class="py-2.5 px-4 font-semibold">Jenis</th>
                                    <th class="py-2.5 px-4 font-semibold text-right">Qty Selisih</th>
                                </tr>
                            </thead>
                            <tbody class="divide-y divide-slate-100">
                                <tr v-for="s in hasil.laporan_selisih" :key="s.nomor" class="bg-white">
                                    <td class="py-2.5 px-4 font-bold text-slate-800">{{ s.nomor }}</td>
                                    <td class="py-2.5 px-4 text-slate-600">{{ s.jenis }}</td>
                                    <td class="py-2.5 px-4 text-right font-bold text-rose-600">{{ angka(s.qty_selisih, 3) }}</td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </div>

                <div class="flex flex-col sm:flex-row gap-3 ml-0 md:ml-13">
                    <router-link v-if="hasil.penerimaan?.id" :to="`/warehouse/input/receipt/${hasil.penerimaan.id}`"
                        class="px-6 py-2.5 bg-slate-900 hover:bg-slate-800 text-white text-sm font-bold rounded-xl transition-colors shadow-md text-center">
                        Lihat Detail
                    </router-link>
                    <button type="button" @click="$emit('tutup')"
                        class="px-6 py-2.5 bg-white border border-slate-200 hover:bg-slate-50 text-slate-700 text-sm font-bold rounded-xl transition-colors text-center">
                        Kembali ke Daftar
                    </button>
                </div>
            </section>
        </template>

        <!-- STATE 2: FORMULIR INPUT -->
        <form v-else @submit.prevent="kirim" class="space-y-6">
            <!-- Panel 1: Info PO & Surat Jalan -->
            <section class="bg-white border border-slate-200 rounded-[24px] p-4 md:p-6 shadow-sm w-full">
                <h2 class="text-sm font-bold text-slate-800 mb-4 pb-2 border-b border-slate-100">Referensi Dokumen</h2>
                <div class="flex flex-col gap-2 mb-4">
                    <label class="text-xs font-bold text-slate-500 uppercase tracking-wider">Pilih Purchase Order</label>
                    <div class="relative">
                        <i class="pi pi-file-edit absolute left-4 top-1/2 -translate-y-1/2 text-slate-400"></i>
                        <select v-model.number="poIdTerpilih"
                            class="w-full pl-11 pr-4 py-3 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-slate-800 text-slate-800 appearance-none font-medium cursor-pointer"
                            required>
                            <option value="" disabled>-- Pilih PO Suplier --</option>
                            <option v-for="po in daftarPOSiapTerima" :key="po.id" :value="po.id">
                                {{ po.no_po }} &bull; {{ po.suplier_nama }}
                            </option>
                        </select>
                        <i class="pi pi-chevron-down absolute right-4 top-1/2 -translate-y-1/2 text-slate-400 text-xs pointer-events-none"></i>
                    </div>
                </div>

                <div v-if="poTerpilih" class="grid grid-cols-1 md:grid-cols-2 gap-4 animate-fade-in">
                    <div class="flex flex-col gap-2">
                        <label class="text-xs font-bold text-slate-500 uppercase tracking-wider">No. Surat Jalan</label>
                        <input v-model="form.no_surat_jalan" type="text" required placeholder="Ketik nomor surat jalan suplier..."
                            class="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-slate-800 text-slate-800 font-medium" />
                    </div>
                    <div class="flex flex-col gap-2">
                        <label class="text-xs font-bold text-slate-500 uppercase tracking-wider">Tanggal Terima</label>
                        <input v-model="form.tanggal" type="date" required
                            class="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-slate-800 text-slate-800 font-medium" />
                    </div>
                    <div class="flex flex-col gap-2 md:col-span-2">
                        <label class="text-xs font-bold text-slate-500 uppercase tracking-wider">Catatan <span class="font-normal normal-case">(Opsional)</span></label>
                        <input v-model="form.catatan" type="text" placeholder="Catatan tambahan penerimaan..."
                            class="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-slate-800 text-slate-800" />
                    </div>
                </div>
            </section>

            <!-- Panel 2: Tabel Input Item -->
            <section v-if="poTerpilih" class="bg-white border border-slate-200 rounded-[24px] p-4 md:p-6 shadow-sm w-full animate-fade-in">
                <h2 class="text-sm font-bold text-slate-800 mb-4 pb-2 border-b border-slate-100 flex justify-between items-center">
                    <span>Pengecekan Fisik & Timbang</span>
                </h2>

                <!-- Tampilan Desktop (Tabel) -->
                <div class="hidden md:block overflow-x-auto custom-scrollbar">
                    <table class="w-full text-left text-sm table-auto min-w-[65rem]">
                        <thead class="text-slate-500 bg-slate-50/50">
                            <tr>
                                <th class="py-3 px-3 font-semibold rounded-tl-xl w-[15%]">Produk</th>
                                <th class="py-3 px-2 font-semibold text-right w-[8%]">Sisa PO</th>
                                <th class="py-3 px-2 font-semibold w-[12%]">Kemasan</th>
                                <th class="py-3 px-2 font-semibold text-right w-[8%]">Koli</th>
                                <th class="py-3 px-2 font-semibold text-right w-[10%]">Isi/Koli</th>
                                <th class="py-3 px-2 font-semibold text-right w-[10%]">Deklarasi</th>
                                <th class="py-3 px-2 font-semibold text-right w-[12%]">Qty Timbang</th>
                                <th class="py-3 px-2 font-semibold text-right w-[10%]">Ditolak</th>
                                <th class="py-3 px-3 font-semibold text-right rounded-tr-xl w-[15%]">Selisih</th>
                            </tr>
                        </thead>
                        <tbody class="divide-y divide-slate-100">
                            <tr v-for="r in baris" :key="r.po_item_id" class="hover:bg-slate-50/30 transition-colors">
                                <td class="py-3 px-3 font-bold text-slate-800 align-top">{{ r.nama_item }}</td>
                                <td class="py-3 px-2 text-right text-slate-500 font-medium align-top pt-3.5">{{ angka(r.sisa_qty, 3) }}</td>
                                <td class="py-3 px-2 align-top">
                                    <select v-model="r.jenis_kemasan"
                                        class="w-full px-2 py-1.5 bg-slate-50 border border-slate-200 rounded-lg text-xs focus:ring-2 focus:ring-slate-800">
                                        <option v-for="k in JENIS_KEMASAN" :key="k" :value="k">{{ k }}</option>
                                    </select>
                                </td>
                                <td class="py-3 px-2 align-top">
                                    <input v-if="r.jenis_kemasan !== 'CURAH'" v-model.number="r.jumlah_koli" type="number" min="0" step="1" required
                                        class="w-full px-2 py-1.5 bg-slate-50 border border-slate-200 rounded-lg text-xs text-right focus:ring-2 focus:ring-slate-800" />
                                </td>
                                <td class="py-3 px-2 align-top">
                                    <input v-if="r.jenis_kemasan !== 'CURAH'" v-model.number="r.isi_per_koli" type="number" min="0" step="0.001" required
                                        class="w-full px-2 py-1.5 bg-slate-50 border border-slate-200 rounded-lg text-xs text-right focus:ring-2 focus:ring-slate-800" />
                                </td>
                                <td class="py-3 px-2 text-right text-slate-600 font-medium align-top pt-3.5">{{ deklarasi(r) != null ? angka(deklarasi(r), 3) : '-' }}</td>
                                <td class="py-3 px-2 align-top">
                                    <input v-model.number="r.qty_diterima" type="number" min="0" step="0.001" :max="r.sisa_qty"
                                        class="w-full px-2 py-1.5 bg-slate-50 border border-slate-200 rounded-lg text-xs text-right font-bold focus:ring-2 focus:ring-emerald-500" />
                                </td>
                                <td class="py-3 px-2 align-top">
                                    <input v-model.number="r.qty_ditolak" type="number" min="0" step="0.001"
                                        class="w-full px-2 py-1.5 bg-slate-50 border border-rose-200 rounded-lg text-xs text-right font-bold text-rose-600 focus:ring-2 focus:ring-rose-500" />
                                </td>
                                <td class="py-3 px-3 text-right font-bold align-top pt-3.5" :class="{ 'text-rose-600': melebihiToleransi(r) }">
                                    <template v-if="selisih(r) != null">
                                        {{ angka(selisih(r), 3) }} <span class="text-[10px] font-normal block">({{ angka(persenSelisih(r), 2) }}%)</span>
                                    </template>
                                    <span v-else class="text-slate-400 font-normal">-</span>
                                </td>
                            </tr>
                        </tbody>
                    </table>
                </div>

                <!-- Tampilan Mobile (Card) -->
                <div class="md:hidden flex flex-col gap-4">
                    <div v-for="r in baris" :key="'kartu-' + r.po_item_id" class="border border-slate-200 rounded-xl p-4 bg-slate-50/30">
                        <div class="flex justify-between items-center mb-4 border-b border-slate-100 pb-2">
                            <span class="font-bold text-slate-800">{{ r.nama_item }}</span>
                            <span class="text-[10px] font-bold text-slate-500 bg-slate-100 px-2 py-1 rounded">Sisa: {{ angka(r.sisa_qty, 3) }}</span>
                        </div>
                        <div class="flex flex-col gap-3">
                            <div class="flex flex-col gap-1.5">
                                <label class="text-[10px] font-bold text-slate-500 uppercase">Jenis Kemasan</label>
                                <select v-model="r.jenis_kemasan"
                                    class="w-full px-3 py-2 bg-white border border-slate-200 rounded-lg text-sm focus:ring-2 focus:ring-slate-800">
                                    <option v-for="k in JENIS_KEMASAN" :key="k" :value="k">{{ k }}</option>
                                </select>
                            </div>
                            <div v-if="r.jenis_kemasan !== 'CURAH'" class="grid grid-cols-2 gap-3">
                                <div class="flex flex-col gap-1.5">
                                    <label class="text-[10px] font-bold text-slate-500 uppercase">Jml Koli</label>
                                    <input v-model.number="r.jumlah_koli" type="number" min="0" step="1" required
                                        class="w-full px-3 py-2 bg-white border border-slate-200 rounded-lg text-sm text-right focus:ring-2 focus:ring-slate-800" />
                                </div>
                                <div class="flex flex-col gap-1.5">
                                    <label class="text-[10px] font-bold text-slate-500 uppercase">Isi/Koli</label>
                                    <input v-model.number="r.isi_per_koli" type="number" min="0" step="0.001" required
                                        class="w-full px-3 py-2 bg-white border border-slate-200 rounded-lg text-sm text-right focus:ring-2 focus:ring-slate-800" />
                                </div>
                            </div>
                            <div class="flex justify-between items-center bg-slate-100 p-2 rounded-lg">
                                <span class="text-[10px] font-bold text-slate-500 uppercase">Total Deklarasi:</span>
                                <span class="font-bold text-slate-700">{{ deklarasi(r) != null ? angka(deklarasi(r), 3) : '-' }}</span>
                            </div>
                            <div class="grid grid-cols-2 gap-3 mt-2">
                                <div class="flex flex-col gap-1.5">
                                    <label class="text-[10px] font-bold text-emerald-600 uppercase">Qty Timbang</label>
                                    <input v-model.number="r.qty_diterima" type="number" min="0" step="0.001" :max="r.sisa_qty"
                                        class="w-full px-3 py-2 bg-white border border-emerald-200 rounded-lg text-sm text-right font-bold focus:ring-2 focus:ring-emerald-500" />
                                </div>
                                <div class="flex flex-col gap-1.5">
                                    <label class="text-[10px] font-bold text-rose-500 uppercase">Qty Ditolak</label>
                                    <input v-model.number="r.qty_ditolak" type="number" min="0" step="0.001"
                                        class="w-full px-3 py-2 bg-white border border-rose-200 rounded-lg text-sm text-right font-bold text-rose-600 focus:ring-2 focus:ring-rose-500" />
                                </div>
                            </div>
                            <div v-if="selisih(r) != null" class="flex justify-between items-center p-2 rounded-lg mt-1 border"
                                :class="melebihiToleransi(r) ? 'bg-rose-50 border-rose-100' : 'bg-slate-50 border-slate-100'">
                                <span class="text-[10px] font-bold uppercase" :class="melebihiToleransi(r) ? 'text-rose-600' : 'text-slate-500'">Selisih:</span>
                                <span class="font-bold" :class="melebihiToleransi(r) ? 'text-rose-600' : 'text-slate-700'">
                                    {{ angka(selisih(r), 3) }} ({{ angka(persenSelisih(r), 2) }}%)
                                </span>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Notifikasi Dinamis dalam Form -->
                <div class="mt-6 space-y-3">
                    <div v-for="r in barisMelebihiToleransi" :key="r.po_item_id" class="p-3 bg-amber-50 border border-amber-200 rounded-xl flex gap-3 items-start">
                        <i class="pi pi-exclamation-triangle text-amber-500 mt-0.5"></i>
                        <div class="text-xs text-amber-700">
                            <strong>{{ r.nama_item }}:</strong> Selisih melebihi 0.5%. Laporan selisih akan diterbitkan secara otomatis setelah disimpan.
                        </div>
                    </div>
                    <div v-for="r in baris.filter(r => Number(r.qty_ditolak) > 0)" :key="'tolak-' + r.po_item_id"
                        class="flex flex-col gap-2 mt-4 p-4 border border-rose-100 bg-rose-50/30 rounded-xl">
                        <label class="text-xs font-bold text-rose-600 uppercase tracking-wider">Alasan Tolak - {{ r.nama_item }}</label>
                        <input v-model="r.alasan_tolak" type="text" required placeholder="Jelaskan alasan penolakan..."
                            class="w-full px-4 py-2.5 bg-white border border-rose-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-rose-400 text-slate-800" />
                    </div>
                    <div v-for="r in barisLewatSisa" :key="'lewat-' + r.po_item_id" class="p-3 bg-red-50 border border-red-200 rounded-xl flex gap-3 items-start">
                        <i class="pi pi-times-circle text-red-500 mt-0.5"></i>
                        <div class="text-xs text-red-700">
                            <strong>{{ r.nama_item }}:</strong> Qty timbang melebihi sisa PO yang diizinkan (Maks: {{ angka(r.sisa_qty, 3) }}).
                        </div>
                    </div>
                </div>

                <!-- Area Error Global & Tombol Submit -->
                <div class="mt-8 pt-6 border-t border-slate-100">
                    <div v-if="pesanError" class="mb-4 p-3 bg-red-50 border border-red-200 rounded-xl text-xs text-red-600 font-bold flex items-center gap-2">
                        <i class="pi pi-exclamation-circle"></i> {{ pesanError }}
                    </div>
                    <div class="flex justify-end gap-3">
                        <!-- PERBAIKAN: Tombol emit untuk menutup Lazy View -->
                        <button type="button" @click="$emit('tutup')"
                            class="px-6 py-3 bg-white border border-slate-200 hover:bg-slate-50 text-slate-700 text-sm font-bold rounded-xl transition-colors">
                            Batal
                        </button>
                        <button type="submit" :disabled="sedangProses || barisLewatSisa.length > 0"
                            class="px-8 py-3 bg-slate-900 hover:bg-slate-800 disabled:bg-slate-300 text-white text-sm font-bold rounded-xl shadow-md transition-all flex items-center gap-2 cursor-pointer disabled:cursor-not-allowed transform hover:-translate-y-0.5">
                            <i v-if="sedangProses" class="pi pi-spin pi-spinner text-xs"></i>
                            <i v-else class="pi pi-save text-xs"></i>
                            {{ sedangProses ? 'Menyimpan...' : 'Simpan Penerimaan' }}
                        </button>
                    </div>
                </div>
            </section>
        </form>
    </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onUnmounted, watch } from 'vue'
import { useGoodsReceipt } from '../composables/useGoodsReceipt'
import { useNavInputEntry } from '../composables/useNavInputEntry'
import { angka, hariIni } from '@/utils/format'

// Deklarasi Emitter untuk Lazy View
const emit = defineEmits(['tutup'])

const JENIS_KEMASAN = ['KARUNG', 'DRUM', 'JERIGEN', 'DUS', 'SAK', 'CURAH']

const { daftarPOSiapTerima, sedangProses, muatPOSiapTerima, simpanPenerimaan } = useGoodsReceipt()
const { setNavInfo, resetNav } = useNavInputEntry()

const poIdTerpilih = ref('')
const poTerpilih = computed(() => daftarPOSiapTerima.value.find(po => po.id === poIdTerpilih.value) ?? null)

const form = reactive({
    no_surat_jalan: '',
    tanggal: hariIni(),
    catatan: ''
})

const baris = ref([])
const pesanError = ref('')
const hasil = ref(null)

watch(poTerpilih, (po) => {
    baris.value = (po?.item ?? []).map(it => ({
        po_item_id: it.id,
        nama_item: it.nama_item,
        sisa_qty: Number(it.sisa_qty),
        jenis_kemasan: 'CURAH',
        jumlah_koli: null,
        isi_per_koli: null,
        qty_diterima: null,
        qty_ditolak: 0,
        alasan_tolak: '',
    }))
})

const deklarasi = (r) => {
    if (r.jenis_kemasan === 'CURAH' || !r.jumlah_koli || !r.isi_per_koli) return null
    return r.jumlah_koli * r.isi_per_koli
}

const selisih = (r) => {
    const d = deklarasi(r)
    if (d == null || r.qty_diterima == null || r.qty_diterima === '') return null
    return Number(r.qty_diterima) - d
}

const persenSelisih = (r) => {
    const d = deklarasi(r)
    const s = selisih(r)
    return d && s != null ? (s / d) * 100 : null
}

const melebihiToleransi = (r) => {
    const p = persenSelisih(r)
    return p != null && Math.abs(p) > 0.5
}

const barisMelebihiToleransi = computed(() => baris.value.filter(melebihiToleransi))
const barisLewatSisa = computed(() => baris.value.filter(r => r.qty_diterima != null && Number(r.qty_diterima) > r.sisa_qty))

const kirim = async () => {
    pesanError.value = ''
    const barisKirim = baris.value
        .filter(r => Number(r.qty_diterima) > 0)
        .map(r => ({
            po_item_id: r.po_item_id,
            jenis_kemasan: r.jenis_kemasan,
            jumlah_koli: r.jenis_kemasan === 'CURAH' ? null : r.jumlah_koli,
            isi_per_koli: r.jenis_kemasan === 'CURAH' ? null : r.isi_per_koli,
            qty_diterima: String(r.qty_diterima),
            qty_ditolak: String(r.qty_ditolak || 0),
            alasan_tolak: r.alasan_tolak || '',
        }))

    if (!barisKirim.length) {
        pesanError.value = 'Minimal satu item harus diisi qty timbang.'
        return
    }

    const res = await simpanPenerimaan({
        po_id: poTerpilih.value.id,
        no_surat_jalan: form.no_surat_jalan,
        tanggal: form.tanggal,
        dokumen_id: null,
        catatan: form.catatan,
        baris: barisKirim,
    })

    if (res.success) {
        hasil.value = res.data
    } else {
        pesanError.value = res.message
    }
}

// INI KUNCI PENTING: Memuat API backend saat form ditampilkan
onMounted(() => {
    setNavInfo('Penerimaan Barang Baru', 'Warehouse > Penerimaan > Entry')
    muatPOSiapTerima()
})

onUnmounted(() => {
    resetNav()
})
</script>

<style scoped>
.animate-fade-in {
    animation: fadeIn 0.3s ease-out forwards;
}

@keyframes fadeIn {
    from {
        opacity: 0;
        transform: translateY(10px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

.custom-scrollbar::-webkit-scrollbar {
    height: 6px;
    width: 6px;
}

.custom-scrollbar::-webkit-scrollbar-track {
    background: transparent;
}

.custom-scrollbar::-webkit-scrollbar-thumb {
    background: #cbd5e1;
    border-radius: 4px;
}

.custom-scrollbar::-webkit-scrollbar-thumb:hover {
    background: #94a3b8;
}
</style>
