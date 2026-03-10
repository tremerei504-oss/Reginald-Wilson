#!/usr/bin/env python3
"""
Agent Shaka — Treme Estate Sales Lead Response System
======================================================
Monitors your inbox for EstateSales.net leads and responds via email
AND text within ~10 seconds using Claude AI.

Usage:
    python agent_shaka.py            # Run the live monitoring loop
    python agent_shaka.py --test     # Send a test lead through the full pipeline

Requirements: copy .env.example → .env and fill in your credentials.
"""

import os
import re
import time
import imaplib
import smtplib
import logging
import argparse
import textwrap
from email import message_from_bytes
from email.header import decode_header
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

import anthropic
from twilio.rest import Client as TwilioClient
from dotenv import load_dotenv

import shaka_db
import shaka_brain

load_dotenv()

# ── Logging ──────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("agent_shaka.log"),
        logging.StreamHandler(),
    ],
)
log = logging.getLogger(__name__)

# ── Config ───────────────────────────────────────────────────────────────────

def _require(key: str) -> str:
    val = os.getenv(key)
    if not val:
        raise EnvironmentError(f"Missing required env var: {key}")
    return val


def load_config() -> dict:
    return {
        "anthropic_api_key":    _require("ANTHROPIC_API_KEY"),
        "twilio_sid":           _require("TWILIO_ACCOUNT_SID"),
        "twilio_token":         _require("TWILIO_AUTH_TOKEN"),
        "twilio_from":          _require("TWILIO_FROM_NUMBER"),
        "imap_host":            os.getenv("IMAP_HOST", "imap.gmail.com"),
        "imap_email":           _require("IMAP_EMAIL"),
        "imap_password":        _require("IMAP_PASSWORD"),
        "smtp_host":            os.getenv("SMTP_HOST", "smtp.gmail.com"),
        "smtp_port":            int(os.getenv("SMTP_PORT", "587")),
        "smtp_email":           _require("SMTP_EMAIL"),
        "smtp_password":        _require("SMTP_PASSWORD"),
        "reginald_phone":       _require("REGINALD_PHONE"),
        "reginald_name":        os.getenv("REGINALD_NAME", "Reginald"),
        "business_name":        os.getenv("BUSINESS_NAME", "Treme Estate Sales"),
        "lead_domains":         [d.strip() for d in os.getenv("LEAD_SOURCE_DOMAINS", "estatesales.net").split(",")],
        "check_interval":       int(os.getenv("CHECK_INTERVAL_SECONDS", "5")),
        "db_path":              os.getenv("DB_PATH", "agent_shaka.db"),
    }


# ── Email utilities ───────────────────────────────────────────────────────────

def _decode_header_value(raw: str) -> str:
    parts = decode_header(raw or "")
    decoded = []
    for part, enc in parts:
        if isinstance(part, bytes):
            decoded.append(part.decode(enc or "utf-8", errors="replace"))
        else:
            decoded.append(str(part))
    return " ".join(decoded)


def _extract_body(msg) -> str:
    """Pull plain-text body from an email.Message object."""
    body_parts = []
    if msg.is_multipart():
        for part in msg.walk():
            ct = part.get_content_type()
            cd = str(part.get("Content-Disposition", ""))
            if ct == "text/plain" and "attachment" not in cd:
                try:
                    body_parts.append(
                        part.get_payload(decode=True).decode(
                            part.get_content_charset() or "utf-8",
                            errors="replace",
                        )
                    )
                except Exception:
                    pass
    else:
        try:
            body_parts.append(
                msg.get_payload(decode=True).decode(
                    msg.get_content_charset() or "utf-8",
                    errors="replace",
                )
            )
        except Exception:
            pass
    return "\n".join(body_parts)


def fetch_new_lead_emails(cfg: dict) -> list[dict]:
    """
    Connect to IMAP, find unread emails from lead source domains,
    mark them read, and return parsed email dicts.
    """
    results = []
    try:
        mail = imaplib.IMAP4_SSL(cfg["imap_host"])
        mail.login(cfg["imap_email"], cfg["imap_password"])
        mail.select("INBOX")

        # Build IMAP search criteria for each configured lead domain
        for domain in cfg["lead_domains"]:
            _, data = mail.search(None, f'(UNSEEN FROM "@{domain}")')
            if not data or not data[0]:
                continue
            ids = data[0].split()
            log.info("Found %d new email(s) from %s", len(ids), domain)

            for eid in ids:
                _, raw = mail.fetch(eid, "(RFC822)")
                if not raw or not raw[0]:
                    continue
                raw_bytes = raw[0][1]
                msg = message_from_bytes(raw_bytes)

                subject    = _decode_header_value(msg.get("Subject", ""))
                from_field = _decode_header_value(msg.get("From", ""))
                message_id = msg.get("Message-ID", f"unknown-{eid.decode()}")
                body       = _extract_body(msg)

                # Parse sender name and email
                email_match = re.search(r"[\w.+-]+@[\w-]+\.[a-zA-Z]+", from_field)
                sender_email = email_match.group() if email_match else ""
                sender_name  = re.sub(r"<.*?>", "", from_field).strip().strip('"')

                # Mark as read
                mail.store(eid, "+FLAGS", "\\Seen")

                results.append({
                    "message_id":   message_id,
                    "sender_email": sender_email,
                    "sender_name":  sender_name,
                    "subject":      subject,
                    "body":         body,
                    "domain":       domain,
                })

        mail.logout()
    except Exception as e:
        log.error("IMAP error: %s", e)

    return results


