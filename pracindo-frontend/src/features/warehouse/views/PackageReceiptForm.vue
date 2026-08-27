<!-- features/warehouse/views/PackageReceipt.vue -->
<template>
    <div class="flex flex-col w-full animate-fade-in relative">
        <!-- STATE 1: SUKSES DISIMPAN -->
        <template v-if="hasil">
            <section class="bg-white border border-emerald-200 rounded-[24px] p-6 md:p-8 shadow-sm w-full">
                <div class="flex items-center gap-3 mb-2">
                    <div class="w-10 h-10 bg-emerald-100 text-emerald-600 rounded-full flex items-center justify-center">
                        <i class="pi pi-check text-xl"></i>
                    </div>
                    <h1 class="text-xl md:text-2xl font-bold text-slate-800 tracking-tight">Penerimaan Kemasan Tersimpan</h1>
                </div>
                <p class="text-sm text-slate-600 mb-4 ml-13">{{ hasil.pesan }}</p>

                <div class="bg-slate-50 border border-slate-100 rounded-xl p-4 mb-6 ml-0 md:ml-13">
                    <p class="text-xs text-slate-400 font-bold uppercase tracking-wider mb-1">Nomor Dokumen</p>
                    <p class="text-lg font-black text-slate-800">{{ hasil.penerimaan?.nomor }}</p>
                </div>

                <div class="flex flex-col sm:flex-row gap-3 ml-0 md:ml-13">
                    <button type="button" @click="resetForm"
                        class="px-6 py-2.5 bg-slate-900 hover:bg-slate-800 text-white text-sm font-bold rounded-xl transition-colors shadow-md text-center">
                        Input Penerimaan Lain
                    </button>
                    <button type="button" @click="$emit('tutup')"
                        class="px-6 py-2.5 bg-white border border-slate-200 hover:bg-slate-50 text-slate-700 text-sm font-bold rounded-xl transition-colors text-center">
                        Kembali ke Daftar
                    </button>
                </div>
            </section>
        </template>

        <!-- STATE 2: FORMULIR INPUT KEMASAN -->
        <form v-else @submit.prevent="kirim" class="space-y-6">
            <!-- Header -->
            <div class="mb-2 flex items-center gap-3">
                <button type="button" @click="$emit('tutup')"
                    class="w-9 h-9 bg-white border border-slate-200 rounded-xl flex items-center justify-center hover:bg-slate-50 transition-colors shadow-sm">
                    <i class="pi pi-arrow-left text-slate-600 text-sm"></i>
                </button>
                <div>
                    <h2 class="text-xl font-bold text-slate-800 tracking-tight">Terima Kemasan Baru</h2>
                    <p class="text-xs text-slate-500">Pilih Purchase Order khusus kemasan untuk memulai pengecekan</p>
                </div>
            </div>

            <!-- Panel 1: Info PO & Surat Jalan -->
            <section class="bg-white border border-slate-200 rounded-[24px] p-4 md:p-6 shadow-sm w-full">
                <h2 class="text-sm font-bold text-slate-800 mb-4 pb-2 border-b border-slate-100">Referensi Dokumen</h2>
                <div class="flex flex-col gap-2 mb-4">
                    <label class="text-xs font-bold text-slate-500 uppercase tracking-wider">Pilih PO Kemasan</label>
                    <div class="relative">
                        <i class="pi pi-file-edit absolute left-4 top-1/2 -translate-y-1/2 text-slate-400"></i>
                        <select v-model.number="poIdTerpilih"
                            class="w-full pl-11 pr-4 py-3 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-slate-800 text-slate-800 appearance-none font-medium cursor-pointer"
                            required>
                            <option value="" disabled>-- Pilih PO Suplier --</option>
                            <option v-for="po in daftarPOKemasan" :key="po.id" :value="po.id">
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

            <!-- Panel 2: Tabel Input Item Khusus Kemasan -->
            <section v-if="poTerpilih" class="bg-white border border-slate-200 rounded-[24px] p-4 md:p-6 shadow-sm w-full animate-fade-in">
                <h2 class="text-sm font-bold text-slate-800 mb-4 pb-2 border-b border-slate-100 flex justify-between items-center">
                    <span>Pengecekan Fisik Kemasan</span>
                </h2>

                <div class="overflow-x-auto custom-scrollbar">
                    <table class="w-full text-left text-sm table-auto min-w-[50rem]">
                        <thead class="text-slate-500 bg-slate-50/50">
                            <tr>
                                <th class="py-3 px-4 font-semibold rounded-tl-xl w-[25%]">Nama Kemasan</th>
                                <th class="py-3 px-3 font-semibold text-right w-[15%]">Sisa PO</th>
                                <th class="py-3 px-3 font-semibold text-right w-[15%]">Qty Diterima</th>
                                <th class="py-3 px-3 font-semibold text-right w-[15%]">Ditolak</th>
                                <th class="py-3 px-4 font-semibold text-right rounded-tr-xl w-[15%]">Selisih</th>
                            </tr>
                        </thead>
                        <tbody class="divide-y divide-slate-100">
                            <tr v-for="r in baris" :key="r.po_item_id" class="hover:bg-slate-50/30 transition-colors">
                                <td class="py-4 px-4 font-bold text-slate-800 align-top">{{ r.nama_item }}</td>
                                <td class="py-4 px-3 text-right text-slate-500 font-medium align-top">{{ formatAngka(r.sisa_qty) }}</td>

                                <td class="py-3 px-3 align-top">
                                    <input v-model.number="r.qty_diterima" type="number" min="0" step="1" :max="r.sisa_qty" placeholder="0"
                                        class="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm text-right font-bold focus:ring-2 focus:ring-emerald-500" />
                                </td>

                                <td class="py-3 px-3 align-top">
                                    <input v-model.number="r.qty_ditolak" type="number" min="0" step="1" placeholder="0"
                                        class="w-full px-3 py-2 bg-slate-50 border border-rose-200 rounded-lg text-sm text-right font-bold text-rose-600 focus:ring-2 focus:ring-rose-500" />
                                </td>

                                <td class="py-4 px-4 text-right font-bold align-top" :class="{ 'text-rose-600': selisih(r) !== 0 }">
                                    <template v-if="r.qty_diterima != null">
                                        {{ formatAngka(selisih(r)) }}
                                    </template>
                                    <span v-else class="text-slate-400 font-normal">-</span>
                                </td>
                            </tr>
                        </tbody>
                    </table>
                </div>

                <!-- Notifikasi Alasan Tolak Dinamis -->
                <div class="mt-4 space-y-3">
                    <div v-for="r in baris.filter(r => Number(r.qty_ditolak) > 0)" :key="'tolak-' + r.po_item_id"
                        class="flex flex-col gap-2 p-4 border border-rose-100 bg-rose-50/30 rounded-xl">
                        <label class="text-xs font-bold text-rose-600 uppercase tracking-wider">Alasan Tolak - {{ r.nama_item }}</label>
                        <input v-model="r.alasan_tolak" type="text" required placeholder="Jelaskan alasan penolakan (contoh: penyok, sobek)..."
                            class="w-full px-4 py-2.5 bg-white border border-rose-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-rose-400 text-slate-800" />
                    </div>
                </div>

                <!-- Area Error Global & Tombol Submit -->
                <div class="mt-8 pt-6 border-t border-slate-100">
                    <div v-if="pesanError" class="mb-4 p-3 bg-red-50 border border-red-200 rounded-xl text-xs text-red-600 font-bold flex items-center gap-2">
                        <i class="pi pi-exclamation-circle"></i> {{ pesanError }}
                    </div>

                    <div class="flex justify-end gap-3">
                        <button type="button" @click="$emit('tutup')"
                            class="px-6 py-3 bg-white border border-slate-200 hover:bg-slate-50 text-slate-700 text-sm font-bold rounded-xl transition-colors">
                            Batal
                        </button>
                        <button type="submit" :disabled="sedangProses"
                            class="px-8 py-3 bg-slate-900 hover:bg-slate-800 disabled:bg-slate-300 text-white text-sm font-bold rounded-xl shadow-md transition-all flex items-center gap-2 cursor-pointer disabled:cursor-not-allowed transform hover:-translate-y-0.5">
                            <i v-if="sedangProses" class="pi pi-spin pi-spinner text-xs"></i>
                            <i v-else class="pi pi-save text-xs"></i>
                            {{ sedangProses ? 'Menyimpan...' : 'Simpan Penerimaan Kemasan' }}
                        </button>
                    </div>
                </div>
            </section>
        </form>
    </div>
