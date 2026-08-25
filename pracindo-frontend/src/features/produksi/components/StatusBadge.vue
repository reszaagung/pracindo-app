<template>
  <span :class="['px-2.5 py-1 text-[11px] font-bold uppercase tracking-wider rounded-lg border', badgeClass]">
    {{ statusLabel }}
  </span>
</template>

<script setup>
import { computed } from 'vue'
import { getStatusBadgeClass, STATUS_BATCH_OPTIONS } from '../uiConfigProduksi'

const props = defineProps({
  status: {
    type: String,
    required: true
  }
})

const badgeClass = computed(() => getStatusBadgeClass(props.status))

const statusLabel = computed(() => {
  const found = STATUS_BATCH_OPTIONS.find(opt => opt.value === props.status)
  return found ? found.label : props.status
})
</script>
