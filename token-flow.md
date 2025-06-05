# AI Agent Token Exchange Flow with RFC 8693

## Complete Token Exchange Flow for AI Agents

This demonstrates how AI agents can use RFC 8693 Token Exchange to create a secure delegation chain for financial processing tasks.

## Step 1: User Authorization (Initial OAuth Flow)

### 1.1 User Authorization Request
```http
GET /authorize?response_type=code&client_id=agent-planner-app&redirect_uri=https://agent-planner.example.com/callback&scope=financial:read%20tax:process&state=xyz123 HTTP/1.1
Host: auth.example.com
```

### 1.2 User Consent and Authorization Code Response
```http
HTTP/1.1 302 Found
Location: https://agent-planner.example.com/callback?code=SplxlOBeZQQYbYS6WxSbIA&state=xyz123
```

### 1.3 Agent-Planner Token Exchange (Authorization Code → Access Token)
```http
POST /token HTTP/1.1
Host: auth.example.com
Content-Type: application/x-www-form-urlencoded
Authorization: Basic YWdlbnQtcGxhbm5lcjpzZWNyZXQ=

grant_type=authorization_code
&code=SplxlOBeZQQYbYS6WxSbIA
&redirect_uri=https://agent-planner.example.com/callback
&client_id=agent-planner-app
```

### 1.4 Initial Access Token Response (for Agent-Planner)
```json
{
  "access_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJhdXRoLmV4YW1wbGUuY29tIiwic3ViIjoidXNlcjEyMyIsImF1ZCI6ImFnZW50LXBsYW5uZXItYXBwIiwiaWF0IjoxNzM1ODg0MDAwLCJleHAiOjE3MzU4ODc2MDAsInNjb3BlIjoiZmluYW5jaWFsOnJlYWQgdGF4OnByb2Nlc3MiLCJjbGllbnRfaWQiOiJhZ2VudC1wbGFubmVyLWFwcCIsIm1heV9hY3QiOnsic3ViIjoiYWdlbnQtdGF4LW9wdGltaXplciIsInNjb3BlcyI6WyJ0YXg6cHJvY2VzcyJdfX0.signature",
  "token_type": "Bearer",
  "expires_in": 3600,
  "scope": "financial:read tax:process"
}
```

**Decoded Initial Token (Agent-Planner):**
```json
{
  "iss": "auth.example.com",
  "sub": "user123",
  "aud": "agent-planner-app",
  "iat": 1735884000,
  "exp": 1735887600,
  "scope": "financial:read tax:process",
  "client_id": "agent-planner-app",
  "may_act": {
    "sub": "agent-tax-optimizer",
    "scopes": ["tax:process"]
  }
}
```

## Step 2: Agent-Planner → Agent-TaxOptimizer Token Exchange

### 2.1 Token Exchange Request (RFC 8693)
```http
POST /token HTTP/1.1
Host: auth.example.com
Content-Type: application/x-www-form-urlencoded
Authorization: Basic YWdlbnQtcGxhbm5lcjpzZWNyZXQ=

grant_type=urn:ietf:params:oauth:grant-type:token-exchange
&subject_token=eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJhdXRoLmV4YW1wbGUuY29tIiwic3ViIjoidXNlcjEyMyIsImF1ZCI6ImFnZW50LXBsYW5uZXItYXBwIiwiaWF0IjoxNzM1ODg0MDAwLCJleHAiOjE3MzU4ODc2MDAsInNjb3BlIjoiZmluYW5jaWFsOnJlYWQgdGF4OnByb2Nlc3MiLCJjbGllbnRfaWQiOiJhZ2VudC1wbGFubmVyLWFwcCIsIm1heV9hY3QiOnsic3ViIjoiYWdlbnQtdGF4LW9wdGltaXplciIsInNjb3BlcyI6WyJ0YXg6cHJvY2VzcyJdfX0.signature
&subject_token_type=urn:ietf:params:oauth:token-type:access_token
&actor_token=eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJhdXRoLmV4YW1wbGUuY29tIiwic3ViIjoiYWdlbnQtcGxhbm5lciIsImF1ZCI6ImF1dGguZXhhbXBsZS5jb20iLCJpYXQiOjE3MzU4ODQwMDAsImV4cCI6MTczNTg4NzYwMCwiY2xpZW50X2lkIjoiYWdlbnQtcGxhbm5lci1hcHAifQ.signature
&actor_token_type=urn:ietf:params:oauth:token-type:access_token
&audience=agent-tax-optimizer
&scope=tax:process
&requested_token_type=urn:ietf:params:oauth:token-type:access_token
```

