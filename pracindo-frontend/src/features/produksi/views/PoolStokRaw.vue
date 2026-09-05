<!-- src/features/inventory/components/PoolStokRaw.vue -->
<template>
    <div class="bg-white border border-slate-200 rounded-[24px] p-6 shadow-sm w-full max-w-md animate-fade-in">
        <h3 class="text-lg font-bold text-slate-800 mb-1">Catat Pemakaian (Raw)</h3>
        <p class="text-xs text-slate-500 mb-6">Keluarkan fisik barang dari saldo Pool</p>

        <div v-if="galatMutasi" class="mb-4 p-3 bg-red-50 border border-red-200 text-red-600 text-xs font-medium rounded-xl flex items-start gap-2">
            <i class="pi pi-exclamation-triangle mt-0.5"></i>
            <span>{{ galatMutasi }}</span>
        </div>
        
        <div v-if="suksesMutasi" class="mb-4 p-3 bg-emerald-50 border border-emerald-200 text-emerald-700 text-xs font-bold rounded-xl flex items-center gap-2">
            <i class="pi pi-check-circle"></i>
            <span>Pemakaian stok berhasil dicatat!</span>
        </div>

        <form @submit.prevent="prosesPemakaian" class="flex flex-col gap-4">
            <div>
                <label class="block text-xs font-bold text-slate-700 mb-1.5">Pilih Produk (Raw)</label>
                <select v-model="form.produk_id" required 
                    class="w-full p-3 bg-slate-50 border border-slate-200 rounded-xl text-sm text-slate-700 focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 transition-all">
                    <option value="" disabled>-- Pilih Produk di Pool --</option>
                    <option v-for="item in opsiPool" :key="item.produk_id" :value="item.produk_id">
                        {{ item.produk_kode }} ({{ item.produk_nama }})
                    </option>
                </select>
            </div>

            <div>
                <label class="block text-xs font-bold text-slate-700 mb-1.5">Qty Dipakai (Kg)</label>
                <div class="relative">
                    <input v-model.number="form.qty" type="number" step="0.001" min="0.001" required placeholder="0.000"
                        class="w-full p-3 bg-slate-50 border border-slate-200 rounded-xl text-sm font-bold text-slate-800 focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 transition-all" />
                    <span class="absolute right-4 top-3 text-xs font-bold text-slate-400">KG</span>
                </div>
            </div>

            <div>
                <label class="block text-xs font-bold text-slate-700 mb-1.5">Nomor Referensi / Catatan</label>
                <input v-model="form.referensi" type="text" placeholder="Contoh: SPK-PROD-2026"
                    class="w-full p-3 bg-slate-50 border border-slate-200 rounded-xl text-sm text-slate-700 focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 transition-all" />
            </div>

            <button type="submit" :disabled="sedangMemproses"
                class="mt-2 w-full py-3.5 bg-slate-800 hover:bg-slate-900 text-white text-sm font-bold rounded-xl transition-colors disabled:opacity-50 flex items-center justify-center gap-2">
                <i v-if="sedangMemproses" class="pi pi-spin pi-spinner"></i>
                <i v-else class="pi pi-box"></i>
                <span>{{ sedangMemproses ? 'Memproses Mutasi...' : 'Catat Pemakaian' }}</span>
            </button>
        </form>
    </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useMutasi } from '../composables/useStock'
import { useStock } from '../composables/useStock'

const emit = defineEmits(['pemakaian-sukses'])

const form = ref({
    produk_id: '',
    qty: null,
    referensi: '',
    jenis_mutasi: 'TARIK_POOL' 
})

const { tarikStokPool, sedangMemproses, galatMutasi, suksesMutasi } = useMutasi()
const { daftarStok, muatStok } = useStock() 

const opsiPool = ref([])

onMounted(async () => {
    await muatStok({ lapis: 'POOL' })
    opsiPool.value = daftarStok.value
})

const prosesPemakaian = async () => {
    await tarikStokPool(form.value)
    
    if (suksesMutasi.value) {
        form.value.qty = null
        form.value.referensi = ''
        emit('pemakaian-sukses')
    }
}
</script>

<style scoped>
.animate-fade-in {
    animation: fadeIn 0.3s ease-out forwards;
}
@keyframes fadeIn {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
}
</style>