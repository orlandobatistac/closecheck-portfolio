import { useState } from 'react'
import { getJobFileUrl } from '../api/client'

const PDF_EXTENSIONS = new Set(['pdf'])
const isPdf = (name) => PDF_EXTENSIONS.has((name || '').split('.').pop().toLowerCase())

// ── Shared placeholder ─────────────────────────────────────────────────────────
function ViewerPlaceholder({ icon, title, body, hint }) {
  return (
    <div
      style={{
        flex: 1,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '32px 24px',
        gap: '8px',
        textAlign: 'center',
      }}
    >
      <span style={{ fontSize: '28px', lineHeight: 1 }}>{icon}</span>
      <p
        style={{
          fontSize: '13px',
          fontWeight: 600,
          fontFamily: 'Sora, sans-serif',
          color: '#1a1a18',
          margin: 0,
        }}
      >
        {title}
      </p>
      <p
        style={{
          fontSize: '13px',
          color: '#5f5e5a',
          margin: 0,
          maxWidth: '300px',
          lineHeight: 1.6,
        }}
      >
        {body}
      </p>
      {hint && (
        <p
          style={{
            fontSize: '11px',
            color: '#888780',
            margin: '6px 0 0',
            maxWidth: '300px',
            lineHeight: 1.5,
            paddingTop: '10px',
            borderTop: '0.5px solid rgba(0,0,0,0.08)',
          }}
        >
          {hint}
        </p>
      )}
    </div>
  )
}

/**
 * Split-view PDF viewer.
 * Shows a document selector when multiple viewable files exist,
 * then renders the selected file in an <iframe>.
 *
 * Props:
 *   jobId        string           — required
 *   documents    DocumentInfo[]   — list of all docs for this job
 *   selectedDoc  string | null    — (optional) controlled: filename to display
 *   onSelectDoc  (filename) => void — (optional) controlled: called when user changes doc
 *   pageNumber   number | null      — (optional) jump to this 1-indexed page on load
 *
 * If selectedDoc/onSelectDoc are provided the component runs in controlled mode.
 * Otherwise it manages selection internally (uncontrolled / backward-compatible).
 */
