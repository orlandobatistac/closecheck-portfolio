import { Routes, Route, Navigate } from 'react-router-dom'
import Upload from './pages/Upload'
import Processing from './pages/Processing'
import Report from './pages/Report'

export default function App() {
  return (
    <div style={{ minHeight: '100vh', background: '#f0efe9' }}>
      <Routes>
        <Route path="/" element={<Upload />} />
        <Route path="/processing/:jobId" element={<Processing />} />
        <Route path="/report/:jobId" element={<Report />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </div>
  )
}
