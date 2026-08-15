<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useBatchDetail } from '../composables/useBatchDetail'
import TabelKomposisi from '../components/TabelKomposisi.vue'
import DialogVoid from '../components/DialogVoid.vue'
import { STATUS_BATCH, WARNA_STATUS } from '../constants'
import { formatKg, formatRp, formatHarga } from '@/utils/uang'

const props = defineProps({
    id: { type: [String, Number], required: true }
})

const router = useRouter()
const { detail, komposisi, memuat, muatDetail, batalkan } = useBatchDetail()

const bukaDialogVoid = ref(false)
const galatVoid = ref(null)

onMounted(() => {
    muatDetail(props.id).catch(() => router.push({ name: 'produksi-batch' }))
})

async function jalankanVoid(alasan) {
    bukaDialogVoid.value = false
    galatVoid.value = null
    try {
        await batalkan(props.id, alasan)
    } catch (e) {
        // Tampilkan pesan penolakan Void dari backend apa adanya (biasanya KonflikSaldo)
        galatVoid.value = e.pesan || "Terjadi kesalahan saat membatalkan dokumen."
    }
}
</script>

<template>
    <div v-if="memuat" class="flex justify-center py-20 text-gray-400 animate-pulse">
        Memuat rincian batch...
    </div>

    <div v-else-if="detail" class="batch-detail max-w-5xl mx-auto pb-10 space-y-6">
        <!-- Header -->
        <header class="flex justify-between items-end border-b pb-4">
            <div>
                <div class="flex items-center gap-3 mb-1">
                    <button @click="router.push({ name: 'produksi-batch' })" class="text-gray-400 hover:text-gray-600">
                        ← Kembali
                    </button>
                    <span class="px-2.5 py-1 text-[10px] font-bold uppercase rounded-md shadow-sm border"
                        :class="WARNA_STATUS[detail.status]">
                        {{ detail.status }}
                    </span>
                </div>
                <h1 class="text-3xl font-bold text-gray-900">{{ detail.nomor || 'DRAFT Belum Diposting' }}</h1>
                <p class="text-sm font-medium text-gray-500 uppercase tracking-widest mt-1">{{ detail.jenis }}</p>
            </div>

            <!-- Tombol Aksi -->
            <div v-if="detail.status === STATUS_BATCH.POSTED">
                <button @click="bukaDialogVoid = true"
                    class="bg-white text-red-600 border border-red-200 hover:bg-red-50 hover:border-red-300 font-bold py-2 px-4 rounded-md shadow-sm transition-colors text-sm">
                    ✖ Batalkan (Void)
                </button>
            </div>
        </header>

        <!-- Galat Void (Jika ada penolakan) -->
        <div v-if="galatVoid" class="bg-red-50 border border-red-200 p-4 rounded-md text-red-800 text-sm flex gap-3">
            <div class="text-xl">🛑</div>
            <div>
                <strong class="block mb-1">Pembatalan Ditolak</strong>
                {{ galatVoid }}
            </div>
        </div>

        <!-- Ringkasan Nilai & Fisik -->
        <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div class="bg-gray-50 border rounded p-4">
                <p class="text-xs text-gray-500 font-bold uppercase mb-1">Hasil</p>
                <p class="font-medium text-gray-900 truncate">{{ detail.nama_hasil }}</p>
            </div>
            <div class="bg-gray-50 border rounded p-4">
                <p class="text-xs text-gray-500 font-bold uppercase mb-1">Masuk Tangki</p>
                <p class="font-medium text-gray-900">{{ detail.tangki_kode }}</p>
            </div>
            <div class="bg-blue-50 border border-blue-100 rounded p-4">
                <p class="text-xs text-blue-500 font-bold uppercase mb-1">Total Nilai</p>
                <p class="font-bold text-blue-900 text-lg">{{ formatRp(detail.nilai_hasil) }}</p>
                <p class="text-xs text-blue-700 font-medium">Qty: {{ formatKg(detail.qty_hasil) }}</p>
            </div>
            <div class="bg-gray-50 border rounded p-4">
                <p class="text-xs text-gray-500 font-bold uppercase mb-1">HPP per Kg</p>
                <p class="font-bold text-gray-900 text-lg">{{ formatHarga(detail.harga_hasil_per_kg) }}</p>
            </div>
        </div>

        <!-- BOM Explosion -->
        <section v-if="komposisi" class="mt-6">
            <TabelKomposisi :komposisi="komposisi" />
        </section>

        <!-- Dialog -->
        <DialogVoid v-if="bukaDialogVoid" :nomor="detail.nomor" @batal="bukaDialogVoid = false"
            @setuju="jalankanVoid" />
    </div>
</template>