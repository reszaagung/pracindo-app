// src/utils/generator.js

/**
 * Fungsi untuk generate kode acak berawalan prefix.
 * Contoh output: RM-260805-X9F2
 */
export const generateKode = (prefix) => {
    const dateStr = new Date().toISOString().slice(2, 10).replace(/-/g, '');
    const random = Math.random().toString(36).substring(2, 6).toUpperCase();

    return `${prefix}-${dateStr}-${random}`;
}