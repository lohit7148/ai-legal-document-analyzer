import React, { useEffect, useState } from 'react'
import { MessageSquare, Loader2, Info, Send } from 'lucide-react'
import { useAnalysis } from '../context/AnalysisContext.jsx'
import { askQuestion, ApiError } from '../services/api.js'
import { EmptyState, ErrorBanner, SectionCard } from '../components/Shared.jsx'
import { SpeakButton } from '../components/VoiceControls.jsx'

const EXAMPLES = [
  'What is the late payment penalty?',
  'How can the contract be ended?',
  'Who owns the software?',
  'How long is the notice period?',
]

export default function AskPage() {
  const { result } = useAnalysis()
  const [question, setQuestion] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [response, setResponse] = useState(null)

  // a new document means the old answer no longer applies
  useEffect(() => { setResponse(null); setError(null) }, [result?.document_id])

  if (!result) {
    return <div className="max-w-4xl mx-auto"><EmptyState /></div>
  }
  if (!result.document_id || !result.search_index?.available) {
    return (
      <div className="max-w-4xl mx-auto">
        <EmptyState
          message="Questions are not available for this analysis."
          hint="The Legal-BERT index could not be built. Check the backend terminal and analyze the document again."
        />
      </div>
    )
  }

  async function ask(q) {
    const text = (q ?? question).trim()
    if (!text) return
    setQuestion(text)
    setError(null)
    setLoading(true)
    try {
      const data = await askQuestion(result.document_id, text)
      setResponse(data)
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'The question could not be answered.')
    } finally {
      setLoading(false)
    }
  }

  const isLlm = response?.mode === 'llm'

  return (
    <div className="max-w-4xl mx-auto space-y-4">
      <SectionCard
        title="Ask a question about this document"
        subtitle="Legal-BERT + FAISS find the relevant passages. An LLM writes the answer only if one is configured."
      >
        <form onSubmit={(e) => { e.preventDefault(); ask() }} className="flex flex-col sm:flex-row gap-2">
          <input
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            maxLength={500}
            placeholder="Type a question, e.g. “How can the contract be ended?”"
            className="flex-1 rounded-lg border border-slate-300 bg-slate-50 px-3.5 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400"
          />
          <button
            type="submit"
            disabled={loading || !question.trim()}
            className="inline-flex items-center justify-center gap-1.5 px-4 py-2 rounded-lg text-sm font-semibold text-white bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50"
          >
            {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
            Ask
          </button>
        </form>
        <div className="flex flex-wrap gap-2 mt-3">
          {EXAMPLES.map((ex) => (
            <button key={ex} onClick={() => ask(ex)} disabled={loading}
              className="text-xs px-2.5 py-1 rounded-full border border-slate-200 text-slate-600 hover:bg-slate-50">
              {ex}
            </button>
          ))}
        </div>
      </SectionCard>

      <ErrorBanner message={error} />

      {response && (
        <>
          <div className="bg-white rounded-xl border border-slate-200 p-5">
            <div className="flex items-center justify-between gap-3 mb-2">
              <div className="flex items-center gap-2">
                <MessageSquare className="w-4 h-4 text-indigo-600" />
                <p className="text-sm font-semibold text-slate-900">{isLlm ? 'Answer' : 'Closest sentence found'}</p>
                <span className={`text-[11px] font-semibold px-2 py-0.5 rounded-full border ${isLlm ? 'bg-indigo-50 text-indigo-700 border-indigo-200' : 'bg-slate-100 text-slate-600 border-slate-200'}`}>
                  {isLlm ? `LLM · ${response.provider}` : 'Retrieval only'}
                </span>
              </div>
              <SpeakButton text={response.answer} label="Read aloud" />
            </div>
            <p className="text-sm text-slate-800 leading-relaxed whitespace-pre-line">{response.answer}</p>
          </div>

          <div className="flex items-start gap-2 bg-slate-50 border border-slate-200 rounded-lg px-4 py-3 text-xs text-slate-500 leading-relaxed">
            <Info className="w-4 h-4 mt-0.5 shrink-0" />
            <p>{response.note}</p>
          </div>

          <SectionCard title="Source passages" subtitle="The answer comes only from these passages of your document">
            <div className="space-y-3">
              {response.sources.map((s, i) => (
                <div key={s.rank} className="border border-slate-100 rounded-lg p-3">
                  <div className="flex justify-between text-xs text-slate-400 mb-1">
                    <span>[{i + 1}] sentences {s.sentence_start + 1}–{s.sentence_end + 1}</span>
                    <span className="font-mono">cosine {s.similarity.toFixed(3)}</span>
                  </div>
                  <p className="text-sm text-slate-700 leading-relaxed whitespace-pre-line">{s.text}</p>
                </div>
              ))}
            </div>
          </SectionCard>
        </>
      )}
    </div>
  )
}
