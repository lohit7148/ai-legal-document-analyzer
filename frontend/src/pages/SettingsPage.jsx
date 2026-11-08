import React, { useEffect, useState } from 'react'
import { SectionCard, DisclaimerBanner } from '../components/Shared.jsx'
import { useAnalysis } from '../context/AnalysisContext.jsx'
import { checkHealth } from '../services/api.js'
import { getVoiceSettings, saveVoiceSettings, speechSupport, useSpeechSynthesis } from '../hooks/useSpeech.js'

const LANGUAGES = [
  ['en-IN', 'English (India)'],
  ['en-US', 'English (US)'],
  ['en-GB', 'English (UK)'],
]

function Row({ label, children }) {
  return (
    <div className="flex justify-between gap-4 text-sm">
      <dt className="text-slate-500">{label}</dt>
      <dd className="text-slate-700 text-right">{children}</dd>
    </div>
  )
}

export default function SettingsPage() {
  const { result } = useAnalysis()
  const [voice, setVoice] = useState(getVoiceSettings())
  const [health, setHealth] = useState(null)
  const support = speechSupport()
  const { speak } = useSpeechSynthesis()

  useEffect(() => { checkHealth().then(setHealth) }, [])

  function update(patch) {
    const next = { ...voice, ...patch }
    setVoice(next)
    saveVoiceSettings(next)
  }

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <SectionCard title="About This Application">
        <p className="text-sm text-slate-600 leading-relaxed">
          AI-Powered Legal Document Analyzer (Stages 1–6): text, PDF and image input, Legal-BERT
          (<span className="font-medium">nlpaueb/legal-bert-base-uncased</span>) embeddings with FAISS semantic search,
          question answering, an extractive summary, transparent risk scoring and optional read-aloud. Clause detection,
          key information and risk indicators use transparent keyword and pattern logic; Legal-BERT supplies the
          embeddings used for search, key sentences and closest-sentence suggestions. An LLM is used only if you
          configure one.
        </p>
      </SectionCard>

      <SectionCard title="Model and services">
        <dl className="space-y-2">
          <Row label="Model name"><span className="font-mono">{result?.model?.name || 'nlpaueb/legal-bert-base-uncased'}</span></Row>
          <Row label="Device">{result?.model?.device || 'cpu'}</Row>
          <Row label="Vector index">{health?.reachable ? result?.search_index?.backend || 'built when a document is analyzed' : 'backend not reachable'}</Row>
          <Row label="OCR engine">{health?.reachable ? (health.ocr_available ? 'available' : 'not installed') : 'backend not reachable'}</Row>
          <Row label="LLM for Q&A / summary">
            {health?.reachable ? (health.llm_configured ? health.llm_provider : 'none (retrieval-only answers)') : 'backend not reachable'}
          </Row>
        </dl>
      </SectionCard>

      <SectionCard title="Read aloud (optional)" subtitle="Nothing is spoken unless you click a Listen button. Uses your browser's built-in voices.">
        <dl className="space-y-2 mb-4">
          <Row label="Read aloud">{support.synthesis ? 'supported' : 'not supported in this browser'}</Row>
        </dl>
        <div className="grid sm:grid-cols-2 gap-4 text-sm">
          <label className="block">
            <span className="text-slate-500">Language</span>
            <select value={voice.lang} onChange={(e) => update({ lang: e.target.value })}
              className="mt-1 w-full rounded-lg border border-slate-300 bg-white px-2 py-2">
              {LANGUAGES.map(([code, name]) => <option key={code} value={code}>{name}</option>)}
            </select>
          </label>
          <label className="block">
            <span className="text-slate-500">Speaking speed: {voice.rate.toFixed(1)}x</span>
            <input type="range" min="0.6" max="1.4" step="0.1" value={voice.rate}
              onChange={(e) => update({ rate: Number(e.target.value) })} className="mt-2 w-full" />
          </label>
        </div>
        {support.synthesis && (
          <button onClick={() => speak('This is a test of the voice output.')}
            className="mt-4 text-xs px-3 py-1.5 rounded-lg border border-slate-300 text-slate-600 hover:bg-slate-50">
            Test voice output
          </button>
        )}
      </SectionCard>

      <SectionCard title="Roadmap">
        <ul className="text-sm text-slate-600 space-y-1.5 list-disc list-inside">
          <li>Stage 1 (done): text input, clauses, key information, risk indicators</li>
          <li>Stage 2 (done): PDF and image upload with OCR</li>
          <li>Stage 3 (done): Legal-BERT embeddings + FAISS semantic search</li>
          <li>Stage 4 (done): question answering with retrieval (LLM optional)</li>
          <li>Stage 5 (done): key-sentence summary and transparent risk scoring</li>
          <li>Stage 6 (done): optional read-aloud (click Listen)</li>
          <li>Stage 7: Raspberry Pi camera and touchscreen deployment (Pi currently used as a display)</li>
        </ul>
      </SectionCard>

      <DisclaimerBanner />
    </div>
  )
}
