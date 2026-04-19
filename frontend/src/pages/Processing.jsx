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
        gap: '16px',
      }}
    >
      {failed ? (
        <>
          <p style={{ fontSize: '14px', fontWeight: 500, color: '#A32D2D' }}>
            Validation failed.
          </p>
          <button
            className="cc-btn-primary"
            onClick={() => navigate('/')}
          >
            Try again
          </button>
        </>
      ) : (
        <>
          <div className="cc-spinner" />
          <p
            style={{
              fontSize: '14px',
              fontWeight: 500,
              color: '#5f5e5a',
            }}
          >
            Reviewing file…
          </p>
          <p
            style={{
              fontFamily: 'DM Mono, monospace',
              fontSize: '12px',
              color: '#888780',
            }}
          >
            {SCAN_STEPS[stepIdx]}
          </p>
        </>
      )}
    </div>
  )
}
