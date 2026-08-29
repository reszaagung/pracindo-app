<template>
    <div class="flex flex-col w-full relative">
        <!-- Header -->
        <div class="mb-4 flex justify-between items-center gap-4 border-b border-slate-100 pb-4">
            <span class="bg-slate-200 text-slate-700 text-[10px] font-bold px-2.5 py-1 rounded-full tracking-wide">
                DRAFT
            </span>

            <div class="flex items-center gap-2">
                <button type="button" @click="showModalProduct = true"
                    class="px-3 py-2 bg-blue-50 hover:bg-blue-100 text-blue-700 text-xs font-bold rounded-lg transition-colors flex items-center gap-2">
                    <i class="pi pi-box"></i> Produk Baru
                </button>

                <button type="button" @click="showModalSupplier = true"
                    class="px-3 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-bold rounded-lg transition-colors flex items-center gap-2">
                    <i class="pi pi-users"></i> Suplier Baru
                </button>
            </div>
        </div>

        <!-- Toggle Jenis PO (Bahan Baku / Kemasan) -->
        <div class="flex items-center gap-2 p-1 mb-6 bg-slate-50 border border-slate-200 rounded-xl w-max">
            <button type="button" @click="jenisPo = 'BAHAN_BAKU'"
                :class="['px-6 py-2.5 text-xs font-bold rounded-lg transition-all duration-300 flex items-center gap-2',
                    jenisPo === 'BAHAN_BAKU'
                        ? 'bg-white text-emerald-700 shadow-sm border border-slate-200/60'
                        : 'text-slate-500 hover:text-slate-700 hover:bg-slate-200/50']">
                <i class="pi pi-box"></i> Bahan Baku
            </button>
            <button type="button" @click="jenisPo = 'KEMASAN'"
                :class="['px-6 py-2.5 text-xs font-bold rounded-lg transition-all duration-300 flex items-center gap-2',
                    jenisPo === 'KEMASAN'
                        ? 'bg-white text-blue-700 shadow-sm border border-slate-200/60'
                        : 'text-slate-500 hover:text-slate-700 hover:bg-slate-200/50']">
                <i class="pi pi-shopping-bag"></i> Kemasan
            </button>
        </div>

        <div v-if="pesanError"
            class="mb-4 p-4 bg-red-50 border border-red-200 rounded-xl text-sm text-red-600 font-medium flex items-start gap-3">
            <i class="pi pi-exclamation-triangle mt-0.5"></i>
            <span>{{ pesanError }}</span>
        </div>

        <form @submit.prevent="kirim" class="w-full">
            <div class="flex flex-col md:flex-row md:items-center justify-between mb-6 border-b border-slate-100 pb-4 gap-4">
                <h3 class="text-sm font-bold text-slate-800">Entitas Pembeli</h3>
                <div class="flex flex-wrap items-center bg-slate-50 p-1 rounded-xl border border-slate-200/60">
                    <button v-for="ent in listEntitas" :key="ent.id" type="button" @click="draf.entitas_id = ent.id"
                        :class="['px-4 md:px-6 py-2 text-[10px] md:text-xs font-bold rounded-lg transition-all duration-300 flex-1 md:flex-none text-center',
                            draf.entitas_id === ent.id
                                ? 'bg-white text-slate-800 shadow-[0_2px_10px_rgba(0,0,0,0.05)] border border-slate-100/50'
                                : 'text-slate-400 hover:text-slate-600 hover:bg-slate-100/50']">
                        {{ ent.kode }}
                    </button>
                </div>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-3 gap-4 md:gap-6 mb-4">
                <div class="flex flex-col gap-2">
                    <label class="text-xs md:text-sm font-bold text-slate-700">No. PO (Preview)</label>
                    <input :value="previewNomor" type="text" readonly
                        class="px-4 py-2.5 bg-slate-100 border border-slate-200 rounded-xl focus:outline-none text-sm text-slate-500 font-semibold cursor-not-allowed" />
                </div>
                <div class="flex flex-col gap-2">
                    <label class="text-xs md:text-sm font-bold text-slate-700">Tanggal PO</label>
                    <input v-model="draf.tanggal" type="date" required
                        class="px-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-emerald-500 text-sm text-slate-800" />
                </div>
                <div class="flex flex-col gap-2">
                    <Select 
                        v-model="draf.suplier_id" 
                        :options="listSupplier" 
                        optionLabel="nama" 
                        optionValue="id" 
                        filter 
                        placeholder="-- Pilih Supplier --"
                        class="w-full bg-slate-50 border border-slate-200 rounded-xl text-sm"
                    >
                        <!-- Template kustom jika tidak ada data -->
                        <template #empty>
                            <div class="p-3 text-center text-slate-500 text-xs">
                                Supplier tidak ditemukan.
                            </div>
                        </template>
                    </Select>
                </div>
            </div>

            <!-- Tabel Detail Item Pesanan (Dinamis berdasarkan jenisPo) -->
            <div class="w-full mb-8">
                <div class="flex justify-between items-center mb-4 pb-2 mt-2">
                    <h3 class="text-sm font-bold text-slate-800">
                        Detail Item Pesanan
                        <span class="text-slate-400 ml-2 font-normal">({{ jenisPo === 'BAHAN_BAKU' ? 'Bahan Baku' : 'Kemasan' }})</span>
                    </h3>
                    <button type="button" @click="tambahItem"
                        class="px-3 py-2 bg-emerald-50 hover:bg-emerald-100 text-emerald-600 text-xs font-bold rounded-lg transition-colors flex items-center gap-2">
                        <i class="pi pi-plus"></i> Tambah Item
                    </button>
                </div>

                <div class="overflow-x-auto">
                    <table class="w-full text-left text-sm min-w-[800px]">
                        <thead class="text-slate-500 bg-slate-50 border-b border-slate-200">
                            <tr>
                                <th class="py-3 px-4 font-semibold rounded-tl-xl w-[40%]">
                                    {{ jenisPo === 'BAHAN_BAKU' ? 'Produk (Bahan Baku)' : 'Produk (Kemasan)' }}
                                </th>
                                <th class="py-3 px-4 font-semibold w-[15%] text-right">
                                    {{ jenisPo === 'BAHAN_BAKU' ? 'Qty (Kg)' : 'Qty (Unit/Pcs)' }}
                                </th>
                                <th class="py-3 px-4 font-semibold w-[20%] text-right">
                                    {{ jenisPo === 'BAHAN_BAKU' ? 'Harga per Kg' : 'Harga per Unit' }}
                                </th>
                                <th class="py-3 px-4 font-semibold w-[20%] text-right">Subtotal</th>
                                <th class="py-3 px-4 font-semibold text-center rounded-tr-xl w-[5%]">Aksi</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr v-for="(item, index) in draf.items" :key="index"
                                class="bg-white border-b border-slate-100 hover:bg-slate-50/50 transition-colors">

                                <td class="py-3 px-4 align-top">
                                    <Dropdown v-model="item.produk" :options="produkBerdasarkanSuplier" optionLabel="label"
                                        appendTo="body"
                                        :placeholder="draf.suplier_id ? 'Pilih atau cari produk...' : 'Pilih supplier dulu'"
                                        class="w-full" :disabled="!draf.suplier_id" filter :loading="loadingProduk"
                                        :pt="{
                                            root: { class: 'w-full h-[42px] bg-slate-50 border border-slate-200 rounded-lg flex items-center' }
                                        }">
                                    </Dropdown>
                                </td>

                                <td class="py-3 px-4 align-top">
                                    <input v-model.number="item.qty" type="number" min="0" step="0.01" required
                                        class="w-full h-[42px] px-3 bg-slate-50 border border-slate-200 rounded-lg text-sm text-right focus:ring-2 focus:ring-emerald-500 text-slate-800"
                                        placeholder="0" />
                                </td>

                                <td class="py-3 px-4 align-top">
                                    <div class="relative h-[42px]">
                                        <span class="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 font-bold text-sm">Rp</span>
                                        <input v-model.number="item.harga_per_kg" type="number" min="0" step="1"
                                            class="w-full h-full pl-9 pr-3 bg-slate-50 border border-slate-200 rounded-lg text-sm text-right focus:ring-2 focus:ring-emerald-500 text-slate-800"
                                            placeholder="0" />
                                    </div>
                                </td>

                                <td class="py-3 px-4 text-right align-top pt-5">
                                    <span class="font-black text-slate-800">
                                        Rp {{ (subtotal(item)).toLocaleString('id-ID') }}
                                    </span>
                                </td>

                                <td class="py-3 px-4 text-center align-top pt-4">
                                    <button type="button" @click="hapusItem(index)" :disabled="draf.items.length === 1"
                                        class="w-8 h-8 rounded-lg text-slate-400 hover:text-red-500 hover:bg-red-50 disabled:opacity-30 disabled:hover:bg-transparent transition-colors flex items-center justify-center mx-auto"
                                        title="Hapus Baris">
                                        <i class="pi pi-times"></i>
                                    </button>
                                </td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>

            <!-- Footer / Total Kalkulasi -->
            <div class="flex flex-col md:flex-row justify-between items-start bg-slate-50 p-4 md:p-6 rounded-2xl border border-slate-100">
                <div class="flex flex-col gap-2 w-full md:w-auto mb-6 md:mb-0">
                    <div class="flex items-center gap-2">
                        <input type="checkbox" id="pakaiPpn" :true-value="11" :false-value="0" v-model="draf.ppn_persen"
                            class="w-4 h-4 rounded border-slate-300 text-emerald-600 focus:ring-emerald-600 cursor-pointer">
                        <label for="pakaiPpn" class="text-sm font-bold text-slate-700 cursor-pointer select-none">
                            Kenakan PPN 11% (Suplier PKP)
                        </label>
                    </div>
                </div>

                <div class="flex flex-col w-full md:w-64 gap-2 border-t md:border-none border-slate-200 pt-4 md:pt-0">
                    <div class="flex justify-between items-center text-sm">
                        <span class="font-semibold text-slate-500">Subtotal</span>
                        <span class="font-bold text-slate-700">Rp {{ (subtotalSemua).toLocaleString('id-ID') }}</span>
                    </div>

                    <div v-if="draf.ppn_persen > 0" class="flex justify-between items-center text-sm">
                        <span class="font-semibold text-emerald-600">PPN (11%)</span>
                        <span class="font-bold text-emerald-700">Rp {{ (ppnNominal).toLocaleString('id-ID') }}</span>
                    </div>

                    <div class="flex justify-between items-end mt-2 pt-2 border-t border-slate-200">
                        <span class="text-xs font-bold text-slate-400 uppercase tracking-wider mb-1">Grand Total</span>
                        <span class="text-2xl font-black text-slate-800">Rp {{ (grandTotal).toLocaleString('id-ID') }}</span>
                    </div>

                    <div class="flex gap-2 mt-4 w-full">
                        <button type="button" @click="$emit('close')"
                            class="flex-1 py-3.5 bg-white border border-slate-200 text-slate-600 hover:bg-slate-50 font-bold rounded-xl transition-all">
                            Batal
                        </button>
                        <button type="submit" :disabled="sedangProses || periodeDitutup"
                            class="flex-1 py-3.5 bg-emerald-600 hover:bg-emerald-700 disabled:bg-slate-400 text-white font-bold rounded-xl shadow-[0_4px_15px_rgba(16,185,129,0.3)] transition-all flex justify-center items-center gap-2 cursor-pointer disabled:cursor-not-allowed">
                            <i class="pi" :class="sedangProses ? 'pi-spin pi-spinner' : 'pi-check-circle'"></i>
                            Simpan
                        </button>
                    </div>
                </div>
            </div>
        </form>

        <SupplierForm v-if="showModalSupplier" @close="showModalSupplier = false" @saved="handleSupplierSaved" />
        <ProductEntry v-if="showModalProduct" @close="showModalProduct = false" @saved="handleProductSaved" />
    </div>
