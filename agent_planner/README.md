# Agent Planner Service

This service handles financial planning requests and coordinates with the tax optimizer service.

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
CLIENT_ID=agent-planner
CLIENT_SECRET=your-secret
PORT=8001
TAX_OPTIMIZER_URL=http://localhost:8002
```

## Running the Service

Start the service with auto-reload enabled:
```bash
python run.py
```

The service will automatically reload when you make changes to any Python files in the directory.

## API Endpoints

- POST `/generate-plan`: Generate a financial plan
  - Requires Bearer token authentication
  - Accepts financial data in the request body
  - Returns plan details and token flow information