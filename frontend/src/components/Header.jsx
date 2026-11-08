import React, { useEffect, useState } from 'react'
import { CheckCircle2, XCircle, Loader2 } from 'lucide-react'
import { checkHealth } from '../services/api.js'

export default function Header({ title, subtitle }) {
  const [status, setStatus] = useState('checking') // checking | ready | offline | degraded

  useEffect(() => {
    let cancelled = false

    async function poll() {
      const health = await checkHealth()
      if (cancelled) return
      if (!health.reachable) setStatus('offline')
      else if (!health.model_loaded) setStatus('degraded')
      else setStatus('ready')
    }

    poll()
    const interval = setInterval(poll, 8000)
    return () => {
      cancelled = true
      clearInterval(interval)
    }
  }, [])

  const badge = {
    checking: { icon: Loader2, text: 'Checking backend...', cls: 'text-slate-500', spin: true },
    ready: { icon: CheckCircle2, text: 'Backend ready · Legal-BERT loaded', cls: 'text-emerald-600', spin: false },
    degraded: { icon: Loader2, text: 'Backend up · loading Legal-BERT...', cls: 'text-amber-600', spin: true },
    offline: { icon: XCircle, text: 'Backend unreachable', cls: 'text-red-600', spin: false },
  }[status]

  const Icon = badge.icon

  return (
    <header className="sticky top-0 z-10 bg-white/90 backdrop-blur border-b border-slate-200 px-5 md:px-8 py-4 flex items-center justify-between gap-4">
      <div>
        <h1 className="text-lg md:text-xl font-semibold text-slate-900">{title}</h1>
        {subtitle && <p className="text-sm text-slate-500 mt-0.5">{subtitle}</p>}
      </div>
      <div className={`flex items-center gap-1.5 text-xs font-medium ${badge.cls} shrink-0`}>
        <Icon className={`w-3.5 h-3.5 ${badge.spin ? 'animate-spin' : ''}`} />
        <span className="hidden sm:inline">{badge.text}</span>
      </div>
    </header>
  )
}