### 2.2 Token Exchange Response (Agent-TaxOptimizer Token)
```json
{
  "access_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJhdXRoLmV4YW1wbGUuY29tIiwic3ViIjoidXNlcjEyMyIsImF1ZCI6ImFnZW50LXRheC1vcHRpbWl6ZXIiLCJpYXQiOjE3MzU4ODQwNjAsImV4cCI6MTczNTg4NzY2MCwic2NvcGUiOiJ0YXg6cHJvY2VzcyIsImFjdCI6eyJzdWIiOiJhZ2VudC1wbGFubmVyIiwiY2xpZW50X2lkIjoiYWdlbnQtcGxhbm5lci1hcHAifSwibWF5X2FjdCI6eyJzdWIiOiJhZ2VudC1jYWxjdWxhdG9yIiwic2NvcGVzIjpbInRheDpjYWxjdWxhdGUiXX19.signature",
  "token_type": "Bearer",
  "expires_in": 3600,
  "scope": "tax:process",
  "issued_token_type": "urn:ietf:params:oauth:token-type:access_token"
}
```

**Decoded Token (Agent-TaxOptimizer):**
```json
{
  "iss": "auth.example.com",
  "sub": "user123",
  "aud": "agent-tax-optimizer",
  "iat": 1735884060,
  "exp": 1735887660,
  "scope": "tax:process",
  "act": {
    "sub": "agent-planner",
    "client_id": "agent-planner-app"
  },
  "may_act": {
    "sub": "agent-calculator",
    "scopes": ["tax:calculate"]
  }
}
```

## Step 3: Agent-TaxOptimizer → Agent-Calculator Token Exchange

### 3.1 Token Exchange Request (RFC 8693)
```http
POST /token HTTP/1.1
Host: auth.example.com
Content-Type: application/x-www-form-urlencoded
Authorization: Basic YWdlbnQtdGF4LW9wdGltaXplcjpzZWNyZXQ=

grant_type=urn:ietf:params:oauth:grant-type:token-exchange
&subject_token=eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJhdXRoLmV4YW1wbGUuY29tIiwic3ViIjoidXNlcjEyMyIsImF1ZCI6ImFnZW50LXRheC1vcHRpbWl6ZXIiLCJpYXQiOjE3MzU4ODQwNjAsImV4cCI6MTczNTg4NzY2MCwic2NvcGUiOiJ0YXg6cHJvY2VzcyIsImFjdCI6eyJzdWIiOiJhZ2VudC1wbGFubmVyIiwiY2xpZW50X2lkIjoiYWdlbnQtcGxhbm5lci1hcHAifSwibWF5X2FjdCI6eyJzdWIiOiJhZ2VudC1jYWxjdWxhdG9yIiwic2NvcGVzIjpbInRheDpjYWxjdWxhdGUiXX19.signature
&subject_token_type=urn:ietf:params:oauth:token-type:access_token
&actor_token=eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJhdXRoLmV4YW1wbGUuY29tIiwic3ViIjoiYWdlbnQtdGF4LW9wdGltaXplciIsImF1ZCI6ImF1dGguZXhhbXBsZS5jb20iLCJpYXQiOjE3MzU4ODQwNjAsImV4cCI6MTczNTg4NzY2MCwiY2xpZW50X2lkIjoiYWdlbnQtdGF4LW9wdGltaXplci1hcHAifQ.signature
&actor_token_type=urn:ietf:params:oauth:token-type:access_token
&audience=agent-calculator
&scope=tax:calculate
&requested_token_type=urn:ietf:params:oauth:token-type:access_token
```

### 3.2 Token Exchange Response (Agent-Calculator Token)
```json
{
  "access_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJhdXRoLmV4YW1wbGUuY29tIiwic3ViIjoidXNlcjEyMyIsImF1ZCI6ImFnZW50LWNhbGN1bGF0b3IiLCJpYXQiOjE3MzU4ODQxMjAsImV4cCI6MTczNTg4NzcyMCwic2NvcGUiOiJ0YXg6Y2FsY3VsYXRlIiwiYWN0Ijp7InN1YiI6ImFnZW50LXRheC1vcHRpbWl6ZXIiLCJjbGllbnRfaWQiOiJhZ2VudC10YXgtb3B0aW1pemVyLWFwcCIsImNoYWluIjpbeyJzdWIiOiJhZ2VudC1wbGFubmVyIiwiY2xpZW50X2lkIjoiYWdlbnQtcGxhbm5lci1hcHAifV19fQ.signature",
  "token_type": "Bearer",
  "expires_in": 3600,
  "scope": "tax:calculate",
  "issued_token_type": "urn:ietf:params:oauth:token-type:access_token"
}
```

