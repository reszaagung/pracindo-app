<!--
  src/features/master/views/Supplier.vue
  =====================================
  Tampilan data Master Suplier: tabel + kartu mobile + cari + paginasi.
  Form input tambah/ubah ada di komponen anak SupplierForm.vue.
-->
<template>
    <div class="p-6 max-w-7xl mx-auto w-full">
        <div class="flex flex-col md:flex-row justify-between items-start md:items-center mb-8 gap-4">
            <div>
                <h1 class="text-2xl font-bold text-slate-800">Master Suplier</h1>
                <p class="text-slate-500 text-sm mt-1">Kelola data pemasok dan vendor perusahaan</p>
            </div>

            <div class="flex gap-3 w-full md:w-auto">
                <span class="p-input-icon-left w-full md:w-auto">
                    <i class="pi pi-search" />
                    <InputText v-model="kataKunci" placeholder="Cari nama / kode..." @keyup.enter="cariData"
                        class="w-full md:w-64 rounded-lg!" />
                </span>

                <!-- Tombol aksi utama: Biru Muda. Hanya muncul untuk role tertentu -->
                <Button v-if="bisaEdit" label="Tambah Suplier" icon="pi pi-plus" @click="bukaTambah"
                    class="bg-sky-500! hover:bg-sky-600! border-none! text-white! rounded-lg! whitespace-nowrap" />
            </div>
        </div>

        <!-- Banner ini hanya untuk error daftar/status. Error simpan tampil di
             dalam SupplierForm, tidak bocor ke sini. -->
        <div v-if="pesanError"
            class="mb-4 p-4 bg-red-50 text-red-600 rounded-lg border border-red-200 whitespace-pre-line">
            {{ pesanError }}
        </div>

        <!-- Tampilan Desktop (Tabel) -->
        <div class="hidden md:block bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
            <DataTable :value="daftarSuplier" :loading="sedangProses" responsiveLayout="scroll" class="p-datatable-sm">
                <Column field="kode" header="Kode" class="font-medium text-slate-700"></Column>
                <Column field="nama" header="Nama Perusahaan"></Column>
                <Column field="kontak_nama" header="Kontak"></Column>
                <Column field="termin_hari_default" header="Termin (Hari)"></Column>
                <Column header="Status">
                    <template #body="{ data }">
                        <span :class="data.aktif ? 'bg-green-100 text-green-700' : 'bg-slate-100 text-slate-500'"
                            class="px-2.5 py-1 rounded-full text-xs font-semibold">
                            {{ data.aktif ? 'Aktif' : 'Nonaktif' }}
                        </span>
                    </template>
                </Column>
                <Column v-if="bisaEdit" header="Aksi" :exportable="false" style="min-width:8rem">
                    <template #body="{ data }">
                        <Button icon="pi pi-pencil" title="Ubah data suplier" @click="bukaUbah(data)"
                            class="p-button-rounded p-button-text text-sky-500! hover:bg-sky-50!" />
                        <Button :icon="data.aktif ? 'pi pi-ban' : 'pi pi-check-circle'"
                            :title="data.aktif ? 'Nonaktifkan suplier' : 'Aktifkan kembali suplier'"
                            @click="gantiStatus(data)"
                            :class="data.aktif ? 'text-amber-500! hover:bg-amber-50!' : 'text-green-600! hover:bg-green-50!'"
                            class="p-button-rounded p-button-text" />
                    </template>
                </Column>
                <template #empty>
                    <p class="text-center p-6 text-slate-400">Data tidak ditemukan</p>
                </template>
            </DataTable>
        </div>

        <!-- Tampilan Mobile (Card) -->
        <div class="md:hidden flex flex-col gap-4">
            <div v-for="item in daftarSuplier" :key="item.id"
                class="bg-white p-4 rounded-xl shadow-sm border border-slate-200 relative">
                <div class="flex justify-between items-start mb-2">
                    <div>
                        <span class="text-xs font-bold text-sky-600 mb-1 block">{{ item.kode }}</span>
                        <h3 class="font-bold text-slate-800">{{ item.nama }}</h3>
                    </div>
                    <div v-if="bisaEdit" class="flex">
                        <Button icon="pi pi-pencil" title="Ubah data suplier" @click="bukaUbah(item)"
                            class="p-button-rounded p-button-text text-sky-500! h-8! w-8!" />
                        <Button :icon="item.aktif ? 'pi pi-ban' : 'pi pi-check-circle'"
                            :title="item.aktif ? 'Nonaktifkan suplier' : 'Aktifkan kembali suplier'"
                            @click="gantiStatus(item)" :class="item.aktif ? 'text-amber-500!' : 'text-green-600!'"
                            class="p-button-rounded p-button-text h-8! w-8!" />
                    </div>
                </div>
                <div class="text-sm text-slate-600 space-y-1 mt-3">
                    <p><i class="pi pi-user text-xs mr-2"></i>{{ item.kontak_nama || '-' }}</p>
                    <p><i class="pi pi-clock text-xs mr-2"></i>Termin: {{ item.termin_hari_default }} Hari</p>
                    <p v-if="!item.aktif" class="text-xs font-semibold text-slate-400">Nonaktif</p>
                </div>
            </div>
            <div v-if="!sedangProses && daftarSuplier.length === 0" class="text-center p-8 text-slate-400">
                Data tidak ditemukan
            </div>
        </div>

        <!-- Satu paginasi untuk desktop dan mobile -->
        <Paginator v-if="totalData > perHalaman" :rows="perHalaman" :totalRecords="totalData"
            :first="(halaman - 1) * perHalaman" @page="(e) => muat(e.page + 1)" class="mt-4 bg-transparent!" />

        <SupplierForm v-if="formTampil" :suplier="suplierTerpilih" @close="formTampil = false"
            @saved="setelahSimpan" />
    </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import InputText from 'primevue/inputtext'
