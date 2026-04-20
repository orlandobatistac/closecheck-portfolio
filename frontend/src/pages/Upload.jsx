import { useState, useRef, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { submitValidation, getResults, submitDemo } from '../api/client'

// ── Constants ────────────────────────────────────────────────────────────────
const ALLOWED_EXTENSIONS = new Set([
  'pdf', 'docx', 'zip', 'jpg', 'jpeg', 'png', 'gif', 'tiff', 'tif', 'webp',
  'bmp', 'html', 'htm', 'xlsx', 'xls', 'csv', 'tsv', 'txt', 'json',
])

const SCAN_STEPS = [
  'Ingesting documents…',
  'Running OCR…',
  'Extracting key fields…',
  'Cross-referencing documents…',
  'Generating executive brief…',
]

const getExt = (name) => name.split('.').pop().toLowerCase()

// ── Shared style tokens ───────────────────────────────────────────────────────
const eyebrow = {
  fontSize: '10px',
  fontWeight: 500,
  letterSpacing: '0.12em',
  textTransform: 'uppercase',
  color: '#888780',
  display: 'block',
  marginBottom: '20px',
}
const sectionTitle = {
  fontSize: 'clamp(22px, 3vw, 32px)',
  fontWeight: 300,
  letterSpacing: '-0.02em',
  color: '#1a1a18',
  lineHeight: 1.15,
  marginBottom: '12px',
}
const bodyText = {
  fontSize: '14px',
  color: '#5f5e5a',
  lineHeight: 1.72,
}

// ── StickyNav ─────────────────────────────────────────────────────────────────
function StickyNav() {
  return (
    <nav className="cc-nav">
      <span className="cc-logo">CloseCheck</span>
      <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
        <a href="#demo" className="cc-btn-sm" style={{ textDecoration: 'none' }}>
          Live demo ↓
        </a>
        <a
          href="https://github.com/orlandobatistac"
          target="_blank"
          rel="noopener noreferrer"
          className="cc-btn-sm"
          style={{ textDecoration: 'none' }}
        >
          GitHub →
        </a>
      </div>
    </nav>
  )
}

// ── Hero ──────────────────────────────────────────────────────────────────────
function HeroSection() {
  return (
    <section style={{ background: '#fff', borderBottom: '0.5px solid rgba(0,0,0,0.07)' }}>
      <div className="cc-section" style={{ paddingTop: '100px', paddingBottom: '100px', textAlign: 'center' }}>
        <span className="cc-hero-badge">Portfolio project · Real estate AI</span>
        <h1
          style={{
            fontSize: 'clamp(28px, 4.5vw, 54px)',
            fontWeight: 300,
            lineHeight: 1.08,
            letterSpacing: '-0.028em',
            color: '#1a1a18',
            maxWidth: '700px',
            margin: '0 auto 24px',
          }}
        >
          An AI that reviews closing files
          <br />in 60 seconds
        </h1>
        <p
          style={{
            fontSize: '15px',
            color: '#5f5e5a',
            maxWidth: '520px',
            margin: '0 auto 36px',
            lineHeight: 1.7,
          }}
        >
          Built solo in 10 days using FastAPI, Claude API, React, and a rules
          engine with{' '}
          <strong style={{ color: '#1a1a18', fontWeight: 500 }}>
            42 domain-specific validations
          </strong>
          .
        </p>
        <div style={{ display: 'flex', gap: '10px', justifyContent: 'center', flexWrap: 'wrap' }}>
          <a href="#problem" className="cc-btn-sm" style={{ textDecoration: 'none' }}>
            See how it works ↓
          </a>
          <a
            href="https://github.com/orlandobatistac"
            target="_blank"
            rel="noopener noreferrer"
            className="cc-btn-sm"
            style={{ textDecoration: 'none' }}
          >
            View on GitHub →
          </a>
        </div>
      </div>
    </section>
  )
}

// ── Problem ───────────────────────────────────────────────────────────────────
function ProblemSection() {
  return (
    <section
      id="problem"
      style={{ background: '#f7f7f5', borderBottom: '0.5px solid rgba(0,0,0,0.07)' }}
    >
      <div className="cc-section" style={{ maxWidth: '680px' }}>
        <span style={{ ...eyebrow }}>The problem</span>
        <p style={{ ...bodyText, marginBottom: '20px' }}>
          Closing coordinators spend{' '}
          <strong style={{ color: '#1a1a18', fontWeight: 500 }}>
            3–4 hours manually reviewing each transaction package
          </strong>
          . They check 6–12 documents for name consistency, price matches, missing
          signatures, expired title commitments, and insurance coverage — a process
          that relies entirely on human attention and institutional knowledge.
        </p>
        <p style={{ ...bodyText, marginBottom: '28px' }}>
          CloseCheck replaces that review with a 60-second AI audit. It classifies each
          document, extracts key fields, runs 42 rule-based checks, and generates a
          prioritized action plan — before any human touches the file.
        </p>
        <blockquote
          style={{
            fontSize: '13px',
            color: '#888780',
            fontStyle: 'italic',
            borderLeft: '2px solid rgba(0,0,0,0.10)',
            paddingLeft: '16px',
            margin: 0,
            lineHeight: 1.7,
          }}
        >
          “At a $5–6 per-file price point, gross margin stays above 98% even at
          low volume. The AI cost per validation is approximately $0.08.”
        </blockquote>
      </div>
    </section>
  )
}

// ── Architecture ──────────────────────────────────────────────────────────────
function ArchitectureSection() {
  const nodes = [
    { label: 'File Upload', sub: 'PDF · DOCX · ZIP · images' },
    { label: 'OCR + Parse', sub: 'PyMuPDF · pdfplumber' },
    { label: 'Classifier', sub: 'Haiku → Sonnet' },
    { label: 'Field Extractor', sub: 'ALTA-aware · head+tail' },
    { label: '42 Rules', sub: 'Deterministic engine' },
    { label: 'Report Builder', sub: 'Brief + Action Plan' },
    { label: 'React Dashboard', sub: 'Conflicts · Email draft' },
  ]

  const decisions = [
    {
      badge: 'LLM',
      badgeColor: '#3B6D11',
      badgeBg: '#EAF3DE',
      title: 'Why Claude API',
      body: 'Grounded extraction with JSON output. Claude returns structured fields — not prose — so downstream rule checks are deterministic. No fine-tuning required.',
    },
    {
      badge: 'HYBRID',
      badgeColor: '#3B6D11',
      badgeBg: '#EAF3DE',
      title: 'Why hybrid validation',
      body: 'Deterministic rules catch ~70% of issues before the API is called. Claude handles only semantic ambiguity: name normalization, narrative clauses, natural language summaries.',
    },
    {
      badge: 'ARCH',
      badgeColor: '#3B6D11',
      badgeBg: '#EAF3DE',
      title: 'Why per-file architecture',
      body: 'Each job is a stateless UUID tracked in SQLite. Files saved to disk (S3-ready). Background tasks via FastAPI — no job queue dependency for the MVP.',
    },
    {
      badge: 'API',
      badgeColor: '#3B6D11',
      badgeBg: '#EAF3DE',
      title: 'Why FastAPI',
      body: 'Async background tasks for processing, auto-generated OpenAPI docs, Pydantic schemas for every response shape. Built for extension — the same endpoints power Docker or Lambda.',
    },
  ]

  return (
    <section style={{ background: '#fff', borderBottom: '0.5px solid rgba(0,0,0,0.07)' }}>
      <div className="cc-section">
        <span style={{ ...eyebrow }}>Architecture</span>
        <h2 style={{ ...sectionTitle }}>From upload to report in one pipeline</h2>
        <p style={{ ...bodyText, marginBottom: '40px', maxWidth: '560px' }}>
          Seven stages, each independently testable. Deterministic work runs first —
          the API is called only when genuine intelligence is needed.
        </p>

        {/* Pipeline diagram */}
        <div style={{ overflowX: 'auto', marginBottom: '52px', paddingBottom: '4px' }}>
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              minWidth: 'max-content',
              padding: '4px 2px',
            }}
          >
            {nodes.map((node, i) => (
              <div key={node.label} style={{ display: 'flex', alignItems: 'center' }}>
                <div
                  style={{
                    background: '#f7f7f5',
                    border: '0.5px solid rgba(0,0,0,0.12)',
                    borderRadius: '8px',
                    padding: '12px 18px',
                    textAlign: 'center',
                    minWidth: '126px',
                  }}
                >
                  <div
                    style={{
                      fontFamily: 'DM Mono, monospace',
                      fontSize: '11px',
                      fontWeight: 500,
                      color: '#1a1a18',
                      marginBottom: '4px',
                      whiteSpace: 'nowrap',
                    }}
                  >
                    {node.label}
                  </div>
                  <div
                    style={{
                      fontFamily: 'DM Mono, monospace',
                      fontSize: '9px',
                      color: '#888780',
                      whiteSpace: 'nowrap',
                    }}
                  >
                    {node.sub}
                  </div>
                </div>
                {i < nodes.length - 1 && (
                  <div style={{ padding: '0 8px', color: '#aaa99b', fontSize: '14px' }}>
                    →
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Decision cards */}
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
            gap: '16px',
          }}
        >
          {decisions.map(({ badge, badgeColor, badgeBg, title, body }) => (
            <div key={title} className="cc-capability-card">
              <span
                style={{
                  fontFamily: 'DM Mono, monospace',
                  fontSize: '9px',
                  fontWeight: 500,
                  padding: '2px 7px',
                  borderRadius: '4px',
                  background: badgeBg,
                  color: badgeColor,
                  display: 'inline-block',
                  marginBottom: '12px',
                  letterSpacing: '0.06em',
                }}
              >
                {badge}
              </span>
              <p
                style={{ fontSize: '13px', fontWeight: 500, color: '#1a1a18', marginBottom: '8px' }}
              >
                {title}
              </p>
              <p style={{ fontSize: '12px', color: '#5f5e5a', lineHeight: 1.65 }}>{body}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}

// ── Cost Architecture ─────────────────────────────────────────────────────────
function CostArchitectureSection() {
  const metrics = [
    {
      num: '~$0.08',
      label: 'Cost per closing package',
      note: '7 documents · full validation · executive brief included',
    },
    {
      num: '≥80%',
      label: 'Docs classified by Haiku alone',
      note: 'Sonnet only called when confidence < 0.85',
    },
    {
      num: '3×',
      label: 'Total LLM calls per job',
      note: 'Classify · extract fields · generate brief',
    },
    {
      num: '~70%',
      label: 'Rules run without any LLM',
      note: '42 deterministic rules — fast, cheap, auditable',
    },
  ]

  const decisionCards = [
    {
      title: 'Cascade classifier',
      body: 'Haiku runs first at 1/10th the cost of Sonnet. Only documents with confidence below 0.85 escalate to the full model — typically ambiguous or non-standard formats.',
    },
    {
      title: 'Head + Tail sampling',
      body: 'Instead of truncating at the start (losing signatures and totals at the end), the extractor takes the first 20K and last 20K characters. Critical fields hide in closing paragraphs.',
    },
    {
      title: 'Section-aware extraction',
      body: 'Title commitments follow ALTA structure: Schedule A, B-I, B-II. A regex parser extracts each section independently — reducing prompt size from ~40K to ~8K chars for this document type.',
    },
    {
      title: 'Deterministic rules first',
      body: 'Purchase price match, name consistency, address validation — all structural checks run as pure Python before any API call. Claude is reserved for semantic understanding and brief generation.',
    },
  ]

  const steps = [
    { label: 'PDF / DOCX upload', free: true },
    { label: 'OCR + Parse', free: true },
    { label: 'Smart Sampler — Head + Tail 40K chars', free: true },
    { label: 'Haiku Classifier', free: false, cost: '~$0.001 / call', llm: true },
    { isBranch: true },
    { label: 'Field Extractor — section-aware for ALTA', free: true },
    { label: '42 Deterministic Rules', free: true },
    { label: 'Claude: Executive Brief + Action Plan', free: false, cost: '~$0.04 / job', llm: true },
    { label: 'Report Builder', free: true },
  ]

  return (
    <section
      style={{ background: '#f7f7f5', borderBottom: '0.5px solid rgba(0,0,0,0.07)' }}
    >
      <div className="cc-section">
        <span style={{ ...eyebrow, color: '#3B6D11' }}>Engineering decision</span>
        <h2 style={{ ...sectionTitle }}>Token cost without quality loss</h2>
        <p style={{ ...bodyText, marginBottom: '48px', maxWidth: '520px' }}>
          Most validation runs without touching the API. When it does, the cheapest
          model goes first.
        </p>

        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'minmax(0,1fr) minmax(0,1fr)',
            gap: '32px',
            marginBottom: '40px',
            alignItems: 'start',
          }}
        >
          {/* Pipeline flow */}
          <div
            style={{
              background: '#fff',
              border: '0.5px solid rgba(0,0,0,0.10)',
              borderRadius: '12px',
              padding: '24px 28px',
            }}
          >
            <p
              style={{
                fontFamily: 'DM Mono, monospace',
                fontSize: '10px',
                color: '#888780',
                marginBottom: '20px',
                letterSpacing: '0.08em',
              }}
            >
              PIPELINE COST MAP
            </p>
            {steps.map((step, i) => {
              if (step.isBranch) {
                return (
                  <div
                    key="branch"
                    style={{
                      marginLeft: '16px',
                      borderLeft: '1.5px solid rgba(0,0,0,0.10)',
                      paddingLeft: '20px',
                      marginBottom: '4px',
                      display: 'flex',
                      flexDirection: 'column',
                      gap: '8px',
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <span
                        style={{
                          fontFamily: 'DM Mono, monospace',
                          fontSize: '9px',
                          color: '#3B6D11',
                          background: '#EAF3DE',
                          padding: '2px 6px',
                          borderRadius: '4px',
                          flexShrink: 0,
                        }}
                      >
                        ≥ 0.85
                      </span>
                      <span style={{ fontSize: '12px', color: '#5f5e5a' }}>Accept result</span>
                      <span
                        style={{
                          fontFamily: 'DM Mono, monospace',
                          fontSize: '9px',
                          color: '#888780',
                          marginLeft: 'auto',
                        }}
                      >
                        ≥80% of docs
                      </span>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <span
                        style={{
                          fontFamily: 'DM Mono, monospace',
                          fontSize: '9px',
                          color: '#854F0B',
                          background: '#FAEEDA',
                          padding: '2px 6px',
                          borderRadius: '4px',
                          flexShrink: 0,
                        }}
                      >
                        {'< 0.85'}
                      </span>
                      <span style={{ fontSize: '12px', color: '#5f5e5a' }}>Sonnet fallback</span>
                      <span
                        style={{
                          fontFamily: 'DM Mono, monospace',
                          fontSize: '9px',
                          color: '#854F0B',
                          marginLeft: 'auto',
                        }}
                      >
                        ~$0.003
                      </span>
                    </div>
                  </div>
                )
              }
              return (
                <div key={step.label}>
                  {i > 0 && (
                    <div
                      style={{
                        width: '1.5px',
                        height: '14px',
                        background: 'rgba(0,0,0,0.09)',
                        marginLeft: '12px',
                      }}
                    />
                  )}
                  <div
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '10px',
                      padding: '7px 10px',
                      borderRadius: '6px',
                      background: step.llm ? 'rgba(250,238,218,0.5)' : 'transparent',
                    }}
                  >
                    <div
                      style={{
                        width: '7px',
                        height: '7px',
                        borderRadius: '50%',
                        background: step.llm ? '#854F0B' : '#C0DD97',
                        flexShrink: 0,
                      }}
                    />
                    <span
                      style={{
                        fontSize: '12px',
                        color: '#1a1a18',
                        fontFamily: step.llm ? 'DM Mono, monospace' : 'Sora, sans-serif',
                        flex: 1,
                      }}
                    >
                      {step.label}
                    </span>
                    <span
                      style={{
                        fontFamily: 'DM Mono, monospace',
                        fontSize: '9px',
                        color: step.free ? '#3B6D11' : '#854F0B',
                        background: step.free ? '#EAF3DE' : '#FAEEDA',
                        padding: '2px 7px',
                        borderRadius: '4px',
                        flexShrink: 0,
                        whiteSpace: 'nowrap',
                      }}
                    >
                      {step.free ? 'free' : step.cost}
                    </span>
                  </div>
                </div>
              )
            })}
          </div>

          {/* Decision cards */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {decisionCards.map(({ title, body }) => (
              <div
                key={title}
                style={{
                  background: '#fff',
                  border: '0.5px solid rgba(0,0,0,0.10)',
                  borderRadius: '10px',
                  padding: '16px 18px',
                }}
              >
                <p
                  style={{
                    fontSize: '12px',
                    fontWeight: 500,
                    color: '#1a1a18',
                    marginBottom: '6px',
                  }}
                >
                  {title}
                </p>
                <p style={{ fontSize: '12px', color: '#5f5e5a', lineHeight: 1.6 }}>{body}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Metric cards */}
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(170px, 1fr))',
            gap: '12px',
            marginBottom: '32px',
          }}
        >
          {metrics.map(({ num, label, note }) => (
            <div
              key={num}
              style={{
                background: '#fff',
                borderRadius: '10px',
                padding: '20px 18px',
                border: '0.5px solid rgba(0,0,0,0.06)',
              }}
            >
              <div
                style={{
                  fontSize: '30px',
                  fontWeight: 500,
                  color: '#1a1a18',
                  letterSpacing: '-0.02em',
                  marginBottom: '6px',
                  lineHeight: 1,
                }}
              >
                {num}
              </div>
              <div
                style={{
                  fontSize: '10px',
                  fontWeight: 500,
                  letterSpacing: '0.08em',
                  textTransform: 'uppercase',
                  color: '#888780',
                  marginBottom: '6px',
                }}
              >
                {label}
              </div>
              <div style={{ fontSize: '11px', color: '#aaa99b', lineHeight: 1.5 }}>{note}</div>
            </div>
          ))}
        </div>

        <p
          style={{
            fontSize: '13px',
            color: '#5f5e5a',
            maxWidth: '540px',
            margin: '0 auto',
            textAlign: 'center',
            lineHeight: 1.75,
          }}
        >
          A closing package with 7 documents costs approximately{' '}
          <strong style={{ color: '#1a1a18', fontWeight: 500 }}>
            $0.08 to validate end-to-end
          </strong>{' '}
          — including classification, field extraction, 42 rule checks,
          cross-document consistency analysis, a 5-bullet executive brief, and a
          prioritized action plan. At $5–6 per file, gross margin stays above 98%.
        </p>
      </div>
    </section>
  )
}

// ── What it detects ───────────────────────────────────────────────────────────
function WhatItDetectsSection() {
  const conflicts = [
    {
      severity: 'FAIL',
      rule_id: 'PA-003',
      title: 'Purchase price mismatch',
      description:
        '$385,000 in Purchase Agreement vs $387,500 in Closing Disclosure. Difference of $2,500 — likely an amendment not reflected in the CD.',
    },
    {
      severity: 'FAIL',
      rule_id: 'PA-001',
      title: 'Buyer name inconsistency',
      description:
        '“Martinez” in Purchase Agreement vs “Martínez” in Title Commitment. Accent difference — may cause title transfer rejection depending on jurisdiction.',
    },
    {
      severity: 'WARNING',
      rule_id: 'LN-004',
      title: 'Missing document',
      description:
        'Builder invoice not found in the package. Required for new construction loan disbursement. File may be present under a non-standard name.',
    },
  ]

  const badge = {
    FAIL: { bg: '#FCEBEB', color: '#A32D2D', border: '#F09595' },
    WARNING: { bg: '#FAEEDA', color: '#854F0B', border: '#FAC775' },
    PASS: { bg: '#EAF3DE', color: '#3B6D11', border: '#C0DD97' },
  }

  return (
    <section style={{ background: '#fff', borderBottom: '0.5px solid rgba(0,0,0,0.07)' }}>
      <div className="cc-section">
        <span style={{ ...eyebrow }}>What it detects</span>
        <h2 style={{ ...sectionTitle }}>Real conflicts, found automatically</h2>
        <p style={{ ...bodyText, marginBottom: '40px', maxWidth: '520px' }}>
          Representative findings from a typical residential closing package. Each card
          shows the rule reference, severity, and a plain-language description —
          exactly as it appears in the generated report.
        </p>
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))',
            gap: '16px',
          }}
        >
          {conflicts.map((c) => {
            const b = badge[c.severity]
            return (
              <div
                key={c.rule_id}
                style={{
                  background: '#fff',
                  border: '0.5px solid rgba(0,0,0,0.10)',
                  borderRadius: '12px',
                  overflow: 'hidden',
                  boxShadow: '0 1px 3px rgba(0,0,0,0.04)',
                }}
              >
                <div
                  style={{
                    padding: '10px 16px',
                    background: b.bg,
                    borderBottom: `0.5px solid ${b.border}`,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                  }}
                >
                  <span
                    style={{
                      fontSize: '11px',
                      fontWeight: 600,
                      color: b.color,
                      letterSpacing: '0.07em',
                    }}
                  >
                    {c.severity}
                  </span>
                  <span
                    style={{
                      fontFamily: 'DM Mono, monospace',
                      fontSize: '10px',
                      color: b.color,
                      opacity: 0.7,
                    }}
                  >
                    {c.rule_id}
                  </span>
                </div>
                <div style={{ padding: '16px' }}>
                  <p
                    style={{
                      fontSize: '13px',
                      fontWeight: 500,
                      color: '#1a1a18',
                      marginBottom: '8px',
                    }}
                  >
                    {c.title}
                  </p>
                  <p style={{ fontSize: '12px', color: '#5f5e5a', lineHeight: 1.65 }}>
                    {c.description}
                  </p>
                </div>
              </div>
            )
          })}
        </div>
      </div>
    </section>
  )
}

