"""
Anomaly detection logic, deliberately kept separate from db.py and app.py.

Why separate? This function takes a plain dict in and returns a plain list
out — no database, no Flask, no I/O. That makes it trivial to unit test
with made-up numbers, instead of needing a running database or server.
This split (pure logic vs. I/O vs. web layer) is a pattern worth being
able to explain in an interview.
"""

ANOMALY_THRESHOLD_BYTES = 10_000_000  # 10 MB — arbitrary demo threshold


def find_anomalies(traffic_totals: dict, threshold: int = ANOMALY_THRESHOLD_BYTES) -> list:
    """
    Given {ip: total_bytes, ...}, return a list of IPs whose total
    exceeds the threshold, sorted highest-usage first.
    """
    flagged = [ip for ip, total in traffic_totals.items() if total > threshold]
    flagged.sort(key=lambda ip: traffic_totals[ip], reverse=True)
    return flagged
