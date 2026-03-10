"""
shaka_brain.py — Agent Shaka AI Engine

Uses Claude Opus 4.6 with adaptive thinking to:
  1. Extract structured lead info from raw EstateSales.net notification emails
  2. Generate professional, personalized email + SMS responses
  3. Learn from past successful interactions to keep improving over time
"""

import re
import json
import logging
from typing import Optional

import anthropic

log = logging.getLogger(__name__)

# ── System prompt: Shaka's personality and knowledge ──────────────────────────

SHAKA_SYSTEM_PROMPT = """You are Agent Shaka, the elite lead response specialist for Treme Estate Sales in the Dallas Fort Worth, Texas area.

Your role is to craft warm, professional, and compelling first-contact messages that make leads feel valued, informed, and excited to work with us.

━━ ABOUT TREME ESTATE SALES ━━
• Full-service estate sales and real estate company
• Operated by an active, licensed Realtor — giving clients professional expertise and legal protection
• We purchase homes completely AS-IS — no repairs, no cleaning, no stress for the seller
• We can close in as few as 10 days — one of the fastest options available
• Proudly earned 90+ five-star reviews on Google — trusted by hundreds of families across DFW
• Reginald Wilson personally follows up with every lead by phone

━━ YOUR RESPONSE GUIDELINES ━━
1. Open with a warm, genuine greeting — use the lead's name when available
2. Acknowledge their specific inquiry — show you read their message and care
3. Introduce Treme Estate Sales naturally — emphasize the licensed Realtor advantage (credibility + protection)
4. Highlight the AS-IS purchase option and our ability to close in as few as 10 days (leads want speed and simplicity)
5. Mention our 90+ five-star Google reviews to reinforce trust
6. Let them know Reginald will be calling them personally — frame this as VIP attention, not a sales call
7. Close warmly with an open invitation to reach back out

━━ TONE ━━
Professional yet warm. Confident but never pushy. Think: "knowledgeable trusted friend in real estate" — not a sales script.

━━ NEVER ━━
• Use aggressive or high-pressure language
• Make guarantees you can't keep
• Include unnecessary filler or fluff
• Sound robotic or templated — every response should feel personal
"""


def extract_lead_info(
    client: anthropic.Anthropic,
    raw_body: str,
    sender_email: str,
    sender_name: str,
    subject: str,
) -> dict:
    """
    Use Claude to extract structured lead data from a raw EstateSales.net
    notification email. Returns a dict with name, phone, address, etc.
    """
    prompt = f"""Extract lead contact information from this EstateSales.net lead notification email.

Sender info (this may be the notification system, not the actual lead):
  From: {sender_name} <{sender_email}>
  Subject: {subject}

Raw email body:
{raw_body[:3000]}

Return ONLY valid JSON in this exact format (use null for missing fields):
{{
  "name": "lead's full name",
  "lead_email": "lead's actual email address (may differ from sender if forwarded)",
  "phone": "lead's phone number formatted as +1XXXXXXXXXX, or null",
  "property_address": "property address if mentioned, or null",
  "inquiry_type": "one-line description of what they are asking about",
  "body_summary": "2-3 sentence summary of their specific inquiry and situation"
}}"""

    try:
        response = client.messages.create(
            model="claude-opus-4-6",
            max_tokens=512,
            messages=[{"role": "user", "content": prompt}],
        )
        text = response.content[0].text
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            info = json.loads(match.group())
            # Ensure we always have a usable email
            info.setdefault("lead_email", sender_email)
            if not info.get("lead_email"):
                info["lead_email"] = sender_email
            info["subject"] = subject
            return info
    except Exception as e:
        log.error("Lead info extraction failed: %s", e)

    return {
        "name": sender_name or "Valued Customer",
        "lead_email": sender_email,
        "phone": None,
        "property_address": None,
        "inquiry_type": "Estate sale / real estate inquiry",
        "body_summary": raw_body[:400],
        "subject": subject,
    }


