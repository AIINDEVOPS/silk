"""
Generates DevOps Case Study Word document (.docx)
Output: DevOps-CaseStudy-Submission.docx
"""
from docx import Document
from docx.shared import Inches, Pt, RGBColor, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
import os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SS   = os.path.join(BASE, 'screenshots')
OUT  = os.path.join(BASE, 'DevOps-CaseStudy-Submission.docx')

doc = Document()

# ── page margins ────────────────────────────────────────────────────────────
for section in doc.sections:
    section.top_margin    = Cm(2.0)
    section.bottom_margin = Cm(2.0)
    section.left_margin   = Cm(2.5)
    section.right_margin  = Cm(2.5)

# ── helpers ─────────────────────────────────────────────────────────────────
def h1(text):
    p = doc.add_heading(text, level=1)
    p.runs[0].font.color.rgb = RGBColor(0x32, 0x6C, 0xE5)
    return p

def h2(text):
    p = doc.add_heading(text, level=2)
    p.runs[0].font.color.rgb = RGBColor(0x1A, 0x1A, 0x2E)
    return p

def h3(text):
    return doc.add_heading(text, level=3)

def para(text='', bold=False, italic=False, size=11, color=None, align=None):
    p = doc.add_paragraph()
    if align:
        p.alignment = align
    run = p.add_run(text)
    run.bold   = bold
    run.italic = italic
    run.font.size = Pt(size)
    if color:
        run.font.color.rgb = RGBColor(*color)
    return p

def bullet(text, level=0):
    p = doc.add_paragraph(text, style='List Bullet')
    p.paragraph_format.left_indent = Cm(0.5 + level * 0.5)
    return p

def numbered(text):
    return doc.add_paragraph(text, style='List Number')

def code_block(text):
    p = doc.add_paragraph()
    p.paragraph_format.left_indent  = Cm(0.5)
    p.paragraph_format.right_indent = Cm(0.5)
    shading = OxmlElement('w:shd')
    shading.set(qn('w:val'),   'clear')
    shading.set(qn('w:color'), 'auto')
    shading.set(qn('w:fill'),  'F3F4F6')
    p._p.get_or_add_pPr().append(shading)
    run = p.add_run(text)
    run.font.name = 'Courier New'
    run.font.size = Pt(8.5)
    run.font.color.rgb = RGBColor(0x1F, 0x29, 0x37)
    return p

def img(path, width=Inches(6.0), caption_text=''):
    if os.path.exists(path):
        doc.add_picture(path, width=width)
        last = doc.paragraphs[-1]
        last.alignment = WD_ALIGN_PARAGRAPH.CENTER
        if caption_text:
            cp = doc.add_paragraph(caption_text)
            cp.alignment = WD_ALIGN_PARAGRAPH.CENTER
            cp.runs[0].font.size   = Pt(9)
            cp.runs[0].italic      = True
            cp.runs[0].font.color.rgb = RGBColor(0x6C, 0x75, 0x7D)
    else:
        para(f'[Screenshot not found: {path}]', italic=True, color=(180,180,180))

def table_2col(rows, col_widths=(Cm(5), Cm(11))):
    t = doc.add_table(rows=len(rows)+1, cols=2)
    t.style = 'Table Grid'
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    hdr = t.rows[0].cells
    for i, h in enumerate(['Item', 'Detail']):
        hdr[i].text = h
        hdr[i].paragraphs[0].runs[0].bold = True
        hdr[i].paragraphs[0].runs[0].font.color.rgb = RGBColor(0xFF,0xFF,0xFF)
        tc = hdr[i]._tc
        tcPr = tc.get_or_add_tcPr()
        shd  = OxmlElement('w:shd')
        shd.set(qn('w:val'),   'clear')
        shd.set(qn('w:color'), 'auto')
        shd.set(qn('w:fill'),  '326CE5')
        tcPr.append(shd)
    for ri, (k, v) in enumerate(rows):
        cells = t.rows[ri+1].cells
        cells[0].text = k
        cells[1].text = v
        cells[0].paragraphs[0].runs[0].bold = True
    return t

def divider():
    doc.add_paragraph('─' * 80).runs[0].font.color.rgb = RGBColor(0xDE,0xE2,0xE6)

def page_break():
    doc.add_page_break()

# ════════════════════════════════════════════════════════════════════════════
# COVER PAGE
# ════════════════════════════════════════════════════════════════════════════
doc.add_paragraph()
doc.add_paragraph()
doc.add_paragraph()

title_p = doc.add_paragraph()
title_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
title_run = title_p.add_run('DevOps Case Study')
title_run.bold = True
title_run.font.size = Pt(28)
title_run.font.color.rgb = RGBColor(0x32, 0x6C, 0xE5)

sub_p = doc.add_paragraph()
sub_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
sub_run = sub_p.add_run('CSV File Processor — End-to-End DevOps Implementation')
sub_run.font.size = Pt(16)
sub_run.font.color.rgb = RGBColor(0x1A, 0x1A, 0x2E)

doc.add_paragraph()

for line, sz in [
    ('Kubernetes (kops) · Helm · Ansible · Terraform · GitHub Actions', 12),
    ('Docker · MinIO · AWS S3 + Glacier · Nginx · Flask · Python', 11),
    ('', 10),
    ('Candidate:  Deepak Inugala', 12),
    ('Image:      deepak415/csv-processor:latest  (DockerHub)', 11),
    ('Repository: github.com/AIINDEVOPS/silk', 11),
    ('Date:       June 2026', 11),
]:
    lp = doc.add_paragraph()
    lp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    lr = lp.add_run(line)
    lr.font.size  = Pt(sz)
    lr.font.color.rgb = RGBColor(0x6C, 0x75, 0x7D)

doc.add_paragraph()
doc.add_paragraph()
doc.add_paragraph()
doc.add_paragraph()

