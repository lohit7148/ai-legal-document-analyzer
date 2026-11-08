import React, { useState } from 'react'
import Sidebar from './components/Sidebar.jsx'
import Header from './components/Header.jsx'
import { AnalysisProvider } from './context/AnalysisContext.jsx'

import DashboardPage from './pages/DashboardPage.jsx'
import AnalyzePage from './pages/AnalyzePage.jsx'
import KeyInformationPage from './pages/KeyInformationPage.jsx'
import ClausesPage from './pages/ClausesPage.jsx'
import RiskAnalysisPage from './pages/RiskAnalysisPage.jsx'
import SearchPage from './pages/SearchPage.jsx'
import AskPage from './pages/AskPage.jsx'
import SummaryPage from './pages/SummaryPage.jsx'
import SettingsPage from './pages/SettingsPage.jsx'

const PAGE_META = {
  dashboard: { title: 'Dashboard', subtitle: 'Document overview at a glance' },
  analyze: { title: 'AI-Powered Legal Document Analyzer', subtitle: 'Analyze legal documents using Legal-BERT' },
  'key-information': { title: 'Key Information', subtitle: 'Parties, dates, financials, and legal terms' },
  clauses: { title: 'Clause Explorer', subtitle: 'All 14 clause types checked against your document' },
  'risk-analysis': { title: 'Risk Analysis', subtitle: 'Potential risk indicators — not a legal determination' },
  'semantic-search': { title: 'Semantic Search', subtitle: 'Find passages by meaning using Legal-BERT embeddings and FAISS' },
  ask: { title: 'Ask Questions', subtitle: 'Question answering over your document' },
  summary: { title: 'Document Summary', subtitle: 'Structured summary and plain-English explanations' },
  settings: { title: 'Settings', subtitle: 'About this application and model information' },
}

function AppShell() {
  const [activePage, setActivePage] = useState('dashboard')
  const meta = PAGE_META[activePage]

  return (
    <div className="flex min-h-screen bg-slate-50">
      <Sidebar activePage={activePage} onNavigate={setActivePage} />

      <div className="flex-1 min-w-0 flex flex-col">
        <Header title={meta.title} subtitle={meta.subtitle} />

        <main className="flex-1 px-5 md:px-8 py-6">
          {activePage === 'dashboard' && <DashboardPage onNavigate={setActivePage} />}
          {activePage === 'analyze' && <AnalyzePage onAnalyzed={() => setActivePage('dashboard')} />}
          {activePage === 'key-information' && <KeyInformationPage />}
          {activePage === 'clauses' && <ClausesPage />}
          {activePage === 'risk-analysis' && <RiskAnalysisPage />}
          {activePage === 'semantic-search' && <SearchPage />}
          {activePage === 'ask' && <AskPage />}
          {activePage === 'summary' && <SummaryPage />}
          {activePage === 'settings' && <SettingsPage />}
        </main>
      </div>
    </div>
  )
}

export default function App() {
  return (
    <AnalysisProvider>
      <AppShell />
    </AnalysisProvider>
  )
}
