import { useEffect } from 'react'

/**
 * A fixed-position toast displayed when the demo rate limit (HTTP 429) is hit.
 * Auto-dismisses after `autoCloseMs` milliseconds.
 *
 * Props:
 *   message      {string}   — The human-readable message from the server
 *   onClose      {function} — Called when the toast is dismissed
 *   autoCloseMs  {number}   — Auto-dismiss delay in ms (default 6000)
 */
export default function RateLimitToast({ message, onClose, autoCloseMs = 6000 }) {
  useEffect(() => {
    const t = setTimeout(onClose, autoCloseMs)
    return () => clearTimeout(t)
  }, [onClose, autoCloseMs])

  return (
    <div
      role="alert"
      aria-live="assertive"
      style={{
        position: 'fixed',
        top: '24px',
        left: '50%',
        transform: 'translateX(-50%)',
        zIndex: 9999,
        display: 'flex',
        alignItems: 'flex-start',
        gap: '12px',
        background: '#1a1a18',
        color: '#f7f7f5',
        borderRadius: '10px',
        padding: '14px 18px',
        boxShadow: '0 4px 24px rgba(0,0,0,0.22)',
        maxWidth: '420px',
        width: 'calc(100vw - 48px)',
        fontFamily: 'Sora, sans-serif',
        fontSize: '13px',
        lineHeight: 1.55,
      }}
    >
      {/* Icon */}
      <span style={{ fontSize: '18px', flexShrink: 0, marginTop: '1px' }}>⏳</span>

      {/* Text */}
      <span style={{ flex: 1 }}>{message}</span>

      {/* Close button */}
      <button
        onClick={onClose}
        aria-label="Dismiss"
        style={{
          background: 'none',
          border: 'none',
          color: 'rgba(247,247,245,0.5)',
          cursor: 'pointer',
          fontSize: '16px',
          lineHeight: 1,
          padding: '0 0 0 4px',
          flexShrink: 0,
        }}
      >
        ✕
      </button>
    </div>
  )
}