</template>

<script setup>
import { ref, reactive, computed, watch, onMounted } from 'vue'

const emit = defineEmits(['tutup'])

// State Dummy untuk simulasi (Gantilah dengan composables backend Anda seperti useGoodsReceipt)
const sedangProses = ref(false)
const pesanError = ref('')
const hasil = ref(null)
const poIdTerpilih = ref('')

const form = reactive({
    no_surat_jalan: '',
    tanggal: new Date().toISOString().split('T')[0], // Hari ini
    catatan: ''
})

const baris = ref([])

// Contoh Data Dummy PO Khusus Kemasan
const daftarPOKemasan = ref([
    {
        id: 1,
        no_po: 'PO/KMS/2026/VIII/001',
        suplier_nama: 'PT PABRIK KALENG JAYA',
        item: [
            { id: 101, nama_item: 'KALENG 1 KG', sisa_qty: 3000 },
            { id: 102, nama_item: 'KARDUS KARTON A4', sisa_qty: 1500 }
        ]
    }
])

const poTerpilih = computed(() => daftarPOKemasan.value.find(po => po.id === poIdTerpilih.value) ?? null)

// Watcher untuk mengisi baris tabel otomatis saat PO dipilih
watch(poTerpilih, (po) => {
    if (!po) {
        baris.value = []
        return
    }
    baris.value = po.item.map(it => ({
        po_item_id: it.id,
        nama_item: it.nama_item,
        sisa_qty: Number(it.sisa_qty),
        qty_diterima: null,
        qty_ditolak: 0,
        alasan_tolak: '',
    }))
})

// Fungsi Helper
const selisih = (r) => {
    if (r.qty_diterima == null || r.qty_diterima === '') return null
    return Number(r.qty_diterima) - r.sisa_qty
}

const formatAngka = (num) => {
    if (num == null) return '-'
    return num.toLocaleString('id-ID')
}

// Fungsi Submit
const kirim = async () => {
    pesanError.value = ''

    const barisKirim = baris.value.filter(r => Number(r.qty_diterima) > 0)

    if (!barisKirim.length) {
        pesanError.value = 'Minimal satu kemasan harus diisi qty terima.'
        return
    }

    sedangProses.value = true

    // Simulasi hit API (Gantilah dengan simpanPenerimaan Anda)
    setTimeout(() => {
        sedangProses.value = false
        hasil.value = {
            success: true,
            pesan: 'Penerimaan kemasan berhasil disimpan ke dalam sistem.',
            penerimaan: { nomor: 'GRN/KMS/2026/VIII/099', id: 99 }
        }
    }, 1000)
}

const resetForm = () => {
    poIdTerpilih.value = ''
    form.no_surat_jalan = ''
    form.catatan = ''
    hasil.value = null
}
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
