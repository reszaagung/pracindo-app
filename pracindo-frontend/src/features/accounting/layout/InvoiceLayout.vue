<template>
  <component :is="layoutAktif" />
</template>

<script setup>
import { shallowRef, onMounted, onUnmounted } from 'vue'
import DesktopInvoiceLayout from './DesktopInvoiceLayout.vue'
import MobileInvoiceLayout from './MobileInvoiceLayout.vue'

const layoutAktif = shallowRef(DesktopInvoiceLayout)

const cekLayar = () => {
  if (window.innerWidth < 1024) {
    layoutAktif.value = MobileInvoiceLayout
  } else {
    layoutAktif.value = DesktopInvoiceLayout
  }
}

onMounted(() => {
  cekLayar()
  window.addEventListener('resize', cekLayar)
})

onUnmounted(() => {
  window.removeEventListener('resize', cekLayar)
})
</script>

<style>
/* CSS transisi dan scrollbar diletakkan di parent agar ter-apply ke anak-anaknya */
.fade-enter-active, .fade-leave-active { transition: opacity 0.2s ease-in-out; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
.custom-scrollbar::-webkit-scrollbar { width: 6px; }
.custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
.custom-scrollbar::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 999px; }
.custom-scrollbar::-webkit-scrollbar-thumb:hover { background: #94a3b8; }
</style>
