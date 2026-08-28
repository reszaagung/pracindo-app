<!-- src/features/produksi/layout/ProduksiLayout.vue -->
<template>
  <!-- Komponen ini akan berubah secara instan tergantung ukuran layar! -->
  <component :is="layoutAktif" />
</template>

<script setup>
import { shallowRef, onMounted, onUnmounted } from 'vue'

// Import dua desain fisik yang sudah kita buat
import DesktopInputProduksi from './DesktopInputProduksi.vue'
import MobileInputProduksi from './MobileInputProduksi.vue'

// Gunakan shallowRef untuk performa dewa (menghindari reaktivitas berlebih pada komponen raksasa)
const layoutAktif = shallowRef(DesktopInputProduksi)

// Otak pendeteksi layar (Tailwind 'lg' breakpoint = 1024px)
const cekLayar = () => {
  if (window.innerWidth < 1024) {
    layoutAktif.value = MobileInputProduksi
  } else {
    layoutAktif.value = DesktopInputProduksi
  }
}

// Pasang pendengar sensor saat masuk modul
onMounted(() => {
  cekLayar()
  window.addEventListener('resize', cekLayar)
})

// Cabut pendengar sensor saat pindah modul agar RAM tidak bocor
onUnmounted(() => {
  window.removeEventListener('resize', cekLayar)
})
</script>
