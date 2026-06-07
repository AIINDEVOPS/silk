# DevOps Case Study — CSV File Processor

A complete DevOps implementation covering Kubernetes cluster configuration,
containerised application deployment, autoscaling, configuration management,
Helm packaging, and S3 Glacier storage — deployed locally on Minikube.

**Docker image:** `deepak415/csv-processor:latest` (DockerHub)  
**Sample CSV:** `tasks/soh-1-.csv` (751 fashion products)

---

## Assignment Tasks

The assignment has two distinct parts:

| Task | Description | Location |
|------|-------------|----------|
| **Task 1 — K8s Cluster Config** | kops cluster config: multiple IGs, mixed spot+on-demand, Cluster Autoscaler | `k8s-kops/` |
| **Task 2 — Application on Minikube** | Nginx+Flask pod, Service, HPA, Ansible, Helm, S3 Glacier | Everything else |

> **Note:** Task 1 is a cluster *configuration* deliverable — a running cluster is not expected.
> Task 2 runs fully on local Minikube.

---

## Quick Start — One Command

```bash
git clone https://github.com/AIINDEVOPS/silk.git
cd silk
bash deploy.sh
```

Then in a **separate terminal**:
```bash
minikube tunnel
```

Open `http://localhost:8080` — upload `tasks/soh-1-.csv` to see 751 rows processed.

To tear down:
```bash
bash deploy.sh --clean
```

---

## Task 1 — Kubernetes Cluster Config (kops)

> *"We are asking you to create Kubernetes cluster creation config for kops which has
> multiple ig, mixed instance group and lifecycle (spot and ondemand). Have cluster
> autoscaler for all instance groups."*

**Location:** `k8s-kops/`

### Instance Groups

| Instance Group | Role | Instance Types | Min | Max | Lifecycle |
|---|---|---|---|---|---|
| master-us-east-1a/b/c | Control Plane | m5.large | 1 | 1 | On-Demand (fixed — etcd quorum) |
| nodes-ondemand | Workers | m5/m5a/m5n/m4.xlarge | 2 | 10 | On-Demand |
| nodes-spot | Workers | m5/m4/r5/c5.xlarge | 0 | 20 | Spot |
| nodes-gpu-spot | Workers | p3.2xl, p2.xl, g4dn.xl | 0 | 5 | Spot |

### Cluster Autoscaler
- `k8s-kops/cluster-autoscaler.yaml` — deployed as a pod inside the cluster
- Auto-discovers worker IGs via ASG tags
- Expander: `least-waste` — picks the IG that wastes fewest resources
- **Masters have NO CA tags** — scaling masters would break etcd quorum

### Files
```
k8s-kops/
├── cluster.yaml              # Cluster spec: VPC 172.20.0.0/16, Calico CNI
├── instancegroups.yaml       # 3 master IGs + 3 worker IGs (spot + on-demand + GPU)
├── cluster-autoscaler.yaml   # Cluster Autoscaler deployment
├── deployment.yaml           # App deployment (nginx+flask sidecar)
└── service-hpa.yaml          # LoadBalancer service + HPA + PDB
```

---

## Task 2 — Application on Minikube

### What it does

Upload a CSV file → Flask parses every row → file stored in MinIO (local S3) →
all rows displayed in browser → previously processed files listed on homepage.

### Architecture

```
                    ┌─────────────────────────────────────────┐
                    │  Minikube Cluster  (namespace: csv-app)  │
                    │                                          │
  Browser           │  ┌──────────────────────────────────┐   │
  localhost:8080 ──►│  │  Pod  (2–5 replicas via HPA)     │   │
                    │  │                                  │   │
                    │  │  [Init Container]                │   │
                    │  │   copies static files            │   │
                    │  │   → emptyDir volume              │   │
                    │  │                                  │   │
                    │  │  [Nginx :80] ◄── emptyDir        │   │
                    │  │   proxy_pass → 127.0.0.1:5000    │   │
                    │  │                                  │   │
                    │  │  [Flask :5000]                   │   │
                    │  │   parse CSV → upload MinIO       │   │
                    │  └──────────────────────────────────┘   │
                    │                                          │
                    │  ┌─────────────────────────────────┐    │
                    │  │  MinIO  (S3-compatible storage)  │    │
                    │  │  csv-uploads/processed/YYYY/MM/  │    │
                    │  └─────────────────────────────────┘    │
                    └─────────────────────────────────────────┘
```

### 2.1 Nginx + Flask in the Same Pod (emptyDir, not NFS)

