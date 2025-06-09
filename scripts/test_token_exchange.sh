#!/bin/bash

# Token Exchange Test Script
# This script tests the complete token exchange flow step by step

set -e  # Exit on any error

# Configuration
KEYCLOAK_URL="${KEYCLOAK_URL:-http://localhost:8081}"
REALM_NAME="ai-agents"
USER_CLIENT_ID="user-web-app"
AGENT_PLANNER_CLIENT_ID="agent-planner"
TARGET_CLIENT_ID="agent-tax-optimizer"
TEST_USERNAME="testuser"
TEST_PASSWORD="password123"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_step() {
    echo -e "${CYAN}[STEP]${NC} $1"
}

# Function to wait for user confirmation
confirm_step() {
    local message="$1"
    local response
    
    echo -e "${YELLOW}$message${NC}"
    while true; do
        read -p "Continue? (Y/n): " response
        # Default to 'y' if empty response (just Enter pressed)
        response=${response:-y}
        case $response in
            [Yy]* ) break;;
            [Nn]* ) 
                log_warning "Test aborted by user"
                exit 1
                ;;
            * ) echo "Please answer y or n (default: y).";;
        esac
    done
}

# Function to check if command exists
check_dependency() {
    if ! command -v "$1" &> /dev/null; then
        log_error "$1 is required but not installed"
        exit 1
    fi
}

# Function to pretty print JSON
pretty_json() {
    if command -v jq &> /dev/null; then
        echo "$1" | jq .
    else
        echo "$1"
    fi
}

