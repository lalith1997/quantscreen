# QuantScreen

A quantitative stock screening and research platform for long-term investors.

## Features

- **6 Core Screeners**: Magic Formula, Acquirer's Multiple, Piotroski F-Score, Altman Z-Score, Beneish M-Score, Sloan Accrual Ratio
- **70+ Fundamental Metrics**: P/E, P/B, ROE, EV/EBITDA, and more
- **32+ Technical Indicators**: RSI, MACD, Bollinger Bands, ADX, Ichimoku Cloud
- **Timing Signals**: Entry/exit guidance for long-term positions
- **Backtesting**: Validate your screening strategies historically
- **Real-time Data**: Live prices and news (Phase 3)

## Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | React 18 + TypeScript + Vite + Tailwind CSS |
| Backend | Python 3.12 + FastAPI |
| Database | PostgreSQL |
| Hosting | Vercel (frontend) + Render (backend + DB) |

## Project Structure

```
quantscreen/
├── frontend/                 # React application
│   ├── src/
│   │   ├── components/       # Reusable UI components
│   │   ├── pages/            # Page components
│   │   ├── hooks/            # Custom React hooks
│   │   ├── services/         # API client functions
│   │   ├── stores/           # Zustand state management
│   │   └── utils/            # Helper functions
│   └── package.json
│
├── backend/                  # FastAPI application
│   ├── app/
│   │   ├── api/routes/       # API endpoints
│   │   ├── core/             # Config, security, database
│   │   ├── models/           # SQLAlchemy models
│   │   ├── schemas/          # Pydantic schemas
│   │   └── services/         # Business logic
│   │       ├── data_providers/   # External API integrations
│   │       ├── formula_engine/   # Financial calculations
│   │       └── screener/         # Screening logic
│   └── requirements.txt
│
├── docker-compose.yml        # Local development setup
├── render.yaml               # Render deployment config
└── docs/                     # Documentation
```

## Getting Started

### Prerequisites

- Python 3.12+
- Node.js 20+
- PostgreSQL 16+ (or use Docker)

### Local Development

1. **Clone the repository**
   ```bash
   git clone https://github.com/lalith1997/quantscreen.git
   cd quantscreen
   ```

2. **Set up environment variables**
   ```bash
   # Backend
   cp backend/.env.example backend/.env
   # Edit backend/.env with your API keys
   
   # Frontend
   cp frontend/.env.example frontend/.env
   ```

3. **Start with Docker (recommended)**
   ```bash
   docker-compose up -d
   ```
   
   Or manually:
   ```bash
   # Terminal 1: Backend
   cd backend
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   uvicorn app.main:app --reload
   
   # Terminal 2: Frontend
   cd frontend
   npm install
   npm run dev
   ```

4. **Access the application**
   - Frontend: http://localhost:5173
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

## Deployment

### Render (Backend + Database)

1. Connect your GitHub repo to Render
2. Render will auto-detect `render.yaml` and create services
3. Add environment variables in Render dashboard

### Vercel (Frontend)

1. Import your GitHub repo to Vercel
2. Set root directory to `frontend`
3. Add `VITE_API_URL` environment variable pointing to your Render backend

## Environment Variables

### Backend (.env)

```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/quantscreen

# API Keys
FMP_API_KEY=your_financial_modeling_prep_key
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_key

# Security
SECRET_KEY=your-secret-key-min-32-chars
```

### Frontend (.env)

```env
VITE_API_URL=http://localhost:8000
```

## API Documentation

Once running, visit http://localhost:8000/docs for interactive API documentation.

## Development Roadmap

- [x] Phase 1: Core screeners + basic UI
- [ ] Phase 2: Backtesting + timing signals
- [ ] Phase 3: International + crypto + real-time
- [ ] Phase 4: Team features + polish

## License

MIT