export default function PdfViewer({ jobId, documents = [], selectedDoc: controlledDoc, onSelectDoc, pageNumber = null }) {
  const viewable = documents.filter((d) => isPdf(d.filename) && d.status !== 'missing')
  const [internalSelected, setInternalSelected] = useState(viewable[0]?.filename || null)
  const [loadErrorUrl, setLoadErrorUrl] = useState(null)

  const isControlled = controlledDoc !== undefined
  const selected = isControlled ? controlledDoc : internalSelected
  const setSelected = isControlled
    ? (filename) => onSelectDoc && onSelectDoc(filename)
    : setInternalSelected

  // ── Case 1–3: no viewable PDFs ─────────────────────────────────────────────
  if (viewable.length === 0) {
    const hasMissing = documents.some((d) => d.status === 'missing')
    const hasNonPdf  = documents.some((d) => !isPdf(d.filename))

    if (documents.length === 0) {
      return (
        <ViewerPlaceholder
          icon="📁"
          title="No documents uploaded"
          body="No files were attached to this job."
          hint="Re-upload your closing package to enable the document preview."
        />
      )
    }

    if (hasMissing) {
      return (
        <ViewerPlaceholder
          icon="🔍"
          title="Documents not found in this package"
          body="One or more files couldn't be located — they may not have uploaded correctly."
          hint="Try re-submitting the package. All detected issues are still shown in the panel."
        />
      )
    }

    if (hasNonPdf) {
      const names = documents.map((d) => d.filename)
      const shown = names.slice(0, 2).join(', ')
      const extra = names.length > 2 ? ` and ${names.length - 2} more` : ''
      return (
        <ViewerPlaceholder
          icon="📄"
          title="Preview not available for these files"
          body={`${shown}${extra} ${names.length === 1 ? 'was' : 'were'} analyzed but can't be displayed inline — only PDF files can be previewed here.`}
          hint="All issues were still detected. Download the originals to review the source documents."
        />
      )
    }

    // Catch-all (e.g. unsupported format not covered above)
    return (
      <ViewerPlaceholder
        icon="📄"
        title="Preview not available"
        body="None of the uploaded files can be displayed in the viewer."
        hint="Download the originals to review the source documents."
      />
    )
  }

  // ── Reusable doc selector ──────────────────────────────────────────────────
  const docSelector = viewable.length > 1 ? (
    <div
      style={{
        padding: '10px 14px',
        borderBottom: '0.5px solid rgba(0,0,0,0.10)',
        background: '#f7f7f5',
        flexShrink: 0,
      }}
    >
      <select
        value={selected || ''}
        onChange={(e) => {
          setLoadErrorUrl(null)
          setSelected(e.target.value)
        }}
        style={{
          width: '100%',
          fontSize: '12px',
          fontFamily: 'DM Mono, monospace',
          fontWeight: 500,
          color: '#1a1a18',
          background: '#ffffff',
          border: '0.5px solid rgba(0,0,0,0.18)',
          borderRadius: '6px',
          padding: '6px 10px',
          cursor: 'pointer',
          appearance: 'none',
          backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath fill='%23888780' d='M6 8L1 3h10z'/%3E%3C/svg%3E")`,
          backgroundRepeat: 'no-repeat',
          backgroundPosition: 'right 10px center',
          paddingRight: '28px',
        }}
      >
        {viewable.map((doc) => (
          <option key={doc.filename} value={doc.filename}>
            {doc.filename}
          </option>
        ))}
      </select>
    </div>
  ) : null

  // ── Case 4–5: a specific doc is selected but can't be previewed ───────────
  if (selected && !viewable.some((d) => d.filename === selected)) {
    const selectedInfo = documents.find((d) => d.filename === selected)
    const isMissing = selectedInfo?.status === 'missing'

    return (
      <div style={{ display: 'flex', flexDirection: 'column', height: '100%', minHeight: '480px' }}>
        {docSelector}
        {isMissing ? (
          <ViewerPlaceholder
            icon="🔍"
            title="Document not found"
            body={`"${selected}" was referenced in an issue but couldn't be located in this package.`}
            hint="The extracted values are still used in the issues panel. Try re-submitting to restore the file."
          />
        ) : (
          <ViewerPlaceholder
            icon="📄"
            title="Preview not available for this file"
            body={`"${selected}" can't be displayed inline — only PDF files can be previewed here.`}
            hint="Download the file to review it directly."
          />
        )}
      </div>
    )
  }

  const fileUrl = selected
    ? getJobFileUrl(jobId, selected) + (pageNumber ? `#page=${pageNumber}` : '')
    : null
  const loadFailed = loadErrorUrl !== null && loadErrorUrl === fileUrl

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', minHeight: '480px' }}>
      {docSelector}

      {/* ── Case 6: load error ── */}
      {loadFailed ? (
        <ViewerPlaceholder
          icon="⚠️"
          title="Unable to load this document"
          body={`"${selected}" couldn't be loaded — the file may be corrupted or temporarily unavailable.`}
          hint="Try selecting a different document or refreshing the page."
        />
      ) : !fileUrl ? (
        /* ── Case 7: nothing selected yet (multi-doc, none chosen) ── */
        <ViewerPlaceholder
          icon="👆"
          title="No document selected"
          body="Select a document from the list above to preview it here."
        />
      ) : (
        <iframe
          key={fileUrl}
          src={fileUrl}
          title={selected}
          onError={() => setLoadErrorUrl(fileUrl)}
          style={{
            flex: 1,
            border: 'none',
            width: '100%',
            minHeight: '440px',
          }}
        />
      )}
    </div>
  )
}
