# Local Mac + Minikube — End-to-End Testing Guide

This guide walks through every step to run the complete DevOps Case Study solution
on your local Mac using Minikube.

---

## Architecture (Local)

```
┌─────────────────────────────── Mac (Minikube) ────────────────────────────┐
│                                                                             │
│  ┌──────────────────────────── Minikube Cluster ─────────────────────┐   │
│  │  namespace: csv-app                                                │   │
│  │                                                                    │   │
│  │  ┌─────────────────────────────────────────────────────────────┐  │   │
│  │  │  Pod: csv-app (2 replicas / HPA min:2 max:5)                │  │   │
│  │  │                                                              │  │   │
│  │  │  [Init] static-files-init                                   │  │   │
│  │  │    └─ copies /app/static → emptyDir (shared-static)         │  │   │
│  │  │                                                              │  │   │
│  │  │  [nginx:80] ◄── emptyDir ──► [flask:5000]                  │  │   │
│  │  │  serves /static/           parses CSV                       │  │   │
│  │  │  proxies / → flask         uploads → MinIO                  │  │   │
│  │  └─────────────────────────────────────────────────────────────┘  │   │
│  │                                                                    │   │
│  │  ┌─────────────────────────────────────────────────────────────┐  │   │
│  │  │  Pod: minio  (S3-compatible local storage)                  │  │   │
│  │  │  API:     ClusterIP minio:9000  (used by flask internally)  │  │   │
│  │  │  Console: NodePort :30901  (open in browser)               │  │   │
│  │  └─────────────────────────────────────────────────────────────┘  │   │
│  │                                                                    │   │
│  │  Services:                                                         │   │
│  │  csv-app-service  NodePort :30080  → browser access              │   │
│  │  minio-console    NodePort :30901  → MinIO web UI                │   │
│  │                                                                    │   │
│  │  HPA: cpu>70% or mem>80% → scale pods (2→5)                      │   │
│  │  metrics-server addon: required for HPA                           │   │
│  └────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  minikube tunnel / NodePort → http://$(minikube ip):30080                │
└─────────────────────────────────────────────────────────────────────────────┘

CSV Upload Flow:
  Browser → Nginx:80 → Flask:5000 → parse CSV → MinIO:9000/csv-uploads/processed/
                                               → metadata.json
```

---

## Prerequisites

### 1. Install Tools

```bash
# Option A: Use Makefile (recommended)
make setup

# Option B: Manual
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
brew install minikube kubectl helm ansible docker
brew install --cask docker
pip3 install ansible boto3 botocore

# Verify
minikube version      # >= 1.32
kubectl version --client  # >= 1.29
helm version          # >= 3.14
ansible --version     # >= 2.16
docker --version      # >= 25
```

### 2. Start Docker Desktop

Open Docker Desktop and wait until it shows "Running" before proceeding.

---

## Quick Start (One Command)

```bash
git clone https://github.com/YOUR_USERNAME/devops-case-study.git
cd devops-case-study

make dev
```

This runs: `minikube-start → build → deploy-helm → ansible-validate`

Then:
```bash
make open        # Opens app in browser
make open-minio  # Opens MinIO console
```

---

## Step-by-Step Manual Guide

### Step 1 — Start Minikube

```bash
make minikube-start

# Or manually with extra options:
minikube start \
  --driver=docker \
  --cpus=4 \
  --memory=8192 \
  --kubernetes-version=stable \
  --addons=metrics-server,dashboard,ingress

# Verify cluster
kubectl get nodes
# NAME       STATUS   ROLES           AGE   VERSION
# minikube   Ready    control-plane   30s   v1.29.x

# Verify metrics-server (required for HPA)
kubectl get deployment metrics-server -n kube-system
```

### Step 2 — Build Docker Image (inside Minikube)

```bash
# IMPORTANT: Point Docker CLI to Minikube's Docker daemon
# This builds the image directly into Minikube – no registry needed
eval $(minikube docker-env)

docker build -t csv-processor:local ./app

# Verify image is available in Minikube
docker images | grep csv-processor
# csv-processor   local   abc123   30s   180MB

# Or use Makefile:
make build
```

### Step 3 — Deploy MinIO (local S3)

```bash
# Apply namespace + MinIO deployment
kubectl apply -f local/k8s/namespace.yaml
kubectl apply -f local/k8s/minio.yaml

# Wait for MinIO
kubectl rollout status deployment/minio -n csv-app --timeout=120s

# Create the csv-uploads bucket
kubectl apply -f local/k8s/minio-init-job.yaml
kubectl wait --for=condition=complete job/minio-setup -n csv-app --timeout=120s

# Verify bucket
kubectl exec -n csv-app deployment/minio \
  -- mc alias set local http://localhost:9000 minioadmin minioadmin && \
  kubectl exec -n csv-app deployment/minio \
  -- mc ls local/
# [2024-01-01]     0B csv-uploads/

# Or use Makefile:
make deploy-minio
```

