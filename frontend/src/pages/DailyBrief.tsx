import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import {
  Newspaper,
  RefreshCw,
  TrendingUp,
  TrendingDown,
  Shield,
  AlertTriangle,
  ChevronDown,
  ChevronRight,
  ExternalLink,
  Clock,
  BarChart3,
  Target,
  Zap,
  Calendar,
} from 'lucide-react'
import { clsx } from 'clsx'
import { dailyBriefApi, type DailyBrief as DailyBriefType, type DailyPick, type Strategy, type NewsArticle, type MarketRisk } from '../services/api'

const SCREEN_LABELS: Record<string, { name: string; description: string }> = {
  magic_formula: { name: 'Magic Formula', description: 'Highest earnings yield + return on capital' },
  deep_value: { name: 'Deep Value', description: 'Lowest EV/EBIT with decent financial health' },
  quality_value: { name: 'Quality at Reasonable Price', description: 'High F-Score + low P/E + high ROE' },
  safe_stocks: { name: 'Financially Safe', description: 'Safe Z-Score + high F-Score + no manipulation flags' },
}

function formatMarketCap(cap: number | null | undefined): string {
  if (!cap) return 'N/A'
  if (cap >= 1e12) return `$${(cap / 1e12).toFixed(1)}T`
  if (cap >= 1e9) return `$${(cap / 1e9).toFixed(1)}B`
  if (cap >= 1e6) return `$${(cap / 1e6).toFixed(0)}M`
  return `$${cap.toLocaleString()}`
}

function formatDate(dateStr: string | null): string {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  return d.toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })
}

function timeAgo(dateStr: string | null): string {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  const now = new Date()
  const hours = Math.floor((now.getTime() - d.getTime()) / (1000 * 60 * 60))
  if (hours < 1) return 'just now'
  if (hours < 24) return `${hours}h ago`
  const days = Math.floor(hours / 24)
  return `${days}d ago`
}

// ============== Market Risk Card ==============