page_break()

# ════════════════════════════════════════════════════════════════════════════
# TABLE OF CONTENTS  (manual)
# ════════════════════════════════════════════════════════════════════════════
h1('Table of Contents')
toc_items = [
    ('1', 'Assignment Requirements Overview'),
    ('2', 'System Architecture Diagram'),
    ('3', 'Kubernetes Cluster — kops (AWS)'),
    ('4', 'Application — Nginx + Flask Sidecar Pod'),
    ('5', 'Helm Multi-Environment Packaging'),
    ('6', 'HPA Autoscaling'),
    ('7', 'Ansible Configuration Management'),
    ('8', 'S3 Storage + Glacier Lifecycle (Terraform)'),
    ('9', 'CI/CD Pipeline (GitHub Actions)'),
    ('10', 'Azure AKS Deployment'),
    ('11', 'Local Development — Minikube Step-by-Step'),
    ('12', 'Application Screenshots'),
    ('13', 'Repository Structure'),
    ('14', 'Technology Stack Summary'),
]
for num, title in toc_items:
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Cm(0.5)
    p.add_run(f'{num}.  ').bold = True
    p.add_run(title).font.size = Pt(11)

page_break()

# ════════════════════════════════════════════════════════════════════════════
# SECTION 1 — REQUIREMENTS OVERVIEW
# ════════════════════════════════════════════════════════════════════════════
h1('1. Assignment Requirements Overview')
para(
    'This document covers the complete implementation of the DevOps Case Study. '
    'Every required component has been implemented, tested locally on Minikube, '
    'and pushed to GitHub. The application processes CSV files (fashion product data), '
    'uploads processed files to object storage, and displays results in a browser.'
)
doc.add_paragraph()

req_rows = [
    ('kops Kubernetes Cluster',      'k8s-kops/ — 3 masters (fixed) + 3 worker IGs (spot + on-demand + GPU)'),
    ('Cluster Autoscaler',           'k8s-kops/cluster-autoscaler.yaml — workers only, least-waste expander'),
    ('Nginx + Flask same pod',       'Init container → emptyDir → Nginx :80 proxies Flask :5000 (no NFS)'),
    ('Service object',               'LoadBalancer — 127.0.0.1:8080 (local) / AWS NLB (prod)'),
    ('HPA autoscaling',              'CPU > 70% or Memory > 85% → 2–5 replicas, stabilised scale-down'),
    ('Ansible config management',    'ansible/site.yaml — kubernetes.core: ConfigMap + Secret + health check'),
    ('Helm multi-environment',       'helm/environments/ — local / dev / prod values files'),
    ('Python CSV app + browser',     'app/app.py — Flask, 751 fashion product rows rendered as HTML table'),
    ('Previously processed files',   'Metadata stored in metadata.json; listed on homepage'),
    ('S3 upload after processing',   'boto3 → MinIO (local) or AWS S3 (prod) at processed/YYYY/MM/DD/'),
    ('S3 Glacier lifecycle',         'terraform-s3/ — 30d→IA, 90d→GLACIER_IR, 365d→DEEP_ARCHIVE, 7yr→DELETE'),
    ('CI/CD pipeline',               '.github/workflows/ci-cd.yaml — test → build → push → helm deploy'),
    ('Docker image on registry',     'deepak415/csv-processor:latest + :v1.0.0 on DockerHub'),
    ('Azure AKS',                    'azure/ — full K8s + Helm + Ansible deployment for AKS'),
]
table_2col(req_rows)
page_break()

# ════════════════════════════════════════════════════════════════════════════
# SECTION 2 — ARCHITECTURE DIAGRAM
# ════════════════════════════════════════════════════════════════════════════
h1('2. System Architecture Diagram')
para(
    'The diagram below shows the complete system topology: CI/CD pipeline, '
    'AWS Kubernetes cluster (kops), multi-container pod (Nginx sidecar + Flask), '
    'S3 Glacier lifecycle, Ansible configuration management, and the local '
    'Minikube development environment with MinIO.'
)
doc.add_paragraph()
img(os.path.join(SS, 'architecture-diagram.png'), width=Inches(6.5),
    caption_text='Figure 1 — Full system architecture: CI/CD → kops cluster → pod → S3 → Glacier')

doc.add_paragraph()
h2('Traffic Flow')
bullet('User browser → LoadBalancer Service :8080 → Nginx :80 → proxy_pass 127.0.0.1:5000 → Flask :5000')
bullet('Flask parses CSV → uploads to S3/MinIO (boto3) → stores metadata.json → renders result table')
bullet('Nginx serves /static/* directly from emptyDir volume (init container pattern — no NFS)')
bullet('HPA monitors CPU and Memory → scales pods from 2 to 5 replicas under load')
bullet('GitHub push → GitHub Actions → build Docker image → push DockerHub → Helm deploy to cluster')

page_break()

# ════════════════════════════════════════════════════════════════════════════
# SECTION 3 — KOPS CLUSTER
# ════════════════════════════════════════════════════════════════════════════
h1('3. Kubernetes Cluster — kops (AWS)')
para(
    'The production cluster runs on AWS (us-east-1) using kops for declarative '
    'cluster management. The cluster spans three Availability Zones with a '
    'high-availability control plane and three worker Instance Groups.'
)

h2('3.1 Control Plane (Masters)')
para(
    'Three master nodes — one per AZ — run the Kubernetes control plane (API server, '
    'etcd, scheduler, controller-manager). Masters are fixed-size (min:1 max:1 per IG) '
    'and intentionally have NO Cluster Autoscaler tags. Scaling masters would risk '
    'breaking etcd quorum and corrupting the cluster state.'
)

