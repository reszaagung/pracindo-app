<script setup>
import { onMounted, ref, reactive } from 'vue'
import { useRouter } from 'vue-router'

import { useInputProduksi } from '../composables/useInputProduksi'
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
} = useInputProduksi()

// Pastikan buatTangki dan memuatSimpan di-import dari useTangki
const { tangkiList, muatTangki, buatTangki, memuatSimpan: memuatSimpanTangki } = useTangki()
const { opsiRaw, opsiBatch, muatOpsi } = useSumberOptions()

const konfirmasi = ref(false)

// === STATE & FUNGSI TAMBAH TANGKI BARU ===
const tampilModalTangki = ref(false)
const formTangkiBaru = reactive({
    kode: '',
    nama: ''
})

function cekTambahTangki() {
    if (form.tangki === 'TAMBAH') {
        form.tangki = null // Bersihkan pilihan agar tidak error
        formTangkiBaru.kode = ''
        formTangkiBaru.nama = ''
        tampilModalTangki.value = true
    }
}

async function simpanTangkiBaru() {
    if (!formTangkiBaru.kode || !formTangkiBaru.nama) {
        alert('Kode dan Nama Tangki harus diisi!')
        return
    }

    try {
        const tangkiBaru = await buatTangki({
            kode: formTangkiBaru.kode.toUpperCase(),
            nama: formTangkiBaru.nama,
            aktif: true
        })

        form.tangki = tangkiBaru.id // Otomatis pilih tangki yang baru jadi
        tampilModalTangki.value = false
    } catch (e) {
        alert('Gagal menyimpan tangki baru. Periksa koneksi internet Anda.')
    }
}
// =========================================

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
                <p class="text-sm text-gray-500 mt-1">Jenis transaksi ditentukan otomatis dari sumber yang Anda pilih.</p>
            </div>
            <span class="px-3 py-1 rounded-full text-sm font-bold tracking-wide shadow-sm"
                :class="jenis === 'BLENDING' ? 'bg-purple-100 text-purple-800' : 'bg-blue-100 text-blue-800'">
                {{ jenis }}
            </span>
        </header>

        <!-- Bagian Header Dokumen -->
        <section class="grid grid-cols-1 md:grid-cols-4 gap-4 bg-gray-50 p-4 rounded-md border">

            <!-- SELECT TANGKI DENGAN FITUR TAMBAH BARU -->
            <label class="block text-sm font-medium text-gray-700">
                Tangki Tujuan <span class="text-red-500">*</span>
                <select v-model="form.tangki" @change="cekTambahTangki"
                    class="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500">
                    <option :value="null">— pilih tangki —</option>
                    <option v-for="t in tangkiList" :key="t.id" :value="t.id">
                        {{ t.kode }} ({{ t.nama }})
                    </option>

                    <!-- Opsi Tambah Tangki -->
                    <option disabled>──────────</option>
                    <option value="TAMBAH" class="font-bold text-blue-600">+ Tambah Tangki Baru...</option>
                </select>
            </label>

            <label class="block text-sm font-medium text-gray-700">
                Nama Hasil <span class="text-red-500">*</span>
                <input v-model="form.nama_hasil" type="text" maxlength="120"
                    class="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
                    placeholder="Contoh: SUGAR BROWN" />
            </label>

            <label class="block text-sm font-medium text-gray-700">
                Tekor Penyusutan (Kg)
                <input v-model="form.tekor_kg" inputmode="decimal"
                    class="mt-1 block w-full border-gray-300 rounded-md shadow-sm text-right focus:ring-blue-500 focus:border-blue-500" />
            </label>

            <label class="block text-sm font-medium text-gray-700">
                Catatan Opsional
                <input v-model="form.catatan" type="text"
                    class="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
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

        <!-- Pesan Galat Server -->
        <div v-if="galatServer" class="p-4 rounded-md border"
            :class="galatServer.invariantMelenceng ? 'bg-red-100 border-red-500 text-red-900' : 'bg-amber-50 border-amber-300 text-amber-900'">
            <div class="flex items-start gap-3">
                <div class="text-2xl mt-0.5">
                    {{ galatServer.invariantMelenceng ? '🚨' : '⚠️' }}
                </div>
                <div>
                    <h3 class="font-bold text-lg mb-1">
                        <template v-if="galatServer.invariantMelenceng">Pemeriksaan Keseimbangan Gagal (Sistem Dihentikan Sementara)</template>
                        <template v-else-if="galatServer.konflikSaldo">Konflik Saldo: Data Berubah</template>
                        <template v-else>Pengajuan Ditolak</template>
                    </h3>
                    <p class="text-sm font-medium">{{ galatServer.pesan }}</p>
                    <p v-if="galatServer.draftId" class="text-xs mt-2 italic opacity-80">
                        Jangan khawatir, isian Anda tidak hilang dan telah tersimpan dengan aman sebagai DRAFT #{{ galatServer.draftId }}.
                    </p>
                </div>
            </div>
        </div>

        <!-- Tombol Aksi Utama -->
        <footer class="flex justify-end pt-4 border-t">
            <button :disabled="!bolehSimpan" @click="konfirmasi = true"
                class="bg-blue-500 hover:bg-blue-600 text-white font-bold py-2.5 px-6 rounded-md shadow-sm transition-colors disabled:opacity-50 disabled:cursor-not-allowed">
                <span v-if="menyimpan">Menyimpan...</span>
                <span v-else>Simpan & Posting</span>
            </button>
        </footer>

        <!-- Dialog Konfirmasi Eksternal -->
        <DialogKonfirmasi v-if="konfirmasi" :judul="`Konfirmasi Posting ${jenis}`"
            :pesan="`Anda akan mem-posting dokumen ${jenis} dengan hasil ${form.nama_hasil}. Setelah di-posting, saldo tangki akan bertambah dan uang tidak dapat dikembalikan secara otomatis. Lanjutkan?`"
            @batal="konfirmasi = false" @setuju="jalankan" />

        <!-- MODAL TAMBAH TANGKI BARU -->
        <div v-if="tampilModalTangki" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
            <div class="bg-white rounded-lg shadow-xl w-full max-w-sm overflow-hidden">
                <div class="px-4 py-3 border-b border-gray-100">
                    <h3 class="text-lg font-bold text-gray-800">Tambah Tangki Baru</h3>
                </div>

                <div class="p-4 space-y-4">
                    <label class="block">
                        <span class="text-xs font-bold text-gray-500 uppercase tracking-wider">Kode Tangki</span>
                        <input v-model="formTangkiBaru.kode" type="text" placeholder="Contoh: T-05"
                            class="mt-1 block w-full border-gray-300 rounded-md shadow-sm uppercase focus:ring-blue-500 focus:border-blue-500 text-sm" />
                    </label>
                    <label class="block">
                        <span class="text-xs font-bold text-gray-500 uppercase tracking-wider">Keterangan / Nama</span>
                        <input v-model="formTangkiBaru.nama" type="text" placeholder="Contoh: Tangki Oksidasi"
                            class="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 text-sm" />
                    </label>
                </div>

                <div class="bg-gray-50 px-4 py-3 border-t border-gray-100 flex justify-end gap-2">
                    <button type="button" @click="tampilModalTangki = false"
                        class="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded hover:bg-gray-50 transition-colors">
                        Batal
                    </button>
                    <button type="button" @click="simpanTangkiBaru" :disabled="memuatSimpanTangki"
                        class="px-4 py-2 text-sm font-bold text-white bg-blue-600 rounded hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors">
                        <span v-if="memuatSimpanTangki">Menyimpan...</span>
                        <span v-else>Simpan Tangki</span>
                    </button>
                </div>
            </div>
        </div>
    </div>
</template>
