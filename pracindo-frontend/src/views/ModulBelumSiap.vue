<!--
  views/ModulBelumSiap.vue
  ========================
  Layar penampung untuk modul yang SUDAH dikirim backend (jadi user berhak
  masuk) tapi layarnya belum dibangun. Judul dan catatan dibaca dari katalog
  lewat route.meta.modul — tidak ada teks per modul di sini.
-->
<template>
    <div class="tunggu">
        <span class="tunggu__tanda">segera</span>
        <h1 class="tunggu__judul">{{ modul?.nama ?? 'Modul ini' }}</h1>
        <p class="tunggu__teks">{{ modul?.catatan || 'Layar untuk modul ini belum dibangun.' }}</p>
        <router-link to="/" class="tunggu__balik">Kembali ke dashboard</router-link>
    </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { cariModul } from '@/config/modules'

const route = useRoute()
const modul = computed(() => cariModul(route.meta?.modul))
</script>

<style scoped>
.tunggu {
    max-width: 34rem;
    margin: 0 auto;
    padding: 5rem clamp(1rem, 4vw, 2.5rem);
    text-align: center;
}

.tunggu__tanda {
    display: inline-block;
    font-size: .625rem;
    font-weight: 600;
    letter-spacing: .06em;
    text-transform: uppercase;
    color: var(--redup-2);
    border: 1px solid var(--garis);
    padding: .12rem .45rem;
    border-radius: 5px;
}

.tunggu__judul {
    margin: 1rem 0 .5rem;
    font-size: 1.5rem;
    font-weight: 700;
    letter-spacing: -.02em;
}

.tunggu__teks {
    margin: 0 0 1.75rem;
    font-size: .9375rem;
    color: var(--redup);
}

.tunggu__balik {
    font-size: .8125rem;
    color: var(--redup);
    text-decoration: none;
    border: 1px solid var(--garis);
    border-radius: var(--lengkung-kecil);
    padding: .5rem .9rem;
}

.tunggu__balik:hover {
    border-color: var(--garis-tegas);
    color: var(--teks);
}
</style>