import Button from 'primevue/button'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Paginator from 'primevue/paginator'

// Pastikan useSupplier.js juga dipindah ke direktori master/composables/
import { useSupplier } from '../composables/useSupplier'
import SupplierForm from './SupplierForm.vue'
import { useAuth } from '@/composables/useAuth'
import { useToast } from '@/composables/useToast'

const { kartu } = useAuth()
const toast = useToast()

// useSupplier() BUKAN singleton — SupplierForm memanggilnya sendiri dan punya
// pesanError/errorField terpisah. Itu memang yang diinginkan: error validasi
// form tidak bocor ke banner halaman ini. Konsekuensinya `daftarSuplier` di
// form tidak ikut ter-refresh, jadi refresh tabel HARUS lewat event `saved`
// (setelahSimpan di bawah). Jangan dijadikan shared state.
const {
    daftarSuplier, sedangProses, pesanError,
    totalData, halaman, perHalaman,
    ambilSuplier, ubahStatusAktif
} = useSupplier()

const kataKunci = ref('')

// Sumber role disamakan dengan DashboardView.vue, yang membaca `kartu`
// (computed turunan profil di useAuth) — bukan `profil` langsung.
// Halaman tetap terbuka untuk semua role; ini cuma menyembunyikan tombol tulis.
const bisaEdit = computed(() => ['ADMIN', 'SUPERVISOR'].includes(kartu.value?.role))

const muat = (ke = 1) => ambilSuplier({ search: kataKunci.value, halaman: ke })
const cariData = () => muat(1)

// ---------- Form (komponen anak) ----------

const formTampil = ref(false)
const suplierTerpilih = ref(null) // null = tambah

const bukaTambah = () => {
    suplierTerpilih.value = null
    formTampil.value = true
}

const bukaUbah = (baris) => {
    suplierTerpilih.value = baris
    formTampil.value = true
}

const setelahSimpan = () => {
    const ubah = !!suplierTerpilih.value
    formTampil.value = false
    toast.success(ubah ? 'Data suplier diperbarui.' : 'Suplier baru ditambahkan.')
    muat(halaman.value) // tetap di halaman yang sedang dilihat
}

// ---------- Nonaktif/aktif ----------

const gantiStatus = async (baris) => {
    if (
        baris.aktif &&
        !confirm(
            `Nonaktifkan suplier ${baris.kode} — ${baris.nama}?\n\n` +
            'Suplier nonaktif tidak bisa dipakai membuat PO baru (ditolak backend). ' +
            'PO yang sudah ada tetap jalan.'
        )
    ) return

    const { success } = await ubahStatusAktif(baris.id, !baris.aktif)
    if (!success) return toast.error(pesanError.value)
    toast.success(baris.aktif ? 'Suplier dinonaktifkan.' : 'Suplier diaktifkan kembali.')
    muat(halaman.value)
}

onMounted(() => muat())
</script>
