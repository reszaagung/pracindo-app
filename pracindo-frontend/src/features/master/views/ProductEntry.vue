<!-- ProductEntry.vue -->
<template>
    <Dialog visible modal header="Tambah Produk (Bahan Baku)" :style="{ width: '90vw', maxWidth: '600px' }"
        :closable="false" class="p-fluid" @update:visible="$emit('close')">
        <template #header>
            <div class="flex items-center justify-between w-full">
                <h3 class="text-xl font-bold text-slate-800 m-0">Tambah Produk Baru</h3>
                <button @click="$emit('close')" class="p-2 text-slate-400 hover:text-slate-600 transition-colors">
                    <i class="pi pi-times text-lg"></i>
                </button>
            </div>
        </template>

        <form @submit.prevent="simpanProduk" class="mt-4 flex flex-col gap-4">

            <div v-if="errorMsg"
                class="p-4 bg-red-50 border border-red-200 rounded-xl text-sm text-red-600 font-medium flex items-start gap-3">
                <i class="pi pi-exclamation-triangle mt-0.5"></i>
                <span>{{ errorMsg }}</span>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div class="flex flex-col gap-2">
                    <label class="text-xs font-bold text-slate-700">Kode Produk <span
                            class="text-red-500">*</span></label>
                    <input v-model="form.kode" type="text" required maxlength="24" placeholder="Contoh: B-P-01"
                        class="px-4 py-2 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-emerald-500 text-sm text-slate-800 uppercase" />
                </div>

                <!-- Nama Produk -->
                <div class="flex flex-col gap-2">
                    <label class="text-xs font-bold text-slate-700">Nama Produk <span
                            class="text-red-500">*</span></label>
                    <input v-model="form.nama" type="text" required maxlength="200"
                        placeholder="Masukkan nama produk..."
                        class="px-4 py-2 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-emerald-500 text-sm text-slate-800" />
                </div>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div class="flex flex-col gap-2">
                    <label class="text-xs font-bold text-slate-700">Jenis Produk <span
                            class="text-red-500">*</span></label>
                    <Dropdown v-model="form.jenis" :options="opsiJenis" optionLabel="label" optionValue="value"
                        placeholder="Pilih Jenis" class="w-full" :pt="{
                            root: { class: 'bg-slate-50 border border-slate-200 rounded-xl h-[38px] flex items-center' }
                        }" />
                </div>
                <div class="flex flex-col gap-2">
                    <label class="text-xs font-bold text-slate-700">Satuan <span class="text-red-500">*</span></label>
                    <Dropdown v-model="form.satuan_id" :options="daftarSatuan" optionLabel="nama" optionValue="id"
                        appendTo="body" placeholder="Pilih Satuan" :loading="loadingMaster" class="w-full" />
                </div>
            </div>
            <div class="flex flex-col gap-2">
                <label class="text-xs font-bold text-slate-700">Katalog Suplier <em
                        class="font-normal text-slate-400 text-[10px]">(Opsional - Bisa pilih lebih dari
                        satu)</em></label>
                <MultiSelect v-model="form.suplier_ids" :options="listSuplier" optionLabel="nama" optionValue="id"
                    placeholder="Pilih suplier penyedia produk ini..." :loading="loadingMaster" display="chip"
                    class="w-full" :pt="{
                        root: { class: 'bg-slate-50 border border-slate-200 rounded-xl min-h-[38px] flex items-center' }
                    }" />
            </div>

            <div class="flex items-center justify-end border-t border-slate-100 pt-4 mt-2">
                <div class="flex gap-3">
                    <button type="button" @click="$emit('close')" :disabled="isSubmitting"
                        class="px-5 py-2 text-sm font-bold text-slate-500 hover:text-slate-700 transition-colors disabled:opacity-50">
                        Batal
                    </button>
                    <button type="submit" :disabled="isSubmitting || daftarSatuan.length === 0"
                        class="px-5 py-2 bg-emerald-600 hover:bg-emerald-700 disabled:bg-slate-400 text-white text-sm font-bold rounded-xl shadow-sm transition-colors flex items-center gap-2">
                        <i class="pi" :class="isSubmitting ? 'pi-spin pi-spinner' : 'pi-save'"></i>
                        Simpan
                    </button>
                </div>
            </div>
        </form>
    </Dialog>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import Dialog from 'primevue/dialog'
import Dropdown from 'primevue/dropdown'
import MultiSelect from 'primevue/multiselect'
import api from '@/utils/api'

import { useProduct } from '@/features/master/composables/useProduct'
const { addProduk } = useProduct()
const emit = defineEmits(['close', 'saved'])

const isSubmitting = ref(false)
const loadingMaster = ref(false)
const errorMsg = ref('')

const daftarSatuan = ref([])
const listSuplier = ref([])

const opsiJenis = [
    { label: 'Bahan Baku', value: 'BAHAN_BAKU' },
    { label: 'Barang Jadi', value: 'BARANG_JADI' },
    { label: 'Kemasan', value: 'KEMASAN' },
    { label: 'Lain-lain', value: 'LAIN' }
]

const form = reactive({
    kode: '',
    nama: '',
    jenis: 'BAHAN_BAKU',
    satuan_id: null,
    suplier_ids: [],
    aktif: true
})

const loadDataMaster = async () => {
    loadingMaster.value = true
    try {
        const [resSat, resSup] = await Promise.allSettled([
            api.get('master/satuan/'),
            api.get('master/suplier/', { params: { ringkas: 1, aktif: true } })
        ])

        if (resSat.status === 'fulfilled') {
            const satuanDariServer = resSat.value.data.results || resSat.value.data || []
            if (satuanDariServer.length > 0) {
                daftarSatuan.value = satuanDariServer.map(s => ({
                    id: s.id, 
                    nama: s.nama || s.kode,
                    kode: s.kode
                }))
            } else {
                errorMsg.value = 'Data Master Satuan di database masih kosong. Silakan tambahkan data satuan melalui Django Admin.'
            }
        }

        if (resSup.status === 'fulfilled') {
            listSuplier.value = resSup.value.data.results || resSup.value.data || []
        }
        if (daftarSatuan.value.length > 0) {
            const satuanKg = daftarSatuan.value.find(s =>
                String(s.kode).toLowerCase() === 'kg' || String(s.nama).toLowerCase().includes('kg')
            )
            form.satuan_id = satuanKg ? satuanKg.id : daftarSatuan.value[0].id
        }
    } catch (err) {
        console.error('Gagal memuat master:', err)
        errorMsg.value = 'Gagal terhubung ke database. Coba muat ulang halaman.'
    } finally {
        loadingMaster.value = false
    }
}

const simpanProduk = async () => {
    if (!form.satuan_id) {
        alert('❌ Gagal: Satuan wajib dipilih.')
        errorMsg.value = 'Satuan wajib dipilih.'
        return
    }

    isSubmitting.value = true
    errorMsg.value = ''

    const payload = {
        kode: form.kode.toUpperCase(),
        nama: form.nama,
        jenis: form.jenis,
        satuan: form.satuan_id,
        suplier: form.suplier_ids,
        aktif: form.aktif
    }

    const result = await addProduk(payload)

    if (result.success) {
        alert("✅ Produk baru berhasil ditambahkan!")
        emit('saved', result.data)
    } else {
        alert("❌ Gagal menyimpan produk:\n" + result.message)
        errorMsg.value = result.message || 'Terjadi kesalahan saat menyimpan produk.'
    }

    isSubmitting.value = false
}

onMounted(() => {
    loadDataMaster()
})
</script>