> *"Create deployment which contains Nginx and below web application running
> (within same pod) and sharing public files (css, js etc) through shared storage (not nfs)."*

The pod uses the **init container pattern**:
1. Init container copies `/app/static/*` → `emptyDir` volume at pod start
2. Nginx reads CSS/JS from the `emptyDir` (in-memory, same node — no NFS)
3. Flask handles all dynamic requests (CSV upload, processing, history)

```
Pod
├── Init Container     copies /app/static/* → emptyDir (once at start)
├── Nginx :80          serves /static/ from emptyDir, proxies / → Flask
└── Flask :5000        CSV parse + MinIO upload + metadata
```

### 2.2 Service Object

> *"Expose application with creating service object."*

- Type: `LoadBalancer`
- Local: `minikube tunnel` maps it to `127.0.0.1:8080`
- Production (kops): AWS Network Load Balancer on port 80

### 2.3 HPA Autoscaling

> *"Implement auto scaling for deployment."*

```yaml
minReplicas: 2
maxReplicas: 5
metrics:
  - CPU:    target 70%
  - Memory: target 85%
scaleUp:   stabilizationWindowSeconds: 60
scaleDown: stabilizationWindowSeconds: 300
```

### 2.4 Ansible Configuration Management

> *"Implementing/using basic configuration management with Ansible
> (to have application configs in Ansible)"*

`ansible/site.yaml` uses `kubernetes.core` — no SSH, pure K8s API:
- Creates `ConfigMap` (APP_NAME, STORAGE_BACKEND, AWS_REGION, S3_BUCKET)
- Creates `Secret` (S3_BUCKET, SECRET_KEY)
- Patches Deployment to reference both
- Verifies rollout and checks `/health` endpoint

```bash
ansible-galaxy collection install -r ansible/requirements.yml
ansible-playbook ansible/site.yaml -i ansible/inventory/k8s.yaml
```

### 2.5 Helm — Multi-Environment Reuse

> *"Use helm to render Kubernetes objects for re-using while creating new environments"*

```
helm/
├── csv-app/           Single reusable chart
└── environments/
    ├── local-values.yaml   Minikube: LoadBalancer :8080, MinIO, 256Mi
    ├── dev-values.yaml     Dev cluster: NodePort, AWS S3, 1 replica
    └── prod-values.yaml    Prod: LoadBalancer :80, AWS S3, 4 replicas
```

Deploy to any environment:
```bash
helm upgrade --install csv-app helm/csv-app -f helm/environments/local-values.yaml -n csv-app --create-namespace
helm upgrade --install csv-app helm/csv-app -f helm/environments/prod-values.yaml  -n csv-app --create-namespace
```

### 2.6 CSV Web Application

> *"Develop a basic web application (using Python) to parse and process CSV files.
> Web application should have basic interface to upload CSV and show previously processed files.
> Once CSV file processed upload it to the s3 storage."*

- `app/app.py` — Flask application
- Upload form with drag-drop (`templates/index.html`)
- Processes every row and renders full table in browser (`templates/result.html`)
- Uploaded to MinIO/S3 at `processed/YYYY/MM/DD/<timestamp>_<filename>.csv`
- Previously processed files shown on homepage (reads `metadata.json`)

### 2.7 S3 Glacier Transition

> *"Waiting you to implement s3 glacier transition on s3 config."*

Implemented in `terraform-s3/main.tf`:

```
Day 0    → STANDARD         upload (full performance)
Day 30   → STANDARD_IA      40% cheaper
Day 90   → GLACIER_IR       68% cheaper, millisecond retrieval
Day 180  → GLACIER          80% cheaper, 3-5 hour retrieval
Day 365  → DEEP_ARCHIVE     95% cheaper, 12 hour retrieval
Day 2555 → DELETE           7-year compliance window
```

```bash
cd terraform-s3
terraform init
terraform plan
terraform apply
```

---

## Step-by-Step Manual Deploy

### Prerequisites
```bash
# macOS
brew install minikube kubectl helm
brew install --cask docker    # Docker Desktop — start it first
```

### Step 1 — Start Minikube
```bash
minikube start --driver=docker --cpus=4 --memory=8192
minikube addons enable metrics-server
```

### Step 2 — Build image inside Minikube
```bash
eval $(minikube docker-env)
docker build -t csv-processor:local ./app
```

