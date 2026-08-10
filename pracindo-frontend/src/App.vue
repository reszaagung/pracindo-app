<template>
    <Toast />
    <router-view />
</template>

<script setup>
import Toast from 'primevue/toast'
// useAuth()'s token/profil/modul refs hydrate synchronously from localStorage
// on import — there's nothing to rehydrate on mount.
</script>
