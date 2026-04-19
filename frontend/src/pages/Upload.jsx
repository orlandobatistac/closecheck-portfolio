import { useState, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { submitValidation } from '../api/client'

export default function Upload() {
  const [files, setFiles] = useState([])
  const [dragging, setDragging] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const inputRef = useRef()
  const navigate = useNavigate()

  const addFiles = (incoming) => {
    const allowed = Array.from(incoming).filter(
      (f) => f.type === 'application/pdf' || f.name.endsWith('.docx')
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
    setLoading(true)
    setError(null)
    try {
      const { job_id } = await submitValidation(files)
      navigate(`/processing/${job_id}`)
    } catch (err) {
      setError(err.response?.data?.detail || 'Upload failed. Is the API running?')
      setLoading(false)
    }
  }

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
      <div className="cc-card" style={{ width: '100%', maxWidth: '720px' }}>

        {/* Topbar */}
        <div className="cc-topbar">
          <span className="cc-logo">CloseCheck</span>
          {files.length > 0 && (
            <span className="cc-file-badge">
              {files.length} file{files.length !== 1 ? 's' : ''} selected
            </span>
          )}
        </div>

        {/* Drop zone */}
        <div
          onDragOver={(e) => { e.preventDefault(); setDragging(true) }}
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
            accept=".pdf,.docx"
            style={{ display: 'none' }}
            onChange={(e) => addFiles(e.target.files)}
          />
          {/* Icon */}
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
          <p style={{ fontSize: '14px', fontWeight: 500, color: '#5f5e5a', textAlign: 'center' }}>
            Drop the closing file folder here
          </p>
          <p style={{ fontSize: '12px', color: '#888780' }}>
            PDF, DOCX — up to 20 files, 25MB each
          </p>
        </div>

        {/* File list */}
        {files.length > 0 && (
          <div
            style={{
              margin: '0 24px 0',
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
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <span
                    style={{
                      fontFamily: 'DM Mono, monospace',
                      fontSize: '10px',
                      fontWeight: 500,
                      padding: '2px 6px',
                      borderRadius: '4px',
                      background: '#EAF3DE',
                      color: '#3B6D11',
                    }}
                  >
                    {f.name.endsWith('.pdf') ? 'PDF' : 'DOCX'}
                  </span>
                  <span
                    style={{
                      fontFamily: 'DM Mono, monospace',
                      fontSize: '12px',
                      color: '#1a1a18',
                    }}
                  >
                    {f.name}
                  </span>
                  <span style={{ fontSize: '11px', color: '#888780' }}>
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

        {error && (
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
            {error}
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
            disabled={!files.length || loading}
            style={{
              opacity: !files.length || loading ? 0.4 : 1,
              cursor: !files.length || loading ? 'not-allowed' : 'pointer',
            }}
          >
            {loading ? 'Submitting…' : 'Validate File →'}
          </button>
        </div>
      </div>
    </div>
  )
}
