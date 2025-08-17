#!/bin/bash

# Quick API endpoint validation script
echo "🚀 Quick API Endpoint Testing"
echo "================================"

BASE_URL="http://localhost:8000"

# Function to test endpoint
test_endpoint() {
    local method=$1
    local endpoint=$2
    local expected_status=${3:-200}

    echo -n "Testing $method $endpoint... "

    if [ "$method" = "GET" ]; then
        response=$(curl -s -w "%{http_code}" -o /dev/null "$BASE_URL$endpoint")
    else
        response=$(curl -s -w "%{http_code}" -o /dev/null -X "$method" "$BASE_URL$endpoint" -H "Content-Type: application/json" -d '{}')
    fi

    if [ "$response" = "$expected_status" ]; then
        echo "✅ PASS ($response)"
    else
        echo "❌ FAIL (got $response, expected $expected_status)"
    fi
}

# Test core endpoints
echo "📊 System Endpoints:"
test_endpoint "GET" "/"
test_endpoint "GET" "/health"
test_endpoint "GET" "/performance"
test_endpoint "GET" "/docs"

echo ""
echo "📝 Content Endpoints:"
test_endpoint "POST" "/api/content/generate"
test_endpoint "POST" "/api/content/optimize/linkedin"

echo ""
echo "📱 Post Endpoints:"
test_endpoint "GET" "/api/posts"
test_endpoint "POST" "/api/post"

echo ""
echo "🎭 Avatar Endpoints:"
test_endpoint "GET" "/api/avatars/profiles"
test_endpoint "GET" "/api/avatars/health"

echo ""
echo "🎨 Media Endpoints:"
test_endpoint "GET" "/api/media"

echo ""
echo "================================"
echo "✅ Quick API test completed!"
