"""SQLite helpers (stdlib sqlite3). Parameterised queries only."""
import json
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

from models import AI_STATUSES, CATEGORIES, PRIORITIES, STATUSES, VERIFICATION

DEFAULT_DB = Path(__file__).resolve().parent / "campusfix.db"


def db_path() -> str:
    return os.getenv("DATABASE_PATH") or str(DEFAULT_DB)


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


@contextmanager
def get_conn():
    conn = sqlite3.connect(db_path())
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _in(values) -> str:
    return ",".join(f"'{v}'" for v in values)


def init_db() -> None:
    with get_conn() as conn:
        conn.execute(f"""
            CREATE TABLE IF NOT EXISTS tickets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                location TEXT NOT NULL,
                category TEXT NOT NULL CHECK (category IN ({_in(CATEGORIES)})),
                priority TEXT NOT NULL CHECK (priority IN ({_in(PRIORITIES)})),
                priority_reason TEXT NOT NULL,
                evidence_summary TEXT NOT NULL,
                verification_status TEXT NOT NULL CHECK (verification_status IN ({_in(VERIFICATION)})),
                recommended_next_step TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'open' CHECK (status IN ({_in(STATUSES)})),
                image_path TEXT,
                ai_provider TEXT,
                ai_status TEXT NOT NULL CHECK (ai_status IN ({_in(AI_STATUSES)})),
                observations_json TEXT NOT NULL DEFAULT '[]',
                assumptions_json TEXT NOT NULL DEFAULT '[]',
                image_analyzed INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)


def ping() -> None:
    with get_conn() as conn:
        conn.execute("SELECT 1")


def _to_ticket(row: sqlite3.Row) -> dict:
    return {
        "id": row["id"],
        "title": row["title"],
        "description": row["description"],
        "location": row["location"],
        "category": row["category"],
        "priority": row["priority"],
        "priority_reason": row["priority_reason"],
        "evidence_summary": row["evidence_summary"],
        "verification_status": row["verification_status"],
        "recommended_next_step": row["recommended_next_step"],
        "status": row["status"],
        "image_url": f"/uploads/{row['image_path']}" if row["image_path"] else None,
        "ai_provider": row["ai_provider"],
        "created_at": row["created_at"],
        "ai_status": row["ai_status"],
        "observations": json.loads(row["observations_json"] or "[]"),
        "assumptions": json.loads(row["assumptions_json"] or "[]"),
        "image_analyzed": bool(row["image_analyzed"]),
        "updated_at": row["updated_at"],
    }


def create_ticket(f: dict) -> int:
    now = utc_now()
    with get_conn() as conn:
        cur = conn.execute(
            """INSERT INTO tickets (title, description, location, category, priority, priority_reason,
                   evidence_summary, verification_status, recommended_next_step, status, image_path,
                   ai_provider, ai_status, observations_json, assumptions_json, image_analyzed,
                   created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'open', ?, ?, ?, ?, ?, ?, ?, ?)""",
            (f["title"], f["description"], f["location"], f["category"], f["priority"],
             f["priority_reason"], f["evidence_summary"], f["verification_status"],
             f["recommended_next_step"], f.get("image_path"), f.get("ai_provider"), f["ai_status"],
             json.dumps(f["observations"]), json.dumps(f["assumptions"]),
             1 if f["image_analyzed"] else 0, now, now),
        )
        return cur.lastrowid


def get_ticket(ticket_id: int):
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,)).fetchone()
    return _to_ticket(row) if row else None


def list_tickets(status=None, priority=None) -> list[dict]:
    sql, params, where = "SELECT * FROM tickets", [], []
    if status:
        where.append("status = ?")
        params.append(status)
    if priority:
        where.append("priority = ?")
        params.append(priority)
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY created_at DESC, id DESC"
    with get_conn() as conn:
        rows = conn.execute(sql, params).fetchall()
    return [_to_ticket(r) for r in rows]


def update_ticket_status(ticket_id: int, status: str):
    with get_conn() as conn:
        cur = conn.execute("UPDATE tickets SET status = ?, updated_at = ? WHERE id = ?",
                           (status, utc_now(), ticket_id))
        if cur.rowcount == 0:
            return None
    return get_ticket(ticket_id)
