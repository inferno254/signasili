# SignAsili - Kenyan Sign Language Education Platform

Empowering 600,000+ Deaf Kenyans through Accessible Education

[![Build Status](https://github.com/inferno254/signasili/workflows/CI/badge.svg)](https://github.com/inferno254/signasili/actions)
[![Coverage](https://codecov.io/gh/inferno254/signasili/branch/main/graph/badge.svg)](https://codecov.io/gh/inferno254/signasili)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## Overview

SignAsili is a comprehensive Kenyan Sign Language (KSL) education platform designed to serve Kenya's deaf community of 600,000+ users across 1,000+ Special Needs Education (SNE) units with 10,000+ teachers.

### Core Features

- **🎓 Interactive KSL Lessons** - 6-phase structured curriculum aligned with KICD CBC
- **🤖 AI-Powered Sign Recognition** - Real-time feedback using MediaPipe Holistic
- **👩‍🏫 IMARA Avatar** - 3D signing assistant with lip-sync
- **📊 Teacher Dashboard** - SLO mastery tracking and intervention tools
- **👨‍👩‍👧 Parent Bridge Programme** - KSL learning for hearing parents
- **📱 Offline-First Mobile App** - Learn anywhere, sync when connected
- **🌍 Community Circles** - Connect deaf learners across Kenya

---

## Architecture

### Tech Stack

| Component | Technology |
|-----------|-----------|
| **Frontend** | Next.js 14.2, React 18.3, TypeScript, Tailwind CSS |
| **Backend** | FastAPI 0.115+, Python 3.11, PostgreSQL 15 |
| **Mobile** | React Native 0.74+, SQLite, WatermelonDB |
| **ML/AI** | TensorFlow, MediaPipe, mT5, TensorFlow Lite |
| **DevOps** | Docker, Kubernetes, GitHub Actions |
| **Monitoring** | Prometheus, Grafana, Sentry |

### Project Structure

```bash
signasili/
├── backend/              # FastAPI backend
│   ├── app/
│   │   ├── api/         # API endpoints
│   │   ├── models/      # SQLAlchemy models
│   │   ├── schemas/     # Pydantic schemas
│   │   ├── services/    # Business logic
│   │   ├── tasks/       # Celery tasks
│   │   └── core/        # Config, security, database
│   ├── alembic/         # Database migrations
│   └── tests/           # Test suite
├── frontend/            # Next.js frontend
│   ├── app/             # App router pages
│   ├── components/      # React components
│   ├── lib/             # Utils, hooks, stores
│   └── public/          # Static assets
├── mobile/              # React Native app
│   ├── src/
│   │   ├── screens/     # App screens
│   │   ├── components/  # Reusable components
│   │   └── services/    # API, offline sync
├── ml/                  # Machine learning
│   ├── sign_detection/  # LSTM sign recognition
│   ├── lip_sync/        # Lip sync scoring
│   └── translation/     # mT5 KSL translation
├── k8s/                 # Kubernetes manifests
└── .github/workflows/   # CI/CD pipelines
```

---

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Node.js 20+
- Python 3.11+
- PostgreSQL 15
- Redis 7

### Development Setup

```bash
# Clone repository
git clone https://github.com/inferno254/signasili.git
cd signasili

# Start infrastructure
docker-compose up -d postgres redis

# Backend setup
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload

# Frontend setup (new terminal)
cd frontend
npm install
npm run dev

# Access the app
# Frontend: http://localhost:3000
# API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

---

## Key Components

### 1. KSL Video Player

Advanced video player with:

- 10 playback speeds (0.25x - 2x)
- Frame-by-frame analysis
- Motion trail visualization
- Picture-in-picture mode
- Multi-language subtitles (English, Kiswahili, Somali, Kikuyu, Luo, Luhya)

### 2. Sign Practice Camera

AI-powered practice with:

- MediaPipe Holistic (543 keypoints)
- Real-time accuracy scoring
- Ghost overlay of IMARA
- Joint-by-joint feedback
- Best attempt recording

### 3. IMARA Avatar

3D signing assistant featuring:

- 96-bone skeletal rigging
- 70 facial blendshapes
- Lip-sync with visemes
- Kenyan outfit variations
- Regional sign variations

### 4. Teacher Dashboard

Comprehensive teaching tools:

- SLO mastery heatmap
- At-risk student identification
- Intervention tracking
- Bulk lesson assignment
- Parent communication

### 5. Bridge Programme

Parent learning system:

- 6-zone progressive curriculum
- KSL card generation
- Co-op challenges with children
- Community verification

---

## API Documentation

Full API documentation available at:

- **OpenAPI/Swagger**: <http://localhost:8000/docs>
- **ReDoc**: <http://localhost:8000/redoc>

### Authentication

```bash
# Register
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "StrongP@ssw0rd123", "full_name": "Test User", "role": "learner"}'

# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "StrongP@ssw0rd123"}'
```

---

## Database Schema

75+ tables including:

- Users (learners, teachers, parents, admins, EARC officers)
- SLO Mastery tracking
- Lesson progress
- Bridge Programme zones
- Sign vocabulary (100+ signs)
- Community circles
- Offline packs

See `backend/alembic/versions/` for full schema.

---

## Machine Learning

### Sign Detection Model

- **Architecture**: LSTM with 2.8M parameters
- **Input**: 30 frames × 1662 keypoints (MediaPipe Holistic)
- **Output**: 100+ KSL sign classes
- **Accuracy**: 85% top-50, 75% full vocabulary
- **Inference**: <100ms on Pixel 4a

### Lip Sync Scoring

- **Input**: 30 frames × 40 lip features
- **Output**: 0-100 score
- **Architecture**: Temporal CNN + LSTM

### KSL Translation

- **Model**: mT5-small (300M parameters)
- **Languages**: KSL gloss ↔ English ↔ Kiswahili
- **Training**: 50,000 parallel sentences

---

## Deployment

### Docker Compose (Development)

```bash
docker-compose up -d
```

### Kubernetes (Production)

```bash
kubectl apply -f k8s/
```

### Environment Variables

```env
# Database
DATABASE_URL=postgresql://signasili:password@postgres:5432/signasili

# Redis
REDIS_URL=redis://redis:6379/0

# Security
SECRET_KEY=your-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7

# AWS S3 (for video storage)
AWS_ACCESS_KEY_ID=your-key
AWS_SECRET_ACCESS_KEY=your-secret
AWS_STORAGE_BUCKET_NAME=signasili-videos

# Sentry
SENTRY_DSN=your-sentry-dsn
```

---

## Testing

```bash
# Backend tests
cd backend
pytest --cov=app --cov-report=html

# Frontend tests
cd frontend
npm run test
npm run test:e2e

# Mobile tests
cd mobile
npm run test
```

---

## Monitoring

- **Prometheus**: <http://localhost:9090>
- **Grafana**: <http://localhost:3001>
- **Sentry**: Error tracking and performance

---

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Development Workflow

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

---

## Security

- JWT tokens with 15-minute expiry
- HTTP-only refresh cookies
- Password hashing with bcrypt
- Rate limiting on auth endpoints
- hCaptcha integration
- MFA support for teachers/admins
- Audit logging

Report security issues to <security@signasili.org>

---

## License

MIT License - see [LICENSE](LICENSE) file

---

## Acknowledgments

- **KICD** - Kenya Institute of Curriculum Development for CBC alignment
- **KNAD** - Kenya National Association of the Deaf
- **EARC Officers** - Educational Assessment and Resource Centres
- **Partner Schools** - Maseno, ACK Ematundu, Sikri, St Angela Mumias, Fr Ouderaa, Ebukuya

---

## Contact

- Website: <https://signasili.org>
- Email: <support@signasili.org>
- Twitter: [@SignAsili](https://twitter.com/SignAsili)

---

## Built with ❤️ for Kenya's Deaf Community