ig_rows = [
    ('master-us-east-1a', 'm5.large', '1', '1', 'On-Demand', 'Control plane AZ-a'),
    ('master-us-east-1b', 'm5.large', '1', '1', 'On-Demand', 'Control plane AZ-b'),
    ('master-us-east-1c', 'm5.large', '1', '1', 'On-Demand', 'Control plane AZ-c'),
    ('nodes-ondemand',    'm5/m5a/m5n/m4.xlarge', '2', '10', 'On-Demand', 'Primary workers'),
    ('nodes-spot',        'm5/m4/r5/c5.xlarge', '0', '20', 'Spot ($0.10/hr max)', 'Cost-optimised burst'),
    ('nodes-gpu-spot',    'p3.2xl, p2.xl, g4dn.xl', '0', '5', 'Spot', 'GPU workloads'),
]
t = doc.add_table(rows=len(ig_rows)+1, cols=6)
t.style = 'Table Grid'
for i, h in enumerate(['Instance Group', 'Instance Types', 'Min', 'Max', 'Lifecycle', 'Purpose']):
    t.rows[0].cells[i].text = h
    t.rows[0].cells[i].paragraphs[0].runs[0].bold = True
    tc = t.rows[0].cells[i]._tc
    tcPr = tc.get_or_add_tcPr()
    shd  = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear')
    shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'), '1A1A2E')
    tcPr.append(shd)
    t.rows[0].cells[i].paragraphs[0].runs[0].font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
for ri, row_data in enumerate(ig_rows):
    for ci, val in enumerate(row_data):
        t.rows[ri+1].cells[ci].text = val
        t.rows[ri+1].cells[ci].paragraphs[0].runs[0].font.size = Pt(9)

doc.add_paragraph()

h2('3.2 Cluster Autoscaler')
bullet('Deployment: k8s-kops/cluster-autoscaler.yaml')
bullet('Auto-discovers worker IGs via ASG tags (k8s.io/cluster-autoscaler/enabled)')
bullet('Expander: least-waste — picks the IG that wastes fewest CPU/memory resources')
bullet('Scale-down delay: 10 minutes of node inactivity before removal')
bullet('Masters: NO CA tags — critical for etcd quorum stability')

h2('3.3 Spot Instance Strategy')
bullet('Spot IG: PreferNoSchedule taint — only scheduled if on-demand IG is full')
bullet('Multiple instance families (m5/m4/r5/c5) for better spot pool availability')
bullet('GPU IG: NoSchedule taint — requires explicit toleration on GPU workloads')
bullet('Mixed instance policy with weight-based selection for cost optimisation')

h2('3.4 Network Configuration')
bullet('VPC CIDR: 172.20.0.0/16')
bullet('Pod network CIDR: 100.96.0.0/11 (Calico CNI — supports NetworkPolicy)')
bullet('Service CIDR: 100.64.0.0/13')
bullet('DNS: CoreDNS')

page_break()

# ════════════════════════════════════════════════════════════════════════════
# SECTION 4 — APPLICATION
# ════════════════════════════════════════════════════════════════════════════
h1('4. Application — Nginx + Flask Sidecar Pod')
para(
    'The application runs as a multi-container pod following the sidecar pattern. '
    'Nginx handles inbound traffic and static file serving; Flask handles CSV parsing '
    'and S3 uploads. Both containers share volumes via emptyDir — no NFS required.'
)

h2('4.1 Pod Architecture')
code_block(
'''Pod (2–5 replicas via HPA)
├── Init Container: static-files-init
│   └── Copies /app/static/* → emptyDir "shared-static" (runs ONCE at pod start)
│
├── Container 1: nginx:1.25-alpine  [:80]
│   ├── Listens on port 80
│   ├── proxy_pass http://127.0.0.1:5000  (to Flask)
│   ├── Serves /static/* from emptyDir "shared-static"
│   └── 30-day cache headers on CSS/JS
│
└── Container 2: deepak415/csv-processor:latest  [:5000]
    ├── Flask + Gunicorn (2 workers)
    ├── POST /upload  → parse CSV → upload S3/MinIO → store metadata.json
    └── GET  /        → read metadata.json → render processed files list

Shared Volumes (emptyDir — in-memory, same node, no NFS):
├── shared-static:     CSS/JS files (init→nginx, alias /static/)
├── uploads-storage:   raw CSV uploads (/app/uploads/)
└── processed-storage: metadata.json (/app/processed/)'''
)

h2('4.2 Why emptyDir and not NFS')
para(
    'The init container pattern avoids NFS entirely. At pod startup, the init container '
    'copies static files from the app image into an emptyDir volume mounted at '
    '/app/shared-static. Nginx reads from that emptyDir directly — fast, in-memory, '
    'no external storage dependency. This satisfies the assignment requirement of '
    '"shared volume between Nginx and Flask without NFS".'
)

h2('4.3 Flask CSV Processing Flow')
numbered('User uploads CSV via drag-drop form at http://localhost:8080')
numbered('Flask receives file at POST /upload (werkzeug secure_filename + timestamp prefix)')
numbered('CSV parsed with csv.reader — strips quotes and leading/trailing spaces')
numbered('File uploaded to MinIO/S3 at processed/YYYY/MM/DD/<timestamp>_<filename>.csv')
numbered('Metadata (filename, rows, S3 path, timestamp) stored in metadata.json')
numbered('Result page renders full product table (ID, Name, Price) in browser')
numbered('Homepage GET / reads metadata.json and lists all previously processed files')

h2('4.4 Storage Backends')
bullet('minio: local Minikube (endpoint: http://minio:9000, credentials: minioadmin/minioadmin)')
bullet('s3: AWS S3 (endpoint: default, IAM role or access key credentials)')
bullet('local: filesystem fallback (no object store — for docker-compose dev mode)')
para('Backend selected via STORAGE_BACKEND environment variable in ConfigMap.')

