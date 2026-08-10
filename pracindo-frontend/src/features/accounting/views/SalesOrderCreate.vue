<template>
    <div class="flex flex-col w-full animate-fade-in relative">
        <!-- Header -->
        <div class="mb-4 md:mb-6 flex flex-col md:flex-row justify-between items-start md:items-end gap-4 md:gap-0">
            <div>
                <p class="text-xs text-slate-400 mb-1">
                    <router-link to="/" class="hover:text-slate-700 transition-colors">Dashboard</router-link> ›
                    <router-link to="/accounting/input/so" class="hover:text-slate-700 transition-colors">Input
                        Entry</router-link> › Buat SO
                </p>
                <div class="flex items-center gap-3">
                    <h2 class="text-xl md:text-2xl font-bold text-slate-800 tracking-tight">Create Sales Order (SO)</h2>
                    <span
                        class="bg-blue-100 text-blue-700 text-[10px] font-bold px-2.5 py-1 rounded-full tracking-wide">PENJUALAN</span>
                </div>
            </div>

            <!-- Tombol Aksi Kanan Atas -->
            <div class="flex flex-wrap items-center gap-2">
                <button type="button" @click="showModalProduct = true"
                    class="px-3 py-2 md:px-4 md:py-2 bg-blue-50 hover:bg-blue-100 text-blue-700 text-[10px] md:text-xs font-bold rounded-lg transition-colors flex items-center gap-2">
                    <i class="pi pi-box"></i> Produk Baru
                </button>

                <button type="button" @click="showModalCustomer = true"
                    class="px-3 py-2 md:px-4 md:py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 text-[10px] md:text-xs font-bold rounded-lg transition-colors flex items-center gap-2">
                    <i class="pi pi-user-plus"></i> Pelanggan Baru
                </button>
            </div>
        </div>

        <!-- Notifikasi Error -->
        <div v-if="pesanError"
            class="mb-4 p-4 bg-red-50 border border-red-200 rounded-xl text-sm text-red-600 font-medium flex items-start gap-3">
            <i class="pi pi-exclamation-triangle mt-0.5"></i>
            <span>{{ pesanError }}</span>
        </div>

        <form @submit.prevent="kirim"
            class="bg-white border border-slate-200 rounded-[24px] p-4 md:p-8 shadow-[0_4px_20px_rgba(0,0,0,0.02)] w-full">

            <!-- Entitas Pills (Perusahaan Anda) -->
            <div
                class="flex flex-col md:flex-row md:items-center justify-between mb-6 border-b border-slate-100 pb-4 gap-4">
                <h3 class="text-sm md:text-base font-bold text-slate-800">Entitas Penjual</h3>
                <div
                    class="flex flex-wrap items-center bg-slate-50 p-1 rounded-xl border border-slate-200/60 shadow-inner">
                    <button v-for="ent in listEntitas" :key="ent.id" type="button" @click="draf.entitas_id = ent.id"
                        :class="['px-4 md:px-6 py-2 text-[10px] md:text-xs font-bold rounded-lg transition-all duration-300 flex-1 md:flex-none text-center',
                            draf.entitas_id === ent.id
                                ? 'bg-white text-slate-800 shadow-[0_2px_10px_rgba(0,0,0,0.05)] border border-slate-100/50'
                                : 'text-slate-400 hover:text-slate-600 hover:bg-slate-100/50']">
                        {{ ent.kode }}
                    </button>
                </div>
            </div>

            <!-- Informasi Utama Penjualan -->
            <div class="grid grid-cols-1 md:grid-cols-3 gap-4 md:gap-6 mb-4">
                <div class="flex flex-col gap-2">
                    <label class="text-xs md:text-sm font-bold text-slate-700">No. SO (Preview)</label>
                    <input :value="previewNomor" type="text" readonly
                        class="px-4 py-2.5 bg-slate-100 border border-slate-200 rounded-xl focus:outline-none text-sm text-slate-500 font-semibold cursor-not-allowed" />
                </div>
                <div class="flex flex-col gap-2">
                    <label class="text-xs md:text-sm font-bold text-slate-700">Tanggal Transaksi</label>
                    <input v-model="draf.tanggal" type="date" required
                        class="px-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm text-slate-800" />
                </div>
                <div class="flex flex-col gap-2">
                    <label class="text-xs md:text-sm font-bold text-slate-700">Pelanggan (Customer)</label>
                    <select v-model.number="draf.pelanggan_id" required
                        class="px-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm text-slate-800 appearance-none">
                        <option value="" disabled>-- Pilih Pelanggan --</option>
                        <option v-for="plg in listPelanggan" :key="plg.id" :value="plg.id">
                            {{ plg.nama }}{{ plg.kota ? ` — ${plg.kota}` : '' }}
                        </option>
                    </select>
                </div>
            </div>

            <!-- Detail Item Pesanan (Format HTML Valid) -->
            <div class="w-full mb-8">
                <!-- Header & Tombol Tambah Item -->
                <div class="flex justify-between items-center mb-4 pb-2 mt-4 border-b border-slate-100">
                    <h3 class="text-sm md:text-base font-bold text-slate-800">Daftar Produk Terjual</h3>
                    <button type="button" @click="tambahItem"
                        class="px-3 py-2 md:px-4 md:py-2 bg-blue-50 hover:bg-blue-100 text-blue-600 text-[10px] md:text-xs font-bold rounded-lg transition-colors flex items-center gap-2">
                        <i class="pi pi-plus"></i> Tambah Item
                    </button>
                </div>

                <table class="w-full text-left text-sm table-fixed">
                    <thead class="hidden md:table-header-group text-slate-500 bg-slate-50/50">
                        <tr>
                            <th class="py-3 px-3 font-semibold rounded-tl-xl w-[45%]">Item / Jasa</th>
                            <th class="py-3 px-2 font-semibold w-[15%] text-right">Qty</th>
                            <th class="py-3 px-2 font-semibold w-[20%] text-right pr-4">Harga Jual</th>
                            <th class="py-3 px-2 font-semibold w-[15%] text-right">Subtotal</th>
                            <th class="py-3 px-2 font-semibold text-center rounded-tr-xl w-[5%]"></th>
                        </tr>
                    </thead>
                    <tbody class="block md:table-row-group">
                        <tr v-for="(item, index) in draf.items" :key="index"
                            class="block md:table-row bg-white border border-slate-200 md:border-b md:border-x-0 md:border-t-0 md:border-slate-100 rounded-2xl md:rounded-none mb-6 md:mb-0 p-4 md:p-0 shadow-sm md:shadow-none relative transition-colors">

                            <td class="block md:table-cell md:py-3 md:px-2 mb-3 md:mb-0">
                                <label class="md:hidden text-xs font-bold text-slate-500 mb-1 block">Produk</label>
                                <Dropdown v-model="item.produk" :options="listProduk" optionLabel="nama"
                                    placeholder="Pilih atau cari produk..." class="w-full" filter :pt="{
                                        root: { class: 'w-full h-[42px] md:h-[38px] bg-slate-50 border border-slate-200 rounded-lg flex items-center' }
                                    }">
                                    <template #value="slotProps">
                                        <span v-if="slotProps.value" class="text-sm text-slate-800">{{
                                            slotProps.value.kode }} - {{ slotProps.value.nama }}</span>
                                        <span v-else class="text-sm text-slate-400">{{ slotProps.placeholder }}</span>
                                    </template>
                                    <template #option="slotProps">
                                        <span class="text-sm text-slate-700">{{ slotProps.option.kode }} - {{
                                            slotProps.option.nama }}</span>
                                    </template>
                                </Dropdown>
                            </td>

                            <td class="block md:table-cell md:py-3 md:px-2 mb-3 md:mb-0">
                                <label class="md:hidden text-xs font-bold text-slate-500 mb-1 block">Qty</label>
                                <input v-model.number="item.qty" type="number" min="0" step="0.01" required
                                    class="w-full px-3 py-2.5 md:py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm md:text-right focus:ring-2 focus:ring-blue-500 text-slate-800"
                                    placeholder="0" />
                            </td>

                            <td class="block md:table-cell md:py-3 md:px-2 mb-4 md:mb-0">
                                <label class="md:hidden text-xs font-bold text-slate-500 mb-1 block">Harga Jual
                                    (Rp)</label>
                                <div class="relative">
                                    <span
                                        class="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 font-bold text-sm">Rp</span>
                                    <input v-model.number="item.harga_jual" type="number" min="0" step="1"
                                        class="w-full pl-9 pr-3 py-2.5 md:py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm text-right focus:ring-2 focus:ring-blue-500 text-slate-800"
                                        placeholder="0" />
                                </div>
                            </td>

                            <td
                                class="flex justify-between items-center md:table-cell md:py-3 md:px-2 bg-slate-50 md:bg-transparent p-3 rounded-lg md:rounded-none mb-3 md:mb-0 font-black text-slate-800 md:text-right">
                                <span class="md:hidden text-xs text-slate-500 uppercase">Subtotal</span>
                                Rp {{ (subtotal(item)).toLocaleString('id-ID') }}
                            </td>

                            <td
                                class="block md:table-cell md:py-3 md:px-2 text-center border-t border-slate-100 md:border-none mt-2 md:mt-0 pt-4 md:pt-0">
                                <button type="button" @click="hapusItem(index)" :disabled="draf.items.length === 1"
                                    class="w-full md:w-8 h-10 md:h-8 rounded-lg text-slate-400 hover:text-red-500 hover:bg-red-50 disabled:opacity-30 disabled:hover:bg-transparent transition-colors flex items-center justify-center gap-2 mx-auto">
                                    <i class="pi pi-times md:text-sm"></i>
                                    <span class="md:hidden font-bold text-sm text-red-500">Hapus Item</span>
                                </button>
                            </td>
                        </tr>
                    </tbody>
                </table>
            </div>

            <!-- Kalkulasi Footer (Subtotal & PPN Keluaran) -->
            <div
                class="flex flex-col md:flex-row justify-between items-start bg-slate-50 p-4 md:p-6 rounded-2xl border border-slate-100">
                <div class="flex flex-col gap-2 w-full md:w-auto mb-6 md:mb-0">
                    <div class="flex items-center gap-2">
                        <input type="checkbox" id="pakaiPpn" :true-value="11" :false-value="0" v-model="draf.ppn_persen"
                            class="w-4 h-4 rounded border-slate-300 text-blue-600 focus:ring-blue-600 cursor-pointer">
                        <label for="pakaiPpn" class="text-sm font-bold text-slate-700 cursor-pointer select-none">
                            Kenakan PPN 11% (PPN Keluaran)
                        </label>
                    </div>
                    <div class="text-slate-500 text-[11px] md:text-xs flex items-center gap-1.5">
                        <i class="pi pi-info-circle"></i> Centang ini untuk menerbitkan Faktur Pajak.
                    </div>
                </div>

                <div class="flex flex-col w-full md:w-64 gap-2 border-t md:border-none border-slate-200 pt-4 md:pt-0">
                    <div class="flex justify-between items-center text-sm">
                        <span class="font-semibold text-slate-500">Subtotal Penjualan</span>
                        <span class="font-bold text-slate-700">Rp {{ (subtotalSemua).toLocaleString('id-ID') }}</span>
                    </div>

                    <div v-if="draf.ppn_persen > 0" class="flex justify-between items-center text-sm animate-fade-in">
                        <span class="font-semibold text-blue-600">PPN (11%)</span>
                        <span class="font-bold text-blue-700">Rp {{ (ppnNominal).toLocaleString('id-ID') }}</span>
                    </div>

                    <div class="flex justify-between items-end mt-2 pt-2 border-t border-slate-200">
                        <span
                            class="text-[10px] md:text-xs font-bold text-slate-400 uppercase tracking-wider mb-1">Total
                            Tagihan</span>
                        <span class="text-2xl font-black text-slate-800">Rp {{ (grandTotal).toLocaleString('id-ID')
                        }}</span>
                    </div>

                    <button type="submit" :disabled="sedangProses || periodeDitutup"
                        class="mt-4 w-full justify-center px-6 py-3.5 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-400 text-white font-bold rounded-xl shadow-[0_4px_15px_rgba(37,99,235,0.3)] transition-all flex items-center gap-2 cursor-pointer disabled:cursor-not-allowed">
                        <i class="pi" :class="sedangProses ? 'pi-spin pi-spinner' : 'pi-check-circle'"></i>
                        {{ sedangProses ? 'Memproses...' : 'Terbitkan SO' }}
                    </button>
                </div>
            </div>
        </form>

        <!-- Placeholder untuk Modal Master Data (bisa disesuaikan komponennya) -->
        <!-- <CustomerForm v-if="showModalCustomer" @close="showModalCustomer = false" @saved="handleCustomerSaved" /> -->
        <!-- <ProductEntry v-if="showModalProduct" @close="showModalProduct = false" @saved="handleProductSaved" /> -->
    </div>
