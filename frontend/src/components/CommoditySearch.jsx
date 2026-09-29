import { useState, useEffect, useRef } from 'react'
import { Search, ChevronDown, X } from 'lucide-react'
import { searchCommodities } from '../api/packora.js'

/**
 * CommoditySearch — autocomplete dropdown for commodity selection.
 *
 * Props:
 *   value: { id, name } | null  — currently selected commodity
 *   onChange: (commodity | null) => void
 */
export default function CommoditySearch({ value, onChange }) {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState([])
  const [open, setOpen] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const inputRef = useRef(null)
  const dropdownRef = useRef(null)

  // Debounced search over backend API
  useEffect(() => {
    if (!open) return
    const timer = setTimeout(async () => {
      setLoading(true)
      setError(null)
      try {
        const data = await searchCommodities(query, 50)
        if (Array.isArray(data)) {
          setResults(data)
        } else {
          setResults([])
        }
      } catch (err) {
        setError('Unable to fetch commodities from server.')
        setResults([])
      } finally {
        setLoading(false)
      }
    }, 200)
    return () => clearTimeout(timer)
  }, [query, open])

  // Close on outside click
  useEffect(() => {
    const handler = (e) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target)) {
        setOpen(false)
      }
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [])

  const handleSelect = (commodity) => {
    onChange(commodity)
    setQuery('')
    setOpen(false)
  }

  const handleClear = () => {
    onChange(null)
    setQuery('')
    setOpen(false)
  }

  return (
    <div className="relative" ref={dropdownRef}>
      <label className="label" htmlFor="commodity-search">
        Food Commodity
      </label>

      {value ? (
        // Selected state
        <div className="flex items-center gap-3 input-field cursor-pointer" onClick={() => { onChange(null); setOpen(true) }}>
          <div className="w-2 h-2 rounded-full bg-brand-400 flex-shrink-0" />
          <span className="flex-1 font-medium text-white">{value.name}</span>
          <span className="badge-green">{value.category || 'Commodity'}</span>
          <button
            id="commodity-clear-btn"
            onClick={(e) => { e.stopPropagation(); handleClear() }}
            className="text-surface-200/50 hover:text-white transition-colors"
          >
            <X size={16} />
          </button>
        </div>
      ) : (
        // Search input
        <div className="relative">
          <Search size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-surface-200/50" />
          <input
            id="commodity-search"
            ref={inputRef}
            type="text"
            className="input-field pl-10 pr-10"
            placeholder="Search: paneer, turmeric, basmati rice…"
            value={query}
            onChange={(e) => { setQuery(e.target.value); setOpen(true) }}
            onFocus={() => setOpen(true)}
            autoComplete="off"
          />
          <ChevronDown
            size={16}
            className={`absolute right-3.5 top-1/2 -translate-y-1/2 text-surface-200/50 transition-transform duration-200 ${open ? 'rotate-180' : ''}`}
          />
        </div>
      )}

      {/* Dropdown */}
      {open && !value && (
        <div className="absolute z-50 w-full mt-2 card border-white/15 shadow-2xl shadow-black/50 overflow-hidden animate-fade-in">
          {loading ? (
            <div className="p-4 text-center text-surface-200/60 text-sm">Searching…</div>
          ) : results.length === 0 ? (
            <div className="p-4 text-center text-surface-200/60 text-sm">No commodities found</div>
          ) : (
            <ul className="max-h-64 overflow-y-auto scrollbar-thin" role="listbox">
              {results.map((c) => (
                <li
                  key={c.id}
                  role="option"
                  className="flex items-center gap-3 px-4 py-3 cursor-pointer hover:bg-white/8 transition-colors border-b border-white/5 last:border-0"
                  onMouseDown={() => handleSelect(c)}
                >
                  <div className="w-2 h-2 rounded-full bg-brand-400/60 flex-shrink-0" />
                  <div className="flex-1 min-w-0">
                    <p className="text-white text-sm font-medium truncate">{c.name}</p>
                    {c.description && (
                      <p className="text-surface-200/50 text-xs truncate mt-0.5">{c.description}</p>
                    )}
                  </div>
                  {c.category && (
                    <span className="badge-blue flex-shrink-0">{c.category}</span>
                  )}
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  )
}
