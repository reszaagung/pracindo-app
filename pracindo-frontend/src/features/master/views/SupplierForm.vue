<!--
  src/features/master/views/SupplierForm.vue
  ==========================================
  Form input Master Suplier (tambah & ubah), dipakai sebagai komponen anak
  overlay oleh Supplier.vue. Komponen ini TIDAK memuat daftar — induk yang
  bertanggung jawab me-refresh tabel lewat event `saved`.

  prop `suplier`: null = tambah, objek baris = ubah.
-->
<template>
    <div
        class="fixed inset-0 z-[100] flex items-center justify-center bg-slate-900/60 backdrop-blur-sm p-4 sm:p-6 animate-fade-in">

        <div
            class="bg-white w-full max-w-3xl rounded-[32px] shadow-2xl relative flex flex-col max-h-[90vh] overflow-hidden animate-fade-in-up">

            <button type="button" @click="emit('close')" :disabled="sedangProses"
                class="absolute top-6 right-6 w-10 h-10 bg-slate-100 hover:bg-red-100 text-slate-500 hover:text-red-600 rounded-full flex items-center justify-center transition-colors z-10 disabled:opacity-50">
                <i class="pi pi-times"></i>
            </button>

            <div class="p-8 overflow-y-auto custom-scrollbar">
                <h2 class="text-3xl font-extrabold text-slate-800 mb-2">
                    {{ ubah ? 'Ubah Data Suplier' : 'Tambah Suplier Baru' }}
                </h2>
                <p class="text-slate-500 mb-8">
                    {{ ubah
                        ? `Memperbarui data ${suplier.kode} — ${suplier.nama}.`
                        : 'Mendaftarkan data vendor atau suplier baru ke dalam sistem.' }}
                </p>

                <div v-if="pesanError"
                    class="mb-6 p-4 bg-red-50 text-red-600 rounded-xl border border-red-200 text-sm whitespace-pre-line">
                    {{ pesanError }}
                </div>

                <form class="form-suplier flex flex-col gap-6" @submit.prevent="simpan">
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div>
                            <label>Kode Suplier <span class="text-red-500">*</span></label>
                            <InputText v-model="form.kode" :readonly="ubah" :invalid="!!errorField.kode"
                                placeholder="SUP-001" class="w-full uppercase" :class="ubah ? 'bg-slate-100!' : ''" />
                            <small v-if="ubah" class="text-slate-400">Dikunci — kode dipakai PO lama.</small>
                            <small v-if="errorField.kode" class="text-red-600">{{ errorField.kode }}</small>
                        </div>
                        <div>
                            <label>Nama Perusahaan <span class="text-red-500">*</span></label>
                            <InputText v-model="form.nama" :invalid="!!errorField.nama"
                                placeholder="PT Sumber Makmur Jaya" class="w-full" />
                            <small v-if="errorField.nama" class="text-red-600">{{ errorField.nama }}</small>
                        </div>
                    </div>

                    <div>
                        <div class="flex items-center gap-2 mb-1">
                            <label class="mb-0!">NPWP</label>
                            <!-- pkp read-only: properti turunan npwp di backend, bukan input -->
                            <Tag :value="pkpLabel" :severity="adaNpwp ? 'success' : 'secondary'" />
                        </div>
                        <InputMask v-model="form.npwp" mask="99.999.999.9-999.999" placeholder="__.___.___._-___.___"
                            :invalid="!!errorField.npwp" class="w-full" />
                        <small class="text-slate-400">Kosongkan kalau suplier non-PKP.</small>
                        <small v-if="errorField.npwp" class="text-red-600">{{ errorField.npwp }}</small>
                    </div>

                    <div>
                        <label>Alamat</label>
                        <Textarea v-model="form.alamat" rows="3" :invalid="!!errorField.alamat"
                            placeholder="Jalan, kota, kode pos..." class="w-full resize-none" />
                        <small v-if="errorField.alamat" class="text-red-600">{{ errorField.alamat }}</small>
                    </div>

                    <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div>
                            <label>Nama Kontak / PIC</label>
                            <InputText v-model="form.kontak_nama" :invalid="!!errorField.kontak_nama" class="w-full" />
                            <small v-if="errorField.kontak_nama" class="text-red-600">{{ errorField.kontak_nama
                                }}</small>
                        </div>
                        <div>
                            <label>No. HP Kontak</label>
                            <InputText v-model="form.kontak_hp" :invalid="!!errorField.kontak_hp" class="w-full" />
                            <small v-if="errorField.kontak_hp" class="text-red-600">{{ errorField.kontak_hp }}</small>
                        </div>
                        <div>
                            <label>Email</label>
                            <InputText v-model="form.email" type="email" :invalid="!!errorField.email"
                                placeholder="info@vendor.com" class="w-full" />
                            <small v-if="errorField.email" class="text-red-600">{{ errorField.email }}</small>
                        </div>
                        <div>
                            <label>Termin Default (Hari)</label>
                            <InputNumber v-model="form.termin_hari_default" :min="0" :useGrouping="false"
                                :invalid="!!errorField.termin_hari_default" class="w-full" inputClass="w-full" />
                            <small class="text-slate-400">0 = tunai.</small>
                            <small v-if="errorField.termin_hari_default" class="text-red-600">
                                {{ errorField.termin_hari_default }}
                            </small>
                        </div>
                    </div>

                    <div>
                        <div class="flex items-center gap-3">
                            <ToggleSwitch v-model="form.aktif" inputId="suplier-aktif" />
                            <label for="suplier-aktif" class="mb-0!">{{ form.aktif ? 'Aktif' : 'Nonaktif' }}</label>
                        </div>
                        <small v-if="!form.aktif" class="text-amber-600">
                            Suplier nonaktif tidak bisa dipakai membuat PO baru. PO yang sudah ada tetap jalan.
                        </small>
                    </div>

                    <div class="flex justify-end items-center gap-4 mt-2 pt-6 border-t border-slate-100">
                        <button type="button" @click="emit('close')" :disabled="sedangProses"
                            class="px-6 py-3 font-bold text-slate-500 hover:text-slate-800 hover:bg-slate-100 rounded-xl transition-all disabled:opacity-50">
                            Batal
                        </button>
                        <button type="submit" :disabled="sedangProses || !form.kode || !form.nama"
                            class="px-8 py-3 rounded-xl font-bold bg-slate-900 text-white hover:bg-slate-800 transition-all shadow-md flex items-center gap-2 transform hover:-translate-y-0.5 disabled:opacity-50 disabled:cursor-not-allowed">
                            <i class="pi" :class="sedangProses ? 'pi-spin pi-spinner' : 'pi-save'"></i>
                            {{ sedangProses ? 'Menyimpan...' : 'Simpan Suplier' }}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import InputText from 'primevue/inputtext'
