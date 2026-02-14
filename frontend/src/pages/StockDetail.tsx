import { useParams, Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import {
  ArrowLeft,
  AlertTriangle,
  CheckCircle,
  Loader2,
} from 'lucide-react'
import { clsx } from 'clsx'
import { companyApi } from '../services/api'

export default function StockDetail() {
  const { ticker } = useParams<{ ticker: string }>()
  
  const { data: company, isLoading, error } = useQuery({
    queryKey: ['company', ticker],
    queryFn: () => companyApi.get(ticker!),
    enabled: !!ticker,
  })
  
  const { data: metricsData } = useQuery({
    queryKey: ['metrics', ticker],
    queryFn: () => companyApi.getMetrics(ticker!),
    enabled: !!ticker,
  })
  
  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-accent-blue" />
      </div>
    )
  }
  
  if (error || !company) {
    return (
      <div className="card text-center py-12">
        <p className="text-accent-red mb-4">Error loading stock data</p>
        <Link to="/screener" className="btn btn-secondary">
          Back to Screener
        </Link>
      </div>
    )
  }
  
  const rawMetrics = company.metrics || {}
  const metrics: Record<string, number | null> = Object.fromEntries(
    Object.entries(rawMetrics).map(([k, v]) => [k, typeof v === 'number' ? v : null])
  )
  const coreScreeners = metricsData?.core_screeners || {}
  
  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div>
        <Link to="/screener" className="inline-flex items-center gap-1 text-text-secondary hover:text-text-primary mb-4">
          <ArrowLeft className="w-4 h-4" />
          Back to Screener
        </Link>
        
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-3xl font-bold">{company.ticker}</h1>
            <p className="text-text-secondary text-lg">{company.name}</p>
            <div className="flex items-center gap-4 mt-2 text-sm text-text-tertiary">
              <span>{company.sector || 'N/A'}</span>
              <span>•</span>
              <span>{company.exchange || 'N/A'}</span>
              <span>•</span>
              <span>{formatMarketCap(company.market_cap)}</span>
            </div>
          </div>
        </div>
      </div>
      
      {/* Core Screeners */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <ScoreCard
          title="Piotroski F-Score"
          value={coreScreeners.piotroski?.f_score}
          maxValue={9}
          interpretation={coreScreeners.piotroski?.interpretation}
          description="Financial strength (0-9)"
          goodThreshold={7}
          badThreshold={4}
        />
        
        <ScoreCard
          title="Altman Z-Score"
          value={coreScreeners.altman_z?.z_score}
          interpretation={coreScreeners.altman_z?.interpretation}
          description="Bankruptcy risk predictor"
          goodThreshold={2.99}
          badThreshold={1.81}
          format={(v) => v.toFixed(2)}
        />
        
        <ScoreCard
          title="Acquirer's Multiple"
          value={coreScreeners.acquirers_multiple}
          description="Enterprise Value / EBIT"
          goodThreshold={8}
          badThreshold={15}
          inverted
          format={(v) => v.toFixed(1) + 'x'}
        />
        
        <ScoreCard
          title="Beneish M-Score"
          value={coreScreeners.beneish_m?.m_score}
          interpretation={coreScreeners.beneish_m?.interpretation}
          description="Earnings manipulation detector"
          goodThreshold={-2.22}
          badThreshold={-1.78}
          inverted
          format={(v) => v.toFixed(2)}
          isWarning={coreScreeners.beneish_m?.is_red_flag}
        />
        
        <ScoreCard
          title="Sloan Accrual Ratio"
          value={coreScreeners.sloan_accrual?.accrual_ratio_pct}
          interpretation={coreScreeners.sloan_accrual?.interpretation}
          description="Earnings quality measure"
          goodThreshold={-5}
          badThreshold={10}
          inverted
          format={(v) => v.toFixed(1) + '%'}
          isWarning={coreScreeners.sloan_accrual?.is_red_flag}
        />
        
        <ScoreCard
          title="Earnings Yield"
          value={coreScreeners.magic_formula?.earnings_yield}
          description="EBIT / Enterprise Value"
          goodThreshold={0.1}
          badThreshold={0.05}
          format={(v) => (v * 100).toFixed(1) + '%'}
        />
      </div>
      
      {/* Valuation Ratios */}
      <div className="card">
        <h2 className="text-xl font-semibold mb-4">Valuation Ratios</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <MetricItem label="P/E Ratio" value={metrics.pe_ratio} format={(v) => v.toFixed(1)} />
          <MetricItem label="P/B Ratio" value={metrics.pb_ratio} format={(v) => v.toFixed(2)} />
          <MetricItem label="P/S Ratio" value={metrics.ps_ratio} format={(v) => v.toFixed(2)} />
          <MetricItem label="EV/EBITDA" value={metrics.ev_ebitda} format={(v) => v.toFixed(1)} />
        </div>
      </div>
      
      {/* Profitability */}
      <div className="card">
        <h2 className="text-xl font-semibold mb-4">Profitability</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <MetricItem label="ROE" value={metrics.roe} format={(v) => v.toFixed(1) + '%'} isPercentage />
          <MetricItem label="ROA" value={metrics.roa} format={(v) => v.toFixed(1) + '%'} isPercentage />
          <MetricItem label="Gross Margin" value={metrics.gross_margin} format={(v) => v.toFixed(1) + '%'} isPercentage />
          <MetricItem label="Net Margin" value={metrics.net_margin} format={(v) => v.toFixed(1) + '%'} isPercentage />
        </div>
      </div>
      
      {/* Financial Health */}
      <div className="card">
        <h2 className="text-xl font-semibold mb-4">Financial Health</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <MetricItem label="Current Ratio" value={metrics.current_ratio} format={(v) => v.toFixed(2)} />
          <MetricItem label="Debt/Equity" value={metrics.debt_to_equity} format={(v) => v.toFixed(2)} />
        </div>
      </div>
    </div>
  )
}

