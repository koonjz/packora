import { useState } from 'react'
import { CheckCircle2, XCircle, ChevronDown, Cpu, Sparkles, Sliders } from 'lucide-react'

/**
 * ReasoningTrace — Interactive component rendering the full decision breakdown.
 *
 * Props:
 *   trace: ReasoningTrace schema object
 *   plainLanguageReason: string
 */
export default function ReasoningTrace({ trace, plainLanguageReason }) {
  const [expanded, setExpanded] = useState(false)

  if (!trace) return null

  const { rules_applied = [], rules_passed = 0, rules_failed = 0, score_breakdown = {}, explanation_source = 'template' } = trace

  return (
    <div className="mt-4 pt-4 border-t border-white/10">
      {/* Plain Language Summary Box */}
      <div className="p-4 bg-brand-500/10 border border-brand-500/20 rounded-xl mb-3">
        <div className="flex items-center gap-2 mb-1.5">
          <Sparkles size={16} className="text-brand-400" />
          <span className="text-xs font-bold uppercase tracking-wider text-brand-400">
            Science-Backed Reasoning
          </span>
          <span className={`ml-auto badge text-[10px] ${
            explanation_source === 'llm' ? 'badge-green' : 'badge-amber'
          }`}>
            {explanation_source === 'llm' ? 'AI Generated' : 'Science Template'}
          </span>
        </div>
        <p className="text-sm text-white/90 leading-relaxed">
          {plainLanguageReason}
        </p>
      </div>

      {/* Expand/Collapse Toggle */}
      <button
        type="button"
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center justify-between text-xs font-semibold text-surface-200/70 hover:text-white py-1 transition-colors"
      >
        <span className="flex items-center gap-1.5">
          <Sliders size={14} className="text-brand-400" />
          {expanded ? 'Hide Technical Reasoning Trace' : 'View Full Decision Trace (Rules & ML Scores)'}
        </span>
        <ChevronDown size={14} className={`transition-transform duration-200 ${expanded ? 'rotate-180' : ''}`} />
      </button>

      {/* Expanded Technical Trace Details */}
      {expanded && (
        <div className="mt-3 space-y-4 animate-fade-in text-xs">
          {/* Score breakdown bars */}
          <div className="p-3 bg-white/5 rounded-xl border border-white/5 space-y-2.5">
            <div className="flex items-center gap-1.5 text-surface-200/80 font-bold mb-1">
              <Cpu size={14} className="text-brand-400" />
              Scikit-Learn ML Score Components
            </div>

            {/* Composite Score Bar */}
            <div>
              <div className="flex justify-between mb-1">
                <span className="text-white font-medium">Composite Score</span>
                <span className="text-brand-400 font-mono font-bold">
                  {((score_breakdown.composite_score || 0) * 100).toFixed(1)}%
                </span>
              </div>
              <div className="w-full h-2 bg-white/10 rounded-full overflow-hidden">
                <div
                  className="h-full bg-brand-400 rounded-full transition-all duration-500"
                  style={{ width: `${(score_breakdown.composite_score || 0) * 100}%` }}
                />
              </div>
            </div>

            {/* Sub-scores */}
            <div className="grid grid-cols-3 gap-3 pt-1">
              <div>
                <span className="text-surface-200/50 block">Barrier Fit</span>
                <span className="font-mono text-white font-semibold">
                  {((score_breakdown.base_ml_score || 0) * 100).toFixed(0)}%
                </span>
              </div>
              <div>
                <span className="text-surface-200/50 block">Cost Index</span>
                <span className="font-mono text-white font-semibold">
                  {((score_breakdown.cost_score || 0) * 100).toFixed(0)}%
                </span>
              </div>
              <div>
                <span className="text-surface-200/50 block">Sustainability</span>
                <span className="font-mono text-white font-semibold">
                  {((score_breakdown.sustainability_score || 0) * 100).toFixed(0)}%
                </span>
              </div>
            </div>
          </div>

          {/* Rule Engine Results */}
          <div className="space-y-2">
            <div className="flex items-center justify-between text-surface-200/80 font-bold">
              <span>Rule Engine Constraints ({rules_passed} Passed / {rules_failed} Failed)</span>
            </div>

            <div className="space-y-1.5">
              {rules_applied.map((rule, idx) => (
                <div
                  key={idx}
                  className={`flex items-start gap-2 p-2 rounded-lg border ${
                    rule.passed
                      ? 'bg-emerald-500/5 border-emerald-500/20 text-emerald-200'
                      : 'bg-red-500/5 border-red-500/20 text-red-200'
                  }`}
                >
                  {rule.passed ? (
                    <CheckCircle2 size={14} className="text-emerald-400 flex-shrink-0 mt-0.5" />
                  ) : (
                    <XCircle size={14} className="text-red-400 flex-shrink-0 mt-0.5" />
                  )}
                  <div>
                    <span className="font-semibold">{rule.rule_name}: </span>
                    <span className="opacity-90">{rule.reason}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
