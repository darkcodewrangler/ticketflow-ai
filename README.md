# TicketFlow AI - Smart Ticket Assistant

An intelligent ticket management system powered by AI that automatically processes, categorizes, and responds to support tickets.

## 🚀 Quick Start

### Option 1: Docker (Recommended)

If you have Docker installed, you can start both backend and frontend services with a single command:

- Copy `.env.example` to `.env`
- Fill in required API keys and database configuration

```bash
docker-compose up --build
```

This will:

- Build and start the backend API server
- Build and start the frontend development server
- Set up all necessary dependencies (database and sample data)

### Option 2: Manual Setup

If you prefer to run the services individually or don't have Docker:

#### Backend Setup

1. **Navigate to backend directory**

   ```bash
   cd backend
   ```

2. **Install Python dependencies**

   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment**

   - Copy `.env.example` to `.env`
   - Fill in required API keys and database configuration

4. **Run setup script**

   ```bash
   python setup.py
   ```

5. **Start the API server**

   ```bash
   python run_api.py
   ```

   Backend will be available at: http://localhost:8000

#### Frontend Setup

1. **Navigate to frontend directory**

   ```bash
   cd frontend
   ```

2. **Install Node.js dependencies**

   ```bash
   pnpm install
   ```

   (or use `npm install` if you don't have pnpm)

3. **Configure environment**

   - Copy `.env.example` to `.env.local`
   - Set `VITE_API_BASE_URL=http://localhost:8000`

4. **Start the development server**

   ```bash
   pnpm dev
   ```

   Frontend will be available at: http://localhost:5173

## 📋 Prerequisites

### For Docker Setup

- Docker and Docker Compose

### For Manual Setup

- **Backend**: Python 3.12+, TiDB database, API keys (OpenAI/OpenRouter, Jina AI, etc.)
- **Frontend**: Node.js 22+, pnpm (recommended) or npm

## 📚 Documentation

- **Backend Documentation**: See `backend/README.md` for detailed API documentation and configuration
- **Frontend Documentation**: See `frontend/README.md` for UI components and development guidelines

## 🏗️ Architecture

- **Backend**: FastAPI-based REST API with AI agent processing
- **Frontend**: React + TypeScript with modern UI components
- **Database**: TiDB for scalable data storage
- **AI Services**: Integration with OpenAI/OpenRouter and Jina AI

## 🤝 Contributing

Contributions are welcome! Please read the individual README files in the `backend/` and `frontend/` directories for specific development guidelines.
