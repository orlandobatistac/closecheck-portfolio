import { useState } from 'react'
import api from '../api/client'

/**
 * Button that triggers PDF report download.
 * Props: { jobId: string }
 */
export default function DownloadButton({ jobId }) {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const handleDownload = async () => {
    setLoading(true)
    setError(null)
    try {
      const resp = await api.get(`/api/v1/report/${jobId}/pdf`, {
        responseType: 'blob',
      })
      const url = URL.createObjectURL(new Blob([resp.data], { type: 'application/pdf' }))
      const a = document.createElement('a')
      a.href = url
      a.download = `CloseCheck_${jobId.slice(0, 8)}.pdf`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
    } catch {
      setError('PDF not yet available.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <button className="cc-btn-sm" onClick={handleDownload} disabled={loading}>
        {loading ? 'Generating…' : 'Download Report PDF'}
      </button>
      {error && (
        <p style={{ fontSize: '11px', marginTop: '4px', color: '#A32D2D' }}>{error}</p>
      )}
    </div>
  )
}
