"""
Generates architecture diagram for the DevOps Case Study as a PNG.
Output: screenshots/architecture-diagram.png
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch

fig, ax = plt.subplots(1, 1, figsize=(24, 16))
ax.set_xlim(0, 24)
ax.set_ylim(0, 16)
ax.axis('off')
fig.patch.set_facecolor('#F8F9FA')

C = {
    'k8s':       '#326CE5',
    'nginx':     '#009639',
    'flask':     '#3776AB',
    'init':      '#F39C12',
    'minio':     '#C72E49',
    'github':    '#24292E',
    'dockerhub': '#2496ED',
    'user':      '#6C757D',
    'master':    '#8B4513',
    'worker':    '#2E7D32',
    'spot':      '#558B2F',
    'gpu':       '#7B1FA2',
    'ca':        '#E65100',
    's3':        '#FF9900',
    'glacier':   '#546E7A',
    'terraform': '#623CE4',
    'ansible':   '#EE0000',
    'helm':      '#0F1689',
    'hpa':       '#1B5E20',
    'border':    '#DEE2E6',
    'text':      '#212529',
    'bg_mk':     '#EFF6FF',
    'bg_ns':     '#E8F5E9',
    'bg_pod':    '#E3F2FD',
    'bg_kops':   '#FFF8E7',
    'bg_lc':     '#ECEFF1',
    'bg_ans':    '#FFF5F5',
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
            ha=ha, va=va, zorder=zorder)


def arrow(ax, x1, y1, x2, y2, color='#6C757D', lw=1.5, style='->'):
    ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle=style, color=color,
                                lw=lw, connectionstyle='arc3,rad=0.0'),
                zorder=3)


# ── TITLE ────────────────────────────────────────────────────────────────────
ax.text(12, 15.6, 'DevOps Case Study — System Architecture',
        fontsize=17, fontweight='bold', ha='center', va='center',
        color=C['text'], zorder=6)
ax.text(12, 15.2, 'Task 1: kops Cluster Config (AWS)   |   Task 2: CSV Processor on Minikube (Mac)',
        fontsize=9.5, ha='center', va='center', color='#6C757D', zorder=6)

# ── USER ─────────────────────────────────────────────────────────────────────
box(ax, 0.2, 12.0, 2.6, 1.8, '#F8F9FA', C['user'], lw=1)
label(ax, 1.5, 13.55, 'User', 10, bold=True)
label(ax, 1.5, 13.1, 'Browser', 8, color='#6C757D')
label(ax, 1.5, 12.65, 'http://localhost:8080', 7.5, color='#6C757D')

# ── GITHUB + DOCKERHUB (simple storage, no CI/CD) ────────────────────────────
box(ax, 0.2, 9.8, 2.6, 2.0, '#F6F8FA', C['github'], lw=1)
label(ax, 1.5, 11.55, 'GitHub', 9, bold=True, color=C['github'])
label(ax, 1.5, 11.15, 'AIINDEVOPS/silk', 7.5, color='#6C757D')
label(ax, 1.5, 10.75, 'code repository', 7, color='#6C757D')
label(ax, 1.5, 10.1, 'clone & run', 7, color='#6C757D')

box(ax, 0.2, 7.6, 2.6, 2.0, '#EBF5FB', C['dockerhub'], lw=1)
label(ax, 1.5, 9.35, 'DockerHub', 9, bold=True, color=C['dockerhub'])
label(ax, 1.5, 8.95, 'deepak415/', 7.5, color='#6C757D')
label(ax, 1.5, 8.55, 'csv-processor:latest', 7, color='#6C757D')
label(ax, 1.5, 7.9, 'public image', 7, color='#6C757D')

# ═══════════════════════════════════════════════════════════════════════════
# TASK 2 — MINIKUBE (primary, left-center, large)
# ═══════════════════════════════════════════════════════════════════════════
box(ax, 3.0, 0.3, 12.5, 14.6, C['bg_mk'], C['k8s'], lw=2.5, radius=0.6)
label(ax, 9.25, 14.65, 'TASK 2 — Application on Minikube (Mac, docker driver)',
      11, bold=True, color=C['k8s'])
label(ax, 9.25, 14.25, 'minikube start --driver=docker --cpus=4 --memory=8192',
      8, color='#6C757D')

# ── LoadBalancer Service ──────────────────────────────────────────────────
box(ax, 3.2, 12.8, 12.1, 1.0, '#FFFFFF', C['k8s'], lw=1.2)
label(ax, 9.25, 13.45, 'Service — LoadBalancer  port 8080',
      9, bold=True, color=C['k8s'])
label(ax, 9.25, 13.05,
      'EXTERNAL-IP: 127.0.0.1  (minikube tunnel)     Selector: app=csv-app',
      7.5, color='#6C757D')

# ── HPA ──────────────────────────────────────────────────────────────────
box(ax, 3.2, 11.5, 12.1, 1.1, '#E8F5E9', C['hpa'], lw=1.2)
label(ax, 9.25, 12.2,
      'HPA v2  —  CPU target 70%  |  Memory target 85%  |  min:2  max:5 replicas',
      9, bold=True, color=C['hpa'])
label(ax, 9.25, 11.75,
      'scaleUp stabilise 60s  ·  scaleDown stabilise 300s  ·  metrics-server addon required',
      7.5, color='#6C757D')

# ── namespace: csv-app ────────────────────────────────────────────────────
box(ax, 3.2, 4.2, 12.1, 7.1, C['bg_ns'], C['k8s'], lw=1.2, radius=0.3)
label(ax, 9.25, 11.1, 'namespace: csv-app', 9, bold=True, color=C['k8s'])

# ── Pod ───────────────────────────────────────────────────────────────────
box(ax, 3.4, 5.5, 11.7, 5.4, C['bg_pod'], C['k8s'], lw=1.2, radius=0.3)
label(ax, 9.25, 10.7, 'Pod  (2-5 replicas managed by HPA)',
      9, bold=True, color=C['k8s'])

# Init Container
box(ax, 3.6, 9.5, 11.3, 1.2, '#FFF8E1', C['init'], lw=1)
label(ax, 9.25, 10.3, 'Init Container: static-files-init  (runs ONCE at pod start)',
      8.5, bold=True, color=C['init'])
label(ax, 9.25, 9.85, 'cp /app/static/* → /app/shared-static/  (emptyDir volume)',
      7.5, color='#6C757D')

# emptyDir volume
box(ax, 7.8, 7.8, 2.9, 1.5, '#FFF9C4', '#F9A825', lw=1.2)
label(ax, 9.25, 9.0, 'emptyDir', 9, bold=True, color='#F57F17')
label(ax, 9.25, 8.6, 'shared-static', 7.5, color='#6C757D')
label(ax, 9.25, 8.15, 'CSS / JS  (no NFS)', 7.5, color='#F57F17')

# Nginx container
box(ax, 3.6, 5.7, 3.8, 4.0, '#E8F5E9', C['nginx'], lw=1.2)
label(ax, 5.5, 9.4, 'Nginx :80', 10, bold=True, color=C['nginx'])
label(ax, 5.5, 9.0, 'sidecar container', 7.5, color='#6C757D')
label(ax, 5.5, 8.6, '/static/  → emptyDir', 7.5, color=C['nginx'])
label(ax, 5.5, 8.2, 'proxy_pass →', 7.5, color='#6C757D')
label(ax, 5.5, 7.8, '127.0.0.1:5000', 7.5, color=C['nginx'])
label(ax, 5.5, 7.3, 'nginx:1.25-alpine', 7, color='#6C757D')
label(ax, 5.5, 6.9, 'non-root  uid 101', 7, color='#6C757D')

# Flask container
box(ax, 11.1, 5.7, 3.8, 4.0, '#DBEAFE', C['flask'], lw=1.2)
label(ax, 13.0, 9.4, 'Flask :5000', 10, bold=True, color=C['flask'])
label(ax, 13.0, 9.0, 'main app container', 7.5, color='#6C757D')
label(ax, 13.0, 8.6, 'POST /upload', 7.5, color=C['flask'])
label(ax, 13.0, 8.2, 'GET  / (history)', 7.5, color=C['flask'])
label(ax, 13.0, 7.8, 'boto3 → MinIO/S3', 7.5, color='#6C757D')
label(ax, 13.0, 7.3, 'python:3.12-slim', 7, color='#6C757D')
label(ax, 13.0, 6.9, 'Gunicorn WSGI', 7, color='#6C757D')

# arrows inside pod
arrow(ax, 9.25, 9.5, 9.25, 9.3, C['init'], lw=1.3)   # init → emptyDir
arrow(ax, 7.8, 8.5, 7.4, 8.5, '#F9A825', lw=1.2)      # emptyDir → nginx
arrow(ax, 7.4, 7.8, 11.1, 7.8, C['k8s'], lw=1.8)      # nginx → flask

# ConfigMap / Secret
box(ax, 3.4, 4.4, 5.5, 0.9, '#FFFFFF', C['ansible'], lw=1)
label(ax, 6.15, 5.0, 'ConfigMap', 8.5, bold=True, color=C['ansible'])
label(ax, 6.15, 4.65, 'APP_NAME · STORAGE_BACKEND · Ansible-managed', 7, color='#6C757D')

box(ax, 9.3, 4.4, 5.8, 0.9, '#FFFFFF', '#7B1FA2', lw=1)
label(ax, 12.2, 5.0, 'Secret', 8.5, bold=True, color='#7B1FA2')
label(ax, 12.2, 4.65, 'S3_BUCKET · SECRET_KEY · Ansible-managed', 7, color='#6C757D')

# MinIO
box(ax, 3.2, 0.5, 5.8, 3.5, '#FFFFFF', C['minio'], lw=1.5)
label(ax, 6.1, 3.7, 'MinIO (local S3)', 10, bold=True, color=C['minio'])
label(ax, 6.1, 3.25, 'S3-compatible object storage', 7.5, color='#6C757D')
label(ax, 6.1, 2.85, 'API:     minio:9000  (boto3 endpoint)', 7.5, color='#6C757D')
label(ax, 6.1, 2.45, 'Console: localhost:9001  (browser)', 7.5, color='#6C757D')
label(ax, 6.1, 2.0, 'csv-uploads/processed/YYYY/MM/DD/', 7.5, color=C['minio'])
label(ax, 6.1, 1.55, 'login: minioadmin / minioadmin', 7, color='#6C757D')
label(ax, 6.1, 1.1, '(production: AWS S3 + Glacier — see Terraform)', 7, color='#6C757D')

# Helm / Ansible / Terraform boxes
box(ax, 9.3, 2.6, 5.8, 1.4, '#FFFFFF', C['helm'], lw=1)
label(ax, 12.2, 3.65, 'Helm  (multi-environment chart)', 8.5, bold=True, color=C['helm'])
label(ax, 12.2, 3.25, 'helm/csv-app/  +  environments/local-values.yaml', 7.5, color='#6C757D')
label(ax, 12.2, 2.85, 'helm upgrade --install csv-app helm/csv-app -f local-values.yaml', 7, color='#6C757D')

box(ax, 9.3, 1.3, 5.8, 1.1, '#FFFFFF', C['ansible'], lw=1)
label(ax, 12.2, 2.05, 'Ansible  (kubernetes.core — no SSH)', 8.5, bold=True, color=C['ansible'])
label(ax, 12.2, 1.65, 'ansible-playbook ansible/site.yaml -i ansible/inventory/k8s.yaml', 7, color='#6C757D')

box(ax, 9.3, 0.5, 5.8, 0.65, '#FFFFFF', C['terraform'], lw=1)
label(ax, 12.2, 0.82, 'Terraform  (S3 Glacier lifecycle)  →  terraform-s3/main.tf', 7.5, bold=True, color=C['terraform'])

# Flask → MinIO arrow
arrow(ax, 11.5, 5.7, 7.2, 4.0, C['flask'], lw=1.5)
ax.annotate('boto3 upload\nCSV file', xy=(9.8, 4.9),
            fontsize=7, color=C['flask'], ha='center', zorder=6)

# Service → HPA → Pod arrows
arrow(ax, 9.25, 12.8, 9.25, 12.6, C['k8s'], lw=1.8)
arrow(ax, 9.25, 11.5, 9.25, 10.9, C['hpa'], lw=1.8)

# ═══════════════════════════════════════════════════════════════════════════
# TASK 1 — KOPS CONFIG (right side, secondary)
# ═══════════════════════════════════════════════════════════════════════════
box(ax, 15.8, 7.5, 7.9, 7.4, C['bg_kops'], '#FF9900', lw=2, radius=0.5)
label(ax, 19.75, 14.65, 'TASK 1 — kops Cluster Config', 10, bold=True, color='#E65100')
label(ax, 19.75, 14.25, 'AWS us-east-1  (config only — no running cluster required)',
      8, color='#6C757D')

# Masters
box(ax, 16.0, 12.5, 7.5, 2.2, '#FFF3E0', C['master'], lw=1)
label(ax, 19.75, 14.45, '', 8)  # spacer
label(ax, 19.75, 14.38, 'Control Plane — Fixed Size  (NO Cluster Autoscaler tags)',
      8, bold=True, color=C['master'])

for i, az in enumerate(['AZ-a', 'AZ-b', 'AZ-c']):
    bx = 16.15 + i * 2.42
    box(ax, bx, 12.65, 2.15, 1.7, '#FFFDE7', C['master'], lw=1)
    label(ax, bx + 1.07, 13.75, f'Master {az}', 8, bold=True, color=C['master'])
    label(ax, bx + 1.07, 13.35, 'm5.large', 7.5, color='#6C757D')
    label(ax, bx + 1.07, 12.95, 'On-Demand  min:1 max:1', 6.5, color=C['master'])

# Cluster Autoscaler
box(ax, 16.0, 11.2, 7.5, 1.1, '#FFF3E0', C['ca'], lw=1)
label(ax, 19.75, 11.77, 'Cluster Autoscaler  (least-waste expander)', 8.5, bold=True, color=C['ca'])
label(ax, 19.75, 11.4, 'Auto-discovers worker IGs via ASG tags  ·  scale-down after 10min', 7, color='#6C757D')

# Worker IGs
box(ax, 16.0, 7.7, 7.5, 3.3, '#E8F5E9', C['worker'], lw=1)
label(ax, 19.75, 10.73, 'Worker Instance Groups  (CA-managed)', 8.5, bold=True, color=C['worker'])

igs = [
    ('On-Demand IG', 'm5/m5a/m5n/m4.xlarge', 'min:2  max:10', C['worker']),
    ('Spot IG',      'm5/m4/r5/c5.xlarge', 'min:0  max:20', C['spot']),
    ('GPU Spot IG',  'p3.2xl/p2.xl/g4dn.xl', 'min:0  max:5',  C['gpu']),
]
for i, (name, inst, limits, col) in enumerate(igs):
    bx = 16.15 + i * 2.42
    box(ax, bx, 7.85, 2.15, 2.7, '#FFFFFF', col, lw=1)
    label(ax, bx + 1.07, 10.3, name, 7.5, bold=True, color=col)
    label(ax, bx + 1.07, 9.9, inst, 6.5, color='#6C757D')
    label(ax, bx + 1.07, 9.5, limits, 6.5, color=col)
    label(ax, bx + 1.07, 9.0, 'Spot' if 'Spot' in name else 'On-Demand', 6.5, color='#6C757D')

arrow(ax, 19.75, 11.2, 19.75, 11.0, C['ca'], lw=1.3)

# ═══════════════════════════════════════════════════════════════════════════
# S3 GLACIER LIFECYCLE  (right side, bottom)
# ═══════════════════════════════════════════════════════════════════════════
box(ax, 15.8, 0.3, 7.9, 7.0, C['bg_lc'], C['terraform'], lw=1.5, radius=0.4)
label(ax, 19.75, 7.05, 'S3 Glacier Lifecycle  (Terraform)', 9.5, bold=True, color=C['terraform'])
label(ax, 19.75, 6.65,
      'terraform-s3/main.tf  |  Assignment: "implement s3 glacier transition"',
      7.5, color='#6C757D')

stages = [
    ('STANDARD',     'Day 0',    '#4CAF50', 'full performance'),
    ('STANDARD_IA',  'Day 30',   '#FF9800', '~40% cheaper'),
    ('GLACIER_IR',   'Day 90',   '#2196F3', '~68% cheaper, ms retrieval'),
    ('GLACIER',      'Day 180',  '#5C6BC0', '~80% cheaper, 3-5hr'),
    ('DEEP_ARCHIVE', 'Day 365',  '#455A64', '~95% cheaper, 12hr'),
    ('DELETE',       'Day 2555', '#F44336', '7-year compliance window'),
]
for i, (name, day, col, note) in enumerate(stages):
    by = 6.05 - i * 0.92
    box(ax, 16.0, by - 0.4, 7.5, 0.72, '#FFFFFF', col, lw=1)
    label(ax, 17.15, by - 0.04, day, 7.5, color='#6C757D', bold=True)
    label(ax, 19.0, by - 0.04, name, 8.5, color=col, bold=True)
    label(ax, 22.3, by - 0.04, note, 7, color='#6C757D')
    if i < len(stages) - 1:
        arrow(ax, 19.75, by - 0.4, 19.75, by - 0.56, col, lw=1)

# ═══════════════════════════════════════════════════════════════════════════
# INTER-COMPONENT ARROWS
# ═══════════════════════════════════════════════════════════════════════════
# User → Service
arrow(ax, 2.8, 13.0, 3.2, 13.3, C['user'], lw=1.8)
ax.annotate('HTTP :8080', xy=(2.9, 13.5), fontsize=7.5, color=C['user'],
            ha='center', zorder=6)

# DockerHub → Pod
arrow(ax, 2.8, 8.6, 3.4, 8.2, C['dockerhub'], lw=1.5)
ax.annotate('pull image', xy=(2.9, 8.0), fontsize=7, color=C['dockerhub'],
            ha='center', zorder=6)

# GitHub → Minikube (clone)
arrow(ax, 2.8, 11.0, 3.2, 10.2, C['github'], lw=1.2)
ax.annotate('git clone', xy=(2.7, 10.5), fontsize=7, color=C['github'],
            ha='center', zorder=6)

# ═══════════════════════════════════════════════════════════════════════════
# LEGEND
# ═══════════════════════════════════════════════════════════════════════════
legend_items = [
    mpatches.Patch(fc=C['k8s'],       label='Kubernetes'),
    mpatches.Patch(fc=C['nginx'],     label='Nginx (sidecar)'),
    mpatches.Patch(fc=C['flask'],     label='Flask / Python'),
    mpatches.Patch(fc=C['minio'],     label='MinIO (local S3)'),
    mpatches.Patch(fc=C['ansible'],   label='Ansible'),
    mpatches.Patch(fc=C['helm'],      label='Helm'),
    mpatches.Patch(fc=C['terraform'], label='Terraform'),
    mpatches.Patch(fc='#FF9900',      label='AWS / kops'),
    mpatches.Patch(fc=C['dockerhub'], label='DockerHub'),
    mpatches.Patch(fc=C['github'],    label='GitHub'),
]
ax.legend(handles=legend_items, loc='lower left', fontsize=7.5,
          framealpha=0.95, ncol=2, bbox_to_anchor=(0.0, 0.0))

plt.tight_layout(pad=0.3)
plt.savefig('screenshots/architecture-diagram.png', dpi=150,
            bbox_inches='tight', facecolor=fig.get_facecolor())
print("Saved: screenshots/architecture-diagram.png")
