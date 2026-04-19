import { useState } from 'react'

/**
 * Conflict card — shows a mismatch between two document values.
 * Props: { conflict: ConflictCard, onEscalate: (conflict) => void }
 */
export default function RuleResult({ conflict, onEscalate }) {
  const [resolved, setResolved] = useState(conflict.resolved || false)
  const isFail = conflict.severity === 'FAIL'

  return (
    <div
      style={{
        border: '0.5px solid rgba(0,0,0,0.10)',
        borderRadius: '12px',
        marginBottom: '8px',
        overflow: 'hidden',
        background: '#ffffff',
        transition: 'border-color 0.15s',
      }}
      onMouseEnter={(e) => (e.currentTarget.style.borderColor = 'rgba(0,0,0,0.18)')}
      onMouseLeave={(e) => (e.currentTarget.style.borderColor = 'rgba(0,0,0,0.10)')}
    >
      {/* Header */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '10px',
          padding: '11px 14px',
          borderBottom: '0.5px solid rgba(0,0,0,0.10)',
          background: '#f7f7f5',
        }}
      >
        <span
          style={{
            fontSize: '10px',
            fontWeight: 500,
            letterSpacing: '0.08em',
            textTransform: 'uppercase',
            color: '#5f5e5a',
          }}
        >
          {conflict.type}
        </span>
        <span
          style={{
            fontSize: '10px',
            padding: '2px 8px',
            borderRadius: '20px',
            fontWeight: 500,
            marginLeft: 'auto',
            background: isFail ? '#FCEBEB' : '#FAEEDA',
            color: isFail ? '#A32D2D' : '#854F0B',
          }}
        >
          {isFail ? 'High' : 'Medium'}
        </span>
      </div>

      {/* Body — 3-column layout */}
      <div
        style={{
          padding: '12px 14px',
          display: 'grid',
          gridTemplateColumns: '1fr auto 1fr',
          gap: '10px',
          alignItems: 'center',
        }}
      >
        {/* Doc A — ok value */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '3px' }}>
          <span
            style={{
              fontSize: '10px',
              fontWeight: 500,
              letterSpacing: '0.06em',
              textTransform: 'uppercase',
              color: '#888780',
            }}
          >
            {conflict.doc_a || 'Document A'}
          </span>
          <span
            style={{
              fontFamily: 'DM Mono, monospace',
              fontSize: '13px',
              color: '#3B6D11',
            }}
          >
            {conflict.value_a || '—'}
          </span>
        </div>

        {/* Divider */}
        <div style={{ fontSize: '16px', color: '#888780', textAlign: 'center' }}>≠</div>

        {/* Doc B — mismatch value */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '3px' }}>
          <span
            style={{
              fontSize: '10px',
              fontWeight: 500,
              letterSpacing: '0.06em',
              textTransform: 'uppercase',
              color: '#888780',
            }}
          >
            {conflict.doc_b || 'Document B'}
          </span>
          <span
            style={{
              fontFamily: 'DM Mono, monospace',
              fontSize: '13px',
              color: '#A32D2D',
              background: '#FCEBEB',
              padding: '3px 7px',
              borderRadius: '4px',
              display: 'inline-block',
            }}
          >
            {conflict.value_b || '—'}
          </span>
        </div>
      </div>

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
