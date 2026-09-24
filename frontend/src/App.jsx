import React, { useState, useEffect } from 'react'
import {
  Scale,
  Shield,
  Zap,
  Sparkles,
  Copy,
  Check,
  Sun,
  Moon,
  HelpCircle,
  RefreshCw,
  Landmark,
  Trophy,
  Cpu,
  TrendingUp,
  FlaskConical,
  Users,
  Newspaper,
  AlertCircle,
  ArrowRight,
  BookOpen,
  Compass,
  CornerDownRight,
  Trash2,
  X,
  Activity,
  Lightbulb,
  Download,
  Shuffle,
  SlidersHorizontal,
  CheckCircle2,
  FileText,
  Share2,
} from 'lucide-react'

const API_BASE = import.meta.env.VITE_API_BASE ?? (import.meta.env.DEV ? 'http://localhost:8000' : '')

// Default curated fallback presets
const FALLBACK_PRESETS = [
  {
    id: 'politics-zoning',
    title: 'Urban Zoning & 15-Min Cities',
    category: 'Politics',
    badge: 'Urban Policy',
    text: 'City council officially approves controversial 15-minute city zoning regulations, restricting private vehicle access in downtown corridors while subsidizing high-density micro-apartments to combat carbon emissions.',
  },
  {
    id: 'sports-underdog',
    title: 'Heartbreak & Late Penalty Drama',
    category: 'Sports',
    badge: 'Football / Soccer',
    text: 'Underdog FC suffers heartbreaking 2-1 defeat in the final stoppage minutes after referee awards a contested penalty against their captain, sparking furious protests from fans and team management.',
  },
  {
    id: 'tech-ai-workplace',
    title: 'Enterprise AI Automation Mandate',
    category: 'Technology & AI',
    badge: 'AI & Labor',
    text: 'Major tech conglomerate replaces 30% of entry-level customer support and copywriting workforce with autonomous LLM agents, reporting record quarterly operating margins and faster turnaround times.',
  },
  {
    id: 'economy-rate-hike',
    title: 'Central Bank Rate Hike',
    category: 'Economy & Business',
    badge: 'Monetary Policy',
    text: 'Federal Reserve raises benchmark interest rates by 50 basis points to curb persistent inflation, drawing sharp criticism from housing developers and small business associations fearing severe recession.',
  },
  {
    id: 'science-nuclear-energy',
    title: 'Modular Nuclear Reactor Push',
    category: 'Science & Climate',
    badge: 'Clean Energy',
    text: 'Energy ministry greenlights $5B funding for next-generation small modular nuclear reactors (SMRs) as the primary baseline power solution for phasing out coal plants by 2030.',
  },
  {
    id: 'society-remote-work',
    title: 'Mandatory 5-Day Office Return',
    category: 'Society & Culture',
    badge: 'Workplace Culture',
    text: 'Fortune 500 financial institution mandates strict 5-day in-office attendance with badge tracking, warning that non-compliance will directly impact performance reviews and promotion eligibility.',
  },
]

