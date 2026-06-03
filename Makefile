##############################################################################
# DevOps Case Study – Makefile
# All commands for local Mac + Minikube end-to-end testing
#
# Usage:
#   make setup          # Install all prerequisites on Mac
#   make dev            # Full local setup (start → build → deploy → open)
#   make clean          # Tear down everything
##############################################################################

DOCKERHUB_USER   ?= YOUR_DOCKERHUB_USERNAME
IMAGE_NAME       := csv-processor
IMAGE_TAG        := local
NAMESPACE        := csv-app
HELM_RELEASE     := csv-app
MINIKUBE_CPUS    := 4
MINIKUBE_MEMORY  := 8192
MINIKUBE_DRIVER  := docker

.PHONY: help setup \
        minikube-start minikube-stop minikube-delete \
        build load \
        deploy-minio deploy-app deploy-helm \
        ansible-validate ansible-test \
        open open-minio \
        hpa-test hpa-watch \
        status logs \
        clean dev

# ── Help ─────────────────────────────────────────────────────────────────────
help:
	@echo ""
	@echo "DevOps Case Study – Minikube Local Testing"
	@echo "==========================================="
	@echo ""
	@echo "  make setup           Install all Mac prerequisites (Homebrew)"
	@echo "  make dev             Full setup: start + build + deploy + open"
	@echo ""
	@echo "  Minikube:"
	@echo "  make minikube-start  Start Minikube cluster"
	@echo "  make minikube-stop   Stop Minikube"
	@echo "  make minikube-delete Delete Minikube cluster"
	@echo ""
	@echo "  Build:"
	@echo "  make build           Build Docker image inside Minikube"
	@echo "  make load            Load image into Minikube cache"
	@echo ""
	@echo "  Deploy:"
	@echo "  make deploy-minio    Deploy MinIO (local S3)"
	@echo "  make deploy-app      Deploy app via raw K8s manifests"
	@echo "  make deploy-helm     Deploy app via Helm chart"
	@echo ""
	@echo "  Ansible:"
	@echo "  make ansible-validate  Run Ansible validation playbook"
	@echo "  make ansible-test      Run Ansible E2E test playbook"
	@echo ""
	@echo "  Test:"
	@echo "  make open            Open app in browser"
	@echo "  make open-minio      Open MinIO console in browser"
	@echo "  make hpa-test        Generate load to trigger HPA"
	@echo "  make hpa-watch       Watch HPA scaling in real time"
	@echo ""
	@echo "  make status          Show all resources"
	@echo "  make logs            Tail all pod logs"
	@echo "  make clean           Delete namespace + Minikube"
	@echo ""

# ── Setup Mac prerequisites ──────────────────────────────────────────────────
setup:
	@echo "==> Installing Mac prerequisites via Homebrew..."
	@which brew || (echo "Install Homebrew first: https://brew.sh" && exit 1)
	brew install minikube kubectl helm ansible docker
	brew install --cask docker
	@echo ""
	@echo "==> Installing Python tools..."
	pip3 install ansible boto3 botocore
	@echo ""
	@echo "==> Verify installations:"
	minikube version
	kubectl version --client
	helm version
	ansible --version
	@echo "✅ Setup complete!"

# ── Minikube ─────────────────────────────────────────────────────────────────
minikube-start:
	@echo "==> Starting Minikube (driver=$(MINIKUBE_DRIVER), CPUs=$(MINIKUBE_CPUS), Memory=$(MINIKUBE_MEMORY)MB)..."
	minikube start \
		--driver=$(MINIKUBE_DRIVER) \
		--cpus=$(MINIKUBE_CPUS) \
		--memory=$(MINIKUBE_MEMORY) \
		--kubernetes-version=stable \
		--addons=metrics-server,dashboard,ingress
	@echo ""
	@echo "==> Enabling addons..."
	minikube addons enable metrics-server
	minikube addons enable dashboard
	@echo ""
	kubectl config use-context minikube
	kubectl get nodes
	@echo "✅ Minikube started!"

minikube-stop:
	minikube stop

minikube-delete:
	minikube delete --all

# ── Docker Build inside Minikube ─────────────────────────────────────────────
build:
	@echo "==> Building Docker image inside Minikube Docker daemon..."
	@echo "    (This avoids pulling from DockerHub – image stays local)"
	eval $$(minikube docker-env) && \
		docker build -t $(IMAGE_NAME):$(IMAGE_TAG) ./app
	@echo "✅ Image built: $(IMAGE_NAME):$(IMAGE_TAG)"
	@echo ""
	@echo "==> Verifying image in Minikube:"
	eval $$(minikube docker-env) && docker images | grep $(IMAGE_NAME)

# ── Deploy MinIO ─────────────────────────────────────────────────────────────
deploy-minio:
	@echo "==> Deploying MinIO (local S3)..."
	kubectl apply -f local/k8s/namespace.yaml
	kubectl apply -f local/k8s/minio.yaml
	@echo "==> Waiting for MinIO to be ready..."
	kubectl rollout status deployment/minio -n $(NAMESPACE) --timeout=120s
	@echo "==> Creating csv-uploads bucket..."
	kubectl apply -f local/k8s/minio-init-job.yaml
	kubectl wait --for=condition=complete job/minio-setup -n $(NAMESPACE) --timeout=120s || true
	@echo "✅ MinIO ready!"