// ── Live Demo ─────────────────────────────────────────────────────────────────
function LiveDemoSection() {
  const [files, setFiles] = useState([])
  const [dragging, setDragging] = useState(false)
  const [view, setView] = useState('idle')
  const [stepIdx, setStepIdx] = useState(0)
  const [errorMsg, setErrorMsg] = useState(null)
  const [demoLoading, setDemoLoading] = useState(false)
  const inputRef = useRef()
  const navigate = useNavigate()
  const pollRef = useRef(null)
  const stepIvRef = useRef(null)

  const addFiles = (incoming) => {
    const allowed = Array.from(incoming).filter((f) =>
      ALLOWED_EXTENSIONS.has(getExt(f.name)),
    )
    setFiles((prev) => [...prev, ...allowed])
  }

  const handleDrop = (e) => {
    e.preventDefault()
    setDragging(false)
    addFiles(e.dataTransfer.files)
  }

  const startPolling = (jobId) => {
    stepIvRef.current = setInterval(() => {
      setStepIdx((i) => (i < SCAN_STEPS.length - 1 ? i + 1 : i))
    }, 900)
    pollRef.current = setInterval(async () => {
      try {
        const data = await getResults(jobId)
        if (data.status === 'completed') {
          clearInterval(stepIvRef.current)
          clearInterval(pollRef.current)
          navigate(`/report/${jobId}`)
        } else if (data.status === 'failed') {
          clearInterval(stepIvRef.current)
          clearInterval(pollRef.current)
          setErrorMsg('Validation failed on the server. Please try again.')
          setView('error')
        }
      } catch {
        clearInterval(stepIvRef.current)
        clearInterval(pollRef.current)
        setErrorMsg('Connection lost while polling. Please try again.')
        setView('error')
      }
    }, 2000)
  }

  const handleSubmit = async () => {
    if (!files.length) return
    setView('processing')
    setStepIdx(0)
    setErrorMsg(null)
    try {
      const result = await submitValidation(files)
      startPolling(result.job_id)
    } catch (err) {
      setErrorMsg(err.response?.data?.detail || 'Upload failed. Is the API running?')
      setView('error')
    }
  }

  const handleDemo = async () => {
    setDemoLoading(true)
    setErrorMsg(null)
    try {
      const result = await submitDemo()
      setDemoLoading(false)
      setView('processing')
      setStepIdx(0)
      startPolling(result.job_id)
    } catch (err) {
      setDemoLoading(false)
      setErrorMsg(err.response?.data?.detail || 'Demo request failed. Is the API running?')
    }
  }

  useEffect(() => {
    return () => {
      if (pollRef.current) clearInterval(pollRef.current)
      if (stepIvRef.current) clearInterval(stepIvRef.current)
    }
  }, [])

  const handleRetry = () => {
    setFiles([])
    setView('idle')
    setErrorMsg(null)
    setStepIdx(0)
  }

  return (
    <section
      id="demo"
      style={{ background: '#f7f7f5', padding: '80px 24px 100px' }}
    >
      <div style={{ maxWidth: '720px', margin: '0 auto' }}>
        <span
          style={{
            ...eyebrow,
            textAlign: 'center',
            display: 'block',
            marginBottom: '8px',
          }}
        >
          Try it live
        </span>
        <p
          style={{
            fontSize: '13px',
            color: '#888780',
            textAlign: 'center',
            marginBottom: '32px',
            maxWidth: '440px',
            margin: '0 auto 32px',
          }}
        >
          Load the Martinez sample closing package, or drop your own files.
          <br />
          Runs live against the real backend.
        </p>

        <div className="cc-card">
          {/* Topbar */}
          <div className="cc-topbar">
            <span className="cc-logo">CloseCheck</span>
            {view === 'idle' && files.length > 0 && (
              <span className="cc-file-badge">
                {files.length} file{files.length !== 1 ? 's' : ''} selected
              </span>
            )}
            {view === 'processing' && (
              <span className="cc-file-badge">Analyzing…</span>
            )}
          </div>

          {/* Processing view */}
          {view === 'processing' && (
            <div
              style={{
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                padding: '60px 24px 52px',
                gap: '16px',
              }}
            >
              <div className="cc-spinner" />
              <p style={{ fontSize: '14px', fontWeight: 500, color: '#5f5e5a' }}>
                Reviewing your files…
              </p>
              <p
                className="cc-fade-up"
                key={stepIdx}
                style={{
                  fontFamily: 'DM Mono, monospace',
                  fontSize: '12px',
                  color: '#888780',
                }}
              >
                {SCAN_STEPS[stepIdx]}
              </p>
              <div style={{ marginTop: '8px', display: 'flex', gap: '6px' }}>
                {SCAN_STEPS.map((_, i) => (
                  <div
                    key={i}
                    style={{
                      width: '6px',
                      height: '6px',
                      borderRadius: '50%',
                      background: i <= stepIdx ? '#1a1a18' : 'rgba(0,0,0,0.12)',
                      transition: 'background 0.3s',
                    }}
                  />
                ))}
              </div>
            </div>
          )}

          {/* Error view */}
          {view === 'error' && (
            <div
              style={{
                padding: '40px 24px',
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                gap: '16px',
              }}
            >
              <div
                style={{
                  width: '100%',
                  background: '#FCEBEB',
                  border: '0.5px solid #F09595',
                  color: '#A32D2D',
                  borderRadius: '8px',
                  padding: '12px 16px',
                  fontSize: '13px',
                  textAlign: 'center',
                }}
              >
                {errorMsg}
              </div>
              <button className="cc-btn-sm" onClick={handleRetry}>
                ← Start over
              </button>
            </div>
          )}

          {/* Idle view */}
          {view === 'idle' && (
            <>
              {/* Drop zone */}
              <div
                onDragOver={(e) => {
                  e.preventDefault()
                  setDragging(true)
                }}
                onDragLeave={() => setDragging(false)}
                onDrop={handleDrop}
                onClick={() => inputRef.current.click()}
                style={{
                  border: dragging
                    ? '1.5px dashed rgba(0,0,0,0.30)'
                    : '1.5px dashed rgba(0,0,0,0.18)',
                  borderRadius: '12px',
                  padding: '40px 24px',
                  margin: '24px',
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  gap: '12px',
                  cursor: 'pointer',
                  background: dragging ? '#f7f7f5' : 'transparent',
                  transition: 'border-color 0.15s, background 0.15s',
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.borderColor = 'rgba(0,0,0,0.28)'
                  e.currentTarget.style.background = '#f9f9f7'
                }}
                onMouseLeave={(e) => {
                  if (!dragging) {
                    e.currentTarget.style.borderColor = 'rgba(0,0,0,0.18)'
                    e.currentTarget.style.background = 'transparent'
                  }
                }}
              >
                <input
                  ref={inputRef}
                  type="file"
                  multiple
                  accept=".pdf,.docx,.zip,.jpg,.jpeg,.png,.gif,.tiff,.tif,.webp,.bmp,.html,.htm,.xlsx,.xls,.csv,.tsv,.txt,.json"
                  style={{ display: 'none' }}
                  onChange={(e) => addFiles(e.target.files)}
                />
                <div
                  style={{
                    width: '40px',
                    height: '40px',
                    borderRadius: '8px',
                    background: '#f0efe9',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: '#888780',
                  }}
                >
                  <svg width="20" height="20" viewBox="0 0 22 22" fill="none">
                    <path
                      d="M11 3v12M7 7l4-4 4 4M3 16h16"
                      stroke="currentColor"
                      strokeWidth="1.5"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    />
                  </svg>
                </div>
                <p
                  style={{
                    fontSize: '13px',
                    fontWeight: 500,
                    color: '#5f5e5a',
                    textAlign: 'center',
                  }}
                >
                  {files.length > 0
                    ? 'Drop more files, or click to browse'
                    : 'Drop your closing files here'}
                </p>
                <p style={{ fontSize: '11px', color: '#888780', textAlign: 'center' }}>
                  PDF · DOCX · ZIP · XLSX · CSV · images — up to 20 files, 25 MB each
                </p>
              </div>

              {/* File list */}
              {files.length > 0 && (
                <div
                  style={{
                    margin: '0 24px',
                    border: '0.5px solid rgba(0,0,0,0.10)',
                    borderRadius: '8px',
                    overflow: 'hidden',
                  }}
                >
                  {files.map((f, i) => (
                    <div
                      key={i}
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        padding: '9px 14px',
                        borderTop: i > 0 ? '0.5px solid rgba(0,0,0,0.07)' : 'none',
                      }}
                    >
                      <div
                        style={{
                          display: 'flex',
                          alignItems: 'center',
                          gap: '10px',
                          minWidth: 0,
                        }}
                      >
                        <span
                          style={{
                            fontFamily: 'DM Mono, monospace',
                            fontSize: '10px',
                            fontWeight: 500,
                            padding: '2px 6px',
                            borderRadius: '4px',
                            background: '#EAF3DE',
                            color: '#3B6D11',
                            flexShrink: 0,
                          }}
                        >
                          {getExt(f.name).toUpperCase()}
                        </span>
                        <span
                          style={{
                            fontFamily: 'DM Mono, monospace',
                            fontSize: '12px',
                            color: '#1a1a18',
                            overflow: 'hidden',
                            textOverflow: 'ellipsis',
                            whiteSpace: 'nowrap',
                          }}
                        >
                          {f.name}
                        </span>
                        <span
                          style={{ fontSize: '11px', color: '#888780', flexShrink: 0 }}
                        >
                          {(f.size / 1024).toFixed(0)} KB
                        </span>
                      </div>
                      <button
                        onClick={(e) => {
                          e.stopPropagation()
                          setFiles(files.filter((_, j) => j !== i))
                        }}
                        style={{
                          background: 'none',
                          border: 'none',
                          cursor: 'pointer',
                          fontSize: '11px',
                          color: '#888780',
                          fontFamily: 'Sora, sans-serif',
                          flexShrink: 0,
                          marginLeft: '8px',
                        }}
                        onMouseEnter={(e) => (e.currentTarget.style.color = '#A32D2D')}
                        onMouseLeave={(e) => (e.currentTarget.style.color = '#888780')}
                      >
                        Remove
                      </button>
                    </div>
                  ))}
                </div>
              )}

              {/* Inline error */}
              {errorMsg && (
                <div
                  style={{
                    margin: '12px 24px 0',
                    background: '#FCEBEB',
                    border: '0.5px solid #F09595',
                    color: '#A32D2D',
                    borderRadius: '8px',
                    padding: '10px 14px',
                    fontSize: '12px',
                  }}
                >
                  {errorMsg}
                </div>
              )}

              {/* Bottom bar */}
              <div
                style={{
                  borderTop: '0.5px solid rgba(0,0,0,0.10)',
                  padding: '14px 24px',
                  marginTop: '24px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  gap: '12px',
                  flexWrap: 'wrap',
                }}
              >
                <button
                  className="cc-btn-sm"
                  onClick={handleDemo}
                  disabled={demoLoading}
                  style={{
                    opacity: demoLoading ? 0.5 : 1,
                    cursor: demoLoading ? 'not-allowed' : 'pointer',
                  }}
                >
                  {demoLoading ? 'Loading…' : 'Load sample package →'}
                </button>
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                  <span style={{ fontSize: '12px', color: '#5f5e5a' }}>
                    {files.length > 0
                      ? `${files.length} file${files.length !== 1 ? 's' : ''} ready`
                      : 'No files selected'}
                  </span>
                  <button
                    className="cc-btn-primary"
                    onClick={handleSubmit}
                    disabled={!files.length}
                    style={{
                      opacity: !files.length ? 0.4 : 1,
                      cursor: !files.length ? 'not-allowed' : 'pointer',
                    }}
                  >
                    Validate →
                  </button>
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </section>
  )
}