export default function App() {
  const [text, setText] = useState('')
  const [perspectiveMode, setPerspectiveMode] = useState('balanced')
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [activeStepIndex, setActiveStepIndex] = useState(0)
  const [error, setError] = useState('')
  const [presets, setPresets] = useState(FALLBACK_PRESETS)
  const [selectedPresetId, setSelectedPresetId] = useState(null)
  const [theme, setTheme] = useState(() => localStorage.getItem('dialectic_theme') || 'light')
  const [toastMessage, setToastMessage] = useState('')
  const [showInfoModal, setShowInfoModal] = useState(false)
  const [backendHealth, setBackendHealth] = useState(null)
  const [history, setHistory] = useState(() => {
    try {
      return JSON.parse(localStorage.getItem('dialectic_history') || '[]')
    } catch {
      return []
    }
  })

  // Set theme attribute (Light theme default)
  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme)
    localStorage.setItem('dialectic_theme', theme)
  }, [theme])

  // Save history to local storage
  useEffect(() => {
    localStorage.setItem('dialectic_history', JSON.stringify(history))
  }, [history])

  // Loading animation step timer
  useEffect(() => {
    let interval = null
    if (loading) {
      setActiveStepIndex(0)
      interval = setInterval(() => {
        setActiveStepIndex((prev) => (prev + 1) % 4)
      }, 700)
    } else {
      setActiveStepIndex(0)
    }
    return () => {
      if (interval) clearInterval(interval)
    }
  }, [loading])

  // Fetch presets and health status from backend
  useEffect(() => {
    async function loadBackendData() {
      try {
        const healthRes = await fetch(`${API_BASE}/health`)
        if (healthRes.ok) {
          const healthData = await healthRes.json()
          setBackendHealth(healthData)
        }
      } catch (err) {
        console.warn('Backend /health unreachable:', err)
      }

      try {
        const presetRes = await fetch(`${API_BASE}/presets`)
        if (presetRes.ok) {
          const presetData = await presetRes.json()
          if (presetData.presets?.length) {
            setPresets(presetData.presets)
          }
        }
      } catch (err) {
        console.warn('Backend /presets unreachable, using fallbacks:', err)
      }
    }
    loadBackendData()
  }, [])

  function showToast(msg) {
    setToastMessage(msg)
    setTimeout(() => {
      setToastMessage('')
    }, 2500)
  }

  function toggleTheme() {
    const nextTheme = theme === 'light' ? 'dark' : 'light'
    setTheme(nextTheme)
    showToast(`Switched to ${nextTheme === 'light' ? 'Light' : 'Dark'} theme`)
  }

  async function handleAnalyze(customText, customMode) {
    const inputText = (typeof customText === 'string' ? customText : text).trim()
    const modeToUse = customMode || perspectiveMode

    if (inputText.length < 5) {
      setError('Please enter a headline or article excerpt (at least 5 characters).')
      return
    }

    setError('')
    setLoading(true)

    try {
      const res = await fetch(`${API_BASE}/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          text: inputText,
          perspective_mode: modeToUse,
        }),
      })

      const data = await res.json()

      if (!res.ok) {
        throw new Error(data.detail || 'Failed to generate analysis.')
      }

      setResult(data)

      // Add to session history (keep latest 8)
      setHistory((prev) => {
        const filtered = prev.filter((item) => item.text !== inputText)
        return [
          {
            id: Date.now().toString(),
            text: inputText,
            category: data.category,
            sentiment: data.sentiment,
            sentiment_score: data.sentiment_score,
            timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          },
          ...filtered,
        ].slice(0, 8)
      })
    } catch (err) {
      setError(err.message || 'Unable to connect to the backend server. Please check if FastAPI is running.')
    } finally {
      setLoading(false)
    }
  }

  function handlePresetClick(preset) {
    setSelectedPresetId(preset.id)
    setText(preset.text)
    setError('')
    handleAnalyze(preset.text, perspectiveMode)
  }

  function handleShufflePreset() {
    if (!presets.length) return
    const randomIndex = Math.floor(Math.random() * presets.length)
    const preset = presets[randomIndex]
    handlePresetClick(preset)
  }

  function handleHistoryItemClick(item) {
    setText(item.text)
    setError('')
    handleAnalyze(item.text, perspectiveMode)
  }

  function handleClearHistory() {
    setHistory([])
    showToast('Session history cleared')
  }

  function handleKeyDown(e) {
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
      e.preventDefault()
      handleAnalyze()
    }
  }

  function copyFormattedAnalysis() {
    if (!result) return
    const formatted = `### DialecticAI Intelligence Report
**Category:** ${result.category}
**Sentiment:** ${result.sentiment} (Polarity Score: ${result.sentiment_score > 0 ? '+' : ''}${result.sentiment_score}/100)
**Tone Rationale:** ${result.sentiment_reason}

---
#### 🎯 Nuanced Opposing Viewpoint (${result.perspective_mode.toUpperCase()} MODE)
${result.opposition_opinion}

---
#### 📑 Original Key Claims:
${result.key_claims.map((c) => `- ${c}`).join('\n')}

#### 🛡️ Structured Counter-Arguments & Trade-offs:
${result.counter_arguments.map((a) => `- ${a}`).join('\n')}

---
#### 🤝 Foundational Common Ground:
${result.common_ground}

#### ❓ Critical Reflection Questions:
${result.critical_questions.map((q) => `1. ${q}`).join('\n')}

---
*${result.disclaimer}*`

    navigator.clipboard.writeText(formatted).then(() => {
      showToast('Report copied to clipboard!')
    })
  }

  function downloadReportFile() {
    if (!result) return
    const formatted = `# DialecticAI Analysis Report: ${result.category}
Generated on: ${new Date().toLocaleString()}

## Headline / Excerpt
"${text}"

## Sentiment & Polarity
- Category: ${result.category}
- Sentiment: ${result.sentiment} (${result.sentiment_score > 0 ? '+' : ''}${result.sentiment_score}/100)
- Analysis: ${result.sentiment_reason}

---

## 🎯 Opposing Perspective (${result.perspective_mode.toUpperCase()} Mode)
${result.opposition_opinion}

---

## 📑 Original Key Claims
${result.key_claims.map((c) => `- ${c}`).join('\n')}

## 🛡️ Structured Counter-Arguments & Overlooked Trade-offs
${result.counter_arguments.map((a) => `- ${a}`).join('\n')}

---

## 🤝 Foundational Common Ground
${result.common_ground}

## ❓ Critical Inquiry Questions
${result.critical_questions.map((q) => `1. ${q}`).join('\n')}

---
${result.disclaimer}
`
    const blob = new Blob([formatted], { type: 'text/markdown;charset=utf-8;' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', `dialectic-analysis-${Date.now()}.md`)
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    showToast('Analysis exported as .md file!')
  }

  function getCategoryIcon(cat) {
    const lower = (cat || '').toLowerCase()
    if (lower.includes('politic')) return <Landmark size={18} />
    if (lower.includes('sport')) return <Trophy size={18} />
    if (lower.includes('tech') || lower.includes('ai')) return <Cpu size={18} />
    if (lower.includes('econ') || lower.includes('business')) return <TrendingUp size={18} />
    if (lower.includes('scien') || lower.includes('climate')) return <FlaskConical size={18} />
    if (lower.includes('societ') || lower.includes('culture')) return <Users size={18} />
    return <Newspaper size={18} />
  }

  function getCategoryClass(cat) {
    const lower = (cat || '').toLowerCase()
    if (lower.includes('politic')) return 'cat-politics'
    if (lower.includes('sport')) return 'cat-sports'
    if (lower.includes('tech') || lower.includes('ai')) return 'cat-tech'
    if (lower.includes('econ') || lower.includes('business')) return 'cat-economy'
    if (lower.includes('scien') || lower.includes('climate')) return 'cat-science'
    if (lower.includes('societ') || lower.includes('culture')) return 'cat-society'
    return 'cat-general'
  }

  // Calculate polarity needle position on gauge [-100, 100] -> [0%, 100%]
  const gaugePercent = result ? Math.max(0, Math.min(100, ((result.sentiment_score + 100) / 200) * 100)) : 50

  const pipelineSteps = [
    { label: 'Categorizing Context', icon: Landmark },
    { label: 'Measuring Polarity', icon: Activity },
    { label: 'Steelmanning Counter-Take', icon: Shield },
    { label: 'Extracting Common Ground', icon: Users },
  ]

  return (
    <div className="app-wrapper">
      <div className="page-container">
        {/* Navigation Bar */}
        <header className="navbar">
          <div className="brand" onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}>
            <div className="brand-icon">
              <Scale size={24} />
            </div>
            <div className="brand-text-col">
              <h1 className="brand-title">
                Dialectic<span>AI</span>
              </h1>
              <span className="brand-tag">Counter-Viewpoint Intelligence</span>
            </div>
          </div>

          <div className="nav-actions">
            {backendHealth && (
              <div className="status-pill" title={`Active Model: ${backendHealth.active_model}`}>
                <span className={`status-dot ${backendHealth.groq_configured ? '' : 'demo'}`} />
                <span>{backendHealth.groq_configured ? 'Groq LLM Active' : 'Offline Demo Engine'}</span>
              </div>
            )}

            <button
              className="icon-btn"
              onClick={() => setShowInfoModal(true)}
              title="Steelmanning & Dialectical Method Guide"
              aria-label="Help Guide"
            >
              <HelpCircle size={19} />
            </button>

            <button
              className="icon-btn"
              onClick={toggleTheme}
              title={`Switch to ${theme === 'light' ? 'Dark' : 'Light'} theme`}
              aria-label="Toggle Theme"
            >
              {theme === 'light' ? <Moon size={19} /> : <Sun size={19} />}
            </button>
          </div>
        </header>

        {/* Hero Section */}
        <section className="hero-banner">
          <div className="hero-pill">
            <Sparkles size={15} />
            <span>Category-Aware Sentiment & Steelman Reasoning</span>
          </div>
          <h2 className="hero-title">
            Challenge Dogma with <span>Nuanced Counter-Angles</span>
          </h2>
          <p className="hero-desc">
            Submit any news headline or policy article. Our dialectical engine classifies category, measures
            emotional polarity, and generates good-faith steelman counter-arguments to expand cognitive breadth.
          </p>
        </section>

        {/* Curated Presets Ribbon */}
        <section className="presets-container">
          <div className="presets-header-row">
            <div className="presets-label">
              <Compass size={15} />
              <span>Curated Sample Headlines (1-Click Test)</span>
            </div>
            <button className="shuffle-btn" onClick={handleShufflePreset} title="Pick random sample">
              <Shuffle size={13} />
              <span>Random Headline</span>
            </button>
          </div>
          <div className="presets-grid">
            {presets.map((preset) => (
              <button
                key={preset.id}
                className={`preset-chip ${selectedPresetId === preset.id ? 'active-preset' : ''}`}
                onClick={() => handlePresetClick(preset)}
                title={preset.text}
              >
                <div className="preset-chip-title">{preset.title}</div>
                <span className="preset-chip-badge">{preset.badge || preset.category}</span>
              </button>
            ))}
          </div>
        </section>

        {/* Main Input Studio Card */}
        <section className="studio-card">
          <div className="input-header">
            <label htmlFor="headline-input" className="input-label">
              <BookOpen size={17} />
              <span>News Headline or Article Excerpt</span>
            </label>
            {text && (
              <div className="input-actions">
                <button
                  className="action-btn"
                  onClick={() => {
                    setText('')
                    setSelectedPresetId(null)
                  }}
                  title="Clear text"
                >
                  <X size={14} /> Clear
                </button>
              </div>
            )}
          </div>

          <div className="textarea-wrapper">
            <textarea
              id="headline-input"
              className="headline-textarea"
              value={text}
              onChange={(e) => setText(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Paste a news headline, policy announcement, sports controversy, or editorial here... (e.g. 'Federal Reserve raises benchmark interest rates by 50 bps to curb persistent inflation...')"
              rows={4}
            />
            <div className="textarea-footer">
              <span className="char-counter">{text.length} characters</span>
              <span>
                Press <kbd style={{ padding: '2px 6px', background: 'var(--surface-subtle)', borderRadius: '4px', border: '1px solid var(--border-subtle)' }}>Ctrl</kbd> + <kbd style={{ padding: '2px 6px', background: 'var(--surface-subtle)', borderRadius: '4px', border: '1px solid var(--border-subtle)' }}>Enter</kbd> to analyze
              </span>
            </div>
          </div>

          {/* Perspective Mode Selection */}
          <div className="modes-section">
            <div className="modes-title">
              <SlidersHorizontal size={15} />
              <span>Select Dialectical Perspective Mode</span>
            </div>
            <div className="modes-grid">
              <button
                type="button"
                className={`mode-btn ${perspectiveMode === 'balanced' ? 'active' : ''}`}
                onClick={() => setPerspectiveMode('balanced')}
              >
                <div className="mode-header">
                  <div className="mode-title-text">
                    <Scale size={16} />
                    <span>Balanced Synthesis</span>
                  </div>
                  {perspectiveMode === 'balanced' && <div className="mode-active-indicator" />}
                </div>
                <div className="mode-desc">
                  Measured, fair equilibrium evaluating valid considerations on both sides.
                </div>
              </button>

              <button
                type="button"
                className={`mode-btn ${perspectiveMode === 'steelman' ? 'active' : ''}`}
                onClick={() => setPerspectiveMode('steelman')}
              >
                <div className="mode-header">
                  <div className="mode-title-text">
                    <Shield size={16} />
                    <span>Steelman Stance</span>
                  </div>
                  {perspectiveMode === 'steelman' && <div className="mode-active-indicator" />}
                </div>
                <div className="mode-desc">
                  The strongest philosophical, strategic &amp; structural defense of the opposing view.
                </div>
              </button>

              <button
                type="button"
                className={`mode-btn ${perspectiveMode === 'challenger' ? 'active' : ''}`}
                onClick={() => setPerspectiveMode('challenger')}
              >
                <div className="mode-header">
                  <div className="mode-title-text">
                    <Zap size={16} />
                    <span>Critical Challenger</span>
                  </div>
                  {perspectiveMode === 'challenger' && <div className="mode-active-indicator" />}
                </div>
                <div className="mode-desc">
                  Probes hidden assumptions, unintended secondary trade-offs, and edge-cases.
                </div>
              </button>
            </div>
          </div>

          <div className="studio-footer">
            <div className="hint-text">
              <Lightbulb size={16} color="var(--accent-primary)" />
              <span>Focuses on principles and structural outcomes without ad hominem character attacks.</span>
            </div>
            <button
              className="btn-primary"
              onClick={() => handleAnalyze()}
              disabled={loading || text.trim().length < 5}
            >
              {loading ? (
                <>
                  <RefreshCw size={18} className="animate-spin" />
                  <span>Evaluating Dialectic...</span>
                </>
              ) : (
                <>
                  <Sparkles size={18} />
                  <span>Generate Counter-Analysis</span>
                  <ArrowRight size={18} />
                </>
              )}
            </button>
          </div>

          {error && (
            <div style={{ marginTop: '16px', padding: '14px 18px', background: 'var(--neg-bg)', border: '1px solid var(--neg-border)', borderRadius: 'var(--radius-md)', color: 'var(--neg-text)', display: 'flex', alignItems: 'center', gap: '10px' }}>
              <AlertCircle size={20} />
              <div>
                <strong>Notice:</strong> {error}
              </div>
            </div>
          )}
        </section>

        {/* Multi-Step Animated Loading Radar */}
        {loading && (
          <section className="evaluating-card">
            <div className="loading-spinner-ring" />
            <h3 className="loading-title">Synthesizing Dialectical Analysis</h3>
            <p className="loading-subtext">
              Our neural reasoning pipeline is examining key assertions, calculating sentiment polarity, and constructing a rigorous counter-argument.
            </p>
            <div className="loading-steps-row">
              {pipelineSteps.map((step, idx) => {
                const StepIcon = step.icon
                const isActive = activeStepIndex === idx
                return (
                  <div
                    key={idx}
                    className="loading-step-pill"
                    style={{
                      borderColor: isActive ? 'var(--accent-primary)' : 'var(--border-subtle)',
                      color: isActive ? 'var(--accent-primary)' : 'var(--text-muted)',
                      background: isActive ? 'var(--accent-light)' : 'var(--surface-subtle)',
                      transform: isActive ? 'scale(1.05)' : 'scale(1)',
                      transition: 'all 0.3s ease',
                    }}
                  >
                    <StepIcon size={14} />
                    <span>{step.label}</span>
                  </div>
                )
              })}
            </div>
          </section>
        )}

        {/* Results Dashboard */}
        {result && !loading && (
          <section className="results-wrapper">
            {/* Meta Summary Card with Polarity Gauge */}
            <div className="meta-summary-card">
              <div className="meta-left">
                <div className="category-row">
                  <span className={`badge-cat ${getCategoryClass(result.category)}`}>
                    {getCategoryIcon(result.category)}
                    {result.category}
                  </span>
                  <span className="badge-mode">
                    {result.perspective_mode} perspective
                  </span>
                </div>
                <p className="sentiment-statement">
                  <strong>Sentiment Tone:</strong> {result.sentiment_reason}
                </p>
              </div>

              <div className="meta-right">
                <div className="gauge-header">
                  <span className="gauge-title">Sentiment Polarity Gauge</span>
                  <span
                    className={`gauge-score-badge ${
                      result.sentiment === 'Positive'
                        ? 'positive'
                        : result.sentiment === 'Negative'
                        ? 'negative'
                        : 'neutral'
                    }`}
                  >
                    {result.sentiment} ({result.sentiment_score > 0 ? '+' : ''}
                    {result.sentiment_score})
                  </span>
                </div>
                <div className="gauge-bar-track">
                  <div
                    className="gauge-indicator"
                    style={{ left: `${gaugePercent}%` }}
                    title={`Polarity Score: ${result.sentiment_score}`}
                  />
                </div>
                <div className="gauge-labels">
                  <span>-100 Critical</span>
                  <span>0 Neutral</span>
                  <span>+100 Favorable</span>
                </div>
              </div>
            </div>

            {/* Hero Opposing Viewpoint Card */}
            <div className="hero-opposition-card">
              <div className="card-top-row">
                <h3 className="opposition-heading">
                  <Shield size={24} color="var(--accent-primary)" />
                  <span>Opposing Viewpoint &amp; Dialectical Counter-Take</span>
                </h3>
                <div className="card-actions">
                  <button className="action-btn" onClick={copyFormattedAnalysis} title="Copy Markdown Report">
                    <Copy size={15} />
                    <span>Copy Report</span>
                  </button>
                  <button className="action-btn" onClick={downloadReportFile} title="Download .md file">
                    <Download size={15} />
                    <span>Export</span>
                  </button>
                </div>
              </div>
              <p className="opposition-paragraph">{result.opposition_opinion}</p>
            </div>

            {/* Side-by-Side Dialectical Grid */}
            <div className="dialectical-grid">
              {/* Key Claims */}
              <div className="grid-card">
                <h4 className="grid-card-header claims">
                  <BookOpen size={19} />
                  <span>Source Framing &amp; Key Claims</span>
                </h4>
                <ul className="claims-list">
                  {result.key_claims.map((claim, idx) => (
                    <li key={idx} className="claim-item">
                      <CornerDownRight size={17} color="var(--text-muted)" className="item-bullet" />
                      <span>{claim}</span>
                    </li>
                  ))}
                </ul>
              </div>

              {/* Counter Arguments */}
              <div className="grid-card">
                <h4 className="grid-card-header counters">
                  <Shield size={19} />
                  <span>Structured Counter-Arguments</span>
                </h4>
                <ul className="counters-list">
                  {result.counter_arguments.map((arg, idx) => (
                    <li key={idx} className="counter-item">
                      <Zap size={17} color="var(--accent-primary)" className="item-bullet" />
                      <span>{arg}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>

            {/* Common Ground & Critical Inquiry Panels */}
            <div className="secondary-grid">
              {/* Common Ground Card */}
              <div className="bridge-card">
                <h4 className="bridge-header">
                  <Users size={19} />
                  <span>Foundational Common Ground</span>
                </h4>
                <p className="bridge-text">{result.common_ground}</p>
              </div>

              {/* Critical Questions Card */}
              <div className="questions-card">
                <h4 className="questions-header">
                  <HelpCircle size={19} />
                  <span>Critical Reflection Questions</span>
                </h4>
                <ul className="questions-list">
                  {result.critical_questions.map((q, idx) => (
                    <li key={idx} className="question-item">
                      <Activity size={17} color="var(--accent-primary)" className="item-bullet" />
                      <span>{q}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>

            {/* Mode Re-Switcher Bar */}
            <div className="mode-switcher-bar">
              <div className="mode-switcher-label">
                <RefreshCw size={15} />
                <span>Re-examine this headline in another perspective:</span>
              </div>
              <div className="mode-pills-group">
                {['balanced', 'steelman', 'challenger'].map((m) => (
                  <button
                    key={m}
                    className={`action-btn ${result.perspective_mode === m ? 'active' : ''}`}
                    onClick={() => {
                      setPerspectiveMode(m)
                      handleAnalyze(text, m)
                    }}
                    disabled={loading}
                  >
                    <span>{m.charAt(0).toUpperCase() + m.slice(1)}</span>
                  </button>
                ))}
              </div>
            </div>

            {/* Disclaimer and Model Badge Footer */}
            <div className="results-footer-bar">
              <p className="disclaimer-text">{result.disclaimer}</p>
              {result.source_model && (
                <span className="model-badge">
                  {result.is_demo_mode ? '⚡ Offline Demo Engine' : `Model: ${result.source_model}`}
                </span>
              )}
            </div>
          </section>
        )}

        {/* Recent Session History */}
        {history.length > 0 && (
          <section className="history-card">
            <div className="history-header">
              <div className="history-title">
                <Compass size={17} />
                <span>Recent Analyses History ({history.length})</span>
              </div>
              <button className="action-btn" onClick={handleClearHistory} title="Clear history">
                <Trash2 size={13} />
                <span>Clear</span>
              </button>
            </div>
            <div className="history-list">
              {history.map((item) => (
                <div key={item.id} className="history-item" onClick={() => handleHistoryItemClick(item)}>
                  <span className="history-item-text">{item.text}</span>
                  <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                    <span className={`badge-cat ${getCategoryClass(item.category)} history-item-badge`}>
                      {item.category}
                    </span>
                    <span style={{ fontSize: '0.74rem', color: 'var(--text-muted)' }}>{item.timestamp}</span>
                  </div>
                </div>
              ))}
            </div>
          </section>
        )}

        {/* Floating Toast Notification */}
        {toastMessage && (
          <div className="toast-container">
            <div className="toast-box">
              <CheckCircle2 size={18} color="#10b981" />
              <span>{toastMessage}</span>
            </div>
          </div>
        )}

        {/* Informational Modal */}
        {showInfoModal && (
          <div className="modal-overlay" onClick={() => setShowInfoModal(false)}>
            <div className="modal-content" onClick={(e) => e.stopPropagation()}>
              <button className="icon-btn modal-close-btn" onClick={() => setShowInfoModal(false)}>
                <X size={18} />
              </button>

              <h3 className="modal-title">
                <Scale size={24} color="var(--accent-primary)" />
                <span>DialecticAI &amp; Steelmanning</span>
              </h3>

              <div className="modal-section">
                <h4>What is the Dialectical Method?</h4>
                <p>
                  Rooted in classical Socratic and Hegelian philosophy, dialectical reasoning seeks deeper truth by
                  examining a thesis against its antithesis to generate a more nuanced synthesis, rather than settling
                  for superficial polarization.
                </p>
              </div>

              <div className="modal-section">
                <h4>What is Steelmanning?</h4>
                <p>
                  Steelmanning is the intellectual practice of formulating the absolute strongest, most plausible, and
                  persuasive version of your opponent’s argument before responding, directly countering the common
                  "strawman" fallacy.
                </p>
              </div>

              <div className="modal-section">
                <h4>Safety &amp; Ethical Guardrails</h4>
                <p>
                  Every headline undergoes strict input safety filtering. Outputs are engineered to critique structural
                  principles, economic trade-offs, and empirical outcomes without resorting to personal insults, slurs,
                  or political attacks.
                </p>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
