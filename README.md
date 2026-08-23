# Network Traffic Monitor & Anomaly Detector

A small REST API that logs network traffic events, flags IPs whose
cumulative usage crosses a threshold, and supports blocking/unblocking
IPs — with a full pytest test suite (18 tests, 93% coverage).

#
| File | Responsibility |
|---|---|
| `db.py` | All database reads/writes (SQLite). Nothing here knows about HTTP. |
| `detector.py` | Pure anomaly-detection logic. Takes a dict in, returns a list out. No database, no Flask. |
| `app.py` | Flask routes. Parses requests, calls `db.py`/`detector.py`, returns JSON. No business logic lives here. |


## Setup & run

```bash
pip install -r requirements.txt
python app.py          # starts the API on http://127.0.0.1:5000
```

##For running tests

```bash
pytest -v                              # run all 18 tests
pytest -v --cov=app --cov=db --cov=detector --cov-report=term-missing
```

## API reference

| Method | Route | Body | Purpose |
|---|---|---|---|
| POST | `/api/traffic` | `{"ip": "1.2.3.4", "bytes": 5000}` | Log a traffic event |
| GET | `/api/stats` | — | List all traffic (excludes blocked IPs) |
| GET | `/api/anomalies` | — | List IPs over the 10MB threshold |
| POST | `/api/block` | `{"ip": "1.2.3.4"}` | Block an IP |
| POST | `/api/unblock` | `{"ip": "1.2.3.4"}` | Unblock an IP |