h2('4.5 Docker Image')
bullet('Base: python:3.12-slim')
bullet('Non-root user: appuser (uid 1001) — security best practice')
bullet('Multi-stage: dependencies installed before app code for layer caching')
bullet('Published: deepak415/csv-processor:latest and deepak415/csv-processor:v1.0.0')
code_block('docker pull deepak415/csv-processor:latest')

page_break()

# ════════════════════════════════════════════════════════════════════════════
# SECTION 5 — HELM
# ════════════════════════════════════════════════════════════════════════════
h1('5. Helm Multi-Environment Packaging')
para(
    'A single reusable Helm chart (helm/csv-app) deploys the application to any '
    'environment by layering environment-specific values files on top of the chart defaults.'
)

h2('5.1 Chart Structure')
code_block(
'''helm/
├── csv-app/
│   ├── Chart.yaml
│   ├── values.yaml            # Defaults (image, resources, HPA config)
│   └── templates/
│       ├── deployment.yaml    # replicas gated: only set when HPA disabled
│       ├── service.yaml       # type driven by values
│       ├── hpa.yaml           # autoscaling/v2 — CPU + Memory metrics
│       ├── configmap.yaml     # APP_NAME, STORAGE_BACKEND, AWS_REGION ...
│       ├── pdb.yaml           # PodDisruptionBudget: minAvailable: 1
│       └── namespace.yaml     # Creates csv-app namespace
└── environments/
    ├── local-values.yaml      # Minikube: LoadBalancer :8080, MinIO, 256Mi req
    ├── dev-values.yaml        # Dev cluster: NodePort, AWS S3, 1 replica
    └── prod-values.yaml       # Prod: LoadBalancer :80, AWS S3, 4 replicas'''
)

h2('5.2 Key Design Decision — spec.replicas and HPA')
para(
    'When HPA is enabled, Helm must NOT set spec.replicas in the Deployment. '
    'If Helm manages replicas while HPA also manages them, a Server-Side Apply '
    'conflict occurs with kube-controller-manager (conflict on the "scale" subresource). '
    'The fix is to conditionally omit the field:'
)
code_block(
'''# helm/csv-app/templates/deployment.yaml
spec:
  {{- if not .Values.autoscaling.enabled }}
  replicas: {{ .Values.replicaCount }}
  {{- end }}'''
)

h2('5.3 Deploy Commands')
code_block(
'''# Local (Minikube)
helm upgrade --install csv-app helm/csv-app \\
  -f helm/environments/local-values.yaml \\
  --namespace csv-app --create-namespace --wait

# Production
helm upgrade --install csv-app helm/csv-app \\
  -f helm/environments/prod-values.yaml \\
  --namespace csv-app --create-namespace --wait --timeout 10m

# Validate (dry-run)
helm template csv-app helm/csv-app -f helm/environments/prod-values.yaml --dry-run'''
)

page_break()

# ════════════════════════════════════════════════════════════════════════════
# SECTION 6 — HPA
# ════════════════════════════════════════════════════════════════════════════
h1('6. HPA Autoscaling')
para(
    'The Horizontal Pod Autoscaler scales the csv-app Deployment between 2 and 5 '
    'replicas based on CPU and Memory utilisation. Both metrics are monitored '
    'simultaneously — whichever breaches its threshold first triggers a scale-up.'
)

h2('6.1 HPA Configuration')
code_block(
'''apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
spec:
  scaleTargetRef:
    kind: Deployment
    name: csv-app
  minReplicas: 2
  maxReplicas: 5
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70        # scale up above 70% CPU
    - type: Resource
      resource:
        name: memory
        target:
          type: Utilization
          averageUtilization: 85        # scale up above 85% Memory
  behavior:
    scaleUp:
      stabilizationWindowSeconds: 60   # react quickly to load spikes
    scaleDown:
      stabilizationWindowSeconds: 300  # avoid flapping during cooldown'''
)

h2('6.2 Memory Utilisation Calculation')
para(
    'Kubernetes calculates memory utilisation as: actual usage / memory REQUEST '
    '(not limit). The Flask container request is set to 256Mi. Actual idle usage '
    'is approximately 195Mi, giving ~76% at rest — safely below the 85% threshold. '
    'Previously (128Mi request, 195Mi usage) the HPA was permanently at 101% and '
    'held 5 replicas at idle. Raising the request to 256Mi fixed this.'
)

h2('6.3 Live HPA Output')
code_block(
'''NAME           REFERENCE           TARGETS                     MINPODS  MAXPODS  REPLICAS
csv-app-hpa    Deployment/csv-app  cpu: 2%/70%  memory: 59%/85%  2        5        2'''
)
para('Both metrics well below thresholds at idle → maintained at minimum 2 replicas.')

h2('6.4 Load Test')
code_block(
'''# Generate load (watch HPA in separate terminal: watch kubectl get hpa -n csv-app)
kubectl run load-gen --image=busybox --restart=Never -n csv-app \\
  -- /bin/sh -c "while true; do wget -q -O- http://csv-app-service/health; done"

# Stop
kubectl delete pod load-gen -n csv-app

# Or via Makefile:
make hpa-test'''
)
page_break()

# ════════════════════════════════════════════════════════════════════════════
# SECTION 7 — ANSIBLE
# ════════════════════════════════════════════════════════════════════════════
h1('7. Ansible Configuration Management')
para(
    'Ansible manages application configuration using the kubernetes.core collection. '
    'The playbook runs on localhost and communicates with the cluster via kubeconfig — '
    'no SSH into nodes. This is the modern K8s-native approach to configuration management.'
)

