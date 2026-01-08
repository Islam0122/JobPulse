# 🚀 JobPulse - Telegram Job Finder Bot

A powerful Telegram bot that helps professionals find job opportunities through intelligent matching and personalized recommendations.

**Language:** Russian | English

---

## 📋 Table of Contents

- [Features](#features)
- [Quick Start](#quick-start)
- [Project Structure](#project-structure)
- [Tech Stack](#tech-stack)
- [Installation](#installation)
- [Configuration](#configuration)
- [API Documentation](#api-documentation)
- [Bot Commands](#bot-commands)
- [Development](#development)
- [Deployment](#deployment)
- [Troubleshooting](#troubleshooting)

---

## ✨ Features

### For Users
- 🔐 **Smart Matching** - AI-powered vacancy matching based on profile
- 👤 **Complete Profile** - Multi-step onboarding process
- 💼 **Browse Vacancies** - Personalized recommendations + all vacancies
- 👍 **React & Favorite** - Like/dislike + add to favorites
- 📊 **Analytics** - Track your job search statistics
- 💡 **Insights** - AI recommendations for profile improvement
- 🔔 **Notifications** - Instant/Daily/Weekly delivery modes
- 💬 **Feedback** - Send comments and suggestions

### For Admins
- 📨 **Broadcast Messages** - Send notifications to all users
- 📺 **Channel Management** - Manage subscription requirements
- 📊 **User Analytics** - Dashboard for monitoring
- 🔄 **Parsing Logs** - Track HH.ru scraping status
- 📈 **Metrics** - Real-time statistics

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- PostgreSQL 12+
- Redis 6+
- Docker & Docker Compose (optional)

### Local Setup (5 minutes)

```bash
# Clone repository
git clone https://github.com/yourusername/jobpulse.git
cd jobpulse

# Backend setup
cd backend
make setup

# Bot setup
cd ../bot
cp .env.example .env
# Edit .env with your BOT_TOKEN and BACKEND_URL

# Start services
cd ../backend
make dev  # Terminal 1: Django
# In other terminals:
make redis  # Terminal 2: Redis
make celery  # Terminal 3: Celery Worker
make beat  # Terminal 4: Celery Beat

# Bot (in separate terminal)
cd ../bot
python bot.py
```

### Docker Setup (recommended)

```bash
# Development
docker-compose up --build

# Production
docker-compose -f docker-compose.prod.yml up -d
```

---

## 📁 Project Structure

```
jobpulse/
├── backend/                    # Django REST API
│   ├── apps/
│   │   ├── users/             # User management
│   │   ├── vacancies/         # Job matching & parsing
│   │   ├── channels/          # Subscription management
│   │   ├── broadcastprompt/   # Admin broadcasts
│   │   └── review/            # User feedback
│   ├── config/
│   │   ├── settings/          # Django settings
│   │   ├── celery.py          # Celery config
│   │   └── urls.py            # API routes
│   ├── deployment/            # Docker & server configs
│   ├── Makefile              # Development commands
│   └── requirements.txt       # Python dependencies
│
├── bot/                        # Telegram Bot (aiogram)
│   ├── handlers/              # Command & callback handlers
│   ├── keyboards/             # Inline keyboards
│   ├── middlewares/           # Request processors
│   ├── services/              # API client
│   ├── states/                # FSM states
│   ├── bot.py                 # Bot entry point
│   ├── config.py              # Bot settings
│   └── requirements.txt        # Bot dependencies
│
└── docs/                       # Documentation
    ├── README.md
    ├── STRUCTURE_DATABASE.md
    ├── CELERY_NOTES.md
    ├── API.md
    ├── DEPLOYMENT.md
    └── TROUBLESHOOTING.md
```

---

## 🛠 Tech Stack

### Backend
| Component | Technology | Purpose |
|-----------|-----------|---------|
| Framework | Django 5.2 | Web framework |
| API | DRF 3.15 | REST API |
| Database | PostgreSQL 12+ | Main database |
| Cache | Redis 6+ | Caching & session store |
| Task Queue | Celery 5.4 | Async tasks |
| Task Scheduler | Celery Beat | Periodic tasks |
| Documentation | drf-spectacular | API docs |

### Bot
| Component | Technology | Purpose |
|-----------|-----------|---------|
| Framework | aiogram 3.24 | Telegram Bot API |
| FSM Storage | Redis | State management |
| HTTP Client | aiohttp | Async requests |

### DevOps
| Tool | Version | Purpose |
|------|---------|---------|
| Docker | Latest | Containerization |
| Docker Compose | Latest | Multi-container orchestration |
| Gunicorn | 23.0 | WSGI server |
| Nginx | Latest | Reverse proxy |

---

## 📦 Installation

### 1. Backend Setup

```bash
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env

# Configure database
export DJANGO_ENV=development
python manage.py migrate

# Create test data
python manage.py create_test_users

# Create superuser
python manage.py createsuperuser

# Collect static files
python manage.py collectstatic --noinput
```

### 2. Bot Setup

```bash
cd bot

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your tokens
```

### 3. Services

```bash
# Start Redis
redis-server

# Start Celery Worker (in separate terminal)
celery -A config worker -l info

# Start Celery Beat (in separate terminal)
celery -A config beat -l info

# Start Django (in separate terminal)
python manage.py runserver

# Start Bot (in separate terminal)
python bot/bot.py
```

---

## ⚙️ Configuration

### Backend (.env)

```bash
# Core
SECRET_KEY=your-secret-key-here
DEBUG=False
DJANGO_ENV=production
ALLOWED_HOST=yourdomain.com

# Database (PostgreSQL)
PGHOST=db.railway.app
PGPORT=5432
PGUSER=postgres
PGPASSWORD=your-password
PGDATABASE=jobpulse_db

# Redis
REDIS_URL=redis://localhost:6379/0

# Telegram Bot
BOT_TOKEN=your-telegram-bot-token

# Email
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
```

### Bot (.env)

```bash
# Telegram
BOT_TOKEN=your-telegram-bot-token

# Backend API
BACKEND_URL=http://localhost:8000/api
API_TIMEOUT=10

# Redis (for FSM)
REDIS_URL=redis://localhost:6379/1
```

---

## 📚 API Documentation

### Auto-Generated Docs
- **Swagger UI**: `http://localhost:8000/api/swagger/`
- **ReDoc**: `http://localhost:8000/api/redoc/`

### Main Endpoints

#### Users
```
GET    /api/users/                    # List all users
POST   /api/users/                    # Create user
GET    /api/users/{telegram_id}/      # Get user profile
PATCH  /api/users/{telegram_id}/      # Update user
POST   /api/users/{telegram_id}/complete_onboarding/
PATCH  /api/users/{telegram_id}/update_notification_mode/
GET    /api/users/insights/?telegram_id=123
GET    /api/users/stats/?telegram_id=123
```

#### Vacancies
```
GET    /api/vacancies/                # List vacancies
GET    /api/vacancies/{id}/           # Get vacancy detail
GET    /api/vacancies/recommended/    # Personalized recommendations
POST   /api/vacancies/{id}/react/     # Like/dislike
POST   /api/vacancies/{id}/add_to_favorites/
GET    /api/vacancies/favorites/      # User favorites
GET    /api/vacancies/history/        # View history
```

#### Reference Data
```
GET    /api/stacks/                   # Technologies
GET    /api/work-formats/             # Work formats
GET    /api/employment-types/         # Employment types
GET    /api/required-channels/        # Required subscriptions
```

---

## 🤖 Bot Commands

### User Commands
```
/start              Start bot / Complete onboarding
/help               Show help menu
/comment            Send feedback
/cancel             Cancel current operation
```

### Menu Navigation
- 💼 **Vacancies** - Browse job offers
- 👤 **Profile** - View/edit profile
- 📊 **Analytics** - Statistics & insights
- 🔔 **Settings** - Notification preferences
- ❓ **Help** - Documentation
- 💡 **Why free?** - Sponsors info

---

## 👨‍💻 Development

### Make Commands

```bash
# Setup & Installation
make setup                 # Full project setup
make install              # Install dependencies
make migrate              # Run migrations

# Running Services
make dev                  # Run all services locally
make run                  # Django server only
make redis                # Redis server
make celery               # Celery worker
make beat                 # Celery scheduler

# Docker
make docker-setup         # Build & run containers
make docker-build         # Build images only
make docker-up            # Start containers
make docker-down          # Stop containers
make docker-logs          # View logs

# Testing
make test                 # Run tests
make test-redis           # Test Redis connection
make check                # Django system check

# Database
make superuser            # Create admin user
make shell                # Django shell
make dbshell              # Database shell

# Maintenance
make clean                # Clean temp files
make clean-all            # Full cleanup
make requirements          # Update requirements.txt
```

### Testing

```bash
# Run all tests
pytest

# Run specific test
pytest apps/users/tests.py

# Run with coverage
pytest --cov=apps

# Run only fast tests
pytest -m "not slow"
```

### Code Quality

```bash
# Format code
black .

# Lint
flake8 .

# Type checking
mypy .
```

---

## 🚀 Deployment

### Option 1: Railway.app (Recommended)

```bash
# 1. Create app on Railway
# 2. Add PostgreSQL & Redis databases
# 3. Set environment variables in Railway dashboard
# 4. Deploy

git push origin main  # Auto-deploy via git push
```

### Option 2: Docker

```bash
# Build image
docker build -t jobpulse:latest -f deployment/Dockerfile .

# Run container
docker run \
  -e DJANGO_ENV=production \
  -e SECRET_KEY=your-key \
  -p 8000:8000 \
  jobpulse:latest
```

### Option 3: Traditional VPS

```bash
# 1. SSH into VPS
ssh root@your-vps

# 2. Install dependencies
sudo apt update && sudo apt install python3.11 postgresql redis-server nginx

# 3. Clone & setup
git clone https://github.com/yourusername/jobpulse.git
cd jobpulse/backend
make setup

# 4. Start services with systemd
sudo systemctl start gunicorn
sudo systemctl start celery
sudo systemctl start celery-beat

# 5. Configure Nginx
sudo nano /etc/nginx/sites-available/jobpulse
sudo systemctl restart nginx
```

---

## 🐛 Troubleshooting

### Redis Connection Failed
```bash
# Check Redis is running
redis-cli ping  # Should return "PONG"

# Restart Redis
redis-server  # or systemctl restart redis
```

### Celery Tasks Not Running
```bash
# Check if worker is running
celery -A config inspect active

# Clear task queue
celery -A config purge

# Restart worker
pkill -f celery && celery -A config worker -l info
```

### PostgreSQL Connection Error
```bash
# Check connection
psql postgresql://user:password@localhost:5432/jobpulse

# Reset migrations
python manage.py migrate --fake-initial
```

### Bot Not Responding
```bash
# Check bot token in .env
# Verify backend is running
curl http://localhost:8000/api/users/

# View bot logs
python bot/bot.py  # Check console output
```

### HH.ru Rate Limiting
```
The parser respects HH.ru API limits (150 requests/minute).
If you see "429 Too Many Requests":
- Wait for cooldown (automatically handled)
- Reduce search queries in make_test_users
- Increase interval between parses
```

---

## 📞 Support & Contribution

### Getting Help
- 📖 [Full Documentation](./docs/)
- 🐛 [Report Issues](https://github.com/yourusername/jobpulse/issues)
- 💬 [Telegram Support](https://t.me/jobpulse_support)

### Contributing
1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

---

## 📄 License

This project is licensed under the MIT License - see LICENSE file for details.

---

## 🙏 Acknowledgments

- **HH.ru API** - Job vacancies data
- **aiogram** - Telegram Bot framework
- **Django REST Framework** - API framework
- **Celery** - Task queue
- **Railway.app** - Hosting platform

---

## 📊 Project Statistics

```
Backend:
  - 5 Django Apps
  - 25+ API Endpoints
  - 10+ Celery Tasks
  - PostgreSQL + Redis

Bot:
  - 7 Handler Modules
  - 20+ Telegram Commands
  - FSM State Management
  - Redis Session Storage

Development:
  - 100+ Make Commands
  - Docker Support
  - Test Coverage
  - CI/CD Ready
```

---

**Last Updated**: January 2026 | **Version**: 1.0.0