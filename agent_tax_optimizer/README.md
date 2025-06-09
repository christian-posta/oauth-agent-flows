# Agent Tax Optimizer Service

This service provides tax optimization recommendations based on financial data.

## Setup

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment variables in `.env`:
```
KEYCLOAK_URL=http://localhost:8080
REALM=master
CLIENT_ID=agent-tax-optimizer
CLIENT_SECRET=your-secret
PORT=8002
```

## Running the Service

Start the service with auto-reload enabled:
```bash
python run.py
```

The service will automatically reload when you make changes to any Python files in the directory.

## API Endpoints

- POST `/optimize`: Optimize tax strategy
  - Requires Bearer token authentication
  - Accepts financial data in the request body
  - Returns optimization recommendations and token information 