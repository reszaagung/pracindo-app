<script setup>
import { onMounted, ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useInputProduksi } from '../composables/useInputProduksi'
import { useSumberOptions } from '../composables/useSumberOptions'
import { useTangki } from '../composables/useTangki'
import BarisSumber from '../components/BarisSumber.vue'
import PanelValuasi from '../components/PanelValuasi.vue'
import DialogKonfirmasi from '@/components/DialogKonfirmasi.vue'

const router = useRouter()
const {
    form, jenis, menyimpan, galatServer,
    galatBaris, valuasiBaris, bolehSimpan,
    tambahBaris, hapusBaris, simpanDanPosting,
} = useInputProduksi()

const { tangkiList, muatTangki, buatTangki, memuatSimpan: memuatSimpanTangki } = useTangki()
const { opsiRaw, opsiBatch, muatOpsi } = useSumberOptions()
const konfirmasi = ref(false)

const tampilModalTangki = ref(false)
const formTangkiBaru = reactive({ kode: '', nama: '' })

function cekTambahTangki() {
    if (form.tangki === 'TAMBAH') {
        form.tangki = null
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
        form.tangki = tangkiBaru.id
        tampilModalTangki.value = false
    } catch (e) {
        alert('Gagal menyimpan tangki baru. Periksa koneksi internet Anda.')
    }
}

onMounted(() => {
    muatTangki()
    muatOpsi()
})

async function jalankan() {
    konfirmasi.value = false
    try {
        const batch = await simpanDanPosting()
        router.push({ name: 'produksi-batch-detail', params: { id: batch.id } })
    } catch (e) {
        if (e.konflikSaldo) await muatOpsi()
    }
}
</script>

