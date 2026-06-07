# DevOps Case Study — Project Context for Claude UI

Paste this entire file as your first message in Claude.ai to give full context.
Then tell Claude what you want to improve in the documentation.

---

## What this project is

A complete DevOps Case Study assignment submission for company **Silk**.
A Python/Flask web app that uploads and processes CSV files (751 rows of fashion products),
deployed on Kubernetes with full DevOps tooling.

**GitHub repo:** github.com/AIINDEVOPS/silk  
**Branch:** claude/quirky-allen-p1WDz  
**DockerHub image:** deepak415/csv-processor:latest  
**Live local URL:** http://localhost:8080 (Minikube + minikube tunnel)

---

## What has been built (complete list)

### Application
- **Flask app** (`app/app.py`): CSV upload → parse → upload to MinIO/S3 → display 751 rows in browser
- **Nginx sidecar** (same pod, port 80): reverse proxy to Flask :5000, serves static files from emptyDir
- **Init container**: copies static files (CSS/JS) from app image → emptyDir volume at pod start
- **Docker image**: `deepak415/csv-processor:latest` and `:v1.0.0` pushed to DockerHub
- **Storage backends**: MinIO (local), AWS S3 (prod), filesystem (docker-compose)

### Kubernetes (kops on AWS)
- **3 master nodes** (m5.large, one per AZ) — fixed size, NO Cluster Autoscaler tags (protects etcd quorum)
- **3 worker Instance Groups**: on-demand (m5.xlarge, min:2 max:10), spot (m5/m4/r5/c5, min:0 max:20), GPU spot (p3/p2/g4dn, min:0 max:5)
- **Cluster Autoscaler**: least-waste expander, workers only
- **HPA**: CPU >70% or Memory >85% → scale 2–5 replicas, stabilise 60s↑ 300s↓
- **PodDisruptionBudget**: minAvailable: 1
- **Service**: LoadBalancer (127.0.0.1:8080 local via minikube tunnel, AWS NLB prod)

### Helm
- Single chart `helm/csv-app/` with 3 environment value files: local, dev, prod
- Key fix: `spec.replicas` conditionally omitted when HPA enabled (prevents SSA conflict)

### Ansible
- `ansible/site.yaml` uses `kubernetes.core` collection (no SSH — pure K8s API)
- Creates ConfigMap (APP_NAME, STORAGE_BACKEND, AWS_REGION, S3_BUCKET, S3_PREFIX)
- Creates Secret (S3_BUCKET, SECRET_KEY)
- Patches Deployment, waits for rollout, checks Flask /health endpoint

### Terraform (S3 + Glacier lifecycle)
- Bucket: devops-csv-uploads — private, AES-256, versioning enabled
- Lifecycle: Day 0 STANDARD → Day 30 STANDARD_IA → Day 90 GLACIER_IR → Day 180 GLACIER → Day 365 DEEP_ARCHIVE → Day 2555 DELETE

---

## Documentation already created

### Files in repo
- `README.md` — GitHub front page: requirements table, Mermaid architecture diagram, quick-start, 8 screenshots, component breakdown, tech stack
- `ARCHITECTURE.md` — deep-dive: system Mermaid diagram, ASCII pod diagram, kops table, S3 lifecycle, repo structure
- `LOCAL-TESTING-GUIDE.md` — step-by-step Minikube guide with embedded screenshots
- `DevOps-CaseStudy-Submission.docx` — 5MB Word document (14 sections, all screenshots embedded)
- `screenshots/architecture-diagram.png` — matplotlib-generated full-colour system diagram

### Screenshots in `screenshots/` folder
| File | Shows |
|------|-------|
| CSV_File_Processor_1.png | Upload form empty state at localhost:8080 |
| CSV_File_Processor_2.png | soh-1-.csv selected, ready to upload |
| CSV_File_Processor_3.png | Result: 751 rows parsed, MinIO path shown |
| pods-svc-hpa-status-kubectl.png | kubectl get pods,svc,hpa — 2/2 Running, LoadBalancer, HPA cpu:2%/70% mem:59%/85% |
| Minio_Storage_1.png | MinIO login page |
| Minio_Storage_2.png | csv-uploads bucket with processed/ folder |
| Minio_Storage_3.png | processed/2026/06/06/ with 4 uploaded CSVs |
| minikube-dashboard-status.png | K8s dashboard: 2 deployments, 3 pods, 4 replica sets, 1 job |
| architecture-diagram.png | Full system architecture diagram (generated) |

---

## Word document structure (DevOps-CaseStudy-Submission.docx)

1. Cover page
2. Table of Contents
3. Assignment Requirements Overview (checklist table)
4. System Architecture Diagram (embedded PNG)
5. Kubernetes Cluster — kops (masters table, CA, spot strategy, networking)
6. Application — Nginx + Flask Sidecar Pod (pod diagram, Flask flow, storage backends)
7. Helm Multi-Environment Packaging (chart structure, replicas/HPA fix)
8. HPA Autoscaling (config YAML, memory math, live output)
9. Ansible Configuration Management (full playbook excerpt)
10. S3 Storage + Glacier Lifecycle — Terraform (lifecycle table, resources)
11. Local Development — Minikube Step-by-Step (10 steps with commands)
12. Application Screenshots (Figures 2–9, all 8 screenshots embedded)
13. Repository Structure (full tree)
14. Technology Stack Summary (table)

---

## Key technical decisions made

- **emptyDir not NFS**: init container copies static files; Nginx reads from emptyDir
- **minikube tunnel not NodePort**: LoadBalancer gives stable 127.0.0.1:8080 on Mac
- **HPA memory request 256Mi**: actual idle ~195Mi → 76% utilisation, stays below 85% threshold
- **Masters no CA tags**: prevents Cluster Autoscaler from removing masters and breaking etcd
- **spec.replicas gated on HPA**: prevents Helm SSA conflict with kube-controller-manager
- **nginx upstream 127.0.0.1:5000 not localhost**: avoids IPv6 resolution issue in same-pod proxy

---

## What needs improvement in the Word document

[The user will fill this in — this is the section to focus on]

Common areas to improve:
- Introduction / executive summary section
- More detailed explanation of each component
- Better formatting of code blocks
- Adding more context around screenshots
- Adding a troubleshooting section
- Adding a "lessons learned" or "design decisions" section
- Adding a conclusion
- Improving the architecture diagram description

---

## How to ask Claude UI for documentation help

Use prompts like:

**For rewriting a section:**
"Rewrite Section 6 (HPA Autoscaling) for a technical reviewer at a DevOps company. 
Make it more detailed, explain WHY each threshold was chosen, and add a comparison 
of what happened before vs after the fix."

**For adding a new section:**
"Add an 'Executive Summary' section (half a page) before the table of contents. 
It should summarise the entire project in business terms — what problem it solves, 
what technologies were used, and what was achieved."

**For improving screenshot captions:**
"For each screenshot in Section 12, write a 3-sentence caption that explains: 
(1) what the screenshot shows, (2) which assignment requirement it satisfies, 
(3) one technical detail visible in the screenshot."

**For a conclusion section:**
"Write a 'Conclusion' section for the Word document. Cover: what was implemented, 
what the most challenging parts were, what would be done differently in a real 
production environment, and what monitoring/observability would be added."
