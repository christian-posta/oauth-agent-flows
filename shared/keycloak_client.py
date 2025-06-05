import requests
import json
from typing import Optional
from jose import jwt
from jose.exceptions import JWTError

class KeycloakClient:
    def __init__(self, keycloak_url: str, realm: str, client_id: str, client_secret: str):
        self.keycloak_url = keycloak_url
        self.realm = realm
        self.client_id = client_id
        self.client_secret = client_secret
        self.token_url = f"{keycloak_url}/realms/{realm}/protocol/openid-connect/token"
        self.jwks_url = f"{keycloak_url}/realms/{realm}/protocol/openid-connect/certs"
    
    def exchange_authorization_code(self, code: str, redirect_uri: str) -> dict:
        """Exchange authorization code for access token"""
        data = {
            "grant_type": "authorization_code",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": code,
            "redirect_uri": redirect_uri
        }
        response = requests.post(self.token_url, data=data)
        response.raise_for_status()
        return response.json()
    
    def exchange_token(self, subject_token: str, audience: str, scope: str) -> dict:
        """RFC 8693 Token Exchange"""
        data = {
            "grant_type": "urn:ietf:params:oauth:grant-type:token-exchange",
            "subject_token": subject_token,
            "subject_token_type": "urn:ietf:params:oauth:token-type:access_token", 
            "audience": audience,
            "scope": scope,
            "client_id": self.client_id,
            "client_secret": self.client_secret
        }
        response = requests.post(self.token_url, data=data)
        response.raise_for_status()
        return response.json()
    
    def validate_token(self, token: str) -> dict:
        """Validate and decode JWT token"""
        try:
            # Get the JWKS (JSON Web Key Set)
            jwks_response = requests.get(self.jwks_url)
            jwks_response.raise_for_status()
            jwks = jwks_response.json()
            
            # Get the unverified header to find the key ID
            unverified_header = jwt.get_unverified_header(token)
            key_id = unverified_header['kid']
            
            # Find the public key
            public_key = None
            for key in jwks['keys']:
                if key['kid'] == key_id:
                    public_key = key
                    break
            
            if not public_key:
                raise ValueError("Public key not found")
            
            # Decode and verify the token
            decoded = jwt.decode(
                token,
                public_key,
                algorithms=['RS256'],
                audience=self.client_id,
                issuer=f"{self.keycloak_url}/realms/{self.realm}"
            )
            return decoded
            
        except JWTError as e:
            raise ValueError(f"Invalid token: {str(e)}")
        except requests.RequestException as e:
            raise ValueError(f"Error fetching JWKS: {str(e)}") 