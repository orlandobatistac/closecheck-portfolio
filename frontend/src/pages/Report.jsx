import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { getResults } from '../api/client'
import SummaryBanner from '../components/SummaryBanner'
import RuleResult from '../components/RuleResult'
import CategorySection from '../components/CategorySection'
import ProgressBar from '../components/ProgressBar'
import DownloadButton from '../components/DownloadButton'
import EmailDraftModal from '../components/EmailDraftModal'

// ─── Action Plan Modal (inline per spec) ────────────────────────────────────

function ActionPlanModal({ report, completedSteps, onToggleStep, onDraftEmail, onClose }) {
  const conflicts = report.conflicts || []
  const actionPlan = report.action_plan || []
  const docs = report.documents || []
  const openConflicts = conflicts.filter((c) => !c.resolved).length
  const missingDocs = docs.filter((d) => d.status === 'missing').length
  const blockers = actionPlan.filter((item) => item.is_blocker)
  const completedCount = Object.values(completedSteps).filter(Boolean).length
  const total = actionPlan.length
  const fileId = docs[0]?.filename?.replace(/\.[^.]+$/, '') || `Job_${report.job_id?.slice(0, 8)}`

  const triageStyle = () => {
    if (report.overall === 'FAIL') return { bg: '#FCEBEB', color: '#A32D2D', border: '#F09595', label: 'Blocked' }
    if (report.overall === 'WARNING') return { bg: '#FAEEDA', color: '#854F0B', border: '#FAC775', label: 'Needs review' }
    return { bg: '#EAF3DE', color: '#3B6D11', border: '#C0DD97', label: 'Ready to close' }
  }
  const ts = triageStyle()

  const stepNumStyle = (urgency) => {
    if (urgency === 'now') return { background: '#FCEBEB', color: '#A32D2D' }
    if (urgency === 'today') return { background: '#FAEEDA', color: '#854F0B' }
    return { background: '#f7f7f5', color: '#5f5e5a' }
  }

  const urgencyTag = (urgency) => {
    if (urgency === 'now') return { bg: '#FCEBEB', color: '#A32D2D', label: 'Do now' }
    if (urgency === 'today') return { bg: '#FAEEDA', color: '#854F0B', label: 'Today' }
    return { bg: '#f7f7f5', color: '#5f5e5a', label: 'After steps 1–3' }
  }

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        background: 'rgba(0,0,0,0.35)',
        zIndex: 100,
        display: 'flex',
        alignItems: 'flex-start',
        justifyContent: 'center',
        overflowY: 'auto',
        padding: '32px 16px',
      }}
      onClick={(e) => { if (e.target === e.currentTarget) onClose() }}
    >
      <div
        style={{
          width: '100%',
          maxWidth: '680px',
          background: '#ffffff',
          border: '0.5px solid rgba(0,0,0,0.10)',
          borderRadius: '12px',
          overflow: 'hidden',
          boxShadow: '0 2px 24px rgba(0,0,0,0.07)',
          padding: '24px',
          position: 'relative',
        }}
      >
        {/* Close */}
        <button
          onClick={onClose}
          style={{
            position: 'absolute',
            top: '14px',
            right: '14px',
            background: 'none',
            border: 'none',
            cursor: 'pointer',
            color: '#888780',
            fontSize: '16px',
          }}
        >
          ✕
        </button>

        {/* File row */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            marginBottom: '24px',
          }}
        >
          <span
            style={{ fontFamily: 'DM Mono, monospace', fontSize: '12px', color: '#888780' }}
          >
            {fileId} — Action Plan
          </span>
          <span
            style={{
              fontSize: '11px',
              fontWeight: 500,
              padding: '4px 12px',
              borderRadius: '20px',
              background: ts.bg,
              color: ts.color,
              border: `0.5px solid ${ts.border}`,
            }}
          >
            {ts.label}
          </span>
        </div>

        {/* Metric cards */}
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(120px, 1fr))',
            gap: '10px',
            marginBottom: '28px',
          }}
        >
          {[
            { label: 'Conflicts', value: `${openConflicts} open`, danger: openConflicts > 0 },
            { label: 'Missing docs', value: String(missingDocs), danger: missingDocs > 0 },
            { label: 'Est. resolution', value: '2–4 hrs', danger: false },
            { label: 'Action items', value: String(total), danger: false },
          ].map((card) => (
            <div
              key={card.label}
              style={{ background: '#f7f7f5', borderRadius: '8px', padding: '12px' }}
            >
              <p
                style={{
                  fontSize: '10px',
                  fontWeight: 500,
                  letterSpacing: '0.08em',
                  textTransform: 'uppercase',
                  color: '#888780',
                  marginBottom: '4px',
                }}
              >
                {card.label}
              </p>
              <p
                style={{
                  fontSize: '14px',
                  fontWeight: 500,
                  color: card.danger ? '#A32D2D' : '#1a1a18',
                }}
              >
                {card.value}
              </p>
            </div>
          ))}
        </div>

        {/* Blocker box */}
        {blockers.length > 0 && (
          <div
            style={{
              border: '0.5px solid #F09595',
              borderRadius: '12px',
              background: '#FCEBEB',
              padding: '14px',
              marginBottom: '28px',
            }}
          >
            <p
              style={{
                fontSize: '10px',
                fontWeight: 500,
                letterSpacing: '0.08em',
                textTransform: 'uppercase',
                color: '#A32D2D',
                marginBottom: '8px',
              }}
            >
              Blockers — file cannot close until resolved
            </p>
            {blockers.map((b, i) => (
              <p
                key={i}
                style={{
                  fontSize: '12px',
                  color: '#791F1F',
                  lineHeight: 1.6,
                  paddingLeft: '12px',
                  position: 'relative',
                  marginBottom: i < blockers.length - 1 ? '4px' : 0,
                }}
              >
                <span
                  style={{
                    position: 'absolute',
                    left: 0,
                    top: '7px',
                    width: '4px',
                    height: '4px',
                    borderRadius: '50%',
                    background: '#E24B4A',
                  }}
                />
                {b.description}
              </p>
            ))}
          </div>
        )}

        {/* Section label */}
        <p
          style={{
            fontSize: '10px',
            fontWeight: 500,
            letterSpacing: '0.1em',
            textTransform: 'uppercase',
            color: '#888780',
            marginBottom: '12px',
          }}
        >
          Action steps — in order of priority
        </p>

        {/* Action list */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', marginBottom: '28px' }}>
          {actionPlan.length === 0 ? (
            <p style={{ fontSize: '13px', color: '#888780', textAlign: 'center', padding: '20px 0' }}>
              No action items generated.
            </p>
          ) : (
            actionPlan.map((item, i) => {
              const numSt = stepNumStyle(item.urgency)
              const urgTag = urgencyTag(item.urgency)
              const done = completedSteps[i]
              return (
                <div
                  key={i}
                  style={{
                    border: '0.5px solid rgba(0,0,0,0.10)',
                    borderRadius: '12px',
                    background: '#ffffff',
                    overflow: 'hidden',
                    transition: 'border-color 0.12s',
                  }}
                  onMouseEnter={(e) => (e.currentTarget.style.borderColor = 'rgba(0,0,0,0.18)')}
                  onMouseLeave={(e) => (e.currentTarget.style.borderColor = 'rgba(0,0,0,0.10)')}
                >
                  {/* Item header */}
                  <div
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '12px',
                      padding: '12px 14px',
                    }}
                  >
                    <span
                      style={{
                        width: '22px',
                        height: '22px',
                        borderRadius: '50%',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        fontSize: '11px',
                        fontWeight: 500,
                        flexShrink: 0,
                        ...numSt,
                      }}
                    >
                      {i + 1}
                    </span>
                    <span
                      style={{
                        fontSize: '13px',
                        fontWeight: 500,
                        color: '#1a1a18',
                        flex: 1,
                      }}
                    >
                      {item.title}
                    </span>
                    <span
                      style={{
                        fontSize: '10px',
                        fontWeight: 500,
                        padding: '2px 8px',
                        borderRadius: '20px',
                        flexShrink: 0,
                        background: urgTag.bg,
                        color: urgTag.color,
                      }}
                    >
                      {urgTag.label}
                    </span>
                  </div>

                  {/* Item body */}
                  <div
                    style={{
                      padding: '10px 14px 13px 48px',
                      borderTop: '0.5px solid rgba(0,0,0,0.10)',
                      fontSize: '12px',
                      color: '#5f5e5a',
                      lineHeight: 1.6,
                    }}
                  >
                    {item.description}
                    <div
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '6px',
                        marginTop: '8px',
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
                        {item.owner}
                      </span>
                      <button
                        onClick={() => onToggleStep(i)}
                        style={{
                          fontSize: '11px',
                          fontWeight: 500,
                          padding: '4px 12px',
                          borderRadius: '20px',
                          border: done
                            ? '0.5px solid #C0DD97'
                            : '0.5px solid rgba(0,0,0,0.18)',
                          background: done ? '#EAF3DE' : 'transparent',
                          color: done ? '#3B6D11' : '#5f5e5a',
                          cursor: 'pointer',
                          marginLeft: 'auto',
                          fontFamily: 'Sora, sans-serif',
                          transition: 'background 0.12s, color 0.12s',
                        }}
                      >
                        {done ? 'Done ✓' : 'Mark done'}
                      </button>
                    </div>
                  </div>
                </div>
              )
            })
          )}
        </div>

        {/* Bottom row */}
        <div
          style={{
            display: 'flex',
            gap: '16px',
            alignItems: 'center',
            justifyContent: 'space-between',
            paddingTop: '8px',
            borderTop: '0.5px solid rgba(0,0,0,0.10)',
          }}
        >
          <div style={{ flex: 1 }}>
            <p style={{ fontSize: '11px', color: '#888780', marginBottom: '6px' }}>
              {completedCount} of {total} steps completed
            </p>
            <div
              style={{
                height: '4px',
                background: '#f7f7f5',
                borderRadius: '4px',
                overflow: 'hidden',
              }}
            >
              <div
                style={{
                  height: '4px',
                  background: '#639922',
                  borderRadius: '4px',
                  width: total > 0 ? `${Math.round((completedCount / total) * 100)}%` : '0%',
                  transition: 'width 0.4s ease',
                }}
              />
            </div>
          </div>
          <button
            className="cc-btn-primary"
            onClick={() => onDraftEmail(conflicts[0])}
          >
            Draft lender email →
          </button>
        </div>
      </div>
    </div>
  )
}

