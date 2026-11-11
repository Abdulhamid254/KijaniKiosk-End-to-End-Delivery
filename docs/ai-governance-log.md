# KijaniKiosk AI Tooling Governance Log

### Entry 001: Jenkinsfile Multi-Environment Gating Structure
* **Date of Generation:** 2026-11-11
* **Target Component:** `jenkins/Jenkinsfile`
* **AI Tool Utilized:** LLM Assistant
* **Specific Prompt Used:** "Generate a declarative Jenkinsfile for local Minikube deployment. Include an automated staging curl smoke test, and a manual approval gate that forces the operator to input a text reason before deploying to production."
* **What the AI Produced:** Generated a standard linear Jenkins declarative pipeline with an input step.
* **What the AI Got Wrong / Omitted:** The generated code completely omitted the mandatory parameter required to log and bind the submitter's written text reason to a persistent environment variable (`env.APPROVE_REASON`), which would have allowed silent approvals without an audit trail.
* **Human Reviewer Modifications:** Manually refactored the input stage block to explicitly include the submitterParameter and captured the input text into a global variable, printing it directly to the console logs for validation.
* **Governance Control Reference:** Attests to Control 02: "Audit Trail and Promotion Path Integrity Verification".

---

### Entry 002: Option B Log Telemetry Engine
* **Date of Generation:** 2026-11-11
* **Target Component:** `monitoring/log_analyzer.py`
* **AI Tool Utilized:** LLM Assistant
* **Specific Prompt Used:** "Create a lightweight Python script that parses structured JSON logs for a service, calculates the error rate over a moving window, and triggers an alert status if it crosses a 5% threshold."
* **What the AI Produced:** A basic file reader that parsed lines and tracked total exception keys.
* **What the AI Got Wrong / Omitted:** The AI script lacked safety exceptions for malformed or unparseable non-JSON text lines, which would cause the entire monitoring thread to crash instantly if a standard plain-text string entered the log buffer.
* **Human Reviewer Modifications:** Wrapped the JSON loader inside a robust `try-except ValueError` block to skip corrupt lines gracefully and ensure continuous monitoring availability.
* **Governance Control Reference:** Attests to Control 05: "Service Health Observability and Signals Verification".
