import { useState } from 'react'

const CATEGORY_LABELS = {
  purchase_agreement: 'Purchase Agreement',
  title_commitment: 'Title Commitment',
  loan: 'Loan Documents',
  loan_note: 'Loan Documents',
  closing_disclosure: 'Closing Disclosure',
  hud1: 'HUD-1',
  property: 'Property Documents',
  property_docs: 'Property Documents',
  insurance: 'Insurance',
  compliance: 'Identity & Compliance',
}

const STATUS_STYLE = {
  FAIL:    { background: '#FCEBEB', color: '#A32D2D' },
  WARNING: { background: '#FAEEDA', color: '#854F0B' },
  PASS:    { background: '#EAF3DE', color: '#3B6D11' },
  INFO:    { background: '#f7f7f5', color: '#5f5e5a' },
  SKIPPED: { background: '#f7f7f5', color: '#888780' },
}

/**
 * Collapsible section of rules grouped by document category.
 * Props: { category: string, rules: RuleResult[], defaultExpanded: bool }
 */
export default function CategorySection({ category, rules = [], defaultExpanded = true }) {
  const [open, setOpen] = useState(defaultExpanded)
  const label = CATEGORY_LABELS[category] || category.replace(/_/g, ' ')
  const failCount = rules.filter((r) => r.status === 'FAIL').length
  const warnCount = rules.filter((r) => r.status === 'WARNING').length

  return (
    <div
      style={{
        border: '0.5px solid rgba(0,0,0,0.10)',
        borderRadius: '12px',
        overflow: 'hidden',
        marginBottom: '8px',
      }}
    >
      {/* Header */}
      <button
        onClick={() => setOpen((v) => !v)}
        style={{
          width: '100%',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '12px 14px',
          background: '#f7f7f5',
          borderBottom: open ? '0.5px solid rgba(0,0,0,0.10)' : 'none',
          border: 'none',
          cursor: 'pointer',
          fontFamily: 'Sora, sans-serif',
          textAlign: 'left',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ fontSize: '13px', fontWeight: 500, color: '#1a1a18' }}>{label}</span>
          {failCount > 0 && (
            <span
              style={{
                fontSize: '10px',
                fontWeight: 500,
                padding: '2px 7px',
                borderRadius: '20px',
                background: '#FCEBEB',
                color: '#A32D2D',
              }}
            >
              {failCount} fail
            </span>
          )}
          {warnCount > 0 && (
            <span
              style={{
                fontSize: '10px',
                fontWeight: 500,
                padding: '2px 7px',
                borderRadius: '20px',
                background: '#FAEEDA',
                color: '#854F0B',
              }}
            >
              {warnCount} warn
            </span>
          )}
        </div>
        <span style={{ color: '#888780', fontSize: '11px' }}>{open ? '▲' : '▼'}</span>
      </button>

      {/* Rule rows */}
      {open && (
        <div>
          {rules.map((rule, idx) => {
            const st = STATUS_STYLE[rule.status] || STATUS_STYLE.SKIPPED
            return (
              <div
                key={rule.rule_id}
                style={{
                  display: 'flex',
                  alignItems: 'flex-start',
                  gap: '12px',
                  padding: '11px 14px',
                  borderTop: idx > 0 ? '0.5px solid rgba(0,0,0,0.07)' : 'none',
                }}
              >
                <div style={{ flex: 1 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '3px' }}>
                    <span
                      style={{
                        fontFamily: 'DM Mono, monospace',
                        fontSize: '10px',
                        color: '#888780',
                      }}
                    >
                      {rule.rule_id}
                    </span>
                    <span
                      style={{
                        fontSize: '10px',
                        fontWeight: 500,
                        padding: '2px 7px',
                        borderRadius: '20px',
                        ...st,
                      }}
                    >
                      {rule.status}
                    </span>
                  </div>
                  <p style={{ fontSize: '13px', color: '#1a1a18', lineHeight: 1.4 }}>
                    {rule.description}
                  </p>
                  {rule.detail && (
                    <p style={{ fontSize: '12px', color: '#5f5e5a', marginTop: '3px', lineHeight: 1.5 }}>
                      {rule.detail}
                    </p>
                  )}
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
