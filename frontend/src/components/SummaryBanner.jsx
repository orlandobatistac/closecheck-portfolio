import { severityBg, severityColor, severityBorder, triageLabel } from '../utils/severity'

/**
 * Triage hero: status pill + executive brief bullets.
 * Props: { overall: string, executiveBrief: string[] }
 */
export default function SummaryBanner({ overall, executiveBrief }) {
  const label = triageLabel(overall)
  const hasDollarOrPercent = (text) => /\$[\d,]+|\d+%/.test(text)

  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'flex-start',
        gap: '20px',
        padding: '28px 24px',
        borderBottom: '0.5px solid rgba(0,0,0,0.10)',
      }}
    >
      {/* Status pill */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          padding: '9px 16px',
          borderRadius: '40px',
          fontSize: '13px',
          fontWeight: 500,
          flexShrink: 0,
          marginTop: '2px',
          background: severityBg(overall),
          color: severityColor(overall),
          border: `0.5px solid ${severityBorder(overall)}`,
        }}
      >
        <span
          style={{ width: '8px', height: '8px', borderRadius: '50%', background: 'currentColor', flexShrink: 0 }}
        />
        {label}
      </div>

      {/* Executive brief */}
      <div style={{ flex: 1 }}>
        <p
          style={{
            fontSize: '10px',
            fontWeight: 500,
            letterSpacing: '0.1em',
            textTransform: 'uppercase',
            color: '#888780',
            marginBottom: '10px',
          }}
        >
          Executive brief
        </p>
        <ul style={{ listStyle: 'none', display: 'flex', flexDirection: 'column', gap: '5px' }}>
          {(executiveBrief || []).map((line, i) => {
            const flagged = hasDollarOrPercent(line)
            return (
              <li
                key={i}
                style={{
                  fontSize: '13px',
                  lineHeight: 1.55,
                  color: flagged ? '#854F0B' : '#5f5e5a',
                  paddingLeft: '14px',
                  position: 'relative',
                }}
              >
                <span
                  style={{
                    position: 'absolute',
                    left: 0,
                    top: '8px',
                    width: '4px',
                    height: '4px',
                    borderRadius: '50%',
                    background: flagged ? '#EF9F27' : '#888780',
                  }}
                />
                {line}
              </li>
            )
          })}
        </ul>
      </div>
    </div>
  )
}
