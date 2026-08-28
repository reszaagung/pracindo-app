<template>
  <component :is="layoutAktif" />
</template>

<script setup>
import { shallowRef, onMounted, onUnmounted } from 'vue'
import DesktopDistributionLayout from './DesktopDistributionLayout.vue'
import MobileDistributionLayout from './MobileDistributionLayout.vue'

const layoutAktif = shallowRef(DesktopDistributionLayout)

const cekLayar = () => {
  if (window.innerWidth < 1024) {
    layoutAktif.value = MobileDistributionLayout
  } else {
    layoutAktif.value = DesktopDistributionLayout
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
.fade-enter-active, .fade-leave-active { transition: opacity .15s ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
.custom-scrollbar::-webkit-scrollbar { width: 6px; }
.custom-scrollbar::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 3px; }
@media (prefers-reduced-motion: reduce) {
    .fade-enter-active, .fade-leave-active { transition: none; }
}
</style>
