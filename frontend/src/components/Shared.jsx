import React from 'react'
import { FileSearch, AlertTriangle } from 'lucide-react'

export function StatCard({ label, value, icon: Icon }) {
  return (
    <div className="bg-white rounded-xl border border-slate-200 p-4 flex items-center gap-3">
      {Icon && (
        <div className="w-10 h-10 rounded-lg bg-indigo-50 flex items-center justify-center shrink-0">
          <Icon className="w-5 h-5 text-indigo-600" />
        </div>
      )}
      <div className="min-w-0">
        <p className="text-xs font-medium text-slate-500 truncate">{label}</p>
        <p className="text-xl font-semibold text-slate-900 truncate">{value}</p>
      </div>
    </div>
  )
}

export function SectionCard({ title, subtitle, children, className = '' }) {
  return (
    <div className={`bg-white rounded-xl border border-slate-200 p-5 ${className}`}>
      {title && (
        <div className="mb-4">
          <h2 className="text-sm font-semibold text-slate-900">{title}</h2>
          {subtitle && <p className="text-xs text-slate-500 mt-0.5">{subtitle}</p>}
        </div>
      )}
      {children}
    </div>
  )
}

export function EmptyState({ message = 'No document analyzed yet.', hint = 'Go to "Analyze Document" to get started.' }) {
  return (
    <div className="bg-white rounded-xl border border-dashed border-slate-300 p-10 flex flex-col items-center text-center gap-3">
      <div className="w-12 h-12 rounded-full bg-slate-100 flex items-center justify-center">
        <FileSearch className="w-6 h-6 text-slate-400" />
      </div>
      <p className="text-sm font-medium text-slate-700">{message}</p>
      <p className="text-xs text-slate-500">{hint}</p>
    </div>
  )
}

export function ErrorBanner({ message }) {
  if (!message) return null
  return (
    <div className="flex items-start gap-2.5 bg-red-50 border border-red-200 text-red-700 text-sm rounded-lg px-4 py-3">
      <AlertTriangle className="w-4 h-4 mt-0.5 shrink-0" />
      <p>{message}</p>
    </div>
  )
}

const RISK_STYLES = {
  HIGH: 'bg-red-50 text-red-700 border-red-200',
  MEDIUM: 'bg-amber-50 text-amber-700 border-amber-200',
  LOW: 'bg-emerald-50 text-emerald-700 border-emerald-200',
}

export function RiskBadge({ level }) {
  const cls = RISK_STYLES[level] || 'bg-slate-100 text-slate-600 border-slate-200'
  return (
    <span className={`text-[11px] font-semibold px-2 py-0.5 rounded-full border ${cls}`}>
      {level}
    </span>
  )
}

export function DetectionBadge({ detected }) {
  return detected ? (
    <span className="text-[11px] font-semibold px-2 py-0.5 rounded-full border bg-indigo-50 text-indigo-700 border-indigo-200">
      Detected
    </span>
  ) : (
    <span className="text-[11px] font-semibold px-2 py-0.5 rounded-full border bg-slate-100 text-slate-500 border-slate-200">
      Not Detected
    </span>
  )
}

export function DisclaimerBanner() {
  return (
    <div className="bg-slate-50 border border-slate-200 rounded-lg px-4 py-3 text-xs text-slate-500 leading-relaxed">
      <span className="font-semibold text-slate-600">Disclaimer: </span>
      AI-generated analysis for informational purposes only. This system does not provide
      legal advice. Consult a qualified legal professional for legal decisions.
    </div>
  )
}
