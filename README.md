# KijaniKiosk Infrastructure & Delivery Platform (Track A)

Production-approaching multi-environment infrastructure, gated CI/CD delivery, live observability, and serverless receipt integration for the `kk-payments` microservice on local Minikube.

---

## 1. Architecture Overview

This platform enforces strict environment isolation between automated staging (`kijani-staging`) and production simulation (`default`) while sharing a single immutable application Deployment blueprint.

```text
[ Developer Push / PR Merge to main ]
                 │
                 ▼
[ Jenkins CI/CD Pipeline (jenkins/Jenkinsfile) ]
   ├── 1. Terraform IaC   ──> Provisions isolated namespaces (kijani-staging & default)
   ├── 2. Ansible Config  ──> Injects environment ConfigMaps + shared Deployment
   ├── 3. Smoke Test      ──> Verifies kk-payments pods are Running in kijani-staging
   ├── 4. Approval Gate   ──> Blocks until manual APPROVE_REASON is logged
   └── 5. Prod Rollout    ──> Deploys verified image to default namespace
                 │
                 ▼
[ Minikube Runtime & Telemetry ]
   ├── kk-payments (x2 replicas, python:3.12-alpine)
   ├── Prometheus (/metrics scrape -> alerts.yml fires on >5% HTTP 500 error rate)
   ├── Log Analyzer (monitoring/log_analyzer.py rolling 2m kubectl log check)
   └── Serverless Receipt Chain (writes to kk-payments-receipts-staging -> receipt_chain.py)
```

---

## 2. Repository Structure

```text
kijanikiosk-infra-capstone/
├── ansible/
│   ├── ansible.cfg                        # Local inventory & Python interpreter defaults
│   ├── site.yml                           # Entry-point orchestration playbook
│   ├── inventory/
│   │   ├── hosts.ini                      # Minikube localhost target & venv interpreter
│   │   └── host_vars/localhost.yml        # Default staging namespace/config variables
│   └── roles/k8s-deploy/tasks/main.yml    # Reusable ConfigMap & Deployment tasks
├── app/
│   ├── Dockerfile                         # Lightweight python:3.12-alpine container (<100MB)
│   └── server.py                          # Microservice (/healthz, /pay, /metrics)
├── docs/
│   ├── ai-governance-log.md               # 8-field audit log of AI-assisted changes
│   └── project-scope.md                   # System boundaries, SLOs & architecture scope
├── jenkins/
│   └── Jenkinsfile                        # Multi-stage pipeline with smoke test & manual gate
├── kubernetes/
│   ├── base/deployment.yaml               # Shared immutable kk-payments Deployment
│   └── environments/
│       ├── staging/configmap.yaml         # Staging DB_HOST & kk-payments-receipts-staging
│       └── production/configmap.yaml      # Production DB_HOST & kk-payments-receipts-production
├── monitoring/
│   ├── alerts.yml                         # Prometheus >5% error rate alerting rule
│   ├── prometheus.yml                     # Live scrape configuration for kk-payments
│   └── log_analyzer.py                    # Option B 2-minute rolling log error analyzer
├── serverless/
│   └── functions/receipt_chain.py         # Week 10 receipt processor & notification chain
└── terraform/
    ├── backend.tf                         # Local state isolation
    ├── main.tf                            # Namespace provisioning & default import
    ├── outputs.tf                         # Exported namespace identifiers
    └── variables.tf                       # Parameterized cluster & namespace inputs
```

---

## 3. Prerequisites & Local Setup

Ensure the following tools are installed on your workstation before starting:

* **Docker** (`>= 24.0`)
* **Minikube** (`>= 1.32`) and **kubectl** (`>= 1.29`)
* **Terraform** (`>= 1.7`)
* **Ansible** (`>= 2.15`) with `kubernetes.core` collection (`ansible-galaxy collection install kubernetes.core`)
* **Python 3** (`>= 3.10`) with `kubernetes` and `PyYAML` installed in `ansible/.venv`

### Quick Cluster & Python Environment Bootstrap

```bash
# 1. Start local Minikube cluster
minikube start

# 2. Set up Ansible Python virtual environment
python3 -m venv ansible/.venv
ansible/.venv/bin/pip install kubernetes PyYAML
```

---

## 4. Infrastructure Provisioning & Deployment

