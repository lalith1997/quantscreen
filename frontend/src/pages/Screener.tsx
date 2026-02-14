import { useState, useEffect } from 'react'
import { useSearchParams, Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { 
  Filter, 
  Play, 
  Loader2, 
  AlertTriangle,
  CheckCircle,
  ChevronRight,
} from 'lucide-react'
import { clsx } from 'clsx'
import { screenerApi, type ScreenerResult } from '../services/api'

const presetOptions = [
  { id: 'magic_formula', name: 'Magic Formula Top 50' },
  { id: 'deep_value', name: 'Deep Value (Acquirer\'s Multiple)' },
  { id: 'quality_value', name: 'Quality at Reasonable Price' },
  { id: 'safe_stocks', name: 'Financially Safe Stocks' },
  { id: 'red_flag_watch', name: 'Manipulation Red Flags' },
]

export default function Screener() {
  const [searchParams] = useSearchParams()
  const initialPreset = searchParams.get('preset') || 'magic_formula'
  const [selectedPreset, setSelectedPreset] = useState(initialPreset)
  
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['screener', selectedPreset],
    queryFn: () => screenerApi.runPreset(selectedPreset),
    enabled: false,
  })
  
  useEffect(() => {
    refetch()
  }, [selectedPreset, refetch])
  
  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Stock Screener</h1>
          <p className="text-text-secondary mt-1">
            Run preset screens or build your own filters
          </p>
        </div>
      </div>
      
      <div className="card">
        <div className="flex items-center gap-2 mb-4">
          <Filter className="w-5 h-5 text-accent-blue" />
          <h2 className="font-semibold">Preset Screens</h2>
        </div>
        
        <div className="flex flex-wrap gap-2">
          {presetOptions.map((preset) => (
            <button
              key={preset.id}
              onClick={() => setSelectedPreset(preset.id)}
              className={clsx(
                'px-4 py-2 rounded-lg text-sm font-medium transition-colors',
                selectedPreset === preset.id
                  ? 'bg-accent-blue text-white'
                  : 'bg-surface-hover text-text-secondary hover:text-text-primary'
              )}
            >
              {preset.name}
            </button>
          ))}
        </div>
        
        <button
          onClick={() => refetch()}
          disabled={isLoading}
          className="btn btn-primary mt-4 flex items-center gap-2"
        >
          {isLoading ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              Running...
            </>
          ) : (
            <>
              <Play className="w-4 h-4" />
              Run Screen
            </>
          )}
        </button>
      </div>
      
      {error && (
        <div className="card border-accent-red/50 bg-accent-red/10">
          <p className="text-accent-red">Error running screen. Please try again.</p>
        </div>
      )}
      
      {data && (
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-semibold">Results ({data.total_count} stocks)</h2>
            <span className="text-sm text-text-tertiary">{data.execution_time_ms.toFixed(0)}ms</span>
          </div>
          
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-border">
                  <th className="text-left py-3 px-2 text-text-secondary font-medium text-sm">Rank</th>
                  <th className="text-left py-3 px-2 text-text-secondary font-medium text-sm">Ticker</th>
                  <th className="text-left py-3 px-2 text-text-secondary font-medium text-sm">Name</th>
                  <th className="text-left py-3 px-2 text-text-secondary font-medium text-sm">Sector</th>
                  <th className="text-right py-3 px-2 text-text-secondary font-medium text-sm">Market Cap</th>
                  <th className="text-right py-3 px-2 text-text-secondary font-medium text-sm">F-Score</th>
                  <th className="text-right py-3 px-2 text-text-secondary font-medium text-sm">P/E</th>
                  <th className="text-right py-3 px-2 text-text-secondary font-medium text-sm">ROE</th>
                  <th className="text-center py-3 px-2 text-text-secondary font-medium text-sm">Flags</th>
                  <th className="py-3 px-2"></th>
                </tr>
              </thead>
              <tbody>
                {data.results.map((result) => (
                  <ResultRow key={result.ticker} result={result} />
                ))}
              </tbody>
            </table>
          </div>
          
          {data.results.length === 0 && (
            <p className="text-center text-text-secondary py-8">
              No stocks match the current filters.
            </p>
          )}
        </div>
      )}
    </div>
  )
}

function ResultRow({ result }: { result: ScreenerResult }) {
  const fScore = result.metrics.f_score as number | null
  const mScoreFlag = result.metrics.m_score_flag as boolean | null
  const pe = result.metrics.pe_ratio as number | null
  const roe = result.metrics.roe as number | null
  
  const formatMarketCap = (value: number | null) => {
    if (!value) return '-'
    if (value >= 1e12) return `$${(value / 1e12).toFixed(1)}T`
    if (value >= 1e9) return `$${(value / 1e9).toFixed(1)}B`
    if (value >= 1e6) return `$${(value / 1e6).toFixed(0)}M`
    return `$${value.toLocaleString()}`
  }
  
  return (
    <tr className="border-b border-border hover:bg-surface-hover transition-colors">
      <td className="py-3 px-2 font-mono text-text-secondary">{result.rank}</td>
      <td className="py-3 px-2">
        <Link to={`/stock/${result.ticker}`} className="font-semibold text-accent-blue hover:underline">
          {result.ticker}
        </Link>
      </td>
      <td className="py-3 px-2 text-text-primary max-w-[200px] truncate">{result.name}</td>
      <td className="py-3 px-2 text-text-secondary text-sm">{result.sector || '-'}</td>
      <td className="py-3 px-2 text-right font-mono text-sm">{formatMarketCap(result.market_cap)}</td>
      <td className="py-3 px-2 text-right">
        {fScore !== null ? (
          <span className={clsx(
            'inline-flex items-center px-2 py-0.5 rounded text-sm font-medium',
            fScore >= 8 ? 'score-high' : fScore >= 5 ? 'score-medium' : 'score-low'
          )}>
            {fScore}
          </span>
        ) : '-'}
      </td>
      <td className="py-3 px-2 text-right font-mono text-sm">{pe !== null ? pe.toFixed(1) : '-'}</td>
      <td className="py-3 px-2 text-right font-mono text-sm">
        {roe !== null ? (
          <span className={roe > 0 ? 'metric-positive' : 'metric-negative'}>{roe.toFixed(1)}%</span>
        ) : '-'}
      </td>
      <td className="py-3 px-2 text-center">
        {mScoreFlag ? (
          <AlertTriangle className="w-4 h-4 text-accent-yellow inline" title="M-Score Warning" />
        ) : (
          <CheckCircle className="w-4 h-4 text-accent-green inline" title="Clean" />
        )}
      </td>
      <td className="py-3 px-2">
        <Link to={`/stock/${result.ticker}`} className="p-1 rounded hover:bg-surface text-text-secondary hover:text-text-primary transition-colors inline-flex">
          <ChevronRight className="w-4 h-4" />
        </Link>
      </td>
    </tr>
  )
}