function MarketRiskCard({ risk }: { risk: MarketRisk }) {
  const riskColor = (score: number | null) => {
    if (!score) return 'text-text-secondary'
    if (score <= 3) return 'text-accent-green'
    if (score <= 5) return 'text-accent-yellow'
    if (score <= 7) return 'text-accent-red'
    return 'text-accent-red'
  }

  const riskBg = (score: number | null) => {
    if (!score) return 'bg-surface'
    if (score <= 3) return 'bg-accent-green/10'
    if (score <= 5) return 'bg-accent-yellow/10'
    return 'bg-accent-red/10'
  }

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold flex items-center gap-2">
          <Shield className="w-5 h-5 text-accent-blue" />
          Market Risk Assessment
        </h2>
        {risk.snapshot_date && (
          <span className="text-xs text-text-tertiary">{risk.snapshot_date}</span>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">
        {/* Risk Score */}
        <div className={clsx('rounded-lg p-4 text-center', riskBg(risk.risk_score))}>
          <div className={clsx('text-3xl font-bold', riskColor(risk.risk_score))}>
            {risk.risk_score ?? '--'}/10
          </div>
          <div className={clsx('text-sm font-medium', riskColor(risk.risk_score))}>
            {risk.risk_label ?? 'Unknown'}
          </div>
        </div>

        {/* VIX */}
        <div className="bg-background-secondary rounded-lg p-4 text-center">
          <div className="text-2xl font-bold text-text-primary">
            {risk.vix_level?.toFixed(1) ?? '--'}
          </div>
          <div className="text-xs text-text-tertiary">VIX</div>
        </div>

        {/* S&P 500 Change */}
        <div className="bg-background-secondary rounded-lg p-4 text-center">
          <div className={clsx(
            'text-2xl font-bold',
            risk.sp500_change_pct && risk.sp500_change_pct > 0 ? 'text-accent-green' : 'text-accent-red'
          )}>
            {risk.sp500_change_pct
              ? `${risk.sp500_change_pct > 0 ? '+' : ''}${risk.sp500_change_pct.toFixed(1)}%`
              : '--'}
          </div>
          <div className="text-xs text-text-tertiary">S&P 500</div>
        </div>

        {/* S&P 500 Price */}
        <div className="bg-background-secondary rounded-lg p-4 text-center">
          <div className="text-2xl font-bold text-text-primary">
            {risk.sp500_price ? risk.sp500_price.toLocaleString(undefined, { maximumFractionDigits: 0 }) : '--'}
          </div>
          <div className="text-xs text-text-tertiary">S&P 500 Level</div>
        </div>
      </div>

      {/* Summary Text */}
      {risk.summary_text && (
        <p className="text-sm text-text-secondary leading-relaxed">{risk.summary_text}</p>
      )}

      {/* Sector Performance */}
      {risk.sector_data && Object.keys(risk.sector_data).length > 0 && (
        <div className="mt-4">
          <h3 className="text-xs font-semibold text-text-tertiary uppercase mb-2">Sector Performance</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-2">
            {Object.entries(risk.sector_data)
              .sort((a, b) => (b[1] ?? 0) - (a[1] ?? 0))
              .map(([sector, change]) => (
                <div
                  key={sector}
                  className={clsx(
                    'rounded-lg px-3 py-2 text-center text-xs',
                    change > 0 ? 'bg-accent-green/10 text-accent-green' : 'bg-accent-red/10 text-accent-red'
                  )}
                >
                  <div className="font-medium truncate">{sector}</div>
                  <div className="font-bold">{change > 0 ? '+' : ''}{change.toFixed(1)}%</div>
                </div>
              ))}
          </div>
        </div>
      )}
    </div>
  )
}

// ============== Strategy Panel ==============

function StrategyPanel({ strategies }: { strategies: Record<string, Strategy> }) {
  const [activeTab, setActiveTab] = useState<string>('swing')
  const tabs = [
    { key: 'swing', label: 'Swing', icon: Zap, desc: 'Days to weeks' },
    { key: 'position', label: 'Position', icon: BarChart3, desc: 'Weeks to months' },
    { key: 'longterm', label: 'Long-term', icon: Calendar, desc: 'Months+' },
  ]

  const strategy = strategies[activeTab]

  const confidenceClass = (c: string | null) => {
    if (c === 'high') return 'bg-accent-green/20 text-accent-green'
    if (c === 'medium') return 'bg-accent-yellow/20 text-accent-yellow'
    return 'bg-border text-text-secondary'
  }

  return (
    <div className="mt-3">
      <div className="flex gap-1 mb-3">
        {tabs.map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            className={clsx(
              'flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors',
              activeTab === tab.key
                ? 'bg-accent-blue/20 text-accent-blue'
                : 'text-text-tertiary hover:text-text-secondary hover:bg-surface-hover'
            )}
          >
            <tab.icon className="w-3 h-3" />
            {tab.label}
          </button>
        ))}
      </div>

      {strategy ? (
        <div className="bg-background-secondary rounded-lg p-3 space-y-3">
          {/* Price levels */}
          <div className="grid grid-cols-3 gap-3">
            <div>
              <div className="text-xs text-text-tertiary">Entry</div>
              <div className="text-sm font-semibold text-accent-blue">
                ${strategy.entry_price?.toFixed(2) ?? '--'}
              </div>
            </div>
            <div>
              <div className="text-xs text-text-tertiary">Stop-Loss</div>
              <div className="text-sm font-semibold text-accent-red">
                ${strategy.stop_loss?.toFixed(2) ?? '--'}
              </div>
            </div>
            <div>
              <div className="text-xs text-text-tertiary">Target</div>
              <div className="text-sm font-semibold text-accent-green">
                ${strategy.take_profit?.toFixed(2) ?? '--'}
              </div>
            </div>
          </div>

          {/* Confidence + R/R */}
          <div className="flex items-center gap-3">
            {strategy.confidence && (
              <span className={clsx('text-xs px-2 py-0.5 rounded-full font-medium', confidenceClass(strategy.confidence))}>
                {strategy.confidence} confidence
              </span>
            )}
            {strategy.risk_reward_ratio && (
              <span className="text-xs text-text-tertiary">
                R/R: 1:{strategy.risk_reward_ratio.toFixed(1)}
              </span>
            )}
          </div>

          {/* Rationale */}
          {strategy.rationale && (
            <p className="text-xs text-text-secondary leading-relaxed">{strategy.rationale}</p>
          )}
        </div>
      ) : (
        <div className="text-xs text-text-tertiary bg-background-secondary rounded-lg p-3">
          No {activeTab} strategy available for this stock.
        </div>
      )}
    </div>
  )
}

// ============== News Feed ==============

function NewsFeed({ news }: { news: NewsArticle[] }) {
  if (!news.length) return null

  const sentimentClass = (s: string | null) => {
    if (s === 'positive') return 'bg-accent-green/20 text-accent-green'
    if (s === 'negative') return 'bg-accent-red/20 text-accent-red'
    return 'bg-border text-text-secondary'
  }

  return (
    <div className="mt-3 space-y-2">
      <h4 className="text-xs font-semibold text-text-tertiary uppercase">Recent News</h4>
      {news.map((article) => (
        <a
          key={article.id}
          href={article.url}
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-start gap-2 bg-background-secondary rounded-lg p-2 hover:bg-surface-hover transition-colors group"
        >
          <div className="flex-1 min-w-0">
            <div className="text-xs font-medium text-text-primary group-hover:text-accent-blue line-clamp-2">
              {article.title}
            </div>
            <div className="flex items-center gap-2 mt-1">
              {article.sentiment && (
                <span className={clsx('text-[10px] px-1.5 py-0.5 rounded-full', sentimentClass(article.sentiment))}>
                  {article.sentiment}
                </span>
              )}
              {article.source && (
                <span className="text-[10px] text-text-tertiary">{article.source}</span>
              )}
              {article.published_at && (
                <span className="text-[10px] text-text-tertiary">{timeAgo(article.published_at)}</span>
              )}
            </div>
          </div>
          <ExternalLink className="w-3 h-3 text-text-tertiary flex-shrink-0 mt-0.5" />
        </a>
      ))}
    </div>
  )
}

