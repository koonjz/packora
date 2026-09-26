import { CheckCircle, XCircle, Award, Leaf, DollarSign, Clock, ChevronDown, ChevronUp } from 'lucide-react'
import { useState } from 'react'

const RANK_COLOURS = ['from-amber-400 to-amber-300', 'from-surface-200 to-surface-300', 'from-amber-700 to-amber-600']
const RANK_LABELS = ['Best Match', '2nd Best', '3rd Best']

function ScoreBar({ label, value, icon: Icon, colorClass }) {
  return (
    <div>
      <div className="flex items-center justify-between mb-1.5">
        <span className="flex items-center gap-1.5 text-xs text-surface-200/70">
          <Icon size={12} />
          {label}
        </span>
        <span className="text-xs font-semibold text-white">{Math.round(value * 100)}%</span>
      </div>
      <div className="h-1.5 bg-white/10 rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-700 ${colorClass}`}
          style={{ width: `${value * 100}%` }}
        />
      </div>
    </div>
  )
}

/**
 * RecommendationCard — one recommended packaging material.
 *
 * Props:
 *   item: RecommendationItem from the API
 */
export default function RecommendationCard({ item }) {
  const [showRules, setShowRules] = useState(false)
  const { rank, material, reasoning_trace, plain_language_reason } = item
  const { score_breakdown, rules_applied, explanation_source } = reasoning_trace
  const rankIdx = rank - 1

  return (
    <div
      className={`card-hover p-6 animate-slide-up ${rank === 1 ? 'ring-1 ring-brand-500/30 glow-brand' : ''}`}
      style={{ animationDelay: `${rankIdx * 100}ms` }}
      id={`recommendation-card-${rank}`}
    >
      {/* Header */}
      <div className="flex items-start justify-between gap-4 mb-5">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className={`text-xs font-bold bg-gradient-to-r ${RANK_COLOURS[rankIdx]} bg-clip-text text-transparent uppercase tracking-wider`}>
              {RANK_LABELS[rankIdx] || `Rank ${rank}`}
            </span>
            {explanation_source === 'template' && (
              <span className="badge bg-surface-200/10 text-surface-200/50 border-surface-200/10 text-[10px]">
                template explanation
              </span>
            )}
          </div>
          <h3 className="text-xl font-display font-bold text-white">{material.name}</h3>
          {material.typical_use_case && (
            <p className="text-surface-200/60 text-sm mt-1">{material.typical_use_case}</p>
          )}
        </div>

        {/* Composite score ring */}
        <div className="text-center flex-shrink-0">
          <div className={`w-16 h-16 rounded-full flex items-center justify-center text-xl font-display font-bold
            ${rank === 1 ? 'bg-brand-500/20 text-brand-400 ring-2 ring-brand-500/40' : 'bg-white/8 text-white/80'}`}>
            {Math.round(score_breakdown.composite_score * 100)}
          </div>
          <p className="text-[10px] text-surface-200/50 mt-1">fit score</p>
        </div>
      </div>

      {/* Plain language reason */}
      <div className="bg-brand-500/8 border border-brand-500/15 rounded-xl px-4 py-3 mb-5">
        <p className="text-surface-200/90 text-sm leading-relaxed">{plain_language_reason}</p>
      </div>

      {/* Score bars */}
      <div className="space-y-3 mb-5">
        <ScoreBar label="Shelf Life Extension" value={score_breakdown.shelf_life_score} icon={Clock} colorClass="bg-brand-500" />
        <ScoreBar label="Cost Efficiency" value={score_breakdown.cost_score} icon={DollarSign} colorClass="bg-blue-500" />
        <ScoreBar label="Sustainability" value={score_breakdown.sustainability_score} icon={Leaf} colorClass="bg-emerald-500" />
      </div>

      {/* Material properties */}
      <div className="grid grid-cols-3 gap-3 mb-4">
        {[
          { label: 'WVTR', value: `${material.wvtr} g/m²/d`, title: 'Water Vapor Transmission Rate (lower = better moisture barrier)' },
          { label: 'OTR', value: `${material.otr} cc/m²/d`, title: 'Oxygen Transmission Rate (lower = better oxygen barrier)' },
          { label: 'Cost', value: `₹${material.cost_per_unit}/unit`, title: 'Estimated cost per packaging unit' },
        ].map(({ label, value, title }) => (
          <div key={label} className="bg-white/5 rounded-xl p-3 text-center" title={title}>
            <p className="text-[10px] text-surface-200/50 uppercase tracking-wider mb-1">{label}</p>
            <p className="text-sm font-semibold text-white font-mono">{value}</p>
          </div>
        ))}
      </div>

      {/* Sustainability badge */}
      <div className="flex items-center gap-2 mb-4">
        <Leaf size={14} className="text-emerald-400" />
        <div className="flex gap-1">
          {Array.from({ length: 5 }).map((_, i) => (
            <div
              key={i}
              className={`w-4 h-1.5 rounded-full transition-colors ${i < material.biodegradability_score ? 'bg-emerald-500' : 'bg-white/10'}`}
            />
          ))}
        </div>
        <span className="text-xs text-surface-200/60">Biodegradability {material.biodegradability_score}/5</span>
      </div>

      {/* Rule results — collapsible */}
      <button
        id={`rules-toggle-${rank}`}
        onClick={() => setShowRules(!showRules)}
        className="w-full flex items-center justify-between py-2 text-sm text-surface-200/60 hover:text-white transition-colors"
      >
        <span className="flex items-center gap-2">
          <Award size={14} />
          Rule Check ({rules_applied.filter(r => r.passed).length}/{rules_applied.length} passed)
        </span>
        {showRules ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
      </button>

      {showRules && (
        <div className="mt-2 space-y-2 animate-fade-in">
          {rules_applied.map((rule, i) => (
            <div
              key={i}
              className={`flex items-start gap-3 p-3 rounded-xl text-sm ${
                rule.passed ? 'bg-brand-500/8 border border-brand-500/15' : 'bg-red-500/8 border border-red-500/15'
              }`}
            >
              {rule.passed ? (
                <CheckCircle size={14} className="text-brand-400 flex-shrink-0 mt-0.5" />
              ) : (
                <XCircle size={14} className="text-red-400 flex-shrink-0 mt-0.5" />
              )}
              <div>
                <p className={`font-medium ${rule.passed ? 'text-brand-300' : 'text-red-300'}`}>{rule.rule_name}</p>
                <p className="text-surface-200/60 text-xs mt-0.5 font-mono leading-relaxed">{rule.reason}</p>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
