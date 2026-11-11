# KijaniKiosk Capstone Project: Scope & Architecture Document (Track A)

### 1. Operational Problem Statement
Ten weeks ago, the **KijaniKiosk** core deployment infrastructure possessed **no automated pipelines, no repeatable Infrastructure as Code (IaC), no environment-level isolation parameters, and zero application-level telemetry metrics**, exposing the platform to extreme structural configuration drift and invisible transactional drop-offs.

### 2. Path Track Selection
* **Selected Path:** **Track A: Infrastructure-First** (Focused on multi-environment isolation, automated delivery gating, and automated log analysis telemetry).

### 3. In-Scope Components
1. **Isolated Infrastructure:** Provisioning a standalone `kijani-staging` Kubernetes namespace using **Terraform** to manage workspace state variables.
2. **Configuration Automation:** Configuring container states and setting runtime elements dynamically via an **Ansible** playbook collection.
3. **Automated Continuous Delivery:** Deploying an end-to-end **Jenkins pipeline** that automatically responds to code changes on the `main` git branch.
4. **Environment Separation:** Running `kk-payments` on an immutable core Deployment schema while toggling specific targets using decoupled **Kubernetes ConfigMaps**.
5. **Observability Harness:** Building a log-based evaluation script that monitors `kk-payments` structured logs to verify that error rates remain below a 5% threshold over a rolling 2-minute interval.

### 4. Out-of-Scope Items
* **Production Datastore High-Availability Clustering:** Multi-master database orchestration is excluded; single-replica storage assets will be utilized to limit localized performance overhead.
* **Live Bank Clearing Integrations:** External processing APIs (e.g., card networks, local payment rails) will be completely emulated via local stub endpoints.

### 5. Measurable Success Criteria
* **SC-1:** Executing the Terraform apply sequences establishes a fully partitioned `kijani-staging` cluster layer without manual shell configuration steps.
* **SC-2:** Merging a feature updates block to `main` triggers a complete Jenkins sequence, executing automated smoke tests before blocking on a manual input gate that forces the developer to type a promotion reason.
* **SC-3:** Injecting simulated malformed payload strings into the active log engine causes the automated monitoring program to record an error flag and mark the status as `FIRING` within its local summary report.

### 6. Architectural Logic Flow Layout
