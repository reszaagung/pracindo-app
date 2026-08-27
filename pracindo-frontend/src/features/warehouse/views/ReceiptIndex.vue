<!-- features/warehouse/views/ReceiptIndex.vue -->
<template>
    <div class="flex flex-col w-full animate-fade-in relative">
        <!-- Header & Toggle Group -->
        <div class="mb-6 flex flex-col gap-4">
            <!-- (Judul utama sudah di-handle global oleh useNavInputEntry) -->
            <div>
                <p class="text-xs text-slate-500 mt-1">Pilih jenis dokumen PO yang ingin Anda proses</p>
            </div>

            <!-- Tombol Toggle -->
            <div class="flex flex-wrap gap-3">
                <button @click="ubahTab('bahan_baku')"
                    :class="tabAktif === 'bahan_baku'
                        ? 'border-slate-800 text-slate-900 font-bold shadow-sm bg-white'
                        : 'border-slate-200 text-slate-500 font-medium hover:bg-slate-50'"
                    class="px-5 py-2.5 rounded-xl border flex items-center gap-2 text-sm transition-all focus:outline-none">
                    <i class="pi pi-box"></i> Bahan Baku
                </button>

                <button @click="ubahTab('kemasan')"
                    :class="tabAktif === 'kemasan'
                        ? 'border-slate-800 text-slate-900 font-bold shadow-sm bg-white'
                        : 'border-slate-200 text-slate-500 font-medium hover:bg-slate-50'"
                    class="px-5 py-2.5 rounded-xl border flex items-center gap-2 text-sm transition-all focus:outline-none">
                    <i class="pi pi-shopping-bag"></i> Kemasan
                </button>
            </div>
        </div>

        <!-- Render Konten Secara Dinamis -->
        <transition name="fade" mode="out-in">
            <GoodsReceiptList v-if="tabAktif === 'bahan_baku'" key="bahan_baku" />
            <PackageReceiptList v-else-if="tabAktif === 'kemasan'" key="kemasan" />
        </transition>
    </div>
</template>

<script setup>
import { useReceiptIndex } from '../composables/useReceiptIndex'
import GoodsReceiptList from './GoodsReceiptList.vue'
import PackageReceiptList from './PackageReceiptList.vue'

const { tabAktif, ubahTab } = useReceiptIndex()
</script>

<style scoped>
.animate-fade-in { animation: fadeIn 0.3s ease-out forwards; }
@keyframes fadeIn {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
}
.fade-enter-active, .fade-leave-active { transition: opacity 0.2s ease, transform 0.2s ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; transform: translateY(-5px); }
</style>
