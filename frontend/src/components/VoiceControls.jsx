import React from 'react'
import { Volume2, Square } from 'lucide-react'
import { useSpeechSynthesis } from '../hooks/useSpeech.js'

/** Read-aloud button for a piece of text. */
export function SpeakButton({ text, label = 'Listen' }) {
  const { supported, speaking, speak, cancel } = useSpeechSynthesis()
  if (!supported || !text) return null
  return (
    <button
      type="button"
      onClick={() => (speaking ? cancel() : speak(text))}
      className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium text-indigo-700 border border-indigo-200 bg-indigo-50 hover:bg-indigo-100"
    >
      {speaking ? <Square className="w-3.5 h-3.5" /> : <Volume2 className="w-3.5 h-3.5" />}
      {speaking ? 'Stop' : label}
    </button>
  )
}
