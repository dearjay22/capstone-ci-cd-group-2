# Capstone CI/CD Project - Group 2

## 🎯 Project Overview

A comprehensive e-commerce application demonstrating end-to-end CI/CD pipeline implementation with microservices architecture, automated testing, security scanning, and cloud deployment.

### Architecture

```
┌─────────────┐
│  Frontend   │ (Flask + HTML/CSS/JS)
│  Port: 3000 │
└──────┬──────┘
       │
       ├──────────────┬──────────────┬──────────────┐
       │              │              │              │
┌──────▼──────┐ ┌────▼─────┐ ┌──────▼──────┐ ┌────▼──────┐
│   Users     │ │ Products │ │   Orders    │ │   MySQL   │
│ Port: 5001  │ │Port: 5002│ │ Port: 5003  │ │Port: 3306 │
└─────────────┘ └──────────┘ └─────────────┘ └───────────┘
```

## 🚀 Features

### Application Components

1. **Users Service** (Python/Flask)
   - Create and list users
   - Email validation
   - MySQL integration

2. **Products Service** (Python/Flask)
   - CRUD operations for products
   - Price validation
   - Product descriptions

3. **Orders Service** (Python/Flask)
   - Create orders linking users and products
   - Order status management
   - Total price calculation

4. **Frontend** (Flask + HTML/CSS/JS)
   - Interactive UI with forms
   - Real-time data display
   - RESTful API integration

### CI/CD Pipeline

- **GitHub Actions** workflows for:
  - Automated testing (15+ unit tests)
  - Code coverage reporting (with Codecov)
  - Security scanning (Bandit + Trivy)
  - Code quality checks (Flake8)
  - Docker image building
  - AWS deployment with CDK

## 📋 Prerequisites

- Docker & Docker Compose
- Python 3.11+
- MySQL 8.0
- AWS Account (for deployment)
- GitHub Account

## 🛠️ Local Development Setup

### 1. Clone Repository

```bash
git clone https://github.com/dearjay22/capstone-ci-cd-group-2.git
cd capstone-ci-cd-group-2
```

### 2. Using Docker Compose (Recommended)

```bash
# Start all services
docker-compose up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

Access the application:
- Frontend: http://localhost:3000
- Users API: http://localhost:5001
- Products API: http://localhost:5002
- Orders API: http://localhost:5003

### 3. Manual Setup

#### Initialize Database

```bash
mysql -u root -p < scripts/init_db.sql
```

#### Users Service

```bash
cd users-service
pip install -r requirements.txt
export DB_HOST=localhost DB_USER=root DB_PASS=yourpass DB_NAME=capstone
python app.py
```

#### Products Service

```bash
cd products-service
pip install -r requirements.txt
export DB_HOST=localhost DB_USER=root DB_PASS=yourpass DB_NAME=capstone
python app.py
```

#### Orders Service

```bash
cd orders-service
pip install -r requirements.txt
export DB_HOST=localhost DB_USER=root DB_PASS=yourpass DB_NAME=capstone
python app.py
```

#### Frontend

```bash
cd frontend
pip install -r requirements.txt
export USERS_HOST=http://localhost:5001
export PRODUCTS_HOST=http://localhost:5002
export ORDERS_HOST=http://localhost:5003
python app.py
```

## 🧪 Testing

### Run All Tests

```bash
# Users service
cd users-service
pytest --cov=. --cov-report=html

# Products service
cd products-service
pytest --cov=. --cov-report=html

# Orders service
cd orders-service
pytest --cov=. --cov-report=html
```

### Code Quality & Security

```bash
# Linting
flake8 users-service --max-line-length=120
flake8 products-service --max-line-length=120
flake8 orders-service --max-line-length=120

