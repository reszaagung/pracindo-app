<template>
    <div class="pos-retail max-w-7xl mx-auto pb-10 space-y-6">

        <!-- HEADER ALA PRACINDO ERP (Sesuai Gambar) -->
        <header class="flex justify-between items-end border-b border-slate-200 pb-4">
            <div>
                <p class="text-sm text-slate-500 mb-1">Retail / Point of Sale</p>
                <h1 class="text-2xl font-bold text-slate-800">Kasir Cabang</h1>
            </div>
            <!-- Boks Pencarian (Visual pelengkap estetika) -->
            <div class="hidden md:flex items-center bg-slate-50 border border-slate-200 rounded-lg px-3 py-1.5 shadow-sm">
                <i class="pi pi-search text-slate-400 mr-2 text-sm"></i>
                <input type="text" placeholder="Cari barcode / produk..." class="bg-transparent border-none text-sm outline-none w-48 text-slate-700 placeholder:text-slate-400">
            </div>
        </header>

        <!-- CONTAINER UTAMA -->
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
                        <div class="h-20 bg-slate-50 rounded-lg mb-3 flex items-center justify-center text-slate-400 text-sm font-mono group-hover:bg-blue-50 transition-colors">
                            {{ item.barcode || 'NO-BARCODE' }}
                        </div>
                        <p class="font-semibold text-sm text-slate-700 truncate" :title="item.nama">{{ item.nama }}</p>
                        <p class="text-blue-600 font-bold mt-1">Rp {{ item.harga }}</p>
                        <p class="text-xs text-slate-400 mt-auto pt-3">Stok: {{ item.stok }}</p>
                    </div>
                </div>
            </div>

            <!-- BAGIAN KANAN: KERANJANG -->
            <div class="w-full lg:w-1/3 bg-white rounded-[20px] shadow-[0_8px_30px_rgb(0,0,0,0.04)] border border-slate-100 flex flex-col h-[calc(100vh-230px)] overflow-hidden">
                <div class="p-4 md:p-5 border-b border-slate-100 bg-slate-50/50">
                    <h2 class="font-bold text-slate-700">Keranjang Belanja</h2>
                </div>

                <div class="flex-1 overflow-y-auto p-4 md:p-5 custom-scrollbar">
                    <!-- Tampilan saat keranjang kosong -->
                    <div v-if="cart.length === 0" class="flex h-full flex-col items-center justify-center opacity-60">
                        <i class="pi pi-shopping-cart text-5xl mb-4 text-slate-300"></i>
                        <p class="text-slate-500 text-sm font-medium">Keranjang masih kosong.</p>
                        <p class="text-slate-400 text-xs mt-1">Klik produk di samping untuk menambah.</p>
                    </div>

                    <!-- Tampilan saat ada barang -->
                    <div v-else class="space-y-3">
                        <div v-for="(cartItem, index) in cart" :key="index"
                            class="flex justify-between items-center bg-white border border-slate-200 p-3 rounded-xl shadow-sm hover:border-blue-300 transition-colors">
                            <div class="overflow-hidden mr-3">
                                <p class="font-bold text-sm text-slate-800 truncate">{{ cartItem.nama }}</p>
                                <p class="text-xs text-slate-500 font-medium mt-0.5">Rp {{ cartItem.harga }} x {{ cartItem.qty }}</p>
                            </div>
                            <div class="flex items-center border border-slate-200 rounded-lg bg-slate-50 shrink-0 overflow-hidden">
                                <button @click="decreaseQty(index)" class="text-red-500 hover:bg-red-100 px-2.5 py-1.5 transition-colors">
                                    <i class="pi pi-minus text-xs"></i>
                                </button>
                                <span class="text-sm font-bold w-7 text-center text-slate-700">{{ cartItem.qty }}</span>
                                <button @click="increaseQty(index)" class="text-blue-600 hover:bg-blue-100 px-2.5 py-1.5 transition-colors">
                                    <i class="pi pi-plus text-xs"></i>
                                </button>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="p-5 bg-slate-50/80 border-t border-slate-100">
                    <div class="flex justify-between items-end mb-4 text-lg">
                        <span class="text-slate-500 font-semibold text-sm uppercase tracking-wider">Total Tagihan</span>
                        <span class="font-bold text-slate-900 text-xl">Rp {{ totalHarga }}</span>
                    </div>
                    <button @click="prosesBayar" :disabled="cart.length === 0 || isLoading"
                        class="w-full bg-slate-800 text-white font-bold py-3.5 rounded-xl hover:bg-slate-900 transition-all shadow-md disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2">
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
import { ref, computed, onMounted } from 'vue'
import { useRetail } from '../composables/useRetail'

const { posProducts, isLoading, fetchPosProducts, checkoutCart } = useRetail()
const cart = ref([])

onMounted(() => {
    fetchPosProducts()
})

const productList = computed(() => {
    if (!posProducts.value) return []
    // Jika data dari API dibungkus oleh Django Pagination (.results)
    if (posProducts.value.results) return posProducts.value.results
    // Jika data dibungkus objek standard axios (.data)
    if (posProducts.value.data) return posProducts.value.data
    // Jika memang sudah bentuk array murni
    if (Array.isArray(posProducts.value)) return posProducts.value

    return []
})

const addToCart = (product) => {
    const existing = cart.value.find(item => item.id === product.id)
    if (existing) {
        if (existing.qty < product.stok) {
            existing.qty++
        }
    } else {
        if (product.stok > 0) {
            cart.value.push({ ...product, qty: 1 })
        }
    }
}

const increaseQty = (index) => {
    const item = cart.value[index]
    const product = productList.value.find(p => p.id === item.id)
    if (product && item.qty < product.stok) {
        item.qty++
    }
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
    if (cart.value.length === 0) return

    const payload = {
        subtotal: totalHarga.value,
        metode_bayar: 'TUNAI',
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
        fetchPosProducts()
    } else {
        alert('Terjadi kesalahan saat memproses pembayaran.')
    }
}
</script>
