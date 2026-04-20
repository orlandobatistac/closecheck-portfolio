/**
 * FlashReportModal — "The Flash Report"
 *
 * Auto-fires when analysis completes. Shows the executive brief, critical
 * blockers, and a single CTA ("Start Resolution") that closes the modal
 * and reveals the full Review Workspace.
 *
 * Props:
 *   report     — JobResultResponse object
 *   onClose    — () => void  called when user clicks "Start Resolution" or the backdrop
 */
export default function FlashReportModal({ report, onClose }) {
  const executiveBrief = report.executive_brief || []
  const actionPlan = report.action_plan || []
  const blockers = actionPlan.filter((item) => item.is_blocker)

  const triageStyle = () => {
    if (report.overall === 'FAIL')
      return { bg: '#FCEBEB', color: '#A32D2D', border: '#F09595', label: 'Blocked' }
    if (report.overall === 'WARNING')
      return { bg: '#FAEEDA', color: '#854F0B', border: '#FAC775', label: 'Needs review' }
    return { bg: '#EAF3DE', color: '#3B6D11', border: '#C0DD97', label: 'Ready to close' }
  }
  const ts = triageStyle()

  const hasDollarOrPercent = (text) => /\$[\d,]+|\d+%/.test(text)

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        background: 'rgba(0,0,0,0.40)',
        zIndex: 200,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '24px 16px',
      }}
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose()
      }}
    >
      <div
        style={{
          width: '100%',
          maxWidth: '560px',
          background: '#ffffff',
          borderRadius: '14px',
          overflow: 'hidden',
          boxShadow: '0 8px 40px rgba(0,0,0,0.12)',
          border: '0.5px solid rgba(0,0,0,0.10)',
        }}
      >
        {/* ── Header ── */}
        <div
          style={{
            padding: '20px 24px 16px',
            borderBottom: '0.5px solid rgba(0,0,0,0.10)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
          }}
        >
          <div>
            <p
              style={{
                fontSize: '9px',
                fontWeight: 500,
                letterSpacing: '0.12em',
                textTransform: 'uppercase',
                color: '#888780',
                marginBottom: '4px',
              }}
            >
              Analysis complete
            </p>
            <h2
              style={{
                fontSize: '16px',
                fontWeight: 600,
                color: '#1a1a18',
                margin: 0,
                fontFamily: 'Sora, sans-serif',
              }}
            >
              Executive Briefing
            </h2>
          </div>
          <span
            style={{
              fontSize: '11px',
              fontWeight: 500,
              padding: '5px 14px',
              borderRadius: '20px',
              background: ts.bg,
              color: ts.color,
              border: `0.5px solid ${ts.border}`,
              flexShrink: 0,
            }}
          >
            {ts.label}
          </span>
        </div>

        {/* ── Body ── */}
        <div style={{ padding: '20px 24px' }}>
          {/* Blockers */}
          {blockers.length > 0 && (
            <div
              style={{
                border: '0.5px solid #F09595',
                borderRadius: '10px',
                background: '#FCEBEB',
                padding: '14px 16px',
                marginBottom: '18px',
              }}
            >
              <p
                style={{
                  fontSize: '9px',
                  fontWeight: 500,
                  letterSpacing: '0.1em',
                  textTransform: 'uppercase',
                  color: '#A32D2D',
                  marginBottom: '8px',
                }}
              >
                Blockers — file cannot close until resolved
              </p>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '5px' }}>
                {blockers.map((b, i) => (
                  <p
                    key={i}
                    style={{
                      fontSize: '13px',
                      color: '#791F1F',
                      lineHeight: 1.55,
                      paddingLeft: '14px',
                      position: 'relative',
                      margin: 0,
                    }}
                  >
                    <span
                      style={{
                        position: 'absolute',
                        left: 0,
                        top: '7px',
                        width: '5px',
                        height: '5px',
                        borderRadius: '50%',
                        background: '#E24B4A',
                      }}
                    />
                    {b.title}
                  </p>
                ))}
              </div>
            </div>
          )}

          {/* Executive brief bullets */}
          {executiveBrief.length > 0 && (
            <div style={{ marginBottom: '6px' }}>
              <p
                style={{
                  fontSize: '9px',
                  fontWeight: 500,
                  letterSpacing: '0.1em',
                  textTransform: 'uppercase',
                  color: '#888780',
                  marginBottom: '10px',
                }}
              >
                Summary
              </p>
              <ul style={{ listStyle: 'none', display: 'flex', flexDirection: 'column', gap: '6px', margin: 0, padding: 0 }}>
                {executiveBrief.map((line, i) => {
                  const flagged = hasDollarOrPercent(line)
                  return (
                    <li
                      key={i}
                      style={{
                        fontSize: '13px',
                        lineHeight: 1.6,
                        color: flagged ? '#854F0B' : '#5f5e5a',
                        paddingLeft: '14px',
                        position: 'relative',
                      }}
                    >
                      <span
                        style={{
                          position: 'absolute',
                          left: 0,
                          top: '8px',
                          width: '4px',
                          height: '4px',
                          borderRadius: '50%',
                          background: flagged ? '#EF9F27' : '#888780',
                        }}
                      />
                      {line}
                    </li>
                  )
                })}
              </ul>
            </div>
          )}

          {executiveBrief.length === 0 && blockers.length === 0 && (
            <p style={{ fontSize: '13px', color: '#888780', textAlign: 'center', padding: '12px 0' }}>
              Analysis complete. No critical issues found.
            </p>
          )}
        </div>

        {/* ── Footer / CTA ── */}
        <div
          style={{
            padding: '16px 24px 20px',
            borderTop: '0.5px solid rgba(0,0,0,0.10)',
            display: 'flex',
            justifyContent: 'flex-end',
          }}
        >
          <button
            className="cc-btn-primary"
            onClick={onClose}
            style={{ fontSize: '14px', padding: '9px 24px' }}
          >
            Start Resolution →
          </button>
        </div>
      </div>
    </div>
  )
}
