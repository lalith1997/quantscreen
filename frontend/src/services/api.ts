import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL || ''

const api = axios.create({
  baseURL: `${API_URL}/api`,
  headers: {
    'Content-Type': 'application/json',
  },
})

// ============== Existing Types ==============

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

// ============== Daily Brief Types ==============

export interface Strategy {
  timeframe: string
  entry_price: number | null
  stop_loss: number | null
  take_profit: number | null
  risk_reward_ratio: number | null
  confidence: 'high' | 'medium' | 'low' | null
  rationale: string | null
  signals: Record<string, unknown>
  analysis_date: string
}

export interface NewsArticle {
  id: number
  ticker: string | null
  title: string
  url: string
  source: string | null
  published_at: string | null
  sentiment: 'positive' | 'negative' | 'neutral' | null
  impact_score: number | null
  impact_explanation: string | null
}

export interface MarketRisk {
  risk_score: number | null
  risk_label: string | null
  vix_level: number | null
  sp500_price: number | null
  sp500_change_pct: number | null
  sector_data: Record<string, number>
  breadth_data: Record<string, unknown>
  summary_text: string | null
  snapshot_date: string
}

export interface DailyPick {
  ticker: string
  rank: number
  metrics: Record<string, number | boolean | null>
  rationale: string | null
  strategies?: Record<string, Strategy>
  news?: NewsArticle[]
}

export interface DailyBrief {
  run_date: string
  completed_at: string | null
  stocks_analyzed: number
  stocks_passed: number
  execution_time_seconds: number | null
  picks_by_screen: Record<string, DailyPick[]>
  market_risk: MarketRisk | null
}

// ============== API Functions ==============

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

export const dailyBriefApi = {
  getLatest: async () => {
    const response = await api.get<DailyBrief>('/daily-brief')
    return response.data
  },

  getHistory: async (days = 30) => {
    const response = await api.get('/daily-brief/history', { params: { days } })
    return response.data
  },

  getPicks: async (screen?: string) => {
    const response = await api.get('/daily-brief/picks', { params: { screen } })
    return response.data
  },

  trigger: async () => {
    const response = await api.post('/daily-brief/trigger')
    return response.data
  },
}

export const newsApi = {
  getStockNews: async (ticker: string, limit = 20) => {
    const response = await api.get<NewsArticle[]>(`/news/${ticker}`, { params: { limit } })
    return response.data
  },

  getMarketNews: async (limit = 20) => {
    const response = await api.get<NewsArticle[]>('/news/market', { params: { limit } })
    return response.data
  },
}

export const analysisApi = {
  getStrategy: async (ticker: string) => {
    const response = await api.get(`/analysis/${ticker}/strategy`)
    return response.data
  },
}

export const marketApi = {
  getRiskSummary: async () => {
    const response = await api.get<MarketRisk>('/market/risk-summary')
    return response.data
  },
}

export default api
