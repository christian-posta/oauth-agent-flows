# User Web Application (user_app)

This is the user-facing web application for the AI Agent OAuth demo. It implements the OAuth2 authorization code flow, provides a financial planning UI, displays real-time token and delegation information, and visualizes agent-to-agent (A2A) message flows.

## Features
- **OAuth2 Authorization Code Flow** with Keycloak
- **Financial Planning Interface**
- **Token Visualization** (decoded JWTs)
- **Delegation Chain Display**
- **A2A Message Flow Visualization** (real-time, via WebSockets)
- **Demo Scenarios and Error Handling**

---

## Prerequisites
- Python 3.9+
- Node.js (v18+ recommended) & npm
- [Keycloak](https://www.keycloak.org/) instance (see project root for setup)

---

## 1. Backend Setup (FastAPI)

1. **Install Python dependencies:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Set environment variables:**
   Create a `.env` file in `services/user_app/` (or set these in your shell):
   ```env
   KEYCLOAK_URL=http://localhost:8081/auth
   KEYCLOAK_EXTERNAL_URL=http://localhost:8081/auth
   KEYCLOAK_REALM=ai-agents
   KEYCLOAK_CLIENT_ID=user-web-app
   KEYCLOAK_CLIENT_SECRET=your_client_secret
   REDIRECT_URI=http://localhost:8000/callback
   ```

3. **Run the FastAPI server:**
   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```
   The backend will be available at [http://localhost:8000](http://localhost:8000)

---

## 2. Frontend Setup (React + Vite)

1. **Install frontend dependencies:**
   ```bash
   cd frontend
   npm install
   ```

2. **Run the frontend in development mode:**
   ```bash
   npm run dev
   ```
   The React app will be available at [http://localhost:5173](http://localhost:5173)

   > **Note:** The Vite dev server proxies API requests to the FastAPI backend.

3. **Build the frontend for production:**
   ```bash
   npm run build
   ```
   The static files will be output to `../static/` and served by FastAPI in production mode.

---

## 3. Using the App
- Open [http://localhost:5173](http://localhost:5173) (dev) or [http://localhost:8000](http://localhost:8000) (prod)
- Login with your Keycloak credentials
- Explore the dashboard, financial planning, token visualization, and A2A flow features

---

## 4. Development Workflow
- **Backend:** Edit `main.py` and restart the FastAPI server for changes
- **Frontend:** Edit files in `frontend/` and Vite will hot-reload changes

---

## 5. Troubleshooting
- Ensure Keycloak is running and configured with the correct realm and client
- Check `.env` values for accuracy
- If you see CORS or cookie issues, make sure both servers are running on `localhost` and using the correct ports

---

## 6. Scripts
- `scripts/setup_frontend.sh`: Installs and builds the frontend (for CI or Docker)

---

## 7. License
MIT 