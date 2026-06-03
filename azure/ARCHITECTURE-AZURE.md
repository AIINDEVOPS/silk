# Azure DevOps Case Study — Architecture & Documentation

## Architecture Diagram

```
┌────────────────────────────────────────────────────────────────────────────┐
│                         Azure Cloud Infrastructure                          │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │              Virtual Network (10.0.0.0/8)                           │  │
│  │                                                                      │  │
│  │  ┌──────────────────────────────────────────────────────────────┐   │  │
│  │  │          AKS Cluster (devops-aks-cluster)                    │   │  │
│  │  │                                                               │   │  │
│  │  │  ┌─────────────────────────────────────────────────────┐    │   │  │
│  │  │  │  System Node Pool (Standard_D2s_v3, on-demand)      │    │   │  │
│  │  │  │  Subnet: 10.240.0.0/16  │  min:3  max:5            │    │   │  │
│  │  │  │  Only critical system pods                          │    │   │  │
│  │  │  └─────────────────────────────────────────────────────┘    │   │  │
│  │  │                                                               │   │  │
│  │  │  ┌──────────────────────────────────────────────────────┐   │   │  │
│  │  │  │         User Node Pools                               │   │   │  │
│  │  │  │                                                        │   │   │  │
│  │  │  │  [On-Demand Pool]   [Spot Pool]      [GPU Spot Pool] │   │   │  │
│  │  │  │  D4s_v3             D4s_v3 Spot       NC6s_v3 Spot   │   │   │  │
│  │  │  │  min:2 max:10       min:0 max:20      min:0 max:5    │   │   │  │
│  │  │  │  Subnet:10.241.0/16 Subnet:10.242.0/16               │   │   │  │
│  │  │  │                                                        │   │   │  │
│  │  │  │  ◄────── Built-in AKS Cluster Autoscaler ──────────► │   │   │  │
│  │  │  └──────────────────────────────────────────────────────┘   │   │  │
│  │  │                                                               │   │  │
│  │  │  ┌──────────────────────────────────────────────────────┐   │   │  │
│  │  │  │  namespace: csv-app                                   │   │   │  │
│  │  │  │                                                        │   │   │  │
│  │  │  │  ServiceAccount ──► Azure Managed Identity (OIDC)    │   │   │  │
│  │  │  │  (Workload Identity = Azure IRSA equivalent)          │   │   │  │
│  │  │  │                                                        │   │   │  │
│  │  │  │  ┌──────────────────────────────────────────────┐    │   │   │  │
│  │  │  │  │  Pod (2-50 replicas / HPA CPU+MEM)           │    │   │   │  │
│  │  │  │  │                                               │    │   │   │  │
│  │  │  │  │  [init] static-files-init                    │    │   │   │  │
│  │  │  │  │      └──► emptyDir (shared-static)           │    │   │   │  │
│  │  │  │  │                    │                         │    │   │   │  │
│  │  │  │  │  [Nginx :80] ◄─────┘  [Flask :5000]        │    │   │   │  │
│  │  │  │  │  serves /static/      CSV parser + upload   │    │   │   │  │
│  │  │  │  │  proxies / → Flask    → Azure Blob Storage  │    │   │   │  │
│  │  │  │  └──────────────────────────────────────────────┘    │   │   │  │
│  │  │  └──────────────────────────────────────────────────────┘   │   │  │
│  │  └──────────────────────────────────────────────────────────────┘   │  │
│  │                                                                      │  │
│  │  ┌──────────────────────────────────────────────────────────────┐   │  │
│  │  │  Azure Storage Account (devopscsvuploads)                     │   │  │
│  │  │                                                               │   │  │
│  │  │  Container: csv-uploads                                       │   │  │
│  │  │                                                               │   │  │
│  │  │  processed/ ──30d──► Cool ──90d──► Cold ──180d──► Archive   │   │  │
│  │  │                                            ──730d──► DELETE  │   │  │
│  │  │                                                               │   │  │
│  │  │  ● Versioning enabled (30-day soft delete)                   │   │  │
│  │  │  ● GRS replication (geo-redundant)                           │   │  │
│  │  │  ● Private endpoint from AKS subnet                         │   │  │
│  │  └──────────────────────────────────────────────────────────────┘   │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  ┌──────────────┐  ┌────────────────────┐  ┌──────────────────────────┐  │
│  │ Azure AD     │  │ Log Analytics      │  │ Azure Load Balancer      │  │
│  │ (RBAC + OIDC)│  │ (AKS monitoring)   │  │ (Service type:LB)        │  │
│  └──────────────┘  └────────────────────┘  └──────────────────────────┘  │
└────────────────────────────────────────────────────────────────────────────┘

Traffic Flow:
  User ──► Azure Load Balancer ──► Nginx:80 ──► Flask:5000 ──► Azure Blob

CI/CD Flow:
  Git Push ──► GitHub Actions ──► Docker Build ──► DockerHub
            ──► Terraform Apply (AKS + Storage)
            ──► az aks get-credentials ──► Helm Deploy ──► AKS
```

