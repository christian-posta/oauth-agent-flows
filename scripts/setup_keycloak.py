"""
Keycloak setup script to configure the realm and clients.
"""
import os
import time
import httpx
import json
from typing import Dict, Any

KEYCLOAK_URL = "http://localhost:8081"
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin"
REALM_NAME = "ai-agents"

async def wait_for_keycloak():
    """Wait for Keycloak to be ready."""
    while True:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{KEYCLOAK_URL}/health")
                if response.status_code == 200:
                    break
        except Exception:
            pass
        print("Waiting for Keycloak to be ready...")
        time.sleep(5)

async def get_admin_token() -> str:
    """Get admin access token."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{KEYCLOAK_URL}/realms/master/protocol/openid-connect/token",
            data={
                "grant_type": "password",
                "client_id": "admin-cli",
                "username": ADMIN_USERNAME,
                "password": ADMIN_PASSWORD,
            },
        )
        response.raise_for_status()
        return response.json()["access_token"]

async def create_realm(token: str):
    """Create the AI agents realm."""
    realm_config = {
        "realm": REALM_NAME,
        "enabled": True,
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{KEYCLOAK_URL}/admin/realms",
            json=realm_config,
            headers={"Authorization": f"Bearer {token}"},
        )
        if response.status_code == 409:
            print(f"Realm {REALM_NAME} already exists")
        else:
            response.raise_for_status()
            print(f"Created realm {REALM_NAME}")

async def create_client(token: str, client_config: Dict[str, Any]):
    """Create a client in the realm."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{KEYCLOAK_URL}/admin/realms/{REALM_NAME}/clients",
            json=client_config,
            headers={"Authorization": f"Bearer {token}"},
        )
        if response.status_code == 409:
            print(f"Client {client_config['clientId']} already exists")
        else:
            response.raise_for_status()
            print(f"Created client {client_config['clientId']}")

async def create_client_scope(token: str, scope_config: Dict[str, Any]):
    """Create a client scope in the realm."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{KEYCLOAK_URL}/admin/realms/{REALM_NAME}/client-scopes",
            json=scope_config,
            headers={"Authorization": f"Bearer {token}"},
        )
        if response.status_code == 409:
            print(f"Client scope {scope_config['name']} already exists")
        else:
            response.raise_for_status()
            print(f"Created client scope {scope_config['name']}")

async def create_user(token: str, user_config: Dict[str, Any]):
    """Create a user in the realm."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{KEYCLOAK_URL}/admin/realms/{REALM_NAME}/users",
            json=user_config,
            headers={"Authorization": f"Bearer {token}"},
        )
        if response.status_code == 409:
            print(f"User {user_config['username']} already exists")
        else:
            response.raise_for_status()
            print(f"Created user {user_config['username']}")

async def main():
    """Main setup function."""
    # Wait for Keycloak to be ready
    await wait_for_keycloak()

    # Get admin token
    token = await get_admin_token()

    # Create realm
    await create_realm(token)

    # Load realm configuration
    with open("keycloak/import/realm-export.json", "r") as f:
        realm_config = json.load(f)

    # Create client scopes
    for scope in realm_config["clientScopes"]:
        await create_client_scope(token, scope)

    # Create clients
    for client in realm_config["clients"]:
        await create_client(token, client)

    # Create users
    for user in realm_config["users"]:
        await create_user(token, user)

    print("Keycloak setup completed successfully")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main()) 