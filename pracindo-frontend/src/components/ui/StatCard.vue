<!--
  components/ui/StatCard.vue
  ==========================
  Kartu metrik. SENGAJA tanpa tren persentase: backend belum punya endpoint
  perbandingan periode, dan menampilkan "+12.4%" palsu lebih buruk daripada
  tidak menampilkannya sama sekali.
-->
<template>
    <div class="mk">
        <p class="mk__label">{{ label }}</p>
        <p class="mk__nilai">{{ nilai }}</p>
        <p class="mk__kaki" :class="{ 'mk__kaki--waspada': waspada }">
            <slot>{{ kaki }}</slot>
        </p>
    </div>
</template>

<script setup>
defineProps({
    label: { type: String, required: true },
    nilai: { type: [String, Number], required: true },
    kaki: { type: String, default: '' },
    waspada: { type: Boolean, default: false },
})
</script>

<style scoped>
.mk {
    background: var(--panel);
    padding: 1.15rem 1.25rem;
}

.mk__label {
    margin: 0 0 .6rem;
    font-size: .8125rem;
    color: var(--redup);
}

.mk__nilai {
    margin: 0;
    font-size: 1.625rem;
    font-weight: 700;
    letter-spacing: -.02em;
    line-height: 1;
}

.mk__kaki {
    margin: .65rem 0 0;
    font-size: .75rem;
    color: var(--redup);
    min-height: 1rem;
}

.mk__kaki--waspada {
    color: var(--merah);
    font-weight: 600;
}
</style>