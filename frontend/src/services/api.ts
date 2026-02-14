import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL || ''

const api = axios.create({
  baseURL: `${API_URL}/api`,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Types
export interface Company {
  id: number
  ticker: string
  name: string
  exchange: string | null
  sector: string | null
  industry: string | null
  market_cap: number | null
  country: string
  currency: string
  is_active: boolean
  created_at: string
  updated_at: string
  metrics?: Record<string, number | boolean | null>
}

export interface ScreenerFilter {
  metric: string
  operator: '>' | '<' | '>=' | '<=' | '==' | 'between' | 'in'
  value: number | number[] | string[]
  percentile?: boolean
  sector_relative?: boolean
}

export interface ScreenerRequest {
  filters: ScreenerFilter[]
  logic?: 'AND' | 'OR'
  sort_by?: string
  sort_order?: 'asc' | 'desc'
  limit?: number
  offset?: number
  exclude_sectors?: string[]
  min_market_cap?: number
  max_market_cap?: number
}

export interface ScreenerResult {
  ticker: string
  name: string
  sector: string | null
  market_cap: number | null
  metrics: Record<string, number | boolean | null>
  rank: number
}

export interface ScreenerResponse {
  results: ScreenerResult[]
  total_count: number
  filters_applied: ScreenerFilter[]
  execution_time_ms: number
}

export interface PresetScreen {
  id: string
  name: string
  description: string
}

// API Functions
export const companyApi = {
  list: async (params?: {
    sector?: string
    country?: string
    min_market_cap?: number
    limit?: number
    offset?: number
  }) => {
    const response = await api.get<Company[]>('/companies', { params })
    return response.data
  },
  
  search: async (query: string) => {
    const response = await api.get<{ ticker: string; name: string; sector: string }[]>(
      '/companies/search',
      { params: { q: query } }
    )
    return response.data
  },
  
  get: async (ticker: string) => {
    const response = await api.get<Company>(`/companies/${ticker}`)
    return response.data
  },
  
  getMetrics: async (ticker: string) => {
    const response = await api.get(`/companies/${ticker}/metrics`)
    return response.data
  },
  
  getFundamentals: async (ticker: string) => {
    const response = await api.get(`/companies/${ticker}/fundamentals`)
    return response.data
  },
  
  getPrices: async (ticker: string, days = 365) => {
    const response = await api.get(`/companies/${ticker}/prices`, { params: { days } })
    return response.data
  },
  
  getSectors: async () => {
    const response = await api.get<string[]>('/companies/sectors')
    return response.data
  },
}

export const screenerApi = {
  getPresets: async () => {
    const response = await api.get<PresetScreen[]>('/screener/presets')
    return response.data
  },
  
  runPreset: async (presetId: string, limit?: number) => {
    const response = await api.post<ScreenerResponse>(
      `/screener/presets/${presetId}/run`,
      null,
      { params: { limit } }
    )
    return response.data
  },
  
  runCustom: async (request: ScreenerRequest) => {
    const response = await api.post<ScreenerResponse>('/screener/run', request)
    return response.data
  },
}

export default api