def generate_response(
    client: anthropic.Anthropic,
    lead_info: dict,
    reginald_name: str,
    business_name: str,
    past_examples: list[dict] | None = None,
) -> dict:
    """
    Generate a professional email AND SMS response for a lead using Claude
    Opus 4.6 with adaptive thinking.

    Passes successful past interactions as few-shot examples so Shaka
    continuously improves its conversion rate.

    Returns: {"email_subject": str, "email_body": str, "sms_message": str}
    """
    name = lead_info.get("name") or "there"
    lead_email = lead_info.get("lead_email", "")
    phone = lead_info.get("phone", "")
    property_address = lead_info.get("property_address", "")
    inquiry_type = lead_info.get("inquiry_type", "")
    body_summary = lead_info.get("body_summary", "")
    subject = lead_info.get("subject", "")

    # ── Build the few-shot learning context ──────────────────────────────────
    examples_block = ""
    if past_examples:
        examples_block = "\n\n━━ PAST SUCCESSFUL RESPONSES (learn from these) ━━\n"
        for i, ex in enumerate(past_examples[:4], 1):
            examples_block += (
                f"\nExample {i} — Lead: {ex.get('name', 'Lead')} | "
                f"Outcome: {ex.get('status', 'engaged')}\n"
                f"Email sent:\n{ex.get('email_response', '')[:400]}\n"
                f"SMS sent: {ex.get('sms_response', '')}\n"
            )
        examples_block += "\n━━ END EXAMPLES ━━\n"

    # ── Main generation prompt ───────────────────────────────────────────────
    prompt = f"""{examples_block}
New incoming lead — respond immediately and professionally.

Lead Details:
  Name:              {name}
  Email:             {lead_email}
  Phone:             {phone or 'Not provided in email'}
  Property address:  {property_address or 'Not specified'}
  Inquiry type:      {inquiry_type}
  Their message:     {body_summary}
  Email subject:     {subject}

Generate TWO responses for this lead:

1. EMAIL RESPONSE: Warm, professional email (150–220 words). Rephrase the key points naturally — do not just list bullet points.
2. SMS RESPONSE: A concise, friendly text message (under 300 characters). Must feel personal, not automated.

Return ONLY valid JSON:
{{
  "email_subject": "compelling reply subject line",
  "email_body": "full email body text",
  "sms_message": "SMS text under 300 characters"
}}

Important: In BOTH messages include — (a) {business_name} is run by a licensed Realtor, (b) we buy AS-IS and can close in as few as 10 days, (c) we have 90+ five-star Google reviews, (d) {reginald_name} will be calling them personally."""

    try:
        response = client.messages.create(
            model="claude-opus-4-6",
            max_tokens=2048,
            thinking={"type": "adaptive"},
            system=SHAKA_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )

        # Extract the text block (adaptive thinking may include a thinking block first)
        text = ""
        for block in response.content:
            if block.type == "text":
                text = block.text
                break

        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            result = json.loads(match.group())
            log.info("Claude generated response for %s <%s>", name, lead_email)
            return result

    except json.JSONDecodeError as e:
        log.error("JSON parse error from Claude response: %s", e)
    except anthropic.APIError as e:
        log.error("Claude API error: %s", e)
    except Exception as e:
        log.error("Unexpected error in generate_response: %s", e)

    # ── Fallback: solid hardcoded response ───────────────────────────────────
    log.warning("Using fallback response for %s", lead_email)
    return _fallback_response(name, reginald_name, business_name, subject)


def _fallback_response(
    name: str, reginald_name: str, business_name: str, subject: str
) -> dict:
    email_body = f"""Dear {name},

Thank you so much for reaching out — we're genuinely excited to connect with you!

{business_name} is a full-service company proudly operated by an active, licensed Realtor. That means you get the professionalism, legal protection, and market expertise that only a licensed real estate professional can provide — combined with the simplicity of working with a dedicated estate sale and property specialist.

One of our most sought-after services is our ability to purchase properties completely AS-IS. No repairs. No cleaning. No showings. We handle everything — and we can close in as few as 10 days when speed matters.

We're proud to have earned over 90 five-star reviews on Google, and we'd love the opportunity to earn your trust as well.

{reginald_name} will be reaching out to you personally very soon. In the meantime, please don't hesitate to reply with any questions — we're here to help every step of the way.

Warm regards,
{reginald_name}
{business_name}"""

    sms_message = (
        f"Hi {name}! Thanks for contacting {business_name}. "
        f"We buy homes AS-IS & close in as few as 10 days. "
        f"90+ ⭐ Google reviews. {reginald_name} will call you shortly!"
    )

    return {
        "email_subject": f"Thank You for Reaching Out — {business_name}",
        "email_body": email_body,
        "sms_message": sms_message[:300],
    }
