import React, { useState } from 'react'
import { Search, Loader2, Info } from 'lucide-react'
import { useAnalysis } from '../context/AnalysisContext.jsx'
import { searchDocument, ApiError } from '../services/api.js'
import { EmptyState, ErrorBanner, SectionCard } from '../components/Shared.jsx'

const EXAMPLES = [
  'late payment penalty',
  'how can the contract be ended',
  'who owns the software',
  'keeping information secret',
  'what happens if there is a dispute',
]

export default function SearchPage() {
  const { result } = useAnalysis()
  const [query, setQuery] = useState('')
  const [topK, setTopK] = useState(5)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [response, setResponse] = useState(null)

  if (!result) {
    return (
      <div className="max-w-4xl mx-auto">
        <EmptyState />
      </div>
    )
  }

  if (!result.document_id || !result.search_index?.available) {
    return (
      <div className="max-w-4xl mx-auto">
        <EmptyState
          message="Semantic search is not available for this analysis."
          hint="The Legal-BERT index could not be built. Check the backend terminal and analyze the document again."
        />
      </div>
    )
  }

  async function runSearch(q) {
    const text = (q ?? query).trim()
    if (!text) return
    setQuery(text)
    setError(null)
    setLoading(true)
    try {
      setResponse(await searchDocument(result.document_id, text, topK))
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'The search failed.')
    } finally {
      setLoading(false)
    }
  }

  const maxSim = response && response.results.length ? Math.max(...response.results.map((r) => r.similarity)) : 1
  const minSim = response && response.results.length ? Math.min(...response.results.map((r) => r.similarity)) : 0

  return (
    <div className="max-w-4xl mx-auto space-y-4">
      <SectionCard
        title="Semantic search with Legal-BERT + FAISS"
        subtitle={`${result.search_index.passages} passages indexed · ${result.search_index.embedding_dim}-dimensional embeddings · ${result.search_index.backend}`}
      >
        <form
          onSubmit={(e) => { e.preventDefault(); runSearch() }}
          className="flex flex-col sm:flex-row gap-2"
        >
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            maxLength={500}
            placeholder="Describe what you are looking for, e.g. “late payment penalty”"
            className="flex-1 rounded-lg border border-slate-300 bg-slate-50 px-3.5 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400"
          />
          <select
            value={topK}
            onChange={(e) => setTopK(Number(e.target.value))}
            className="rounded-lg border border-slate-300 bg-white px-2 py-2 text-sm"
            aria-label="Number of results"
          >
            {[3, 5, 8, 10].map((n) => <option key={n} value={n}>Top {n}</option>)}
          </select>
          <button
            type="submit"
            disabled={loading || !query.trim()}
            className="inline-flex items-center justify-center gap-1.5 px-4 py-2 rounded-lg text-sm font-semibold text-white bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50"
          >
            {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Search className="w-4 h-4" />}
            Search
          </button>
        </form>

        <div className="flex flex-wrap gap-2 mt-3">
          {EXAMPLES.map((ex) => (
            <button
              key={ex}
              onClick={() => runSearch(ex)}
              disabled={loading}
              className="text-xs px-2.5 py-1 rounded-full border border-slate-200 text-slate-600 hover:bg-slate-50"
            >
              {ex}
            </button>
          ))}
        </div>
      </SectionCard>

      <ErrorBanner message={error} />

      {response && (
        <>
          <div className="flex items-start gap-2 bg-slate-50 border border-slate-200 rounded-lg px-4 py-3 text-xs text-slate-500 leading-relaxed">
            <Info className="w-4 h-4 mt-0.5 shrink-0" />
            <p>{response.similarity_note}</p>
          </div>

          {response.results.length === 0 ? (
            <p className="text-sm text-slate-500">No passages were returned.</p>
          ) : (
            response.results.map((hit) => {
              const span = maxSim - minSim || 1
              const width = 25 + 75 * ((hit.similarity - minSim) / span)
              return (
                <div key={hit.rank} className="bg-white rounded-xl border border-slate-200 p-4">
                  <div className="flex items-center justify-between gap-3 mb-2">
                    <p className="text-sm font-semibold text-slate-900">
                      Result {hit.rank}
                      <span className="ml-2 text-xs font-normal text-slate-400">
                        sentences {hit.sentence_start + 1}–{hit.sentence_end + 1}
                      </span>
                    </p>
                    <span className="text-xs font-mono text-indigo-700 bg-indigo-50 border border-indigo-100 rounded-full px-2 py-0.5">
                      cosine {hit.similarity.toFixed(3)}
                    </span>
                  </div>
                  <div className="h-1.5 rounded-full bg-slate-100 mb-3">
                    <div className="h-1.5 rounded-full bg-indigo-400" style={{ width: `${width}%` }} />
                  </div>
                  <p className="text-sm text-slate-700 leading-relaxed whitespace-pre-line">{hit.text}</p>
                </div>
              )
            })
          )}
        </>
      )}
    </div>
  )
}
