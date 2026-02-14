import { Outlet, Link, useLocation } from 'react-router-dom'
import { Newspaper, LayoutDashboard, Filter, TrendingUp, Settings } from 'lucide-react'
import { clsx } from 'clsx'

const navigation = [
  { name: 'Daily Brief', href: '/', icon: Newspaper },
  { name: 'Screener', href: '/screener', icon: Filter },
  { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
]

export default function Layout() {
  const location = useLocation()

  return (
    <div className="min-h-screen bg-background-primary">
      {/* Header */}
      <header className="sticky top-0 z-50 bg-background-primary/80 backdrop-blur-xl border-b border-border">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            {/* Logo */}
            <Link to="/" className="flex items-center gap-2">
              <TrendingUp className="w-8 h-8 text-accent-blue" />
              <span className="text-xl font-bold">QuantScreen</span>
            </Link>

            {/* Navigation */}
            <nav className="flex items-center gap-1">
              {navigation.map((item) => {
                const isActive =
                  item.href === '/'
                    ? location.pathname === '/' || location.pathname === '/daily'
                    : location.pathname === item.href
                return (
                  <Link
                    key={item.name}
                    to={item.href}
                    className={clsx(
                      'flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors',
                      isActive
                        ? 'bg-surface text-text-primary'
                        : 'text-text-secondary hover:text-text-primary hover:bg-surface/50'
                    )}
                  >
                    <item.icon className="w-4 h-4" />
                    {item.name}
                  </Link>
                )
              })}
            </nav>

            {/* Settings */}
            <button className="p-2 rounded-lg text-text-secondary hover:text-text-primary hover:bg-surface transition-colors">
              <Settings className="w-5 h-5" />
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Outlet />
      </main>
    </div>
  )
}
