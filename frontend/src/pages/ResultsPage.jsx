import { useLocation, useNavigate } from 'react-router-dom'
import { ArrowLeft, Package, AlertCircle, CheckCircle2, Info } from 'lucide-react'
import RecommendationCard from '../components/RecommendationCard.jsx'
import ComparisonTable from '../components/ComparisonTable.jsx'

export default function ResultsPage() {
  const location = useLocation()
  const navigate = useNavigate()
  const { result, commodity, conditions } = location.state || {}

  // If someone navigates directly to /results without state
  if (!result) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <p className="text-surface-200/60 mb-4">No results to display.</p>
          <button id="back-to-home-fallback" onClick={() => navigate('/')} className="btn-primary">
            Back to Home
          </button>
        </div>
      </div>
    )
  }

  const { recommendations, total_materials_evaluated, total_materials_passing_rules, warning } = result

  return (
    <div className="min-h-screen pb-20">
      {/* Nav */}
      <header className="sticky top-0 z-10 bg-surface-950/80 backdrop-blur-md border-b border-white/5">
        <div className="max-w-5xl mx-auto px-6 py-4 flex items-center gap-4">
          <button
            id="back-btn"
            onClick={() => navigate('/')}
            className="flex items-center gap-2 text-surface-200/60 hover:text-white transition-colors text-sm"
          >
            <ArrowLeft size={16} />
            New Search
          </button>
          <div className="flex items-center gap-2 ml-auto">
            <div className="w-6 h-6 bg-brand-500 rounded-lg flex items-center justify-center">
              <Package size={14} className="text-white" />
            </div>
            <span className="font-display font-bold text-white text-sm">Packora</span>
          </div>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-6 pt-10">
        {/* Result summary header */}
        <div className="mb-8">
          <p className="text-brand-400 text-sm font-medium uppercase tracking-wider mb-2">
            Packaging Recommendation
          </p>
          <h1 className="text-3xl font-display font-bold text-white mb-2">
            {commodity?.name}
          </h1>
          <div className="flex flex-wrap gap-3 text-sm text-surface-200/60">
            <span>🗓 {conditions?.target_shelf_life_days} days shelf life</span>
            <span>•</span>
            <span>🌡 {conditions?.storage_condition}</span>
            <span>•</span>
            <span>🚚 {conditions?.transport_condition}</span>
          </div>
        </div>

        {/* Stats row */}
        <div className="grid grid-cols-3 gap-4 mb-8">
          {[
            { label: 'Materials Evaluated', value: total_materials_evaluated, icon: Info, color: 'text-white' },
            {
              label: 'Passed All Rules',
              value: total_materials_passing_rules,
              icon: CheckCircle2,
              color: total_materials_passing_rules > 0 ? 'text-brand-400' : 'text-red-400',
            },
            { label: 'Recommendations', value: recommendations.length, icon: Package, color: 'text-white' },
          ].map(({ label, value, icon: Icon, color }) => (
            <div key={label} className="card p-4 text-center">
              <Icon size={18} className={`mx-auto mb-1.5 ${color}`} />
              <p className={`text-2xl font-display font-bold ${color}`}>{value}</p>
              <p className="text-xs text-surface-200/50 mt-0.5">{label}</p>
            </div>
          ))}
        </div>

        {/* Warning (LLM fallback notice) */}
        {warning && (
          <div className="flex items-start gap-3 p-4 bg-amber-500/10 border border-amber-500/20 rounded-xl mb-8 text-sm text-amber-300">
            <AlertCircle size={16} className="flex-shrink-0 mt-0.5" />
            {warning}
          </div>
        )}

        {/* No valid materials */}
        {recommendations.length === 0 && (
          <div className="card p-10 text-center">
            <AlertCircle size={32} className="text-amber-400 mx-auto mb-4" />
            <h2 className="text-xl font-display font-semibold text-white mb-2">
              No packaging materials passed all rules
            </h2>
            <p className="text-surface-200/60 max-w-md mx-auto text-sm">
              The constraints for this commodity and shelf-life target eliminated all available
              materials. Try adjusting the shelf life or storage conditions, or contact us to
              expand the materials database.
            </p>
            <button id="try-again-btn" onClick={() => navigate('/')} className="btn-primary mt-6">
              Try Different Conditions
            </button>
          </div>
        )}

        {/* Recommendation cards */}
        <div className="space-y-6">
          {recommendations.map((item) => (
            <RecommendationCard key={item.rank} item={item} />
          ))}
        </div>

        {/* Comparative Table */}
        <ComparisonTable recommendations={recommendations} />

        {/* Footer note */}
        {recommendations.length > 0 && (
          <p className="text-center text-surface-200/30 text-xs mt-10">
            Recommendations based on FSSAI packaging guidelines, BIS IS-code standards, and
            published food-science shelf-life studies. Always validate with a certified food
            technologist before production-scale deployment.
          </p>
        )}
      </main>
    </div>
  )
}
