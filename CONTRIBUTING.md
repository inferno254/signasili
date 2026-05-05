# Contributing to SignAsili

Thank you for your interest in contributing to SignAsili! This document provides guidelines for contributing to this Kenyan Sign Language (KSL) education platform.

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/YOUR_USERNAME/signasili.git`
3. Create a branch: `git checkout -b feature/your-feature-name`
4. Make your changes
5. Commit: `git commit -m "feat: add your feature"`
6. Push: `git push origin feature/your-feature-name`
7. Open a Pull Request

## Development Setup

### Prerequisites

- Docker & Docker Compose
- Node.js 20+
- Python 3.11+

### Quick Start

```bash
# Start all services
docker-compose up -d

# Run migrations
cd backend
alembic upgrade head

# Access the app
# Frontend: http://localhost:3000
# API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

## Code Standards

### Backend (Python/FastAPI)

- Follow PEP 8
- Use type hints
- Write docstrings for all functions
- Maintain 80%+ test coverage
- Use `black` for formatting: `black backend/`
- Use `isort` for imports: `isort backend/`

### Frontend (TypeScript/Next.js)

- Use TypeScript for all new code
- Follow ESLint rules
- Use Tailwind CSS for styling
- Write tests for components
- Use React Query for data fetching

### Commit Messages

Follow conventional commits:

- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation
- `style:` Formatting
- `refactor:` Code refactoring
- `test:` Tests
- `chore:` Maintenance

Example: `feat: add lip sync scoring to practice mode`

## Testing

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test

# E2E tests
cd frontend
npm run test:e2e
```

## Pull Request Process

1. Update documentation if needed
2. Add tests for new features
3. Ensure all tests pass
4. Update CHANGELOG.md
5. Request review from maintainers
6. Address review feedback
7. Merge when approved

## Accessibility Guidelines

SignAsili serves deaf and hard-of-hearing users. All contributions must consider:

- Visual clarity and contrast
- Support for screen readers
- Keyboard navigation
- Reduced motion preferences
- Large text mode compatibility

## Areas for Contribution

- KSL sign videos from native signers
- ML model improvements
- Mobile app features
- Offline functionality
- Teacher dashboard enhancements
- Documentation and translations

## Questions?

- Open an issue for bugs
- Start a discussion for features
- Email: <contributors@signasili.org>

## Code of Conduct

- Be respectful and inclusive
- Focus on constructive feedback
- Help others learn and grow
- Prioritize accessibility

Thank you for helping make KSL education accessible to all!
