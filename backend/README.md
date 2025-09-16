# TicketFlow AI - Backend

An intelligent ticket management system powered by AI that automatically processes, categorizes, and responds to support tickets.

## 🚀 Quick Start

> **Note**: This project is API-first, so the `backend` can run independently.

### Prerequisites

- Python 3.12 or higher
- TiDB database
- API keys for external services (OpenAI/OpenRouter, Jina AI, Resend,Slack bot token etc.)

### 1. Clone and Setup

```bash
# Clone the repository (if not already done)
git clone <repository-url>
cd ticketflow-ai/backend

# Install dependencies
pip install -r requirements.txt
```

### 2. Environment Configuration

Rename the `.env.example` file to `.env` in the backend directory and fill out the required variables :

```env
# Database Configuration
TIDB_HOST=
TIDB_PORT=4000
TIDB_USER=root
TIDB_PASSWORD=
TIDB_DATABASE=ticketflow

# AI Services
OPENROUTER_API_KEY=your-openrouter-api-key  # For LLM responses
OPENAI_API_KEY=your-openai-api-key          # Alternative to OpenRouter
JINA_API_KEY=your-jina-api-key              # For embeddings

# External Integrations
SLACK_BOT_TOKEN=xoxb-your-slack-bot-token   # Optional, for Slack integration
RESEND_API_KEY=your-resend-api-key          # For email notifications

# Security
ENCRYPTION_KEY=your-32-character-encryption-key  # For sensitive settings

# Application Settings
DEBUG=False
LOG_LEVEL=INFO
DEMO_MODE=True
```

### 3. Run Setup Script

The setup script will initialize the database, create tables, configure settings, and add sample data:

```bash
python setup.py
```

This script will:

- ✅ Validate your environment configuration
- ✅ Initialize database and create all required tables
- ✅ Set up default application settings
- ✅ Create sample tickets and knowledge base articles
- ✅ Verify the setup completed successfully

### 4. Start the API Server

Once setup is complete, start the development server:

```bash
python run_api.py
```

The API will be available at:

- **Main API**: http://localhost:8000
- **Interactive Docs**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc

## 📚 API Documentation

### Core Endpoints

- **Tickets**: `/api/tickets/` - Create, read, update, delete tickets
- **Knowledge Base**: `/api/kb/` - Manage knowledge base articles
- **Settings**: `/api/settings/` - Configure application settings
- **Agent**: `/api/agent/` - AI agent interactions and processing

### Authentication

Currently, the API runs in development mode without authentication. For production deployment, implement proper authentication mechanisms.

## 🗄️ Database Schema

The system uses the following main tables:

- `tickets` - Support tickets with AI processing status
- `kb_articles` - Knowledge base articles for AI responses
- `settings` - Application configuration settings
- `performance_metrics` - Performance Metrics
- `api_keys` - API Keys
- `agent_workflows` - Agent Workflows
- `learning_metrics` - AI performance tracking

## ⚙️ Configuration

### Settings Management

The application uses a flexible settings system that supports:

- **Categories**: System, Slack, Email, Agent settings
- **Types**: String, Integer, Float, Boolean, JSON
- **Encryption**: Sensitive settings are automatically encrypted
- **Validation**: Built-in validation rules for setting values

Access settings via:

- API: `GET /api/settings/`
- Direct database: Use the `SettingsManager` class

### Key Settings

| Setting                       | Category | Description                   | Default |
| ----------------------------- | -------- | ----------------------------- | ------- |
| `slack_notifications_enabled` | slack    | Enable Slack notifications    | `true`  |
| `email_notifications_enabled` | email    | Enable email notifications    | `true`  |
| `system_timezone`             | system   | System timezone               | `UTC`   |
| `agent_auto_response_enabled` | agent    | Enable automatic AI responses | `true`  |

## 🤖 AI Agent Features

### Ticket Processing

- Automatic categorization and priority assignment
- Intelligent response generation using knowledge base
- Multi-step reasoning for complex issues
- Learning from interaction feedback

### Knowledge Base Integration

- Semantic search across articles
- Automatic article suggestions
- Context-aware response generation
- Continuous learning and improvement

## 🔧 Development

### Project Structure

```
backend/
├── src/ticketflow/           # Main application code
│   ├── api/                  # FastAPI routes and models
│   ├── agent/                # AI agent core logic
│   ├── database/             # Database operations and models
│   └── utils/                # Utility functions
├── setup.py                  # Project setup script
├── run_api.py               # API server launcher
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

### Running Tests

```bash
# Install test dependencies (included in requirements.txt)
pip install pytest pytest-asyncio

# Run tests
pytest
```

### Code Formatting

```bash
# Format code
black .

# Check code style
flake8 .
```

## 🚀 Deployment

### Production Setup

1. **Environment**: Set `DEBUG=False` and configure production database
2. **Security**: Use strong encryption keys and secure API keys
3. **Database**: Use a production-grade TiDB instance with SSL enabled
4. **Monitoring**: Configure logging and monitoring systems
5. **SSL**: Enable HTTPS for production deployments

### Docker Deployment (Optional)

Create a `Dockerfile` for containerized deployment:

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["python", "run_api.py"]
```

## 🔍 Troubleshooting

### Common Issues

**Database Connection Failed**

- Verify database credentials in `.env`
- Check network connectivity to TiDB instance
- Ensure database exists and user has proper permissions

**API Keys Not Working**

- Verify API keys are correctly set in `.env`
- Check API key permissions and quotas
- Ensure no extra spaces or characters in keys

**Setup Script Fails**

- Check all required environment variables are set
- Verify database is accessible and empty/clean
- Review logs for specific error messages

**Import Errors**

- Ensure all dependencies are installed: `pip install -r requirements.txt`
- Check Python version compatibility (3.12+)
- Verify virtual environment is activated

### Logs and Debugging

- Application logs are output to console by default
- Set `LOG_LEVEL=DEBUG` for detailed logging
- Check database connection status in logs
- Review API request/response logs for debugging

## 📞 Support

For issues and questions:

1. Check this README and troubleshooting section
2. Review API documentation at `/docs`
3. Check application logs for error details
4. Verify environment configuration

## 🔄 Updates and Maintenance

### Database Migrations

- Future schema changes will include migration scripts
- Always backup database before running migrations
- Test migrations in development environment first

---

**Happy ticket processing! 🎫✨**
