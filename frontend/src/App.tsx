import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import DailyBrief from './pages/DailyBrief'
import Dashboard from './pages/Dashboard'
import Screener from './pages/Screener'
import StockDetail from './pages/StockDetail'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<DailyBrief />} />
          <Route path="daily" element={<DailyBrief />} />
          <Route path="dashboard" element={<Dashboard />} />
          <Route path="screener" element={<Screener />} />
          <Route path="stock/:ticker" element={<StockDetail />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}

export default App