// ============== Pick Card ==============

function PickCard({ pick }: { pick: DailyPick }) {
  const [expanded, setExpanded] = useState(false)

  const metricValue = (key: string, format?: (v: number) => string) => {
    const val = pick.metrics[key]
    if (val === null || val === undefined || typeof val === 'boolean') return null
    return format ? format(val as number) : val
  }

  return (
    <div className="card">
      <div
        className="flex items-center justify-between cursor-pointer"
        onClick={() => setExpanded(!expanded)}
      >
        <div className="flex items-center gap-3 min-w-0">
          <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-accent-blue/20 text-accent-blue text-sm font-bold">
            #{pick.rank}
          </div>
          <div className="min-w-0">
            <div className="flex items-center gap-2">
              <Link
                to={`/stock/${pick.ticker}`}
                className="text-sm font-bold text-accent-blue hover:underline"
                onClick={(e) => e.stopPropagation()}
              >
                {pick.ticker}
              </Link>
              <span className="text-xs text-text-tertiary">
                {formatMarketCap(pick.metrics.market_cap as number | null)}
              </span>
            </div>
            {pick.rationale && (
              <p className="text-xs text-text-secondary line-clamp-1 mt-0.5">{pick.rationale}</p>
            )}
          </div>
        </div>

        <div className="flex items-center gap-3 flex-shrink-0">
          {/* Key metrics at a glance */}
          {metricValue('f_score') !== null && (
            <div className="hidden sm:block text-center">
              <div className={clsx(
                'text-xs font-bold',
                (pick.metrics.f_score as number) >= 7 ? 'text-accent-green' : (pick.metrics.f_score as number) >= 5 ? 'text-accent-yellow' : 'text-accent-red'
              )}>
                {pick.metrics.f_score as number}/9
              </div>
              <div className="text-[10px] text-text-tertiary">F-Score</div>
            </div>
          )}
          {metricValue('pe_ratio') !== null && (
            <div className="hidden sm:block text-center">
              <div className="text-xs font-bold text-text-primary">
                {(pick.metrics.pe_ratio as number)?.toFixed(1)}
              </div>
              <div className="text-[10px] text-text-tertiary">P/E</div>
            </div>
          )}

          {expanded ? <ChevronDown className="w-4 h-4 text-text-tertiary" /> : <ChevronRight className="w-4 h-4 text-text-tertiary" />}
        </div>
      </div>

      {expanded && (
        <div className="mt-4 pt-4 border-t border-border animate-fade-in">
          {/* Metrics Grid */}
          <div className="grid grid-cols-3 sm:grid-cols-6 gap-3 mb-4">
            {[
              { key: 'f_score', label: 'F-Score', fmt: (v: number) => `${v}/9` },
              { key: 'z_score', label: 'Z-Score', fmt: (v: number) => v.toFixed(2) },
              { key: 'pe_ratio', label: 'P/E', fmt: (v: number) => v.toFixed(1) },
              { key: 'roe', label: 'ROE', fmt: (v: number) => `${v.toFixed(1)}%` },
              { key: 'acquirers_multiple', label: "Acq. Mult", fmt: (v: number) => `${v.toFixed(1)}x` },
              { key: 'earnings_yield', label: 'Earn. Yield', fmt: (v: number) => `${(v * 100).toFixed(1)}%` },
            ].map(({ key, label, fmt }) => {
              const val = metricValue(key, fmt)
              if (val === null) return null
              return (
                <div key={key} className="bg-background-secondary rounded-lg p-2 text-center">
                  <div className="text-xs font-semibold text-text-primary">{val}</div>
                  <div className="text-[10px] text-text-tertiary">{label}</div>
                </div>
              )
            })}
          </div>

          {/* Strategy Panel */}
          {pick.strategies && Object.keys(pick.strategies).length > 0 && (
            <StrategyPanel strategies={pick.strategies} />
          )}

          {/* News Feed */}
          {pick.news && pick.news.length > 0 && <NewsFeed news={pick.news} />}
        </div>
      )}
    </div>
  )
}

