import { useState } from 'react'

/**
 * Conflict card — two rendering modes:
 *
 *  comparison  doc_a && doc_b present — two document values with a ≠ divider.
 *              Value states:
 *                "present"  — field extracted successfully  (neutral)
 *                "missing"  — field absent in that document (red)
 *                "mismatch" — present but value differs     (amber)
 *
 *  finding     No doc_a/doc_b — single-document rule failure.
 *              Shows the rule message; no comparison columns.
 */

const EMPTY_VALUES = new Set(['', '—', 'none', 'null', 'n/a', 'unknown'])
const isEmpty = (v) => !v || EMPTY_VALUES.has(String(v).toLowerCase().trim())

function valueState(value, isBSide) {
  if (isEmpty(value)) return 'missing'
  if (isBSide) return 'mismatch'
  return 'present'
}

const STATE_STYLES = {
  present:  { color: '#1a1a18', background: 'transparent', border: 'none' },
  missing:  { color: '#A32D2D', background: '#FCEBEB', border: '0.5px solid #F09595' },
  mismatch: { color: '#854F0B', background: '#FAEEDA', border: '0.5px solid #FAC775' },
}

const STATE_LABEL = {
  present:  null,
  missing:  'Not found in this document',
  mismatch: 'Value differs from source',
}

const stateTooltip = {
  present:  (doc)        => `Value extracted from ${doc}`,
  missing:  (doc)        => `This field is absent in the ${doc} — it must be present for this rule to pass`,
  mismatch: (docA, docB) => `The value in ${docB} does not match the one found in ${docA}`,
}

