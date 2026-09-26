import { useState, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { Package, Zap, Leaf, ShieldCheck, ArrowRight } from 'lucide-react'
import CommoditySearch from '../components/CommoditySearch.jsx'
import ConditionsForm from '../components/ConditionsForm.jsx'
import { getRecommendations } from '../api/packora.js'

const DEFAULT_CONDITIONS = {
  target_shelf_life_days: 30,
  storage_condition: 'ambient',
  transport_condition: 'standard',
  weight_cost: 0.33,
  weight_sustainability: 0.33,
  weight_shelf_life: 0.34,
}

const FEATURES = [
  { icon: ShieldCheck, title: 'Rule Engine', desc: 'Hard physical constraints validated first — WVTR, OTR, light blocking, crush resistance.' },
  { icon: Zap, title: 'AI Ranking', desc: 'Surviving materials scored by a scikit-learn model trained on curated commodity data.' },
  { icon: Leaf, title: 'Explainable', desc: 'Every recommendation shows which rules passed and what drove the score — no black box.' },
]

export default function HomePage() {
  const navigate = useNavigate()
  const [commodity, setCommodity] = useState(null)
  const [conditions, setConditions] = useState(DEFAULT_CONDITIONS)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const handleConditionChange = useCallback((field, value) => {
    setConditions(prev => ({ ...prev, [field]: value }))
  }, [])

  const weightsSum = (
    conditions.weight_cost + conditions.weight_sustainability + conditions.weight_shelf_life
  ).toFixed(2)
  const weightsValid = Math.abs(parseFloat(weightsSum) - 1.0) < 0.01
  const canSubmit = commodity && weightsValid && !loading

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!canSubmit) return
    setLoading(true)
    setError(null)
    try {
      const result = await getRecommendations({
        commodity_id: commodity.id,
        ...conditions,
      })
      navigate('/results', { state: { result, commodity, conditions } })
    } catch (err) {
      setError(
        err.response?.data?.detail ||
        'Failed to get recommendations. Is the API running?'
      )
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen">
      {/* Hero */}
      <header className="pt-16 pb-10 px-6 text-center">
        <div className="flex items-center justify-center gap-3 mb-6">
          <div className="w-10 h-10 bg-brand-500 rounded-xl flex items-center justify-center shadow-lg shadow-brand-500/30">
            <Package size={22} className="text-white" />
          </div>
          <span className="text-2xl font-display font-bold text-white">Packora</span>
        </div>
        <h1 className="text-5xl md:text-6xl font-display font-extrabold text-white mb-4 leading-tight">
          Packaging,{' '}
          <span className="text-gradient">chosen by science.</span>
        </h1>
        <p className="text-surface-200/70 text-lg max-w-2xl mx-auto leading-relaxed">
          AI-assisted packaging recommendations for food MSMEs and FPOs.
          Tell us your commodity and conditions — we'll explain exactly which packaging material
          fits, and <em>why</em>.
        </p>
      </header>

      {/* Main form card */}
      <main className="max-w-3xl mx-auto px-6 pb-20">
        <form onSubmit={handleSubmit} className="card p-8 shadow-2xl shadow-black/30">
          <h2 className="text-xl font-display font-bold text-white mb-6">
            Get Your Recommendation
          </h2>

          <div className="space-y-8">
            <CommoditySearch value={commodity} onChange={setCommodity} />
            <hr className="border-white/8" />
            <ConditionsForm values={conditions} onChange={handleConditionChange} />
          </div>

          {error && (
            <div className="mt-6 p-4 bg-red-500/10 border border-red-500/20 rounded-xl text-red-300 text-sm">
              {error}
            </div>
          )}

          <div className="mt-8 flex items-center gap-4">
            <button
              id="get-recommendations-btn"
              type="submit"
              disabled={!canSubmit}
              className="btn-primary flex items-center gap-2 flex-1 justify-center text-base"
            >
              {loading ? (
                <>
                  <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  Analysing…
                </>
              ) : (
                <>
                  Get Recommendations
                  <ArrowRight size={16} />
                </>
              )}
            </button>
          </div>

          {!commodity && (
            <p className="mt-3 text-center text-surface-200/40 text-xs">
              Select a commodity above to continue
            </p>
          )}
        </form>

        {/* Feature highlights */}
        <div className="grid grid-cols-3 gap-4 mt-8">
          {FEATURES.map(({ icon: Icon, title, desc }) => (
            <div key={title} className="card p-5 text-center">
              <div className="w-10 h-10 bg-brand-500/15 rounded-xl flex items-center justify-center mx-auto mb-3">
                <Icon size={20} className="text-brand-400" />
              </div>
              <h3 className="text-sm font-semibold text-white mb-1">{title}</h3>
              <p className="text-xs text-surface-200/50 leading-relaxed">{desc}</p>
            </div>
          ))}
        </div>

        <p className="text-center text-surface-200/30 text-xs mt-8">
          Smart India Hackathon 2026 · SIH26236 · Ministry of Food Processing Industries
        </p>
      </main>
    </div>
  )
}
