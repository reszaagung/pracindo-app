<template>
    <div class="flex flex-col w-full relative">
        <!-- Header -->
        <div class="mb-3 flex justify-between items-center gap-2 border-b border-slate-100 pb-3">
            <span class="bg-slate-200 text-slate-700 text-[9px] font-bold px-2 py-0.5 rounded-full tracking-wide">
                DRAFT
            </span>

            <div class="flex items-center gap-1.5">
                <button type="button" @click="showModalProduct = true"
                    class="px-2.5 py-1.5 bg-blue-50 hover:bg-blue-100 text-blue-700 text-[10px] md:text-xs font-bold rounded-lg transition-colors flex items-center gap-1.5">
                    <i class="pi pi-box text-[10px]"></i> <span class="hidden sm:inline">Produk Baru</span><span class="sm:hidden">Produk</span>
                </button>

                <button type="button" @click="showModalSupplier = true"
                    class="px-2.5 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 text-[10px] md:text-xs font-bold rounded-lg transition-colors flex items-center gap-1.5">
                    <i class="pi pi-users text-[10px]"></i> <span class="hidden sm:inline">Suplier Baru</span><span class="sm:hidden">Suplier</span>
                </button>
            </div>
        </div>

        <!-- Toggle Jenis PO -->
        <div class="flex items-center gap-1 p-1 mb-4 bg-slate-50 border border-slate-200 rounded-lg w-full sm:w-max">
            <button type="button" @click="jenisPo = 'BAHAN_BAKU'"
                :class="['flex-1 sm:flex-none justify-center px-4 py-1.5 text-[10px] md:text-xs font-bold rounded-md transition-all duration-300 flex items-center gap-1.5',
                    jenisPo === 'BAHAN_BAKU'
                        ? 'bg-white text-emerald-700 shadow-sm border border-slate-200/60'
                        : 'text-slate-500 hover:text-slate-700 hover:bg-slate-200/50']">
                <i class="pi pi-box text-[10px]"></i> Bahan Baku
            </button>
            <button type="button" @click="jenisPo = 'KEMASAN'"
                :class="['flex-1 sm:flex-none justify-center px-4 py-1.5 text-[10px] md:text-xs font-bold rounded-md transition-all duration-300 flex items-center gap-1.5',
                    jenisPo === 'KEMASAN'
                        ? 'bg-white text-blue-700 shadow-sm border border-slate-200/60'
                        : 'text-slate-500 hover:text-slate-700 hover:bg-slate-200/50']">
                <i class="pi pi-shopping-bag text-[10px]"></i> Kemasan
            </button>
        </div>

        <div v-if="pesanError"
            class="mb-3 p-3 bg-red-50 border border-red-200 rounded-lg text-xs text-red-600 font-medium flex items-start gap-2">
            <i class="pi pi-exclamation-triangle mt-0.5 text-[10px]"></i>
            <span>{{ pesanError }}</span>
        </div>

        <form @submit.prevent="kirim" class="w-full">
            <!-- Entitas Pembeli -->
            <div class="flex flex-row items-center justify-between mb-4 border-b border-slate-100 pb-3 gap-2">
                <h3 class="text-xs font-bold text-slate-800">Entitas Pembeli</h3>
                <div class="flex flex-wrap items-center bg-slate-50 p-0.5 rounded-lg border border-slate-200/60">
                    <button v-for="ent in listEntitas" :key="ent.id" type="button" @click="draf.entitas_id = ent.id"
                        :class="['px-3 py-1 text-[10px] font-bold rounded-md transition-all duration-300 text-center',
                            draf.entitas_id === ent.id
                                ? 'bg-white text-slate-800 shadow-sm border border-slate-100'
                                : 'text-slate-400 hover:text-slate-600']">
                        {{ ent.kode }}
                    </button>
                </div>
            </div>

            <!-- Form Inputs -->
            <div class="grid grid-cols-1 md:grid-cols-3 gap-3 mb-4">
                <div class="flex flex-col gap-1">
                    <label class="text-[10px] md:text-xs font-bold text-slate-700">No. PO (Preview)</label>
                    <input :value="previewNomor" type="text" readonly
                        class="px-3 py-1.5 bg-slate-100 border border-slate-200 rounded-lg focus:outline-none text-xs text-slate-500 font-semibold cursor-not-allowed" />
                </div>
                <div class="flex flex-col gap-1">
                    <label class="text-[10px] md:text-xs font-bold text-slate-700">Tanggal PO</label>
                    <input v-model="draf.tanggal" type="date" required
                        class="px-3 py-1.5 bg-slate-50 border border-slate-200 rounded-lg focus:outline-none focus:ring-1 focus:ring-emerald-500 text-xs text-slate-800" />
                </div>
                <div class="flex flex-col gap-1">
                    <label class="text-[10px] md:text-xs font-bold text-slate-700">Pilih Supplier</label>
                    <Select 
                        v-model="draf.suplier_id" 
                        :options="listSupplier" 
                        optionLabel="nama" 
                        optionValue="id" 
                        filter 
                        placeholder="-- Pilih Supplier --"
                        class="w-full bg-slate-50 border border-slate-200 rounded-lg text-xs h-[34px] flex items-center"
                    >
                        <template #empty>
                            <div class="p-2 text-center text-slate-500 text-[10px]">Supplier tidak ditemukan.</div>
                        </template>
                    </Select>
                </div>
            </div>

            <!-- Bagian Item Pesanan (Responsive: Card untuk Mobile, Tabel untuk Desktop) -->
            <div class="w-full mb-6">
                <div class="flex justify-between items-center mb-2 pb-2 mt-1">
                    <h3 class="text-xs font-bold text-slate-800">
                        Item Pesanan <span class="text-slate-400 font-normal">({{ jenisPo === 'BAHAN_BAKU' ? 'Bahan' : 'Kemasan' }})</span>
                    </h3>
                    <button type="button" @click="tambahItem"
                        class="px-2.5 py-1.5 bg-emerald-50 hover:bg-emerald-100 text-emerald-600 text-[10px] font-bold rounded-lg transition-colors flex items-center gap-1.5">
                        <i class="pi pi-plus text-[10px]"></i> Tambah
                    </button>
                </div>

                <!-- 1. TAMPILAN MOBILE: Model Baris ke Bawah (Card Stack) -->
                <div class="block md:hidden space-y-3">
                    <div v-for="(item, index) in draf.items" :key="'m-' + index" 
                        class="p-3 bg-slate-50 border border-slate-200 rounded-xl relative flex flex-col gap-2.5">
                        
                        <!-- Tombol Hapus di pojok kanan atas card -->
                        <div class="flex justify-between items-center border-b border-slate-200/60 pb-2">
                            <span class="text-[10px] font-bold text-slate-400 uppercase">Item #{{ index + 1 }}</span>
                            <button type="button" @click="hapusItem(index)" :disabled="draf.items.length === 1"
                                class="text-red-500 hover:text-red-700 text-xs disabled:opacity-30 p-1">
                                <i class="pi pi-trash"></i> Hapus
                            </button>
                        </div>

                        <!-- Pilih Produk -->
                        <div class="flex flex-col gap-1">
                            <label class="text-[10px] font-bold text-slate-600">
                                {{ jenisPo === 'BAHAN_BAKU' ? 'Bahan Baku' : 'Kemasan' }}
                            </label>
                            <Dropdown v-model="item.produk" :options="produkBerdasarkanSuplier" optionLabel="label"
                                appendTo="body"
                                :placeholder="draf.suplier_id ? 'Pilih produk...' : 'Pilih supplier dulu'"
                                class="w-full text-xs" :disabled="!draf.suplier_id" filter :loading="loadingProduk"
                                :pt="{
                                    root: { class: 'w-full h-[36px] bg-white border border-slate-200 rounded-md flex items-center text-xs' },
                                    input: { class: 'text-xs p-2' }
                                }">
                            </Dropdown>
                        </div>

                        <!-- Qty & Harga berdampingan agar hemat tempat tapi tetap lapang -->
                        <div class="grid grid-cols-2 gap-2">
                            <div class="flex flex-col gap-1">
                                <label class="text-[10px] font-bold text-slate-600">
                                    {{ jenisPo === 'BAHAN_BAKU' ? 'Qty (Kg)' : 'Qty (Pcs)' }}
                                </label>
                                <input v-model.number="item.qty" type="number" min="0" step="0.01" required
                                    class="w-full h-[36px] px-2 bg-white border border-slate-200 rounded-md text-xs text-right text-slate-800 font-semibold"
                                    placeholder="0" />
                            </div>
                            <div class="flex flex-col gap-1">
                                <label class="text-[10px] font-bold text-slate-600">Harga Satuan</label>
                                <div class="relative h-[36px]">
                                    <span class="absolute left-2 top-1/2 -translate-y-1/2 text-slate-400 font-bold text-[10px]">Rp</span>
                                    <input v-model.number="item.harga_per_kg" type="number" min="0" step="1"
                                        class="w-full h-full pl-7 pr-2 bg-white border border-slate-200 rounded-md text-xs text-right text-slate-800 font-semibold"
                                        placeholder="0" />
                                </div>
                            </div>
                        </div>

                        <!-- Subtotal per item -->
                        <div class="flex justify-between items-center pt-2 border-t border-slate-200/60 mt-1">
                            <span class="text-[10px] font-semibold text-slate-500">Subtotal Item:</span>
                            <span class="font-bold text-emerald-700 text-xs">
                                Rp {{ (subtotal(item)).toLocaleString('id-ID') }}
                            </span>
                        </div>
                    </div>
                </div>

                <!-- 2. TAMPILAN DESKTOP: Model Tabel Rapi -->
                <div class="hidden md:block overflow-x-auto pb-2 custom-scrollbar">
                    <table class="w-full text-left text-xs min-w-[700px]">
                        <thead class="text-slate-500 bg-slate-50 border-b border-slate-200">
                            <tr>
                                <th class="py-2 px-2 font-semibold rounded-tl-lg w-[40%] text-[10px] uppercase">
                                    {{ jenisPo === 'BAHAN_BAKU' ? 'Bahan Baku' : 'Kemasan' }}
                                </th>
                                <th class="py-2 px-2 font-semibold w-[15%] text-right text-[10px] uppercase">
                                    {{ jenisPo === 'BAHAN_BAKU' ? 'Qty (Kg)' : 'Qty (Pcs)' }}
                                </th>
                                <th class="py-2 px-2 font-semibold w-[20%] text-right text-[10px] uppercase">Harga</th>
                                <th class="py-2 px-2 font-semibold w-[20%] text-right text-[10px] uppercase">Subtotal</th>
                                <th class="py-2 px-2 font-semibold text-center rounded-tr-lg w-[5%] text-[10px] uppercase">Aksi</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr v-for="(item, index) in draf.items" :key="'d-' + index"
                                class="bg-white border-b border-slate-100 hover:bg-slate-50/50 transition-colors">

                                <td class="py-1.5 px-2 align-top">
                                    <Dropdown v-model="item.produk" :options="produkBerdasarkanSuplier" optionLabel="label"
                                        appendTo="body"
                                        :placeholder="draf.suplier_id ? 'Pilih produk...' : 'Pilih supplier'"
                                        class="w-full text-xs" :disabled="!draf.suplier_id" filter :loading="loadingProduk"
                                        :pt="{
                                            root: { class: 'w-full h-[34px] bg-slate-50 border border-slate-200 rounded-md flex items-center text-xs' },
                                            input: { class: 'text-xs p-2' }
                                        }">
                                    </Dropdown>
                                </td>

                                <td class="py-1.5 px-2 align-top">
                                    <input v-model.number="item.qty" type="number" min="0" step="0.01" required
                                        class="w-full h-[34px] px-2 bg-slate-50 border border-slate-200 rounded-md text-xs text-right focus:ring-1 focus:ring-emerald-500 text-slate-800"
                                        placeholder="0" />
                                </td>

                                <td class="py-1.5 px-2 align-top">
                                    <div class="relative h-[34px]">
                                        <span class="absolute left-2 top-1/2 -translate-y-1/2 text-slate-400 font-bold text-[10px]">Rp</span>
                                        <input v-model.number="item.harga_per_kg" type="number" min="0" step="1"
                                            class="w-full h-full pl-7 pr-2 bg-slate-50 border border-slate-200 rounded-md text-xs text-right focus:ring-1 focus:ring-emerald-500 text-slate-800"
                                            placeholder="0" />
                                    </div>
                                </td>

                                <td class="py-1.5 px-2 text-right align-top pt-3">
                                    <span class="font-bold text-slate-800 text-xs">
                                        Rp {{ (subtotal(item)).toLocaleString('id-ID') }}
                                    </span>
                                </td>

                                <td class="py-1.5 px-2 text-center align-top pt-2">
                                    <button type="button" @click="hapusItem(index)" :disabled="draf.items.length === 1"
                                        class="w-7 h-7 rounded-md text-slate-400 hover:text-red-500 hover:bg-red-50 disabled:opacity-30 disabled:hover:bg-transparent transition-colors flex items-center justify-center mx-auto"
                                        title="Hapus">
                                        <i class="pi pi-times text-[10px]"></i>
                                    </button>
                                </td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>

            <!-- Footer / Total Kalkulasi -->
            <div class="flex flex-col md:flex-row justify-between items-start bg-slate-50 p-3 md:p-4 rounded-xl border border-slate-100">
                <div class="flex flex-col gap-2 w-full md:w-auto mb-4 md:mb-0">
                    <div class="flex items-center gap-2">
                        <input type="checkbox" id="pakaiPpn" :true-value="11" :false-value="0" v-model="draf.ppn_persen"
                            class="w-3.5 h-3.5 rounded border-slate-300 text-emerald-600 focus:ring-emerald-600 cursor-pointer">
                        <label for="pakaiPpn" class="text-[10px] md:text-xs font-bold text-slate-700 cursor-pointer select-none">
                            Kenakan PPN 11%
                        </label>
                    </div>
                </div>

                <div class="flex flex-col w-full md:w-56 gap-1.5 border-t md:border-none border-slate-200 pt-3 md:pt-0">
                    <div class="flex justify-between items-center text-[10px] md:text-xs">
                        <span class="font-semibold text-slate-500">Subtotal</span>
                        <span class="font-bold text-slate-700">Rp {{ (subtotalSemua).toLocaleString('id-ID') }}</span>
                    </div>

                    <div v-if="draf.ppn_persen > 0" class="flex justify-between items-center text-[10px] md:text-xs">
                        <span class="font-semibold text-emerald-600">PPN (11%)</span>
                        <span class="font-bold text-emerald-700">Rp {{ (ppnNominal).toLocaleString('id-ID') }}</span>
                    </div>

                    <div class="flex justify-between items-end mt-1 pt-1.5 border-t border-slate-200">
                        <span class="text-[9px] md:text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-0.5">Grand Total</span>
                        <span class="text-lg md:text-xl font-black text-slate-800">Rp {{ (grandTotal).toLocaleString('id-ID') }}</span>
                    </div>

                    <div class="flex gap-2 mt-3 w-full">
                        <button type="button" @click="$emit('close')"
                            class="flex-1 py-2 bg-white border border-slate-200 text-slate-600 hover:bg-slate-50 font-bold rounded-lg text-xs transition-all">
                            Batal
                        </button>
                        <button type="submit" :disabled="sedangProses || periodeDitutup"
                            class="flex-1 py-2 bg-emerald-600 hover:bg-emerald-700 disabled:bg-slate-400 text-white font-bold rounded-lg text-xs shadow-sm transition-all flex justify-center items-center gap-1.5 cursor-pointer disabled:cursor-not-allowed">
                            <i class="pi text-[10px]" :class="sedangProses ? 'pi-spin pi-spinner' : 'pi-check-circle'"></i>
                            Simpan
                        </button>
                    </div>
                </div>
            </div>
        </form>

        <!-- Modal Tambah Suplier -->
        <SupplierForm v-if="showModalSupplier" @close="showModalSupplier = false" @saved="handleSupplierSaved" />

        <!-- Modal Tambah Produk -->
        <ProductEntry v-if="showModalProduct" @close="showModalProduct = false" @saved="handleProductSaved" />
    </div>
</template>

<script setup>
import { reactive, computed, ref, watch, onMounted } from 'vue'
import Dropdown from 'primevue/dropdown'
import Select from 'primevue/select'
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
        // Menggunakan endpoint yang benar: 'master/produk/'
        const response = await api.get('master/produk/', {
            params: {
                suplier: idSuplier,
                jenis: jenisPo.value,
                aktif: true,
                ringkas: 1
            }
        })
        const hasil = response.data?.results || response.data || []
        
        produkBerdasarkanSuplier.value = hasil.map(p => ({ ...p, label: `${p.kode} - ${p.nama}` }))
    } catch (err) {
        console.error("Gagal menarik produk:", err)
    } finally {
        loadingProduk.value = false
    }
}

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
        kategori_po: jenisPo.value,
        items: draf.items.map(i => {
            const idSatuan = i.produk.satuan?.id || i.produk.satuan_id || i.produk.satuan;
            return {
                produk_id: i.produk.id,
                qty_pesan: Number(i.qty) || 0,
                harga_per_kg: Number(i.harga_per_kg) || 0,
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