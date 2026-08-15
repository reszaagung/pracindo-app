<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

import { useBatchForm } from '../composables/useBatchForm'
import { useSumberOptions } from '../composables/useSumberOptions'
import { useTangki } from '../composables/useTangki'

import BarisSumber from '../components/BarisSumber.vue'
import PanelValuasi from '../components/PanelValuasi.vue'

// Menggunakan komponen global yang sudah ada di luar modul produksi
import DialogKonfirmasi from '@/components/DialogKonfirmasi.vue'

const router = useRouter()

const {
    form, jenis, pratinjau, memuat, menyimpan, galatServer,
    galatBaris, galatUmum, valuasiBaris, bolehSimpan,
    tambahBaris, hapusBaris, simpanDanPosting,
} = useBatchForm()

const { tangkiList, muatTangki } = useTangki()
const { opsiRaw, opsiBatch, muatOpsi } = useSumberOptions()

const konfirmasi = ref(false)

onMounted(() => {
    muatTangki()
    muatOpsi()
})

async function jalankan() {
    konfirmasi.value = false
    try {
        const batch = await simpanDanPosting()
        // Jika berhasil, arahkan langsung ke halaman detail batch yang baru diposting
        router.push({ name: 'produksi-batch-detail', params: { id: batch.id } })
    } catch (e) {
        // 409 Konflik Saldo: Kenyataan menolak karena saldo berubah di detik terakhir.
        // Solusinya: muat ulang opsi sumber agar operator mendapat angka stok terbaru.
        if (e.konflikSaldo) {
            await muatOpsi()
        }
    }
}
</script>

<template>
    <div class="batch-form max-w-5xl mx-auto pb-10 space-y-6">
        <header class="flex justify-between items-end border-b pb-4">
            <div>
                <h1 class="text-2xl font-bold text-gray-800">Input Produksi</h1>
                <p class="text-sm text-gray-500 mt-1">Jenis transaksi ditentukan otomatis dari sumber yang Anda pilih.
                </p>
            </div>
            <span class="px-3 py-1 rounded-full text-sm font-bold tracking-wide shadow-sm"
                :class="jenis === 'BLENDING' ? 'bg-purple-100 text-purple-800' : 'bg-blue-100 text-blue-800'">
                {{ jenis }}
            </span>
        </header>

        <!-- Bagian Header Dokumen -->
        <section class="grid grid-cols-1 md:grid-cols-4 gap-4 bg-gray-50 p-4 rounded-md border">
            <label class="block text-sm font-medium text-gray-700">
                Tangki Tujuan <span class="text-red-500">*</span>
                <select v-model="form.tangki" class="mt-1 block w-full border-gray-300 rounded-md shadow-sm">
                    <option :value="null">— pilih tangki —</option>
                    <option v-for="t in tangkiList" :key="t.id" :value="t.id">
                        {{ t.kode }} ({{ t.nama }})
                    </option>
                </select>
            </label>

            <label class="block text-sm font-medium text-gray-700">
                Nama Hasil <span class="text-red-500">*</span>
                <input v-model="form.nama_hasil" type="text" maxlength="120"
                    class="mt-1 block w-full border-gray-300 rounded-md shadow-sm" placeholder="Contoh: SUGAR BROWN" />
            </label>

            <label class="block text-sm font-medium text-gray-700">
                Tekor Penyusutan (Kg)
                <input v-model="form.tekor_kg" inputmode="decimal"
                    class="mt-1 block w-full border-gray-300 rounded-md shadow-sm text-right" />
            </label>

            <label class="block text-sm font-medium text-gray-700">
                Catatan Opsional
                <input v-model="form.catatan" type="text" class="mt-1 block w-full border-gray-300 rounded-md shadow-sm"
                    placeholder="Catatan produksi..." />
            </label>
        </section>

        <!-- Bagian Baris Sumber -->
        <section class="sumber space-y-3">
            <div class="flex justify-between items-center mb-2">
                <h2 class="text-lg font-semibold text-gray-800">Bahan Sumber</h2>
                <button type="button" @click="tambahBaris"
                    class="text-sm bg-gray-100 hover:bg-gray-200 border text-gray-700 px-3 py-1.5 rounded-md font-medium transition-colors">
                    + Tambah Sumber
                </button>
            </div>

            <div class="space-y-3">
                <BarisSumber v-for="b in form.baris" :key="b._id" v-model="form.baris[form.baris.indexOf(b)]"
                    :opsi-raw="opsiRaw" :opsi-batch="opsiBatch"
                    :valuasi="valuasiBaris[b.sumber === 'RAW' ? `RAW:${b.raw}` : `WIP:${b.batch_sumber}`]"
                    :galat="galatBaris[b._id]" :bisa-hapus="form.baris.length > 1" @hapus="hapusBaris(b._id)" />
            </div>
        </section>

        <!-- Panel Informasi Angka & Valuasi -->
        <PanelValuasi :pratinjau="pratinjau" :memuat="memuat" :galat-umum="galatUmum" />

        <!-- Pesan Galat Server (Hanya muncul saat submit gagal) -->
        <div v-if="galatServer" class="p-4 rounded-md border"
            :class="galatServer.invariantMelenceng ? 'bg-red-100 border-red-500 text-red-900' : 'bg-amber-50 border-amber-300 text-amber-900'">
            <div class="flex items-start gap-3">
                <div class="text-2xl mt-0.5">
                    {{ galatServer.invariantMelenceng ? '🚨' : '⚠️' }}
                </div>
                <div>
                    <h3 class="font-bold text-lg mb-1">
                        <template v-if="galatServer.invariantMelenceng">Pemeriksaan Keseimbangan Gagal (Sistem
                            Dihentikan Sementara)</template>
                        <template v-else-if="galatServer.konflikSaldo">Konflik Saldo: Data Berubah</template>
                        <template v-else>Pengajuan Ditolak</template>
                    </h3>
                    <p class="text-sm font-medium">{{ galatServer.pesan }}</p>
                    <p v-if="galatServer.draftId" class="text-xs mt-2 italic opacity-80">
                        Jangan khawatir, isian Anda tidak hilang dan telah tersimpan dengan aman sebagai DRAFT #{{
                        galatServer.draftId }}.
                    </p>
                </div>
            </div>
        </div>

        <!-- Tombol Aksi Utama -->
        <footer class="flex justify-end pt-4 border-t">
            <button :disabled="!bolehSimpan" @click="konfirmasi = true"
                class="bg-blue-600 hover:bg-blue-700 text-white font-bold py-2.5 px-6 rounded-md shadow-sm transition-colors disabled:opacity-50 disabled:cursor-not-allowed">
                <span v-if="menyimpan">Menyimpan...</span>
                <span v-else>Simpan & Posting</span>
            </button>
        </footer>

        <!-- Dialog Konfirmasi Eksternal -->
        <DialogKonfirmasi v-if="konfirmasi" :judul="`Konfirmasi Posting ${jenis}`"
            :pesan="`Anda akan mem-posting dokumen ${jenis} dengan hasil ${form.nama_hasil}. Setelah di-posting, saldo tangki akan bertambah dan uang tidak dapat dikembalikan secara otomatis. Lanjutkan?`"
            @batal="konfirmasi = false" @setuju="jalankan" />
    </div>
</template>