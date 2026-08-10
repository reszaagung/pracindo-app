import { ref, computed } from 'vue'
import api from '@/utils/api'
import { bacaError } from '@/utils/error'
import { generateKode } from '@/utils/generate_id'
export function usePurchaseOrder() {

    const daftarPO = ref([])
    const isLoadingDaftar = ref(false)
    const cari = ref('')
    const saringStatus = ref('semua')

    const listEntitas = ref([])
    const listSupplier = ref([])
    const listProduk = ref([])
    const listSatuan = ref([])
    const sedangProses = ref(false)
    const pesanError = ref('')
    const previewNomor = ref('')

    const periodeDitutup = ref(false)


    const muatDaftarPO = async () => {
        isLoadingDaftar.value = true
        try {
            const { data } = await api.get('akunting/purchase-order/')
            daftarPO.value = data.results || data || []
        } catch (err) {
            console.error('Gagal memuat daftar PO:', bacaError(err))
        } finally {
            isLoadingDaftar.value = false
        }
    }

    const tampil = computed(() => {
        const q = cari.value.trim().toLowerCase()
        return daftarPO.value
            .filter(po => saringStatus.value === 'semua' || po.status === saringStatus.value)
            .filter(po => !q
                || po.no_po?.toLowerCase().includes(q)
                || po.suplier_nama?.toLowerCase().includes(q))
            .sort((a, b) => new Date(b.tanggal) - new Date(a.tanggal))
    })

    const belumDiterima = computed(() =>
        daftarPO.value.filter(po => ['TERKIRIM', 'SEBAGIAN'].includes(po.status))
    )

    const draftCount = computed(() =>
        daftarPO.value.filter(po => po.status === 'DRAFT').length
    )

    const totalBulanIni = computed(() => {
        const kini = new Date()
        return daftarPO.value
            .filter(po => {
                const d = new Date(po.tanggal)
                return d.getMonth() === kini.getMonth() && d.getFullYear() === kini.getFullYear()
            })
            .reduce((s, po) => s + Number(po.total_nilai ?? 0), 0)
    })
    const muatDataMaster = async () => {
        sedangProses.value = true
        pesanError.value = ''
        try {
            const [resPortal, resSupplier, resProduk] = await Promise.all([
                api.get('auth/portal/'),
                api.get('master/suplier/', { params: { ringkas: 1, aktif: true } }),
                api.get('master/produk/', { params: { ringkas: 1, aktif: true, jenis: 'BAHAN_BAKU' } })
            ])

            listEntitas.value = resPortal.data.entitas || []
            listSupplier.value = resSupplier.data.results || resSupplier.data || []
            listProduk.value = resProduk.data.results || resProduk.data || []
            console.log("Cek Data Produk dari Backend:", listProduk.value)

        } catch (err) {
            pesanError.value = bacaError(err, 'Gagal memuat data master (Entitas/Suplier/Produk).')
        } finally {
            sedangProses.value = false
        }
    }

    const muatPreviewNomor = async (entitasId, tanggal) => {
        if (!entitasId || !tanggal) {
            previewNomor.value = 'Pilih entitas & tanggal'
            return
        }
        try {
            const { data } = await api.get('akunting/purchase-order/preview-nomor/', {
                params: { entitas: entitasId, tanggal }
            })
            previewNomor.value = data.nomor || 'TIDAK TERSEDIA'
        } catch {
            previewNomor.value = 'GAGAL MEMUAT NOMOR'
        }
    }

    const cekStatusPeriode = async (entitasId, tanggal) => {
        if (!entitasId || !tanggal) {
            periodeDitutup.value = false
            return
        }

        try {
            const { data } = await api.get('core/periode/status/', {
                params: { entitas: entitasId, tanggal }
            })
            periodeDitutup.value = !data.terbuka
            if (periodeDitutup.value) {
                pesanError.value = data.pesan || 'Periode akuntansi untuk entitas & tanggal ini sudah ditutup.'
            }
        } catch (err) {
            console.error('Gagal mengecek status periode:', err)

            periodeDitutup.value = false
        }
    }

    const cariProduk = async (query) => {
        try {
            const { data } = await api.get('master/produk/', {
                params: { ringkas: 1, aktif: true, jenis: 'BAHAN_BAKU', search: query }
            })
            return data.results || data || []
        } catch {
            return []
        }
    }
    const buatProdukBaru = async (nama) => {
        const namaProduk = nama.trim()

        if (!namaProduk) {
            throw new Error('Nama produk wajib diisi.')
        }

        if (!listSatuan.value.length) {
            const { data } = await api.get('master/satuan/', {
                params: { aktif: true }
            })
            listSatuan.value = data.results || data || []
        }

        const satuanKg =
            listSatuan.value.find(
                s => s.kode?.toLowerCase() === 'kg'
            ) || listSatuan.value[0]

        if (!satuanKg) {
            throw new Error('Belum ada data satuan pada master.')
        }

        const produkLokal = listProduk.value.find(
            p => p.nama.trim().toLowerCase() === namaProduk.toLowerCase()
        )

        if (produkLokal) {
            return produkLokal
        }
        const kode = generateKode('RM')

        try {
            const { data } = await api.post('master/produk/', {
                kode,
                nama: namaProduk,
                jenis: 'BAHAN_BAKU',
                satuan: satuanKg.id
            })

            const produkBaru = {
                id: data.id,
                kode: data.kode,
                nama: data.nama,
                satuan_kode: data.satuan_kode,
                jenis: data.jenis
            }
            listProduk.value.unshift(produkBaru)

            return produkBaru

        } catch (err) {
            throw new Error(
                bacaError(err, 'Gagal membuat produk baru.'),
                { cause: err }
            )
        }
    }

    const simpanPO = async (form, isKirim = false) => {
        if (periodeDitutup.value) {
            pesanError.value = 'Tidak dapat menyimpan PO karena periode telah ditutup.'
            return { success: false, message: pesanError.value }
        }

        sedangProses.value = true
        pesanError.value = ''
        try {
            const payloadItems = form.items
                .filter(i => i.produk_id && parseFloat(i.qty_pesan) > 0)
                .map(i => ({
                    produk_id: i.produk_id,
                    qty_pesan: String(i.qty_pesan),
                    harga_per_kg: String(i.harga_per_kg || 0),
                    satuan: i.satuan || 'kg',
                }))

            if (!payloadItems.length) {
                pesanError.value = 'Minimal harus ada 1 item dengan produk dan Qty lebih dari 0.'
                return { success: false, message: pesanError.value }
            }

            const payload = {
                entitas_id: form.entitas_id,
                suplier_id: form.suplier_id,
                tanggal: form.tanggal,
                tanggal_kirim_diminta: form.tanggal_kirim_diminta || null,
                catatan: form.catatan,
                items: payloadItems
            }

            const res = await api.post('akunting/purchase-order/', payload)
            const idPO = res.data.id

            if (isKirim && idPO) {
                await api.post(`akunting/purchase-order/${idPO}/kirim/`)
            }

            await muatDaftarPO()
            return { success: true, data: res.data }

        } catch (err) {
            pesanError.value = bacaError(err, 'Gagal menyimpan PO.')
            return { success: false, message: pesanError.value }
        } finally {
            sedangProses.value = false
        }
    }



    return {
        daftarPO, isLoadingDaftar, cari, saringStatus, tampil,
        belumDiterima, draftCount, totalBulanIni, muatDaftarPO,
        listEntitas, listSupplier, listProduk, sedangProses,
        pesanError, previewNomor, muatDataMaster, muatPreviewNomor,
        cariProduk, buatProdukBaru, simpanPO,
        periodeDitutup, cekStatusPeriode
    }
}