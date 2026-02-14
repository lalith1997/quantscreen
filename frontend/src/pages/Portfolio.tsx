import { useState, useRef } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  Briefcase,
  Plus,
  Upload,
  RefreshCw,
  AlertTriangle,
  TrendingUp,
  TrendingDown,
  X,
  Bell,
  Activity,
  Shield,
  Check,
} from 'lucide-react'
import { clsx } from 'clsx'
import {
  portfolioApi,
  type PortfolioHolding,
  type PortfolioAlert,
  type PortfolioAnalysis,
} from '../services/api'

// ============== Add Holding Modal ==============

function AddHoldingModal({ onClose }: { onClose: () => void }) {
  const queryClient = useQueryClient()
  const [form, setForm] = useState({
    ticker: '',
    shares: '',
    avg_cost_basis: '',
    buy_date: '',
    notes: '',
  })

  const addMutation = useMutation({
    mutationFn: () =>
      portfolioApi.addHolding({
        ticker: form.ticker.toUpperCase(),
        shares: parseFloat(form.shares),
        avg_cost_basis: parseFloat(form.avg_cost_basis),
        buy_date: form.buy_date || undefined,
        notes: form.notes || undefined,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['portfolio-holdings'] })
      onClose()
    },
  })

  const isValid = form.ticker && form.shares && form.avg_cost_basis

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
      <div className="card w-full max-w-md mx-4">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold">Add Holding</h3>
          <button onClick={onClose} className="p-1 rounded hover:bg-surface-hover">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="space-y-3">
          <div>
            <label className="text-xs font-medium text-text-secondary">Ticker *</label>
            <input
              type="text"
              value={form.ticker}
              onChange={(e) => setForm({ ...form, ticker: e.target.value.toUpperCase() })}
              placeholder="AAPL"
              className="w-full mt-1 px-3 py-2 bg-background-secondary rounded-lg border border-border text-sm focus:outline-none focus:border-accent-blue"
            />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-xs font-medium text-text-secondary">Shares *</label>
              <input
                type="number"
                value={form.shares}
                onChange={(e) => setForm({ ...form, shares: e.target.value })}
                placeholder="100"
                className="w-full mt-1 px-3 py-2 bg-background-secondary rounded-lg border border-border text-sm focus:outline-none focus:border-accent-blue"
              />
            </div>
            <div>
              <label className="text-xs font-medium text-text-secondary">Avg Cost *</label>
              <input
                type="number"
                step="0.01"
                value={form.avg_cost_basis}
                onChange={(e) => setForm({ ...form, avg_cost_basis: e.target.value })}
                placeholder="150.00"
                className="w-full mt-1 px-3 py-2 bg-background-secondary rounded-lg border border-border text-sm focus:outline-none focus:border-accent-blue"
              />
            </div>
          </div>
          <div>
            <label className="text-xs font-medium text-text-secondary">Buy Date</label>
            <input
              type="date"
              value={form.buy_date}
              onChange={(e) => setForm({ ...form, buy_date: e.target.value })}
              className="w-full mt-1 px-3 py-2 bg-background-secondary rounded-lg border border-border text-sm focus:outline-none focus:border-accent-blue"
            />
          </div>
          <div>
            <label className="text-xs font-medium text-text-secondary">Notes</label>
            <input
              type="text"
              value={form.notes}
              onChange={(e) => setForm({ ...form, notes: e.target.value })}
              placeholder="Optional notes..."
              className="w-full mt-1 px-3 py-2 bg-background-secondary rounded-lg border border-border text-sm focus:outline-none focus:border-accent-blue"
            />
          </div>
        </div>

        <div className="flex gap-2 mt-4">
          <button onClick={onClose} className="btn btn-secondary flex-1">
            Cancel
          </button>
          <button
            onClick={() => addMutation.mutate()}
            disabled={!isValid || addMutation.isPending}
            className="btn btn-primary flex-1"
          >
            {addMutation.isPending ? 'Adding...' : 'Add Holding'}
          </button>
        </div>

        {addMutation.isError && (
          <p className="text-xs text-accent-red mt-2">Failed to add holding. Check the ticker and try again.</p>
        )}
      </div>
    </div>
  )
}

// ============== CSV Import Modal ==============

