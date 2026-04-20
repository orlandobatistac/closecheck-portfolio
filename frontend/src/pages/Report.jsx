import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { getResults } from '../api/client'
import DownloadButton from '../components/DownloadButton'
import EmailDraftModal from '../components/EmailDraftModal'
import PdfViewer from '../components/PdfViewer'
import FlashReportModal from '../components/FlashReportModal'
import TaskCard from '../components/TaskCard'

// ─── (ActionPlanModal removed — replaced by FlashReportModal + TaskCard) ────

export default function Report() {
  const { jobId } = useParams()
  const [report, setReport] = useState(null)
  const [fetchError, setFetchError] = useState(null)

  // Flash Report modal — auto-opens once data loads
  const [showFlashReport, setShowFlashReport] = useState(false)

  // Controlled PDF viewer
  const [activePdfDoc, setActivePdfDoc] = useState(null)
  const [activePdfPage, setActivePdfPage] = useState(null)

  // Per-task resolved state: { [index]: bool }
  const [resolvedTasks, setResolvedTasks] = useState({})

  // Left panel tab
  const [leftTab, setLeftTab] = useState('issues')

  // Email draft modal
  const [showEmailModal, setShowEmailModal] = useState(false)
  const [emailConflict, setEmailConflict] = useState(null)

  useEffect(() => {
    if (!jobId) return
    getResults(jobId)
      .then((data) => {
        setReport(data)
        setShowFlashReport(true) // auto-open on load
      })
      .catch(() => setFetchError('Could not load report.'))
  }, [jobId])

  if (fetchError) {
    return (
      <div style={{ height: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: '#f0efe9' }}>
        <p style={{ color: '#A32D2D', fontSize: '14px' }}>{fetchError}</p>
      </div>
    )
  }

  if (!report) {
    return (
      <div style={{ height: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: '#f0efe9' }}>
        <div className="cc-spinner" />
      </div>
    )
  }

  const conflicts = report.conflicts || []
  const actionPlan = report.action_plan || []
  const docs = report.documents || []
  const results = report.results || []
  const fileBadge = docs[0]?.filename || 'Closing package'

  // ── Build merged task list (by-index pairing) ──────────────────────────────
  const taskCount = Math.max(conflicts.length, actionPlan.length)
  const tasks = Array.from({ length: taskCount }, (_, i) => ({
    conflict: conflicts[i] || null,
    actionItem: actionPlan[i] || null,
  }))

  // ── Health Score ───────────────────────────────────────────────────────────
  const passCount = results.filter((r) => r.status === 'PASS').length
  const totalRules = results.filter((r) => r.status !== 'SKIPPED').length
  const passRate = totalRules > 0 ? Math.round((passCount / totalRules) * 100) : 0
  const gaugeColor = passRate >= 70 ? '#3B6D11' : passRate >= 40 ? '#854F0B' : '#A32D2D'
  const gaugeTrack = passRate >= 70 ? '#EAF3DE' : passRate >= 40 ? '#FAEEDA' : '#FCEBEB'
  const C = 175.93
  const dashOffset = C * (1 - passRate / 100)

  // ── Triage style ───────────────────────────────────────────────────────────
  const triageStyle = () => {
    if (report.overall === 'FAIL')    return { bg: '#FCEBEB', color: '#A32D2D', border: '#F09595', label: 'Blocked' }
    if (report.overall === 'WARNING') return { bg: '#FAEEDA', color: '#854F0B', border: '#FAC775', label: 'Needs review' }
    return { bg: '#EAF3DE', color: '#3B6D11', border: '#C0DD97', label: 'Ready to close' }
  }
  const ts = triageStyle()

  // ── Handlers ───────────────────────────────────────────────────────────────
  const handleToggleResolved = (i) =>
    setResolvedTasks((prev) => ({ ...prev, [i]: !prev[i] }))

  const handleEscalate = (conflict) => {
    setEmailConflict(conflict)
    setShowEmailModal(true)
  }

  // Accept {filename, page, ruleId} from TaskCard chips/header clicks.
  // Also accepts a plain string for backward-compat with any legacy callers.
  // Normalizes "Purchase Agreement" → "purchase_agreement" to match d.document_type.
  // Falls back to results.documents_referenced when filename is absent (old jobs,
  // single-doc issues, "document not found" rules that have no doc_a).
  const handleDocClick = (target) => {
    const filename = target?.filename ?? target
    const page = target?.page ?? null
    const ruleId = target?.ruleId ?? null
    const normalize = (s) => (s || '').toLowerCase().replace(/[\s-]+/g, '_')

    const findByName = (name) =>
      name
        ? docs.find(
            (d) =>
              d.filename === name ||
              d.document_type === name ||
              normalize(d.document_type) === normalize(name)
          )
        : null

    let match = findByName(filename)

    // Fallback: resolve from results.documents_referenced using ruleId.
    // Covers old jobs where single-doc issues have no doc_a, and any case
    // where the filename / label doesn't match a known document.
    if (!match && ruleId) {
      const ruleResult = results.find((r) => r.rule_id === ruleId)
      const docTypes = ruleResult?.documents_referenced || []
      for (const docType of docTypes) {
        match = findByName(docType)
        if (match) break
      }
    }

    const resolved = match?.filename || null
    if (resolved) {
      setActivePdfDoc(resolved)
      setActivePdfPage(page)
    }
  }

  // Effective PDF doc: use activePdfDoc if set and exists, else first viewable
  const viewableDocs = docs.filter((d) => d.status !== 'missing')
  const effectivePdfDoc = activePdfDoc || viewableDocs[0]?.filename || null

  return (
    <div
      style={{
        height: '100vh',
        display: 'flex',
        flexDirection: 'column',
        background: '#f0efe9',
        overflow: 'hidden',
      }}
    >
      {/* ── Topbar ─────────────────────────────────────────── */}
      <div className="cc-topbar" style={{ flexShrink: 0 }}>
        <Link to="/" className="cc-logo" style={{ textDecoration: 'none' }}>CloseCheck</Link>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span className="cc-file-badge">{fileBadge}</span>
          <DownloadButton jobId={jobId} />
          <Link to="/" className="cc-btn-sm" style={{ textDecoration: 'none' }}>New package →</Link>
        </div>
      </div>

      {/* ── Split area ─────────────────────────────────────── */}
      <div style={{ flex: 1, display: 'flex', overflow: 'hidden' }}>

        {/* Left (40%): Control panel ──────────────────────── */}
        <div
          style={{
            flex: '0 0 40%',
            borderRight: '0.5px solid rgba(0,0,0,0.12)',
            overflow: 'hidden',
            display: 'flex',
            flexDirection: 'column',
            background: '#f7f7f5',
            boxShadow: '2px 0 8px rgba(0,0,0,0.04)',
          }}
        >
          {/* ── Sticky: Health Score + Status + View Summary ─── */}
          <div
            style={{
              position: 'sticky',
              top: 0,
              zIndex: 10,
              background: '#ffffff',
              borderBottom: '0.5px solid rgba(0,0,0,0.10)',
              padding: '14px 16px',
              display: 'flex',
              alignItems: 'center',
              gap: '14px',
              flexShrink: 0,
            }}
          >
            {/* Health gauge */}
            {totalRules > 0 && (
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '2px', flexShrink: 0 }}>
                <svg width="56" height="56" viewBox="0 0 72 72">
                  <circle cx="36" cy="36" r="28" fill="none" stroke={gaugeTrack} strokeWidth="7" />
                  <circle
                    cx="36" cy="36" r="28"
                    fill="none"
                    stroke={gaugeColor}
                    strokeWidth="7"
                    strokeLinecap="round"
                    strokeDasharray={`${C} ${C}`}
                    strokeDashoffset={dashOffset}
                    transform="rotate(-90 36 36)"
                    style={{ transition: 'stroke-dashoffset 0.6s ease' }}
                  />
                  <text
                    x="36" y="40"
                    textAnchor="middle"
                    dominantBaseline="middle"
                    style={{ fontFamily: 'Sora, sans-serif', fontSize: '13px', fontWeight: '600', fill: gaugeColor }}
                  >
                    {passRate}%
                  </text>
                </svg>
                <span style={{ fontSize: '9px', fontWeight: 500, letterSpacing: '0.08em', textTransform: 'uppercase', color: '#888780' }}>
                  Health
                </span>
              </div>
            )}

            {/* Status + issue count */}
            <div style={{ flex: 1, minWidth: 0 }}>
              <div
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '6px',
                  padding: '5px 12px',
                  borderRadius: '40px',
                  fontSize: '12px',
                  fontWeight: 500,
                  marginBottom: '5px',
                  background: ts.bg,
                  color: ts.color,
                  border: `0.5px solid ${ts.border}`,
                }}
              >
                <span style={{ width: '7px', height: '7px', borderRadius: '50%', background: 'currentColor', flexShrink: 0 }} />
                {ts.label}
              </div>
              <p style={{ fontSize: '11px', color: '#888780', margin: 0, lineHeight: 1.4 }}>
                {tasks.length} issue{tasks.length !== 1 ? 's' : ''} · {docs.length} doc{docs.length !== 1 ? 's' : ''}
              </p>
            </div>

            {/* View Summary button */}
            <button
              className="cc-btn-sm"
              onClick={() => setShowFlashReport(true)}
              style={{ flexShrink: 0 }}
            >
              View Summary
            </button>
          </div>

          {/* ── Tab bar ───────────────────────────────────── */}
          <div
            style={{
              display: 'flex',
              borderBottom: '0.5px solid rgba(0,0,0,0.10)',
              background: '#ffffff',
              flexShrink: 0,
            }}
          >
            {[{ id: 'issues', label: `Issues (${tasks.length})` }, { id: 'rules', label: `Rules (${totalRules})` }].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setLeftTab(tab.id)}
                style={{
                  flex: 1,
                  padding: '9px 0',
                  fontSize: '11px',
                  fontWeight: leftTab === tab.id ? 600 : 400,
                  color: leftTab === tab.id ? '#1a1a18' : '#888780',
                  background: 'none',
                  border: 'none',
                  borderBottom: leftTab === tab.id ? '2px solid #1a1a18' : '2px solid transparent',
                  cursor: 'pointer',
                  letterSpacing: '0.02em',
                  transition: 'color 0.15s',
                }}
              >
                {tab.label}
              </button>
            ))}
          </div>

          {/* ── Scrollable content ────────────────────────── */}
          <div style={{ flex: 1, overflowY: 'auto', padding: '12px 12px 24px' }}>
            {leftTab === 'issues' ? (
              <>
                <p
                  className="cc-section-label"
                  style={{ marginBottom: '8px', fontSize: '10px', letterSpacing: '0.08em' }}
                >
                  Issues — {tasks.filter((_, i) => !resolvedTasks[i]).length} open
                </p>

                {tasks.length === 0 ? (
                  <p style={{ fontSize: '13px', color: '#888780', textAlign: 'center', padding: '32px 0' }}>
                    No issues detected. File is clean.
                  </p>
                ) : (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                    {tasks.map((task, i) => (
                      <TaskCard
                        key={task.conflict?.rule_id || `task-${i}`}
                        conflict={task.conflict}
                        actionItem={task.actionItem}
                        resolved={!!resolvedTasks[i]}
                        onToggleResolved={() => handleToggleResolved(i)}
                        onEscalate={handleEscalate}
                        onDocClick={handleDocClick}
                      />
                    ))}
                  </div>
                )}
              </>
            ) : (
              <>
                <p
                  className="cc-section-label"
                  style={{ marginBottom: '8px', fontSize: '10px', letterSpacing: '0.08em' }}
                >
                  All rules — {passCount} passed · {results.filter((r) => r.status === 'WARNING').length} warnings · {results.filter((r) => r.status === 'FAIL').length} failed
                </p>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                  {results
                    .filter((r) => r.status !== 'SKIPPED')
                    .sort((a, b) => {
                      const order = { FAIL: 0, WARNING: 1, PASS: 2 }
                      return (order[a.status] ?? 3) - (order[b.status] ?? 3)
                    })
                    .map((r) => {
                      const statusColors = {
                        FAIL:    { color: '#A32D2D', bg: '#FCEBEB', border: 'rgba(163,45,45,0.20)' },
                        WARNING: { color: '#854F0B', bg: '#FAEEDA', border: 'rgba(133,79,11,0.20)' },
                        PASS:    { color: '#3B6D11', bg: '#EAF3DE', border: 'rgba(59,109,17,0.15)' },
                      }
                      const sc = statusColors[r.status] || statusColors.PASS
                      return (
                        <div
                          key={r.rule_id}
                          style={{
                            display: 'flex',
                            alignItems: 'flex-start',
                            gap: '10px',
                            padding: '9px 11px',
                            borderRadius: '8px',
                            border: `0.5px solid ${sc.border}`,
                            background: r.status === 'PASS' ? '#ffffff' : sc.bg,
                          }}
                        >
                          <span
                            style={{
                              flexShrink: 0,
                              marginTop: '1px',
                              width: '46px',
                              textAlign: 'center',
                              fontFamily: 'DM Mono, monospace',
                              fontSize: '9px',
                              fontWeight: 600,
                              letterSpacing: '0.06em',
                              padding: '2px 5px',
                              borderRadius: '4px',
                              background: sc.bg,
                              color: sc.color,
                              border: `0.5px solid ${sc.border}`,
                            }}
                          >
                            {r.status}
                          </span>
                          <div style={{ flex: 1, minWidth: 0 }}>
                            <p style={{ fontSize: '12px', fontWeight: 500, color: '#1a1a18', marginBottom: r.detail ? '3px' : 0, lineHeight: 1.4 }}>
                              {r.description}
                            </p>
                            {r.detail && (
                              <p style={{ fontSize: '11px', color: '#5f5e5a', lineHeight: 1.5, margin: 0 }}>
                                {r.detail}
                              </p>
                            )}
                          </div>
                          <span style={{ flexShrink: 0, fontFamily: 'DM Mono, monospace', fontSize: '9px', color: '#aaa99b', marginTop: '1px' }}>
                            {r.rule_id}
                          </span>
                        </div>
                      )
                    })}
                </div>
              </>
            )}
          </div>
        </div>

        {/* Right (60%): PDF viewer ────────────────────────── */}
        <div
          style={{
            flex: 1,
            overflow: 'hidden',
            display: 'flex',
            flexDirection: 'column',
            background: '#ffffff',
          }}
        >
          <PdfViewer
            jobId={jobId}
            documents={docs}
            selectedDoc={effectivePdfDoc}
            onSelectDoc={(filename) => {
              setActivePdfDoc(filename)
              setActivePdfPage(null)
            }}
            pageNumber={activePdfPage}
          />
        </div>
      </div>

      {/* ── Flash Report Modal ──────────────────────────────── */}
      {showFlashReport && (
        <FlashReportModal
          report={report}
          onClose={() => setShowFlashReport(false)}
        />
      )}

      {/* ── Email Draft Modal ───────────────────────────────── */}
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
