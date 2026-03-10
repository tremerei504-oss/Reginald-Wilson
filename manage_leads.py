#!/usr/bin/env python3
"""
manage_leads.py — Agent Shaka Lead Manager
==========================================
Reginald's command-line tool to:
  • View incoming leads and their status
  • Mark leads as converted / engaged / no-response
  • See stats and Shaka's improving conversion rate
  • Manually trigger re-processing of a lead

The more you mark leads as "converted", the smarter Shaka gets —
those successful responses become training examples for future leads.

Usage:
    python manage_leads.py list              # Show all leads
    python manage_leads.py list --status new # Filter by status
    python manage_leads.py view 42           # See full lead #42
    python manage_leads.py update 42 converted "Signed contract today!"
    python manage_leads.py stats             # Shaka's performance report
"""

import argparse
import sys
import os
from dotenv import load_dotenv

load_dotenv()

import shaka_db

DB_PATH = os.getenv("DB_PATH", "agent_shaka.db")

VALID_STATUSES = ["new", "responded", "engaged", "converted", "closed", "no_response"]

# ── Display helpers ───────────────────────────────────────────────────────────

def _row(label: str, value: str, width: int = 18) -> str:
    return f"  {label:<{width}} {value}"


def print_lead_table(leads: list[dict]) -> None:
    if not leads:
        print("  No leads found.")
        return
    header = f"{'ID':>4}  {'Name':<22}  {'Email':<32}  {'Status':<12}  {'Received':<19}"
    print("\n" + header)
    print("  " + "─" * (len(header) - 2))
    for l in leads:
        received = (l.get("received_at") or "")[:19]
        print(
            f"  {l['id']:>4}  "
            f"{(l.get('name') or '—'):<22}  "
            f"{(l.get('email') or '—'):<32}  "
            f"{(l.get('status') or '—'):<12}  "
            f"{received:<19}"
        )
    print()


def print_lead_detail(lead: dict) -> None:
    print("\n" + "━" * 60)
    print(f"  LEAD #{lead['id']}")
    print("━" * 60)
    print(_row("Name:",            lead.get("name")            or "—"))
    print(_row("Email:",           lead.get("email")           or "—"))
    print(_row("Phone:",           lead.get("phone")           or "—"))
    print(_row("Status:",          lead.get("status")          or "—"))
    print(_row("Source:",          lead.get("source")          or "—"))
    print(_row("Inquiry:",         lead.get("inquiry_type")    or "—"))
    print(_row("Property:",        lead.get("property_address") or "—"))
    print(_row("Received:",        (lead.get("received_at")    or "—")[:19]))
    print(_row("Responded:",       (lead.get("responded_at")   or "never")[:19]))
    print(_row("Subject:",         lead.get("subject")         or "—"))
    if lead.get("notes"):
        print(_row("Notes:",       lead["notes"]))
    if lead.get("email_response"):
        print("\n  ── Email Shaka Sent ──")
        print(f"  Subject: {lead.get('email_subject', '')}")
        for line in (lead.get("email_response") or "").splitlines():
            print(f"  {line}")
    if lead.get("sms_response"):
        print("\n  ── SMS Shaka Sent ──")
        print(f"  {lead.get('sms_response', '')}")
    print("━" * 60 + "\n")


def print_stats(stats: dict) -> None:
    print("\n" + "━" * 40)
    print("  Agent Shaka — Performance Report")
    print("━" * 40)
    print(_row("Total leads:", str(stats["total"])))
    print(_row("Responded:",   str(stats["responded"])))
    print(_row("Engaged:",     str(stats["engaged"])))
    print(_row("Converted:",   str(stats["converted"])))
    print(_row("Response rate:",    stats["response_rate"]))
    print(_row("Conversion rate:",  stats["conversion_rate"]))
    print("━" * 40)
    print("\n  Tip: Mark leads as 'converted' to teach Shaka what works!\n")


# ── Commands ──────────────────────────────────────────────────────────────────

def cmd_list(args) -> None:
    leads = shaka_db.get_all_leads(DB_PATH)
    if args.status:
        leads = [l for l in leads if l.get("status") == args.status]
    print_lead_table(leads)
    print(f"  Showing {len(leads)} lead(s).  Run 'python manage_leads.py view <ID>' for details.\n")


def cmd_view(args) -> None:
    lead = shaka_db.get_lead_by_id(DB_PATH, args.id)
    if not lead:
        print(f"  Lead #{args.id} not found.")
        sys.exit(1)
    print_lead_detail(lead)


def cmd_update(args) -> None:
    if args.status not in VALID_STATUSES:
        print(f"  Invalid status '{args.status}'. Choose from: {', '.join(VALID_STATUSES)}")
        sys.exit(1)

    lead = shaka_db.get_lead_by_id(DB_PATH, args.id)
    if not lead:
        print(f"  Lead #{args.id} not found.")
        sys.exit(1)

    notes = args.notes or ""
    shaka_db.update_status(DB_PATH, args.id, args.status, notes)

    # Also record as a response outcome for the learning system
    outcome_map = {
        "engaged":     "replied",
        "converted":   "converted",
        "no_response": "no_response",
        "closed":      "converted",
    }
    if args.status in outcome_map:
        shaka_db.record_outcome(DB_PATH, args.id, outcome_map[args.status], notes)

    print(f"\n  ✓ Lead #{args.id} ({lead.get('name', '—')}) updated → {args.status}")
    if args.status == "converted":
        print("  🧠 Shaka will use this as a training example for future leads!\n")
    else:
        print()


def cmd_stats(args) -> None:
    stats = shaka_db.get_stats(DB_PATH)
    print_stats(stats)


# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        prog="manage_leads",
        description="Agent Shaka Lead Manager — Treme Estate Sales",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # list
    p_list = sub.add_parser("list", help="List all leads")
    p_list.add_argument("--status", choices=VALID_STATUSES, help="Filter by status")
    p_list.set_defaults(func=cmd_list)

    # view
    p_view = sub.add_parser("view", help="View full details for a lead")
    p_view.add_argument("id", type=int, help="Lead ID")
    p_view.set_defaults(func=cmd_view)

    # update
    p_update = sub.add_parser("update", help="Update a lead's status (trains Shaka!)")
    p_update.add_argument("id",     type=int,              help="Lead ID")
    p_update.add_argument("status", choices=VALID_STATUSES, help="New status")
    p_update.add_argument("notes",  nargs="?", default="", help="Optional notes")
    p_update.set_defaults(func=cmd_update)

    # stats
    p_stats = sub.add_parser("stats", help="View Shaka's performance stats")
    p_stats.set_defaults(func=cmd_stats)

    args = parser.parse_args()

    # Ensure DB exists
    shaka_db.init_db(DB_PATH)

    args.func(args)


if __name__ == "__main__":
    main()
