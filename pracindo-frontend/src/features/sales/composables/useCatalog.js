// src/features/sales/composables/useKatalog.js
import { ref, computed } from 'vue'

export function useKatalog() {
    const isLoading = ref(false)
    const keranjang = ref([])

    // MOCKUP: Katalog Produk Digital
    const katalog = ref([
        { id: 'PRD-001', sku: 'PIG-RED-1L', nama: 'Pigment Red 1 Liter', harga: 125000, stok: 45, kategori: 'Bahan Baku' },
        { id: 'PRD-002', sku: 'PIG-BLU-1L', nama: 'Pigment Blue 1 Liter', harga: 130000, stok: 12, kategori: 'Bahan Baku' },
        { id: 'PRD-003', sku: 'SOL-X01', nama: 'Solvent Extra 5L', harga: 450000, stok: 3, kategori: 'Pelarut' },
        { id: 'PRD-004', sku: 'PKG-BTL-1L', nama: 'Botol Kosong 1L + Tutup', harga: 5500, stok: 1200, kategori: 'Kemasan' },
    ])

    // Fungsi Keranjang (Cart)
    const tambahKeKeranjang = (produk) => {
        const ada = keranjang.value.find(item => item.id === produk.id)
        if (ada) {
            if (ada.qty < produk.stok) ada.qty++
        } else {
            if (produk.stok > 0) keranjang.value.push({ ...produk, qty: 1 })
        }
    }

    const kurangiDariKeranjang = (id) => {
        const index = keranjang.value.findIndex(item => item.id === id)
        if (index !== -1) {
            if (keranjang.value[index].qty > 1) {
                keranjang.value[index].qty--
            } else {
                keranjang.value.splice(index, 1)
            }
        }
    }

    const totalNilai = computed(() => {
        return keranjang.value.reduce((total, item) => total + (item.harga * item.qty), 0)
    })

    const totalItem = computed(() => {
        return keranjang.value.reduce((total, item) => total + item.qty, 0)
    })

    const kosongkanKeranjang = () => {
        keranjang.value = []
    }

    return {
        isLoading,
        katalog,
        keranjang,
        totalNilai,
        totalItem,
        tambahKeKeranjang,
        kurangiDariKeranjang,
        kosongkanKeranjang
    }
}