#!/usr/bin/env bash
# ==============================================================================
# FinLens AI — Production Container Orchestration & Deployment Script
# ==============================================================================
# Usage:
#   ./scripts/deploy_prod.sh build    - Build production Docker image
#   ./scripts/deploy_prod.sh up       - Start production container stack
#   ./scripts/deploy_prod.sh down     - Stop production container stack
#   ./scripts/deploy_prod.sh verify   - Verify running stack via health & metrics probes
#   ./scripts/deploy_prod.sh logs     - Tail container logs
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
COMPOSE_FILE="${ROOT_DIR}/infrastructure/docker-compose.prod.yml"

COMMAND="${1:-up}"

case "${COMMAND}" in
    build)
        echo "==> Building FinLens AI Production Docker Image..."
        docker compose -f "${COMPOSE_FILE}" build
        echo "✓ Production Docker image built successfully."
        ;;

    up)
        echo "==> Deploying FinLens AI Production Stack..."
        docker compose -f "${COMPOSE_FILE}" up -d --remove-orphans
        echo "✓ Container stack launched."
        echo ""
        "${SCRIPT_DIR}/deploy_prod.sh" verify
        ;;

    down)
        echo "==> Stopping FinLens AI Production Stack..."
        docker compose -f "${COMPOSE_FILE}" down
        echo "✓ Container stack stopped."
        ;;

    logs)
        docker compose -f "${COMPOSE_FILE}" logs -f
        ;;

    verify|test)
        echo "==> Verifying Production Stack Health & Probes..."
        HOST_PORT="${PORT:-8088}"
        BASE_URL="http://127.0.0.1:${HOST_PORT}"

        MAX_RETRIES=20
        RETRY_COUNT=0
        READY=false

        echo "Probing ${BASE_URL}/health..."
        while [ ${RETRY_COUNT} -lt ${MAX_RETRIES} ]; do
            if curl -s -f "${BASE_URL}/health" > /dev/null 2>&1; then
                READY=true
                break
            fi
            RETRY_COUNT=$((RETRY_COUNT + 1))
            sleep 2
        done

        if [ "${READY}" = false ]; then
            echo "❌ ERROR: Production stack failed to become healthy within 40s."
            docker compose -f "${COMPOSE_FILE}" logs
            exit 1
        fi

        echo "✓ Gateway & API Health Probe: OK"

        # Verify Observability Metrics Endpoint
        echo "Probing Observability Metrics..."
        METRICS_RES=$(curl -s "${BASE_URL}/api/v1/observability/metrics")
        if echo "${METRICS_RES}" | grep -q "uptime_seconds"; then
            echo "✓ Observability Metrics Endpoint: OK"
        else
            echo "❌ ERROR: Metrics endpoint returned unexpected payload: ${METRICS_RES}"
            exit 1
        fi

        # Verify Security and Privacy Headers
        echo "Probing Security Headers..."
        HEADERS=$(curl -s -I "${BASE_URL}/health")
        if echo "${HEADERS}" | grep -qi "X-Frame-Options: DENY" && echo "${HEADERS}" | grep -qi "X-Content-Type-Options: nosniff"; then
            echo "✓ Production Security Headers: OK"
        else
            echo "⚠️ Warning: Some security headers missing from response."
        fi

        echo ""
        echo "======================================================================"
        echo "  🎉 PRODUCTION STACK VERIFIED & FULLY OPERATIONAL 🎉"
        echo "  - URL: ${BASE_URL}"
        echo "  - Docs: ${BASE_URL}/docs"
        echo "  - Metrics: ${BASE_URL}/api/v1/observability/metrics"
        echo "======================================================================"
        ;;

    *)
        echo "Usage: $0 {build|up|down|verify|logs}"
        exit 1
        ;;
esac
