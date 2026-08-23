"""
API-level tests for app.py's routes.

Each test gets a fresh temp SQLite file (via the `client` fixture below),
so tests never leak state into each other and never touch your real
traffic.db. This is the standard way to test a Flask app that hits a
real database instead of mocking it out entirely.
"""
import os
import pytest
import db
import app as app_module


@pytest.fixture
def client(tmp_path):
    test_db_path = str(tmp_path / "test_traffic.db")
    db.DB_PATH = test_db_path  # both app.py and this file import the same db module
    db.init_db(test_db_path)

    app_module.app.config["TESTING"] = True
    with app_module.app.test_client() as test_client:
        yield test_client

    if os.path.exists(test_db_path):
        os.remove(test_db_path)


class TestLogTrafficEndpoint:
    def test_logs_valid_traffic_returns_201(self, client):
        response = client.post("/api/traffic", json={"ip": "10.0.0.1", "bytes": 5000})
        assert response.status_code == 201
        assert response.get_json()["logged"]["ip"] == "10.0.0.1"

    def test_missing_ip_returns_400(self, client):
        response = client.post("/api/traffic", json={"bytes": 5000})
        assert response.status_code == 400

    def test_missing_bytes_returns_400(self, client):
        response = client.post("/api/traffic", json={"ip": "10.0.0.1"})
        assert response.status_code == 400

    def test_negative_bytes_returns_400(self, client):
        response = client.post("/api/traffic", json={"ip": "10.0.0.1", "bytes": -100})
        assert response.status_code == 400

    def test_non_numeric_bytes_returns_400(self, client):
        response = client.post("/api/traffic", json={"ip": "10.0.0.1", "bytes": "a lot"})
        assert response.status_code == 400


class TestStatsEndpoint:
    def test_returns_logged_traffic(self, client):
        client.post("/api/traffic", json={"ip": "10.0.0.1", "bytes": 5000})
        response = client.get("/api/stats")
        ips = [entry["ip"] for entry in response.get_json()]
        assert "10.0.0.1" in ips

    def test_excludes_blocked_ip(self, client):
        client.post("/api/traffic", json={"ip": "10.0.0.1", "bytes": 5000})
        client.post("/api/block", json={"ip": "10.0.0.1"})
        response = client.get("/api/stats")
        ips = [entry["ip"] for entry in response.get_json()]
        assert "10.0.0.1" not in ips


class TestAnomaliesEndpoint:
    def test_flags_high_traffic_ip(self, client):
        client.post("/api/traffic", json={"ip": "10.0.0.9", "bytes": 20_000_000})
        response = client.get("/api/anomalies")
        assert "10.0.0.9" in response.get_json()["anomalies"]

    def test_sums_multiple_events_before_flagging(self, client):
        """Two 6MB events from the same IP should combine to trigger the 10MB threshold."""
        client.post("/api/traffic", json={"ip": "10.0.0.2", "bytes": 6_000_000})
        client.post("/api/traffic", json={"ip": "10.0.0.2", "bytes": 6_000_000})
        response = client.get("/api/anomalies")
        assert "10.0.0.2" in response.get_json()["anomalies"]


class TestBlockUnblockEndpoints:
    def test_block_missing_ip_returns_400(self, client):
        response = client.post("/api/block", json={})
        assert response.status_code == 400

    def test_unblock_missing_ip_returns_400(self, client):
        response = client.post("/api/unblock", json={})
        assert response.status_code == 400

    def test_block_then_unblock_restores_visibility(self, client):
        client.post("/api/traffic", json={"ip": "10.0.0.5", "bytes": 1000})
        client.post("/api/block", json={"ip": "10.0.0.5"})
        client.post("/api/unblock", json={"ip": "10.0.0.5"})
        response = client.get("/api/stats")
        ips = [entry["ip"] for entry in response.get_json()]
        assert "10.0.0.5" in ips
