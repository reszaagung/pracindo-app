<template>
  <component :is="layoutAktif" />
</template>

<script setup>
import { shallowRef, onMounted, onUnmounted } from 'vue'
import DesktopWarehouseMainLayout from './DesktopWarehouseMainLayout.vue'
import MobileWarehouseMainLayout from './MobileWarehouseMainLayout.vue'

const layoutAktif = shallowRef(DesktopWarehouseMainLayout)

const cekLayar = () => {
  if (window.innerWidth < 1024) {
    layoutAktif.value = MobileWarehouseMainLayout
  } else {
    layoutAktif.value = DesktopWarehouseMainLayout
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
</style>
