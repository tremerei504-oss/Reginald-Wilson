#!/usr/bin/env python3
"""
GHL Estate Sales Setup Script
Builds: tag, pipeline, workflow, and email forwarding inbox
for Wilson Estate Services / Treme Estate Sales
"""

import json
import time
import requests

# ── Credentials ──────────────────────────────────────────────────────────────
API_KEY     = "pit-01f1f25e-b1bd-4192-8624-08501b5a6d29"
LOCATION_ID = "s5j2ByFqZm7zD0DDxbSN"
BASE_URL    = "https://services.leadconnectorhq.com"

HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type":  "application/json",
    "Version":       "2021-07-28",
}

# ── Helpers ───────────────────────────────────────────────────────────────────
def ok(label, r):
    if r.status_code in (200, 201):
        print(f"  [OK {r.status_code}] {label}")
        return r.json()
    else:
        print(f"  [FAIL {r.status_code}] {label}")
        print(f"          {r.text[:400]}")
        return None

# ═════════════════════════════════════════════════════════════════════════════
# STEP 1 — Create tag
# ═════════════════════════════════════════════════════════════════════════════
print("\n[1/4] Creating tag: estatesales-net")
r = requests.post(
    f"{BASE_URL}/locations/{LOCATION_ID}/tags",
    headers=HEADERS,
    json={"name": "estatesales-net"},
)
tag_data = ok("tag estatesales-net", r)
TAG_ID = tag_data.get("tag", {}).get("id") if tag_data else None
print(f"       TAG_ID = {TAG_ID}")

# ═════════════════════════════════════════════════════════════════════════════
# STEP 2 — Create pipeline
# ═════════════════════════════════════════════════════════════════════════════
print("\n[2/4] Creating pipeline: EstateSales Leads")
r = requests.post(
    f"{BASE_URL}/opportunities/pipelines",
    headers=HEADERS,
    json={
        "locationId": LOCATION_ID,
        "name": "EstateSales Leads",
        "stages": [
            {"name": "New Lead"},
            {"name": "Contacted"},
            {"name": "Responded"},
            {"name": "Booked"},
            {"name": "Long Nurture"},
            {"name": "Dead"},
        ],
    },
)
pipeline_data = ok("pipeline EstateSales Leads", r)
PIPELINE_ID = pipeline_data.get("pipeline", {}).get("id") if pipeline_data else None

stage_ids = {}
if pipeline_data:
    for stage in pipeline_data.get("pipeline", {}).get("stages", []):
        stage_ids[stage["name"]] = stage["id"]

print(f"       PIPELINE_ID = {PIPELINE_ID}")
print(f"       STAGES = {json.dumps(stage_ids, indent=8)}")

# ═════════════════════════════════════════════════════════════════════════════
# STEP 3 — Create workflow
# ═════════════════════════════════════════════════════════════════════════════
print("\n[3/4] Creating workflow: EstateSales Lead Nurture")

EMAIL1_SUBJECT = "Your Estate Sale in {{contact.city}} — Let's Talk"
EMAIL1_BODY = """\
Hi {{contact.first_name}},

I noticed you reached out about an estate sale — I want to make sure you get the most out of it.

At Wilson Estate Services, we handle everything:
✔ Professional pricing & staging
✔ Marketing to thousands of local buyers
✔ Full cleanup after the sale

Most families walk away with 30–40% more than DIY sales.

👉 Book a Free 15-Min Call: YOUR_CALENDAR_LINK

Talk soon,
Reginald Wilson
Wilson Estate Services
YOUR_PHONE"""

EMAIL2_SUBJECT = "Quick question about your estate sale, {{contact.first_name}}"
EMAIL2_BODY = """\
Hi {{contact.first_name}},

Just checking in — estate sales move fast and the best dates book up quickly.

Do you have a target date in mind? Even a rough timeframe helps us plan.

Reply to this email or grab a time here:
👉 Schedule a Call: YOUR_CALENDAR_LINK

Reginald Wilson"""

EMAIL3_SUBJECT = "Keeping your spot warm, {{contact.first_name}}"
EMAIL3_BODY = """\
Hi {{contact.first_name}},

No rush at all — when the time is right, we're here.

I'll check back in 30 days. In the meantime, here's what other families have said about working with us:

INSERT_TESTIMONIAL_OR_GOOGLE_REVIEW_LINK

Reginald Wilson
Wilson Estate Services"""

SMS1 = ("Hey {{contact.first_name}}, this is Reginald with Wilson Estate Services. "
        "I saw your inquiry — are you still looking for help with your estate sale in "
        "{{contact.city}}? Reply YES and I'll get you a free quote today.")

SMS2 = ("Still here if you need us, {{contact.first_name}}. Most families we work with "
        "save 20–30% more by going pro. Want a free walkthrough? Just reply back.")