**Decoded Token (Agent-Calculator):**
```json
{
  "iss": "auth.example.com",
  "sub": "user123",
  "aud": "agent-calculator",
  "iat": 1735884120,
  "exp": 1735887720,
  "scope": "tax:calculate",
  "act": {
    "sub": "agent-tax-optimizer",
    "client_id": "agent-tax-optimizer-app",
    "chain": [
      {
        "sub": "agent-planner",
        "client_id": "agent-planner-app"
      }
    ]
  }
}
```

## Step 4: Agent-Calculator → Tax API Call

### 4.1 API Request with Final Token
```http
GET /api/v1/calculate-tax HTTP/1.1
Host: tax-api.example.com
Authorization: Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJhdXRoLmV4YW1wbGUuY29tIiwic3ViIjoidXNlcjEyMyIsImF1ZCI6ImFnZW50LWNhbGN1bGF0b3IiLCJpYXQiOjE3MzU4ODQxMjAsImV4cCI6MTczNTg4NzcyMCwic2NvcGUiOiJ0YXg6Y2FsY3VsYXRlIiwiYWN0Ijp7InN1YiI6ImFnZW50LXRheC1vcHRpbWl6ZXIiLCJjbGllbnRfaWQiOiJhZ2VudC10YXgtb3B0aW1pemVyLWFwcCIsImNoYWluIjpbeyJzdWIiOiJhZ2VudC1wbGFubmVyIiwiY2xpZW50X2lkIjoiYWdlbnQtcGxhbm5lci1hcHAifV19fQ.signature
Content-Type: application/json

{
  "income": 75000,
  "deductions": 12000,
  "filing_status": "single"
}
```

### 4.2 Tax API Token Validation and Response
The Tax API validates the token and sees:
- **Subject**: `user123` (original user)
- **Audience**: `agent-calculator` (this agent)
- **Scope**: `tax:calculate` (authorized action)
- **Actor Chain**: `agent-planner` → `agent-tax-optimizer` → `agent-calculator`

```json
{
  "calculated_tax": 9250.00,
  "effective_rate": 12.33,
  "marginal_rate": 22.0,
  "calculation_id": "calc_789",
  "processed_by": "agent-calculator",
  "on_behalf_of": "user123",
  "delegation_chain": ["agent-planner", "agent-tax-optimizer", "agent-calculator"]
}
```

## Key Security Features

### 1. **Progressive Scope Reduction**
- Initial: `['financial:read', 'tax:process']`
- Agent-TaxOptimizer: `['tax:process']`
- Agent-Calculator: `['tax:calculate']`

### 2. **Auditable Delegation Chain**
Each token contains the complete delegation chain in the `act` claim, enabling full traceability.

### 3. **Time-Limited Tokens**
Each token has its own expiration, typically shorter-lived as the chain progresses.

### 4. **Audience Restriction**
Each token is bound to a specific audience (agent), preventing token misuse.

### 5. **May Act Authorization**
The `may_act` claim in each token explicitly authorizes which agents can be delegated to next.

## Authorization Server Policy Example

```javascript
// Policy for token exchange validation
function validateTokenExchange(subject_token, actor_token, requested_audience, requested_scope) {
  // 1. Validate subject token
  const decoded_subject = jwt.verify(subject_token);
  
  // 2. Check may_act authorization
  if (!decoded_subject.may_act || 
      decoded_subject.may_act.sub !== requested_audience ||
      !decoded_subject.may_act.scopes.includes(requested_scope)) {
    throw new Error("Delegation not authorized");
  }
  
  // 3. Validate actor token
  const decoded_actor = jwt.verify(actor_token);
  
  // 4. Create new token with delegation chain
  const new_token = {
    iss: "auth.example.com",
    sub: decoded_subject.sub, // Preserve original user
    aud: requested_audience,
    scope: requested_scope,
    act: {
      sub: decoded_actor.sub,
      client_id: decoded_actor.client_id,
      chain: buildDelegationChain(decoded_subject.act)
    }
  };
  
  return jwt.sign(new_token);
}
```

This flow demonstrates how RFC 8693 enables secure, auditable, and scope-limited delegation chains for AI agents while maintaining full traceability back to the original user authorization.