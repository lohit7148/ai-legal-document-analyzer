import { useCallback, useEffect, useRef, useState } from 'react'

// ---------------------------------------------------------------------------
// Optional voice output: text is spoken ONLY when the user clicks a Listen
// button. Uses the browser's built-in speech synthesis; nothing is sent to our
// backend. There is no voice input and no automatic reading.
// ---------------------------------------------------------------------------

const SETTINGS_KEY = 'legal-analyzer-voice'
const DEFAULTS = { lang: 'en-IN', rate: 1 }

export function getVoiceSettings() {
  try {
    return { ...DEFAULTS, ...JSON.parse(localStorage.getItem(SETTINGS_KEY) || '{}') }
  } catch {
    return { ...DEFAULTS }
  }
}

export function saveVoiceSettings(settings) {
  try {
    localStorage.setItem(SETTINGS_KEY, JSON.stringify(settings))
  } catch {
    /* storage unavailable: settings last for this session only */
  }
}

export function speechSupport() {
  return { synthesis: typeof window !== 'undefined' && 'speechSynthesis' in window }
}

function chunkText(text, maxLen = 180) {
  // Browsers cut off long utterances, so read sentence by sentence.
  const sentences = text.replace(/\s+/g, ' ').match(/[^.!?]+[.!?]*/g) || [text]
  const chunks = []
  let current = ''
  for (const s of sentences) {
    if ((current + s).length > maxLen && current) {
      chunks.push(current.trim())
      current = ''
    }
    current += s + ' '
  }
  if (current.trim()) chunks.push(current.trim())
  return chunks
}

/** Text -> speech. */
export function useSpeechSynthesis() {
  const supported = speechSupport().synthesis
  const [speaking, setSpeaking] = useState(false)
  const tokenRef = useRef(0)

  const cancel = useCallback(() => {
    tokenRef.current += 1
    if (supported) window.speechSynthesis.cancel()
    setSpeaking(false)
  }, [supported])

  const speak = useCallback(
    (text) => {
      if (!supported || !text) return
      window.speechSynthesis.cancel()
      const token = ++tokenRef.current
      const { lang, rate } = getVoiceSettings()
      const chunks = chunkText(text)
      setSpeaking(true)
      chunks.forEach((chunk, i) => {
        const u = new SpeechSynthesisUtterance(chunk)
        u.lang = lang
        u.rate = rate
        u.onend = () => {
          if (token === tokenRef.current && i === chunks.length - 1) setSpeaking(false)
        }
        u.onerror = () => {
          if (token === tokenRef.current) setSpeaking(false)
        }
        window.speechSynthesis.speak(u)
      })
    },
    [supported]
  )

  useEffect(() => () => supported && window.speechSynthesis.cancel(), [supported])
  return { supported, speaking, speak, cancel }
}