export default function RuleResult({ conflict, onEscalate }) {
  const [resolved, setResolved] = useState(conflict.resolved || false)

  const severity     = conflict.severity === 'FAIL' ? 'high' : 'medium'
  const isComparison = Boolean(conflict.doc_a && conflict.doc_b)
  const stateA = valueState(conflict.value_a, false)
  const stateB = valueState(conflict.value_b, true)

  const severityBadge =
    severity === 'high'
      ? { bg: '#FCEBEB', color: '#A32D2D', border: '#F09595', label: 'High' }
      : { bg: '#FAEEDA', color: '#854F0B', border: '#FAC775', label: 'Medium' }

  return (
    <div
      style={{
        border: '0.5px solid rgba(0,0,0,0.10)',
        borderRadius: '12px',
        marginBottom: '8px',
        overflow: 'hidden',
        background: '#ffffff',
        opacity: resolved ? 0.55 : 1,
        transition: 'border-color 0.15s, box-shadow 0.15s, opacity 0.2s',
        ...(severity === 'high' && !resolved && { borderLeft: '3px solid #A32D2D' }),
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.boxShadow = '0 4px 16px rgba(0,0,0,0.10)'
        if (severity !== 'high') e.currentTarget.style.borderColor = 'rgba(0,0,0,0.18)'
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.boxShadow = 'none'
        if (severity !== 'high') e.currentTarget.style.borderColor = 'rgba(0,0,0,0.10)'
      }}
    >
      {/* Header */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          padding: '11px 14px',
          borderBottom: '0.5px solid rgba(0,0,0,0.10)',
          background: '#f7f7f5',
        }}
      >
        <span
          style={{
            fontSize: '11px',
            fontWeight: 500,
            letterSpacing: '0.08em',
            textTransform: 'uppercase',
            color: '#5f5e5a',
            flex: 1,
          }}
        >
          {conflict.type}
        </span>

        {/* Kind badge */}
        <span
          title={
            isComparison
              ? 'Two documents contain conflicting values for the same field'
              : 'An issue was detected within a single document or the package is missing this document'
          }
          style={{
            fontSize: '11px',
            padding: '2px 7px',
            borderRadius: '20px',
            fontWeight: 500,
            background: '#f0efe9',
            color: '#888780',
            border: '0.5px solid rgba(0,0,0,0.10)',
            letterSpacing: '0.04em',
            cursor: 'default',
          }}
        >
          {isComparison ? 'Mismatch' : 'Finding'}
        </span>

        {/* Severity badge */}
        <span
          title={
            severity === 'high'
              ? 'Critical — this issue can block closing'
              : 'Needs review before closing proceeds'
          }
          style={{
            fontSize: '11px',
            padding: '2px 8px',
            borderRadius: '20px',
            fontWeight: 500,
            background: severityBadge.bg,
            color: severityBadge.color,
            border: `0.5px solid ${severityBadge.border}`,
            cursor: 'default',
          }}
        >
          {severityBadge.label}
        </span>
      </div>

      {/* Body */}
      {isComparison ? (
        <div
          style={{
            padding: '12px 14px',
            display: 'grid',
            gridTemplateColumns: '1fr auto 1fr',
            gap: '10px',
            alignItems: 'start',
          }}
        >
          <ValueColumn
            label={conflict.doc_a}
            value={conflict.value_a}
            state={stateA}
            tooltip={stateTooltip[stateA](conflict.doc_a)}
          />
          <div
            title="These two values do not match"
            style={{
              fontSize: '16px',
              color: '#888780',
              textAlign: 'center',
              paddingTop: '20px',
              cursor: 'default',
            }}
          >
            ≠
          </div>
          <ValueColumn
            label={conflict.doc_b}
            value={conflict.value_b}
            state={stateB}
            tooltip={
              stateB === 'mismatch'
                ? stateTooltip.mismatch(conflict.doc_a, conflict.doc_b)
                : stateTooltip[stateB](conflict.doc_b)
            }
          />
        </div>
      ) : (
        <div style={{ padding: '12px 14px 14px' }}>
          <p style={{ fontSize: '13px', color: '#1a1a18', lineHeight: 1.65, margin: '0 0 6px' }}>
            {conflict.message}
          </p>
          <p
            style={{
              fontSize: '12px',
              color: '#888780',
              margin: 0,
              display: 'flex',
              alignItems: 'center',
              gap: '5px',
            }}
          >
            <span
              style={{
                display: 'inline-block',
                width: '5px',
                height: '5px',
                borderRadius: '50%',
                background: severity === 'high' ? '#E24B4A' : '#F5A623',
                flexShrink: 0,
              }}
            />
            Rule finding — no cross-document comparison applies
          </p>
        </div>
      )}

      {/* Actions */}
      <div
        style={{
          display: 'flex',
          gap: '6px',
          padding: '8px 14px',
          borderTop: '0.5px solid rgba(0,0,0,0.10)',
        }}
      >
        <button
          className="cc-btn-sm"
          style={
            resolved
              ? { background: '#EAF3DE', color: '#3B6D11', borderColor: '#C0DD97' }
              : {}
          }
          onClick={() => setResolved((r) => !r)}
        >
          {resolved ? 'Done ✓' : 'Mark resolved'}
        </button>
        <button
          className="cc-btn-sm"
          style={{ color: '#A32D2D', borderColor: '#F09595' }}
          onClick={() => onEscalate?.(conflict)}
          onMouseEnter={(e) => (e.currentTarget.style.background = '#FCEBEB')}
          onMouseLeave={(e) => (e.currentTarget.style.background = 'transparent')}
        >
          Escalate
        </button>
      </div>
    </div>
  )
}

function ValueColumn({ label, value, state, tooltip }) {
  const st       = STATE_STYLES[state]
  const sublabel = STATE_LABEL[state]

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '3px' }}>
      <span
        style={{
          fontSize: '11px',
          fontWeight: 500,
          letterSpacing: '0.06em',
          textTransform: 'uppercase',
          color: '#888780',
          marginBottom: '2px',
        }}
      >
        {label}
      </span>
      <span
        title={tooltip}
        style={{
          fontFamily: 'DM Mono, monospace',
          fontSize: '13px',
          padding: st.background !== 'transparent' ? '3px 8px' : '3px 0',
          borderRadius: '4px',
          display: 'inline-block',
          cursor: 'default',
          ...st,
        }}
      >
        {isEmpty(value) ? '—' : value}
      </span>
      {sublabel && (
        <span style={{ fontSize: '11px', color: st.color, lineHeight: 1.4 }}>
          {sublabel}
        </span>
      )}
    </div>
  )
}