# ── Email sender ──────────────────────────────────────────────────────────────

def send_email_reply(cfg: dict, to_email: str, subject: str, body: str) -> bool:
    """Send a plain-text email reply via SMTP."""
    try:
        msg = MIMEMultipart("alternative")
        msg["From"]    = cfg["smtp_email"]
        msg["To"]      = to_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        with smtplib.SMTP(cfg["smtp_host"], cfg["smtp_port"]) as server:
            server.ehlo()
            server.starttls()
            server.login(cfg["smtp_email"], cfg["smtp_password"])
            server.sendmail(cfg["smtp_email"], to_email, msg.as_string())

        log.info("Email sent → %s", to_email)
        return True
    except Exception as e:
        log.error("SMTP error sending to %s: %s", to_email, e)
        return False


# ── SMS sender ────────────────────────────────────────────────────────────────

def _format_e164(phone: str) -> Optional[str]:
    """Convert a phone string to E.164 (+1XXXXXXXXXX). Returns None if invalid."""
    digits = re.sub(r"\D", "", phone)
    if len(digits) == 10:
        return f"+1{digits}"
    if len(digits) == 11 and digits.startswith("1"):
        return f"+{digits}"
    return None


def send_sms(cfg: dict, to_phone: str, message: str) -> bool:
    """Send an SMS via Twilio."""
    formatted = _format_e164(to_phone)
    if not formatted:
        log.warning("Cannot send SMS — invalid phone: %s", to_phone)
        return False
    try:
        client = TwilioClient(cfg["twilio_sid"], cfg["twilio_token"])
        client.messages.create(
            body=message[:1600],   # Twilio max
            from_=cfg["twilio_from"],
            to=formatted,
        )
        log.info("SMS sent → %s", formatted)
        return True
    except Exception as e:
        log.error("Twilio error → %s: %s", formatted, e)
        return False


# ── Core pipeline ─────────────────────────────────────────────────────────────

def process_lead(cfg: dict, raw_email: dict, ai_client: anthropic.Anthropic) -> None:
    """
    Full pipeline for a single incoming lead:
      1. Dedup check
      2. Extract structured lead info via Claude
      3. Generate personalized email + SMS via Claude
      4. Send email reply
      5. Send SMS to lead (if phone available)
      6. Notify Reginald via SMS
      7. Save everything to DB
    """
    db = cfg["db_path"]
    message_id   = raw_email["message_id"]
    sender_email = raw_email["sender_email"]
    sender_name  = raw_email["sender_name"]
    subject      = raw_email["subject"]
    body         = raw_email["body"]
    domain       = raw_email["domain"]

    # ── 1. Dedup ──────────────────────────────────────────────────────────────
    if shaka_db.is_duplicate(db, message_id):
        log.info("Skipping duplicate lead: %s", message_id)
        return

    start = time.time()
    log.info("=== New lead from %s — processing... ===", domain)

    # ── 2. Extract lead info ──────────────────────────────────────────────────
    lead_info = shaka_brain.extract_lead_info(
        ai_client, body, sender_email, sender_name, subject
    )
    lead_email = lead_info.get("lead_email") or sender_email
    lead_name  = lead_info.get("name") or sender_name or "Valued Customer"
    lead_phone = lead_info.get("phone")

    log.info("Lead: %s <%s> | Phone: %s", lead_name, lead_email, lead_phone or "none")

    # ── 3. Save lead to DB ────────────────────────────────────────────────────
    lead_id = shaka_db.save_lead(
        db,
        message_id      = message_id,
        email           = lead_email,
        name            = lead_name,
        phone           = lead_phone,
        subject         = subject,
        raw_body        = body,
        property_address= lead_info.get("property_address"),
        inquiry_type    = lead_info.get("inquiry_type"),
        source          = domain,
    )

    # ── 4. Pull successful past examples for learning ─────────────────────────
    past_examples = shaka_db.get_successful_examples(db, limit=4)
    if past_examples:
        log.info("Using %d successful past responses as training examples", len(past_examples))

    # ── 5. Generate response via Claude ──────────────────────────────────────
    response = shaka_brain.generate_response(
        ai_client,
        lead_info     = {**lead_info, "lead_email": lead_email, "name": lead_name},
        reginald_name = cfg["reginald_name"],
        business_name = cfg["business_name"],
        past_examples = past_examples,
    )

    email_subject = response["email_subject"]
    email_body    = response["email_body"]
    sms_message   = response["sms_message"]

    # ── 6. Send email reply ───────────────────────────────────────────────────
    email_sent = send_email_reply(cfg, lead_email, email_subject, email_body)

    # ── 7. Send SMS to lead (if phone known) ──────────────────────────────────
    sms_sent = False
    if lead_phone:
        sms_sent = send_sms(cfg, lead_phone, sms_message)
    else:
        log.info("No phone number found — skipping lead SMS")

    # ── 8. Notify Reginald ────────────────────────────────────────────────────
    reginald_notice = (
        f"🔔 NEW LEAD — {lead_name}\n"
        f"📧 {lead_email}\n"
        f"📱 {lead_phone or 'no phone'}\n"
        f"💬 {lead_info.get('inquiry_type', '')[:80]}\n"
        f"⚡ Shaka responded in {time.time()-start:.1f}s. Give them a call!"
    )
    send_sms(cfg, cfg["reginald_phone"], reginald_notice)

    # ── 9. Mark responded in DB ───────────────────────────────────────────────
    shaka_db.mark_responded(db, lead_id, email_subject, email_body, sms_message)

    elapsed = time.time() - start
    log.info(
        "=== Lead #%d processed in %.1fs | Email: %s | SMS: %s ===",
        lead_id, elapsed,
        "✓" if email_sent else "✗",
        "✓" if sms_sent else "✗ (no phone)" if not lead_phone else "✗ (error)",
    )


