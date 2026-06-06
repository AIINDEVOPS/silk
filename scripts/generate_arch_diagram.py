"""
Generates architecture diagram for the DevOps Case Study as a PNG.
Output: screenshots/architecture-diagram.png
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import matplotlib.patheffects as pe

fig, ax = plt.subplots(1, 1, figsize=(22, 16))
ax.set_xlim(0, 22)
ax.set_ylim(0, 16)
ax.axis('off')
fig.patch.set_facecolor('#F8F9FA')

# ── colour palette ──────────────────────────────────────────────────────────
C = {
    'aws':      '#FF9900',
    'k8s':      '#326CE5',
    'pod':      '#E8F4FD',
    'nginx':    '#009639',
    'flask':    '#3776AB',
    'init':     '#F39C12',
    'minio':    '#C72E49',
    'ci':       '#2088FF',
    'github':   '#24292E',
    'dockerhub':'#2496ED',
    'user':     '#6C757D',
    'master':   '#8B4513',
    'worker':   '#2E7D32',
    'spot':     '#558B2F',
    'gpu':      '#7B1FA2',
    'ca':       '#E65100',
    's3':       '#FF9900',
    'glacier':  '#546E7A',
    'terraform':'#623CE4',
    'ansible':  '#EE0000',
    'helm':     '#0F1689',
    'border':   '#DEE2E6',
    'text':     '#212529',
    'bg_aws':   '#FFF8E7',
    'bg_k8s':   '#EFF6FF',
    'bg_ci':    '#F0F7FF',
    'bg_ns':    '#E8F5E9',
    'bg_pod':   '#E3F2FD',
    'bg_lc':    '#ECEFF1',
    'bg_local': '#F3E5F5',
}

def box(ax, x, y, w, h, fc, ec, alpha=1.0, lw=1.5, radius=0.3):
    p = FancyBboxPatch((x, y), w, h,
                       boxstyle=f"round,pad=0,rounding_size={radius}",
                       facecolor=fc, edgecolor=ec,
                       linewidth=lw, alpha=alpha, zorder=2)
    ax.add_patch(p)

def label(ax, x, y, text, size=8, color='#212529', bold=False,
          ha='center', va='center', zorder=5):
    weight = 'bold' if bold else 'normal'
    ax.text(x, y, text, fontsize=size, color=color, fontweight=weight,
            ha=ha, va=va, zorder=zorder,
            wrap=True)

def arrow(ax, x1, y1, x2, y2, color='#6C757D', lw=1.5,
          style='->', zorder=3):
    ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle=style, color=color,
                                lw=lw, connectionstyle='arc3,rad=0.0'),
                zorder=zorder)

# ════════════════════════════════════════════════════════════════════════════
# TITLE
# ════════════════════════════════════════════════════════════════════════════
ax.text(11, 15.5, 'DevOps Case Study — System Architecture',
        fontsize=16, fontweight='bold', ha='center', va='center',
        color=C['text'], zorder=6)
ax.text(11, 15.1, 'CSV File Processor · Kubernetes (kops) · Helm · Ansible · Terraform · GitHub Actions',
        fontsize=9, ha='center', va='center', color='#6C757D', zorder=6)

# ════════════════════════════════════════════════════════════════════════════
# 1. USER / INTERNET  (top-left)
# ════════════════════════════════════════════════════════════════════════════
box(ax, 0.2, 12.8, 2.8, 1.6, '#F8F9FA', C['user'], lw=1)
label(ax, 1.6, 14.0, 'User', 9, bold=True)
label(ax, 1.6, 13.5, 'Browser', 8, color='#6C757D')
label(ax, 1.6, 13.1, 'http://localhost:8080', 7, color='#6C757D')

# ════════════════════════════════════════════════════════════════════════════
# 2. CI/CD  (top-centre)
# ════════════════════════════════════════════════════════════════════════════
box(ax, 3.5, 12.4, 8.0, 2.0, C['bg_ci'], C['ci'], lw=1.5)
label(ax, 7.5, 14.1, 'CI/CD — GitHub Actions', 9, bold=True, color=C['ci'])

# GitHub
box(ax, 3.8, 12.6, 1.8, 1.4, '#F6F8FA', C['github'], lw=1)
label(ax, 4.7, 13.55, 'GitHub', 8, bold=True)
label(ax, 4.7, 13.15, 'git push', 7, color='#6C757D')
label(ax, 4.7, 12.82, 'main / develop', 7, color='#6C757D')

# Actions
box(ax, 6.0, 12.6, 2.2, 1.4, '#E8F4FD', C['ci'], lw=1)
label(ax, 7.1, 13.55, 'Actions', 8, bold=True, color=C['ci'])
label(ax, 7.1, 13.15, 'test → build', 7, color='#6C757D')
label(ax, 7.1, 12.82, 'helm validate', 7, color='#6C757D')

# DockerHub
box(ax, 8.6, 12.6, 2.6, 1.4, '#E8F4FD', C['dockerhub'], lw=1)
label(ax, 9.9, 13.55, 'DockerHub', 8, bold=True, color=C['dockerhub'])
label(ax, 9.9, 13.15, 'deepak415/', 7, color='#6C757D')
label(ax, 9.9, 12.82, 'csv-processor:latest', 7, color='#6C757D')

arrow(ax, 5.6, 13.3, 6.0, 13.3, C['ci'])
arrow(ax, 8.2, 13.3, 8.6, 13.3, C['dockerhub'])

# ════════════════════════════════════════════════════════════════════════════
# 3. AWS CLOUD  (main body)
# ════════════════════════════════════════════════════════════════════════════
box(ax, 0.2, 0.3, 13.8, 12.0, C['bg_aws'], C['aws'], lw=2, radius=0.5)
label(ax, 7.1, 12.15, 'AWS Cloud  (us-east-1)', 10, bold=True, color=C['aws'])

# ── Kubernetes cluster ────────────────────────────────────────────────────
box(ax, 0.5, 0.5, 13.2, 11.4, C['bg_k8s'], C['k8s'], lw=1.5, radius=0.4)
label(ax, 7.1, 11.7, 'Kubernetes Cluster (kops)   VPC 172.20.0.0/16', 9,
      bold=True, color=C['k8s'])

# ── Masters ──────────────────────────────────────────────────────────────
box(ax, 0.7, 9.8, 4.0, 1.6, '#FFF3E0', C['master'], lw=1)
label(ax, 2.7, 11.2, 'Control Plane — Fixed Size (no CA tags)', 8,
      bold=True, color=C['master'])
for i, az in enumerate(['AZ-a', 'AZ-b', 'AZ-c']):
    bx = 0.85 + i * 1.27
    box(ax, bx, 9.95, 1.1, 1.0, '#FFFDE7', C['master'], lw=1)
    label(ax, bx + 0.55, 10.65, f'Master\n{az}', 7, bold=True, color=C['master'])
    label(ax, bx + 0.55, 10.2, 'm5.large', 6.5, color='#6C757D')

# ── Cluster Autoscaler ───────────────────────────────────────────────────
box(ax, 0.7, 8.7, 4.0, 0.85, '#FFF3E0', C['ca'], lw=1)
label(ax, 2.7, 9.12, 'Cluster Autoscaler  (least-waste expander)', 8,
      bold=True, color=C['ca'])

# ── Worker IGs ───────────────────────────────────────────────────────────
box(ax, 0.7, 6.5, 4.0, 2.0, '#E8F5E9', C['worker'], lw=1)
label(ax, 2.7, 8.28, 'Worker Node Instance Groups', 8, bold=True, color=C['worker'])

igs = [
    ('On-Demand', 'm5.xlarge\nm5a/m5n/m4', 'min:2 max:10', C['worker']),
    ('Spot IG', 'm5/m4/r5/c5\n.xlarge', 'min:0 max:20', C['spot']),
    ('GPU Spot', 'p3.2xl\np2/g4dn', 'min:0 max:5', C['gpu']),
]
for i, (name, inst, limits, col) in enumerate(igs):
    bx = 0.85 + i * 1.27
    box(ax, bx, 6.65, 1.1, 1.45, '#FFFFFF', col, lw=1)
    label(ax, bx + 0.55, 7.85, name, 7, bold=True, color=col)
    label(ax, bx + 0.55, 7.45, inst, 6.5, color='#6C757D')
    label(ax, bx + 0.55, 6.95, limits, 6.5, color=col)

arrow(ax, 2.7, 8.7, 2.7, 8.55, C['ca'], lw=1.2)

# ── namespace: csv-app ────────────────────────────────────────────────────
box(ax, 5.0, 0.5, 8.5, 11.4, C['bg_ns'], C['k8s'], lw=1.2, radius=0.3)
label(ax, 9.25, 11.7, 'namespace: csv-app', 9, bold=True, color=C['k8s'])

# ── HPA ──────────────────────────────────────────────────────────────────
box(ax, 5.2, 10.3, 8.1, 0.95, '#E8F5E9', '#2E7D32', lw=1)
label(ax, 9.25, 10.77, 'HPA — CPU > 70%  or  Memory > 85%  →  scale up'
      '        min: 2   max: 5   stabilise: 60s↑ 300s↓', 8,
      bold=True, color='#2E7D32')

# ── Pod ───────────────────────────────────────────────────────────────────
box(ax, 5.2, 4.5, 8.1, 5.6, C['bg_pod'], C['k8s'], lw=1.2, radius=0.3)
label(ax, 9.25, 9.88, 'Pod  (2–5 replicas)', 9, bold=True, color=C['k8s'])

# Init container
box(ax, 5.4, 8.9, 7.7, 0.80, '#FFF8E1', C['init'], lw=1)
label(ax, 9.25, 9.30, 'Init Container — static-files-init', 8,
      bold=True, color=C['init'])
label(ax, 9.25, 8.98, 'copies /app/static/* → emptyDir volume (once at pod start)',
      7.5, color='#6C757D')

# emptyDir
box(ax, 8.5, 7.5, 2.0, 1.2, '#FFF9C4', '#F9A825', lw=1)
label(ax, 9.5, 8.3, 'emptyDir', 8, bold=True, color='#F57F17')
label(ax, 9.5, 7.95, 'shared-static', 7, color='#6C757D')
label(ax, 9.5, 7.68, 'CSS / JS files', 7, color='#6C757D')

# Nginx
box(ax, 5.4, 6.0, 2.8, 2.5, '#E8F5E9', C['nginx'], lw=1)
label(ax, 6.8, 8.25, 'Nginx :80', 9, bold=True, color=C['nginx'])
label(ax, 6.8, 7.9, 'reverse proxy', 7.5, color='#6C757D')
label(ax, 6.8, 7.6, 'static files', 7.5, color='#6C757D')
label(ax, 6.8, 7.3, 'proxy_pass →', 7.5, color='#6C757D')
label(ax, 6.8, 7.0, '127.0.0.1:5000', 7.5, color=C['nginx'])
label(ax, 6.8, 6.55, 'LoadBalancer :8080', 7, color='#6C757D')

# Flask
box(ax, 10.5, 6.0, 2.6, 2.5, '#DBEAFE', C['flask'], lw=1)
label(ax, 11.8, 8.25, 'Flask :5000', 9, bold=True, color=C['flask'])
label(ax, 11.8, 7.9, 'CSV Parser', 7.5, color='#6C757D')
label(ax, 11.8, 7.6, 'POST /upload', 7.5, color='#6C757D')
label(ax, 11.8, 7.3, 'GET  / (history)', 7.5, color='#6C757D')
label(ax, 11.8, 7.0, 'boto3 → S3/MinIO', 7.5, color=C['flask'])
label(ax, 11.8, 6.55, 'Gunicorn WSGI', 7, color='#6C757D')

# arrows inside pod
arrow(ax, 8.2, 9.0, 9.5, 8.7, C['init'], lw=1.2)  # init → emptyDir
arrow(ax, 8.1, 7.9, 8.5, 7.9, '#F9A825', lw=1.2)   # nginx → emptyDir
arrow(ax, 8.2, 7.3, 10.5, 7.3, C['k8s'], lw=1.5)   # nginx → flask

# ConfigMap / Secret
box(ax, 5.4, 4.7, 3.5, 1.1, '#FFFFFF', C['ansible'], lw=1)
label(ax, 7.15, 5.45, 'ConfigMap', 8, bold=True, color=C['ansible'])
label(ax, 7.15, 5.12, 'Managed by Ansible', 7, color='#6C757D')

box(ax, 9.2, 4.7, 4.0, 1.1, '#FFFFFF', '#7B1FA2', lw=1)
label(ax, 11.2, 5.45, 'Secret', 8, bold=True, color='#7B1FA2')
label(ax, 11.2, 5.12, 'S3_BUCKET · SECRET_KEY', 7, color='#6C757D')

# LoadBalancer Service label
box(ax, 5.4, 3.2, 7.7, 1.2, '#FFFFFF', C['k8s'], lw=1)
label(ax, 9.25, 3.85, 'Service — LoadBalancer  :8080  →  Pod :80',
      8, bold=True, color=C['k8s'])
label(ax, 9.25, 3.45, 'EXTERNAL-IP: 127.0.0.1  (minikube tunnel)  /  AWS NLB (prod)',
      7.5, color='#6C757D')

# HPA scale arrow
arrow(ax, 9.25, 10.3, 9.25, 10.1, '#2E7D32', lw=1.5)

# ════════════════════════════════════════════════════════════════════════════
# 4. S3 + GLACIER LIFECYCLE  (bottom of AWS box)
# ════════════════════════════════════════════════════════════════════════════
box(ax, 0.5, 0.5, 4.2, 5.7, C['bg_lc'], C['s3'], lw=1.2, radius=0.3)
label(ax, 2.6, 5.98, 'AWS S3 + Glacier Lifecycle (Terraform)', 8,
      bold=True, color=C['s3'])

stages = [
    ('STANDARD',    'Day 0',    '#4CAF50'),
    ('STANDARD_IA', 'Day 30',   '#FF9800'),
    ('GLACIER_IR',  'Day 90',   '#2196F3'),
    ('GLACIER',     'Day 180',  '#5C6BC0'),
    ('DEEP_ARCHIVE','Day 365',  '#455A64'),
    ('DELETE',      'Day 2555', '#F44336'),
]
for i, (name, day, col) in enumerate(stages):
    by = 4.85 - i * 0.74
    box(ax, 0.7, by, 3.8, 0.58, '#FFFFFF', col, lw=1)
    label(ax, 1.65, by + 0.29, day, 7, color='#6C757D', bold=True, ha='center')
    label(ax, 3.1, by + 0.29, name, 8, color=col, bold=True, ha='center')
    if i < len(stages) - 1:
        arrow(ax, 2.6, by, 2.6, by - 0.16, col, lw=1)

label(ax, 2.6, 0.75, '~40% · ~32% · ~20% · ~5% cost vs STANDARD', 6.5,
      color='#6C757D')

# ════════════════════════════════════════════════════════════════════════════
# 5. LOCAL DEV  (right column)
# ════════════════════════════════════════════════════════════════════════════
box(ax, 14.5, 0.3, 7.2, 6.5, C['bg_local'], '#7B1FA2', lw=1.5, radius=0.4)
label(ax, 18.1, 6.55, 'Local Dev (Minikube + docker driver)', 9,
      bold=True, color='#7B1FA2')

box(ax, 14.7, 4.8, 6.8, 1.6, '#FFFFFF', '#7B1FA2', lw=1)
label(ax, 18.1, 6.15, 'Minikube Cluster', 8, bold=True, color='#7B1FA2')
label(ax, 18.1, 5.8, 'minikube start --driver=docker', 7.5, color='#6C757D')
label(ax, 18.1, 5.5, 'metrics-server addon (for HPA)', 7.5, color='#6C757D')
label(ax, 18.1, 5.1, 'minikube tunnel → http://localhost:8080', 7.5, color='#7B1FA2')

box(ax, 14.7, 2.9, 6.8, 1.7, '#FFFFFF', C['minio'], lw=1)
label(ax, 18.1, 4.35, 'MinIO  (S3-compatible)', 8, bold=True, color=C['minio'])
label(ax, 18.1, 3.95, 'API: minio:9000  (boto3 endpoint)', 7.5, color='#6C757D')
label(ax, 18.1, 3.65, 'Console: localhost:9001  (browser)', 7.5, color='#6C757D')
label(ax, 18.1, 3.2, 'csv-uploads/processed/YYYY/MM/DD/', 7.5, color=C['minio'])

box(ax, 14.7, 1.6, 6.8, 1.1, '#FFFFFF', C['helm'], lw=1)
label(ax, 18.1, 2.35, 'Helm  +  Ansible  +  Terraform', 8, bold=True, color=C['helm'])
label(ax, 18.1, 1.95, 'helm upgrade --install csv-app helm/csv-app -f local-values.yaml', 7, color='#6C757D')

box(ax, 14.7, 0.5, 6.8, 0.9, '#FFFFFF', C['dockerhub'], lw=1)
label(ax, 18.1, 1.1, ' deepak415/csv-processor:latest  (DockerHub)', 7.5,
      bold=True, color=C['dockerhub'])
label(ax, 18.1, 0.72, 'docker pull → minikube image load  or  eval $(minikube docker-env)', 6.5, color='#6C757D')

# ════════════════════════════════════════════════════════════════════════════
# 6. ANSIBLE  (right column, top)
# ════════════════════════════════════════════════════════════════════════════
box(ax, 14.5, 7.1, 7.2, 5.3, '#FFF5F5', C['ansible'], lw=1.5, radius=0.4)
label(ax, 18.1, 12.15, 'Ansible  (kubernetes.core)', 9, bold=True, color=C['ansible'])

ansible_items = [
    ('ConfigMap apply', 'APP_NAME · STORAGE_BACKEND · AWS_REGION'),
    ('Secret apply', 'S3_BUCKET · SECRET_KEY (vault)'),
    ('Deployment patch', 'reference ConfigMap + Secret'),
    ('Rollout status', 'kubernetes.core.k8s_rollout_status'),
    ('Health check', 'k8s_exec → /health endpoint'),
]
for i, (task, detail) in enumerate(ansible_items):
    by = 11.55 - i * 0.84
    box(ax, 14.7, by - 0.35, 6.8, 0.68, '#FFFFFF', C['ansible'], lw=0.8)
    label(ax, 15.05, by + 0.0, f'▸ {task}', 7.5, bold=True, color=C['ansible'], ha='left')
    label(ax, 15.05, by - 0.2, f'  {detail}', 7, color='#6C757D', ha='left')

# ════════════════════════════════════════════════════════════════════════════
# INTER-COMPONENT ARROWS
# ════════════════════════════════════════════════════════════════════════════
# User → Service
arrow(ax, 1.6, 12.8, 3.5, 9.5, C['user'], lw=1.5)
ax.annotate('HTTP\n:8080', xy=(2.3, 11.0), fontsize=7, color=C['user'],
            ha='center', zorder=6)

# CI → DockerHub → Pod
arrow(ax, 9.25, 12.4, 9.25, 11.0, C['dockerhub'], lw=1.5)
ax.annotate('docker push\n+ helm deploy', xy=(9.6, 11.6),
            fontsize=7, color=C['dockerhub'], ha='left', zorder=6)

# Flask → S3 (inside AWS)
arrow(ax, 11.8, 6.0, 4.5, 5.2, C['flask'], lw=1.3)
ax.annotate('boto3\nupload', xy=(8.5, 5.7), fontsize=7, color=C['flask'],
            ha='center', zorder=6)

# Ansible → ConfigMap
arrow(ax, 14.5, 9.5, 13.2, 5.45, C['ansible'], lw=1.2)

# Service → Pod
arrow(ax, 9.25, 3.2, 9.25, 2.5, C['k8s'], lw=1.5)
arrow(ax, 7.8, 3.2, 7.8, 4.5, C['k8s'], lw=1.0)

# legend
legend_items = [
    mpatches.Patch(fc='#FF9900', label='AWS / S3'),
    mpatches.Patch(fc='#326CE5', label='Kubernetes'),
    mpatches.Patch(fc='#009639', label='Nginx'),
    mpatches.Patch(fc='#3776AB', label='Flask / Python'),
    mpatches.Patch(fc='#EE0000', label='Ansible'),
    mpatches.Patch(fc='#2088FF', label='GitHub Actions'),
    mpatches.Patch(fc='#2496ED', label='DockerHub'),
    mpatches.Patch(fc='#7B1FA2', label='Local / Minikube'),
    mpatches.Patch(fc='#C72E49', label='MinIO (local S3)'),
    mpatches.Patch(fc='#623CE4', label='Terraform'),
]
ax.legend(handles=legend_items, loc='lower right', fontsize=7,
          framealpha=0.9, ncol=2, bbox_to_anchor=(1.0, 0.0))

plt.tight_layout(pad=0.5)
plt.savefig('screenshots/architecture-diagram.png', dpi=150,
            bbox_inches='tight', facecolor=fig.get_facecolor())
print("Saved: screenshots/architecture-diagram.png")
