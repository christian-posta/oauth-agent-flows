# AI Agent Demo - Token Exchange Flow

This demo implements a simple financial planning scenario using RFC 8693 Token Exchange for authorization between AI agents.

## Architecture

The system consists of the following components:
* Keycloak (port 8081)
* User App UI (port 5173) - UI / Web interface for user login
* User App Backend (port 8000) - backend routes to service the UI
* Agent-Planner (port 8001) - Initial planning agent
* Agent-TaxOptimizer (port 8002) - Tax optimization agent
* Agent-Calculator (port 8003) - Tax calculation agent
* Tax API (port 8004) - Final tax calculation service

## Prerequisites

- Python 3.9+
- Docker and Docker Compose
- Keycloak 23.0

## Setup

1. **Create and activate a Python virtual environment:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

Note each project has its own requirements.txt file also. You'll need to import those as you start those services. 

3. **Start Keycloak:**
```bash
cd keycloak
docker-compose up -d
```

4. **Configure Keycloak:**

```bash
cd scripts
python setup_keycloak.py --config config.json --url http://localhost:8081 --debug --verbose
```

## Environment Variables

Each service/module should have its own `.env` file (e.g. `user_app/.env`, `agent_planner/.env`, etc.) with the following variables:

```
KEYCLOAK_URL=http://localhost:8080
REALM=ai-agents
CLIENT_ID=your-client-id
CLIENT_SECRET=your-client-secret
REDIRECT_URI=http://localhost:3000/callback  # Only for user_app
```

**Note:** Only include `REDIRECT_URI` in the `user_app/.env` file.

Each should have an example.env file that you can just run:

```bash
cp example.env .env
```

## Running the Services

Each service loads its configuration from its `.env` file using `python-dotenv`.

Start each service in a separate terminal:

```bash
# Terminal 1
python user_app/app.py

# Terminal 2
python agent_planner/app.py

# Terminal 3
python agent_tax_optimizer/app.py

# Terminal 4
python agent_calculator/app.py

# Terminal 5
python tax_api/app.py
```

## Testing the Flow

1. Visit http://localhost:3000/login
2. Login with your Keycloak credentials
3. The token will flow through all agents:
   - User → Planner → TaxOptimizer → Calculator → TaxAPI
4. Each agent exchanges the token for a more restrictive one
5. The final API returns a tax calculation result

## Next Steps

- Phase 2: Proper token validation and JWT decoding
- Phase 3: A2A Protocol for agent communication
- Phase 4: Better error handling and logging
- Phase 5: Simple Docker setup 