# ── Monitoring loop ───────────────────────────────────────────────────────────

def run(cfg: dict) -> None:
    """Main polling loop — runs forever until Ctrl+C."""
    ai_client = anthropic.Anthropic(api_key=cfg["anthropic_api_key"])
    interval  = cfg["check_interval"]

    log.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    log.info("  Agent Shaka is LIVE — Treme Estate Sales")
    log.info("  Monitoring: %s", ", ".join(cfg["lead_domains"]))
    log.info("  Polling every %ds | DB: %s", interval, cfg["db_path"])
    log.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    while True:
        try:
            emails = fetch_new_lead_emails(cfg)
            for raw_email in emails:
                process_lead(cfg, raw_email, ai_client)
        except KeyboardInterrupt:
            log.info("Agent Shaka shutting down. See you next time!")
            break
        except Exception as e:
            log.error("Unexpected error in main loop: %s", e)

        time.sleep(interval)


# ── Test mode ─────────────────────────────────────────────────────────────────

def run_test(cfg: dict) -> None:
    """
    Push a synthetic EstateSales.net lead through the full pipeline so you
    can verify Claude, email, and SMS all work before going live.
    """
    log.info("=== TEST MODE — running synthetic lead through Agent Shaka ===")

    ai_client = anthropic.Anthropic(api_key=cfg["anthropic_api_key"])

    fake_email = {
        "message_id":   "<test-shaka-001@estatesales.net>",
        "sender_email": "leads@estatesales.net",
        "sender_name":  "EstateSales.net Leads",
        "subject":      "New Lead: Property Inquiry — 1234 Oak Lane, Dallas TX",
        "body": textwrap.dedent("""\
            You have a new lead from EstateSales.net!

            Name:     Marcus Johnson
            Email:    marcus.johnson@example.com
            Phone:    (214) 555-0187
            Message:  Hi, I inherited my grandmother's house at 1234 Oak Lane, Dallas TX 75201.
                      The property needs some work and I don't have the time or budget to fix it up.
                      I'm interested in selling it quickly as-is. Can you help?
        """),
        "domain": "estatesales.net",
    }

    # Override the lead email so the test email goes to YOUR inbox, not the fake address
    # (comment this out if you want to test full end-to-end delivery)
    ai_client_info = shaka_brain.extract_lead_info(
        ai_client,
        fake_email["body"],
        fake_email["sender_email"],
        "Marcus Johnson",
        fake_email["subject"],
    )
    # Redirect test email to your own inbox
    ai_client_info["lead_email"] = cfg["imap_email"]

    log.info("Extracted lead info: %s", ai_client_info)

    past_examples = shaka_db.get_successful_examples(cfg["db_path"], limit=4)
    response = shaka_brain.generate_response(
        ai_client,
        lead_info     = ai_client_info,
        reginald_name = cfg["reginald_name"],
        business_name = cfg["business_name"],
        past_examples = past_examples,
    )

    log.info("\n── Generated Email Subject ──\n%s", response["email_subject"])
    log.info("\n── Generated Email Body ──\n%s", response["email_body"])
    log.info("\n── Generated SMS ──\n%s", response["sms_message"])

    # Actually send the test messages
    send_email_reply(cfg, cfg["imap_email"], response["email_subject"], response["email_body"])
    if cfg["reginald_phone"]:
        send_sms(cfg, cfg["reginald_phone"], response["sms_message"])

    log.info("=== TEST COMPLETE — check your email and phone ===")


# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Agent Shaka — Treme Estate Sales")
    parser.add_argument("--test", action="store_true", help="Run a test lead through the pipeline")
    args = parser.parse_args()

    cfg = load_config()
    shaka_db.init_db(cfg["db_path"])

    if args.test:
        run_test(cfg)
    else:
        run(cfg)


if __name__ == "__main__":
    main()
