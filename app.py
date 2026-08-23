"""
Network Traffic Monitor & Anomaly Detector — Flask API.

Routes are intentionally thin: they parse the request, call db.py or
detector.py, and return JSON. Business logic lives in those two modules,
not here. This is what lets each piece be tested in isolation.
"""
from flask import Flask, jsonify, request
import db
from detector import find_anomalies

app = Flask(__name__)


@app.post("/api/traffic")
def log_traffic():
    """Record a traffic event. Body: {"ip": "1.2.3.4", "bytes": 5000}"""
    data = request.get_json(silent=True) or {}
    ip = data.get("ip")
    bytes_transferred = data.get("bytes")

    if not ip or bytes_transferred is None:
        return jsonify({"error": "ip and bytes are required"}), 400
    if not isinstance(bytes_transferred, (int, float)) or bytes_transferred < 0:
        return jsonify({"error": "bytes must be a non-negative number"}), 400

    db.log_traffic(ip, bytes_transferred)
    return jsonify({"logged": {"ip": ip, "bytes": bytes_transferred}}), 201


@app.get("/api/stats")
def get_stats():
    """Return raw traffic log, excluding any blocked IPs."""
    blocked = db.get_blocked_ips()
    all_traffic = db.get_all_traffic()
    visible = [entry for entry in all_traffic if entry["ip"] not in blocked]
    return jsonify(visible), 200


@app.get("/api/anomalies")
def get_anomalies():
    """Return IPs whose cumulative traffic exceeds the anomaly threshold."""
    totals = db.get_traffic_totals_by_ip()
    flagged = find_anomalies(totals)
    return jsonify({"anomalies": flagged}), 200


@app.post("/api/block")
def block_ip():
    data = request.get_json(silent=True) or {}
    ip = data.get("ip")
    if not ip:
        return jsonify({"error": "ip is required"}), 400
    db.block_ip(ip)
    return jsonify({"blocked": ip}), 200


@app.post("/api/unblock")
def unblock_ip():
    data = request.get_json(silent=True) or {}
    ip = data.get("ip")
    if not ip:
        return jsonify({"error": "ip is required"}), 400
    db.unblock_ip(ip)
    return jsonify({"unblocked": ip}), 200


if __name__ == "__main__":
    db.init_db()
    app.run(debug=True)
