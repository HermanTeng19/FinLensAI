#!/usr/bin/env bash
# ==============================================================================
# FinLens AI — Complete Automated Test & Quality Verification Suite
# ==============================================================================
# This script executes the complete validation pipeline:
# 1. Backend Linting & Formatting (Ruff)
# 2. Backend Unit & E2E Lifecycle Tests (Pytest with Coverage)
# 3. AI Evaluation Benchmark Suite (Merchant, Categorizer, Agent)
# 4. Apple Shared Core Unit Tests (Swift Package Manager / FinLensCore)
# 5. Multiplatform Xcode Build Verification (iOS & macOS)
# ==============================================================================

set -eo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

echo "======================================================================"
echo "          FinLens AI — End-to-End Test & Verification Suite"
echo "======================================================================"
echo "Root Directory: ${ROOT_DIR}"
echo ""

# ------------------------------------------------------------------------------
# 1. Backend Code Quality & Linting
# ------------------------------------------------------------------------------
echo "==> [1/5] Checking Backend Code Quality with Ruff..."
cd "${ROOT_DIR}/backend"

if [ -f ".venv/bin/ruff" ]; then
    RUFF_BIN=".venv/bin/ruff"
else
    RUFF_BIN="ruff"
fi

${RUFF_BIN} check app tests
${RUFF_BIN} format --check app tests
echo "✓ Backend linting and formatting passed (0 errors)."
echo ""

# ------------------------------------------------------------------------------
# 2. Backend Pytest & Code Coverage
# ------------------------------------------------------------------------------
echo "==> [2/5] Running Backend Unit & E2E Lifecycle Tests with Pytest..."

# Ensure local test database is accessible
if ! nc -z localhost 5432 2>/dev/null; then
    echo "--> Starting local PostgreSQL test container via Docker..."
    docker compose -f "${ROOT_DIR}/infrastructure/docker-compose.yml" up -d db
    sleep 2
fi

if [ -f ".venv/bin/pytest" ]; then
    PYTEST_BIN=".venv/bin/pytest"
else
    PYTEST_BIN="pytest"
fi

${PYTEST_BIN} tests/ --cov=app --cov-report=term-missing --cov-fail-under=80
echo "✓ All backend tests passed with >=80% coverage."
echo ""

# ------------------------------------------------------------------------------
# 3. AI Evaluation Benchmark Suite
# ------------------------------------------------------------------------------
echo "==> [3/5] Running AI Engine Evaluation & Benchmarks..."
if [ -f ".venv/bin/python" ]; then
    PYTHON_BIN=".venv/bin/python"
else
    PYTHON_BIN="python3"
fi

${PYTHON_BIN} -m app.evaluation.runner
echo "✓ AI evaluation benchmarks met all quality gates (>90% accuracy/F1)."
echo ""

# ------------------------------------------------------------------------------
# 4. Apple FinLensCore Swift Package Tests
# ------------------------------------------------------------------------------
echo "==> [4/5] Running Apple Shared Core Tests (FinLensCore)..."
cd "${ROOT_DIR}"
swift test --package-path apple/FinLensCore
echo "✓ FinLensCore Swift Package unit tests passed."
echo ""

# ------------------------------------------------------------------------------
# 5. Apple Multiplatform Xcode Schemes Compilation
# ------------------------------------------------------------------------------
echo "==> [5/5] Building Multiplatform Xcode Schemes (iOS & macOS)..."

echo "--> Compiling FinLens_macOS..."
xcodebuild build \
    -project "${ROOT_DIR}/apple/FinLens/FinLens.xcodeproj" \
    -scheme FinLens_macOS \
    -destination 'platform=macOS' \
    -quiet

echo "--> Compiling FinLens_iOS (Simulator)..."
xcodebuild build \
    -project "${ROOT_DIR}/apple/FinLens/FinLens.xcodeproj" \
    -scheme FinLens_iOS \
    -destination 'generic/platform=iOS Simulator' \
    -quiet

echo "✓ Multiplatform Xcode schemes (iOS & macOS) compiled successfully."
echo ""

echo "======================================================================"
echo "  🎉 ALL TEST SUITES & QUALITY GATES PASSED (100% SUCCESS) 🎉"
echo "======================================================================"