workflow_payload = {
    "locationId": LOCATION_ID,
    "name": "EstateSales Lead Nurture",
    "status": "draft",
    "trigger": {
        "type": "contact_created",
        "filters": [
            {
                "field": "tags",
                "operator": "contains",
                "value": "estatesales-net",
            }
        ],
    },
    "entryMode": "once_per_contact",
    "actions": [
        # 1. Immediate SMS
        {
            "type": "send_sms",
            "name": "Immediate SMS #1",
            "delayValue": 0,
            "delayType": "minutes",
            "message": SMS1,
        },
        # 2. Wait 5 min → Email #1
        {
            "type": "send_email",
            "name": "Email #1 — Free Quote",
            "delayValue": 5,
            "delayType": "minutes",
            "subject": EMAIL1_SUBJECT,
            "body": EMAIL1_BODY,
        },
        # 3. Wait 1 day → SMS #2 (if no reply)
        {
            "type": "send_sms",
            "name": "Day-1 SMS #2",
            "delayValue": 1,
            "delayType": "days",
            "message": SMS2,
            "condition": {"type": "no_reply"},
        },
        # 4. Wait 3 days → Email #2 (if no reply)
        {
            "type": "send_email",
            "name": "Day-3 Email #2",
            "delayValue": 3,
            "delayType": "days",
            "subject": EMAIL2_SUBJECT,
            "body": EMAIL2_BODY,
            "condition": {"type": "no_reply"},
        },
        # 5. Wait 7 days → Move stage + Email #3 (if no reply)
        {
            "type": "move_to_stage",
            "name": "Move to Long Nurture",
            "delayValue": 7,
            "delayType": "days",
            "pipelineId": PIPELINE_ID,
            "stageId": stage_ids.get("Long Nurture"),
            "condition": {"type": "no_reply"},
        },
        {
            "type": "send_email",
            "name": "Day-7 Email #3 — Keeping Warm",
            "delayValue": 0,
            "delayType": "minutes",
            "subject": EMAIL3_SUBJECT,
            "body": EMAIL3_BODY,
        },
        # 6. IF reply received → stop + move to Responded + task
        {
            "type": "if_else",
            "name": "Reply Received Branch",
            "condition": {"type": "reply_received"},
            "yesActions": [
                {
                    "type": "stop_workflow",
                    "name": "Stop on Reply",
                },
                {
                    "type": "move_to_stage",
                    "name": "Move to Responded",
                    "pipelineId": PIPELINE_ID,
                    "stageId": stage_ids.get("Responded"),
                },
                {
                    "type": "create_task",
                    "name": "Task — Call within 1 hour",
                    "title": "Call lead within 1 hour",
                    "dueDate": "1h",
                },
            ],
        },
        # 7. IF tag 'booked' added → stop all
        {
            "type": "if_else",
            "name": "Booked Tag Branch",
            "condition": {
                "type": "tag_added",
                "value": "booked",
            },
            "yesActions": [
                {
                    "type": "stop_workflow",
                    "name": "Stop on Booked Tag",
                },
            ],
        },
    ],
}

r = requests.post(
    f"{BASE_URL}/workflows/",
    headers=HEADERS,
    json=workflow_payload,
)
workflow_data = ok("workflow EstateSales Lead Nurture", r)
WORKFLOW_ID = workflow_data.get("workflow", {}).get("id") if workflow_data else None
print(f"       WORKFLOW_ID = {WORKFLOW_ID}")

# ═════════════════════════════════════════════════════════════════════════════
# STEP 4 — Create forwarding inbox
# ═════════════════════════════════════════════════════════════════════════════
print("\n[4/4] Creating email forwarding inbox")
r = requests.post(
    f"{BASE_URL}/conversations/providers/email",
    headers=HEADERS,
    json={
        "locationId": LOCATION_ID,
        "name": "EstateSales.net Lead Inbox",
        "forwardingEnabled": True,
    },
)
inbox_data = ok("email forwarding inbox", r)
FORWARDING_EMAIL = inbox_data.get("forwardingEmail") if inbox_data else None
print(f"       FORWARDING_EMAIL = {FORWARDING_EMAIL}")

# ═════════════════════════════════════════════════════════════════════════════
# SUMMARY
# ═════════════════════════════════════════════════════════════════════════════
print("\n" + "═" * 60)
print("SETUP COMPLETE — SUMMARY")
print("═" * 60)
print(f"  Tag ID           : {TAG_ID}")
print(f"  Pipeline ID      : {PIPELINE_ID}")
print(f"  Stage IDs        : {json.dumps(stage_ids, indent=20)}")
print(f"  Workflow ID      : {WORKFLOW_ID}")
print(f"  Forwarding Email : {FORWARDING_EMAIL}")
print("═" * 60)
print("\nNEXT STEPS:")
print("  1. Replace YOUR_CALENDAR_LINK in email bodies with your Calendly/GHL calendar URL")
print("  2. Replace YOUR_PHONE with your business phone number")
print("  3. Replace INSERT_TESTIMONIAL_OR_GOOGLE_REVIEW_LINK in Email #3")
print("  4. Set up Gmail filter to forward EstateSales.net emails to:", FORWARDING_EMAIL)
print("  5. Activate the workflow in GHL (it's saved as draft — publish it)")
print()
