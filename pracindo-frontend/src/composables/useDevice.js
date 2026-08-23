import { ref, computed, onMounted, onUnmounted } from 'vue'

export function useDevice() {
    const windowWidth = ref(typeof window !== 'undefined' ? window.innerWidth : 0)

    const updateWidth = () => {
        windowWidth.value = window.innerWidth
    }

    onMounted(() => {
        window.addEventListener('resize', updateWidth)
        updateWidth()
    })

    onUnmounted(() => {
        window.removeEventListener('resize', updateWidth)
    })

    const isMobile = computed(() => windowWidth.value < 768)
    const isTablet = computed(() => windowWidth.value >= 768 && windowWidth.value < 1024)
    const isDesktop = computed(() => windowWidth.value >= 1024)

    return {
        windowWidth,
        isMobile,
        isTablet,
        isDesktop
    }
}