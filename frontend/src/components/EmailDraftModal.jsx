import { useState, useEffect, useRef } from 'react'
import { draftEmail } from '../api/client'

/**
 * Email draft modal — pixel-faithful to email_draft_modal.html.
 * Props: {
 *   isOpen: bool,
 *   onClose: () => void,
 *   jobId: string,
 *   conflict: ConflictCard,
 *   closingDate: string,
 * }
 */
export default function EmailDraftModal({ isOpen, onClose, jobId, conflict, closingDate }) {
  const [activeVariant, setActiveVariant] = useState('pro')
  const [draft, setDraft] = useState(null)
  const [loading, setLoading] = useState(false)
  const [copied, setCopied] = useState(false)
  const [charCount, setCharCount] = useState({ pro: 0, urg: 0 })
  const proBodyRef = useRef(null)
  const urgBodyRef = useRef(null)

  useEffect(() => {
    if (!isOpen || !conflict) return
    setLoading(true)
    setDraft(null)
    setActiveVariant('pro')
    draftEmail(jobId, conflict.rule_id, 'lender')
      .then((data) => {
        setDraft(data)
        setLoading(false)
        setCharCount({
          pro: (data.body_pro || '').length,
          urg: (data.body_urg || '').length,
        })
      })
      .catch(() => {
        setDraft({ subject_pro: '', body_pro: '', subject_urg: '', body_urg: '' })
        setLoading(false)
      })
  }, [isOpen, conflict, jobId])

  if (!isOpen) return null

  const fileLabel =
    (conflict?.doc_a || '').replace(/\.[^.]+$/, '') || `Job_${jobId?.slice(0, 8)}`

  const discrepancy = (() => {
    const a = parseFloat((conflict?.value_a || '').replace(/[$,]/g, ''))
    const b = parseFloat((conflict?.value_b || '').replace(/[$,]/g, ''))
    if (!isNaN(a) && !isNaN(b)) return `$${Math.abs(a - b).toLocaleString()}`
    return conflict?.message || '—'
  })()

  const currentSubject = activeVariant === 'pro' ? draft?.subject_pro : draft?.subject_urg
  const currentBody = activeVariant === 'pro' ? draft?.body_pro : draft?.body_urg

  const updateCount = (variant, value) => {
    setCharCount((prev) => ({ ...prev, [variant]: value.length }))
  }

  const copyEmail = () => {
    const text = `Subject: ${currentSubject}\n\n${currentBody}`
    if (navigator.clipboard) {
      navigator.clipboard.writeText(text).catch(() => {})
    } else {
      const ta = document.createElement('textarea')
      ta.value = text
      document.body.appendChild(ta)
      ta.select()
      document.execCommand('copy')
      document.body.removeChild(ta)
    }
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const openMail = () => {
    const subj = encodeURIComponent(currentSubject || '')
    const body = encodeURIComponent(currentBody || '')
    window.location.href = `mailto:?subject=${subj}&body=${body}`
  }

  return (
    /* Overlay */
    <div
      style={{
        position: 'fixed',
        inset: 0,
        background: 'rgba(0,0,0,0.35)',
        zIndex: 200,
        display: 'flex',
        alignItems: 'flex-start',
        justifyContent: 'center',
        overflowY: 'auto',
        padding: '32px 16px',
      }}
      onClick={(e) => { if (e.target === e.currentTarget) onClose() }}
    >
      {/* Modal */}
      <div
        style={{
          width: '100%',
          maxWidth: '720px',
          background: '#ffffff',
          border: '0.5px solid rgba(0,0,0,0.10)',
          borderRadius: '12px',
          overflow: 'hidden',
          boxShadow: '0 2px 24px rgba(0,0,0,0.07)',
        }}
      >
        {/* Topbar */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '14px 24px',
            borderBottom: '0.5px solid rgba(0,0,0,0.10)',
          }}
        >
          <span
            style={{
              fontSize: '13px',
              fontWeight: 500,
              letterSpacing: '0.08em',
              textTransform: 'uppercase',
              color: '#5f5e5a',
            }}
          >
            CloseCheck
          </span>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            {/* Conflict pill */}
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                fontSize: '11px',
                fontWeight: 500,
                padding: '4px 12px',
                borderRadius: '20px',
                background: '#FCEBEB',
                color: '#A32D2D',
                border: '0.5px solid #F09595',
              }}
            >
              <span
                style={{
                  width: '6px',
                  height: '6px',
                  borderRadius: '50%',
                  background: 'currentColor',
                  flexShrink: 0,
                }}
              />
              {conflict?.type || 'Conflict'} — {conflict?.rule_id}
            </div>
            {/* Close button */}
            <button
              onClick={onClose}
              style={{
                background: 'none',
                border: 'none',
                cursor: 'pointer',
                color: '#888780',
                fontSize: '16px',
                lineHeight: 1,
                padding: '2px 4px',
              }}
            >
              ✕
            </button>
          </div>
        </div>

        {/* Context bar */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '12px',
            padding: '14px 24px',
            borderBottom: '0.5px solid rgba(0,0,0,0.10)',
            background: '#f7f7f5',
            flexWrap: 'wrap',
          }}
        >
          {[
            { label: 'File', value: fileLabel, danger: false },
            { label: 'Recipient', value: 'Lender — closing dept.', danger: false },
            { label: 'Discrepancy', value: discrepancy, danger: true },
            { label: 'Closing date', value: closingDate || '—', danger: false },
          ].map((item, i, arr) => (
            <div key={item.label} style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
                <span
                  style={{
                    fontSize: '10px',
                    fontWeight: 500,
                    letterSpacing: '0.08em',
                    textTransform: 'uppercase',
                    color: '#888780',
                  }}
                >
                  {item.label}
                </span>
                <span
                  style={{
                    fontFamily: 'DM Mono, monospace',
                    fontSize: '12px',
                    color: item.danger ? '#A32D2D' : '#1a1a18',
                  }}
                >
                  {item.value}
                </span>
              </div>
              {i < arr.length - 1 && (
                <div
                  style={{
                    width: '0.5px',
                    height: '28px',
                    background: 'rgba(0,0,0,0.10)',
                    flexShrink: 0,
                  }}
                />
              )}
            </div>
          ))}
        </div>

        {/* Variant tabs */}
        <div style={{ display: 'flex', gap: '8px', padding: '16px 24px 0' }}>
          {[
            { id: 'pro', label: 'Professional & direct', urgent: false },
            { id: 'urg', label: 'Urgent — closing at risk', urgent: true },
          ].map((tab) => {
            const isActive = activeVariant === tab.id
            const activeStyle = tab.urgent && isActive
              ? { background: '#FCEBEB', color: '#A32D2D', borderColor: '#F09595' }
              : isActive
              ? { background: '#ffffff', color: '#1a1a18', borderColor: 'rgba(0,0,0,0.18)' }
              : { background: '#f7f7f5', color: '#5f5e5a', borderColor: 'rgba(0,0,0,0.10)' }

            return (
              <button
                key={tab.id}
                onClick={() => setActiveVariant(tab.id)}
                style={{
                  fontSize: '12px',
                  fontWeight: 500,
                  padding: '8px 16px',
                  borderRadius: '8px',
                  border: '0.5px solid',
                  cursor: 'pointer',
                  fontFamily: 'Sora, sans-serif',
                  transition: 'all 0.12s',
                  ...activeStyle,
                }}
              >
                {tab.label}
              </button>
            )
          })}
        </div>

        {/* Email pane */}
        <div style={{ padding: '16px 24px 0' }}>
          {loading ? (
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                padding: '60px 0',
              }}
            >
              <div
                style={{
                  width: '32px',
                  height: '32px',
                  borderRadius: '50%',
                  border: '1.5px solid rgba(0,0,0,0.10)',
                  borderTopColor: '#1a1a18',
                  animation: 'spin 1s linear infinite',
                }}
              />
            </div>
          ) : (
            <>
              {/* Professional pane */}
              <div style={{ display: activeVariant === 'pro' ? 'block' : 'none' }}>
                <div style={{ margin: '14px 0 10px' }}>
                  <span
                    style={{
                      display: 'inline-flex',
                      alignItems: 'center',
                      fontSize: '10px',
                      fontWeight: 500,
                      padding: '3px 10px',
                      borderRadius: '20px',
                      background: '#f7f7f5',
                      color: '#5f5e5a',
                      border: '0.5px solid rgba(0,0,0,0.10)',
                    }}
                  >
                    Normal lender relationship · gives space to respond
                  </span>
                </div>
                <div
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '10px',
                    marginBottom: '10px',
                  }}
                >
                  <span
                    style={{
                      fontSize: '10px',
                      fontWeight: 500,
                      letterSpacing: '0.08em',
                      textTransform: 'uppercase',
                      color: '#888780',
                      whiteSpace: 'nowrap',
                    }}
                  >
                    Subject
                  </span>
                  <span
                    style={{
                      fontFamily: 'DM Mono, monospace',
                      fontSize: '12px',
                      color: '#1a1a18',
                      flex: 1,
                      background: '#f7f7f5',
                      padding: '6px 10px',
                      borderRadius: '8px',
                      border: '0.5px solid rgba(0,0,0,0.10)',
                    }}
                  >
                    {draft?.subject_pro || ''}
                  </span>
                </div>
                <textarea
                  ref={proBodyRef}
                  defaultValue={draft?.body_pro || ''}
                  onInput={(e) => updateCount('pro', e.target.value)}
                  style={{
                    width: '100%',
                    minHeight: '240px',
                    fontFamily: 'DM Mono, monospace',
                    fontSize: '12px',
                    lineHeight: 1.7,
                    color: '#1a1a18',
                    background: '#f7f7f5',
                    border: '0.5px solid rgba(0,0,0,0.10)',
                    borderRadius: '12px',
                    padding: '14px',
                    resize: 'vertical',
                    outline: 'none',
                    transition: 'border-color 0.12s',
                  }}
                  onFocus={(e) => (e.target.style.borderColor = 'rgba(0,0,0,0.30)')}
                  onBlur={(e) => (e.target.style.borderColor = 'rgba(0,0,0,0.10)')}
                />
                <p
                  style={{
                    fontFamily: 'DM Mono, monospace',
                    fontSize: '10px',
                    color: '#888780',
                    textAlign: 'right',
                    marginTop: '4px',
                  }}
                >
                  {charCount.pro} chars
                </p>
              </div>

              {/* Urgent pane */}
              <div style={{ display: activeVariant === 'urg' ? 'block' : 'none' }}>
                <div style={{ margin: '14px 0 10px' }}>
                  <span
                    style={{
                      display: 'inline-flex',
                      alignItems: 'center',
                      fontSize: '10px',
                      fontWeight: 500,
                      padding: '3px 10px',
                      borderRadius: '20px',
                      background: '#FCEBEB',
                      color: '#A32D2D',
                      border: '0.5px solid #F09595',
                    }}
                  >
                    Hard deadline · documents closing risk
                  </span>
                </div>
                <div
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '10px',
                    marginBottom: '10px',
                  }}
                >
                  <span
                    style={{
                      fontSize: '10px',
                      fontWeight: 500,
                      letterSpacing: '0.08em',
                      textTransform: 'uppercase',
                      color: '#888780',
                      whiteSpace: 'nowrap',
                    }}
                  >
                    Subject
                  </span>
                  <span
                    style={{
                      fontFamily: 'DM Mono, monospace',
                      fontSize: '12px',
                      color: '#A32D2D',
                      flex: 1,
                      background: '#FCEBEB',
                      padding: '6px 10px',
                      borderRadius: '8px',
                      border: '0.5px solid #F09595',
                    }}
                  >
                    {draft?.subject_urg || ''}
                  </span>
                </div>
                <textarea
                  ref={urgBodyRef}
                  defaultValue={draft?.body_urg || ''}
                  onInput={(e) => updateCount('urg', e.target.value)}
                  style={{
                    width: '100%',
                    minHeight: '240px',
                    fontFamily: 'DM Mono, monospace',
                    fontSize: '12px',
                    lineHeight: 1.7,
                    color: '#1a1a18',
                    background: '#f7f7f5',
                    border: '0.5px solid rgba(0,0,0,0.10)',
                    borderRadius: '12px',
                    padding: '14px',
                    resize: 'vertical',
                    outline: 'none',
                    transition: 'border-color 0.12s',
                  }}
                  onFocus={(e) => (e.target.style.borderColor = 'rgba(0,0,0,0.30)')}
                  onBlur={(e) => (e.target.style.borderColor = 'rgba(0,0,0,0.10)')}
                />
                <p
                  style={{
                    fontFamily: 'DM Mono, monospace',
                    fontSize: '10px',
                    color: '#888780',
                    textAlign: 'right',
                    marginTop: '4px',
                  }}
                >
                  {charCount.urg} chars
                </p>
              </div>
            </>
          )}
        </div>

        {/* Bottom actions */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '14px 24px',
            borderTop: '0.5px solid rgba(0,0,0,0.10)',
            marginTop: '14px',
            gap: '16px',
            flexWrap: 'wrap',
          }}
        >
          {/* Note */}
          <span
            style={{
              fontSize: '11px',
              color: '#888780',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
            }}
          >
            <span
              style={{
                width: '5px',
                height: '5px',
                borderRadius: '50%',
                background: '#EF9F27',
                flexShrink: 0,
              }}
            />
            Both paths documented — corrected CD or written confirmation
          </span>

          {/* Buttons */}
          <div style={{ display: 'flex', gap: '8px' }}>
            <button
              onClick={copyEmail}
              style={{
                fontSize: '12px',
                fontWeight: 500,
                padding: '8px 16px',
                borderRadius: '20px',
                border: copied
                  ? '0.5px solid #C0DD97'
                  : '0.5px solid rgba(0,0,0,0.18)',
                background: copied ? '#EAF3DE' : 'transparent',
                color: copied ? '#3B6D11' : '#5f5e5a',
                cursor: 'pointer',
                fontFamily: 'Sora, sans-serif',
                transition: 'all 0.12s',
              }}
            >
              {copied ? 'Copied ✓' : 'Copy email'}
            </button>
            <button
              onClick={openMail}
              style={{
                fontSize: '12px',
                fontWeight: 500,
                padding: '8px 18px',
                borderRadius: '20px',
                border: 'none',
                background: activeVariant === 'urg' ? '#A32D2D' : '#1a1a18',
                color: '#ffffff',
                cursor: 'pointer',
                fontFamily: 'Sora, sans-serif',
                transition: 'opacity 0.12s',
              }}
              onMouseEnter={(e) => (e.currentTarget.style.opacity = '0.85')}
              onMouseLeave={(e) => (e.currentTarget.style.opacity = '1')}
            >
              Open in Mail →
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
