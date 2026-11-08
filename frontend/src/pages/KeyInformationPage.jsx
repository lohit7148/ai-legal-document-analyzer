import React from 'react'
import { useAnalysis } from '../context/AnalysisContext.jsx'
import { SectionCard, EmptyState } from '../components/Shared.jsx'

const NOT_SPECIFIED = 'Not specified in the document.'

function Field({ label, value }) {
  return (
    <div className="border border-slate-100 rounded-lg p-3">
      <p className="text-xs font-medium text-slate-400">{label}</p>
      <p className="text-sm text-slate-700 mt-1 break-words">{value || NOT_SPECIFIED}</p>
    </div>
  )
}

function ListField({ label, values }) {
  return (
    <div className="border border-slate-100 rounded-lg p-3">
      <p className="text-xs font-medium text-slate-400">{label}</p>
      {values && values.length ? (
        <ul className="mt-1 space-y-1">
          {values.map((v, i) => (
            <li key={i} className="text-sm text-slate-700">{v}</li>
          ))}
        </ul>
      ) : (
        <p className="text-sm text-slate-700 mt-1">{NOT_SPECIFIED}</p>
      )}
    </div>
  )
}

export default function KeyInformationPage() {
  const { result } = useAnalysis()

  if (!result) {
    return (
      <div className="max-w-5xl mx-auto">
        <EmptyState />
      </div>
    )
  }

  const k = result.key_information

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      <SectionCard title="Parties">
        <ListField label="Identified Parties" values={k.parties} />
      </SectionCard>

      <SectionCard title="Dates">
        <div className="grid sm:grid-cols-2 gap-3">
          <Field label="Effective Date" value={k.effective_date} />
          <Field label="Expiration Date" value={k.expiration_date} />
        </div>
        <div className="mt-3">
          <ListField label="Other Dates Mentioned" values={k.other_dates} />
        </div>
      </SectionCard>

      <SectionCard title="Financial Information">
        <div className="grid sm:grid-cols-2 gap-3">
          <ListField label="Payment Amounts" values={k.payment_amounts} />
          <ListField label="Percentages Referenced" values={k.percentages} />
        </div>
        <div className="mt-3">
          <ListField label="Penalty Clauses" values={k.penalties} />
        </div>
      </SectionCard>

      <SectionCard title="Contract Information">
        <div className="grid sm:grid-cols-2 gap-3">
          <Field label="Duration" value={k.contract_duration} />
          <Field label="Termination Notice" value={k.termination_notice} />
        </div>
        <div className="mt-3">
          <Field label="Renewal" value={k.renewal} />
        </div>
      </SectionCard>

      <SectionCard title="Legal Information">
        <div className="grid sm:grid-cols-2 gap-3">
          <Field label="Governing Law" value={k.governing_law} />
          <Field label="Jurisdiction" value={k.jurisdiction} />
        </div>
        <div className="mt-3">
          <Field label="Dispute Resolution" value={k.dispute_resolution} />
        </div>
      </SectionCard>
    </div>
  )
}