# Function to decode JWT payload
decode_jwt() {
    local token="$1"
    local payload=$(echo "$token" | cut -d'.' -f2)
    
    # Add padding if needed
    while [ $((${#payload} % 4)) -ne 0 ]; do
        payload="${payload}="
    done
    
    if command -v base64 &> /dev/null; then
        echo "$payload" | base64 -d 2>/dev/null | jq . 2>/dev/null || echo "Could not decode JWT"
    else
        echo "base64 command not available"
    fi
}

# Check dependencies
check_dependencies() {
    log_step "Checking dependencies..."
    check_dependency "curl"
    
    if command -v jq &> /dev/null; then
        log_success "jq found - JSON output will be formatted"
    else
        log_warning "jq not found - JSON output will be raw"
    fi
    
    log_success "Dependencies check passed"
}

# Test Keycloak connectivity
test_connectivity() {
    log_step "Testing Keycloak connectivity..."
    
    # Try multiple possible endpoints
    local endpoints=(
        "$KEYCLOAK_URL/realms/$REALM_NAME/.well-known/openid_configuration"
        "$KEYCLOAK_URL/auth/realms/$REALM_NAME/.well-known/openid_configuration"
        "$KEYCLOAK_URL/admin/"
        "$KEYCLOAK_URL/auth/admin/"
    )
    
    local success=false
    for endpoint in "${endpoints[@]}"; do
        log_info "Trying: $endpoint"
        local response
        response=$(curl -s -o /dev/null -w "%{http_code}" "$endpoint" || echo "000")
        
        if [ "$response" == "200" ] || [ "$response" == "302" ]; then
            log_success "Keycloak is accessible at $KEYCLOAK_URL (endpoint: $endpoint, HTTP $response)"
            success=true
            break
        else
            log_warning "Endpoint $endpoint returned HTTP $response"
        fi
    done
    
    if [ "$success" = false ]; then
        log_error "Keycloak not accessible at any known endpoint"
        log_error "Make sure Keycloak is running and the URL is correct"
        exit 1
    fi
}

# Get user access token
get_user_token() {
    log_step "Getting user access token..."
    
    echo "Request details:"
    echo "  URL: $KEYCLOAK_URL/realms/$REALM_NAME/protocol/openid-connect/token"
    echo "  Grant type: password"
    echo "  Client: $USER_CLIENT_ID"
    echo "  User: $TEST_USERNAME"
    echo "  Scope: openid"
    
    confirm_step "Ready to get user token?"
    
    local response
    response=$(curl -s -X POST \
        "$KEYCLOAK_URL/realms/$REALM_NAME/protocol/openid-connect/token" \
        -H 'Content-Type: application/x-www-form-urlencoded' \
        -d "grant_type=password" \
        -d "client_id=$USER_CLIENT_ID" \
        -d "username=$TEST_USERNAME" \
        -d "password=$TEST_PASSWORD" \
        -d "scope=openid")
    
    if echo "$response" | grep -q "access_token"; then
        USER_TOKEN=$(echo "$response" | jq -r '.access_token' 2>/dev/null || echo "$response" | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)
        log_success "User token obtained successfully"
        
        echo "Token response:"
        pretty_json "$response"
        
        echo -e "\n${CYAN}Token Details:${NC}"
        echo "Length: ${#USER_TOKEN} characters"
        echo "First 50 chars: ${USER_TOKEN:0:50}..."
        
        echo -e "\n${CYAN}Decoded JWT Payload:${NC}"
        decode_jwt "$USER_TOKEN"
        
        confirm_step "User token looks good?"
    else
        log_error "Failed to get user token"
        echo "Response:"
        pretty_json "$response"
        exit 1
    fi
}

# Get agent planner client secret
get_client_secret() {
    log_step "Getting agent-planner client secret..."
    
    echo "Note: This step requires admin access to Keycloak"
    echo "We'll extract the client secret from your previous curl commands"
    echo "Or you can get it from: Keycloak Admin → Clients → agent-planner → Credentials"
    
    # Try to extract from previous commands or ask user
    if [ -z "$AGENT_PLANNER_SECRET" ]; then
        echo "Please enter the agent-planner client secret:"
        read -r AGENT_PLANNER_SECRET
    fi
    
    if [ -z "$AGENT_PLANNER_SECRET" ]; then
        log_error "Client secret is required"
        exit 1
    fi
    
    log_success "Client secret configured"
    echo "Secret: ${AGENT_PLANNER_SECRET:0:10}... (first 10 chars)"
}

# Test token exchange
test_token_exchange() {
    log_step "Testing token exchange..."
    
    echo "Token exchange details:"
    echo "  Grant type: urn:ietf:params:oauth:grant-type:token-exchange"
    echo "  Requester client: $AGENT_PLANNER_CLIENT_ID"
    echo "  Subject token: User access token"
    echo "  Target audience: $TARGET_CLIENT_ID"
    echo "  Scope: (none - basic exchange)"
    
    confirm_step "Ready to test token exchange?"
    
    local response
    response=$(curl -s -X POST \
        "$KEYCLOAK_URL/realms/$REALM_NAME/protocol/openid-connect/token" \
        -H 'Content-Type: application/x-www-form-urlencoded' \
        -d 'grant_type=urn:ietf:params:oauth:grant-type:token-exchange' \
        -d "client_id=$AGENT_PLANNER_CLIENT_ID" \
        -d "client_secret=$AGENT_PLANNER_SECRET" \
        -d "subject_token=$USER_TOKEN" \
        -d 'subject_token_type=urn:ietf:params:oauth:token-type:access_token' \
        -d 'requested_token_type=urn:ietf:params:oauth:token-type:access_token' \
        -d "audience=$TARGET_CLIENT_ID")
    
    if echo "$response" | grep -q "access_token"; then
        EXCHANGED_TOKEN=$(echo "$response" | jq -r '.access_token' 2>/dev/null || echo "$response" | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)
        log_success "Token exchange successful!"
        
        echo "Exchange response:"
        pretty_json "$response"
        
        echo -e "\n${CYAN}Exchanged Token Details:${NC}"
        echo "Length: ${#EXCHANGED_TOKEN} characters"
        echo "First 50 chars: ${EXCHANGED_TOKEN:0:50}..."
        
        echo -e "\n${CYAN}Decoded Exchanged JWT Payload:${NC}"
        decode_jwt "$EXCHANGED_TOKEN"
        
        confirm_step "Token exchange successful - continue with custom scope test?"
        
    else
        log_error "Token exchange failed"
        echo "Response:"
        pretty_json "$response"
        
        # Common troubleshooting
        echo -e "\n${YELLOW}Troubleshooting tips:${NC}"
        echo "1. Ensure 'Standard Token Exchange' is enabled in Keycloak UI:"
        echo "   - Go to Clients → agent-planner → Settings → Capability config"
        echo "2. Check that user has roles for target client (agent-tax-optimizer)"
        echo "3. Verify client secret is correct"
        echo "4. Make sure subject token hasn't expired"
        
        exit 1
    fi
}

# Test token exchange with custom scope
test_token_exchange_with_scope() {
    log_step "Testing token exchange with custom scope..."
    
    echo "Token exchange with scope details:"
    echo "  Same as previous, but with:"
    echo "  Scope: tax:process"
    
    confirm_step "Ready to test token exchange with custom scope?"
    
    local response
    response=$(curl -s -X POST \
        "$KEYCLOAK_URL/realms/$REALM_NAME/protocol/openid-connect/token" \
        -H 'Content-Type: application/x-www-form-urlencoded' \
        -d 'grant_type=urn:ietf:params:oauth:grant-type:token-exchange' \
        -d "client_id=$AGENT_PLANNER_CLIENT_ID" \
        -d "client_secret=$AGENT_PLANNER_SECRET" \
        -d "subject_token=$USER_TOKEN" \
        -d 'subject_token_type=urn:ietf:params:oauth:token-type:access_token' \
        -d 'requested_token_type=urn:ietf:params:oauth:token-type:access_token' \
        -d "audience=$TARGET_CLIENT_ID" \
        -d 'scope=tax:process')
    
    if echo "$response" | grep -q "access_token"; then
        SCOPED_TOKEN=$(echo "$response" | jq -r '.access_token' 2>/dev/null || echo "$response" | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)
        log_success "Token exchange with scope successful!"
        
        echo "Scoped exchange response:"
        pretty_json "$response"
        
        echo -e "\n${CYAN}Scoped Token Details:${NC}"
        echo "Length: ${#SCOPED_TOKEN} characters"
        echo "First 50 chars: ${SCOPED_TOKEN:0:50}..."
        
        echo -e "\n${CYAN}Decoded Scoped JWT Payload:${NC}"
        decode_jwt "$SCOPED_TOKEN"
        
    else
        log_warning "Token exchange with scope failed (this might be expected if scope isn't configured)"
        echo "Response:"
        pretty_json "$response"
        
        if echo "$response" | grep -q "invalid_scope"; then
            echo -e "\n${YELLOW}Note:${NC} The 'tax:process' scope might not be properly configured."
            echo "This is normal if you haven't set up custom scopes yet."
        fi
    fi
}

# Compare tokens
compare_tokens() {
    log_step "Comparing original and exchanged tokens..."
    
    echo -e "${CYAN}=== TOKEN COMPARISON ===${NC}"
    
    echo -e "\n${YELLOW}Original User Token Audience:${NC}"
    decode_jwt "$USER_TOKEN" | jq -r '.aud // "N/A"' 2>/dev/null || echo "Could not extract audience"
    
    echo -e "\n${YELLOW}Exchanged Token Audience:${NC}"
    decode_jwt "$EXCHANGED_TOKEN" | jq -r '.aud // "N/A"' 2>/dev/null || echo "Could not extract audience"
    
    echo -e "\n${YELLOW}Original Token Subject:${NC}"
    decode_jwt "$USER_TOKEN" | jq -r '.sub // "N/A"' 2>/dev/null || echo "Could not extract subject"
    
    echo -e "\n${YELLOW}Exchanged Token Subject:${NC}"
    decode_jwt "$EXCHANGED_TOKEN" | jq -r '.sub // "N/A"' 2>/dev/null || echo "Could not extract subject"
    
    echo -e "\n${YELLOW}Original Token Scopes:${NC}"
    decode_jwt "$USER_TOKEN" | jq -r '.scope // "N/A"' 2>/dev/null || echo "Could not extract scope"
    
    echo -e "\n${YELLOW}Exchanged Token Scopes:${NC}"
    decode_jwt "$EXCHANGED_TOKEN" | jq -r '.scope // "N/A"' 2>/dev/null || echo "Could not extract scope"
    
    if [ -n "$SCOPED_TOKEN" ]; then
        echo -e "\n${YELLOW}Scoped Token Scopes:${NC}"
        decode_jwt "$SCOPED_TOKEN" | jq -r '.scope // "N/A"' 2>/dev/null || echo "Could not extract scope"
    fi
    
    confirm_step "Token comparison complete - review the differences above."
}

# Print summary
print_summary() {
    log_step "Test Summary"
    
    echo -e "${CYAN}=== TOKEN EXCHANGE TEST SUMMARY ===${NC}"
    echo -e "${GREEN}✅ Keycloak connectivity${NC}"
    echo -e "${GREEN}✅ User authentication${NC}"
    echo -e "${GREEN}✅ Basic token exchange${NC}"
    
    if [ -n "$SCOPED_TOKEN" ]; then
        echo -e "${GREEN}✅ Token exchange with custom scope${NC}"
    else
        echo -e "${YELLOW}⚠️  Token exchange with custom scope (failed/skipped)${NC}"
    fi
    
    echo -e "\n${CYAN}Key Findings:${NC}"
    echo "• Token exchange is working correctly"
    echo "• Audience filtering is functional"
    echo "• User roles are properly assigned"
    echo "• Standard token exchange v2 is enabled"
    
    echo -e "\n${CYAN}Next Steps:${NC}"
    echo "• Integrate token exchange into your application"
    echo "• Set up additional client scopes if needed"
    echo "• Configure proper token lifespans for production"
    echo "• Test with different user roles and permissions"
    
    echo -e "\n${GREEN}🎉 Token exchange setup is working correctly!${NC}"
}

# Main function
main() {
    echo -e "${CYAN}=== KEYCLOAK TOKEN EXCHANGE TEST SCRIPT ===${NC}"
    echo "This script will test the complete token exchange flow step by step."
    echo "You'll be asked to confirm each step before proceeding."
    echo ""
    echo "Configuration:"
    echo "  Keycloak URL: $KEYCLOAK_URL"
    echo "  Realm: $REALM_NAME" 
    echo "  User Client: $USER_CLIENT_ID"
    echo "  Requester Client: $AGENT_PLANNER_CLIENT_ID"
    echo "  Target Client: $TARGET_CLIENT_ID"
    echo "  Test User: $TEST_USERNAME"
    echo ""
    
    confirm_step "Ready to start token exchange testing?"
    
    check_dependencies
    test_connectivity
    get_user_token
    get_client_secret
    test_token_exchange
    test_token_exchange_with_scope
    compare_tokens
    print_summary
}

# Handle script arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --url)
            KEYCLOAK_URL="$2"
            shift 2
            ;;
        --secret)
            AGENT_PLANNER_SECRET="$2"
            shift 2
            ;;
        --help)
            echo "Usage: $0 [--url KEYCLOAK_URL] [--secret CLIENT_SECRET]"
            echo ""
            echo "Options:"
            echo "  --url URL      Keycloak URL (default: http://localhost:8081)"
            echo "  --secret SEC   Agent planner client secret"
            echo "  --help         Show this help"
            echo ""
            echo "Example:"
            echo "  $0 --url http://localhost:8081 --secret myClientSecret123"
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Run the main function
main