import axios from 'axios'

// Persist a stable device token in localStorage so the server can fingerprint
// this browser session across page reloads and IP changes.
if (!localStorage.getItem('cc_device_token')) {
  localStorage.setItem('cc_device_token', crypto.randomUUID())
}

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
  headers: {
    'X-API-Key': import.meta.env.VITE_API_KEY || 'dev-key',
  },
})

// Attach the device token to every request so the backend can fingerprint it.
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('cc_device_token')
  if (token) {
    config.headers['X-Device-Token'] = token
  }
  return config
})

/**
 * Submit a closing package for validation.
 * @param {File[]} files
 * @param {string} transactionType
 * @returns {Promise<{job_id: string, status: string, created_at: string}>}
 */
export async function submitValidation(files, transactionType = 'residential') {
  const form = new FormData()
  files.forEach((file) => form.append('files', file))
  form.append('transaction_type', transactionType)

  const { data } = await api.post('/api/v1/validate', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return data
}

/**
 * Poll job status and results.
 * @param {string} jobId
 */
export async function getResults(jobId) {
  const { data } = await api.get(`/api/v1/results/${jobId}`)
  return data
}

/**
 * Draft an email for a specific conflict.
 * @param {string} jobId
 * @param {string} conflictRuleId
 * @param {string} recipient
 * @returns {Promise<{subject_pro, body_pro, subject_urg, body_urg}>}
 */
export async function draftEmail(jobId, conflictRuleId, recipient = 'lender') {
  const { data } = await api.post(`/api/v1/jobs/${jobId}/draft-email`, {
    conflict_rule_id: conflictRuleId,
    recipient,
  })
  return data
}

export async function submitDemo() {
  const { data } = await api.post('/api/v1/demo')
  return data
}

/**
 * Returns the URL to stream an original uploaded file (for the PDF viewer).
 * @param {string} jobId
 * @param {string} filename
 */
export function getJobFileUrl(jobId, filename) {
  const base = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
  return `${base}/api/v1/jobs/${encodeURIComponent(jobId)}/files/${encodeURIComponent(filename)}`
}

export default api