---

## AWS vs Azure Service Mapping

| Component | AWS (kops) | Azure (AKS) |
|-----------|-----------|-------------|
| **Kubernetes** | kops (self-managed) | AKS (managed) |
| **Control Plane** | 3x EC2 masters (m5.large) | AKS managed (Microsoft runs it) |
| **On-Demand Nodes** | nodes-ondemand IG (m5.xl) | `ondemand` node pool (D4s_v3) |
| **Spot Nodes** | nodes-spot IG (mixed) | `spot` node pool (Spot priority) |
| **GPU Nodes** | nodes-gpu-spot (p3/p2) | `gpuspot` node pool (NC6s_v3) |
| **Cluster Autoscaler** | Separate CA deployment | Built into AKS (native) |
| **Node IAM** | kops IAM role + kube2iam | Workload Identity + Managed Identity |
| **Object Storage** | S3 bucket | Azure Blob Storage (StorageV2) |
| **Cold Storage** | S3 Standard-IA | Azure Blob Cool tier |
| **Archive Storage** | S3 Glacier / Deep Archive | Azure Blob Archive tier |
| **Lifecycle Policy** | S3 lifecycle rules | Azure Storage Management Policy |
| **IAM / Auth** | IAM Roles + IRSA | Managed Identity + Workload Identity |
| **Load Balancer** | AWS NLB | Azure Standard Load Balancer |
| **CNI** | Calico | Azure CNI + Calico network policy |
| **Secrets** | AWS Secrets Manager | Azure Key Vault |
| **Monitoring** | CloudWatch | Azure Monitor + Log Analytics |
| **Container Registry** | ECR / DockerHub | ACR / DockerHub |

---

## Azure Blob Storage Lifecycle vs AWS S3 Glacier

```
AWS S3:                              Azure Blob:
─────────────────────────            ─────────────────────────
Standard     (day 0)     ◄──────►   Hot         (day 0)
Standard-IA  (day 30)    ◄──────►   Cool        (day 30)
Glacier IR   (day 90)    ◄──────►   Cold        (day 90)
Glacier      (day 180)   ◄──────►   Archive     (day 180)
Deep Archive (day 365)   ◄──────►   Archive     (already deepest)
DELETE       (day 2555)  ◄──────►   DELETE      (day 730)
```

**Azure Archive rehydration** (equiv to Glacier restore):
- Standard priority: 1-15 hours
- High priority: < 1 hour
- `az storage blob set-tier --tier Hot` to rehydrate

---

## AKS Node Pool Summary

| Pool | VM Size | Azure Equiv | Min | Max | Priority | Taint |
|------|---------|-------------|-----|-----|----------|-------|
| system | Standard_D2s_v3 | t3.medium | 3 | 5 | On-Demand | system-only |
| ondemand | Standard_D4s_v3 | m5.xlarge | 2 | 10 | On-Demand | none |
| spot | Standard_D4s_v3 | m5.xlarge | 0 | 20 | Spot | PreferNoSchedule |
| gpuspot | Standard_NC6s_v3 | p3.2xlarge | 0 | 5 | Spot | NoSchedule |

---

## Workload Identity Flow (Azure IRSA equivalent)

