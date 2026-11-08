// Uses the host the page was opened from, so the dashboard also works when
// opened from another device (e.g. a Raspberry Pi) on the same network.
const API_BASE_URL = `http://${window.location.hostname}:8000`

/**
 * Error type so the UI can show a friendly message. status 0 = the backend
 * could not be reached at all.
 */
export class ApiError extends Error {
  constructor(message, status) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

async function request(path, options) {
  let response
  try {
    response = await fetch(`${API_BASE_URL}${path}`, options)
  } catch {
    throw new ApiError(
      'Could not reach the backend server. Make sure the FastAPI backend is running at ' +
        `${API_BASE_URL} (see README: "uvicorn main:app --reload").`,
      0
    )
  }

  let data = null
  try {
    data = await response.json()
  } catch {
    // response had no JSON body
  }

  if (!response.ok) {
    let detail = `Request failed with status ${response.status}.`
    if (data && typeof data.detail === 'string') detail = data.detail
    else if (data && Array.isArray(data.detail)) detail = 'Invalid input. Please check your entry and try again.'
    throw new ApiError(detail, response.status)
  }
  return data
}

const postJson = (path, body) =>
  request(path, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) })

/** Stage 1: analyse pasted / extracted text. */
export const analyzeDocument = (text) => postJson('/api/analyze', { text })

/** Stage 2: upload a PDF or image and get its text back (OCR when needed). */
export function extractText(file) {
  const form = new FormData()
  form.append('file', file)
  return request('/api/extract-text', { method: 'POST', body: form })
}

/** Stage 3: semantic search inside an analysed document. */
export const searchDocument = (documentId, query, topK = 5) =>
  postJson('/api/search', { document_id: documentId, query, top_k: topK })

/** Stage 4: ask a question about the analysed document (RAG). */
export const askQuestion = (documentId, question, topK = 4) =>
  postJson('/api/ask', { document_id: documentId, question, top_k: topK })

/** Stage 5: plain-English summary (LLM if configured, else extractive). */
export const aiSummary = (documentId) => postJson('/api/ai-summary', { document_id: documentId })

/** GET /health -> used for the status badge in the header. */
export async function checkHealth() {
  try {
    const response = await fetch(`${API_BASE_URL}/health`)
    if (!response.ok) return { reachable: true, model_loaded: false }
    const data = await response.json()
    return { reachable: true, model_loaded: !!data.model_loaded, ocr_available: !!data.ocr_available, llm_configured: !!data.llm_configured, llm_provider: data.llm_provider }
  } catch {
    return { reachable: false, model_loaded: false }
  }
}