### Step 3 — Deploy MinIO (local S3)
```bash
kubectl apply -f local/k8s/namespace.yaml
kubectl apply -f local/k8s/minio.yaml
kubectl rollout status deployment/minio -n csv-app --timeout=120s
kubectl apply -f local/k8s/minio-init-job.yaml
kubectl wait --for=condition=complete job/minio-setup -n csv-app --timeout=120s
```

### Step 4 — Deploy application via Helm
```bash
helm upgrade --install csv-app helm/csv-app \
  -f helm/environments/local-values.yaml \
  --namespace csv-app --create-namespace --wait
```

### Step 5 — Start tunnel (separate terminal, keep open)
```bash
minikube tunnel
```

### Step 6 — Open app
```bash
open http://localhost:8080
# MinIO console:
minikube service minio-console -n csv-app
# login: minioadmin / minioadmin
```

### Step 7 — Verify
```bash
kubectl get pods,svc,hpa -n csv-app
# pod/csv-app-xxx   2/2  Running   ← 2 containers: Nginx + Flask
# LoadBalancer      127.0.0.1:8080
# HPA               cpu:2%/70%  memory:59%/85%
```

---

## Screenshots

### Upload form
![Upload form](screenshots/CSV_File_Processor_1.png)

### File selected — ready to process
![File selected](screenshots/CSV_File_Processor_2.png)

### 751 rows processed and displayed
![CSV result](screenshots/CSV_File_Processor_3.png)

### kubectl — pods, services, HPA
![kubectl output](screenshots/pods-svc-hpa-status-kubectl.png)

### MinIO console — processed files
![MinIO bucket](screenshots/Minio_Storage_2.png)

### MinIO — CSV files stored by date
![MinIO files](screenshots/Minio_Storage_3.png)

### Minikube dashboard
![Dashboard](screenshots/minikube-dashboard-status.png)

---

## Repository Structure

```
.
├── deploy.sh                     One-command deploy script
├── Makefile                      All individual commands
│
├── app/                          Web application
│   ├── app.py                    Flask: CSV parse, S3/MinIO upload, metadata
│   ├── Dockerfile                python:3.12-slim, non-root (uid 1001)
│   ├── nginx.conf                Reverse proxy + static files (emptyDir)
│   ├── requirements.txt
│   ├── templates/
│   │   ├── index.html            Upload form + previously processed files
│   │   └── result.html           Full CSV table display
│   └── static/css/ + js/
│
├── k8s-kops/                     Task 1 — kops cluster configuration
│   ├── cluster.yaml
│   ├── instancegroups.yaml       3 masters + 3 worker IGs
│   ├── cluster-autoscaler.yaml
│   ├── deployment.yaml
│   └── service-hpa.yaml
│
├── helm/                         Task 2 — Helm packaging
│   ├── csv-app/                  Reusable chart
│   └── environments/             local / dev / prod values
│
├── ansible/                      Task 2 — Config management
│   ├── site.yaml
│   ├── requirements.yml
│   ├── inventory/k8s.yaml
│   └── group_vars/all.yaml
│
├── terraform-s3/                 Task 2 — S3 + Glacier lifecycle
│   ├── main.tf                   Bucket + Glacier transition rules + IAM
│   ├── variables.tf
│   └── outputs.tf
│
├── local/                        Local Minikube helpers
│   ├── k8s/                      namespace, minio, minio-init-job manifests
│   ├── ansible/                  Local Ansible playbook
│   └── scripts/smoke-test.sh
│
├── screenshots/                  All captured screenshots
├── docker-compose.yml            Quick local start (no Minikube)
├── ARCHITECTURE.md               Full architecture diagram + details
├── LOCAL-TESTING-GUIDE.md        Detailed Minikube walkthrough
└── DevOps-CaseStudy-Submission.docx  Word document submission
```

---

## Technology Stack

| Layer | Technology |
|-------|-----------|
| Web framework | Python 3.12 + Flask |
| Web server | Nginx 1.25-alpine (sidecar) |
| WSGI server | Gunicorn |
| Container | Docker — `deepak415/csv-processor:latest` |
| Orchestration | Kubernetes via kops (config) / Minikube (local) |
| Node autoscaling | Cluster Autoscaler (kops workers) |
| Pod autoscaling | HPA v2 (CPU + Memory) |
| Helm | Multi-environment K8s packaging |
| Config management | Ansible + kubernetes.core |
| Infrastructure as Code | Terraform (S3 + Glacier lifecycle) |
| Local object storage | MinIO (S3-compatible) |
| Cloud object storage | AWS S3 with Glacier transitions |
| Image registry | DockerHub (`deepak415/csv-processor`) |
| Local cluster | Minikube (docker driver) |