# Security scanning
bandit -r users-service -ll
bandit -r products-service -ll
bandit -r orders-service -ll
```

## 📊 API Documentation

### Users Service

**GET /users** - List all users
```bash
curl http://localhost:5001/users
```

**POST /users** - Create a user
```bash
curl -X POST http://localhost:5001/users \
  -H "Content-Type: application/json" \
  -d '{"name":"John Doe","email":"john@example.com"}'
```

### Products Service

**GET /products** - List all products
```bash
curl http://localhost:5002/products
```

**POST /products** - Create a product
```bash
curl -X POST http://localhost:5002/products \
  -H "Content-Type: application/json" \
  -d '{"name":"Widget","price":9.99,"description":"A useful widget"}'
```

**GET /products/{id}** - Get specific product
```bash
curl http://localhost:5002/products/1
```

**PUT /products/{id}** - Update a product
```bash
curl -X PUT http://localhost:5002/products/1 \
  -H "Content-Type: application/json" \
  -d '{"price":12.99}'
```

**DELETE /products/{id}** - Delete a product
```bash
curl -X DELETE http://localhost:5002/products/1
```

### Orders Service

**GET /orders** - List all orders
```bash
curl http://localhost:5003/orders
```

**POST /orders** - Create an order
```bash
curl -X POST http://localhost:5003/orders \
  -H "Content-Type: application/json" \
  -d '{"user_id":1,"product_id":1,"quantity":2}'
```

**GET /orders/user/{user_id}** - Get orders for a user
```bash
curl http://localhost:5003/orders/user/1
```

**PUT /orders/{id}/status** - Update order status
```bash
curl -X PUT http://localhost:5003/orders/1/status \
  -H "Content-Type: application/json" \
  -d '{"status":"shipped"}'
```

## ☁️ AWS Deployment

### Prerequisites

1. Configure AWS credentials:
```bash
aws configure
```

2. Install CDK:
```bash
npm install -g aws-cdk
pip install -r infra/requirements.txt
```

### Deploy Infrastructure

```bash
cd infra
cdk bootstrap  # First time only
cdk synth      # Generate CloudFormation
cdk deploy --all
```

### GitHub Secrets Required

Add these secrets to your GitHub repository:
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `AWS_REGION`
- `CODECOV_TOKEN`

## 🔄 CI/CD Workflow

### On Pull Request
1. ✅ Run linting (Flake8)
2. 🔒 Security scan (Bandit)
3. 🧪 Run unit tests with coverage
4. 📊 Upload coverage to Codecov
5. 🐋 Build Docker images
6. 🔍 Scan images with Trivy

### On Push to Main
- All PR checks +
- 🚀 Deploy to AWS using CDK

## 📈 Code Coverage

View detailed coverage reports:
- [Codecov: https://app.codecov.io/gh/dearjay22/capstone-ci-cd-group-2]
- Local: Open `htmlcov/index.html` after running pytest

## 🔐 Security

- SQL injection prevention using parameterized queries
- Input validation on all endpoints
- Bandit security scanning in CI
- Trivy container scanning
- No hardcoded credentials

## 🤝 Team & Branching Strategy

### Branching Model
- `main` - Production-ready code
- `feature/*` - Feature development branches
- `bugfix/*` - Bug fix branches

### Contribution Workflow
1. Create feature branch from `main`
2. Make changes and commit
3. Push branch and create Pull Request
4. Request review from team member
5. Address review comments
6. Merge after approval and passing CI


## 🐛 Troubleshooting

### Database Connection Issues

```bash
# Check MySQL is running
docker-compose ps mysql

# View MySQL logs
docker-compose logs mysql

# Restart MySQL
docker-compose restart mysql
```

### Service Not Responding

```bash
# Check service health
curl http://localhost:5001/health
curl http://localhost:5002/health
curl http://localhost:5003/health

# Check logs
docker-compose logs users
docker-compose logs products
docker-compose logs orders
```

### Port Already in Use

```bash
# Find process using port
lsof -i :3000
lsof -i :5001

# Kill process
kill -9 <PID>
```
