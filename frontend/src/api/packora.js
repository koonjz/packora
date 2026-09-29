/**
 * Packora API client — axios wrappers for all backend endpoints.
 *
 * Base URL resolution:
 *   - Local dev:   VITE_API_BASE_URL is unset → uses Vite proxy at /api
 *                  vite.config.js proxies /api → http://localhost:8000 (strips /api)
 *                  so FastAPI sees /commodities, /recommend, /materials
 *
 *   - Production:  VITE_API_BASE_URL = https://packora.onrender.com
 *                  axios calls https://packora.onrender.com/commodities, etc.
 *                  FastAPI on Render sees /commodities, /recommend, /materials
 *
 * Never hardcode a URL here — always use the env var or the /api proxy default.
 */
import axios from 'axios'

// In production: set VITE_API_BASE_URL=https://packora.onrender.com in Vercel env vars.
// Locally: leave unset — Vite proxy handles /api → http://localhost:8000.
const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api'

const api = axios.create({
  baseURL: API_BASE,
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
})

/**
 * GET /commodities?q=<search>&limit=<n>
 * Returns: CommodityOut[]
 */
export async function searchCommodities(q = '', limit = 50) {
  const { data } = await api.get('/commodities', { params: { q, limit } })
  return data
}

/**
 * GET /commodities/:id
 * Returns: CommodityOut
 */
export async function getCommodity(id) {
  const { data } = await api.get(`/commodities/${id}`)
  return data
}

/**
 * GET /materials
 * Returns: PackagingMaterialOut[]
 */
export async function getMaterials() {
  const { data } = await api.get('/materials')
  return data
}

/**
 * POST /recommend
 * @param {Object} payload — matches RecommendRequest schema
 * Returns: RecommendResponse
 */
export async function getRecommendations(payload) {
  const { data } = await api.post('/recommend', payload)
  return data
}

/**
 * GET /health
 * Returns: { status: "ok", service: "packora-api" }
 */
export async function checkHealth() {
  const { data } = await api.get('/health')
  return data
}
