<template>
    <div class="memuat">
        <span class="memuat__garis"></span> {{ pesan }}
    </div>
</template>

<script setup>
defineProps({
    pesan: {
        type: String,
        default: 'Memuat data...'
    }
})
</script>

<style scoped>
.memuat {
    display: flex;
    align-items: center;
    gap: 0.85rem;
    padding: 3rem 0;
    color: var(--redup);
    font-size: 0.9375rem;
}

.memuat__garis {
    width: 2.5rem;
    height: 2px;
    background: var(--garis);
    overflow: hidden;
    position: relative;
}

.memuat__garis::after {
    content: '';
    position: absolute;
    inset: 0;
    background: var(--kuning);
    animation: geser 1.1s ease-in-out infinite;
}

@keyframes geser {
    0% {
        transform: translateX(-100%);
    }

    100% {
        transform: translateX(100%);
    }
}

@media (prefers-reduced-motion: reduce) {
    .memuat__garis::after {
        animation: none;
        opacity: 0.5;
    }
}
</style>