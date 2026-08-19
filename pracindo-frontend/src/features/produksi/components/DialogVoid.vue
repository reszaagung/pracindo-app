<script setup>
import { ref } from 'vue'

const props = defineProps({
    nomor: String
})

const emit = defineEmits(['batal', 'setuju'])
const alasan = ref('')

function kirim() {
    if (alasan.value.trim().length < 5) return
    emit('setuju', alasan.value.trim())
}
</script>

<template>
    <div class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
        <div class="bg-white rounded-lg shadow-xl w-full max-w-md overflow-hidden">
            <div class="bg-red-50 p-4 border-b border-red-100 flex items-start gap-3">
                <div class="text-red-500 text-2xl">⚠️</div>
                <div>
                    <h3 class="text-red-800 font-bold text-lg">Void Batch {{ nomor }}?</h3>
                    <p class="text-red-600 text-xs mt-1">
                        Ini akan membalikkan uang dan kuantitas dari tangki kembali ke sumber asalnya.
                    </p>
                </div>
            </div>
            <div class="p-4 space-y-3 text-sm text-gray-700">
                <p><strong>Peringatan:</strong> Jika nilai batch ini sudah ada yang ditarik oleh Packing, sistem akan menolak Void secara otomatis untuk mencegah konflik saldo. Dalam kasus tersebut, gunakan penyesuaian manual.</p>
                <label class="block">
                    <span class="font-bold text-gray-800">Alasan Pembatalan <span class="text-red-500">*</span></span>
                    <textarea v-model="alasan" rows="3" placeholder="Wajib diisi minimal 5 karakter..."
                        class="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:border-red-500 focus:ring-red-500 text-sm"></textarea>
                </label>
            </div>
            <div class="bg-gray-50 px-4 py-3 border-t flex justify-end gap-2">
                <button @click="$emit('batal')"
                    class="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded hover:bg-gray-50 transition-colors">
                    Batal
                </button>
                <button @click="kirim" :disabled="alasan.trim().length < 5"
                    class="px-4 py-2 text-sm font-bold text-white bg-red-600 rounded hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors">
                    Void Sekarang
                </button>
            </div>
        </div>
    </div>
</template>
