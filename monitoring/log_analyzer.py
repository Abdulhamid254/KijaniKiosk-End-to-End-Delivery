import json
import os
import subprocess
from datetime import datetime, timezone

NAMESPACE = os.getenv("KK_NAMESPACE", "kijani-staging")
APP_LABEL = os.getenv("KK_APP_LABEL", "app=kk-payments")
MONITOR_OUTPUT = os.getenv("KK_MONITOR_OUTPUT", "monitoring/error_rate_summary.txt")
WINDOW_SECONDS = 120
ERROR_THRESHOLD_PERCENT = 5.0


def fetch_k8s_logs():
    cmd = [
        "kubectl", "logs",
        "-n", NAMESPACE,
        "-l", APP_LABEL,
        f"--since={WINDOW_SECONDS}s",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise RuntimeError(f"kubectl logs failed: {result.stderr.strip()}")
    return result.stdout.splitlines()


def analyze_logs():
    lines = fetch_k8s_logs()
    total_count = 0
    error_count = 0

    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            entry = json.loads(line)
        except ValueError:
            continue

        total_count += 1
        status = str(entry.get("status", "")).lower()
        code = int(entry.get("code", 200))

        if status == "error" or code >= 500:
            error_count += 1

    error_rate = (error_count / total_count * 100.0) if total_count > 0 else 0.0
    alarm_status = "FIRING" if error_rate > ERROR_THRESHOLD_PERCENT else "OK"
    write_report(total_count, error_count, error_rate, alarm_status)


def write_report(total, errors, rate, status):
    os.makedirs(os.path.dirname(MONITOR_OUTPUT), exist_ok=True)
    timestamp_human = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    report = (
        f"SERVICE: kk-payments\n"
        f"NAMESPACE: {NAMESPACE}\n"
        f"TIMESTAMP: {timestamp_human}\n"
        f"WINDOW: 2m ({WINDOW_SECONDS}s)\n"
        f"TOTAL_REQUESTS: {total}\n"
        f"TOTAL_ERRORS: {errors}\n"
        f"ERROR_RATE: {rate:.2f}%\n"
        f"THRESHOLD: {ERROR_THRESHOLD_PERCENT:.1f}%\n"
        f"ALARM_STATUS: {status}\n"
    )

    with open(MONITOR_OUTPUT, "w", encoding="utf-8") as out:
        out.write(report)

    print(report)


if __name__ == "__main__":
    analyze_logs()
