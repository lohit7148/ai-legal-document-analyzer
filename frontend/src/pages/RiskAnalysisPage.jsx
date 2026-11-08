import React from 'react'
import { useAnalysis } from '../context/AnalysisContext.jsx'
import { StatCard, SectionCard, EmptyState, RiskBadge } from '../components/Shared.jsx'

export default function RiskAnalysisPage() {
  const { result } = useAnalysis()

  if (!result) {
    return (
      <div className="max-w-5xl mx-auto">
        <EmptyState />
      </div>
    )
  }

  const { risk_indicators, risk_score } = result
  const counts = { HIGH: 0, MEDIUM: 0, LOW: 0 }
  risk_indicators.forEach((r) => (counts[r.level] = (counts[r.level] || 0) + 1))

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      <div className="grid grid-cols-3 gap-4">
        <StatCard label="High" value={counts.HIGH} />
        <StatCard label="Medium" value={counts.MEDIUM} />
        <StatCard label="Low" value={counts.LOW} />
      </div>

      {risk_score && (
        <SectionCard
          title="Overall risk score"
          subtitle="Transparent point count from the indicators below, not a legal determination"
        >
          <div className="flex items-center gap-4 mb-3">
            <p className="text-3xl font-semibold text-slate-900">{risk_score.score}<span className="text-base text-slate-400"> / 100</span></p>
            <RiskBadge level={risk_score.level} />
          </div>
          <div className="h-2 rounded-full bg-slate-100 mb-3">
            <div className="h-2 rounded-full bg-indigo-500" style={{ width: `${risk_score.score}%` }} />
          </div>
          <ul className="text-sm text-slate-600 space-y-1">
            {risk_score.components.map((c, i) => (
              <li key={i} className="flex justify-between gap-3"><span>{c.name}{c.detail ? ` (${c.detail})` : ''}</span><span className="font-mono">+{c.points}</span></li>
            ))}
          </ul>
          <p className="text-xs text-slate-400 mt-3 leading-relaxed">How it is calculated: {risk_score.formula}</p>
          {risk_score.missing_clause_checks.length > 0 && (
            <div className="mt-3 bg-amber-50 border border-amber-200 rounded-lg px-3 py-2 text-xs text-amber-800 leading-relaxed">
              Potentially missing clause types: {risk_score.missing_clause_checks.join(', ')}. A keyword search found nothing, which does not prove the clause is absent. Check the document.
            </div>
          )}
        </SectionCard>
      )}

      <SectionCard
        title="Potential Risk Indicators"
        subtitle="Transparent keyword and pattern flags — this is an academic AI analysis tool, not a legal risk determination"
      >
        {risk_indicators.length === 0 ? (
          <p className="text-sm text-slate-500">No potential risk indicators were detected in this document.</p>
        ) : (
          <div className="space-y-3">
            {risk_indicators.map((r, i) => (
              <div key={i} className="border border-slate-100 rounded-lg p-4">
                <div className="flex items-center justify-between gap-3 mb-2">
                  <p className="text-sm font-semibold text-slate-900">{r.category}</p>
                  <RiskBadge level={r.level} />
                </div>
                <p className="text-sm text-slate-600 mb-2">{r.reason}</p>
                <p className="text-xs text-slate-400">
                  Evidence keyword: <span className="font-mono text-slate-500">"{r.evidence}"</span>
                </p>
                <blockquote className="mt-2 text-sm text-slate-700 bg-slate-50 border-l-2 border-slate-300 pl-3 py-1.5 italic">
                  {r.source_text}
                </blockquote>
              </div>
            ))}
          </div>
        )}
      </SectionCard>
    </div>
  )
}