</template>

<script setup>
import { reactive, computed, ref, watch, onMounted } from 'vue'
import Dropdown from 'primevue/dropdown'
import Select from 'primevue/select'
import { CACHE_KEY, denganCache } from '@/utils/cacheService'
import SupplierForm from '@/features/master/views/SupplierForm.vue'
import ProductEntry from '@/features/master/views/ProductEntry.vue'
import { usePurchaseOrder } from '@/features/accounting/composables/usePurchaseOrder'
import api from '@/utils/api'

const emit = defineEmits(['close', 'saved'])

const {
    listEntitas, listSupplier, sedangProses, pesanError, previewNomor,
    periodeDitutup, muatDataMaster, muatPreviewNomor, simpanPO, cekStatusPeriode
} = usePurchaseOrder()

const showModalSupplier = ref(false)
const showModalProduct = ref(false)
const produkBerdasarkanSuplier = ref([])
const loadingProduk = ref(false)
const jenisPo = ref('BAHAN_BAKU')

const hariIni = () => {
    const t = new Date(Date.now() - new Date().getTimezoneOffset() * 60_000)
    return t.toISOString().slice(0, 10)
}

const itemKosong = () => ({ produk: null, qty: null, harga_per_kg: null })

const draf = reactive({
    entitas_id: '',
    suplier_id: '',
    tanggal: hariIni(),
    tanggal_kirim_diminta: '',
    catatan: '',
    ppn_persen: 0,
    items: [itemKosong()],
})

