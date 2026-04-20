import { useState, useRef, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { submitValidation, getResults } from '../api/client'

const ALLOWED_EXTENSIONS = new Set([
  'pdf', 'docx', 'zip',
  'jpg', 'jpeg', 'png', 'gif', 'tiff', 'tif', 'webp', 'bmp',
  'html', 'htm',
  'xlsx', 'xls',
  'csv', 'tsv',
  'txt', 'json',
])

const SCAN_STEPS = [
  'Ingesting documents…',
  'Running OCR…',
  'Extracting key fields…',
  'Cross-referencing documents…',
  'Generating executive brief…',
]

const FORMATS = [
  'PDF', 'DOCX', 'ZIP', 'XLSX', 'XLS',
  'CSV', 'TSV', 'JPG', 'JPEG', 'PNG',
  'TIFF', 'WEBP', 'BMP', 'HTML', 'TXT', 'JSON',
]

const getExt = (name) => name.split('.').pop().toLowerCase()

// ── Nav ──────────────────────────────────────────────────────────────
function StickyNav() {
  return (
    <nav className="cc-nav">
      <span className="cc-logo">CloseCheck</span>
      <a
        href="#upload"
        className="cc-btn-primary"
        style={{ fontSize: '12px', padding: '7px 16px', textDecoration: 'none' }}
      >
        Try it →
      </a>
    </nav>
  )
}

// ── Hero ─────────────────────────────────────────────────────────────
function HeroSection() {
  return (
    <section style={{ background: '#fff', borderBottom: '0.5px solid rgba(0,0,0,0.07)' }}>
      <div
        className="cc-section"
        style={{ textAlign: 'center', paddingTop: '96px', paddingBottom: '96px' }}
      >
        <span className="cc-hero-badge">AI-Powered · Real Estate</span>
        <h1
          style={{
            fontSize: 'clamp(30px, 5vw, 54px)',
            fontWeight: 300,
            lineHeight: 1.12,
            letterSpacing: '-0.02em',
            color: '#1a1a18',
            maxWidth: '700px',
            margin: '0 auto 20px',
          }}
        >
          Validate any closing package<br />in 60 seconds
        </h1>
        <p
          style={{
            fontSize: '16px',
            color: '#5f5e5a',
            maxWidth: '480px',
            margin: '0 auto 36px',
            lineHeight: 1.65,
          }}
        >
          Upload your real estate transaction files. CloseCheck's AI reviews every
          document, flags inconsistencies, and delivers a structured audit report —
          before closing day.
        </p>
        <a
          href="#upload"
          className="cc-btn-primary"
          style={{
            fontSize: '14px',
            padding: '10px 24px',
            textDecoration: 'none',
            display: 'inline-block',
          }}
        >
          Validate a file now →
        </a>
      </div>
    </section>
  )
}

// ── How it works ─────────────────────────────────────────────────────
function HowItWorksSection() {
  const steps = [
    {
      n: '01',
      title: 'Upload',
      desc: 'Drop your closing package — PDFs, DOCX, images, spreadsheets, or a ZIP of everything.',
    },
    {
      n: '02',
      title: 'AI Analyzes',
      desc: 'CloseCheck classifies each document, extracts key fields, and cross-references names, amounts, and dates.',
    },
    {
      n: '03',
      title: 'Get Report',
      desc: 'Receive a Pass / Warning / Fail audit with specific issues, rule references, and an executive summary.',
    },
  ]

  return (
    <section style={{ background: '#f0efe9', borderBottom: '0.5px solid rgba(0,0,0,0.07)' }}>
      <div className="cc-section">
        <p className="cc-section-label" style={{ marginBottom: '40px' }}>
          How it works
        </p>
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
            gap: '32px',
          }}
        >
          {steps.map(({ n, title, desc }) => (
            <div key={n} style={{ display: 'flex', gap: '16px', alignItems: 'flex-start' }}>
              <div className="cc-step-dot">{n}</div>
              <div>
                <p
                  style={{
                    fontSize: '14px',
                    fontWeight: 500,
                    color: '#1a1a18',
                    marginBottom: '6px',
                  }}
                >
                  {title}
                </p>
                <p style={{ fontSize: '13px', color: '#5f5e5a', lineHeight: 1.65 }}>{desc}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}

// ── Capabilities ─────────────────────────────────────────────────────
function CapabilitiesSection() {
  const caps = [
    {
      label: 'DOC',
      title: 'Document Classification',
      desc: 'Identifies purchase agreements, title commitments, loan docs, closing disclosures, insurance binders, and 10 more document types using Claude AI.',
    },
    {
      label: 'X-REF',
      title: 'Cross-Reference Validation',
      desc: 'Verifies buyer/seller names, property addresses, purchase prices, and loan amounts are consistent across every document in the package.',
    },
    {
      label: 'RISK',
      title: 'Risk Flagging',
      desc: 'Runs 40+ structured rules with FAIL · WARNING · INFO severity tiers covering title, loan, insurance, identity, and compliance checks.',
    },
    {
      label: 'BRIEF',
      title: 'Executive Summary',
      desc: 'Claude generates a plain-language brief of the key findings — so agents and title officers can focus review where it matters most.',
    },
  ]

  return (
    <section style={{ background: '#fff', borderBottom: '0.5px solid rgba(0,0,0,0.07)' }}>
      <div className="cc-section">
        <p className="cc-section-label" style={{ marginBottom: '40px' }}>
          Capabilities
        </p>
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
            gap: '20px',
          }}
        >
          {caps.map(({ label, title, desc }) => (
            <div key={title} className="cc-capability-card">
              <span
                style={{
                  fontFamily: 'DM Mono, monospace',
                  fontSize: '10px',
                  fontWeight: 500,
                  padding: '2px 7px',
                  borderRadius: '4px',
                  background: '#EAF3DE',
                  color: '#3B6D11',
                  display: 'inline-block',
                  marginBottom: '14px',
                }}
              >
                {label}
              </span>
              <p
                style={{
                  fontSize: '13px',
                  fontWeight: 500,
                  color: '#1a1a18',
                  marginBottom: '8px',
                }}
              >
                {title}
              </p>
              <p style={{ fontSize: '12px', color: '#5f5e5a', lineHeight: 1.65 }}>{desc}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}

// ── Supported formats ────────────────────────────────────────────────
function FormatsSection() {
  return (
    <section style={{ background: '#f0efe9', borderBottom: '0.5px solid rgba(0,0,0,0.07)' }}>
      <div className="cc-section" style={{ paddingTop: '60px', paddingBottom: '60px' }}>
        <p className="cc-section-label" style={{ marginBottom: '24px' }}>
          Supported formats
        </p>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
          {FORMATS.map((f) => (
            <span key={f} className="cc-format-badge">
              {f}
            </span>
          ))}
        </div>
        <p style={{ fontSize: '12px', color: '#888780', marginTop: '16px' }}>
          Up to 20 files · 25 MB each · Batches can include a ZIP of the full closing folder
        </p>
      </div>
    </section>
  )
}

// ── Uploader ─────────────────────────────────────────────────────────
function UploaderSection() {
  const [files, setFiles] = useState([])
  const [dragging, setDragging] = useState(false)
  const [view, setView] = useState('idle') // 'idle' | 'processing' | 'error'
  const [stepIdx, setStepIdx] = useState(0)
  const [errorMsg, setErrorMsg] = useState(null)
  const inputRef = useRef()
  const navigate = useNavigate()
  const pollRef = useRef(null)
  const stepIvRef = useRef(null)

  const addFiles = (incoming) => {
    const allowed = Array.from(incoming).filter((f) =>
      ALLOWED_EXTENSIONS.has(getExt(f.name))
    )
    setFiles((prev) => [...prev, ...allowed])
  }

  const handleDrop = (e) => {
    e.preventDefault()
    setDragging(false)
    addFiles(e.dataTransfer.files)
  }

  const handleSubmit = async () => {
    if (!files.length) return
    setView('processing')
    setStepIdx(0)
    setErrorMsg(null)

    let jobId
    try {
      const result = await submitValidation(files)
      jobId = result.job_id
    } catch (err) {
      setErrorMsg(
        err.response?.data?.detail || 'Upload failed. Is the API running?'
      )
      setView('error')
      return
    }

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
      id="upload"
      style={{ background: '#fff', padding: '80px 24px 100px' }}
    >
      <div style={{ maxWidth: '720px', margin: '0 auto' }}>
        <p
          className="cc-section-label"
          style={{ marginBottom: '32px', textAlign: 'center' }}
        >
          Try it now
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

          {/* ── Processing ── */}
          {view === 'processing' && (
            <div
              style={{
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                padding: '56px 24px 48px',
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

          {/* ── Error ── */}
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
                �? Start over
              </button>
            </div>
          )}

          {/* ── Idle / files selected ── */}
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
                  padding: '48px 24px',
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
                  e.currentTarget.style.borderColor = 'rgba(0,0,0,0.30)'
                  e.currentTarget.style.background = '#f7f7f5'
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
                    width: '44px',
                    height: '44px',
                    borderRadius: '8px',
                    background: '#f7f7f5',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: '#888780',
                  }}
                >
                  <svg width="22" height="22" viewBox="0 0 22 22" fill="none">
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
                    fontSize: '14px',
                    fontWeight: 500,
                    color: '#5f5e5a',
                    textAlign: 'center',
                  }}
                >
                  {files.length > 0
                    ? 'Drop more files, or click to browse'
                    : 'Drop the closing file folder here'}
                </p>
                <p style={{ fontSize: '12px', color: '#888780', textAlign: 'center' }}>
                  PDF · DOCX · ZIP · XLSX · CSV · images · TXT · JSON — up to 20 files, 25 MB each
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
                        padding: '10px 14px',
                        borderTop: i > 0 ? '0.5px solid rgba(0,0,0,0.07)' : 'none',
                      }}
                    >
                      <div style={{ display: 'flex', alignItems: 'center', gap: '10px', minWidth: 0 }}>
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
                        <span style={{ fontSize: '11px', color: '#888780', flexShrink: 0 }}>
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

              {/* Bottom bar */}
              <div
                style={{
                  borderTop: '0.5px solid rgba(0,0,0,0.10)',
                  padding: '14px 24px',
                  marginTop: '24px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  gap: '16px',
                }}
              >
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
            </>
          )}
        </div>
      </div>
    </section>
  )
}

// ── Footer ────────────────────────────────────────────────────────────
function Footer() {
  return (
    <footer
      style={{
        background: '#f0efe9',
        borderTop: '0.5px solid rgba(0,0,0,0.08)',
        padding: '28px 32px',
        textAlign: 'center',
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
    </footer>
  )
}

// ── Page ──────────────────────────────────────────────────────────────
export default function Upload() {
  return (
    <div style={{ minHeight: '100vh' }}>
      <StickyNav />
      <HeroSection />
      <HowItWorksSection />
      <CapabilitiesSection />
      <FormatsSection />
      <UploaderSection />
      <Footer />
    </div>
  )
}