<template>
    <div class="batch-form w-full mx-auto pb-12 px-3 sm:px-4 space-y-6 md:space-y-8 mt-2 md:mt-4">

        <header class="flex flex-col sm:flex-row sm:justify-between sm:items-end border-b border-slate-200 pb-4 gap-3">
            <div>
                <h1 class="text-2xl font-bold text-slate-800">Input Produksi</h1>
                <p class="text-sm text-slate-500 mt-1">Jenis transaksi akan menyesuaikan secara otomatis.</p>
            </div>
            <div class="inline-flex items-center justify-center px-3 py-1 rounded-md text-xs font-bold tracking-wide uppercase shadow-sm border self-start sm:self-auto"
                :class="jenis === 'BLENDING' ? 'bg-purple-50 text-purple-700 border-purple-200' : 'bg-blue-50 text-blue-700 border-blue-200'">
                <i class="pi mr-2" :class="jenis === 'BLENDING' ? 'pi-sync' : 'pi-sitemap'"></i>
                {{ jenis }}
            </div>
        </header>

        <section class="bg-white p-4 md:p-5 rounded-lg shadow-sm border border-slate-200">
            <!-- Penyesuaian Grid: Hanya maksimal 2 kolom agar muat di panel sempit -->
            <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <label class="block">
                    <span class="text-xs font-semibold text-slate-700 mb-1.5 block">Tangki Tujuan <span class="text-red-500">*</span></span>
                    <select v-model="form.tangki" @change="cekTambahTangki"
                        class="block w-full border-slate-300 rounded-md shadow-sm text-sm py-1.5 px-3 focus:ring-1 focus:ring-blue-500 focus:border-blue-500 bg-white">
                        <option :value="null">-- Pilih Tangki --</option>
                        <option v-for="t in tangkiList" :key="t.id" :value="t.id">{{ t.kode }} ({{ t.nama }})</option>
                        <option disabled>──────────</option>
                        <option value="TAMBAH" class="font-bold text-blue-600">+ Tambah Tangki Baru...</option>
                    </select>
                </label>

                <label class="block">
                    <span class="text-xs font-semibold text-slate-700 mb-1.5 block">Nama Hasil <span class="text-red-500">*</span></span>
                    <input v-model="form.nama_hasil" type="text" maxlength="120"
                        class="block w-full border-slate-300 rounded-md shadow-sm text-sm py-1.5 px-3 focus:ring-1 focus:ring-blue-500 focus:border-blue-500 bg-white placeholder:text-slate-300"
                        placeholder="Contoh: SUGAR BROWN" />
                </label>

                <label class="block">
                    <span class="text-xs font-semibold text-slate-700 mb-1.5 block">Tekor / Susut (Kg)</span>
                    <div class="relative">
                        <input v-model="form.tekor_kg" type="text" inputmode="decimal" pattern="[0-9]*[.,]?[0-9]*"
                            class="block w-full border-slate-300 rounded-md shadow-sm text-sm py-1.5 pr-8 pl-3 text-right focus:ring-1 focus:ring-blue-500 focus:border-blue-500 bg-white" />
                        <div class="absolute inset-y-0 right-0 flex items-center pr-2.5 pointer-events-none">
                            <span class="text-xs font-medium text-slate-400">Kg</span>
                        </div>
                    </div>
                </label>

                <label class="block">
                    <span class="text-xs font-semibold text-slate-700 mb-1.5 block">Catatan Tambahan</span>
                    <input v-model="form.catatan" type="text"
                        class="block w-full border-slate-300 rounded-md shadow-sm text-sm py-1.5 px-3 focus:ring-1 focus:ring-blue-500 focus:border-blue-500 bg-white placeholder:text-slate-300"
                        placeholder="Opsional..." />
                </label>
            </div>
        </section>

        <section class="space-y-3">
            <div class="flex justify-between items-center px-1 border-b border-slate-200 pb-2">
                <h2 class="text-base font-bold text-slate-800 flex items-center gap-2">
                    <i class="pi pi-box text-blue-500 text-sm"></i> Bahan Sumber
                </h2>
                <button type="button" @click="tambahBaris"
                    class="text-xs bg-white hover:bg-slate-50 border border-slate-300 text-slate-700 px-3 py-1.5 rounded-md font-semibold transition-colors shadow-sm flex items-center gap-2">
                    <i class="pi pi-plus text-[10px]"></i> <span class="hidden sm:inline">Tambah Sumber</span><span class="sm:hidden">Tambah</span>
                </button>
            </div>

            <div class="space-y-2.5">
                <!-- PERBAIKAN: Gunakan (b, index) dan v-model="form.baris[index]" -->
                <BarisSumber v-for="(b, index) in form.baris" :key="b._id"
                    v-model="form.baris[index]"
                    :opsi-raw="opsiRaw" :opsi-batch="opsiBatch"
                    :valuasi="valuasiBaris[b.sumber === 'RAW' ? `RAW:${b.raw}` : `WIP:${b.batch_sumber}`]"
                    :galat="galatBaris[b._id]" :bisa-hapus="form.baris.length > 1"
                    @hapus="hapusBaris(b._id)" />
            </div>
        </section>

        <PanelValuasi :form="form" :opsi-raw="opsiRaw" :opsi-batch="opsiBatch" :tangki-list="tangkiList" />

        <div v-if="galatServer" class="p-4 rounded-lg border shadow-sm"
            :class="galatServer.invariantMelenceng ? 'bg-red-50 border-red-300' : 'bg-amber-50 border-amber-300'">
            <div class="flex items-start gap-3">
                <div class="mt-0.5">
                    <i class="pi" :class="galatServer.invariantMelenceng ? 'pi-times-circle text-red-600 text-xl' : 'pi-exclamation-triangle text-amber-600 text-xl'"></i>
                </div>
                <div>
                    <h3 class="font-bold text-sm mb-1" :class="galatServer.invariantMelenceng ? 'text-red-900' : 'text-amber-900'">
                        <template v-if="galatServer.invariantMelenceng">Sistem Dihentikan (Pemeriksaan Gagal)</template>
                        <template v-else-if="galatServer.konflikSaldo">Konflik Saldo Material</template>
                        <template v-else>Pengajuan Ditolak</template>
                    </h3>
                    <p class="text-sm text-slate-700">{{ galatServer.pesan }}</p>
                    <p v-if="galatServer.draftId" class="text-xs mt-2 italic text-slate-500">
                        Isian tersimpan sebagai DRAFT #{{ galatServer.draftId }}.
                    </p>
                </div>
            </div>
        </div>

        <!-- Tombol Aksi Utama -->
        <footer class="pt-4 flex justify-end">
            <button :disabled="!bolehSimpan" @click="konfirmasi = true"
                class="w-full sm:w-auto bg-slate-800 hover:bg-slate-900 text-white font-semibold text-sm py-2 px-6 rounded-lg shadow transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2">
                <i v-if="menyimpan" class="pi pi-spinner pi-spin text-xs"></i>
                <i v-else class="pi pi-send text-xs"></i>
                <span v-if="menyimpan">Menyimpan...</span>
                <span v-else>Simpan & Posting Data</span>
            </button>
        </footer>

        <!-- Dialog-Dialog -->
        <DialogKonfirmasi v-if="konfirmasi" :judul="`Konfirmasi Posting ${jenis}`"
            :pesan="`Anda akan mem-posting dokumen ${jenis} dengan hasil ${form.nama_hasil}. Setelah di-posting, saldo tangki akan bertambah dan uang tidak dapat dikembalikan secara otomatis. Lanjutkan?`"
            @batal="konfirmasi = false" @setuju="jalankan" />

        <div v-if="tampilModalTangki" class="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-slate-900/50 backdrop-blur-sm">
            <div class="bg-white rounded-xl shadow-xl w-full max-w-sm overflow-hidden">
                <div class="px-5 py-4 border-b border-slate-100 bg-slate-50 flex items-center gap-2">
                    <i class="pi pi-database text-blue-600"></i>
                    <h3 class="text-sm font-bold text-slate-800">Tambah Tangki Baru</h3>
                </div>
                <div class="p-5 space-y-4">
                    <label class="block">
                        <span class="text-xs font-semibold text-slate-700 mb-1.5 block">Kode Tangki</span>
                        <input v-model="formTangkiBaru.kode" type="text" placeholder="T-05"
                            class="block w-full border-slate-300 rounded-md shadow-sm uppercase focus:ring-1 focus:ring-blue-500 focus:border-blue-500 text-sm py-1.5 px-3 bg-white" />
                    </label>
                    <label class="block">
                        <span class="text-xs font-semibold text-slate-700 mb-1.5 block">Nama / Keterangan</span>
                        <input v-model="formTangkiBaru.nama" type="text" placeholder="Tangki Blue Cw"
                            class="block w-full border-slate-300 rounded-md shadow-sm focus:ring-1 focus:ring-blue-500 focus:border-blue-500 text-sm py-1.5 px-3 bg-white" />
                    </label>
                </div>
                <div class="bg-slate-50 px-5 py-3 border-t border-slate-100 flex justify-end gap-2">
                    <button type="button" @click="tampilModalTangki = false"
                        class="px-4 py-1.5 text-sm font-semibold text-slate-600 bg-white border border-slate-300 rounded-md hover:bg-slate-50 transition-colors">
                        Batal
                    </button>
                    <button type="button" @click="simpanTangkiBaru" :disabled="memuatSimpanTangki"
                        class="px-4 py-1.5 text-sm font-semibold text-white bg-blue-600 rounded-md hover:bg-blue-700 shadow-sm disabled:opacity-50 transition-colors flex items-center gap-2">
                        <i v-if="memuatSimpanTangki" class="pi pi-spinner pi-spin"></i>
                        <span v-if="memuatSimpanTangki">Memproses...</span>
                        <span v-else>Simpan</span>
                    </button>
                </div>
            </div>
        </div>
    </div>
</template>
