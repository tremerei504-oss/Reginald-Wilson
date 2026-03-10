"""
shaka_db.py — Agent Shaka Database Layer

Stores every lead interaction and tracks outcomes so Shaka gets smarter
over time by learning from successful conversions.
"""

import sqlite3
import logging
from datetime import datetime
from typing import Optional

log = logging.getLogger(__name__)


def get_connection(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: str) -> None:
    """Create tables if they don't exist."""
    with get_connection(db_path) as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS leads (
                id               INTEGER PRIMARY KEY AUTOINCREMENT,
                message_id       TEXT UNIQUE,          -- Email Message-ID header (dedup)
                email            TEXT NOT NULL,
                name             TEXT,
                phone            TEXT,
                subject          TEXT,
                raw_body         TEXT,
                property_address TEXT,
                inquiry_type     TEXT,
                source           TEXT DEFAULT 'estatesales.net',
                received_at      TEXT DEFAULT (datetime('now')),
                responded_at     TEXT,
                email_subject    TEXT,
                email_response   TEXT,
                sms_response     TEXT,
                status           TEXT DEFAULT 'new',
                -- status: new | responded | engaged | converted | closed | no_response
                notes            TEXT
            );

            CREATE TABLE IF NOT EXISTS response_outcomes (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                lead_id      INTEGER NOT NULL REFERENCES leads(id),
                outcome      TEXT NOT NULL,
                -- outcome: replied | called | appointment | converted | no_response
                recorded_at  TEXT DEFAULT (datetime('now')),
                notes        TEXT
            );
        """)
    log.info("Database initialized at %s", db_path)


def is_duplicate(db_path: str, message_id: str) -> bool:
    """Return True if we've already processed this email."""
    with get_connection(db_path) as conn:
        row = conn.execute(
            "SELECT 1 FROM leads WHERE message_id = ?", (message_id,)
        ).fetchone()
    return row is not None


def save_lead(
    db_path: str,
    message_id: str,
    email: str,
    name: str,
    phone: Optional[str],
    subject: str,
    raw_body: str,
    property_address: Optional[str],
    inquiry_type: Optional[str],
    source: str,
) -> int:
    """Insert a new lead and return its row ID."""
    with get_connection(db_path) as conn:
        cur = conn.execute(
            """INSERT INTO leads
               (message_id, email, name, phone, subject, raw_body,
                property_address, inquiry_type, source)
               VALUES (?,?,?,?,?,?,?,?,?)""",
            (message_id, email, name, phone, subject, raw_body,
             property_address, inquiry_type, source),
        )
        lead_id = cur.lastrowid
    log.info("Saved lead #%d — %s <%s>", lead_id, name, email)
    return lead_id


def mark_responded(
    db_path: str,
    lead_id: int,
    email_subject: str,
    email_response: str,
    sms_response: str,
) -> None:
    with get_connection(db_path) as conn:
        conn.execute(
            """UPDATE leads
               SET responded_at = datetime('now'),
                   email_subject = ?,
                   email_response = ?,
                   sms_response = ?,
                   status = 'responded'
               WHERE id = ?""",
            (email_subject, email_response, sms_response, lead_id),
        )
    log.info("Marked lead #%d as responded", lead_id)


def update_status(db_path: str, lead_id: int, status: str, notes: str = "") -> None:
    with get_connection(db_path) as conn:
        conn.execute(
            "UPDATE leads SET status = ?, notes = ? WHERE id = ?",
            (status, notes, lead_id),
        )


def record_outcome(
    db_path: str, lead_id: int, outcome: str, notes: str = ""
) -> None:
    with get_connection(db_path) as conn:
        conn.execute(
            "INSERT INTO response_outcomes (lead_id, outcome, notes) VALUES (?,?,?)",
            (lead_id, outcome, notes),
        )
        # Also update the lead status
        status_map = {
            "replied": "engaged",
            "called": "engaged",
            "appointment": "engaged",
            "converted": "converted",
            "no_response": "no_response",
        }
        new_status = status_map.get(outcome, "engaged")
        conn.execute(
            "UPDATE leads SET status = ? WHERE id = ?",
            (new_status, lead_id),
        )
    log.info("Recorded outcome '%s' for lead #%d", outcome, lead_id)


def get_successful_examples(db_path: str, limit: int = 5) -> list[dict]:
    """
    Fetch the best past responses — used as few-shot examples so Shaka
    keeps improving with every successful conversion.

    'Successful' = leads that converted or engaged after our response.
    """
    with get_connection(db_path) as conn:
        rows = conn.execute(
            """SELECT l.name, l.email_response, l.sms_response,
                      l.inquiry_type, l.status
               FROM leads l
               WHERE l.status IN ('converted', 'engaged')
                 AND l.email_response IS NOT NULL
               ORDER BY
                 CASE l.status
                   WHEN 'converted' THEN 1
                   WHEN 'engaged'   THEN 2
                   ELSE 3
                 END,
                 l.responded_at DESC
               LIMIT ?""",
            (limit,),
        ).fetchall()
    return [dict(r) for r in rows]


def get_all_leads(db_path: str) -> list[dict]:
    with get_connection(db_path) as conn:
        rows = conn.execute(
            """SELECT id, name, email, phone, status, received_at,
                      responded_at, subject, inquiry_type
               FROM leads ORDER BY received_at DESC"""
        ).fetchall()
    return [dict(r) for r in rows]


def get_lead_by_id(db_path: str, lead_id: int) -> Optional[dict]:
    with get_connection(db_path) as conn:
        row = conn.execute(
            "SELECT * FROM leads WHERE id = ?", (lead_id,)
        ).fetchone()
    return dict(row) if row else None


def get_stats(db_path: str) -> dict:
    with get_connection(db_path) as conn:
        total      = conn.execute("SELECT COUNT(*) FROM leads").fetchone()[0]
        responded  = conn.execute("SELECT COUNT(*) FROM leads WHERE status != 'new'").fetchone()[0]
        engaged    = conn.execute("SELECT COUNT(*) FROM leads WHERE status = 'engaged'").fetchone()[0]
        converted  = conn.execute("SELECT COUNT(*) FROM leads WHERE status = 'converted'").fetchone()[0]
    return {
        "total": total,
        "responded": responded,
        "engaged": engaged,
        "converted": converted,
        "response_rate": f"{(responded/total*100):.1f}%" if total else "N/A",
        "conversion_rate": f"{(converted/total*100):.1f}%" if total else "N/A",
    }
