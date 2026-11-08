import React, { useEffect, useState } from 'react'
import { Loader2, Sparkles } from 'lucide-react'
import { useAnalysis } from '../context/AnalysisContext.jsx'
import { aiSummary, ApiError } from '../services/api.js'
import { SectionCard, EmptyState, DisclaimerBanner, ErrorBanner } from '../components/Shared.jsx'
import { SpeakButton } from '../components/VoiceControls.jsx'

const ROWS = [
  ['overview', 'Overview'],
  ['parties', 'Parties'],
  ['main_purpose', 'Main Purpose'],
  ['services', 'Services'],
  ['payment', 'Payment'],
  ['contract_duration', 'Contract Duration'],
  ['termination', 'Termination'],
  ['renewal', 'Renewal'],
  ['important_obligations', 'Important Obligations'],
  ['governing_law', 'Governing Law'],
  ['risk_overview', 'Potential Risk Indicators'],
]

export default function SummaryPage() {
  const { result } = useAnalysis()
  const [ai, setAi] = useState(null)
  const [aiLoading, setAiLoading] = useState(false)
  const [aiError, setAiError] = useState(null)

  useEffect(() => { setAi(null); setAiError(null) }, [result?.document_id])

  if (!result) {
    return <div className="max-w-4xl mx-auto"><EmptyState /></div>
  }

  const s = result.summary
  const keySentences = result.key_sentences || []
  const spoken = ROWS.map(([key, label]) => `${label}. ${s[key]}`).join(' ')

  async function loadAiSummary() {
    setAiError(null)
    setAiLoading(true)
    try {
      setAi(await aiSummary(result.document_id))
    } catch (err) {
      setAiError(err instanceof ApiError ? err.message : 'The summary could not be created.')
    } finally {
      setAiLoading(false)
    }
  }

  return (
    <div className="max-w-4xl mx-auto space-y-4">
      <SectionCard title="Document Summary" subtitle="Generated from the submitted document">
        <div className="mb-2"><SpeakButton text={spoken} label="Read summary aloud" /></div>
        <div className="divide-y divide-slate-100">
          {ROWS.map(([key, label]) => (
            <div key={key} className="py-3 grid sm:grid-cols-[180px_1fr] gap-1 sm:gap-4">
              <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide">{label}</p>
              <p className="text-sm text-slate-700 leading-relaxed">{s[key]}</p>
            </div>
          ))}
        </div>
      </SectionCard>

      {keySentences.length > 0 && (
        <SectionCard
          title="Key sentences (Legal-BERT extractive summary)"
          subtitle="Real sentences from your document, chosen by embedding similarity to the document as a whole, without repeating each other"
        >
          <ol className="space-y-2 list-decimal list-inside">
            {keySentences.map((k) => (
              <li key={k.sentence_index} className="text-sm text-slate-700 leading-relaxed">
                {k.text}
                <span className="ml-2 text-xs text-slate-400 font-mono">sentence {k.sentence_index + 1} · centrality {k.centrality.toFixed(3)}</span>
              </li>
            ))}
          </ol>
          <div className="mt-3"><SpeakButton text={keySentences.map((k) => k.text).join(' ')} label="Read key sentences" /></div>
        </SectionCard>
      )}

      {result.document_id && (
        <SectionCard title="Plain-English summary" subtitle="Written by an LLM if one is configured; otherwise the key sentences above are shown">
          <button
            onClick={loadAiSummary}
            disabled={aiLoading}
            className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-lg text-sm font-semibold text-white bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50"
          >
            {aiLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />}
            Create plain-English summary
          </button>
          <div className="mt-3"><ErrorBanner message={aiError} /></div>
          {ai && (
            <div className="mt-3 space-y-2">
              <div className="flex items-center justify-between gap-3">
                <span className="text-[11px] font-semibold px-2 py-0.5 rounded-full border bg-slate-100 text-slate-600 border-slate-200">
                  {ai.mode === 'llm' ? `LLM · ${ai.provider}` : 'Extractive'}
                </span>
                <SpeakButton text={ai.text} label="Read aloud" />
              </div>
              <p className="text-sm text-slate-700 leading-relaxed">{ai.text}</p>
              {ai.note && <p className="text-xs text-slate-500">{ai.note}</p>}
            </div>
          )}
        </SectionCard>
      )}

      <SectionCard title="Simple English Explanations">
        <div className="space-y-3">
          {result.explanations.map((e) => (
            <div key={e.clause_name} className="border border-slate-100 rounded-lg p-4">
              <p className="text-xs font-semibold text-indigo-600 uppercase tracking-wide mb-1">{e.clause_name}</p>
              <p className="text-sm text-slate-500 italic mb-2">"{e.legal_text}"</p>
              <p className="text-sm text-slate-700">{e.simple_english}</p>
            </div>
          ))}
        </div>
      </SectionCard>

      <DisclaimerBanner />
    </div>
  )
}
