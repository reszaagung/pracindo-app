<template>
    <div class="flex flex-col w-full animate-fade-in relative">
        <div class="mb-6 flex flex-col md:flex-row justify-between items-start md:items-end gap-4">
            <div>
                <p class="text-xs text-slate-400 mb-1">
                    <span class="hover:text-slate-700 transition-colors">Distribution</span> /
                    <span class="text-slate-600 font-semibold">Validasi Muat (Loading)</span>
                </p>
                <h1 class="text-xl md:text-2xl font-bold text-slate-800 tracking-tight">Validasi Muat Barang</h1>
                <p class="text-xs md:text-sm text-slate-500 mt-1">Pindai atau centang barang yang naik ke armada agar sesuai dengan DO.</p>
            </div>
            <button class="px-5 py-2.5 bg-blue-600 hover:bg-blue-700 text-white text-sm font-bold rounded-xl transition-colors shadow-md flex items-center gap-2">
                <i class="pi pi-qrcode text-xs"></i>
                <span>Scan Barcode</span>
            </button>
        </div>

        <div class="bg-white border border-slate-200 rounded-[24px] p-4 md:p-6 shadow-sm w-full mb-6">
            <div class="flex flex-col md:flex-row justify-between md:items-center border-b border-slate-100 pb-4 mb-4">
                <div>
                    <h2 class="text-lg font-black text-slate-800">DO-202608-002</h2>
                    <p class="text-sm text-slate-500 font-medium">Tujuan: Depo Bangunan Pusat (Surabaya)</p>
                </div>
                <div class="mt-3 md:mt-0 text-left md:text-right">
                    <span class="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-0.5">Armada</span>
                    <span class="px-3 py-1 bg-slate-100 text-slate-700 rounded-lg text-sm font-bold border border-slate-200">
                        <i class="pi pi-truck mr-1 text-slate-400"></i> L 8821 XA (Ahmad M.)
                    </span>
                </div>
            </div>

            <div class="overflow-x-auto custom-scrollbar">
                <table class="w-full text-left text-sm table-auto min-w-[50rem]">
                    <thead class="text-slate-500 bg-slate-50/50">
                        <tr>
                            <th class="py-3 px-4 font-semibold rounded-tl-xl w-[40%]">Nama Produk / Varian</th>
                            <th class="py-3 px-4 font-semibold text-right w-[15%]">Qty DO</th>
                            <th class="py-3 px-4 font-semibold text-right w-[15%]">Qty Muat</th>
                            <th class="py-3 px-4 font-semibold text-center w-[15%]">Status</th>
                            <th class="py-3 px-4 font-semibold text-center rounded-tr-xl w-[15%]">Aksi</th>
                        </tr>
                    </thead>
                    <tbody class="divide-y divide-slate-100">
                        <tr class="hover:bg-slate-50/50 transition-colors">
                            <td class="py-4 px-4">
                                <div class="font-bold text-slate-800">Super White SC SC</div>
                                <div class="text-[11px] text-slate-500 mt-0.5">Karung / Sak</div>
                            </td>
                            <td class="py-4 px-4 text-right font-medium text-slate-500">150</td>
                            <td class="py-4 px-4 text-right font-black text-emerald-600 text-base">150</td>
                            <td class="py-4 px-4 text-center">
                                <span class="px-2.5 py-1 bg-emerald-50 text-emerald-600 border border-emerald-200 rounded-md text-[10px] font-bold tracking-wide uppercase">Sesuai</span>
                            </td>
                            <td class="py-4 px-4 text-center">
                                <button class="w-8 h-8 bg-slate-100 text-slate-400 rounded-lg cursor-not-allowed mx-auto flex items-center justify-center">
                                    <i class="pi pi-check"></i>
                                </button>
                            </td>
                        </tr>
                        <tr class="hover:bg-slate-50/50 transition-colors">
                            <td class="py-4 px-4">
                                <div class="font-bold text-slate-800">Super White Standard</div>
                                <div class="text-[11px] text-slate-500 mt-0.5">Karung / Sak</div>
                            </td>
                            <td class="py-4 px-4 text-right font-medium text-slate-500">50</td>
                            <td class="py-4 px-4 text-right font-black text-amber-500 text-base">30</td>
                            <td class="py-4 px-4 text-center">
                                <span class="px-2.5 py-1 bg-amber-50 text-amber-600 border border-amber-200 rounded-md text-[10px] font-bold tracking-wide uppercase">Kurang</span>
                            </td>
                            <td class="py-4 px-4 text-center">
                                <button class="w-8 h-8 bg-blue-50 text-blue-600 rounded-lg hover:bg-blue-600 hover:text-white transition-colors mx-auto flex items-center justify-center shadow-sm">
                                    <i class="pi pi-plus"></i>
                                </button>
                            </td>
                        </tr>
                    </tbody>
                </table>
            </div>

            <div class="mt-6 pt-4 border-t border-slate-100 flex justify-end">
                <button class="px-8 py-3 bg-slate-900 hover:bg-slate-800 text-white text-sm font-bold rounded-xl transition-all shadow-md flex items-center gap-2 transform hover:-translate-y-0.5">
                    <i class="pi pi-verified text-xs"></i>
                    <span>Selesaikan Loading & Kunci DO</span>
                </button>
            </div>
        </div>
    </div>
</template>

<style scoped>
.animate-fade-in { animation: fadeIn 0.3s ease-out forwards; }
@keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
.custom-scrollbar::-webkit-scrollbar { height: 6px; }
.custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
.custom-scrollbar::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 4px; }
.custom-scrollbar::-webkit-scrollbar-thumb:hover { background: #94a3b8; }
</style>
