<template>
  <div class="p-6 bg-white rounded-lg shadow max-w-4xl mx-auto">
    <div class="flex items-center justify-between mb-6">
      <h2 class="text-2xl font-bold text-gray-800">Input Eksekusi Packing</h2>
      <button @click="$router.back()" class="text-gray-600 hover:underline">Kembali</button>
    </div>

    <div v-if="error" class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
      {{ error }}
    </div>

    <form @submit.prevent="submitForm" class="space-y-6">
      <div class="grid grid-cols-2 gap-4">
        <div>
          <label class="block text-sm font-medium mb-1">Entitas</label>
          <select v-model="form.entitas" required class="w-full border p-2 rounded">
            <option v-for="ent in entitasList" :key="ent.id" :value="ent.id">{{ ent.kode }}</option>
          </select>
        </div>
        <div>
          <label class="block text-sm font-medium mb-1">Batch Produksi (WIP)</label>
          <select v-model="form.batch" required class="w-full border p-2 rounded">
            <option v-for="b in batchList" :key="b.id" :value="b.id">{{ b.nomor }}</option>
          </select>
        </div>
        <div>
          <label class="block text-sm font-medium mb-1">Total Qty Cairan (Kg)</label>
          <input type="number" step="0.001" v-model="form.qty_kg" required class="w-full border p-2 rounded" />
        </div>
      </div>

      <hr />

      <div class="grid grid-cols-2 gap-4">
        <div>
          <label class="block text-sm font-medium mb-1">Kemasan Luar (Dus/Jerigen)</label>
          <select v-model="form.kemasan" @change="cekKemasanDalam" required class="w-full border p-2 rounded">
             <option value="">-- Pilih Kemasan --</option>
             <option v-for="k in kemasanLuarList" :key="k.id" :value="k.id">{{ k.produk_nama }}</option>
          </select>
        </div>
        <div>
          <label class="block text-sm font-medium mb-1">Total Unit (Kemasan Luar)</label>
          <input type="number" v-model="form.total_unit" required class="w-full border p-2 rounded" />
        </div>
      </div>

      <div v-if="butuhKemasanDalam" class="bg-blue-50 p-4 border border-blue-200 rounded grid grid-cols-2 gap-4">
        <div>
          <label class="block text-sm font-medium text-blue-800 mb-1">Isi Kemasan Dalam (Botol/Pouch)</label>
          <select v-model="form.kemasan_dalam" required class="w-full border p-2 rounded border-blue-300">
             <option value="">-- Pilih Botol --</option>
             <option v-for="k in kemasanDalamList" :key="k.id" :value="k.id">{{ k.produk_nama }}</option>
          </select>
        </div>
        <div>
          <label class="block text-sm font-medium text-blue-800 mb-1">Isi Per Dus (Pcs)</label>
          <input type="number" v-model="form.qty_kemasan_dalam" required class="w-full border p-2 rounded border-blue-300" />
        </div>
      </div>

      <div class="flex justify-end pt-4">
        <button type="submit" :disabled="isLoading" class="bg-green-600 text-white px-6 py-2 rounded hover:bg-green-700 font-bold disabled:opacity-50">
          {{ isLoading ? 'Menyimpan & Mengeksekusi...' : 'Simpan & Eksekusi Packing' }}
        </button>
      </div>
    </form>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { warehouseApi } from '../api'
import { usePacking } from '../composables/usePacking'

const router = useRouter()
const { createPacking, isLoading, error } = usePacking()

const entitasList = ref([])
const batchList = ref([])
const kemasanLuarList = ref([])
const kemasanDalamList = ref([])
const butuhKemasanDalam = ref(false)

const form = reactive({
  entitas: '',
  batch: '',
  qty_kg: '',
  kemasan: '',
  total_unit: '',
  kemasan_dalam: '',
  qty_kemasan_dalam: ''
})

const fetchData = async () => {
  try {
    const [resEntitas, resKemasan, resBatch] = await Promise.all([
      warehouseApi.getEntitasAktif(),
      warehouseApi.getKemasanAktif(),
      warehouseApi.getBatchTersedia()
    ])
    entitasList.value = resEntitas.data?.results || resEntitas.data || []
    kemasanLuarList.value = resKemasan.data?.results || resKemasan.data || []
    kemasanDalamList.value = resKemasan.data?.results || resKemasan.data || []
    batchList.value = resBatch.data?.results || resBatch.data || []
  } catch (err) {
    console.error(err)
  }
}

onMounted(() => {
  fetchData()
})

const cekKemasanDalam = (event) => {
  const selectedText = event.target.options[event.target.selectedIndex].text.toUpperCase()
  
  if (selectedText.includes('DUS') || selectedText.includes('KARTON')) {
    butuhKemasanDalam.value = true
  } else {
    butuhKemasanDalam.value = false
    form.kemasan_dalam = ''
    form.qty_kemasan_dalam = ''
  }
}

const submitForm = async () => {
  try {
    const payload = {
      ...form,
      kemasan_dalam: butuhKemasanDalam.value ? form.kemasan_dalam : null,
      qty_kemasan_dalam: butuhKemasanDalam.value ? form.qty_kemasan_dalam : 0
    }
    
    await createPacking(payload)
    alert('Packing berhasil dieksekusi!')
    router.push({ name: 'InputPackingList' })
  } catch (err) {
    console.error(err)
  }
}
</script>