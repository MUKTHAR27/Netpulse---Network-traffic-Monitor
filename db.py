"""
Tiny SQLite data layer for the traffic monitor.

Keeping DB code in its own module (separate from routes in app.py) is a
standard pattern — it makes each piece independently testable and is
usually one of the first things an interviewer will ask about ("why did
you structure it this way?").
"""
import sqlite3

DB_PATH = "traffic.db"


def get_connection(db_path=None):
    # NOTE: db_path defaults to None, resolved to the module-level DB_PATH
    # *inside* the function body, not in the signature. If we wrote
    # `db_path=DB_PATH` here, Python would bind that default once, at
    # import time — so tests that reassign db.DB_PATH to a temp file
    # would be silently ignored and would keep hitting the real database.
    if db_path is None:
        db_path = DB_PATH
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # lets us access columns by name
    return conn


def init_db(db_path=None):
    conn = get_connection(db_path)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS traffic (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ip TEXT NOT NULL,
            bytes_transferred INTEGER NOT NULL,
            timestamp TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS blocked_ips (
            ip TEXT PRIMARY KEY,
            blocked_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()


def log_traffic(ip, bytes_transferred, db_path=None):
    conn = get_connection(db_path)
    conn.execute(
        "INSERT INTO traffic (ip, bytes_transferred) VALUES (?, ?)",
        (ip, bytes_transferred),
    )
    conn.commit()
    conn.close()


def get_all_traffic(db_path=None):
    conn = get_connection(db_path)
    rows = conn.execute("SELECT ip, bytes_transferred, timestamp FROM traffic").fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_traffic_totals_by_ip(db_path=None):
    """Sum bytes per IP — this is what anomaly detection runs against."""
    conn = get_connection(db_path)
    rows = conn.execute("""
        SELECT ip, SUM(bytes_transferred) AS total_bytes
        FROM traffic
        GROUP BY ip
    """).fetchall()
    conn.close()
    return {row["ip"]: row["total_bytes"] for row in rows}


def block_ip(ip, db_path=None):
    conn = get_connection(db_path)
    conn.execute("INSERT OR IGNORE INTO blocked_ips (ip) VALUES (?)", (ip,))
    conn.commit()
    conn.close()


def unblock_ip(ip, db_path=None):
    conn = get_connection(db_path)
    conn.execute("DELETE FROM blocked_ips WHERE ip = ?", (ip,))
    conn.commit()
    conn.close()


def get_blocked_ips(db_path=None):
    conn = get_connection(db_path)
    rows = conn.execute("SELECT ip FROM blocked_ips").fetchall()
    conn.close()
    return {row["ip"] for row in rows}


def clear_all(db_path=None):
    """Used by tests to reset state between runs."""
    conn = get_connection(db_path)
    conn.execute("DELETE FROM traffic")
    conn.execute("DELETE FROM blocked_ips")
    conn.commit()
    conn.close()
