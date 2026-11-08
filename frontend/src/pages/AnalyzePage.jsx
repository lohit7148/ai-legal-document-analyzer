import React, { useRef, useState } from 'react'
import { Loader2, Eraser, Sparkles, UploadCloud, FileText, Info } from 'lucide-react'
import { useAnalysis } from '../context/AnalysisContext.jsx'
import { ErrorBanner } from '../components/Shared.jsx'
import { extractText, ApiError } from '../services/api.js'

const ACCEPT = '.pdf,.png,.jpg,.jpeg,.bmp,.tif,.tiff,.webp'

function countStats(text) {
  const words = (text.match(/\S+/g) || []).length
  const characters = text.length
  const sentences = (text.match(/[.!?]+(\s|$)/g) || []).length
  return { words, characters, sentences }
}

const METHOD_LABEL = {
  'text-layer': 'text layer of the PDF',
  ocr: 'OCR (text recognition)',
  'text-layer+ocr': 'PDF text layer + OCR for scanned pages',
}

export default function AnalyzePage({ onAnalyzed }) {
  const { documentText, setDocumentText, isAnalyzing, loadingStage, error, runAnalysis } = useAnalysis()
  const stats = countStats(documentText)

  const fileInput = useRef(null)
  const [dragging, setDragging] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [uploadError, setUploadError] = useState(null)
  const [extraction, setExtraction] = useState(null)

  async function handleAnalyze() {
    try {
      await runAnalysis(documentText)
      onAnalyzed && onAnalyzed()
    } catch {
      // error is already captured in context state and shown below
    }
  }

  async function handleFile(file) {
    if (!file) return
    setUploadError(null)
    setExtraction(null)
    setUploading(true)
    try {
      const data = await extractText(file)
      setDocumentText(data.text)
      setExtraction(data)
    } catch (err) {
      setUploadError(err instanceof ApiError ? err.message : 'The file could not be processed.')
    } finally {
      setUploading(false)
      if (fileInput.current) fileInput.current.value = ''
    }
  }

  function onDrop(e) {
    e.preventDefault()
    setDragging(false)
    handleFile(e.dataTransfer.files && e.dataTransfer.files[0])
  }

  return (
    <div className="max-w-4xl mx-auto space-y-4">
      <ErrorBanner message={error} />

      {/* Stage 2: upload */}
      <div
        onDragOver={(e) => { e.preventDefault(); setDragging(true) }}
        onDragLeave={() => setDragging(false)}
        onDrop={onDrop}
        className={`bg-white rounded-xl border-2 border-dashed p-5 flex flex-col sm:flex-row items-center gap-4 transition-colors ${
          dragging ? 'border-indigo-400 bg-indigo-50' : 'border-slate-300'
        }`}
      >
        <div className="w-11 h-11 rounded-lg bg-indigo-50 flex items-center justify-center shrink-0">
          {uploading ? <Loader2 className="w-5 h-5 text-indigo-600 animate-spin" /> : <UploadCloud className="w-5 h-5 text-indigo-600" />}
        </div>
        <div className="flex-1 text-center sm:text-left">
          <p className="text-sm font-semibold text-slate-900">Upload a PDF or an image of a document</p>
          <p className="text-xs text-slate-500 mt-0.5">
            PDF, PNG, JPG, TIFF, WEBP (up to 15 MB). Scanned pages and photos are read with OCR.
          </p>
        </div>
        <input ref={fileInput} type="file" accept={ACCEPT} className="hidden" onChange={(e) => handleFile(e.target.files[0])} />
        <button
          onClick={() => fileInput.current && fileInput.current.click()}
          disabled={uploading || isAnalyzing}
          className="inline-flex items-center gap-1.5 px-4 py-2 rounded-lg text-sm font-semibold text-indigo-700 bg-indigo-50 border border-indigo-200 hover:bg-indigo-100 disabled:opacity-50"
        >
          <FileText className="w-4 h-4" />
          {uploading ? 'Reading file...' : 'Choose file'}
        </button>
      </div>

      <ErrorBanner message={uploadError} />

      {extraction && (
        <div className="bg-emerald-50 border border-emerald-200 rounded-lg px-4 py-3 text-sm text-emerald-800 space-y-1">
          <p>
            <span className="font-semibold">{extraction.filename}</span>: extracted{' '}
            {extraction.characters.toLocaleString()} characters from {extraction.pages} page
            {extraction.pages === 1 ? '' : 's'} using {METHOD_LABEL[extraction.method] || extraction.method}.
            The text is in the editor below. Review it, then click Analyze Document.
          </p>
          {extraction.warnings.map((w, i) => (
            <p key={i} className="flex items-start gap-1.5 text-amber-700">
              <Info className="w-4 h-4 mt-0.5 shrink-0" /> {w}
            </p>
          ))}
        </div>
      )}

      <div className="bg-white rounded-xl border border-slate-200 p-5">
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-sm font-semibold text-slate-900">Paste, type or review your legal document below</h2>
          <span className="text-xs text-slate-400">Text, PDF or image</span>
        </div>

        <textarea
          value={documentText}
          onChange={(e) => setDocumentText(e.target.value)}
          placeholder="Paste your legal document here..."
          className="w-full h-80 md:h-96 resize-y rounded-lg border border-slate-300 bg-slate-50 p-4 text-sm text-slate-800 leading-relaxed focus:outline-none focus:ring-2 focus:ring-indigo-400 focus:border-indigo-400"
        />

        <div className="flex flex-wrap items-center justify-between gap-3 mt-3">
          <div className="text-xs text-slate-500 flex gap-4">
            <span>Words: <span className="font-semibold text-slate-700">{stats.words}</span></span>
            <span>Characters: <span className="font-semibold text-slate-700">{stats.characters}</span></span>
            <span>Sentences: <span className="font-semibold text-slate-700">{stats.sentences}</span></span>
          </div>

          <div className="flex gap-2">
            <button
              onClick={() => { setDocumentText(''); setExtraction(null); setUploadError(null) }}
              disabled={isAnalyzing || !documentText}
              className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-lg text-sm font-medium text-slate-600 border border-slate-300 hover:bg-slate-50 disabled:opacity-40 disabled:cursor-not-allowed"
            >
              <Eraser className="w-4 h-4" />
              Clear
            </button>
            <button
              onClick={handleAnalyze}
              disabled={isAnalyzing || uploading || documentText.trim().length < 20}
              className="inline-flex items-center gap-1.5 px-4 py-2 rounded-lg text-sm font-semibold text-white bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isAnalyzing ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Analyzing...
                </>
              ) : (
                <>
                  <Sparkles className="w-4 h-4" />
                  Analyze Document
                </>
              )}
            </button>
          </div>
        </div>

        {isAnalyzing && (
          <div className="mt-4 flex items-center gap-2 text-sm text-indigo-600 bg-indigo-50 border border-indigo-100 rounded-lg px-4 py-2.5">
            <Loader2 className="w-4 h-4 animate-spin" />
            {loadingStage}
          </div>
        )}
      </div>
    </div>
  )
}
