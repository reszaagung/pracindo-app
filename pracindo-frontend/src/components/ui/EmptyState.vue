<!--
  components/ui/EmptyState.vue
  ============================
  Layar kosong = undangan bertindak, bukan pengumuman kegagalan.
-->
<template>
    <div class="kosong">
        <p class="kosong__pesan">{{ pesan }}</p>
        <p v-if="petunjuk" class="kosong__petunjuk">{{ petunjuk }}</p>
        <slot />
    </div>
</template>

<script setup>
defineProps({
    pesan: { type: String, required: true },
    petunjuk: { type: String, default: '' },
})
</script>

<style scoped>
.kosong {
    padding: 3rem 1.5rem;
    text-align: center;
}

.kosong__pesan {
    margin: 0;
    font-size: .9375rem;
    color: var(--teks-2);
}

.kosong__petunjuk {
    margin: .4rem 0 0;
    font-size: .8125rem;
    color: var(--redup-2);
}
</style>