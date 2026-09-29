import { Thermometer, Truck, Calendar, Scale } from 'lucide-react'

const STORAGE_OPTIONS = [
  { value: 'ambient', label: 'Ambient (room temperature)' },
  { value: 'refrigerated', label: 'Refrigerated (0–8°C)' },
  { value: 'frozen', label: 'Frozen (< –18°C)' },
]

const TRANSPORT_OPTIONS = [
  { value: 'standard', label: 'Standard truck / rail' },
  { value: 'cold_chain', label: 'Cold chain vehicle' },
  { value: 'controlled_atmosphere', label: 'Controlled atmosphere' },
]

/**
 * ConditionsForm — shelf life, storage, transport, and weight preferences.
 *
 * Props:
 *   values: { target_shelf_life_days, storage_condition, transport_condition,
 *             weight_cost, weight_sustainability, weight_shelf_life }
 *   onChange: (field, value) => void
 */
export default function ConditionsForm({ values, onChange }) {
  const weightsSum = (
    parseFloat(values.weight_cost) +
    parseFloat(values.weight_sustainability) +
    parseFloat(values.weight_shelf_life)
  ).toFixed(2)
  const weightsValid = Math.abs(parseFloat(weightsSum) - 1.0) < 0.01

  return (
    <div className="space-y-6">
      {/* Shelf Life */}
      <div>
        <label className="label" htmlFor="shelf-life-input">
          <Calendar size={14} className="inline mr-1.5 text-brand-400" />
          Target Shelf Life
        </label>
        <div className="flex flex-col sm:flex-row sm:items-center gap-3">
          <div className="flex items-center gap-2">
            <input
              id="shelf-life-input"
              type="number"
              min="1"
              max="730"
              className="input-field w-28 sm:w-32 text-center text-lg font-semibold"
              value={values.target_shelf_life_days}
              onChange={(e) => onChange('target_shelf_life_days', parseInt(e.target.value, 10))}
            />
            <span className="text-surface-200/60 text-sm">days</span>
          </div>
          <div className="flex flex-wrap gap-1.5">
            {[7, 30, 90, 180, 365].map(d => (
              <button
                key={d}
                type="button"
                id={`shelf-life-preset-${d}`}
                onClick={() => onChange('target_shelf_life_days', d)}
                className={`px-2.5 py-1 rounded-lg text-xs font-medium transition-all duration-150 ${
                  values.target_shelf_life_days === d
                    ? 'bg-brand-500 text-white'
                    : 'bg-white/5 text-surface-200/60 hover:bg-white/10 hover:text-white'
                }`}
              >
                {d < 365 ? `${d}d` : '1yr'}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Storage + Transport */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div>
          <label className="label" htmlFor="storage-select">
            <Thermometer size={14} className="inline mr-1.5 text-brand-400" />
            Storage Condition
          </label>
          <select
            id="storage-select"
            className="select-field"
            value={values.storage_condition}
            onChange={(e) => onChange('storage_condition', e.target.value)}
          >
            {STORAGE_OPTIONS.map(o => (
              <option key={o.value} value={o.value} className="bg-surface-900">{o.label}</option>
            ))}
          </select>
        </div>
        <div>
          <label className="label" htmlFor="transport-select">
            <Truck size={14} className="inline mr-1.5 text-brand-400" />
            Transport Condition
          </label>
          <select
            id="transport-select"
            className="select-field"
            value={values.transport_condition}
            onChange={(e) => onChange('transport_condition', e.target.value)}
          >
            {TRANSPORT_OPTIONS.map(o => (
              <option key={o.value} value={o.value} className="bg-surface-900">{o.label}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Priority Weights */}
      <div>
        <label className="label">
          <Scale size={14} className="inline mr-1.5 text-brand-400" />
          Scoring Priorities
          {!weightsValid && (
            <span className="block sm:inline sm:ml-2 text-amber-400 text-xs">(must sum to 1.0 — currently {weightsSum})</span>
          )}
        </label>
        <div className="space-y-3">
          {[
            { field: 'weight_shelf_life', label: 'Shelf Life Extension' },
            { field: 'weight_cost', label: 'Cost Efficiency' },
            { field: 'weight_sustainability', label: 'Sustainability' },
          ].map(({ field, label }) => (
            <div key={field} className="flex items-center gap-2 sm:gap-3">
              <span className="text-xs sm:text-sm text-surface-200/70 w-28 sm:w-40 flex-shrink-0 truncate">{label}</span>
              <input
                id={`weight-${field}`}
                type="range"
                min="0"
                max="1"
                step="0.05"
                className="flex-1 accent-brand-500 cursor-pointer"
                value={values[field]}
                onChange={(e) => onChange(field, parseFloat(e.target.value))}
              />
              <span className="text-xs sm:text-sm font-mono text-white w-9 sm:w-10 text-right">
                {Math.round(values[field] * 100)}%
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