### Step 4 — Deploy Application

#### Option A: Raw Kubernetes Manifests

```bash
kubectl apply -f local/k8s/deployment.yaml
kubectl apply -f local/k8s/service-hpa.yaml

kubectl rollout status deployment/csv-app -n csv-app --timeout=180s
# Waiting for deployment "csv-app" rollout to finish: 0 of 2 updated replicas...
# deployment "csv-app" successfully rolled out

# Or:
make deploy-app
```

#### Option B: Helm Chart (recommended – demonstrates multi-environment reuse)

```bash
helm upgrade --install csv-app helm/csv-app \
  -f helm/environments/local-values.yaml \
  --namespace csv-app \
  --create-namespace \
  --wait \
  --timeout 5m

# See what Helm rendered:
helm template csv-app helm/csv-app \
  -f helm/environments/local-values.yaml

# Or:
make deploy-helm
```

### Step 5 — Verify the Deployment

```bash
# See all resources
kubectl get all -n csv-app
# NAME                           READY   STATUS    RESTARTS   AGE
# pod/csv-app-xxx-yyy            2/2     Running   0          60s   ← 2 containers!
# pod/csv-app-xxx-zzz            2/2     Running   0          60s
# pod/minio-xxx-aaa              1/1     Running   0          90s
# NAME                    TYPE       CLUSTER-IP     PORT(S)
# service/csv-app-service NodePort   10.96.x.x      80:30080/TCP
# service/minio           ClusterIP  10.96.x.x      9000/TCP
# service/minio-console   NodePort   10.96.x.x      9001:30901/TCP
# NAME                      READY   UP-TO-DATE   AVAILABLE
# deployment.apps/csv-app   2/2     2            2
# NAME                                   REFERENCE            TARGETS        MINPODS
# horizontalpodautoscaler.autoscaling/   Deployment/csv-app   cpu: 5%/70%    2

# Check pod details (2/2 = Nginx + Flask both running)
kubectl describe pod -l app=csv-app -n csv-app | grep -A5 "Containers:"

# Check init container completed
kubectl get pod -n csv-app -l app=csv-app \
  -o jsonpath='{.items[0].status.initContainerStatuses[0].state}'

# Verify shared static volume (emptyDir)
kubectl exec -n csv-app deployment/csv-app -c nginx \
  -- ls /app/shared-static/css/
# main.css   ← copied from Flask container via init container

# Verify Nginx serves static file
kubectl exec -n csv-app deployment/csv-app -c nginx \
  -- wget -qO- http://localhost/static/css/main.css | head -5

# Verify Flask health
kubectl exec -n csv-app deployment/csv-app -c flask-app \
  -- curl -s http://localhost:5000/health
# {"service":"csv-processor","status":"healthy","storage_backend":"minio","version":"1.0.0"}
```

### Step 6 — Open Application in Browser

```bash
# Method 1: Minikube service (auto-opens browser)
minikube service csv-app-service -n csv-app
# 🎉 Opens http://127.0.0.1:<random-port>

# Method 2: Get URL only
minikube service csv-app-service -n csv-app --url
# http://127.0.0.1:55432

# Method 3: Port forward
kubectl port-forward svc/csv-app-service 8080:80 -n csv-app &
# Then open http://localhost:8080

# Make:
make open
```

### Step 7 — Upload and Process the CSV File

1. Open the app URL in your browser
2. Click **Browse File** or drag the `soh.csv` file onto the drop zone
3. Click **Upload & Process**
4. The page will display all 751 rows from the CSV file in a table
5. The file is uploaded to MinIO automatically

Verify the upload reached MinIO:
```bash
# List objects in MinIO bucket
kubectl exec -n csv-app deployment/minio \
  -- mc alias set local http://localhost:9000 minioadmin minioadmin 2>/dev/null && \
  kubectl exec -n csv-app deployment/minio \
  -- mc ls --recursive local/csv-uploads/processed/
# [2024-01-01]   4.2 KiB processed/2024/01/01/20240101_123456_soh.csv
```

### Step 8 — Open MinIO Console (S3 UI)

```bash
minikube service minio-console -n csv-app
# Opens http://127.0.0.1:<port>
# Username: minioadmin
# Password: minioadmin
```

