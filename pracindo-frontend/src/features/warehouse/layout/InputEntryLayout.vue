<template>
    <component :is="layoutAktif" />
</template>

<script setup>
import { shallowRef, onMounted, onUnmounted } from 'vue'
import DesktopInputEntryLayout from './DesktopInputEntryLayout.vue'
import MobileInputEntryLayout from './MobileInputEntryLayout.vue'

const layoutAktif = shallowRef(DesktopInputEntryLayout)

const cekLayar = () => {
    if (window.innerWidth < 1024) {
        layoutAktif.value = MobileInputEntryLayout
    } else {
        layoutAktif.value = DesktopInputEntryLayout
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
/* Style global untuk Layout Input Gudang */
.fade-enter-active, .fade-leave-active { transition: opacity .15s ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
.custom-scrollbar::-webkit-scrollbar { width: 6px; }
.custom-scrollbar::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 3px; }
</style>