h2('7.1 Playbook Structure')
code_block(
'''# ansible/site.yaml
- name: Manage Kubernetes application configuration
  hosts: localhost
  connection: local
  tasks:
    - name: Apply app ConfigMap (non-sensitive config via Ansible)
      kubernetes.core.k8s:
        state: present
        definition:
          kind: ConfigMap
          data:
            APP_NAME: "{{ app_name }}"
            APP_ENV:  "{{ target_env }}"
            STORAGE_BACKEND: "{{ storage_backend }}"
            AWS_REGION: "{{ aws_region }}"
            S3_BUCKET:  "{{ s3_bucket }}"
            S3_PREFIX:  "{{ s3_prefix }}"

    - name: Apply app Secret (sensitive values — use Vault in prod)
      kubernetes.core.k8s:
        definition:
          kind: Secret
          stringData:
            S3_BUCKET:  "{{ s3_bucket }}"
            SECRET_KEY: "{{ vault_secret_key | default('change-me') }}"

    - name: Patch Deployment to reference Ansible-managed ConfigMap
      kubernetes.core.k8s:
        state: patched
        kind: Deployment
        name: csv-app

- name: Verify application health after config rollout
  hosts: localhost
  tasks:
    - name: Wait for deployment rollout
      kubernetes.core.k8s_rollout_status:
        kind: Deployment
        name: csv-app
        namespace: csv-app
    - name: Check Flask health endpoint
      kubernetes.core.k8s_exec:
        namespace: csv-app
        pod: "{{ pod_name }}"
        command: ["curl", "-s", "http://localhost:5000/health"]'''
)

h2('7.2 Installation and Run')
code_block(
'''# Install required Ansible collections
ansible-galaxy collection install -r ansible/requirements.yml

# Run playbook
export KUBECONFIG=~/.kube/config
ansible-playbook ansible/site.yaml -i ansible/inventory/k8s.yaml -v

# Or via Makefile:
make ansible-validate'''
)

h2('7.3 Collections Required')
bullet('kubernetes.core >= 3.0.0 — K8s API management without kubectl')
bullet('community.general >= 8.0.0 — general utility modules')

page_break()

# ════════════════════════════════════════════════════════════════════════════
# SECTION 8 — TERRAFORM + S3 LIFECYCLE
# ════════════════════════════════════════════════════════════════════════════
h1('8. S3 Storage + Glacier Lifecycle (Terraform)')
para(
    'The Terraform configuration in terraform-s3/ creates the S3 bucket and '
    'applies a lifecycle policy that progressively moves processed CSV files '
    'through cheaper storage classes, reaching deletion after 7 years.'
)

h2('8.1 Lifecycle Stages')
lifecycle_rows = [
    ('Day 0',    'STANDARD',     'Initial upload — full performance', '100%'),
    ('Day 30',   'STANDARD_IA',  'Infrequent access — same durability', '~60%'),
    ('Day 90',   'GLACIER_IR',   'Glacier Instant Retrieval — ms access', '~32%'),
    ('Day 180',  'GLACIER',      'Glacier Flexible — 3–5 hr retrieval', '~20%'),
    ('Day 365',  'DEEP_ARCHIVE', 'Lowest cost — 12 hr retrieval', '~5%'),
    ('Day 2555', 'DELETE',       '7-year compliance window', '—'),
]
t = doc.add_table(rows=len(lifecycle_rows)+1, cols=4)
t.style = 'Table Grid'
for i, h in enumerate(['Transition', 'Storage Class', 'Retrieval', 'Cost vs Standard']):
    t.rows[0].cells[i].text = h
    t.rows[0].cells[i].paragraphs[0].runs[0].bold = True
    tc = t.rows[0].cells[i]._tc
    tcPr = tc.get_or_add_tcPr()
    shd  = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear')
    shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'), 'FF9900')
    tcPr.append(shd)
for ri, row_data in enumerate(lifecycle_rows):
    for ci, val in enumerate(row_data):
        t.rows[ri+1].cells[ci].text = val
        t.rows[ri+1].cells[ci].paragraphs[0].runs[0].font.size = Pt(9)

doc.add_paragraph()

h2('8.2 Terraform Resources')
bullet('aws_s3_bucket: devops-csv-uploads — private, versioning enabled')
bullet('aws_s3_bucket_server_side_encryption_configuration: AES-256 (SSE-S3) with bucket key')
bullet('aws_s3_bucket_public_access_block: all public access blocked')
bullet('aws_s3_bucket_lifecycle_configuration: 5-stage transition + expiration')
bullet('aws_iam_role + aws_iam_policy: least-privilege (PutObject, GetObject, ListBucket only)')

h2('8.3 Deploy')
code_block(
'''cd terraform-s3
terraform init
terraform plan   # review changes
terraform apply  # create resources
terraform output # show bucket name and IAM role ARN''')

page_break()

# ════════════════════════════════════════════════════════════════════════════
# SECTION 9 — CI/CD
# ════════════════════════════════════════════════════════════════════════════
h1('9. CI/CD Pipeline (GitHub Actions)')
para(
    'The pipeline triggers on pushes to main and develop branches. '
    'All jobs run in parallel where possible; deploy jobs depend on build success.'
)

h2('9.1 Pipeline Stages')
code_block(
'''git push main / develop
       │
       ├── test          pytest + flake8 (Python 3.12)
       │
       ├── helm-validate helm lint + template dry-run (dev + prod values)
       │
       ├── terraform     terraform validate + plan (S3 config)
       │
       ├── build         docker build + push to DockerHub (main only)
       │                 tags: latest + git SHA for traceability
       │
       ├── deploy-dev    helm upgrade → dev cluster  (develop branch)
       │
       └── deploy-prod   helm upgrade → prod cluster (main branch)
                         + kubectl rollout status verification''')

