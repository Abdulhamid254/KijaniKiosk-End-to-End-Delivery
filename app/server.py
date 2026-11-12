import json
import os
import threading
import uuid
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

DB_HOST = os.getenv("DB_HOST", "localhost")
RECEIPT_BUCKET = os.getenv("RECEIPT_BUCKET", "kk-payments-receipts-staging")
LOCAL_BUCKET_DIR = f"/tmp/{RECEIPT_BUCKET}"

METRICS_LOCK = threading.Lock()
REQUEST_COUNTS = {"200": 0, "500": 0}


def record_metric(status_code):
    with METRICS_LOCK:
        code_str = str(status_code)
        REQUEST_COUNTS[code_str] = REQUEST_COUNTS.get(code_str, 0) + 1


def log_event(level, status, code, tx_id, message):
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "service": "kk-payments",
        "db_host": DB_HOST,
        "receipt_bucket": RECEIPT_BUCKET,
        "tx_id": tx_id,
        "level": level,
        "status": status,
        "code": code,
        "message": message,
    }
    print(json.dumps(entry), flush=True)


def write_receipt_to_bucket(tx_id, amount=1500):
    os.makedirs(LOCAL_BUCKET_DIR, exist_ok=True)
    receipt_payload = {
        "tx_id": tx_id,
        "amount": amount,
        "currency": "KES",
        "bucket": RECEIPT_BUCKET,
        "db_host": DB_HOST,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    file_path = os.path.join(LOCAL_BUCKET_DIR, f"{tx_id}.json")
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(receipt_payload, f)
    return receipt_payload


class PaymentHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        return

    def do_GET(self):
        parsed = urlparse(self.path)
        query = parse_qs(parsed.query)

        if parsed.path == "/healthz":
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"ok")
            return

        if parsed.path == "/metrics":
            with METRICS_LOCK:
                lines = [
                    "# HELP kk_payments_requests_total Total HTTP payment requests",
                    "# TYPE kk_payments_requests_total counter",
                ]
                for code, count in REQUEST_COUNTS.items():
                    lines.append(f'kk_payments_requests_total{{app="kk-payments",status="{code}"}} {count}')
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; version=0.0.4")
            self.end_headers()
            self.wfile.write(("\n".join(lines) + "\n").encode())
            return

        if parsed.path == "/pay":
            tx_id = f"tx-{uuid.uuid4().hex[:8]}"
            if query.get("fail") == ["true"]:
                record_metric(500)
                log_event("ERROR", "error", 500, tx_id, "Payment gateway timeout")
                self.send_response(500)
                self.end_headers()
                self.wfile.write(json.dumps({"tx_id": tx_id, "status": "error"}).encode())
                return

            record_metric(200)
            payload = write_receipt_to_bucket(tx_id)
            log_event("INFO", "success", 200, tx_id, f"Receipt written to {RECEIPT_BUCKET}/{tx_id}.json")
            self.send_response(200)
            self.end_headers()
            self.wfile.write(json.dumps(payload).encode())
            return

        self.send_response(404)
        self.end_headers()


if __name__ == "__main__":
    server = HTTPServer(("0.0.0.0", 8080), PaymentHandler)
    log_event("INFO", "startup", 200, "init", f"kk-payments listening on 8080 | target_bucket={RECEIPT_BUCKET}")
    server.serve_forever()