// ── Stack & Timeline ──────────────────────────────────────────────────────────
function StackTimelineSection() {
  const stack = [
    { badge: 'LANG', label: 'Python 3.11' },
    { badge: 'API', label: 'FastAPI + uvicorn' },
    { badge: 'LLM', label: 'Claude Sonnet 4.5 + Haiku' },
    { badge: 'DB', label: 'SQLite → PostgreSQL' },
    { badge: 'PARSE', label: 'PyMuPDF · pdfplumber · python-docx' },
    { badge: 'FRONT', label: 'React 18 + Vite + Tailwind CSS' },
    { badge: 'HTTP', label: 'Axios' },
    { badge: 'DEPLOY', label: 'Docker Compose' },
  ]

  const timeline = [
    'Domain research + validation rule schema design',
    'FastAPI skeleton + file ingestion pipeline',
    'Claude document classifier + confidence-based routing',
    'Field extractor + head/tail sampler + ALTA parser',
    '42-rule deterministic validation engine',
    'Cross-document consistency checker',
    'Report builder + executive brief generator',
    'React frontend — uploader, processing, report dashboard',
    'ConflictCard UI + action plan modal + email draft',
    'Docker Compose + test suite + portfolio page',
  ]

  const badgeStyle = {
    fontFamily: 'DM Mono, monospace',
    fontSize: '9px',
    fontWeight: 500,
    padding: '2px 7px',
    borderRadius: '4px',
    background: 'rgba(255,255,255,0.08)',
    color: 'rgba(255,255,255,0.45)',
    flexShrink: 0,
    letterSpacing: '0.06em',
  }

  return (
    <section style={{ background: '#1a1a18', padding: '80px 32px 72px' }}>
      <div style={{ maxWidth: '1100px', margin: '0 auto' }}>
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
            gap: '64px',
            marginBottom: '64px',
          }}
        >
          {/* Stack column */}
          <div>
            <p
              style={{
                fontSize: '10px',
                fontWeight: 500,
                letterSpacing: '0.12em',
                textTransform: 'uppercase',
                color: 'rgba(255,255,255,0.30)',
                marginBottom: '24px',
              }}
            >
              Stack
            </p>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {stack.map(({ badge, label }) => (
                <div key={badge} style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                  <span style={badgeStyle}>{badge}</span>
                  <span
                    style={{
                      fontSize: '13px',
                      color: 'rgba(255,255,255,0.75)',
                      fontFamily: 'Sora, sans-serif',
                    }}
                  >
                    {label}
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Timeline column */}
          <div>
            <p
              style={{
                fontSize: '10px',
                fontWeight: 500,
                letterSpacing: '0.12em',
                textTransform: 'uppercase',
                color: 'rgba(255,255,255,0.30)',
                marginBottom: '24px',
              }}
            >
              10-day build
            </p>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              {timeline.map((item, i) => (
                <div
                  key={i}
                  style={{ display: 'flex', gap: '14px', alignItems: 'flex-start' }}
                >
                  <span
                    style={{
                      fontFamily: 'DM Mono, monospace',
                      fontSize: '10px',
                      color: 'rgba(255,255,255,0.22)',
                      flexShrink: 0,
                      paddingTop: '2px',
                      minWidth: '20px',
                    }}
                  >
                    {String(i + 1).padStart(2, '0')}
                  </span>
                  <span
                    style={{
                      fontSize: '12px',
                      color: 'rgba(255,255,255,0.62)',
                      lineHeight: 1.6,
                      fontFamily: 'Sora, sans-serif',
                    }}
                  >
                    {item}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Bio + CTA */}
        <div
          style={{
            borderTop: '0.5px solid rgba(255,255,255,0.07)',
            paddingTop: '40px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            flexWrap: 'wrap',
            gap: '20px',
          }}
        >
          <div>
            <p
              style={{
                fontSize: '14px',
                fontWeight: 500,
                color: 'rgba(255,255,255,0.85)',
                marginBottom: '4px',
              }}
            >
              Built by Orlando B.
            </p>
            <p style={{ fontSize: '12px', color: 'rgba(255,255,255,0.38)' }}>
              Full-stack developer &amp; AI systems builder · Charlotte, NC
            </p>
          </div>
          <a
            href="mailto:me@orlandobatista.dev"
            style={{
              fontFamily: 'Sora, sans-serif',
              fontSize: '13px',
              fontWeight: 500,
              color: 'rgba(255,255,255,0.85)',
              background: 'rgba(255,255,255,0.07)',
              border: '0.5px solid rgba(255,255,255,0.12)',
              borderRadius: '20px',
              padding: '10px 22px',
              textDecoration: 'none',
              transition: 'background 0.15s',
            }}
            onMouseEnter={(e) =>
              (e.currentTarget.style.background = 'rgba(255,255,255,0.12)')
            }
            onMouseLeave={(e) =>
              (e.currentTarget.style.background = 'rgba(255,255,255,0.07)')
            }
          >
            Interested in what I can build for your team? →
          </a>
        </div>
      </div>
    </section>
  )
}

// ── Footer ────────────────────────────────────────────────────────────────────
function Footer() {
  return (
    <footer
      style={{
        background: '#f0efe9',
        borderTop: '0.5px solid rgba(0,0,0,0.08)',
        padding: '28px 32px',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        gap: '6px',
      }}
    >
      <p
        style={{
          fontFamily: 'DM Mono, monospace',
          fontSize: '11px',
          color: '#888780',
          letterSpacing: '0.06em',
        }}
      >
        CLOSECHECK · AI PRE-CLOSE VALIDATOR · BUILT WITH CLAUDE API
      </p>
      <p
        style={{
          fontFamily: 'DM Mono, monospace',
          fontSize: '10px',
          color: '#aaa99b',
          letterSpacing: '0.05em',
        }}
      >
        orlandobatista.dev · me@orlandobatista.dev · github.com/orlandobatistac
      </p>
    </footer>
  )
}

// ── Page ──────────────────────────────────────────────────────────────────────
export default function Upload() {
  return (
    <div style={{ minHeight: '100vh' }}>
      <StickyNav />
      <HeroSection />
      <ProblemSection />
      <ArchitectureSection />
      <CostArchitectureSection />
      <WhatItDetectsSection />
      <LiveDemoSection />
      <StackTimelineSection />
      <Footer />
    </div>
  )
}