import InputMask from 'primevue/inputmask'
import InputNumber from 'primevue/inputnumber'
import Textarea from 'primevue/textarea'
import ToggleSwitch from 'primevue/toggleswitch'
import Tag from 'primevue/tag'

import { useSupplier } from '../composables/useSupplier'

const props = defineProps({
    suplier: { type: Object, default: null } // null = mode tambah
})
const emit = defineEmits(['close', 'saved'])

// pesanError/errorField di sini terpisah dari milik Supplier.vue — memang
// disengaja, lihat catatan di induk.
const { sedangProses, pesanError, errorField, simpanSuplier } = useSupplier()

const ubah = computed(() => !!props.suplier?.id)

// Disalin per field, bukan spread: `pkp` (read-only, turunan npwp) dan `id`
// tidak boleh ikut terkirim, dan baris di tabel induk tidak ikut termutasi.
// Induk merender dengan v-if, jadi komponen selalu mount ulang — tidak perlu
// watch props.
const form = ref({
    kode: props.suplier?.kode ?? '',
    nama: props.suplier?.nama ?? '',
    npwp: props.suplier?.npwp ?? '',
    alamat: props.suplier?.alamat ?? '',
    kontak_nama: props.suplier?.kontak_nama ?? '',
    kontak_hp: props.suplier?.kontak_hp ?? '',
    email: props.suplier?.email ?? '',
    termin_hari_default: props.suplier?.termin_hari_default ?? 0,
    aktif: props.suplier?.aktif ?? true
})

const adaNpwp = computed(() => /\d/.test(form.value.npwp || ''))
const pkpLabel = computed(() => (adaNpwp.value ? 'PKP' : 'Non-PKP'))

const payload = () => {
    const isi = { ...form.value }
    isi.nama = isi.nama.trim()
    // InputNumber mengosongkan jadi null; backend tidak menerima null.
    isi.termin_hari_default = isi.termin_hari_default ?? 0
    if (ubah.value) delete isi.kode // kunci bisnis, tidak boleh berubah
    else isi.kode = isi.kode.trim().toUpperCase()
    return isi
}

const simpan = async () => {
    const { success } = await simpanSuplier(payload(), props.suplier?.id ?? null)
    // Gagal: pesanError + errorField sudah diisi composable, form tetap terbuka.
    if (success) emit('saved')
}
</script>

<style scoped>
/* Label & pesan bantu form — dipakai berulang, ditaruh di sini supaya markup
   tidak dipenuhi kelas yang sama sepuluh kali. */
.form-suplier label {
    display: block;
    margin-bottom: .5rem;
    font-size: .875rem;
    font-weight: 700;
    color: #334155;
}

.form-suplier small {
    display: block;
    margin-top: .35rem;
    font-size: .75rem;
}

.animate-fade-in {
    animation: fadeIn 0.3s ease-out forwards;
}

.animate-fade-in-up {
    animation: fadeInUp 0.4s ease-out forwards;
}

@keyframes fadeIn {
    from {
        opacity: 0;
    }

    to {
        opacity: 1;
    }
}

@keyframes fadeInUp {
    from {
        opacity: 0;
        transform: translateY(20px) scale(0.95);
    }

    to {
        opacity: 1;
        transform: translateY(0) scale(1);
    }
}

.custom-scrollbar::-webkit-scrollbar {
    width: 6px;
}

.custom-scrollbar::-webkit-scrollbar-track {
    background: transparent;
}

.custom-scrollbar::-webkit-scrollbar-thumb {
    background-color: #cbd5e1;
    border-radius: 10px;
}

.custom-scrollbar::-webkit-scrollbar-thumb:hover {
    background-color: #94a3b8;
}
</style>
