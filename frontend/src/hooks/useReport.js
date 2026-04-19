import { useState, useEffect } from 'react'
import { getResults } from '../api/client'

/**
 * Fetch a completed report once. Does not poll — job must already be completed.
 */
export function useReport(jobId) {
  const [report, setReport] = useState(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    if (!jobId) return
    setIsLoading(true)
    getResults(jobId)
      .then((data) => {
        setReport(data)
        setIsLoading(false)
      })
      .catch((err) => {
        setError(err.message || 'Failed to load report')
        setIsLoading(false)
      })
  }, [jobId])

  return { report, isLoading, error }
}
