#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$SCRIPT_DIR"

PYTEST_BIN=".venv/bin/pytest"
if [ ! -f "$PYTEST_BIN" ]; then
    PYTEST_BIN="pytest"
fi

echo "======================================================="
echo "Running All Microservices Automated Test Suites"
echo "======================================================="

echo ""
echo ">>> [1/3] Running User Service Tests..."
PYTHONPATH="$SCRIPT_DIR:$SCRIPT_DIR/user-service:$SCRIPT_DIR/shared" $PYTEST_BIN user-service/tests -v --tb=short

echo ""
echo ">>> [2/3] Running Notification Service Tests..."
PYTHONPATH="$SCRIPT_DIR:$SCRIPT_DIR/notification-service:$SCRIPT_DIR/shared" $PYTEST_BIN notification-service/tests -v --tb=short

echo ""
echo ">>> [3/3] Running API Gateway Tests..."
PYTHONPATH="$SCRIPT_DIR:$SCRIPT_DIR/gateway:$SCRIPT_DIR/shared" $PYTEST_BIN gateway/tests -v --tb=short

echo ""
echo "======================================================="
echo "All Microservices Test Suites Passed Successfully! ✅"
echo "======================================================="
