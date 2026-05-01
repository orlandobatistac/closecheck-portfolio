import { useEffect, useRef } from 'react'
import { Routes, Route, Navigate, useLocation } from 'react-router-dom'
import Upload from './pages/Upload'
import Processing from './pages/Processing'
import Report from './pages/Report'
import { trackPageView } from './utils/analytics'

function RouteAnalytics() {
  const location = useLocation()
  const hasTrackedInitialRef = useRef(false)

  useEffect(() => {
    if (!hasTrackedInitialRef.current) {
      hasTrackedInitialRef.current = true
      return
    }

    trackPageView(`${location.pathname}${location.search}${location.hash}`)
  }, [location.hash, location.pathname, location.search])

  return null
}

export default function App() {
  return (
    <div style={{ minHeight: '100vh', background: '#f0efe9' }}>
      <RouteAnalytics />
      <Routes>
        <Route path="/" element={<Upload />} />
        <Route path="/processing/:jobId" element={<Processing />} />
        <Route path="/report/:jobId" element={<Report />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </div>
  )
}