onMounted(async () => {
    await muatDataMaster()
    previewNomor.value = 'Pilih entitas & tanggal'

    if (listEntitas.value.length > 0) {
        draf.entitas_id = listEntitas.value[0].id
    }
})

const handleSupplierSaved = async () => {
    showModalSupplier.value = false
    await muatDataMaster()
}

const handleProductSaved = async (produkBaru) => {
    showModalProduct.value = false
    if (draf.suplier_id) {
        await tarikProdukDariAPI(draf.suplier_id)

        const produkTerpilih = produkBerdasarkanSuplier.value.find(p => p.id === produkBaru.id)
        if (produkTerpilih) {
            const barisTerakhir = draf.items[draf.items.length - 1]
            if (!barisTerakhir.produk) {
                barisTerakhir.produk = produkTerpilih
            }
        }
    }
}

watch([() => draf.entitas_id, () => draf.tanggal], async ([entitas, tanggal]) => {
    if (entitas && tanggal) {
        await Promise.all([
            muatPreviewNomor(entitas, tanggal),
            cekStatusPeriode(entitas, tanggal)
        ])
    } else {
        previewNomor.value = 'Pilih entitas & tanggal'
        periodeDitutup.value = false
    }
})

const tarikProdukDariAPI = async (idSuplier) => {
    if (!idSuplier) {
        produkBerdasarkanSuplier.value = []
        return
    }

    loadingProduk.value = true
    try {
        const response = await api.get('master/produk/', {
            params: {
                suplier: idSuplier,
                jenis: jenisPo.value, // Menggunakan jenis yang dipilih dari state toggle
                aktif: true,
                ringkas: 1
            }
        })
        const hasil = response.data.results || response.data || []
        produkBerdasarkanSuplier.value = hasil.map(p => ({ ...p, label: `${p.kode} - ${p.nama}` }))
    } catch (err) {
        console.error("Gagal menarik produk berdasarkan suplier:", err)
    } finally {
        loadingProduk.value = false
    }
}