Navigate to: **Buckets → csv-uploads → processed/** to see uploaded CSVs.

This demonstrates the **S3 Glacier lifecycle** concept – in production the
Terraform S3 lifecycle rules move files:
`Standard → Standard-IA(30d) → Glacier(90d) → Deep Archive(365d)`

### Step 9 — Run Ansible Validation

```bash
cd local/ansible
ansible-playbook site-local.yaml \
  -i inventory/minikube.yaml \
  -e @group_vars/local.yaml \
  -v

# Or:
make ansible-validate
```

The playbook:
- Verifies Minikube status
- Checks all pods are running
- Applies ConfigMap via kubectl (shows Ansible managing K8s config)
- Validates Flask health endpoint
- Verifies Nginx serves static files from emptyDir
- Runs E2E upload test

### Step 10 — Test HPA Autoscaling

```bash
# Watch HPA in real-time (open a new terminal)
watch -n 3 kubectl get hpa,pods -n csv-app

# Generate load (in another terminal)
APP_URL=$(minikube service csv-app-service -n csv-app --url)
kubectl run load-gen \
  --image=busybox \
  --restart=Never \
  -n csv-app \
  -- /bin/sh -c "while true; do wget -q -O- $APP_URL/health >/dev/null; done"

# Watch pods scale from 2 → 5
# NAME           REFERENCE            TARGETS    MINPODS   MAXPODS   REPLICAS
# csv-app-hpa    Deployment/csv-app   78%/70%    2         5         4

# Stop load generator
kubectl delete pod load-gen -n csv-app

# Or:
make hpa-test
make hpa-watch
```

---

## Helm Multi-Environment Demo

```bash
# Show Helm renders different configs per environment
# Local (MinIO, NodePort, 2 replicas):
helm template local helm/csv-app -f helm/environments/local-values.yaml \
  | grep -E "STORAGE_BACKEND|type:|replicas:"

# Dev (S3, NodePort, 1 replica):
helm template dev helm/csv-app -f helm/environments/dev-values.yaml \
  | grep -E "STORAGE_BACKEND|type:|replicas:"

# Prod (S3, LoadBalancer, 4 replicas):
helm template prod helm/csv-app -f helm/environments/prod-values.yaml \
  | grep -E "STORAGE_BACKEND|type:|replicas:"
```

---

## Kubernetes Dashboard

```bash
minikube dashboard
# Auto-opens in browser
# Navigate to: Workloads → Deployments → csv-app
# Shows pods, containers, volumes, HPA
```

---

## Troubleshooting

### Pod not starting (ImagePullBackOff)

```bash
# Cause: imagePullPolicy=Always or image not in Minikube
# Fix: rebuild inside Minikube Docker daemon
eval $(minikube docker-env)
docker build -t csv-processor:local ./app
docker images | grep csv-processor
```

### HPA shows `<unknown>` targets

```bash
# Cause: metrics-server not running
minikube addons enable metrics-server
kubectl rollout restart deployment metrics-server -n kube-system
# Wait ~60s then check again
kubectl get hpa -n csv-app
```

### MinIO upload fails

```bash
# Check MinIO pod logs
kubectl logs deployment/minio -n csv-app

# Check Flask logs for error
kubectl logs deployment/csv-app -c flask-app -n csv-app

# Verify DNS resolves minio service
kubectl exec deployment/csv-app -c flask-app -n csv-app \
  -- nslookup minio
```

### Port-forward stopped working

```bash
# Kill existing port-forwards
pkill -f "kubectl port-forward"
# Re-open
kubectl port-forward svc/csv-app-service 8080:80 -n csv-app &
```

### Static files returning 404

```bash
# Verify init container ran successfully
kubectl get pod -n csv-app -l app=csv-app \
  -o jsonpath='{.items[0].status.initContainerStatuses}'

# Check shared volume has files
kubectl exec deployment/csv-app -c nginx -n csv-app \
  -- ls /app/shared-static/
# css/  js/
```

---

## Full Clean Up

```bash
make clean           # Removes namespace, Helm release
make minikube-delete # Fully removes Minikube VM
```

---

## Submission Checklist

| Item | How to verify |
|------|--------------|
| ✅ Nginx + Flask in same pod | `kubectl get pod -n csv-app` → 2/2 READY |
| ✅ Shared static via emptyDir | `kubectl exec -c nginx -- ls /app/shared-static/` |
| ✅ Service object | `kubectl get svc -n csv-app` |
| ✅ HPA autoscaling | `kubectl get hpa -n csv-app` |
| ✅ Ansible config management | `make ansible-validate` |
| ✅ Helm multi-env rendering | `helm template local/dev/prod helm/csv-app -f ...` |
| ✅ CSV upload + display | Browser → upload soh.csv → see 751 rows |
| ✅ S3/MinIO upload | MinIO console → csv-uploads/processed/ |
| ✅ Glacier lifecycle (Terraform) | `terraform plan terraform-s3/` |
| ✅ Architecture diagram | ARCHITECTURE.md |
| ✅ kops cluster config | k8s-kops/ |
| ✅ Azure AKS config | azure/ |
