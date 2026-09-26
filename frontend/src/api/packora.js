/**
 * Packora API client — axios wrappers for all three endpoints.
 *
 * Base URL comes from the Vite proxy (/api → FastAPI backend).
 * All functions return the response data directly and throw on HTTP errors.
 */
import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
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
