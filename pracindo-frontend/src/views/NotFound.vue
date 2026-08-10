<!--
  views/NotFound.vue
  ==================
  404 yang menyebut path-nya. Sebelumnya rute mati di-redirect diam-diam ke
  dashboard, jadi tautan salah di menu tidak pernah ketahuan — sekarang
  kelihatan, lengkap dengan path yang dicari.
-->
<template>
    <div class="hilang">
        <span class="hilang__tanda">404</span>
        <h1 class="hilang__judul">Halaman tidak ditemukan</h1>
        <p class="hilang__teks">
            Tidak ada rute untuk <code class="hilang__path">{{ route.fullPath }}</code>.
            Kalau kamu sampai di sini lewat menu, tautan menunya salah — laporkan.
        </p>
        <router-link to="/" class="hilang__balik">Kembali ke dashboard</router-link>
    </div>
</template>

<script setup>
import { useRoute } from 'vue-router'

const route = useRoute()
</script>

<style scoped>
.hilang {
    max-width: 34rem;
    margin: 0 auto;
    padding: 5rem clamp(1rem, 4vw, 2.5rem);
    text-align: center;
}

.hilang__tanda {
    font-size: .75rem;
    font-weight: 700;
    letter-spacing: .1em;
    color: var(--redup-2);
}

.hilang__judul {
    margin: .6rem 0 .5rem;
    font-size: 1.5rem;
    font-weight: 700;
    letter-spacing: -.02em;
}

.hilang__teks {
    margin: 0 0 1.75rem;
    font-size: .9375rem;
    color: var(--redup);
    line-height: 1.6;
}

.hilang__path {
    font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
    font-size: .875rem;
    background: var(--latar);
    border: 1px solid var(--garis);
    border-radius: var(--lengkung-kecil);
    padding: .1rem .35rem;
    word-break: break-all;
}

.hilang__balik {
    font-size: .8125rem;
    color: var(--redup);
    text-decoration: none;
    border: 1px solid var(--garis);
    border-radius: var(--lengkung-kecil);
    padding: .5rem .9rem;
}

.hilang__balik:hover {
    border-color: var(--garis-tegas);
    color: var(--teks);
}
</style>
