<!--
  components/ui/BaseIcon.vue
  ==========================
  SVG inline dari IKON di config/modules.js — tanpa library ikon.
-->
<template>
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round"
        stroke-linejoin="round" :width="ukuran" :height="ukuran" aria-hidden="true" v-html="jalur" />
</template>

<script setup>
import { computed } from 'vue'
import { IKON } from '@/config/modules'

const props = defineProps({
    nama: { type: String, required: true },
    ukuran: { type: [Number, String], default: 20 },
})

const jalur = computed(() => IKON[props.nama] ?? '<circle cx="12" cy="12" r="8"/>')
</script>