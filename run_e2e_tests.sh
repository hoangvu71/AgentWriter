#!/bin/bash

# E2E Test Runner Script
# This script starts the test server and runs E2E tests

set -e

echo "🧪 AgentWriter E2E Test Runner"
echo "=============================="

# Check if Python3 is available
if ! command -v python3 &> /dev/null; then
    echo "❌ python3 is required but not found"
    exit 1
fi

# Clean up any existing test database
rm -f test_e2e.db

# Clean up any existing processes on port 8000
echo "🧹 Cleaning up existing processes on port 8000..."
lsof -ti:8000 | xargs kill -9 2>/dev/null || true
sleep 2

# Start the test server in the background
echo "🚀 Starting test server..."
python3 test_app.py &
SERVER_PID=$!

# Function to cleanup on exit
cleanup() {
    echo "🧹 Cleaning up..."
    if ps -p $SERVER_PID > /dev/null 2>&1; then
        echo "Stopping test server (PID: $SERVER_PID)..."
        kill $SERVER_PID 2>/dev/null || true
        wait $SERVER_PID 2>/dev/null || true
    fi
    echo "✅ Cleanup complete"
}

# Set trap to cleanup on script exit
trap cleanup EXIT

# Wait for server to start
echo "⏳ Waiting for server to start..."
for i in {1..30}; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo "✅ Server is running!"
        break
    fi
    sleep 1
    if [ $i -eq 30 ]; then
        echo "❌ Server failed to start within 30 seconds"
        exit 1
    fi
done

# Verify server health
echo "🩺 Checking server health..."
HEALTH_RESPONSE=$(curl -s http://localhost:8000/health)
echo "Health response: $HEALTH_RESPONSE"

# Run the E2E tests
echo "🧪 Running E2E tests..."
cd tests/e2e
python3 run_e2e_tests.py local

# Check test results
TEST_EXIT_CODE=$?

if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo "✅ All E2E tests passed!"
else
    echo "❌ Some E2E tests failed (exit code: $TEST_EXIT_CODE)"
fi

echo "📊 E2E test run complete"
exit $TEST_EXIT_CODE