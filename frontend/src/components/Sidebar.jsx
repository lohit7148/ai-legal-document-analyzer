import React from 'react'
import {
  LayoutDashboard,
  FileSearch,
  Info,
  ListChecks,
  ShieldAlert,
  FileText,
  Search,
  MessageSquare,
  Settings as SettingsIcon,
  Scale,
} from 'lucide-react'

const NAV_ITEMS = [
  { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { id: 'analyze', label: 'Analyze Document', icon: FileSearch },
  { id: 'key-information', label: 'Key Information', icon: Info },
  { id: 'clauses', label: 'Clauses', icon: ListChecks },
  { id: 'risk-analysis', label: 'Risk Analysis', icon: ShieldAlert },
  { id: 'semantic-search', label: 'Semantic Search', icon: Search },
  { id: 'ask', label: 'Ask Questions', icon: MessageSquare },
  { id: 'summary', label: 'Summary', icon: FileText },
  { id: 'settings', label: 'Settings', icon: SettingsIcon },
]

export default function Sidebar({ activePage, onNavigate }) {
  return (
    <aside className="hidden md:flex md:flex-col md:w-64 shrink-0 bg-navy-950 text-slate-200 min-h-screen">
      <div className="flex items-center gap-2 px-6 py-6 border-b border-white/10">
        <div className="w-9 h-9 rounded-lg bg-indigo-500/20 flex items-center justify-center">
          <Scale className="w-5 h-5 text-indigo-400" />
        </div>
        <div>
          <p className="font-semibold text-white leading-tight">AI Legal Analyzer</p>
          <p className="text-[11px] text-slate-400 leading-tight">Stage 6 · Legal-BERT</p>
        </div>
      </div>

      <nav className="flex-1 px-3 py-4 space-y-1">
        {NAV_ITEMS.map(({ id, label, icon: Icon }) => {
          const active = activePage === id
          return (
            <button
              key={id}
              onClick={() => onNavigate(id)}
              className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors
                ${active
                  ? 'bg-indigo-500/15 text-indigo-300 border border-indigo-500/30'
                  : 'text-slate-300 hover:bg-white/5 hover:text-white border border-transparent'}`}
            >
              <Icon className="w-4 h-4 shrink-0" />
              <span className="truncate">{label}</span>
            </button>
          )
        })}
      </nav>

      <div className="px-4 py-4 border-t border-white/10 text-[11px] text-slate-500 leading-relaxed">
        AI-generated analysis for informational purposes only. Not legal advice.
      </div>
    </aside>
  )
}
