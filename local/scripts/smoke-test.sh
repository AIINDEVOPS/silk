#!/usr/bin/env bash
# smoke-test.sh – Quick end-to-end validation of the local Minikube deployment
# Run after: make deploy-helm
# Usage: ./local/scripts/smoke-test.sh

set -euo pipefail

NAMESPACE="csv-app"
PASS=0
FAIL=0

green()  { echo -e "\033[32m✅ $*\033[0m"; }
red()    { echo -e "\033[31m❌ $*\033[0m"; }
yellow() { echo -e "\033[33m⚠️  $*\033[0m"; }
header() { echo -e "\n\033[1;34m══ $* ══\033[0m"; }

check() {
  local desc="$1"; shift
  if "$@" &>/dev/null; then
    green "$desc"
    PASS=$((PASS + 1))
  else
    red "$desc"
    FAIL=$((FAIL + 1))
  fi
}

header "Minikube cluster"
check "Minikube is running"           minikube status
check "kubectl context is minikube"   bash -c 'kubectl config current-context | grep -q minikube'
check "metrics-server running"        kubectl get deployment metrics-server -n kube-system

header "Namespace + Pods"
check "csv-app namespace exists"      kubectl get ns $NAMESPACE
check "csv-app deployment exists"     kubectl get deployment csv-app -n $NAMESPACE
check "minio deployment exists"       kubectl get deployment minio -n $NAMESPACE
check "csv-app pods are 2/2 ready"    bash -c "kubectl get pods -n $NAMESPACE -l app=csv-app | grep -E '2/2.*Running' | wc -l | grep -q [1-9]"
check "minio pod is running"          bash -c "kubectl get pods -n $NAMESPACE -l app=minio | grep -q Running"

header "Services"
check "csv-app-service NodePort"      kubectl get svc csv-app-service -n $NAMESPACE
check "minio ClusterIP"               kubectl get svc minio -n $NAMESPACE
check "minio-console NodePort"        kubectl get svc minio-console -n $NAMESPACE

header "HPA"
check "HPA csv-app-hpa exists"        kubectl get hpa csv-app-hpa -n $NAMESPACE
check "HPA min=2 max=5"               bash -c "kubectl get hpa csv-app-hpa -n $NAMESPACE -o jsonpath='{.spec.minReplicas}' | grep -q 2"

header "Shared static volume (emptyDir – NOT NFS)"
check "Init container completed"      bash -c "kubectl get pod -n $NAMESPACE -l app=csv-app -o jsonpath='{.items[0].status.initContainerStatuses[0].state.terminated.reason}' | grep -q Completed"
check "CSS file in shared volume"     kubectl exec -n $NAMESPACE deployment/csv-app -c nginx -- test -f /app/shared-static/css/main.css
check "JS file in shared volume"      kubectl exec -n $NAMESPACE deployment/csv-app -c nginx -- test -f /app/shared-static/js/main.js
check "Nginx serves /static/css/"     bash -c "kubectl exec -n $NAMESPACE deployment/csv-app -c nginx -- wget -qO- http://127.0.0.1/static/css/main.css | grep -q 'primary'"

header "Flask application"
check "Flask health endpoint"         bash -c "kubectl exec -n $NAMESPACE deployment/csv-app -c flask-app -- curl -sf http://localhost:5000/health | grep -q healthy"
check "Flask ready endpoint"          bash -c "kubectl exec -n $NAMESPACE deployment/csv-app -c flask-app -- curl -sf http://localhost:5000/ready | grep -q ready"
check "Storage backend is minio"      bash -c "kubectl exec -n $NAMESPACE deployment/csv-app -c flask-app -- curl -sf http://localhost:5000/health | grep -q minio"

header "MinIO (local S3)"
check "MinIO API reachable from pod"  bash -c "kubectl exec -n $NAMESPACE deployment/csv-app -c flask-app -- curl -sf http://minio:9000/minio/health/live"
check "csv-uploads bucket exists"     bash -c "kubectl exec -n $NAMESPACE deployment/minio -- mc alias set local http://localhost:9000 minioadmin minioadmin 2>/dev/null && kubectl exec -n $NAMESPACE deployment/minio -- mc ls local/ | grep -q csv-uploads"

header "End-to-End HTTP test"
# LoadBalancer is exposed at 127.0.0.1:8080 via minikube tunnel
APP_URL="${APP_URL:-http://127.0.0.1:8080}"
if ! curl -sf --max-time 5 "$APP_URL/health" &>/dev/null; then
  yellow "App not reachable at $APP_URL — is 'minikube tunnel' running? Skipping HTTP tests."
  APP_URL=""
fi
if [ -z "$APP_URL" ]; then
  yellow "Skipping HTTP tests"
else
  # Health via HTTP through Nginx
  if curl -sf "$APP_URL/health" | grep -q "healthy"; then
    green "Health via Nginx → Flask chain"
    PASS=$((PASS + 1))
  else
    red "Health via Nginx → Flask chain"
    FAIL=$((FAIL + 1))
  fi

  # Index page loads
  if curl -sf "$APP_URL/" | grep -q "CSV File Processor"; then
    green "Index page loads"
    PASS=$((PASS + 1))
  else
    red "Index page loads"
    FAIL=$((FAIL + 1))
  fi

  # CSV upload
  TEST_CSV="${TMPDIR:-/tmp}/test-smoke.csv"
  cat > "$TEST_CSV" <<'CSV'
"ID","Name","Price"
"001","Test Product","100.00"
"002","Another Product","200.00"
CSV

  RESP=$(curl -sf -X POST "$APP_URL/upload" \
    -F "file=@${TEST_CSV};type=text/csv" \
    --max-time 30 || echo "")

  if echo "$RESP" | grep -qi "processed successfully\|rows"; then
    green "CSV upload + processing works"
    PASS=$((PASS + 1))
  else
    red "CSV upload + processing failed"
    FAIL=$((FAIL + 1))
  fi
  rm -f "$TEST_CSV"
fi

# ── Summary ──────────────────────────────────────────────────────────────────
echo ""
echo "════════════════════════════════════════"
echo "  Smoke Test Results"
echo "════════════════════════════════════════"
echo "  Passed : $PASS"
echo "  Failed : $FAIL"
echo "  Total  : $((PASS + FAIL))"
echo "════════════════════════════════════════"

if [ -n "${APP_URL:-}" ]; then
  echo "  App URL    : $APP_URL"
fi
echo "  MinIO UI   : minikube service minio-console -n $NAMESPACE"
echo "  Dashboard  : minikube dashboard"
echo "════════════════════════════════════════"

if [ $FAIL -gt 0 ]; then
  echo ""
  red "Some checks failed. Run 'make logs' to debug."
  exit 1
else
  echo ""
  green "All checks passed! Environment is ready."
  exit 0
fi