// ─── Report Page ─────────────────────────────────────────────────────────────

export default function Report() {
  const { jobId } = useParams()
  const [report, setReport] = useState(null)
  const [fetchError, setFetchError] = useState(null)
  const [activeTab, setActiveTab] = useState('result')
  const [showActionPlan, setShowActionPlan] = useState(false)
  const [showEmailModal, setShowEmailModal] = useState(false)
  const [emailConflict, setEmailConflict] = useState(null)
  const [completedSteps, setCompletedSteps] = useState({})

  useEffect(() => {
    if (!jobId) return
    getResults(jobId)
      .then(setReport)
      .catch(() => setFetchError('Could not load report.'))
  }, [jobId])

  if (fetchError) {
    return (
      <div
        style={{
          minHeight: '100vh',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          background: '#f0efe9',
        }}
      >
        <p style={{ color: '#A32D2D', fontSize: '14px' }}>{fetchError}</p>
      </div>
    )
  }

  if (!report) {
    return (
      <div
        style={{
          minHeight: '100vh',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          background: '#f0efe9',
        }}
      >
        <div className="cc-spinner" />
      </div>
    )
  }

  // Group results by category, FAIL first within each group
  const resultsByCategory = {}
  for (const r of (report.results || [])) {
    if (!resultsByCategory[r.category]) resultsByCategory[r.category] = []
    resultsByCategory[r.category].push(r)
  }
  for (const cat of Object.keys(resultsByCategory)) {
    resultsByCategory[cat].sort((a, b) => {
      const order = { FAIL: 0, WARNING: 1, INFO: 2, PASS: 3, SKIPPED: 4 }
      return (order[a.status] ?? 5) - (order[b.status] ?? 5)
    })
  }

  const conflicts = report.conflicts || []
  const docs = report.documents || []
  const fileBadge = docs[0]?.filename || 'Closing package'
  const categories = Object.keys(resultsByCategory)

  const handleToggleStep = (i) => {
    setCompletedSteps((prev) => ({ ...prev, [i]: !prev[i] }))
  }

  const handleEscalate = (conflict) => {
    setEmailConflict(conflict)
    setShowEmailModal(true)
  }

  const handleDraftEmail = (conflict) => {
    setEmailConflict(conflict || conflicts[0])
    setShowActionPlan(false)
    setShowEmailModal(true)
  }

  const TABS = [
    { id: 'result', label: 'Result' },
    { id: 'documents', label: 'Documents' },
    { id: 'rules', label: 'Rules' },
  ]

  return (
    <div
      style={{
        minHeight: '100vh',
        background: '#f0efe9',
        display: 'flex',
        alignItems: 'flex-start',
        justifyContent: 'center',
        padding: '32px 16px',
      }}
    >
      {/* Main card */}
      <div className="cc-card" style={{ width: '100%', maxWidth: '720px' }}>

        {/* Topbar */}
        <div className="cc-topbar">
          <span className="cc-logo">CloseCheck</span>
          <span className="cc-file-badge">{fileBadge}</span>
        </div>

        {/* Tabs */}
        <div
          style={{
            display: 'flex',
            padding: '0 24px',
            borderBottom: '0.5px solid rgba(0,0,0,0.10)',
          }}
        >
          {TABS.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              style={{
                fontSize: '12px',
                fontWeight: 500,
                padding: '10px 0',
                marginRight: '20px',
                color: activeTab === tab.id ? '#1a1a18' : '#888780',
                background: 'none',
                border: 'none',
                borderBottom: activeTab === tab.id
                  ? '2px solid #1a1a18'
                  : '2px solid transparent',
                cursor: 'pointer',
                fontFamily: 'Sora, sans-serif',
                transition: 'all 0.15s',
              }}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* ── RESULT TAB ── */}
        {activeTab === 'result' && (
          <>
            <SummaryBanner overall={report.overall} executiveBrief={report.executive_brief} />

            <p
              className="cc-section-label"
              style={{ padding: '20px 24px 10px' }}
            >
              Conflicts detected — {conflicts.length} of {docs.length} docs
            </p>

            <div style={{ padding: '0 24px 24px' }}>
              {conflicts.length === 0 ? (
                <p style={{ fontSize: '13px', color: '#888780', textAlign: 'center', padding: '16px 0' }}>
                  No conflicts detected.
                </p>
              ) : (
                conflicts.map((c) => (
                  <RuleResult key={c.rule_id} conflict={c} onEscalate={handleEscalate} />
                ))
              )}
            </div>

            {/* Bottom bar */}
            <div
              style={{
                borderTop: '0.5px solid rgba(0,0,0,0.10)',
                padding: '14px 24px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                gap: '16px',
              }}
            >
              <span style={{ fontSize: '12px', color: '#5f5e5a' }}>
                <strong style={{ color: '#1a1a18', fontWeight: 500 }}>Suggested:</strong>{' '}
                contact lender to confirm closing figures
              </span>
              <button className="cc-btn-primary" onClick={() => setShowActionPlan(true)}>
                Generate action plan →
              </button>
            </div>
          </>
        )}

        {/* ── DOCUMENTS TAB ── */}
        {activeTab === 'documents' && (
          <>
            <p
              className="cc-section-label"
              style={{ padding: '20px 24px 10px' }}
            >
              Documents processed — {docs.length} files
            </p>
            <ProgressBar documents={docs} />
          </>
        )}

        {/* ── RULES TAB ── */}
        {activeTab === 'rules' && (
          <div style={{ padding: '24px' }}>
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                marginBottom: '16px',
              }}
            >
              <p className="cc-section-label">All rules</p>
              <DownloadButton jobId={jobId} />
            </div>
            {categories.length === 0 ? (
              <p style={{ fontSize: '13px', color: '#888780', textAlign: 'center', padding: '32px 0' }}>
                No rules ran yet.
              </p>
            ) : (
              categories.map((cat) => (
                <CategorySection
                  key={cat}
                  category={cat}
                  rules={resultsByCategory[cat]}
                  defaultExpanded={resultsByCategory[cat].some((r) => r.status === 'FAIL')}
                />
              ))
            )}
          </div>
        )}
      </div>

      {/* Action Plan Modal */}
      {showActionPlan && (
        <ActionPlanModal
          report={report}
          completedSteps={completedSteps}
          onToggleStep={handleToggleStep}
          onDraftEmail={handleDraftEmail}
          onClose={() => setShowActionPlan(false)}
        />
      )}

      {/* Email Draft Modal */}
      {showEmailModal && emailConflict && (
        <EmailDraftModal
          isOpen={showEmailModal}
          onClose={() => setShowEmailModal(false)}
          jobId={jobId}
          conflict={emailConflict}
          closingDate={
            report.results?.find((r) => r.rule_id === 'PA-004')?.detail || '—'
          }
        />
      )}
    </div>
  )
}