// Reset baris item & tarik ulang produk setiap jenis PO diubah
watch(() => jenisPo.value, async () => {
    draf.items = [itemKosong()]
    if (draf.suplier_id) {
        await tarikProdukDariAPI(draf.suplier_id)
    }
})

watch(() => draf.suplier_id, async (newVal, oldVal) => {
    if (oldVal && newVal !== oldVal) {
        draf.items = [itemKosong()]
    }
    await tarikProdukDariAPI(newVal)
}, { immediate: true })

const subtotal = (item) => (Number(item.qty) || 0) * (Number(item.harga_per_kg) || 0)
const subtotalSemua = computed(() => draf.items.reduce((s, i) => s + subtotal(i), 0))
const ppnNominal = computed(() => subtotalSemua.value * (draf.ppn_persen / 100))
const grandTotal = computed(() => subtotalSemua.value + ppnNominal.value)

const tambahItem = () => draf.items.push(itemKosong())
const hapusItem = (i) => {
    if (draf.items.length > 1) draf.items.splice(i, 1)
}

const kirim = async () => {
    if (periodeDitutup.value) return

    pesanError.value = ''
    const kosong = draf.items.some(i => !i.produk?.id || !(Number(i.qty) > 0))
    if (kosong) {
        alert('❌ Gagal: Setiap item butuh produk dan Qty minimal 1.')
        pesanError.value = 'Setiap item butuh produk (yang valid) dan Qty minimal 1.'
        return
    }

    const payload = {
        entitas_id: draf.entitas_id,
        suplier_id: draf.suplier_id,
        tanggal: draf.tanggal,
        tanggal_kirim_diminta: draf.tanggal_kirim_diminta || null,
        catatan: draf.catatan,
        pakai_ppn: draf.ppn_persen > 0,
        ppn_persen: draf.ppn_persen || 0,
        kategori_po: jenisPo.value, // Sisipkan jenis PO (Bahan/Kemasan) agar tercatat ke Backend
        items: draf.items.map(i => {
            const idSatuan = i.produk.satuan?.id || i.produk.satuan_id || i.produk.satuan;
            return {
                produk_id: i.produk.id,
                qty_pesan: Number(i.qty) || 0,
                harga_per_kg: Number(i.harga_per_kg) || 0, // Backend logic tetap menerima field harga_per_kg, abaikan penamaannya
                satuan: idSatuan
            }
        }),
    }

    const hasil = await simpanPO(payload, true)

    if (hasil.success) {
        alert("✅ Berhasil! Purchase Order baru telah tersimpan.")
        emit('saved', hasil.data)
    } else {
        alert("❌ Gagal menyimpan PO:\n" + hasil.message)
        pesanError.value = hasil.message
    }
}
</script>