### Step 1: Provision Isolated Namespaces with Terraform

```bash
cd terraform
terraform init
terraform validate
terraform apply -auto-approve
cd ..
```

Verify both namespaces exist:
```bash
kubectl get namespaces --show-labels
```

### Step 2: Deploy `kk-payments` to Staging with Ansible

```bash
ansible-playbook -i ansible/inventory/hosts.ini ansible/site.yml \
  -e "k8s_namespace=kijani-staging k8s_config_dir=staging"
```

Verify staging ConfigMap isolation and running pods:
```bash
kubectl get configmap kk-payments-config -n kijani-staging -o yaml
kubectl get pods -n kijani-staging -l app=kk-payments
```

---

## 5. CI/CD Pipeline Execution (Jenkins)

The declarative pipeline in `jenkins/Jenkinsfile` automates end-to-end delivery:

1. **Initialize & Validate:** Verifies `terraform`, `ansible`, and `kubectl` binaries.
2. **Infrastructure Provision:** Applies Terraform state for `kijani-staging` and `default`.
3. **Deploy to Staging Namespace:** Runs Ansible against `kijani-staging` with staging ConfigMaps.
4. **Automated Smoke Testing:** Verifies `kk-payments` pods reach `Running` state in `kijani-staging`.
5. **Production Promotion Gate:** Pauses execution until an authorized reviewer submits an `APPROVE_REASON`.
6. **Deploy to Production:** Deploys the verified container blueprint to the `default` namespace with production ConfigMaps.

### Configuring Jenkins Polling
1. Create a **Pipeline** job named `kijanikiosk-track-a-delivery`.
2. Under **Build Triggers**, enable **Poll SCM** with schedule `H/3 * * * *`.
3. Under **Pipeline**, choose **Pipeline script from SCM** (`Git`), set branch to `*/main`, and set **Script Path** to `jenkins/Jenkinsfile`.

---

## 6. Observability & Alert Verification

### Live Prometheus Alerting (`monitoring/alerts.yml`)

1. Forward the staging service and start Prometheus:
   ```bash
   kubectl port-forward --address 0.0.0.0 -n kijani-staging deploy/kk-payments 8080:8080 >/dev/null 2>&1 &

   docker run -d --name kk-prometheus --network host \
     -v "\$(pwd)/monitoring/prometheus.yml:/etc/prometheus/prometheus.yml:ro" \
     -v "\$(pwd)/monitoring/alerts.yml:/etc/prometheus/alerts.yml:ro" \
     prom/prometheus:latest
   ```
2. Trigger simulated HTTP 500 gateway errors (`>5%` threshold) and verify the alert fires:
   ```bash
   for i in {1..10}; do curl -s http://localhost:8080/pay > /dev/null; done
   for i in {1..4}; do curl -s "http://localhost:8080/pay?fail=true" > /dev/null; done
   sleep 20
   curl -s http://localhost:9090/api/v1/alerts | python3 -m json.tool
   ```

### Log-Based Error Rate Analyzer (`monitoring/log_analyzer.py`)

Run the rolling 2-minute Kubernetes log analyzer to evaluate stdout JSON logs directly:
```bash
python3 monitoring/log_analyzer.py
```
Output is written to `monitoring/error_rate_summary.txt` with `ALARM_STATUS: OK` or `ALARM_STATUS: FIRING`.

---

## 7. Week 10 Serverless Receipt Chain Integration

Every successful `/pay` call in `kijani-staging` writes a structured receipt JSON object to `kk-payments-receipts-staging`. Sync staged receipts and trigger the downstream receipt processor and notifier chain:

```bash
for POD in \$(kubectl get pods -n kijani-staging -l app=kk-payments -o jsonpath='{.items[*].metadata.name}'); do
  kubectl exec -n kijani-staging "\$POD" -- sh -c 'ls /tmp/kk-payments-receipts-staging/*.json 2>/dev/null' | while read -r FILE; do
    kubectl cp "kijani-staging/POD:FILE" "serverless/buckets/kk-payments-receipts-staging/(basename "FILE")"
  done
done

python3 serverless/functions/receipt_chain.py
```

Processed customer notifications are written to `serverless/buckets/kk-notifications-staging/` and logged in `serverless/receipt_chain_audit.log`.