function CsvImportModal({ onClose }: { onClose: () => void }) {
  const queryClient = useQueryClient()
  const fileRef = useRef<HTMLInputElement>(null)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)

  const importMutation = useMutation({
    mutationFn: () => portfolioApi.importCsv(selectedFile!),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['portfolio-holdings'] })
      onClose()
    },
  })

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
      <div className="card w-full max-w-md mx-4">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold">Import CSV</h3>
          <button onClick={onClose} className="p-1 rounded hover:bg-surface-hover">
            <X className="w-5 h-5" />
          </button>
        </div>

        <p className="text-xs text-text-secondary mb-3">
          Upload a CSV file with columns: <strong>ticker</strong>, <strong>shares</strong>, <strong>avg_cost</strong> (or cost/price).
          Optional: buy_date, notes.
        </p>

        <div
          onClick={() => fileRef.current?.click()}
          className="border-2 border-dashed border-border rounded-lg p-8 text-center cursor-pointer hover:border-accent-blue transition-colors"
        >
          <Upload className="w-8 h-8 text-text-tertiary mx-auto mb-2" />
          {selectedFile ? (
            <p className="text-sm text-accent-blue">{selectedFile.name}</p>
          ) : (
            <p className="text-sm text-text-secondary">Click to select CSV file</p>
          )}
          <input
            ref={fileRef}
            type="file"
            accept=".csv"
            className="hidden"
            onChange={(e) => setSelectedFile(e.target.files?.[0] ?? null)}
          />
        </div>

        <div className="flex gap-2 mt-4">
          <button onClick={onClose} className="btn btn-secondary flex-1">
            Cancel
          </button>
          <button
            onClick={() => importMutation.mutate()}
            disabled={!selectedFile || importMutation.isPending}
            className="btn btn-primary flex-1"
          >
            {importMutation.isPending ? 'Importing...' : 'Import'}
          </button>
        </div>

        {importMutation.isSuccess && (
          <p className="text-xs text-accent-green mt-2">Import successful!</p>
        )}
        {importMutation.isError && (
          <p className="text-xs text-accent-red mt-2">Import failed. Check your CSV format and try again.</p>
        )}
      </div>
    </div>
  )
}

// ============== Summary Card ==============

