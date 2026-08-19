<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useBatchDetail } from '../composables/useBatchDetail'
import TabelKomposisi from '../components/TabelKomposisi.vue'
import DialogVoid from '../components/DialogVoid.vue'
import { formatKg } from '@/utils/uang'
import { WARNA_STATUS } from '../constants'

const props = defineProps({ id: { type: [String, Number], required: true } })
const router = useRouter()
const { detail, komposisi, memuat, muatDetail, batalkan } = useBatchDetail()
const tampilVoid = ref(false)

onMounted(() => {
    muatDetail(props.id)
})

async function prosesVoid(alasan) {
    try {
        await batalkan(props.id, alasan)
        tampilVoid.value = false
    } catch (e) {
        alert('Gagal melakukan Void. Silakan coba lagi.')
    }
}
</script>

<template>
    <div class="batch-detail max-w-5xl mx-auto pb-10 space-y-6">
         <header class="flex justify-between items-center border-b pb-4">
            <div class="flex items-center gap-4">
                <button @click="router.push({ name: 'produksi-batch' })" class="text-gray-500 hover:text-gray-800 flex items-center gap-2">
                    <i class="pi pi-arrow-left"></i> Kembali
                </button>
                <h1 class="text-2xl font-bold text-gray-800">Detail Batch</h1>
            </div>
            <span v-if="detail" class="px-3 py-1 text-xs font-bold uppercase rounded-md border" :class="WARNA_STATUS[detail.status]">
                {{ detail.status }}
            </span>
         </header>

         <div v-if="memuat" class="py-10 text-center text-gray-500 animate-pulse">Memuat rincian dokumen...</div>

         <template v-else-if="detail">
            <section class="grid grid-cols-2 md:grid-cols-4 gap-4 bg-gray-50 p-4 rounded-md border text-sm">
                <div>
                    <p class="text-gray-500 mb-1">Nomor Batch</p>
                    <p class="font-bold text-gray-900">{{ detail.nomor }}</p>
                </div>
                <div>
                    <p class="text-gray-500 mb-1">Tangki Tujuan</p>
                    <p class="font-bold text-gray-900">{{ detail.tangki_kode }}</p>
                </div>
                <div>
                    <p class="text-gray-500 mb-1">Hasil (Nama)</p>
                    <p class="font-bold text-gray-900">{{ detail.nama_hasil }}</p>
                </div>
                <div>
                    <p class="text-gray-500 mb-1">Total Tersimpan</p>
                    <p class="font-bold text-gray-900">{{ formatKg(detail.qty_hasil) }}</p>
                </div>
            </section>

            <TabelKomposisi v-if="komposisi" :komposisi="komposisi" />

            <div v-if="detail.status === 'POSTED'" class="flex justify-end pt-4">
                <button @click="tampilVoid = true" class="bg-red-50 text-red-600 border border-red-200 px-4 py-2 rounded-md hover:bg-red-100 transition font-medium">
                    Batalkan (Void) Dokumen Ini
                </button>
            </div>

            <DialogVoid v-if="tampilVoid" :nomor="detail.nomor" @batal="tampilVoid = false" @setuju="prosesVoid" />
         </template>
    </div>
</template>
