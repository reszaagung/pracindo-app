import { ref, reactive, computed, watch } from 'vue'
import { apiTangki, apiBatch, apiPratinjau, apiRawUntukProduksi } from '../api'

export function useMixingForm() {
  const loadingForm = ref(false)
  const submitting = ref(false)
  const errorMsg = ref('')
  const daftarTangki = ref([])
  const daftarRaw = ref([])
  const pratinjau = ref(null)

  const form = reactive({
    nama_hasil: '',
    tangki_tujuan: '',
    batch: '',
    tekor_kg: 0
  })

  const bomRows = ref([])

  let seqBom = 0
  function buatBarisBom() {
    seqBom += 1
    return { _id: `bom-${seqBom}`, raw: '', qty: 0, saldo: 0, harga: 0, subtotal: 0 }
  }

  async function muatTangki() {
    try {
      const res = await apiTangki.daftar()
      daftarTangki.value = res?.results ?? res ?? []
    } catch {
      errorMsg.value = 'Gagal memuat daftar tangki'
    }
  }

  async function muatRawPool() {
    try {
      const res = await apiRawUntukProduksi.daftar()
      const list = res?.rincian ?? res?.data?.rincian ?? res?.results ?? res ?? []
      daftarRaw.value = list
        .filter((item) => Number(item.qty_kg) > 0)
        .map((item) => ({ ...item, raw: item.produk_id }))
    } catch {
      errorMsg.value = 'Gagal memuat saldo bahan baku'
    }
  }

  async function bukaFormBaru() {
    form.nama_hasil = ''
    form.tangki_tujuan = ''
    form.batch = ''
    form.tekor_kg = 0
    pratinjau.value = null
    errorMsg.value = ''

    loadingForm.value = true
    await Promise.all([muatTangki(), muatRawPool()])
    bomRows.value = [buatBarisBom()]
    loadingForm.value = false
  }

  async function bukaFormEdit(batchId) {
    loadingForm.value = true
    errorMsg.value = ''
    try {
      await Promise.all([muatTangki(), muatRawPool()])
      const [detail, komposisi] = await Promise.all([
        apiBatch.detail(batchId),
        apiBatch.komposisi(batchId)
      ])

      form.nama_hasil = detail.nama_hasil || ''
      form.tangki_tujuan = detail.tangki_tujuan || detail.tangki || ''
      form.batch = detail.batch || detail.nomor_batch || ''
      form.tekor_kg = Number(detail.tekor_kg || 0)

      bomRows.value = (komposisi?.materials || komposisi?.bahan_baku || []).map((m) => {
        const row = buatBarisBom()
        row.raw = m.raw
        row.qty = Number(m.qty_kg)
        row.harga = Number(m.harga_per_kg)
        row.subtotal = row.qty * row.harga
        perbaruiTelemetriBom(row)
        return row
      })
      if (bomRows.value.length === 0) bomRows.value = [buatBarisBom()]
    } catch {
      errorMsg.value = 'Gagal memuat detail batch mixing'
    } finally {
      loadingForm.value = false
    }
  }

  async function tambahTangkiBaru(nama) {
    const namaBersih = String(nama || '').trim().toUpperCase()
    if (!namaBersih) return null
    try {
      const dibuat = await apiTangki.buat({ nama: namaBersih, kode: namaBersih })
      await muatTangki()
      return dibuat
    } catch {
      errorMsg.value = 'Gagal membuat tangki baru'
      return null
    }
  }

  async function generateNomorBatch() {
    try {
      const res = await apiBatch.nomorBaru('MIXING')
      form.batch = res?.nomor ?? res?.batch ?? ''
    } catch {
      errorMsg.value = 'Gagal membuat nomor batch otomatis'
    }
  }

  function tambahBomRow() { bomRows.value.push(buatBarisBom()) }
  function hapusBomRow(id) {
    if (bomRows.value.length <= 1) return
    bomRows.value = bomRows.value.filter((r) => r._id !== id)
  }

  function perbaruiTelemetriBom(row) {
    const item = daftarRaw.value.find((r) => r.raw === row.raw)
    row.saldo = item ? Number(item.qty_kg) : 0
    row.harga = item ? Number(item.harga_rata) : 0
    row.subtotal = (Number(row.qty) || 0) * row.harga
  }

  const totalQtyBom = computed(() => bomRows.value.reduce((s, r) => s + (Number(r.qty) || 0), 0))
  const totalNilaiBom = computed(() => bomRows.value.reduce((s, r) => s + (Number(r.qty) || 0) * (Number(r.harga) || 0), 0))
  const proyeksiYield = computed(() => totalQtyBom.value - (Number(form.tekor_kg) || 0))
  const proyeksiHargaRata = computed(() => proyeksiYield.value > 0 ? totalNilaiBom.value / proyeksiYield.value : 0)

  function susunPayload() {
    return {
      jenis: 'MIXING',
      nama_hasil: form.nama_hasil.trim(),
      tangki_tujuan: Number(form.tangki_tujuan),
      batch: form.batch.trim(),
      tekor_kg: Number(form.tekor_kg) || 0,
      materials: bomRows.value
        .filter((r) => r.raw && Number(r.qty) > 0)
        .map((r) => ({ raw: String(r.raw), qty_kg: Number(r.qty) })),
      wip_sources: []
    }
  }

  function validasiForm() {
    if (!form.nama_hasil.trim()) return 'Nama hasil produksi wajib diisi'
    if (!form.tangki_tujuan) return 'Tangki tujuan wajib dipilih'
    if (!form.batch.trim()) return 'Batch ID wajib diisi'

    const adaBom = bomRows.value.some((r) => r.raw && Number(r.qty) > 0)
    if (!adaBom) return 'Minimal satu baris bahan baku (BOM) harus diisi'

    for (const row of bomRows.value) {
      if (row.raw && Number(row.qty) > row.saldo + 0.001) {
        return `Saldo pool tidak cukup. Diminta ${row.qty} Kg, tersedia ${row.saldo.toFixed(3)} Kg`
      }
    }
    if (proyeksiYield.value <= 0) return 'Yield harus positif setelah dikurangi tekor'
    return ''
  }

  async function mintaPratinjau() {
    errorMsg.value = validasiForm()
    if (errorMsg.value) return null
    try {
      const res = await apiPratinjau(susunPayload())
      pratinjau.value = res
      return res
    } catch (e) {
      errorMsg.value = e?.response?.data?.pesan || 'Gagal kalkulasi pratinjau.'
      return null
    }
  }

  // FUNGSI SIMPAN DRAFT DIHAPUS

  async function simpanDanPosting(batchId = null) {
    errorMsg.value = validasiForm()
    if (errorMsg.value) return false
    submitting.value = true
    try {
      const payload = susunPayload()
      let targetId = batchId
      if (targetId) {
        await apiBatch.ubah(targetId, payload)
      } else {
        const res = await apiBatch.buat(payload)
        targetId = res?.id ?? res?.data?.id ?? res
      }
      // Langsung tembak endpoint posting
      await apiBatch.posting(targetId)
      return true
    } catch (e) {
      const data = e?.response?.data
      errorMsg.value = data?.detail || data?.pesan || 'Gagal memposting batch produksi'
      return false
    } finally {
      submitting.value = false
    }
  }

  watch(
    bomRows,
    (rows) => rows.forEach((r) => (r.subtotal = (Number(r.qty) || 0) * (Number(r.harga) || 0))),
    { deep: true }
  )

  return {
    loadingForm,
    submitting,
    errorMsg,
    daftarTangki,
    daftarRaw,
    form,
    bomRows,
    pratinjau,
    proyeksiYield,
    proyeksiHargaRata,
    bukaFormBaru,
    bukaFormEdit,
    tambahTangkiBaru,
    generateNomorBatch,
    tambahBomRow,
    hapusBomRow,
    perbaruiTelemetriBom,
    mintaPratinjau,
    simpanDanPosting
  }
}
