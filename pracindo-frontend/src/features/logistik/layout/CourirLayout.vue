<template>
  <div class="min-h-screen bg-slate-200 flex justify-center items-start md:items-center p-0 md:p-6 font-sans">
    <div class="w-full max-w-md bg-slate-50 min-h-screen md:min-h-[800px] md:max-h-[90vh] md:rounded-[2.5rem] shadow-2xl relative overflow-hidden flex flex-col">
      <router-view />
    </div>
  </div>
</template>

<style scoped>
.fade-enter-active, .fade-leave-active {
    transition: opacity 0.25s ease, transform 0.25s ease;
}
.fade-enter-from {
    opacity: 0;
    transform: translateX(10px);
}
.fade-leave-to {
    opacity: 0;
    transform: translateX(-10px);
}
</style>