```
Pod (csv-app)
  │
  ├── ServiceAccount: csv-app-sa
  │     annotation: azure.workload.identity/client-id: <MANAGED_IDENTITY_CLIENT_ID>
  │
  ├── AKS OIDC Issuer: https://oidc.prod.eastus.aksapp.io/<cluster-id>
  │
  └── Azure AD Federated Credential
        Issuer:  AKS OIDC URL
        Subject: system:serviceaccount:csv-app:csv-app-sa
        ──► Issues token for Managed Identity
              ──► RBAC: Storage Blob Data Contributor
                    ──► Azure Blob Storage access (no keys/secrets needed)
```

---

## Key Differences from AWS Implementation

1. **No CA deployment** — AKS Cluster Autoscaler is managed by Azure. Configure via `auto_scaler_profile` in Terraform or `az aks update`.

2. **Spot VMs vs AWS Spot** — Azure uses `priority = "Spot"` with `eviction_policy = "Delete"`. Taint is `kubernetes.azure.com/scalesetpriority=spot`.

3. **Workload Identity** — Replaces AWS IRSA. Uses OIDC federation between AKS and Azure AD. No long-lived credentials in pods.

4. **Azure CNI** — Pods get IPs from the VNet subnet directly (not an overlay). Enables native Azure NSG integration.

5. **Storage lifecycle** — Uses `azurerm_storage_management_policy` instead of `aws_s3_bucket_lifecycle_configuration`. Same concepts, different tier names.

6. **Load Balancer** — Azure LB is provisioned automatically when `service.type = LoadBalancer`. Annotations control health probe path and timeouts.

---

## Quick Start

```bash
# 1. Provision AKS cluster + Azure Blob Storage
cd azure/terraform
terraform init
terraform plan -out=tfplan
terraform apply tfplan

# 2. Get AKS credentials
az aks get-credentials \
  --resource-group devops-case-study-rg \
  --name devops-aks-cluster

# 3. Install Workload Identity webhook
helm repo add azure-workload-identity https://azure.github.io/azure-workload-identity/charts
helm install workload-identity-webhook \
  azure-workload-identity/workload-identity-webhook \
  --namespace azure-workload-identity-system --create-namespace

# 4. Deploy application with Helm
helm upgrade --install csv-app helm/csv-app \
  -f azure/helm/environments/azure-prod-values.yaml \
  --namespace csv-app --create-namespace

# 5. Verify
kubectl get pods,svc,hpa -n csv-app
az storage blob list \
  --account-name devopscsvuploads \
  --container-name csv-uploads \
  --prefix processed/
```

---

## Repository Structure (azure/)

```
azure/
├── terraform/
│   ├── providers.tf          # AzureRM + AzureAD providers, backend config
│   ├── main.tf               # AKS cluster: system + ondemand + spot + GPU pools
│   ├── storage.tf            # Azure Blob Storage + lifecycle policy (Glacier equiv)
│   ├── variables.tf
│   └── outputs.tf
│
├── k8s/
│   ├── deployment.yaml       # Pod: nginx sidecar + flask, emptyDir, Workload Identity SA
│   ├── service-hpa.yaml      # Azure LB service + HPA + PDB
│   └── cluster-autoscaler-notes.yaml  # AKS built-in CA config + KEDA option
│
├── helm/
│   └── environments/
│       ├── azure-dev-values.yaml   # Dev overrides (Azure-specific env vars)
│       └── azure-prod-values.yaml  # Prod overrides (Azure-specific)
│
├── app/
│   ├── app.py                # Flask + azure-storage-blob SDK (replaces boto3)
│   ├── Dockerfile
│   ├── requirements.txt      # azure-storage-blob + azure-identity
│   ├── templates/
│   │   ├── index.html        # Azure-branded UI
│   │   └── result.html
│   └── static/
│       ├── css/main.css      # Azure blue theme
│       └── js/main.js
│
├── ansible/
│   ├── site.yaml
│   ├── inventory/
│   │   ├── azure-hosts.ini   # Static inventory
│   │   └── azure_rm.yaml     # Dynamic Azure RM inventory plugin
│   ├── group_vars/azure.yaml # Azure-specific vars
│   └── roles/
│       ├── app-config/       # App env (AZURE_STORAGE_ACCOUNT instead of S3)
│       └── nginx-config/     # Same Nginx, azure user
│
└── .github/workflows/
    └── ci-cd-azure.yaml      # GitHub Actions: Azure Login (OIDC) + AKS deploy
```
