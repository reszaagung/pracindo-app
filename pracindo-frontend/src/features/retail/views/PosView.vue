<template>
    <div class="pos-retail max-w-7xl mx-auto pb-10 space-y-6">
        <header class="flex justify-between items-end border-b border-slate-200 pb-4">
            <div>
                <p class="text-sm text-slate-500 mb-1">Retail / Point of Sale</p>
                <h1 class="text-2xl font-bold text-slate-800">Kasir Cabang</h1>
            </div>
            <div class="hidden md:flex items-center bg-slate-50 border border-slate-200 rounded-lg px-3 py-1.5 shadow-sm">
                <i class="pi pi-search text-slate-400 mr-2 text-sm"></i>
                <input type="text" placeholder="Cari produk..." class="bg-transparent border-none text-sm outline-none w-48 text-slate-700">
            </div>
        </header>

        <div class="flex flex-col lg:flex-row gap-6">
            <!-- BAGIAN KIRI: DAFTAR PRODUK -->
            <div class="w-full lg:w-2/3 bg-white rounded-[20px] shadow-[0_8px_30px_rgb(0,0,0,0.04)] border border-slate-100 flex flex-col h-[calc(100vh-230px)] overflow-hidden">
                <div class="p-4 md:p-5 border-b border-slate-100 bg-slate-50/50 flex justify-between items-center">
                    <h2 class="font-bold text-slate-700">Daftar Produk</h2>
                    <span class="text-xs font-semibold bg-blue-100 text-blue-700 px-2.5 py-1 rounded-md">{{ productList.length }} Item</span>
                </div>
                <div class="flex-1 overflow-y-auto p-4 md:p-5 grid grid-cols-2 sm:grid-cols-3 xl:grid-cols-4 gap-4 custom-scrollbar">
                    <div v-for="item in productList" :key="item.id" @click="addToCart(item)"
                        class="bg-white p-4 rounded-xl shadow-sm border border-slate-200 cursor-pointer hover:border-blue-500 hover:shadow-md transition-all text-center group flex flex-col">
                        <div class="h-16 bg-slate-50 rounded-lg mb-3 flex items-center justify-center text-slate-400 text-xs font-mono group-hover:bg-blue-50 transition-colors">
                            {{ item.produk_nama || item.nama }}
                        </div>
                        <p class="font-semibold text-sm text-slate-700 truncate">{{ item.produk_nama || item.nama }}</p>
                        <p class="text-blue-600 font-bold mt-1">Rp {{ item.harga_jual || item.harga }}</p>
                        <p class="text-xs text-slate-400 mt-auto pt-3">Stok: {{ item.qty || item.stok }}</p>
                    </div>
                </div>
            </div>

            <!-- BAGIAN KANAN: KERANJANG & PEMBAYARAN -->
            <div class="w-full lg:w-1/3 bg-white rounded-[20px] shadow-[0_8px_30px_rgb(0,0,0,0.04)] border border-slate-100 flex flex-col h-[calc(100vh-230px)] overflow-hidden">
                <div class="p-4 md:p-5 border-b border-slate-100 bg-slate-50/50">
                    <h2 class="font-bold text-slate-700">Keranjang Belanja</h2>
                </div>

                <div class="flex-1 overflow-y-auto p-4 md:p-5 custom-scrollbar">
                    <div v-if="cart.length === 0" class="flex h-full flex-col items-center justify-center opacity-60">
                        <i class="pi pi-shopping-cart text-5xl mb-4 text-slate-300"></i>
                        <p class="text-slate-500 text-sm font-medium">Keranjang kosong.</p>
                    </div>
                    <div v-else class="space-y-3">
                        <div v-for="(cartItem, index) in cart" :key="index" class="flex justify-between items-center bg-white border border-slate-200 p-3 rounded-xl shadow-sm hover:border-blue-300">
                            <div class="overflow-hidden mr-3">
                                <p class="font-bold text-sm text-slate-800 truncate">{{ cartItem.nama }}</p>
                                <p class="text-xs text-slate-500 font-medium mt-0.5">Rp {{ cartItem.harga }} x {{ cartItem.qty }}</p>
                            </div>
                            <div class="flex items-center border border-slate-200 rounded-lg bg-slate-50 shrink-0 overflow-hidden">
                                <button @click="decreaseQty(index)" class="text-red-500 hover:bg-red-100 px-2.5 py-1.5 transition-colors"><i class="pi pi-minus text-xs"></i></button>
                                <span class="text-sm font-bold w-7 text-center text-slate-700">{{ cartItem.qty }}</span>
                                <button @click="increaseQty(index)" class="text-blue-600 hover:bg-blue-100 px-2.5 py-1.5 transition-colors"><i class="pi pi-plus text-xs"></i></button>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- AREA FORM PEMBAYARAN -->
                <div class="p-4 md:p-5 bg-slate-50/80 border-t border-slate-100 space-y-4">
                    <!-- Dropdown Sales & Pelanggan -->
                    <div class="grid grid-cols-2 gap-3">
                        <div>
                            <label class="block text-xs font-semibold text-slate-600 mb-1">Sales (Opsional)</label>
                            <select v-model="selectedSales" class="w-full text-sm border border-slate-200 rounded-lg px-2 py-1.5 outline-none focus:border-blue-500">
                                <option :value="null">-- Tanpa Sales --</option>
                                <option v-for="s in salesList" :key="s.id" :value="s.id">{{ s.nama }}</option>
                            </select>
                        </div>
                        <div>
                            <label class="block text-xs font-semibold text-slate-600 mb-1">Pelanggan <span v-if="metodeBayar === 'TEMPO'" class="text-red-500">*</span></label>
                            <select v-model="selectedPelanggan" class="w-full text-sm border border-slate-200 rounded-lg px-2 py-1.5 outline-none focus:border-blue-500">
                                <option :value="null">-- Umum --</option>
                                <option v-for="p in pelangganList" :key="p.id" :value="p.id">{{ p.nama }}</option>
                            </select>
                        </div>
                    </div>

                    <!-- Pilihan Tunai / Tempo -->
                    <div>
                        <label class="block text-xs font-semibold text-slate-600 mb-1">Metode Bayar</label>
                        <div class="flex gap-2">
                            <button @click="metodeBayar = 'TUNAI'" :class="metodeBayar === 'TUNAI' ? 'bg-blue-600 text-white shadow-md' : 'bg-slate-200 text-slate-600 hover:bg-slate-300'" class="flex-1 py-1.5 rounded-lg text-sm font-bold transition-all">TUNAI</button>
                            <button @click="metodeBayar = 'TEMPO'" :class="metodeBayar === 'TEMPO' ? 'bg-orange-500 text-white shadow-md' : 'bg-slate-200 text-slate-600 hover:bg-slate-300'" class="flex-1 py-1.5 rounded-lg text-sm font-bold transition-all">TEMPO (BON)</button>
                        </div>
                    </div>

                    <div class="flex justify-between items-end mb-2 pt-2 border-t border-slate-200">
                        <span class="text-slate-500 font-semibold text-sm">TOTAL</span>
                        <span class="font-bold text-slate-900 text-xl">Rp {{ totalHarga.toLocaleString('id-ID') }}</span>
                    </div>

                    <button @click="prosesBayar" :disabled="cart.length === 0 || isLoading || (metodeBayar === 'TEMPO' && !selectedPelanggan)"
                        class="w-full bg-slate-800 text-white font-bold py-3.5 rounded-xl hover:bg-slate-900 transition-all shadow-md disabled:opacity-50 flex items-center justify-center gap-2">
                        <i v-if="isLoading" class="pi pi-spinner pi-spin"></i>
                        <i v-else class="pi pi-check-circle"></i>
                        <span>{{ isLoading ? 'MEMPROSES...' : 'BAYAR SEKARANG' }}</span>
                    </button>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRetail } from '../composables/useRetail'