h2('9.2 GitHub Secrets Required')
secrets_rows = [
    ('DOCKERHUB_USERNAME', 'DockerHub username (deepak415)'),
    ('DOCKERHUB_TOKEN',    'DockerHub access token (not password)'),
    ('KUBECONFIG_DEV',     'base64-encoded kubeconfig for dev cluster'),
    ('KUBECONFIG_PROD',    'base64-encoded kubeconfig for prod cluster'),
    ('AWS_ACCESS_KEY_ID',  'For Terraform S3 plan/apply'),
    ('AWS_SECRET_ACCESS_KEY', 'For Terraform S3 plan/apply'),
]
table_2col(secrets_rows)

h2('9.3 Docker Image Tagging Strategy')
bullet('latest — always points to the most recent build from main')
bullet('git SHA (e.g. abc1234) — immutable tag for exact traceability')
bullet('v1.0.0 — manually tagged releases for rollback reference')
bullet('Rollback: helm upgrade with --set image.flaskApp.tag=<previous-sha>')

page_break()

# ════════════════════════════════════════════════════════════════════════════
# SECTION 10 — AZURE
# ════════════════════════════════════════════════════════════════════════════
h1('10. Azure AKS Deployment')
para(
    'A parallel deployment configuration for Azure Kubernetes Service is provided '
    'in the azure/ directory. The same Helm chart and Ansible playbook are reused; '
    'only the values files and kubeconfig differ.'
)

h2('10.1 Azure-Specific Configuration')
bullet('azure/k8s/deployment.yaml — raw K8s manifests targeting AKS')
bullet('azure/helm/environments/azure-dev-values.yaml — dev values for AKS')
bullet('azure/helm/environments/azure-prod-values.yaml — prod values for AKS')
bullet('azure/ansible/group_vars/azure.yaml — Azure-specific Ansible variables')

h2('10.2 Key Differences vs AWS')
azure_rows = [
    ('Image registry',    'deepak415/csv-processor (same DockerHub)'),
    ('Service type',      'LoadBalancer (Azure provisioner assigns public IP)'),
    ('Storage backend',   'Azure Blob Storage (same boto3 API, different endpoint)'),
    ('Ingress',           'Azure Application Gateway or NGINX Ingress Controller'),
    ('Node autoscaling',  'AKS cluster autoscaler (native Azure integration)'),
    ('Secrets',           'Azure Key Vault (replace Ansible secrets in prod)'),
]
table_2col(azure_rows)

page_break()

# ════════════════════════════════════════════════════════════════════════════
# SECTION 11 — LOCAL MINIKUBE STEPS
# ════════════════════════════════════════════════════════════════════════════
h1('11. Local Development — Minikube Step-by-Step')
para(
    'The complete application stack runs locally on Minikube using the docker driver. '
    'minikube tunnel maps the LoadBalancer service to 127.0.0.1:8080 permanently — '
    'no NodePort or port-forward needed.'
)

h2('11.1 Prerequisites')
code_block(
'''# macOS
brew install minikube kubectl helm ansible
brew install --cask docker       # Docker Desktop — must be running

# Verify versions
minikube version  # >= 1.32
kubectl version --client  # >= 1.29
helm version      # >= 3.14
docker --version  # >= 25''')

h2('11.2 Start Minikube')
code_block(
'''minikube start --driver=docker --cpus=4 --memory=8192
minikube addons enable metrics-server   # required for HPA
minikube addons enable dashboard        # optional: K8s dashboard

# Verify
kubectl get nodes
# NAME       STATUS   ROLES           AGE   VERSION
# minikube   Ready    control-plane   30s   v1.29.x''')

h2('11.3 Deploy MinIO (local S3)')
code_block(
'''kubectl apply -f local/k8s/namespace.yaml
kubectl apply -f local/k8s/minio.yaml
kubectl rollout status deployment/minio -n csv-app --timeout=120s

# Create the csv-uploads bucket
kubectl apply -f local/k8s/minio-init-job.yaml
kubectl wait --for=condition=complete job/minio-setup -n csv-app --timeout=120s

# Or via Makefile:
make deploy-minio''')

h2('11.4 Deploy Application via Helm')
code_block(
'''helm upgrade --install csv-app helm/csv-app \\
  -f helm/environments/local-values.yaml \\
  --namespace csv-app \\
  --create-namespace \\
  --wait --timeout 5m

# Verify deployment
kubectl get pods -n csv-app
# NAME                       READY   STATUS    RESTARTS   AGE
# csv-app-xxx-yyy            2/2     Running   0          60s   <- 2 containers!
# minio-xxx-aaa              1/1     Running   0          90s

# Or via Makefile:
make deploy-helm''')

h2('11.5 Start minikube tunnel (separate terminal)')
code_block(
'''# Keep this terminal open — tunnel must stay alive
minikube tunnel

# You will see:
# Status:
#   machine: minikube
#   pid: 12345
#   route: 10.96.0.0/12 -> 192.168.49.2
#   minikube: Running
#   services: [csv-app-service]
#     127.0.0.1:8080 <- csv-app-service''')

h2('11.6 Open Application')
code_block(
'''# Open in browser
open http://localhost:8080

# Or via Makefile:
make open          # opens http://localhost:8080
make open-minio    # opens MinIO console (login: minioadmin/minioadmin)''')

h2('11.7 Verify All Resources')
code_block(
'''kubectl get pods,svc,hpa -n csv-app -o wide

# Expected output:
# NAME                  READY STATUS   RESTARTS  AGE
# pod/csv-app-xxx-yyy   2/2   Running  0         60s
# pod/minio-xxx-aaa     1/1   Running  0         90s
#
# NAME                    TYPE         CLUSTER-IP    EXTERNAL-IP  PORT(S)
# service/csv-app-service LoadBalancer 10.107.x.x    127.0.0.1    8080:xxxxx/TCP
# service/minio           ClusterIP    10.103.x.x    <none>       9000/TCP
# service/minio-console   NodePort     10.105.x.x    <none>       9001:30901/TCP
#
# NAME          REFERENCE           TARGETS                    MINPODS MAXPODS REPLICAS
# csv-app-hpa   Deployment/csv-app  cpu: 2%/70% mem: 59%/85%  2       5       2''')