</template>

<script setup>
import { reactive, computed, ref, watch, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import Dropdown from 'primevue/dropdown'
import { useSalesOrder } from '@/features/accounting/composables/useSalesOrder'

const router = useRouter()
const {
    listEntitas, listPelanggan, listProduk, sedangProses, pesanError, previewNomor,
    periodeDitutup, muatDataMaster, muatPreviewNomor, simpanSO
} = useSalesOrder()

const showModalCustomer = ref(false)
const showModalProduct = ref(false)

const hariIni = () => {
    const t = new Date(Date.now() - new Date().getTimezoneOffset() * 60_000)
    return t.toISOString().slice(0, 10)
}

const itemKosong = () => ({ produk: null, qty: null, harga_jual: null })

const draf = reactive({
    entitas_id: '',
    pelanggan_id: '',
    tanggal: hariIni(),
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

watch([() => draf.entitas_id, () => draf.tanggal], async ([entitas, tanggal]) => {
    if (entitas && tanggal) {
        await muatPreviewNomor(entitas, tanggal)
    } else {
        previewNomor.value = 'Pilih entitas & tanggal'
    }
})

// === LOGIKA KALKULASI HARGA & PPN ===
const subtotal = (item) => (Number(item.qty) || 0) * (Number(item.harga_jual) || 0)
const subtotalSemua = computed(() => draf.items.reduce((s, i) => s + subtotal(i), 0))
const ppnNominal = computed(() => subtotalSemua.value * (draf.ppn_persen / 100))
const grandTotal = computed(() => subtotalSemua.value + ppnNominal.value)
// ====================================

const tambahItem = () => draf.items.push(itemKosong())
const hapusItem = (i) => {
    if (draf.items.length > 1) draf.items.splice(i, 1)
}

const kirim = async () => {
    pesanError.value = ''
    const kosong = draf.items.some(i => !i.produk?.id || !(Number(i.qty) > 0))
    if (kosong) {
        pesanError.value = 'Setiap item butuh produk yang valid dan Qty minimal 1.'
        return
    }

    const payload = {
        entitas_id: draf.entitas_id,
        pelanggan_id: draf.pelanggan_id,
        tanggal: draf.tanggal,
        catatan: draf.catatan,
        ppn_persen: draf.ppn_persen || 0,
        items: draf.items.map(i => ({
            produk_id: i.produk.id,
            qty: Number(i.qty) || 0,
            harga_jual: Number(i.harga_jual) || 0,
            satuan: i.produk.satuan_kode || 'pcs',
        })),
    }

    const hasil = await simpanSO(payload)

    if (hasil.success) {
        // Arahkan kembali ke tabel daftar SO (Sesuaikan rute Anda)
        router.push('/accounting/input/so')
    }
}
</script>

<style scoped>
.animate-fade-in {
    animation: fadeIn 0.3s ease-out forwards;
}

@keyframes fadeIn {
    from {
        opacity: 0;
        transform: translateY(10px);
    }

    to {
        opacity: 1;
        transform: translateY(0);
    }
}
</style>