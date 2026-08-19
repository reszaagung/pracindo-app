export const JENIS_BATCH = {
    MIXING: 'MIXING',
    BLENDING: 'BLENDING'
}

export const STATUS_BATCH = {
    DRAFT: 'DRAFT',
    POSTED: 'POSTED',
    VOID: 'VOID'
}

export const SUMBER = {
    RAW: 'RAW',
    WIP: 'WIP'
}

export const WARNA_STATUS = {
    [STATUS_BATCH.DRAFT]: 'bg-gray-200 text-gray-800',
    [STATUS_BATCH.POSTED]: 'bg-blue-100 text-blue-800',
    [STATUS_BATCH.VOID]: 'bg-red-100 text-red-800'
}