h2('11.8 Upload and Process CSV')
numbered('Open http://localhost:8080 in your browser')
numbered('Drag and drop tasks/soh-1-.csv (751 fashion products) onto the upload zone')
numbered('Click Upload & Process')
numbered('Result page shows: filename, 751 rows, MinIO storage path, full product table')
numbered('Return to homepage — previously processed files list shows the upload history')

h2('11.9 Run Ansible Validation')
code_block(
'''ansible-galaxy collection install -r ansible/requirements.yml

export KUBECONFIG=~/.kube/config
ansible-playbook ansible/site.yaml \\
  -i ansible/inventory/k8s.yaml \\
  -v

# Or via Makefile:
make ansible-validate''')

h2('11.10 Clean Up')
code_block(
'''make clean            # removes Helm release + namespace
make minikube-delete  # fully removes Minikube VM''')

page_break()

# ════════════════════════════════════════════════════════════════════════════
# SECTION 12 — SCREENSHOTS
# ════════════════════════════════════════════════════════════════════════════
h1('12. Application Screenshots')
para('All screenshots captured from the live Minikube deployment at http://localhost:8080.')

h2('12.1 Upload Form — Empty State')
para('CSV File Processor homepage. Storage backend shows MinIO (local Minikube). '
     'Drag-drop upload zone with Browse File button.')
img(os.path.join(SS, 'CSV_File_Processor_1.png'), width=Inches(5.8),
    caption_text='Figure 2 — CSV File Processor homepage at http://localhost:8080')

doc.add_paragraph()

h2('12.2 File Selected — Ready to Upload')
para('The soh-1-.csv file (751 fashion products) selected and ready for processing.')
img(os.path.join(SS, 'CSV_File_Processor_2.png'), width=Inches(5.8),
    caption_text='Figure 3 — soh-1-.csv selected, ready to click Upload & Process')

page_break()

h2('12.3 CSV Processed — 751 Rows Displayed')
para('Result page after processing. Shows: filename with timestamp prefix, '
     'total rows (751), storage backend (MinIO local), full MinIO path, '
     'and the complete product table with ID, Name, and Price columns.')
img(os.path.join(SS, 'CSV_File_Processor_3.png'), width=Inches(5.8),
    caption_text='Figure 4 — 751 rows parsed and displayed, stored at MinIO processed/ path')

doc.add_paragraph()

h2('12.4 Kubernetes Resources — kubectl output')
para('Terminal output showing all resources in the csv-app namespace: '
     '2/2 Running pods (Nginx + Flask sidecar), LoadBalancer with EXTERNAL-IP '
     '127.0.0.1:8080, and HPA showing cpu:2%/70% memory:59%/85% at idle.')
img(os.path.join(SS, 'pods-svc-hpa-status-kubectl.png'), width=Inches(5.8),
    caption_text='Figure 5 — kubectl get pods,svc,hpa -n csv-app showing live cluster state')

page_break()

h2('12.5 MinIO Console — Login Page')
para('MinIO Object Store web console accessible via minikube service minio-console. '
     'Credentials: minioadmin / minioadmin.')
img(os.path.join(SS, 'Minio_Storage_1.png'), width=Inches(5.0),
    caption_text='Figure 6 — MinIO Object Store login page (local S3-compatible storage)')

doc.add_paragraph()

h2('12.6 MinIO Bucket Browser — csv-uploads')
para('The csv-uploads bucket created by the init job. Shows the processed/ prefix '
     'where all uploaded CSVs are stored, organised by date.')
img(os.path.join(SS, 'Minio_Storage_2.png'), width=Inches(5.8),
    caption_text='Figure 7 — MinIO csv-uploads bucket with processed/ prefix (223.3 KiB, 6 objects)')

page_break()

h2('12.7 MinIO Processed Files — Date-Partitioned')
para('Contents of processed/2026/06/06/ — four CSV files uploaded during the demo session. '
     'File naming: YYYYMMDD_HHMMSS_<original-filename>.csv for uniqueness and sortability.')
img(os.path.join(SS, 'Minio_Storage_3.png'), width=Inches(5.8),
    caption_text='Figure 8 — Processed CSVs stored at processed/2026/06/06/ in MinIO')

doc.add_paragraph()

h2('12.8 Minikube Dashboard — Workload Status')
para('Kubernetes dashboard filtered to csv-app namespace. Shows: 2 Deployments running '
     '(csv-app + minio), 3 Pods running (2 app pods 2/2 + 1 MinIO), '
     '4 Replica Sets (current + rollout history), 1 completed Job (MinIO bucket init).')
img(os.path.join(SS, 'minikube-dashboard-status.png'), width=Inches(5.8),
    caption_text='Figure 9 — Minikube dashboard: csv-app namespace workload status')

page_break()

