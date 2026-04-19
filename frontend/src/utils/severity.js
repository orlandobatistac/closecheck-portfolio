/**
 * Severity color helpers — exact hex values from the design reference.
 */

export function severityColor(s) {
  if (s === 'FAIL') return '#A32D2D'
  if (s === 'WARNING') return '#854F0B'
  if (s === 'PASS') return '#3B6D11'
  return '#5f5e5a'
}

export function severityBg(s) {
  if (s === 'FAIL') return '#FCEBEB'
  if (s === 'WARNING') return '#FAEEDA'
  if (s === 'PASS') return '#EAF3DE'
  return '#f7f7f5'
}

export function severityBorder(s) {
  if (s === 'FAIL') return '#F09595'
  if (s === 'WARNING') return '#FAC775'
  if (s === 'PASS') return '#C0DD97'
  return 'rgba(0,0,0,0.10)'
}

export function triageLabel(overall) {
  if (overall === 'FAIL') return 'Blocked'
  if (overall === 'WARNING') return 'Needs review'
  return 'Ready to close'
}