const {
    posProducts, isLoading, pelangganList, salesList,
    fetchPosProducts, fetchPelanggan, fetchSales, checkoutCart
} = useRetail()

const cart = ref([])
const metodeBayar = ref('TUNAI')
const selectedPelanggan = ref(null)
const selectedSales = ref(null)

onMounted(() => {
    fetchPosProducts()
    fetchPelanggan()
    fetchSales()
})

// Jika pelanggan dipilih, otomatis pilih sales yang mengikat pelanggan tersebut
watch(selectedPelanggan, (newVal) => {
    if (newVal) {
        const p = pelangganList.value.find(x => x.id === newVal)
        if (p && p.sales) {
            selectedSales.value = p.sales
        }
    }
})

const productList = computed(() => {
    if (!posProducts.value) return []
    if (posProducts.value.results) return posProducts.value.results
    if (posProducts.value.data) return posProducts.value.data
    if (Array.isArray(posProducts.value)) return posProducts.value
    return []
})

const addToCart = (product) => {
    const existing = cart.value.find(item => item.id === (product.produk_id || product.id))
    const pStok = product.qty || product.stok

    if (existing) {
        if (existing.qty < pStok) existing.qty++
    } else {
        if (pStok > 0) {
            cart.value.push({
                id: product.produk_id || product.id,
                nama: product.produk_nama || product.nama,
                harga: product.harga_jual || product.harga,
                stok: pStok,
                qty: 1
            })
        }
    }
}

const increaseQty = (index) => {
    const item = cart.value[index]
    if (item.qty < item.stok) item.qty++
}

const decreaseQty = (index) => {
    if (cart.value[index].qty > 1) {
        cart.value[index].qty--
    } else {
        cart.value.splice(index, 1)
    }
}

const totalHarga = computed(() => {
    return cart.value.reduce((total, item) => total + (item.harga * item.qty), 0)
})

const prosesBayar = async () => {
    if (metodeBayar.value === 'TEMPO' && !selectedPelanggan.value) {
        alert('Untuk pembayaran TEMPO, Anda wajib memilih Pelanggan!')
        return
    }

    const payload = {
        subtotal: totalHarga.value,
        metode_bayar: metodeBayar.value,
        pelanggan_id: selectedPelanggan.value,
        sales_id: selectedSales.value,
        keranjang: cart.value.map(item => ({
            id: item.id,
            qty: item.qty,
            harga: item.harga
        }))
    }

    const result = await checkoutCart(payload)
    if (result.status === 'sukses') {
        alert(`Transaksi Berhasil!\nNomor Struk: ${result.nomor_struk}`)
        cart.value = []
        metodeBayar.value = 'TUNAI'
        selectedPelanggan.value = null
        selectedSales.value = null
        fetchPosProducts()
    } else {
        alert(`Gagal: ${result.pesan}`)
    }
}
</script>
