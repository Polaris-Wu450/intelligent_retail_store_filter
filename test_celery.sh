#!/bin/bash

echo "========================================="
echo "Celery System Test"
echo "========================================="
echo ""

echo "1️⃣  Checking Celery Worker status..."
docker-compose ps celery_worker
echo ""

echo "2️⃣  Checking if tasks are registered..."
docker-compose exec celery_worker celery -A config inspect registered
echo ""

echo "3️⃣  Submitting test order..."
RESPONSE=$(curl -s -X POST http://localhost:8000/api/action-plans/ \
  -H "Content-Type: application/json" \
  -d '{
    "store_name": "Test Store",
    "store_location": "Beijing",
    "issue_description": "System test order"
  }')

echo "$RESPONSE"
PLAN_ID=$(echo "$RESPONSE" | grep -o '"id": [0-9]*' | grep -o '[0-9]*')
echo ""

if [ -z "$PLAN_ID" ]; then
  echo "❌ Failed to create order"
  exit 1
fi

echo "✅ Order created: ID=$PLAN_ID"
echo ""

echo "4️⃣  Checking Celery Worker logs (last 20 lines)..."
docker-compose logs --tail=20 celery_worker
echo ""

echo "5️⃣  Waiting 10 seconds for processing..."
sleep 10
echo ""

echo "6️⃣  Querying result (manual refresh simulation)..."
curl -s http://localhost:8000/api/action-plans/$PLAN_ID/ | python3 -m json.tool
echo ""

echo "========================================="
echo "Test completed!"
echo "Check the status field above:"
echo "  - 'pending' or 'processing' → Wait and run again"
echo "  - 'completed' → Success! ✅"
echo "  - 'failed' → Check error_message"
echo "========================================="
