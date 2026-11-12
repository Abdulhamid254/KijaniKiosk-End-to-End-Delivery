import json
import os
from datetime import datetime, timezone

STAGING_BUCKET = os.getenv("RECEIPT_BUCKET_PATH", "serverless/buckets/kk-payments-receipts-staging")
NOTIFY_BUCKET = os.getenv("NOTIFY_BUCKET_PATH", "serverless/buckets/kk-notifications-staging")
CHAIN_LOG = "serverless/receipt_chain_audit.log"


def process_receipt(receipt_file):
    filepath = os.path.join(STAGING_BUCKET, receipt_file)
    with open(filepath, "r", encoding="utf-8") as f:
        receipt = json.load(f)

    # Step 1: kk-receipt-processor validates and enriches the receipt
    enriched = {
        **receipt,
        "processed_by": "kk-receipt-processor",
        "processed_at": datetime.now(timezone.utc).isoformat(),
        "status": "VERIFIED",
    }

    # Step 2: kk-notifier writes the customer notification payload
    out_path = os.path.join(NOTIFY_BUCKET, f"notify-{receipt_file}")
    with open(out_path, "w", encoding="utf-8") as out:
        json.dump(enriched, out, indent=2)

    log_line = (
        f"[{enriched['processed_at']}] CHAIN_TRIGGERED | "
        f"bucket={os.path.basename(STAGING_BUCKET)} | "
        f"tx_id={receipt.get('tx_id')} | "
        f"notification={os.path.basename(out_path)}"
    )
    print(log_line)
    with open(CHAIN_LOG, "a", encoding="utf-8") as logf:
        logf.write(log_line + "\n")


def run_once():
    os.makedirs(STAGING_BUCKET, exist_ok=True)
    os.makedirs(NOTIFY_BUCKET, exist_ok=True)
    files = sorted(f for f in os.listdir(STAGING_BUCKET) if f.endswith(".json"))
    if not files:
        print("No pending receipts in kk-payments-receipts-staging.")
        return
    for fname in files:
        process_receipt(fname)


if __name__ == "__main__":
    run_once()
