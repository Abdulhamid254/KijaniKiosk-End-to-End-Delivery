# KijaniKiosk Infrastructure & Delivery Platform (Track A)

## 1. System Overview & Track Selection
This repository implements **Track A (Infrastructure-First)** for the KijaniKiosk End-to-End Delivery Capstone. It extends the `kk-payments` microservice into an isolated, multi-environment, monitored delivery platform running locally on **Minikube** with zero cloud spend.

* **Infrastructure Provisioning:** Terraform (`terraform/`) manages isolated Kubernetes namespaces (`kijani-staging` and `default`).
* **Configuration Management:** Ansible (`ansible/`) injects environment-specific ConfigMaps alongside a single shared Kubernetes Deployment manifest.
* **Continuous Delivery:** Jenkins (`jenkins/Jenkinsfile`) automates staging deployment, executes pod health smoke tests, and enforces a manual production approval gate with audit logging.
* **Observability:** Dual telemetry via live **Prometheus** alerting (`monitoring/alerts.yml`) and a **2-minute rolling log error rate analyzer** (`monitoring/log_analyzer.py`).
* **Event Integration:** Staging payments write receipt payloads to `kk-payments-receipts-staging` and trigger the Week 10 serverless receipt chain (`serverless/`).

---

## 2. Repository Structure
```text
kijanikiosk-infra-capstone/
├── app/                     # kk-payments Python HTTP service & optimized Alpine Dockerfile
├── ansible/                 # Inventory, host_vars, and k8s-deploy role playbooks
├── docs/                    # Project scope document and 8-field AI governance log
├── jenkins/                 # Declarative CI/CD pipeline with smoke tests & approval gate
├── kubernetes/
│   ├── base/                # Shared immutable kk-payments Deployment manifest
│   └── environments/        # Decoupled staging and production ConfigMaps
├── monitoring/              # Prometheus scrape/alert rules & live kubectl log analyzer
├── serverless/              # Week 10 staging receipt bucket & receipt chain processor
└── terraform/               # Modular IaC (main.tf, variables.tf, outputs.tf, backend.tf)
```

---

## 3. Prerequisites
Ensure the following tools are installed on your local workstation before starting:
* **Minikube** (`v1.32+`) and **kubectl** (`v1.29+`)
* **Terraform** (`>= 1.7`)
* **Ansible** (`core 2.16+`) with Python `kubernetes` and `PyYAML` packages
* **Docker** (`v24+`) and **Python** (`3.10+`)
* **Jenkins** (local controller or Docker container with `terraform`, `ansible`, and `kubectl` access)

---

## 4. Environment Configuration Matrix
Both environments run the exact same `kubernetes/base/deployment.yaml` blueprint, differentiated strictly by ConfigMap injection:

| Variable | Staging (`kijani-staging`) | Production (`default`) |
| :--- | :--- | :--- |
| **`DB_HOST`** | `stg-db-service.kijani-staging.svc.cluster.local` | `prod-db-service.default.svc.cluster.local` |
| **`RECEIPT_BUCKET`** | `kk-payments-receipts-staging` | `kk-payments-receipts-production` |
| **Replicas** | `2` | `2` |
| **CPU / Memory Limits** | `500m` / `512Mi` | `500m` / `512Mi` |

---

## 5. Quickstart: First-Day Local Deployment
Follow these steps to bring up the entire stack from scratch in under 15 minutes:

1. **Start Minikube:**
   ```bash
   minikube start
   ```

2. **Provision Namespaces with Terraform:**
   ```bash
   cd terraform
   terraform init
   terraform apply -auto-approve
   cd ..
   ```

3. **Set Up Ansible Python Dependencies & Deploy Staging:**
   ```bash
   python3 -m venv ansible/.venv
   ansible/.venv/bin/pip install kubernetes PyYAML
   ansible-playbook -i ansible/inventory/hosts.ini ansible/site.yml -e "k8s_namespace=kijani-staging k8s_config_dir=staging"
   ```

4. **Verify Staging Isolation & Running Pods:**
   ```bash
   kubectl get configmap kk-payments-config -n kijani-staging -o yaml
   kubectl get pods -n kijani-staging
   ```

---

## 6. Verification & Observability Runbook

### A. Live Log-Based Error Rate Check (Option B)
```bash
python3 monitoring/log_analyzer.py
cat monitoring/error_rate_summary.txt
```

### B. Live Prometheus Alert Verification
```bash
kubectl port-forward --address 0.0.0.0 -n kijani-staging deploy/kk-payments 8080:8080 >/dev/null 2>&1 &
sudo docker run -d --name kk-prometheus --network host \
  -v "\$(pwd)/monitoring/prometheus.yml:/etc/prometheus/prometheus.yml:ro" \
  -v "\$(pwd)/monitoring/alerts.yml:/etc/prometheus/alerts.yml:ro" \
  prom/prometheus:latest

# Trigger simulated 500 errors (>5% threshold) and check live alert state
for i in {1..10}; do curl -s http://localhost:8080/pay > /dev/null; done
for i in {1..4}; do curl -s "http://localhost:8080/pay?fail=true" > /dev/null; done
sleep 20
curl -s http://localhost:9090/api/v1/alerts | python3 -m json.tool
```

### C. Week 10 Serverless Receipt Chain Trigger
```bash
for POD in \$(kubectl get pods -n kijani-staging -l app=kk-payments -o jsonpath='{.items[*].metadata.name}'); do
  kubectl exec -n kijani-staging "\$POD" -- sh -c 'ls /tmp/kk-payments-receipts-staging/*.json 2>/dev/null' | while read -r FILE; do
    kubectl cp "kijani-staging/POD:FILE" "serverless/buckets/kk-payments-receipts-staging/(basename "FILE")"
  done
done
python3 serverless/functions/receipt_chain.py
```

---

## 7. Known Gaps & Production Hardening Roadmap
* **Remote State Locking:** Terraform currently uses a local backend (`terraform/state/terraform.tfstate`). Production deployment requires migrating to an S3 + DynamoDB backend for concurrent team state locking.
* **Real S3 Event Notifications:** The Week 10 receipt chain currently syncs staged JSON objects from pod `/tmp` storage. Production requires IAM ServiceAccount credentials (IRSA) writing directly to AWS S3 to invoke Lambda asynchronously.
* **Database Secrets Management:** Database hostnames are stored in ConfigMaps, while credentials should be injected via Kubernetes Secrets or External Secrets Operator rather than plaintext manifests.
