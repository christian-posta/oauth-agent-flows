# Keycloak Token Exchange Setup

This Python script automates the complete setup for Standard Token Exchange in Keycloak 26.2.5 using configuration from a JSON file.

## Prerequisites

- Python 3.7+
- Keycloak 26.2.5+ server running
- Admin access to Keycloak

## Installation

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Make the script executable:**
   ```bash
   chmod +x setup_keycloak.py
   ```

## Usage

### Basic Setup


```bash
python setup_keycloak.py --config config.json --url http://localhost:8081 --debug --verbose

```

> Note: this sets up everything except enabling token exchange on the agent-planner client; you MUST do this in the UI


After setting up, you can run the test token exchange script which will guide you through:

```bash
./test_token_exchange.sh
```

NOTE, to get the clients working in the larger demo, you'll have to update the client_secrets for each of the clients. 


```bash
python setup_keycloak.py \
  --config config.json \
  --url http://localhost:8081 \
  --admin-user admin \
  --admin-pass admin \
  --test \
  --summary \
  --test-commands \
  --verbose
```

## Command Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `--config, -c` | Path to configuration JSON file | Required |
| `--url, -u` | Keycloak URL | `http://localhost:8080` |
| `--admin-user` | Admin username | `admin` |
| `--admin-pass` | Admin password | `admin` |
| `--test` | Run token exchange test after setup | False |
| `--summary` | Print setup summary | False |
| `--test-commands` | Print test commands | False |
| `--verbose, -v` | Verbose output (includes summary and test commands) | False |

## Configuration File

The script uses a JSON configuration file to define:

- **Realm settings**: Name, token lifespans, etc.
- **Clients**: Public/confidential clients with token exchange settings
- **Client Scopes**: Custom scopes and audience mappers
- **Users**: Test users with role assignments
- **Token Exchange Rules**: Documentation of exchange flows

### Key Configuration Sections

#### Clients
```json
{
  "clientId": "agent-planner",
  "type": "confidential",
  "tokenExchange": {
    "enabled": true,
    "allowRefreshToken": "same-session"
  },
  "assignedScopes": {
    "default": [],
    "optional": ["tax:process"]
  }
}
```

#### Client Scopes with Audience Mappers
```json
{
  "name": "agent-tax-optimizer-audience",
  "description": "Adds agent-tax-optimizer to available audiences",
  "mappers": [
    {
      "name": "agent-tax-optimizer-audience-mapper",
      "type": "oidc-audience-mapper",
      "config": {
        "included.client.audience": "agent-tax-optimizer",
        "access.token.claim": "true"
      }
    }
  ]
}
```

#### Users with Role Assignments
```json
{
  "username": "testuser",
  "password": "password123",
  "clientRoles": {
    "agent-tax-optimizer": ["user"],
    "agent-planner": ["planner"]
  }
}
```

## What the Script Does

1. **Creates Realm**: Sets up the AI agents realm with proper token lifespans
2. **Creates Client Scopes**: Sets up audience scopes and custom scopes
3. **Creates Clients**: Configures public and confidential clients with token exchange
4. **Assigns Scopes**: Links client scopes to clients as default or optional
5. **Creates Roles**: Sets up client-specific roles
6. **Creates Users**: Creates test users with proper role assignments
7. **Tests Setup**: Optionally runs token exchange test

## Token Exchange Flow

The default configuration sets up this flow:

```
[User Web App] 
    ↓ (password grant → token with multiple audiences)
[Agent Planner] 
    ↓ (token exchange → filtered token for tax optimizer)
[Agent Tax Optimizer]
```

## Adding New Clients

To add a new client that can be targeted by token exchange:

1. **Add the client to config.json:**
   ```json
   {
     "clientId": "agent-new-service",
     "type": "confidential",
     "roles": [
       {
         "name": "user",
         "description": "Basic user role"
       }
     ]
   }
   ```

2. **Add audience scope:**
   ```json
   {
     "name": "agent-new-service-audience",
     "description": "Adds agent-new-service to available audiences",
     "mappers": [
       {
         "name": "agent-new-service-audience-mapper",
         "type": "oidc-audience-mapper",
         "config": {
           "included.client.audience": "agent-new-service",
           "access.token.claim": "true"
         }
       }
     ]
   }
   ```

3. **Add scope to user-web-app:**
   ```json
   {
     "clientId": "user-web-app",
     "assignedScopes": {
       "default": ["agent-planner-audience", "agent-new-service-audience"]
     }
   }
   ```

4. **Add role to test users:**
   ```json
   {
     "username": "testuser",
     "clientRoles": {
       "agent-new-service": ["user"]
     }
   }
   ```

## Troubleshooting

### Common Issues

1. **"Failed to get admin token"**
   - Check Keycloak URL and admin credentials
   - Ensure Keycloak is running

2. **"Requested audience not available"**
   - User doesn't have roles for target client
   - Check user role assignments in config

3. **"Invalid scopes"**
   - Custom scope doesn't exist or isn't assigned
   - Check client scope assignments

4. **"Invalid client credentials"**
   - Client secret might have changed
   - Check client configuration

### Debugging

Run with verbose mode to see detailed output:
```bash
python setup_keycloak.py --config config.json --url http://localhost:8081 --verbose
```

The script will show:
- All created resources
- Client secrets
- Test commands
- Token exchange test results

## Example Output

```
[INFO] Starting Keycloak setup from configuration...
[SUCCESS] Admin token obtained
[INFO] Creating realm: ai-agents...
[SUCCESS] Realm ai-agents created
[INFO] Creating client scopes...
[SUCCESS] Client scope agent-planner-audience created
[INFO] Creating clients...
[SUCCESS] Client user-web-app created
[SUCCESS] Client agent-planner created
[INFO] Testing token exchange functionality...
[SUCCESS] Token exchange test successful!

🎉 Setup complete! You can now test token exchange.
```

## Security Notes

- Change default passwords in production
- Use environment variables for sensitive data
- Restrict client redirect URIs appropriately
- Review token lifespans for your use case
- Enable HTTPS in production