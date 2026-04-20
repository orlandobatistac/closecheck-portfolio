import { severityBg, severityColor, severityBorder, triageLabel } from '../utils/severity'

/**
 * Triage hero: status pill + executive brief bullets.
 * Props: { overall: string, executiveBrief: string[] }
 */
export default function SummaryBanner({ overall, executiveBrief, results = [] }) {
  const label = triageLabel(overall)
  const hasDollarOrPercent = (text) => /\$[\d,]+|\d+%/.test(text)

  const passCount = results.filter((r) => r.status === 'PASS').length
  const totalRules = results.filter((r) => r.status !== 'SKIPPED').length
  const passRate = totalRules > 0 ? Math.round((passCount / totalRules) * 100) : 0
  const gaugeColor = passRate >= 70 ? '#3B6D11' : passRate >= 40 ? '#854F0B' : '#A32D2D'
  const gaugeTrack = passRate >= 70 ? '#EAF3DE' : passRate >= 40 ? '#FAEEDA' : '#FCEBEB'
  const C = 175.93
  const dashOffset = C * (1 - passRate / 100)

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

      {/* Health score gauge */}
      {totalRules > 0 && (
        <div
          style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: '4px',
            flexShrink: 0,
          }}
        >
          <svg width="72" height="72" viewBox="0 0 72 72">
            <circle cx="36" cy="36" r="28" fill="none" stroke={gaugeTrack} strokeWidth="6" />
            <circle
              cx="36"
              cy="36"
              r="28"
              fill="none"
              stroke={gaugeColor}
              strokeWidth="6"
              strokeLinecap="round"
              strokeDasharray={`${C} ${C}`}
              strokeDashoffset={dashOffset}
              transform="rotate(-90 36 36)"
              style={{ transition: 'stroke-dashoffset 0.6s ease' }}
            />
            <text
              x="36"
              y="40"
              textAnchor="middle"
              dominantBaseline="middle"
              style={{
                fontFamily: 'Sora, sans-serif',
                fontSize: '13px',
                fontWeight: '600',
                fill: gaugeColor,
              }}
            >
              {passRate}%
            </text>
          </svg>
          <span
            style={{
              fontSize: '9px',
              fontWeight: 500,
              letterSpacing: '0.08em',
              textTransform: 'uppercase',
              color: '#888780',
            }}
          >
            Health
          </span>
        </div>
      )}
    </div>
  )
}
