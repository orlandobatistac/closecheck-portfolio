import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
  headers: {
    'X-API-Key': import.meta.env.VITE_API_KEY || 'dev-key',
  },
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

export default api
