import { useState } from 'react'

// Point this at wherever your FastAPI backend is running.
const API_BASE = 'http://localhost:8000'

export default function App() {
  const [text, setText] = useState('')
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  async function handleAnalyze() {
    setError('')
    setResult(null)

    if (text.trim().length < 5) {
      setError('Paste a headline or a few sentences from the article first.')
      return
    }

    setLoading(true)
    try {
      const res = await fetch(`${API_BASE}/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text }),
      })

      const data = await res.json()

      if (!res.ok) {
        throw new Error(data.detail || 'Something went wrong on the server.')
      }

      setResult(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="page">
      <header>
        <h1>News Sentiment &amp; Opposition Generator</h1>
        <p className="subtitle">
          Paste a Politics or Sports headline/article. It'll classify the tone
          and generate a respectful counter-viewpoint.
        </p>
      </header>

      <section className="input-panel">
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="e.g. 'Local council approves new stadium funding despite public opposition...'"
          rows={6}
        />
        <button onClick={handleAnalyze} disabled={loading}>
          {loading ? 'Analyzing...' : 'Analyze'}
        </button>
        {error && <p className="error">{error}</p>}
      </section>

      {result && (
        <section className="results-panel">
          <div className="badge-row">
            <span className={`badge badge-${result.category.toLowerCase()}`}>
              {result.category}
            </span>
            <span className={`badge badge-sentiment-${result.sentiment.toLowerCase()}`}>
              {result.sentiment}
            </span>
          </div>

          <p className="sentiment-reason">{result.sentiment_reason}</p>

          <div className="opposition-box">
            <h2>Opposing Viewpoint</h2>
            <p>{result.opposition_opinion}</p>
          </div>

          <p className="disclaimer">{result.disclaimer}</p>
        </section>
      )}
    </div>
  )
}
