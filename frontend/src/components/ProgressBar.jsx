/**
 * Document grid — shows each processed document as a chip with status dot.
 * Props: { documents: DocumentInfo[] }
 */
export default function ProgressBar({ documents }) {
  if (!documents?.length) {
    return (
      <div style={{ padding: '24px', textAlign: 'center' }}>
        <p style={{ fontSize: '13px', color: '#888780' }}>No documents processed.</p>
      </div>
    )
  }

  return (
    <div
      style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fill, minmax(140px, 1fr))',
        gap: '8px',
        padding: '0 24px 24px',
      }}
    >
      {documents.map((doc) => {
        const st = docStatus(doc)
        const styles = DOC_STYLES[st]
        const ext = (doc.filename.split('.').pop() || 'FILE').toUpperCase().slice(0, 4)
        const name = truncate(doc.filename, 18)

        return (
          <div
            key={doc.filename}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              padding: '9px 12px',
              borderRadius: '8px',
              border: '0.5px solid rgba(0,0,0,0.10)',
              background: '#ffffff',
              fontSize: '11px',
              color: '#5f5e5a',
              transition: 'border-color 0.12s',
              cursor: 'default',
            }}
            onMouseEnter={(e) => (e.currentTarget.style.borderColor = 'rgba(0,0,0,0.18)')}
            onMouseLeave={(e) => (e.currentTarget.style.borderColor = 'rgba(0,0,0,0.10)')}
          >
            {/* File type icon */}
            <div
              style={{
                width: '20px',
                height: '20px',
                borderRadius: '3px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: '9px',
                fontWeight: 500,
                fontFamily: 'DM Mono, monospace',
                flexShrink: 0,
                ...styles.icon,
              }}
            >
              {ext}
            </div>

            {/* Filename */}
            <span
              style={{
                flex: 1,
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                whiteSpace: 'nowrap',
              }}
            >
              {name}
            </span>

            {/* Status dot */}
            <span
              style={{
                width: '6px',
                height: '6px',
                borderRadius: '50%',
                flexShrink: 0,
                marginLeft: 'auto',
                background: styles.dot,
              }}
            />
          </div>
        )
      })}
    </div>
  )
}

function docStatus(doc) {
  if (!doc || doc.status === 'missing') return 'err'
  if (doc.status === 'warn') return 'warn'
  return 'ok'
}

const DOC_STYLES = {
  ok:   { icon: { background: '#EAF3DE', color: '#3B6D11' }, dot: '#639922' },
  warn: { icon: { background: '#FAEEDA', color: '#854F0B' }, dot: '#EF9F27' },
  err:  { icon: { background: '#FCEBEB', color: '#A32D2D' }, dot: '#E24B4A' },
}

function truncate(name, max) {
  if (name.length <= max) return name
  return name.slice(0, max - 1) + '…'
}
