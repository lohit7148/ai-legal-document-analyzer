import React, { useState } from 'react'
import { ChevronDown, ChevronUp } from 'lucide-react'
import { useAnalysis } from '../context/AnalysisContext.jsx'
import { EmptyState, DetectionBadge } from '../components/Shared.jsx'

export default function ClausesPage() {
  const { result } = useAnalysis()
  const [openClause, setOpenClause] = useState(null)

  if (!result) {
    return (
      <div className="max-w-5xl mx-auto">
        <EmptyState />
      </div>
    )
  }

  const { clauses, explanations } = result
  const explanationByClause = Object.fromEntries(explanations.map((e) => [e.clause_name, e]))

  return (
    <div className="max-w-5xl mx-auto space-y-3">
      {clauses.map((clause) => {
        const isOpen = openClause === clause.clause_name
        const explanation = explanationByClause[clause.clause_name]

        return (
          <div key={clause.clause_name} className="bg-white rounded-xl border border-slate-200 overflow-hidden">
            <button
              onClick={() => setOpenClause(isOpen ? null : clause.clause_name)}
              className="w-full flex items-center justify-between gap-3 px-5 py-4 text-left"
            >
              <div className="min-w-0">
                <p className="text-sm font-semibold text-slate-900">{clause.clause_name}</p>
                {clause.detected_text && (
                  <p className="text-xs text-slate-500 mt-1 truncate max-w-2xl">{clause.detected_text}</p>
                )}
              </div>
              <div className="flex items-center gap-3 shrink-0">
                <DetectionBadge detected={clause.detected} />
                {isOpen ? <ChevronUp className="w-4 h-4 text-slate-400" /> : <ChevronDown className="w-4 h-4 text-slate-400" />}
              </div>
            </button>

            {isOpen && (
              <div className="px-5 pb-5 border-t border-slate-100 pt-4 space-y-3 text-sm">
                {clause.detected ? (
                  <>
                    <DetailRow label="Full Detected Text" value={clause.detected_text} />
                    <DetailRow label="Source Sentence" value={clause.source_sentence} />
                    <DetailRow label="Detection Indicator" value={clause.detection_indicator} />
                    {clause.position !== null && clause.position !== undefined && (
                      <DetailRow label="Position (sentence index)" value={String(clause.position)} />
                    )}
                    {explanation && (
                      <div className="bg-indigo-50 border border-indigo-100 rounded-lg p-3">
                        <p className="text-xs font-semibold text-indigo-700 mb-1">Explain in Simple English</p>
                        <p className="text-slate-700">{explanation.simple_english}</p>
                      </div>
                    )}
                  </>
                ) : (
                  <p className="text-slate-500">This clause type was not detected in the submitted document.</p>
                )}
                {clause.semantic_sentence && (
                  <div className="bg-slate-50 border border-slate-200 rounded-lg p-3">
                    <p className="text-xs font-semibold text-slate-600 mb-1">
                      Closest sentence by Legal-BERT similarity (cosine {clause.semantic_similarity.toFixed(3)})
                    </p>
                    <p className="text-slate-700">{clause.semantic_sentence}</p>
                    <p className="text-[11px] text-slate-400 mt-1.5 leading-relaxed">
                      Supplementary only: Legal-BERT is not fine-tuned for this, a closest sentence is shown even when the clause does not exist, and it does not change the Detected / Not Detected status.
                    </p>
                  </div>
                )}
              </div>
            )}
          </div>
        )
      })}
    </div>
  )
}

function DetailRow({ label, value }) {
  return (
    <div>
      <p className="text-xs font-medium text-slate-400">{label}</p>
      <p className="text-slate-700 mt-0.5">{value}</p>
    </div>
  )
}
