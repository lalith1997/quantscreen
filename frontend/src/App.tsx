import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import Screener from './pages/Screener'
import StockDetail from './pages/StockDetail'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Dashboard />} />
          <Route path="screener" element={<Screener />} />
          <Route path="stock/:ticker" element={<StockDetail />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}

export default App
