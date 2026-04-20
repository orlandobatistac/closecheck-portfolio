import { useState } from 'react'
import { getJobFileUrl } from '../api/client'

const PDF_EXTENSIONS = new Set(['pdf'])
const isPdf = (name) => PDF_EXTENSIONS.has((name || '').split('.').pop().toLowerCase())

/**
 * Split-view PDF viewer.
 * Shows a document selector when multiple viewable files exist,
 * then renders the selected file in an <iframe>.
 *
 * Props: { jobId: string, documents: DocumentInfo[] }
 */
export default function PdfViewer({ jobId, documents = [] }) {
  const viewable = documents.filter((d) => isPdf(d.filename) && d.status !== 'missing')
  const [selected, setSelected] = useState(viewable[0]?.filename || null)

  if (viewable.length === 0) {
    return (
      <div
        style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          height: '100%',
          minHeight: '320px',
          gap: '10px',
          color: '#888780',
        }}
      >
        <span style={{ fontSize: '28px' }}>📄</span>
        <p style={{ fontSize: '13px', textAlign: 'center', maxWidth: '260px', lineHeight: 1.6 }}>
          No PDF documents were uploaded for this job.
          <br />
          Upload PDF files to enable the document viewer.
        </p>
      </div>
    )
  }

  const fileUrl = selected ? getJobFileUrl(jobId, selected) : null

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', minHeight: '480px' }}>
      {/* Document selector */}
      {viewable.length > 1 && (
        <div
          style={{
            display: 'flex',
            gap: '6px',
            padding: '12px 16px',
            borderBottom: '0.5px solid rgba(0,0,0,0.10)',
            flexWrap: 'wrap',
          }}
        >
          {viewable.map((doc) => {
            const active = doc.filename === selected
            return (
              <button
                key={doc.filename}
                onClick={() => setSelected(doc.filename)}
                style={{
                  fontSize: '11px',
                  fontWeight: active ? 500 : 400,
                  fontFamily: 'DM Mono, monospace',
                  padding: '4px 10px',
                  borderRadius: '6px',
                  border: active
                    ? '0.5px solid rgba(0,0,0,0.25)'
                    : '0.5px solid rgba(0,0,0,0.10)',
                  background: active ? '#1a1a18' : 'transparent',
                  color: active ? '#ffffff' : '#5f5e5a',
                  cursor: 'pointer',
                  transition: 'all 0.12s',
                  maxWidth: '180px',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  whiteSpace: 'nowrap',
                }}
                title={doc.filename}
              >
                {doc.filename}
              </button>
            )
          })}
        </div>
      )}

      {/* Viewer */}
      {fileUrl ? (
        <iframe
          key={fileUrl}
          src={fileUrl}
          title={selected}
          style={{
            flex: 1,
            border: 'none',
            width: '100%',
            minHeight: '440px',
          }}
        />
      ) : (
        <div
          style={{
            flex: 1,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#888780',
            fontSize: '13px',
          }}
        >
          Select a document above.
        </div>
      )}
    </div>
  )
}
