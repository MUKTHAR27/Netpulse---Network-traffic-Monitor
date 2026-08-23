# Network Traffic Monitor & Anomaly Detector

A small REST API that logs network traffic events, flags IPs whose
cumulative usage crosses a threshold, and supports blocking/unblocking
IPs — with a full pytest test suite (18 tests, 93% coverage).

## Why it's structured this way

Three files, three jobs — this separation is worth explaining out loud in
an interview if asked "why did you organize it like this?":

| File | Responsibility |
|---|---|
| `db.py` | All database reads/writes (SQLite). Nothing here knows about HTTP. |
| `detector.py` | Pure anomaly-detection logic. Takes a dict in, returns a list out. No database, no Flask. |
| `app.py` | Flask routes. Parses requests, calls `db.py`/`detector.py`, returns JSON. No business logic lives here. |

Keeping logic out of the routes is what makes each piece independently
testable — `test_detector.py` needs zero setup (no DB, no server) because
`detector.py` has no side effects.

## Setup & run

```bash
pip install -r requirements.txt
python app.py          # starts the API on http://127.0.0.1:5000
```

## Run the tests

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

## A real bug this test suite caught

Worth knowing this story for an interview — it's a genuinely good answer
to "tell me about a bug you found while testing."

The first version of `db.py` had functions like:

```python
def log_traffic(ip, bytes_transferred, db_path=DB_PATH):
```

That looks fine, but Python evaluates default argument values **once, at
import time** — not every time the function is called. So when the test
suite reassigned `db.DB_PATH` to point at a temporary test database (to
avoid polluting the real one), the already-defined default in
`log_traffic` didn't notice — it kept pointing at the original path,
and every insert failed with `no such table: traffic`.

Fix: default to `db_path=None`, then resolve it to `DB_PATH` **inside**
the function body, so it re-reads the current value on every call.

This is exactly the kind of thing tests are for — the bug was invisible
by inspection but immediately obvious the moment real test cases ran
against it.

## Test suite structure

- `test_detector.py` — unit tests for pure logic (thresholds, sorting,
  boundary case at exactly the threshold, empty input).
- `test_app.py` — API-level tests using Flask's test client against a
  temporary SQLite file per test (via pytest's `tmp_path` fixture), so
  tests never touch the real database and never leak state into each
  other. Covers happy paths and negative/invalid-input cases for every
  route.

## Next steps if you want to extend this

- Add a `/api/traffic/<ip>` route to get one IP's full history.
- Add input validation for malformed IP strings.
- Swap the fixed 10MB threshold for a per-IP baseline (e.g. flag anything
  3x above that IP's rolling average).
