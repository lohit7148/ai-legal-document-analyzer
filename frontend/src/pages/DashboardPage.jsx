import React from 'react'
import { FileText, Type, ListChecks, ShieldAlert } from 'lucide-react'
import { useAnalysis } from '../context/AnalysisContext.jsx'
import { StatCard, SectionCard, EmptyState, RiskBadge, DetectionBadge, DisclaimerBanner } from '../components/Shared.jsx'

export default function DashboardPage({ onNavigate }) {
  const { result } = useAnalysis()

  if (!result) {
    return (
      <div className="max-w-5xl mx-auto space-y-4">
        <EmptyState />
      </div>
    )
  }

  const { document_stats, key_information, clauses, risk_indicators, summary, explanations } = result
  const detectedClauses = clauses.filter((c) => c.detected)

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard label="Words" value={document_stats.words.toLocaleString()} icon={Type} />
        <StatCard label="Sentences" value={document_stats.sentences.toLocaleString()} icon={FileText} />
        <StatCard label="Clauses Detected" value={`${detectedClauses.length} / ${clauses.length}`} icon={ListChecks} />
        <StatCard label="Potential Risks" value={risk_indicators.length} icon={ShieldAlert} />
      </div>

      <SectionCard title="Key Information" subtitle="Extracted from the submitted document">
        <dl className="grid sm:grid-cols-2 gap-x-8 gap-y-3 text-sm">
          <Field label="Parties" value={key_information.parties.length ? key_information.parties.join(', ') : null} />
          <Field label="Payment" value={key_information.payment_amounts.length ? key_information.payment_amounts.join(', ') : null} />
          <Field label="Contract Duration" value={key_information.contract_duration} />
          <Field label="Governing Law" value={key_information.governing_law} />
        </dl>
      </SectionCard>

      <SectionCard title="Detected Clauses" subtitle="Tap 'Clauses' in the sidebar for full details">
        <div className="flex flex-wrap gap-2">
          {clauses.map((c) => (
            <span
              key={c.clause_name}
              className={`text-xs font-medium px-2.5 py-1 rounded-full border ${
                c.detected
                  ? 'bg-indigo-50 text-indigo-700 border-indigo-200'
                  : 'bg-slate-50 text-slate-400 border-slate-200 line-through'
              }`}
            >
              {c.clause_name}
            </span>
          ))}
        </div>
      </SectionCard>

      <SectionCard title="Potential Risk Indicators" subtitle="Academic AI analysis — not a legal determination">
        {risk_indicators.length === 0 ? (
          <p className="text-sm text-slate-500">No potential risk indicators were detected.</p>
        ) : (
          <div className="space-y-2">
            {risk_indicators.slice(0, 5).map((r, i) => (
              <div key={i} className="flex items-center justify-between gap-3 text-sm border border-slate-100 rounded-lg px-3 py-2">
                <span className="text-slate-700">{r.category}</span>
                <RiskBadge level={r.level} />
              </div>
            ))}
          </div>
        )}
      </SectionCard>

      <SectionCard title="Document Summary">
        <p className="text-sm text-slate-600 leading-relaxed">{summary.overview}</p>
        <p className="text-sm text-slate-600 leading-relaxed mt-2">{summary.risk_overview}</p>
      </SectionCard>

      <SectionCard title="Simple English Explanations" subtitle={`${explanations.length} clause${explanations.length === 1 ? '' : 's'} explained`}>
        <div className="space-y-3">
          {explanations.slice(0, 3).map((e) => (
            <div key={e.clause_name} className="border border-slate-100 rounded-lg p-3">
              <p className="text-xs font-semibold text-indigo-600 uppercase tracking-wide">{e.clause_name}</p>
              <p className="text-sm text-slate-600 mt-1">{e.simple_english}</p>
            </div>
          ))}
        </div>
      </SectionCard>

      <DisclaimerBanner />
    </div>
  )
}

function Field({ label, value }) {
  return (
    <div>
      <dt className="text-xs font-medium text-slate-400">{label}</dt>
      <dd className="text-slate-700 mt-0.5">{value || 'Not specified in the document.'}</dd>
    </div>
  )
}
