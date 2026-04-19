/**
 * Display formatting helpers.
 */

export function formatCurrency(val) {
  if (val == null) return '—'
  const num = typeof val === 'string' ? parseFloat(val.replace(/[$,]/g, '')) : Number(val)
  if (isNaN(num)) return String(val)
  return '$' + num.toLocaleString('en-US', { minimumFractionDigits: 0, maximumFractionDigits: 0 })
}

export function formatDate(str) {
  if (!str) return '—'
  const d = new Date(str)
  if (isNaN(d.getTime())) return str
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
}

export function truncateFilename(name, maxLen = 20) {
  if (!name || name.length <= maxLen) return name
  const ext = name.includes('.') ? '.' + name.split('.').pop() : ''
  const base = name.slice(0, maxLen - ext.length - 1)
  return base + '…' + ext
}