# ════════════════════════════════════════════════════════════════════════════
# SECTION 13 — REPO STRUCTURE
# ════════════════════════════════════════════════════════════════════════════
h1('13. Repository Structure')
code_block(
'''.
├── app/                          Web application
│   ├── app.py                    Flask: CSV parse, S3/MinIO upload, metadata
│   ├── Dockerfile                python:3.12-slim, non-root user (uid 1001)
│   ├── nginx.conf                Reverse proxy + static file serving (emptyDir)
│   ├── requirements.txt          Flask, boto3, gunicorn, werkzeug
│   ├── templates/
│   │   ├── index.html            Upload form + previously processed files list
│   │   └── result.html           Full CSV table (all 751 rows)
│   └── static/
│       ├── css/main.css          Responsive styles
│       └── js/main.js            Drag-drop upload UX
│
├── k8s-kops/                     Production kops cluster manifests
│   ├── cluster.yaml              Cluster spec: VPC, subnets, Calico, OIDC
│   ├── instancegroups.yaml       3 masters + 3 worker IGs
│   ├── cluster-autoscaler.yaml   CA with least-waste expander
│   ├── deployment.yaml           App deployment (nginx+flask, emptyDir)
│   └── service-hpa.yaml          LoadBalancer service + HPA + PDB
│
├── helm/                         Helm chart
│   ├── csv-app/                  Reusable chart
│   └── environments/             local / dev / prod values files
│
├── ansible/                      Kubernetes config management
│   ├── site.yaml                 ConfigMap + Secret + Deployment patch + health
│   ├── requirements.yml          kubernetes.core >= 3.0.0
│   ├── inventory/k8s.yaml        localhost, ansible_connection: local
│   └── group_vars/all.yaml       App vars, AWS region, image reference
│
├── terraform-s3/                 S3 infrastructure as code
│   ├── main.tf                   Bucket + lifecycle policy + IAM + encryption
│   ├── variables.tf
│   └── outputs.tf
│
├── local/                        Local Minikube helpers
│   ├── k8s/                      Raw manifests: namespace, minio, deployment, hpa
│   ├── ansible/                  Minikube-specific Ansible playbook
│   └── scripts/smoke-test.sh     End-to-end smoke test
│
├── azure/                        Azure AKS deployment
│   ├── k8s/                      Raw K8s manifests
│   ├── helm/environments/        azure-dev + azure-prod values
│   └── ansible/group_vars/       Azure-specific Ansible variables
│
├── .github/workflows/
│   └── ci-cd.yaml                Test → Build → Helm validate → Deploy
│
├── screenshots/                  All captured screenshots
├── docker-compose.yml            Quickest local start (no Minikube needed)
├── Makefile                      All commands: dev, build, deploy, test, clean
├── README.md                     Project overview + quick start
├── ARCHITECTURE.md               Deep-dive architecture + Mermaid diagram
└── LOCAL-TESTING-GUIDE.md        Step-by-step Minikube walkthrough''')

page_break()

# ════════════════════════════════════════════════════════════════════════════
# SECTION 14 — TECH STACK
# ════════════════════════════════════════════════════════════════════════════
h1('14. Technology Stack Summary')

tech_rows = [
    ('Web Framework',        'Python 3.12 + Flask',    'Lightweight, fast CSV processing'),
    ('Web Server',           'Nginx 1.25-alpine',      'High-performance reverse proxy + static files'),
    ('WSGI Server',          'Gunicorn',               'Production multi-worker WSGI server'),
    ('Container',            'Docker 25+',             'Immutable, reproducible images'),
    ('Orchestration',        'Kubernetes 1.29+ (kops)','Full cluster control on AWS'),
    ('Cluster Provisioner',  'kops 1.29+',             'Declarative K8s cluster on AWS'),
    ('Node Autoscaling',     'Cluster Autoscaler',     'Scale IGs based on pending pods'),
    ('Pod Autoscaling',      'HPA v2',                 'Scale on CPU + Memory metrics'),
    ('Package Manager',      'Helm 3.14+',             'Reusable K8s templates per env'),
    ('Config Management',    'Ansible 2.16+ / kubernetes.core 3+', 'K8s-native ConfigMap/Secret management'),
    ('Infrastructure as Code','Terraform 1.7+',        'S3 bucket + lifecycle + IAM'),
    ('Object Storage',       'AWS S3 / MinIO',         'Lifecycle-managed CSV archiving'),
    ('Archive Storage',      'S3 Glacier / Deep Archive', '7-year compliance retention'),
    ('CI/CD',                'GitHub Actions',         'Automated test → build → deploy'),
    ('Image Registry',       'DockerHub',              'deepak415/csv-processor:latest'),
    ('CNI',                  'Calico',                 'Network policy support'),
    ('Local Cluster',        'Minikube (docker driver)','Fast local iteration on Mac'),
    ('Cloud (prod)',         'AWS (kops) + Azure (AKS)','Multi-cloud deployment configs'),
]

t = doc.add_table(rows=len(tech_rows)+1, cols=3)
t.style = 'Table Grid'
for i, h in enumerate(['Layer', 'Technology', 'Rationale']):
    t.rows[0].cells[i].text = h
    t.rows[0].cells[i].paragraphs[0].runs[0].bold = True
    tc = t.rows[0].cells[i]._tc
    tcPr = tc.get_or_add_tcPr()
    shd  = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear')
    shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'), '1A1A2E')
    tcPr.append(shd)
    t.rows[0].cells[i].paragraphs[0].runs[0].font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
for ri, (layer, tech, rationale) in enumerate(tech_rows):
    t.rows[ri+1].cells[0].text = layer
    t.rows[ri+1].cells[1].text = tech
    t.rows[ri+1].cells[2].text = rationale
    for ci in range(3):
        t.rows[ri+1].cells[ci].paragraphs[0].runs[0].font.size = Pt(9)
    t.rows[ri+1].cells[0].paragraphs[0].runs[0].bold = True

# ── footer ───────────────────────────────────────────────────────────────────
doc.add_paragraph()
doc.add_paragraph()
divider()
fp = doc.add_paragraph()
fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
fr = fp.add_run('DevOps Case Study Submission  |  deepak415/csv-processor  |  github.com/AIINDEVOPS/silk  |  June 2026')
fr.font.size  = Pt(8)
fr.font.color.rgb = RGBColor(0x6C, 0x75, 0x7D)
fr.italic = True

# ── save ─────────────────────────────────────────────────────────────────────
doc.save(OUT)
print(f"Saved: {OUT}")