# ── Deploy App (raw manifests) ────────────────────────────────────────────────
deploy-app: build deploy-minio
	@echo "==> Deploying CSV app via raw K8s manifests..."
	kubectl apply -f local/k8s/deployment.yaml
	kubectl apply -f local/k8s/service-hpa.yaml
	@echo "==> Waiting for deployment..."
	kubectl rollout status deployment/csv-app -n $(NAMESPACE) --timeout=180s
	@echo "✅ App deployed!"
	@$(MAKE) status

# ── Deploy App (Helm) ─────────────────────────────────────────────────────────
deploy-helm: build deploy-minio
	@echo "==> Deploying CSV app via Helm..."
	helm upgrade --install $(HELM_RELEASE) helm/csv-app \
		-f helm/environments/local-values.yaml \
		--namespace $(NAMESPACE) \
		--create-namespace \
		--wait \
		--timeout 5m \
		--debug
	@echo "✅ Helm deployment complete!"
	@$(MAKE) status

# ── Ansible ──────────────────────────────────────────────────────────────────
ansible-validate:
	@echo "==> Running Ansible validation playbook..."
	cd local/ansible && \
		ansible-playbook site-local.yaml \
		-i inventory/minikube.yaml \
		-e @group_vars/local.yaml \
		-v

ansible-test: ansible-validate
	@echo "✅ Ansible validation complete!"

# ── Open in browser ──────────────────────────────────────────────────────────
open:
	@echo "==> Opening CSV app in browser..."
	minikube service csv-app-service -n $(NAMESPACE)

open-minio:
	@echo "==> Opening MinIO console (user: minioadmin / pass: minioadmin)..."
	minikube service minio-console -n $(NAMESPACE)

# ── HPA Load Testing ─────────────────────────────────────────────────────────
hpa-test:
	@echo "==> Generating load to trigger HPA..."
	@echo "    Watch scaling with: make hpa-watch"
	$(eval APP_URL := $(shell minikube service csv-app-service -n $(NAMESPACE) --url 2>/dev/null))
	@echo "    Hitting: $(APP_URL)"
	kubectl run load-generator \
		--image=busybox:latest \
		--restart=Never \
		-n $(NAMESPACE) \
		--rm -it \
		-- /bin/sh -c \
		"while true; do wget -q -O- $(APP_URL)/health > /dev/null 2>&1; done" &
	@echo "==> Load generator started. Run 'make hpa-watch' to observe scaling."

hpa-watch:
	@echo "==> Watching HPA (Ctrl+C to stop)..."
	watch -n 5 kubectl get hpa,pods -n $(NAMESPACE)

hpa-stop:
	kubectl delete pod load-generator -n $(NAMESPACE) --ignore-not-found

# ── Smoke Test ────────────────────────────────────────────────────────────────
smoke-test:
	@echo "==> Running smoke tests..."
	bash local/scripts/smoke-test.sh

# ── Docker Compose (no Minikube) ──────────────────────────────────────────────
compose-up:
	@echo "==> Starting Docker Compose stack (MinIO + Nginx + Flask)..."
	docker-compose up --build -d
	@echo "✅ Stack running:"
	@echo "   App:   http://localhost:8080"
	@echo "   MinIO: http://localhost:9001  (minioadmin/minioadmin)"

compose-down:
	docker-compose down -v

# ── Status ────────────────────────────────────────────────────────────────────
status:
	@echo ""
	@echo "════════════════════════════════════════════"
	@echo "  Minikube Cluster Status"
	@echo "════════════════════════════════════════════"
	@minikube status 2>/dev/null || true
	@echo ""
	@echo "════════════════════════════════════════════"
	@echo "  Namespace: $(NAMESPACE)"
	@echo "════════════════════════════════════════════"
	@kubectl get all -n $(NAMESPACE) 2>/dev/null || true
	@echo ""
	@echo "════════════════════════════════════════════"
	@echo "  HPA"
	@echo "════════════════════════════════════════════"
	@kubectl get hpa -n $(NAMESPACE) 2>/dev/null || true
	@echo ""
	@echo "════════════════════════════════════════════"
	@echo "  Access URLs"
	@echo "════════════════════════════════════════════"
	@minikube service csv-app-service -n $(NAMESPACE) --url 2>/dev/null | \
		xargs -I{} echo "  App:   {}" || true
	@echo "  MinIO: minikube service minio-console -n $(NAMESPACE)"
	@echo ""

logs:
	@echo "==> Tailing all pod logs in $(NAMESPACE) (Ctrl+C to stop)..."
	kubectl logs -f -l app=csv-app -n $(NAMESPACE) --all-containers --prefix=true

# ── Full Dev Flow ─────────────────────────────────────────────────────────────
dev: minikube-start deploy-helm ansible-validate
	@echo ""
	@echo "╔════════════════════════════════════════════╗"
	@echo "║  ✅  Local Environment Ready!              ║"
	@echo "╠════════════════════════════════════════════╣"
	@echo "║  Run: make open       → App in browser     ║"
	@echo "║  Run: make open-minio → MinIO console      ║"
	@echo "║  Run: make hpa-test   → Trigger autoscale  ║"
	@echo "║  Run: make status     → Show resources     ║"
	@echo "╚════════════════════════════════════════════╝"

# ── Clean Up ─────────────────────────────────────────────────────────────────
clean:
	@echo "==> Removing Helm release..."
	helm uninstall $(HELM_RELEASE) -n $(NAMESPACE) 2>/dev/null || true
	@echo "==> Deleting namespace..."
	kubectl delete namespace $(NAMESPACE) 2>/dev/null || true
	@echo "==> Stopping Minikube..."
	minikube stop
	@echo "✅ Clean complete (Minikube still running). Run 'make minikube-delete' to fully remove."
