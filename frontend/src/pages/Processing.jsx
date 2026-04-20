import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { getResults } from '../api/client'

const SCAN_STEPS = [
  'Ingesting documents',
  'Running OCR…',
  'Extracting key fields…',
  'Cross-referencing docs…',
  'Generating executive brief…',
]

const STEP_SUBLABELS = [
  'Parsing and classifying all files',
  'Extracting text from images and PDFs',
  'Claude reading each document',
  'Running 42 deterministic rules',
  'Claude synthesizing findings',
]

export default function Processing() {
  const { jobId } = useParams()
  const navigate = useNavigate()
  const [stepIdx, setStepIdx] = useState(0)
  const [failed, setFailed] = useState(false)

  // Step animation
  useEffect(() => {
    const iv = setInterval(() => {
      setStepIdx((i) => (i < SCAN_STEPS.length - 1 ? i + 1 : i))
    }, 900)
    return () => clearInterval(iv)
  }, [])

  // Poll for completion
  useEffect(() => {
    const poll = setInterval(async () => {
      try {
        const data = await getResults(jobId)
        if (data.status === 'completed') {
          clearInterval(poll)
          navigate(`/report/${jobId}`)
        } else if (data.status === 'failed') {
          clearInterval(poll)
          setFailed(true)
        }
      } catch {
        clearInterval(poll)
        setFailed(true)
      }
    }, 2000)
    return () => clearInterval(poll)
  }, [jobId, navigate])

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        background: 'rgba(255,255,255,0.96)',
        zIndex: 100,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
      }}
    >
      {failed ? (
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '16px' }}>
          <p style={{ fontSize: '14px', fontWeight: 500, color: '#A32D2D' }}>
            Validation failed.
          </p>
          <button className="cc-btn-primary" onClick={() => navigate('/')}>
            Try again
          </button>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', width: '300px' }}>
          <p
            style={{
              fontSize: '11px',
              fontWeight: 500,
              letterSpacing: '0.1em',
              textTransform: 'uppercase',
              color: '#888780',
              marginBottom: '24px',
            }}
          >
            CloseCheck — reviewing file
          </p>
          {SCAN_STEPS.map((label, idx) => {
            const done   = idx < stepIdx
            const active = idx === stepIdx
            return (
              <div key={label} style={{ display: 'flex', gap: '14px', alignItems: 'flex-start' }}>
                {/* Left rail */}
                <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', width: '20px', flexShrink: 0 }}>
                  {done ? (
                    <div
                      style={{
                        width: '20px',
                        height: '20px',
                        borderRadius: '50%',
                        background: '#EAF3DE',
                        border: '0.5px solid #C0DD97',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        fontSize: '10px',
                        color: '#3B6D11',
                        flexShrink: 0,
                      }}
                    >
                      ✓
                    </div>
                  ) : active ? (
                    <div
                      style={{
                        width: '20px',
                        height: '20px',
                        borderRadius: '50%',
                        border: '2px solid rgba(0,0,0,0.10)',
                        borderTopColor: '#1a1a18',
                        animation: 'spin 1s linear infinite',
                        flexShrink: 0,
                      }}
                    />
                  ) : (
                    <div
                      style={{
                        width: '20px',
                        height: '20px',
                        borderRadius: '50%',
                        border: '0.5px solid rgba(0,0,0,0.15)',
                        flexShrink: 0,
                      }}
                    />
                  )}
                  {idx < SCAN_STEPS.length - 1 && (
                    <div
                      style={{
                        width: '1px',
                        flex: 1,
                        minHeight: '24px',
                        background: done ? '#C0DD97' : 'rgba(0,0,0,0.10)',
                        margin: '3px 0',
                      }}
                    />
                  )}
                </div>
                {/* Step text */}
                <div style={{ paddingBottom: idx < SCAN_STEPS.length - 1 ? '18px' : 0 }}>
                  <p
                    style={{
                      fontSize: '13px',
                      fontWeight: active ? 500 : 400,
                      color: done ? '#aaa99b' : active ? '#1a1a18' : '#c8c7c0',
                      marginBottom: active ? '3px' : 0,
                      lineHeight: 1.3,
                    }}
                  >
                    {label}
                  </p>
                  {active && (
                    <p
                      style={{
                        fontFamily: 'DM Mono, monospace',
                        fontSize: '11px',
                        color: '#888780',
                        lineHeight: 1.4,
                      }}
                    >
                      {STEP_SUBLABELS[idx]}
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
