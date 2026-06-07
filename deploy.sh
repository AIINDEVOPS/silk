#!/usr/bin/env bash
# =============================================================================
# DevOps Case Study — One-Command Local Deploy
# =============================================================================
# Usage:
#   bash deploy.sh          # full deploy
#   bash deploy.sh --clean  # tear down everything
#
# Prerequisites (auto-installed if missing):
#   - Docker Desktop (must be running manually first)
#   - minikube, kubectl, helm  (installed by this script via brew if absent)
# =============================================================================

set -euo pipefail

# ── colours ──────────────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
BLUE='\033[0;34m'; BOLD='\033[1m'; NC='\033[0m'

info()    { echo -e "${BLUE}==>${NC} ${BOLD}$*${NC}"; }
success() { echo -e "${GREEN}✅  $*${NC}"; }
warn()    { echo -e "${YELLOW}⚠️   $*${NC}"; }
error()   { echo -e "${RED}❌  $*${NC}"; exit 1; }

NAMESPACE="csv-app"
HELM_RELEASE="csv-app"
IMAGE_NAME="csv-processor"
IMAGE_TAG="local"

# ── clean mode ───────────────────────────────────────────────────────────────
if [[ "${1:-}" == "--clean" ]]; then
  info "Tearing down everything..."
  helm uninstall "$HELM_RELEASE" -n "$NAMESPACE" 2>/dev/null || true
  kubectl delete namespace "$NAMESPACE" 2>/dev/null || true
  minikube stop 2>/dev/null || true
  success "Clean complete. Run 'minikube delete' to fully remove the VM."
  exit 0
fi

echo ""
echo -e "${BOLD}╔══════════════════════════════════════════════════╗${NC}"
echo -e "${BOLD}║   DevOps Case Study — Local Deploy (Minikube)   ║${NC}"
echo -e "${BOLD}╚══════════════════════════════════════════════════╝${NC}"
echo ""

# ── Step 1: Check Docker Desktop is running ──────────────────────────────────
info "Step 1/7 — Checking Docker Desktop..."
if ! docker info >/dev/null 2>&1; then
  error "Docker Desktop is not running. Please start Docker Desktop and re-run."
fi
success "Docker Desktop is running"

# ── Step 2: Install tools if missing ─────────────────────────────────────────
info "Step 2/7 — Checking prerequisites..."

install_if_missing() {
  local cmd="$1" pkg="${2:-$1}"
  if ! command -v "$cmd" &>/dev/null; then
    warn "$cmd not found — installing via brew..."
    brew install "$pkg"
  fi
}

if [[ "$(uname)" == "Darwin" ]]; then
  install_if_missing minikube
  install_if_missing kubectl
  install_if_missing helm
else
  for tool in minikube kubectl helm; do
    command -v "$tool" &>/dev/null || error "$tool is required but not installed."
  done
fi
success "All tools present (minikube, kubectl, helm)"

# ── Step 3: Start Minikube ────────────────────────────────────────────────────
info "Step 3/7 — Starting Minikube cluster..."
if minikube status 2>/dev/null | grep -q "Running"; then
  success "Minikube already running"
else
  minikube start \
    --driver=docker \
    --cpus=4 \
    --memory=8192 \
    --kubernetes-version=stable
  success "Minikube started"
fi

info "   Enabling metrics-server addon (required for HPA)..."
minikube addons enable metrics-server >/dev/null 2>&1 || true
success "metrics-server enabled"

# ── Step 4: Build Docker image inside Minikube ───────────────────────────────
info "Step 4/7 — Building Docker image inside Minikube..."
eval "$(minikube docker-env)"
docker build -t "${IMAGE_NAME}:${IMAGE_TAG}" ./app
success "Image built: ${IMAGE_NAME}:${IMAGE_TAG}"

# reset docker env to host
eval "$(minikube docker-env -u)"

# ── Step 5: Deploy MinIO (local S3) ──────────────────────────────────────────
info "Step 5/7 — Deploying MinIO (local S3 storage)..."
kubectl apply -f local/k8s/namespace.yaml
kubectl apply -f local/k8s/minio.yaml
kubectl rollout status deployment/minio -n "$NAMESPACE" --timeout=120s
kubectl delete job/minio-setup -n "$NAMESPACE" --ignore-not-found >/dev/null
kubectl apply -f local/k8s/minio-init-job.yaml
kubectl wait --for=condition=complete job/minio-setup -n "$NAMESPACE" --timeout=120s 2>/dev/null || \
  warn "MinIO init job timed out — bucket may already exist"
success "MinIO ready (S3-compatible local storage)"

# ── Step 6: Deploy application via Helm ──────────────────────────────────────
info "Step 6/7 — Deploying CSV Processor app via Helm..."
helm upgrade --install "$HELM_RELEASE" helm/csv-app \
  -f helm/environments/local-values.yaml \
  --namespace "$NAMESPACE" \
  --create-namespace \
  --wait \
  --timeout 5m

kubectl rollout status deployment/csv-app -n "$NAMESPACE" --timeout=180s
success "Application deployed"

# ── Step 7: Show status and access info ──────────────────────────────────────
info "Step 7/7 — Deployment complete!"
echo ""
kubectl get pods,svc,hpa -n "$NAMESPACE"
echo ""

echo -e "${BOLD}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BOLD}║  ✅  All done! Follow these steps to access the app:        ║${NC}"
echo -e "${BOLD}╠══════════════════════════════════════════════════════════════╣${NC}"
echo -e "${BOLD}║                                                              ║${NC}"
echo -e "${BOLD}║  1. Open a NEW terminal and run:                             ║${NC}"
echo -e "${BOLD}║       minikube tunnel                                        ║${NC}"
echo -e "${BOLD}║     (keep this terminal open)                                ║${NC}"
echo -e "${BOLD}║                                                              ║${NC}"
echo -e "${BOLD}║  2. Open in browser:                                         ║${NC}"
echo -e "${BOLD}║       App:   http://localhost:8080                           ║${NC}"
echo -e "${BOLD}║       MinIO: run → minikube service minio-console -n csv-app ║${NC}"
echo -e "${BOLD}║              login: minioadmin / minioadmin                  ║${NC}"
echo -e "${BOLD}║                                                              ║${NC}"
echo -e "${BOLD}║  3. Upload the sample CSV:                                   ║${NC}"
echo -e "${BOLD}║       tasks/soh-1-.csv  (751 fashion products)               ║${NC}"
echo -e "${BOLD}║                                                              ║${NC}"
echo -e "${BOLD}║  Tear down: bash deploy.sh --clean                          ║${NC}"
echo -e "${BOLD}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""