// ============== Main Page ==============

export default function DailyBrief() {
  const queryClient = useQueryClient()

  const { data: brief, isLoading, error } = useQuery({
    queryKey: ['daily-brief'],
    queryFn: () => dailyBriefApi.getLatest(),
    staleTime: 2 * 60 * 1000,
    retry: false,
  })

  const triggerMutation = useMutation({
    mutationFn: () => dailyBriefApi.trigger(),
    onSuccess: () => {
      // Poll for results after triggering
      setTimeout(() => queryClient.invalidateQueries({ queryKey: ['daily-brief'] }), 5000)
    },
  })

  // Empty state — no analysis yet
  if (!isLoading && (error || !brief)) {
    return (
      <div className="space-y-6 animate-fade-in">
        <div className="text-center py-16">
          <Newspaper className="w-16 h-16 text-text-tertiary mx-auto mb-4" />
          <h1 className="text-2xl font-bold mb-2">Daily Pre-Market Brief</h1>
          <p className="text-text-secondary mb-6 max-w-md mx-auto">
            No analysis has been run yet. Click below to trigger the daily analysis engine.
            It will scan all S&P 500 stocks + ETFs, apply filters, generate strategies, and fetch news.
          </p>
          <button
            onClick={() => triggerMutation.mutate()}
            disabled={triggerMutation.isPending}
            className="btn btn-primary inline-flex items-center gap-2"
          >
            <RefreshCw className={clsx('w-4 h-4', triggerMutation.isPending && 'animate-spin')} />
            {triggerMutation.isPending ? 'Triggering...' : 'Run Daily Analysis'}
          </button>
          {triggerMutation.isSuccess && (
            <p className="text-sm text-accent-green mt-3">
              Analysis triggered. This may take several minutes. Refresh the page shortly.
            </p>
          )}
        </div>
      </div>
    )
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-20">
        <RefreshCw className="w-6 h-6 text-accent-blue animate-spin" />
        <span className="ml-3 text-text-secondary">Loading daily brief...</span>
      </div>
    )
  }

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-3">
            <Newspaper className="w-7 h-7 text-accent-blue" />
            Daily Pre-Market Brief
          </h1>
          <div className="flex items-center gap-3 mt-1">
            <span className="text-sm text-text-secondary">{formatDate(brief!.run_date)}</span>
            {brief!.completed_at && (
              <span className="text-xs text-text-tertiary flex items-center gap-1">
                <Clock className="w-3 h-3" />
                Completed {timeAgo(brief!.completed_at)}
              </span>
            )}
            <span className="text-xs bg-accent-blue/20 text-accent-blue px-2 py-0.5 rounded-full">
              {brief!.stocks_analyzed} stocks analyzed
            </span>
          </div>
        </div>

        <button
          onClick={() => triggerMutation.mutate()}
          disabled={triggerMutation.isPending}
          className="btn btn-secondary inline-flex items-center gap-2 text-sm"
        >
          <RefreshCw className={clsx('w-4 h-4', triggerMutation.isPending && 'animate-spin')} />
          Re-run
        </button>
      </div>

      {/* Market Risk */}
      {brief!.market_risk && <MarketRiskCard risk={brief!.market_risk} />}

      {/* Picks by Screen */}
      {brief!.picks_by_screen && Object.entries(brief!.picks_by_screen).map(([screenName, picks]) => {
        const label = SCREEN_LABELS[screenName]
        return (
          <div key={screenName}>
            <div className="flex items-center justify-between mb-3">
              <div>
                <h2 className="text-lg font-semibold flex items-center gap-2">
                  <Target className="w-5 h-5 text-accent-purple" />
                  {label?.name ?? screenName}
                </h2>
                {label?.description && (
                  <p className="text-xs text-text-tertiary mt-0.5">{label.description}</p>
                )}
              </div>
              <span className="text-xs bg-surface px-2 py-1 rounded-lg text-text-secondary">
                {picks.length} stocks
              </span>
            </div>

            <div className="space-y-2">
              {picks.slice(0, 10).map((pick) => (
                <PickCard key={`${screenName}-${pick.ticker}`} pick={pick} />
              ))}
              {picks.length > 10 && (
                <p className="text-xs text-text-tertiary text-center py-2">
                  +{picks.length - 10} more stocks in this screen
                </p>
              )}
            </div>
          </div>
        )
      })}

      {/* Execution Info Footer */}
      {brief!.execution_time_seconds && (
        <div className="text-center text-xs text-text-tertiary py-4">
          Analysis completed in {brief!.execution_time_seconds.toFixed(1)}s
          {' | '}{brief!.stocks_passed} stocks passed filters out of {brief!.stocks_analyzed} analyzed
        </div>
      )}
    </div>
  )
}