function formatMarketCap(value: number | null): string {
  if (!value) return 'N/A'
  if (value >= 1e12) return `$${(value / 1e12).toFixed(1)}T`
  if (value >= 1e9) return `$${(value / 1e9).toFixed(1)}B`
  if (value >= 1e6) return `$${(value / 1e6).toFixed(0)}M`
  return `$${value.toLocaleString()}`
}

function ScoreCard({
  title,
  value,
  maxValue,
  interpretation,
  description,
  goodThreshold,
  badThreshold,
  inverted = false,
  format = (v: number) => v.toString(),
  isWarning = false,
}: {
  title: string
  value: number | null | undefined
  maxValue?: number
  interpretation?: string
  description: string
  goodThreshold: number
  badThreshold: number
  inverted?: boolean
  format?: (v: number) => string
  isWarning?: boolean
}) {
  const getStatus = () => {
    if (value === null || value === undefined) return 'neutral'
    if (inverted) {
      if (value <= goodThreshold) return 'good'
      if (value >= badThreshold) return 'bad'
    } else {
      if (value >= goodThreshold) return 'good'
      if (value <= badThreshold) return 'bad'
    }
    return 'neutral'
  }
  
  const status = getStatus()
  
  return (
    <div className={clsx(
      'card',
      isWarning && 'border-accent-yellow/50 bg-accent-yellow/5'
    )}>
      <div className="flex items-start justify-between mb-2">
        <h3 className="font-medium text-text-secondary">{title}</h3>
        {isWarning ? (
          <AlertTriangle className="w-5 h-5 text-accent-yellow" />
        ) : status === 'good' ? (
          <CheckCircle className="w-5 h-5 text-accent-green" />
        ) : status === 'bad' ? (
          <AlertTriangle className="w-5 h-5 text-accent-red" />
        ) : null}
      </div>
      
      <div className="flex items-baseline gap-2">
        <span className={clsx(
          'text-2xl font-bold font-mono',
          status === 'good' && 'text-accent-green',
          status === 'bad' && 'text-accent-red',
          status === 'neutral' && 'text-text-primary'
        )}>
          {value !== null && value !== undefined ? format(value) : '-'}
        </span>
        {maxValue && <span className="text-text-tertiary">/ {maxValue}</span>}
      </div>
      
      {interpretation && (
        <p className="text-sm text-text-secondary mt-1">{interpretation}</p>
      )}
      <p className="text-xs text-text-tertiary mt-2">{description}</p>
    </div>
  )
}

function MetricItem({
  label,
  value,
  format = (v: number) => v.toString(),
  isPercentage = false,
}: {
  label: string
  value: number | null | undefined
  format?: (v: number) => string
  isPercentage?: boolean
}) {
  return (
    <div className="p-3 rounded-lg bg-background-secondary">
      <p className="text-sm text-text-secondary">{label}</p>
      <p className={clsx(
        'text-lg font-semibold font-mono mt-1',
        isPercentage && value !== null && value !== undefined && (
          value > 0 ? 'text-accent-green' : value < 0 ? 'text-accent-red' : 'text-text-primary'
        )
      )}>
        {value !== null && value !== undefined ? format(value) : '-'}
      </p>
    </div>
  )
}
