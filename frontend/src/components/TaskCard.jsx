import { useState } from 'react'

/**
 * TaskCard — Unified accordion card that merges a ConflictCard with its
 * paired ActionItem into a single "Issue" entry.
 *
 * Props:
 *   conflict      ConflictCard | null
 *   actionItem    ActionItem | null
 *   resolved      bool
 *   onToggleResolved  (void) => void
 *   onEscalate    (conflict) => void
 *   onDocClick    ({filename: string|null, page: number|null}) => void
 */
export default function TaskCard({ conflict, actionItem, resolved, onToggleResolved, onEscalate, onDocClick }) {
  const [expanded, setExpanded] = useState(false)

  // ── Derive display values ──────────────────────────────────────────────────
  const title = conflict?.type || actionItem?.title || 'Unknown issue'
  const body = conflict?.message || actionItem?.description || ''
  const urgency = actionItem?.urgency || (conflict?.severity === 'FAIL' ? 'now' : 'today')
  const isHighSeverity = conflict?.severity === 'FAIL' || actionItem?.is_blocker

  // ── Color helpers ──────────────────────────────────────────────────────────
  const priorityTag = () => {
    if (urgency === 'now' || actionItem?.is_blocker)
      return { bg: '#FCEBEB', color: '#A32D2D', label: 'Do now' }
    if (urgency === 'today')
      return { bg: '#FAEEDA', color: '#854F0B', label: 'Today' }
    return { bg: '#f7f7f5', color: '#5f5e5a', label: 'Soon' }
  }
  const tag = priorityTag()

  const handleHeaderClick = () => {
    setExpanded((prev) => !prev)
    if (!expanded && onDocClick) {
      // Use resolved filename when available (new jobs); fall back to doc_a
      // label (e.g. "Purchase Agreement") for old jobs that predate filename_a.
      onDocClick({
        filename: conflict?.filename_a || conflict?.doc_a || null,
        page: conflict?.page_a || null,
        ruleId: conflict?.rule_id || null,
      })
    }
  }

  return (
    <div
      style={{
        border: isHighSeverity && !resolved
          ? '0.5px solid #F09595'
          : '0.5px solid rgba(0,0,0,0.10)',
        borderLeft: isHighSeverity && !resolved ? '3px solid #A32D2D' : undefined,
        borderRadius: '10px',
        background: '#ffffff',
        overflow: 'hidden',
        opacity: resolved ? 0.5 : 1,
        transition: 'opacity 0.2s, box-shadow 0.15s',
      }}
      onMouseEnter={(e) => {
        if (!resolved) e.currentTarget.style.boxShadow = '0 4px 16px rgba(0,0,0,0.08)'
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.boxShadow = 'none'
      }}
    >
      {/* ── Header (always visible) ── */}
      <button
        onClick={handleHeaderClick}
        style={{
          width: '100%',
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          padding: '11px 14px',
          background: 'none',
          border: 'none',
          cursor: 'pointer',
          textAlign: 'left',
        }}
      >
        {/* Expand chevron */}
        <span
          style={{
            fontSize: '10px',
            color: '#888780',
            flexShrink: 0,
            transition: 'transform 0.18s',
            transform: expanded ? 'rotate(90deg)' : 'rotate(0deg)',
            display: 'inline-block',
          }}
        >
          ›
        </span>

        {/* Title */}
        <span
          style={{
            fontSize: '13px',
            fontWeight: 500,
            color: '#1a1a18',
            flex: 1,
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            whiteSpace: 'nowrap',
            fontFamily: 'Sora, sans-serif',
          }}
        >
          {title}
        </span>

        {/* Priority tag */}
        <span
          style={{
            fontSize: '10px',
            fontWeight: 500,
            padding: '2px 8px',
            borderRadius: '20px',
            flexShrink: 0,
            background: tag.bg,
            color: tag.color,
          }}
        >
          {tag.label}
        </span>
      </button>

      {/* ── Body (always visible) ── */}
      {body && (
        <div
          style={{
            padding: '0 14px 11px 33px',
            fontSize: '13px',
            color: '#5f5e5a',
            lineHeight: 1.6,
          }}
        >
          {body}

          {/* doc reference chips */}
          {(conflict?.doc_a || conflict?.doc_b) && (
            <div style={{ display: 'flex', gap: '6px', marginTop: '6px', flexWrap: 'wrap' }}>
              {conflict.doc_a && (() => {
                const label = conflict.doc_a +
                  (conflict.value_a ? `: ${conflict.value_a}` : '') +
                  (conflict.page_a ? ` · pg ${conflict.page_a}` : '')
                const chipStyle = {
                  fontSize: '10px',
                  fontFamily: 'DM Mono, monospace',
                  background: '#f7f7f5',
                  color: '#5f5e5a',
                  padding: '2px 8px',
                  borderRadius: '4px',
                  border: '0.5px solid rgba(0,0,0,0.10)',
                }
                return conflict.filename_a ? (
                  <button
                    onClick={(e) => {
                      e.stopPropagation()
                      onDocClick && onDocClick({ filename: conflict.filename_a, page: conflict.page_a || null })
                    }}
                    title={`Open ${conflict.filename_a} in viewer`}
                    style={{ ...chipStyle, cursor: 'pointer', background: 'none', textDecoration: 'underline dotted' }}
                  >
                    {label}
                  </button>
                ) : (
                  <span style={chipStyle}>{label}</span>
                )
              })()}
              {conflict.doc_b && (() => {
                const label = conflict.doc_b +
                  (conflict.value_b ? `: ${conflict.value_b}` : '') +
                  (conflict.page_b ? ` · pg ${conflict.page_b}` : '')
                const chipStyle = {
                  fontSize: '10px',
                  fontFamily: 'DM Mono, monospace',
                  background: '#FAEEDA',
                  color: '#854F0B',
                  padding: '2px 8px',
                  borderRadius: '4px',
                  border: '0.5px solid #FAC775',
                }
                return conflict.filename_b ? (
                  <button
                    onClick={(e) => {
                      e.stopPropagation()
                      onDocClick && onDocClick({ filename: conflict.filename_b, page: conflict.page_b || null })
                    }}
                    title={`Open ${conflict.filename_b} in viewer`}
                    style={{ ...chipStyle, cursor: 'pointer', background: 'none', textDecoration: 'underline dotted' }}
                  >
                    {label}
                  </button>
                ) : (
                  <span style={chipStyle}>{label}</span>
                )
              })()}
            </div>
          )}
        </div>
      )}

      {/* ── Expanded: Recommended Action footer ── */}
      {expanded && (
        <div
          style={{
            borderTop: '0.5px solid rgba(0,0,0,0.08)',
            background: '#f9f9f7',
            padding: '12px 14px',
          }}
        >
          <p
            style={{
              fontSize: '9px',
              fontWeight: 500,
              letterSpacing: '0.1em',
              textTransform: 'uppercase',
              color: '#888780',
              marginBottom: '6px',
            }}
          >
            Recommended Action
          </p>

          {actionItem ? (
            <>
              <p
                style={{
                  fontSize: '13px',
                  color: '#1a1a18',
                  lineHeight: 1.6,
                  marginBottom: '10px',
                }}
              >
                {actionItem.description}
              </p>

              {/* Owner + action buttons */}
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  flexWrap: 'wrap',
                }}
              >
                <span
                  style={{
                    fontSize: '10px',
                    background: '#f7f7f5',
                    color: '#5f5e5a',
                    padding: '2px 8px',
                    borderRadius: '20px',
                    border: '0.5px solid rgba(0,0,0,0.10)',
                  }}
                >
                  {actionItem.owner}
                </span>

                <div style={{ marginLeft: 'auto', display: 'flex', gap: '6px' }}>
                  {conflict && (
                    <button
                      onClick={(e) => {
                        e.stopPropagation()
                        onEscalate && onEscalate(conflict)
                      }}
                      style={{
                        fontSize: '11px',
                        fontWeight: 500,
                        padding: '4px 12px',
                        borderRadius: '20px',
                        border: '0.5px solid rgba(0,0,0,0.18)',
                        background: 'transparent',
                        color: '#5f5e5a',
                        cursor: 'pointer',
                        fontFamily: 'Sora, sans-serif',
                      }}
                    >
                      Escalate
                    </button>
                  )}
                  <button
                    onClick={(e) => {
                      e.stopPropagation()
                      onToggleResolved && onToggleResolved()
                    }}
                    style={{
                      fontSize: '11px',
                      fontWeight: 500,
                      padding: '4px 12px',
                      borderRadius: '20px',
                      border: resolved ? '0.5px solid #C0DD97' : '0.5px solid rgba(0,0,0,0.18)',
                      background: resolved ? '#EAF3DE' : 'transparent',
                      color: resolved ? '#3B6D11' : '#5f5e5a',
                      cursor: 'pointer',
                      fontFamily: 'Sora, sans-serif',
                      transition: 'background 0.12s, color 0.12s',
                    }}
                  >
                    {resolved ? 'Resolved ✓' : 'Mark Resolved'}
                  </button>
                </div>
              </div>
            </>
          ) : (
            <p style={{ fontSize: '13px', color: '#888780' }}>No action item paired with this conflict.</p>
          )}
        </div>
      )}
    </div>
  )
}
