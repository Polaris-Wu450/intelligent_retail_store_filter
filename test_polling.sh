#!/bin/bash

# Test script for polling functionality
# This script tests the new status endpoint

echo "======================================"
echo "Testing Polling API"
echo "======================================"

API_BASE="http://localhost:8000/api"

# Check if jq is available for better JSON parsing
HAS_JQ=false
if command -v jq &> /dev/null; then
  HAS_JQ=true
fi

echo ""
echo "1. Creating a new action plan..."
RESPONSE=$(curl -s -X POST "${API_BASE}/action-plans/" \
  -H "Content-Type: application/json" \
  -d '{
    "store_name": "Test Store #999",
    "store_location": "123 Test St, Test City",
    "issue_description": "Testing polling functionality"
  }')

# Extract ID using jq if available, otherwise use grep/sed
if [ "$HAS_JQ" = true ]; then
  PLAN_ID=$(echo "$RESPONSE" | jq -r '.id')
else
  # Try with grep
  PLAN_ID=$(echo "$RESPONSE" | grep -oE '"id"[[:space:]]*:[[:space:]]*[0-9]+' | grep -oE '[0-9]+' | head -1)
  
  # Fallback: try with sed
  if [ -z "$PLAN_ID" ]; then
    PLAN_ID=$(echo "$RESPONSE" | sed -n 's/.*"id"[[:space:]]*:[[:space:]]*\([0-9]*\).*/\1/p' | head -1)
  fi
fi

# Check if we got an ID
if [ -z "$PLAN_ID" ] || [ "$PLAN_ID" = "null" ]; then
  echo "❌ Failed to extract plan ID from response"
  echo "Response: $RESPONSE"
  exit 1
fi

echo "✅ Created action plan with ID: $PLAN_ID"
echo "   Response: $RESPONSE"
echo ""

# Simulate polling with exponential backoff
DELAYS=(1 2 3 5 5 5 5 5)
MAX_ATTEMPTS=20
ATTEMPT=0

echo "2. Starting polling (exponential backoff: 1s, 2s, 3s, then 5s)..."
echo ""

while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
  DELAY_INDEX=$((ATTEMPT < ${#DELAYS[@]} ? ATTEMPT : ${#DELAYS[@]} - 1))
  DELAY=${DELAYS[$DELAY_INDEX]}
  
  echo "   Attempt $((ATTEMPT + 1)): Checking status (waiting ${DELAY}s)..."
  sleep $DELAY
  
  STATUS_RESPONSE=$(curl -s "${API_BASE}/action-plans/${PLAN_ID}/status/")
  
  # Extract status using jq if available
  if [ "$HAS_JQ" = true ]; then
    STATUS=$(echo "$STATUS_RESPONSE" | jq -r '.status')
  else
    STATUS=$(echo "$STATUS_RESPONSE" | grep -oE '"status"[[:space:]]*:[[:space:]]*"[^"]*"' | sed -n 's/.*"\([^"]*\)".*/\1/p')
  fi
  
  echo "   Status: $STATUS"
  
  if [ "$STATUS" = "completed" ]; then
    echo ""
    echo "✅ Task completed!"
    echo "   Response: $STATUS_RESPONSE"
    echo ""
    echo "3. Fetching full plan details..."
    FULL_RESPONSE=$(curl -s "${API_BASE}/action-plans/${PLAN_ID}/")
    echo "$FULL_RESPONSE" | grep -o '"plan_content":"[^"]*"' | cut -d'"' -f4 | head -c 200
    echo "..."
    break
  elif [ "$STATUS" = "failed" ]; then
    echo ""
    echo "❌ Task failed!"
    echo "   Response: $STATUS_RESPONSE"
    break
  fi
  
  ATTEMPT=$((ATTEMPT + 1))
done

if [ $ATTEMPT -eq $MAX_ATTEMPTS ]; then
  echo ""
  echo "⚠️  Polling timeout after $MAX_ATTEMPTS attempts"
fi

echo ""
echo "======================================"
echo "Test completed"
echo "======================================"
