import { Link } from 'react-router-dom'
import { ArrowRight, TrendingUp, Shield, Target, AlertTriangle } from 'lucide-react'

const presetScreens = [
  {
    id: 'magic_formula',
    name: 'Magic Formula',
    description: 'Greenblatt\'s classic value + quality combo',
    icon: Target,
    color: 'text-accent-blue',
    bgColor: 'bg-accent-blue/10',
  },
  {
    id: 'deep_value',
    name: 'Deep Value',
    description: 'Acquirer\'s Multiple - lowest EV/EBIT',
    icon: TrendingUp,
    color: 'text-accent-green',
    bgColor: 'bg-accent-green/10',
  },
  {
    id: 'quality_value',
    name: 'Quality at Reasonable Price',
    description: 'High F-Score + reasonable valuation',
    icon: Shield,
    color: 'text-accent-purple',
    bgColor: 'bg-accent-purple/10',
  },
  {
    id: 'safe_stocks',
    name: 'Financially Safe',
    description: 'High Z-Score + strong fundamentals',
    icon: Shield,
    color: 'text-accent-yellow',
    bgColor: 'bg-accent-yellow/10',
  },
]

export default function Dashboard() {
  return (
    <div className="space-y-8 animate-fade-in">
      {/* Welcome Section */}
      <div>
        <h1 className="text-3xl font-bold">Welcome to QuantScreen</h1>
        <p className="text-text-secondary mt-2">
          Find undervalued, high-quality stocks using proven quantitative strategies.
        </p>
      </div>
      
      {/* Quick Actions */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {presetScreens.map((screen) => (
          <Link
            key={screen.id}
            to={`/screener?preset=${screen.id}`}
            className="card hover:border-border-hover transition-all group"
          >
            <div className={`w-10 h-10 rounded-lg ${screen.bgColor} flex items-center justify-center mb-3`}>
              <screen.icon className={`w-5 h-5 ${screen.color}`} />
            </div>
            <h3 className="font-semibold text-text-primary group-hover:text-accent-blue transition-colors">
              {screen.name}
            </h3>
            <p className="text-sm text-text-secondary mt-1">
              {screen.description}
            </p>
            <div className="flex items-center gap-1 text-sm text-accent-blue mt-3 opacity-0 group-hover:opacity-100 transition-opacity">
              Run screen <ArrowRight className="w-4 h-4" />
            </div>
          </Link>
        ))}
      </div>
      
      {/* Core Screeners Info */}
      <div className="card">
        <h2 className="text-xl font-semibold mb-4">6 Core Screeners</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <ScreenerInfo
            name="Magic Formula"
            description="Earnings Yield + Return on Capital rankings"
            author="Joel Greenblatt"
          />
          <ScreenerInfo
            name="Acquirer's Multiple"
            description="Enterprise Value / Operating Earnings"
            author="Tobias Carlisle"
          />
          <ScreenerInfo
            name="Piotroski F-Score"
            description="9-point financial strength score"
            author="Joseph Piotroski"
          />
          <ScreenerInfo
            name="Altman Z-Score"
            description="Bankruptcy risk predictor"
            author="Edward Altman"
          />
          <ScreenerInfo
            name="Beneish M-Score"
            description="Earnings manipulation detector"
            author="Messod Beneish"
            isWarning
          />
          <ScreenerInfo
            name="Sloan Accrual Ratio"
            description="Earnings quality measure"
            author="Richard Sloan"
          />
        </div>
      </div>
      
      {/* Getting Started */}
      <div className="card bg-gradient-to-br from-accent-blue/10 to-accent-purple/10 border-accent-blue/20">
        <h2 className="text-xl font-semibold mb-2">Getting Started</h2>
        <p className="text-text-secondary mb-4">
          New to QuantScreen? Here's how to find your next investment:
        </p>
        <ol className="list-decimal list-inside space-y-2 text-text-secondary">
          <li>Run a preset screen like <strong className="text-text-primary">Magic Formula</strong> to find candidates</li>
          <li>Review the F-Score and M-Score to verify quality and avoid red flags</li>
          <li>Check the timing signals to find the best entry point</li>
          <li>Add to your watchlist and set alerts</li>
        </ol>
        <Link to="/screener" className="btn btn-primary mt-4 inline-flex items-center gap-2">
          Go to Screener <ArrowRight className="w-4 h-4" />
        </Link>
      </div>
    </div>
  )
}

function ScreenerInfo({ 
  name, 
  description, 
  author,
  isWarning = false,
}: { 
  name: string
  description: string
  author: string
  isWarning?: boolean
}) {
  return (
    <div className="p-4 rounded-lg bg-background-secondary">
      <div className="flex items-start justify-between">
        <h3 className="font-medium text-text-primary">{name}</h3>
        {isWarning && (
          <AlertTriangle className="w-4 h-4 text-accent-yellow" />
        )}
      </div>
      <p className="text-sm text-text-secondary mt-1">{description}</p>
      <p className="text-xs text-text-tertiary mt-2">by {author}</p>
    </div>
  )
}
