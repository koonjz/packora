import { Check, X, Shield, Sparkles, DollarSign, Leaf } from 'lucide-react'

/**
 * ComparisonTable — Side-by-side comparative matrix of recommended materials.
 *
 * Props:
 *   recommendations: RecommendationItem[]
 */
export default function ComparisonTable({ recommendations = [] }) {
  if (!recommendations || recommendations.length === 0) return null

  return (
    <div className="card p-6 mt-8 border-brand-500/20 shadow-2xl">
      <div className="flex items-center gap-3 mb-6">
        <div className="w-8 h-8 rounded-xl bg-brand-500/20 flex items-center justify-center border border-brand-500/30">
          <Sparkles className="text-brand-400" size={18} />
        </div>
        <div>
          <h3 className="text-lg font-display font-bold text-white">Side-by-Side Material Comparison</h3>
          <p className="text-xs text-surface-200/60">Compare physical barrier metrics, cost, and sustainability across top candidates</p>
        </div>
      </div>

      <div className="overflow-x-auto scrollbar-thin">
        <table className="w-full text-left text-sm border-collapse min-w-[600px]">
          <thead>
            <tr className="border-b border-white/10 text-surface-200/70 text-xs uppercase tracking-wider">
              <th className="py-3 px-4 font-semibold">Metric</th>
              {recommendations.map(({ rank, material }) => (
                <th key={rank} className="py-3 px-4 font-bold text-white text-center">
                  <span className={`inline-block px-2 py-0.5 rounded-full text-xs font-bold mr-2 ${
                    rank === 1 ? 'bg-brand-500 text-white' : 'bg-white/10 text-surface-200'
                  }`}>
                    #{rank}
                  </span>
                  {material.name}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-white/5 text-surface-200/90">
            {/* Composite Score */}
            <tr className="bg-white/5">
              <td className="py-3 px-4 font-semibold text-white">Composite Fit Score</td>
              {recommendations.map(({ rank, reasoning_trace }) => {
                const score = reasoning_trace?.score_breakdown?.composite_score ?? 0
                return (
                  <td key={rank} className="py-3 px-4 text-center font-display font-bold text-brand-400 text-base">
                    {(score * 100).toFixed(0)}%
                  </td>
                )
              })}
            </tr>

            {/* WVTR */}
            <tr>
              <td className="py-3 px-4 flex items-center gap-2">
                <Shield size={14} className="text-brand-400" />
                WVTR (Moisture Barrier)
              </td>
              {recommendations.map(({ rank, material }) => (
                <td key={rank} className="py-3 px-4 text-center font-mono">
                  {material.wvtr} <span className="text-xs text-surface-200/50">g/m²/day</span>
                </td>
              ))}
            </tr>

            {/* OTR */}
            <tr>
              <td className="py-3 px-4 flex items-center gap-2">
                <Shield size={14} className="text-blue-400" />
                OTR (Oxygen Barrier)
              </td>
              {recommendations.map(({ rank, material }) => (
                <td key={rank} className="py-3 px-4 text-center font-mono">
                  {material.otr} <span className="text-xs text-surface-200/50">cc/m²/day</span>
                </td>
              ))}
            </tr>

            {/* Light Blocking */}
            <tr>
              <td className="py-3 px-4">Light Protection</td>
              {recommendations.map(({ rank, material }) => (
                <td key={rank} className="py-3 px-4 text-center">
                  {material.light_blocking ? (
                    <span className="inline-flex items-center gap-1 text-emerald-400 text-xs font-semibold">
                      <Check size={14} /> Full Light Barrier
                    </span>
                  ) : (
                    <span className="inline-flex items-center gap-1 text-surface-200/50 text-xs">
                      <X size={14} /> Transparent / Pass-through
                    </span>
                  )}
                </td>
              ))}
            </tr>

            {/* Crush Resistance */}
            <tr>
              <td className="py-3 px-4">Crush Resistance</td>
              {recommendations.map(({ rank, material }) => (
                <td key={rank} className="py-3 px-4 text-center">
                  <div className="flex items-center justify-center gap-1">
                    {[1, 2, 3, 4, 5].map((star) => (
                      <div
                        key={star}
                        className={`w-2 h-2 rounded-full ${
                          star <= material.crush_resistance ? 'bg-amber-400' : 'bg-white/10'
                        }`}
                      />
                    ))}
                    <span className="text-xs text-surface-200/50 ml-1">({material.crush_resistance}/5)</span>
                  </div>
                </td>
              ))}
            </tr>

            {/* Cost */}
            <tr>
              <td className="py-3 px-4 flex items-center gap-2">
                <DollarSign size={14} className="text-emerald-400" />
                Estimated Unit Cost
              </td>
              {recommendations.map(({ rank, material }) => (
                <td key={rank} className="py-3 px-4 text-center font-semibold text-white">
                  ₹{material.cost_per_unit.toFixed(2)}
                </td>
              ))}
            </tr>

            {/* Sustainability */}
            <tr>
              <td className="py-3 px-4 flex items-center gap-2">
                <Leaf size={14} className="text-emerald-400" />
                Biodegradability Score
              </td>
              {recommendations.map(({ rank, material }) => (
                <td key={rank} className="py-3 px-4 text-center">
                  <span className={`badge ${
                    material.biodegradability_score >= 4
                      ? 'badge-green'
                      : material.biodegradability_score >= 2
                      ? 'badge-amber'
                      : 'badge-blue'
                  }`}>
                    {material.biodegradability_score}/5
                  </span>
                </td>
              ))}
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  )
}
