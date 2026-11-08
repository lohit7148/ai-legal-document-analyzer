import React, { createContext, useContext, useState, useCallback } from 'react'
import { analyzeDocument, ApiError } from '../services/api.js'

const AnalysisContext = createContext(null)

const LOADING_STAGES = [
  'Analyzing document...',
  'Processing with Legal-BERT...',
  'Extracting legal clauses...',
  'Preparing results...',
]

export function AnalysisProvider({ children }) {
  const [documentText, setDocumentText] = useState('')
  const [result, setResult] = useState(null)
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [loadingStage, setLoadingStage] = useState('')
  const [error, setError] = useState(null)

  const runAnalysis = useCallback(async (text) => {
    setError(null)
    setIsAnalyzing(true)

    // Real UI loading states (not fake delays) -- we step through the
    // stage labels while the single API call is in flight so the user
    // sees meaningful progress text, then the backend response replaces
    // it as soon as it arrives.
    let stageIndex = 0
    setLoadingStage(LOADING_STAGES[0])
    const interval = setInterval(() => {
      stageIndex = Math.min(stageIndex + 1, LOADING_STAGES.length - 1)
      setLoadingStage(LOADING_STAGES[stageIndex])
    }, 700)

    try {
      const data = await analyzeDocument(text)
      setResult(data)
      return data
    } catch (err) {
      const message = err instanceof ApiError ? err.message : 'An unexpected error occurred.'
      setError(message)
      throw err
    } finally {
      clearInterval(interval)
      setIsAnalyzing(false)
      setLoadingStage('')
    }
  }, [])

  const value = {
    documentText,
    setDocumentText,
    result,
    isAnalyzing,
    loadingStage,
    error,
    setError,
    runAnalysis,
  }

  return <AnalysisContext.Provider value={value}>{children}</AnalysisContext.Provider>
}

export function useAnalysis() {
  const ctx = useContext(AnalysisContext)
  if (!ctx) throw new Error('useAnalysis must be used within an AnalysisProvider')
  return ctx
}