function SummaryCard({ holdings }: { holdings: PortfolioHolding[] }) {
  const totalValue = holdings.reduce((sum, h) => sum + (h.market_value ?? 0), 0)
  const totalCost = holdings.reduce((sum, h) => sum + h.shares * h.avg_cost_basis, 0)
  const totalGainLoss = totalValue - totalCost
  const totalGainLossPct = totalCost > 0 ? (totalGainLoss / totalCost) * 100 : 0
  const isPositive = totalGainLoss >= 0

  return (
    <div className="card">
      <h2 className="text-lg font-semibold flex items-center gap-2 mb-4">
        <Briefcase className="w-5 h-5 text-accent-blue" />
        Portfolio Summary
      </h2>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div>
          <div className="text-xs text-text-tertiary">Total Value</div>
          <div className="text-xl font-bold text-text-primary">
            ${totalValue.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </div>
        </div>
        <div>
          <div className="text-xs text-text-tertiary">Total Cost</div>
          <div className="text-xl font-bold text-text-secondary">
            ${totalCost.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </div>
        </div>
        <div>
          <div className="text-xs text-text-tertiary">Total P&L</div>
          <div className={clsx('text-xl font-bold', isPositive ? 'text-accent-green' : 'text-accent-red')}>
            {isPositive ? '+' : ''}${totalGainLoss.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </div>
        </div>
        <div>
          <div className="text-xs text-text-tertiary">Total Return</div>
          <div className={clsx('text-xl font-bold flex items-center gap-1', isPositive ? 'text-accent-green' : 'text-accent-red')}>
            {isPositive ? <TrendingUp className="w-4 h-4" /> : <TrendingDown className="w-4 h-4" />}
            {isPositive ? '+' : ''}{totalGainLossPct.toFixed(2)}%
          </div>
        </div>
      </div>
    </div>
  )
}

// ============== Holdings Table ==============

function HoldingsTable({ holdings }: { holdings: PortfolioHolding[] }) {
  const queryClient = useQueryClient()

  const deleteMutation = useMutation({
    mutationFn: (id: number) => portfolioApi.deleteHolding(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['portfolio-holdings'] })
    },
  })

  return (
    <div className="card overflow-hidden">
      <h2 className="text-lg font-semibold mb-4">Holdings</h2>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-border text-text-tertiary text-xs">
              <th className="text-left py-2 px-3">Ticker</th>
              <th className="text-right py-2 px-3">Shares</th>
              <th className="text-right py-2 px-3">Avg Cost</th>
              <th className="text-right py-2 px-3">Price</th>
              <th className="text-right py-2 px-3">Value</th>
              <th className="text-right py-2 px-3">P&L</th>
              <th className="text-right py-2 px-3">P&L %</th>
              <th className="text-right py-2 px-3">Today</th>
              <th className="text-right py-2 px-3"></th>
            </tr>
          </thead>
          <tbody>
            {holdings.map((h) => {
              const isPositive = (h.gain_loss ?? 0) >= 0
              const todayPositive = (h.todays_change_pct ?? 0) >= 0
              return (
                <tr key={h.id} className="border-b border-border/50 hover:bg-surface-hover transition-colors">
                  <td className="py-3 px-3">
                    <span className="font-bold text-accent-blue">{h.ticker}</span>
                  </td>
                  <td className="text-right py-3 px-3">{h.shares}</td>
                  <td className="text-right py-3 px-3">${h.avg_cost_basis.toFixed(2)}</td>
                  <td className="text-right py-3 px-3 font-medium">
                    {h.current_price ? `$${h.current_price.toFixed(2)}` : '--'}
                  </td>
                  <td className="text-right py-3 px-3 font-medium">
                    {h.market_value ? `$${h.market_value.toLocaleString(undefined, { maximumFractionDigits: 2 })}` : '--'}
                  </td>
                  <td className={clsx('text-right py-3 px-3 font-medium', isPositive ? 'text-accent-green' : 'text-accent-red')}>
                    {h.gain_loss !== null ? `${isPositive ? '+' : ''}$${h.gain_loss.toFixed(2)}` : '--'}
                  </td>
                  <td className={clsx('text-right py-3 px-3 font-medium', isPositive ? 'text-accent-green' : 'text-accent-red')}>
                    {h.gain_loss_pct !== null ? `${isPositive ? '+' : ''}${h.gain_loss_pct.toFixed(1)}%` : '--'}
                  </td>
                  <td className={clsx('text-right py-3 px-3 text-xs', todayPositive ? 'text-accent-green' : 'text-accent-red')}>
                    {h.todays_change_pct !== null ? `${todayPositive ? '+' : ''}${h.todays_change_pct.toFixed(1)}%` : '--'}
                  </td>
                  <td className="text-right py-3 px-3">
                    <button
                      onClick={() => deleteMutation.mutate(h.id)}
                      className="text-text-tertiary hover:text-accent-red transition-colors p-1"
                      title="Remove"
                    >
                      <X className="w-3.5 h-3.5" />
                    </button>
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}

// ============== Health Dashboard ==============

function HealthDashboard({ analysis }: { analysis: PortfolioAnalysis }) {
  const holdingsData = analysis.holdings_data

  if (!holdingsData || Object.keys(holdingsData).length === 0) {
    return null
  }

  const healthColor = (fScore: number | null) => {
    if (fScore === null) return 'text-text-tertiary'
    if (fScore >= 7) return 'text-accent-green'
    if (fScore >= 5) return 'text-accent-yellow'
    return 'text-accent-red'
  }

  const riskColor = (zScore: number | null) => {
    if (zScore === null) return 'text-text-tertiary'
    if (zScore > 2.99) return 'text-accent-green'
    if (zScore > 1.81) return 'text-accent-yellow'
    return 'text-accent-red'
  }

  return (
    <div className="card">
      <h2 className="text-lg font-semibold flex items-center gap-2 mb-4">
        <Activity className="w-5 h-5 text-accent-purple" />
        Health Dashboard
      </h2>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
        {Object.entries(holdingsData).map(([ticker, data]) => (
          <div key={ticker} className="bg-background-secondary rounded-lg p-3">
            <div className="flex items-center justify-between mb-2">
              <span className="font-bold text-accent-blue">{ticker}</span>
              <span className={clsx(
                'text-xs px-2 py-0.5 rounded-full font-medium',
                data.trend === 'up' ? 'bg-accent-green/20 text-accent-green' : data.trend === 'down' ? 'bg-accent-red/20 text-accent-red' : 'bg-border text-text-secondary'
              )}>
                {data.trend === 'up' ? 'Uptrend' : data.trend === 'down' ? 'Downtrend' : 'N/A'}
              </span>
            </div>

            <div className="grid grid-cols-3 gap-2 text-center">
              <div>
                <div className={clsx('text-sm font-bold', healthColor(data.f_score))}>
                  {data.f_score !== null ? `${data.f_score}/9` : '--'}
                </div>
                <div className="text-[10px] text-text-tertiary">Health</div>
              </div>
              <div>
                <div className={clsx('text-sm font-bold', riskColor(data.z_score))}>
                  {data.z_score !== null ? data.z_score.toFixed(1) : '--'}
                </div>
                <div className="text-[10px] text-text-tertiary">Safety</div>
              </div>
              <div>
                <div className={clsx(
                  'text-sm font-bold',
                  data.rsi !== null ? (data.rsi > 70 ? 'text-accent-red' : data.rsi < 30 ? 'text-accent-green' : 'text-text-primary') : 'text-text-tertiary'
                )}>
                  {data.rsi !== null ? data.rsi.toFixed(0) : '--'}
                </div>
                <div className="text-[10px] text-text-tertiary">RSI</div>
              </div>
            </div>

            <div className="mt-2 flex items-center justify-between text-xs">
              <span className={clsx(data.gain_loss_pct >= 0 ? 'text-accent-green' : 'text-accent-red')}>
                {data.gain_loss_pct >= 0 ? '+' : ''}{data.gain_loss_pct.toFixed(1)}%
              </span>
              {data.m_score_flag && (
                <span className="text-accent-red flex items-center gap-1">
                  <AlertTriangle className="w-3 h-3" /> Flag
                </span>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

// ============== Alerts Panel ==============

function AlertsPanel({ alerts }: { alerts: PortfolioAlert[] }) {
  const queryClient = useQueryClient()

  const markReadMutation = useMutation({
    mutationFn: (id: number) => portfolioApi.markAlertRead(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['portfolio-alerts'] })
    },
  })

  if (!alerts.length) return null

  const severityClass = (severity: string) => {
    if (severity === 'high') return 'border-l-accent-red bg-accent-red/5'
    if (severity === 'medium') return 'border-l-accent-yellow bg-accent-yellow/5'
    return 'border-l-accent-blue bg-accent-blue/5'
  }

  const typeIcon = (type: string) => {
    if (type === 'exit_signal') return <AlertTriangle className="w-4 h-4 text-accent-red" />
    if (type === 'health_warning') return <Shield className="w-4 h-4 text-accent-yellow" />
    return <Bell className="w-4 h-4 text-accent-blue" />
  }

  const typeLabel = (type: string) => {
    if (type === 'exit_signal') return 'Exit Signal'
    if (type === 'health_warning') return 'Health Warning'
    return 'Earnings Alert'
  }

  return (
    <div className="card">
      <h2 className="text-lg font-semibold flex items-center gap-2 mb-4">
        <Bell className="w-5 h-5 text-accent-yellow" />
        Alerts
        <span className="text-xs bg-accent-red/20 text-accent-red px-2 py-0.5 rounded-full">
          {alerts.length}
        </span>
      </h2>

      <div className="space-y-2">
        {alerts.map((alert) => (
          <div
            key={alert.id}
            className={clsx(
              'border-l-4 rounded-lg p-3 flex items-start gap-3',
              severityClass(alert.severity)
            )}
          >
            <div className="flex-shrink-0 mt-0.5">{typeIcon(alert.alert_type)}</div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-1">
                <span className="text-xs font-bold text-text-primary">{alert.ticker}</span>
                <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-surface text-text-secondary">
                  {typeLabel(alert.alert_type)}
                </span>
              </div>
              <p className="text-xs text-text-secondary leading-relaxed">{alert.message}</p>
            </div>
            <button
              onClick={() => markReadMutation.mutate(alert.id)}
              className="flex-shrink-0 p-1 rounded hover:bg-surface-hover text-text-tertiary hover:text-accent-green"
              title="Dismiss"
            >
              <Check className="w-4 h-4" />
            </button>
          </div>
        ))}
      </div>
    </div>
  )
}

// ============== Main Portfolio Page ==============

export default function Portfolio() {
  const queryClient = useQueryClient()
  const [showAddModal, setShowAddModal] = useState(false)
  const [showCsvModal, setShowCsvModal] = useState(false)
  const [showHealth, setShowHealth] = useState(false)

  const { data: holdings, isLoading } = useQuery({
    queryKey: ['portfolio-holdings'],
    queryFn: () => portfolioApi.getHoldings(),
    staleTime: 60 * 1000,
  })

  const { data: alerts } = useQuery({
    queryKey: ['portfolio-alerts'],
    queryFn: () => portfolioApi.getAlerts(),
    staleTime: 60 * 1000,
  })

  const analysisMutation = useMutation({
    mutationFn: () => portfolioApi.runAnalysis(),
    onSuccess: () => {
      setShowHealth(true)
      queryClient.invalidateQueries({ queryKey: ['portfolio-alerts'] })
    },
  })

  // Empty state
  if (!isLoading && (!holdings || holdings.length === 0)) {
    return (
      <div className="space-y-6 animate-fade-in">
        <div className="text-center py-16">
          <Briefcase className="w-16 h-16 text-text-tertiary mx-auto mb-4" />
          <h1 className="text-2xl font-bold mb-2">Portfolio Tracker</h1>
          <p className="text-text-secondary mb-6 max-w-md mx-auto">
            Add your existing stock holdings to get daily health checks, exit signals, and earnings alerts.
          </p>
          <div className="flex gap-3 justify-center">
            <button
              onClick={() => setShowAddModal(true)}
              className="btn btn-primary inline-flex items-center gap-2"
            >
              <Plus className="w-4 h-4" />
              Add Holding
            </button>
            <button
              onClick={() => setShowCsvModal(true)}
              className="btn btn-secondary inline-flex items-center gap-2"
            >
              <Upload className="w-4 h-4" />
              Import CSV
            </button>
          </div>
        </div>

        {showAddModal && <AddHoldingModal onClose={() => setShowAddModal(false)} />}
        {showCsvModal && <CsvImportModal onClose={() => setShowCsvModal(false)} />}
      </div>
    )
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-20">
        <RefreshCw className="w-6 h-6 text-accent-blue animate-spin" />
        <span className="ml-3 text-text-secondary">Loading portfolio...</span>
      </div>
    )
  }

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-3">
            <Briefcase className="w-7 h-7 text-accent-blue" />
            Portfolio Tracker
          </h1>
          <p className="text-sm text-text-secondary mt-1">
            {holdings!.length} holdings tracked
          </p>
        </div>

        <div className="flex gap-2">
          <button
            onClick={() => analysisMutation.mutate()}
            disabled={analysisMutation.isPending}
            className="btn btn-secondary inline-flex items-center gap-2 text-sm"
          >
            <Activity className={clsx('w-4 h-4', analysisMutation.isPending && 'animate-spin')} />
            {analysisMutation.isPending ? 'Analyzing...' : 'Health Check'}
          </button>
          <button
            onClick={() => setShowAddModal(true)}
            className="btn btn-primary inline-flex items-center gap-2 text-sm"
          >
            <Plus className="w-4 h-4" />
            Add
          </button>
          <button
            onClick={() => setShowCsvModal(true)}
            className="btn btn-secondary inline-flex items-center gap-2 text-sm"
          >
            <Upload className="w-4 h-4" />
            CSV
          </button>
        </div>
      </div>

      {/* Alerts */}
      {alerts && alerts.length > 0 && <AlertsPanel alerts={alerts} />}

      {/* Summary */}
      <SummaryCard holdings={holdings!} />

      {/* Holdings Table */}
      <HoldingsTable holdings={holdings!} />

      {/* Health Dashboard (shown after analysis) */}
      {analysisMutation.isSuccess && analysisMutation.data && showHealth && (
        <HealthDashboard analysis={analysisMutation.data} />
      )}

      {/* Modals */}
      {showAddModal && <AddHoldingModal onClose={() => setShowAddModal(false)} />}
      {showCsvModal && <CsvImportModal onClose={() => setShowCsvModal(false)} />}
    </div>
  )
}
