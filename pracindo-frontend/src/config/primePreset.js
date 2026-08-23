// File: src/config/primePreset.js

export const modernDropdown = {
    root: {
        class: 'w-full h-[42px] bg-slate-50 border border-slate-200 rounded-xl flex items-center px-3 font-sans transition-colors focus-within:border-emerald-500 focus-within:ring-1 focus-within:ring-emerald-500 hover:border-slate-300 cursor-pointer relative'
    },
    input: {
        class: 'text-sm text-slate-700 font-semibold font-sans focus:outline-none w-full bg-transparent'
    },
    trigger: {
        class: 'text-slate-400 w-8 flex items-center justify-center'
    },
    panel: {
        // PERBAIKAN 1: Tambah mt-2 (margin-top) agar ada jarak dengan kotak form, dan perjelas border
        class: 'bg-white rounded-xl shadow-[0_10px_40px_-10px_rgba(0,0,0,0.1)] border border-slate-200 font-sans mt-2'
    },
    list: {
        class: 'p-1.5 custom-scrollbar font-sans'
    },
    item: {
        // Tambah sedikit margin antar item (mt-0.5) agar tidak terlalu berdempetan
        class: 'p-2.5 text-sm font-semibold text-slate-600 hover:bg-slate-50 hover:text-slate-900 rounded-lg cursor-pointer transition-colors font-sans mt-0.5'
    },
    itemHighlighted: {
        class: 'bg-emerald-50 text-emerald-700 font-bold'
    },
    filterContainer: {
        // Pastikan container relative untuk mengunci posisi ikon
        class: 'relative w-full p-2 border-b border-slate-100'
    },
    filterInput: {
        // PERBAIKAN 2: Padding kanan (pr-10) dilebarkan agar teks tidak menabrak ikon
        class: 'w-full pl-3 pr-10 py-2 text-sm text-slate-700 bg-slate-50 border border-slate-200 rounded-lg focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 font-sans transition-colors'
    },
    filterIcon: {
        // PERBAIKAN 3: Ikon ditarik ke kanan (right-5) dan dikunci agar tidak bisa diklik (pointer-events-none)
        class: 'absolute right-5 top-1/2 -translate-y-1/2 text-slate-400 text-sm pointer-events-none'
    },
    emptyMessage: {
        class: 'p-4 text-sm text-slate-500 text-center font-sans'
    }
}
