"""
Claude prompt templates for 3-stage deal generation pipeline.
All prompts are string constants that get formatted with variables.
"""

SYSTEM_PROMPT = """You are a B2B sales data generator. You create realistic, specific, human-sounding synthetic CRM data for demo environments. Always respond with valid JSON only — no markdown, no code fences, no explanations. Company names must be fictional but plausible. People must have realistic full names. All data must be internally consistent. CRITICAL: Generate only valid JSON. Inside string values: use alphanumeric characters, spaces, hyphens, apostrophes, periods, and commas ONLY. Do NOT use quotes, ampersands, parentheses, slashes, newlines, or other special characters. If you must include a double quote in a string value, use \\" to escape it. Never include raw newlines in strings."""

# ============= STAGE 1: Foundation =============

STAGE_1_PROMPT_TEMPLATE = """Generate the deal foundation for a B2B SaaS sales deal with these parameters:

Industry: {industry}
Deal Size: {deal_size}
Sales Cycle: {sales_cycle_length_days} days
Outcome: {deal_outcome}
Complexity: {complexity}
Main Objection: {main_objection}
Buyer Urgency: {buyer_urgency}
Number of Stakeholders: {num_stakeholders}
Starting Sentiment: {starting_sentiment}
Ending Sentiment: {ending_sentiment}
Champion Entry: {champion_entry}
{company_name_line}

Return a single JSON object with this exact structure:
{{
  "company": {{
    "name": "string",
    "industry": "string",
    "employee_count": "string (e.g. '200-500')",
    "arr_range": "string (e.g. '$5M-$15M ARR')",
    "tech_stack": ["string", "string", "string"],
    "icp_type": "string (e.g. 'Mid-market SaaS')",
    "hq_location": "string (City, State)"
  }},
  "sales_rep": {{
    "name": "string",
    "title": "Account Executive",
    "email": "string (firstname.lastname@vendorcompany.com)",
    "vendor_company": "string (fictional SaaS vendor name)"
  }},
  "stakeholders": [
    {{
      "id": "uuid4",
      "name": "string",
      "title": "string",
      "email": "string",
      "archetype": "string (e.g. 'The Analytical Gatekeeper')",
      "support_level": "champion | supporter | neutral | skeptic | blocker",
      "influence_level": "high | medium | low",
      "is_champion": false
    }}
  ],
  "sentiment_arc": [
    {{ "stage": "Prospecting", "sentiment": "positive | neutral | concerned | negative" }},
    {{ "stage": "Discovery", "sentiment": "positive | neutral | concerned | negative" }},
    {{ "stage": "Demo", "sentiment": "positive | neutral | concerned | negative" }},
    {{ "stage": "Evaluation", "sentiment": "positive | neutral | concerned | negative" }},
    {{ "stage": "Negotiation", "sentiment": "positive | neutral | concerned | negative" }},
    {{ "stage": "Closed", "sentiment": "positive | neutral | concerned | negative" }}
  ],
  "stage_progression": [
    {{ "stage": "string", "entered_date": "YYYY-MM-DD", "exited_date": "YYYY-MM-DD or null" }}
  ],
  "objections": [
    {{
      "id": "uuid4",
      "text": "string (specific, realistic objection)",
      "stage": "string",
      "raised_by_stakeholder_id": "uuid4",
      "resolved": true
    }}
  ]
}}

Rules:
- sentiment_arc must start at {starting_sentiment} and end at {ending_sentiment} with natural intermediate progression.
- stage_progression dates must fall within {deal_start_date} to {deal_end_date}.
- stakeholders must include exactly {num_stakeholders} people. Assign exactly one as is_champion: true only if champion_entry is not "none".
- For all text fields (name, title, archetype, text): Use ONLY alphanumeric characters, spaces, hyphens, apostrophes, periods, and commas. NO quotes (straight or curly), NO ampersands, NO parentheses, NO slashes.
- If complexity is "simple": 1-2 objections, all resolved. Mostly supporter/neutral stakeholders.
- If complexity is "normal": 3-4 objections, most resolved. At least one skeptic.
- If complexity is "messy": 5+ objections, some unresolved. At least one blocker. Include budget, security, and procurement objections.
- If deal_outcome is "closed_lost": at least one objection must remain unresolved."""

# ============= STAGE 1 CS: Customer Success Context =============

STAGE_1_CS_PROMPT_TEMPLATE = """Generate the post-close customer success context for this deal.

Deal Foundation:
{stage1_json}

CS Configuration:
- Deal close date: {deal_close_date}
- CS start date: {cs_start_date}
- CS end date: {cs_end_date}
- Adoption challenge: {adoption_challenge}
- Support contact frequency: {support_contact_frequency}
- Churn probability: {churn_probability}

Return a single JSON object with this exact structure:
{{
  "cs_context": {{
    "onboarding_start_date": "YYYY-MM-DD (1-2 days after deal_close_date, on or before cs_end_date)",
    "initial_sentiment": "positive",
    "primary_blocker": "string (specific blocker matching adoption_challenge, 5-10 words)",
    "support_contact_initiator": "uuid4 or name string (person who first reaches out)",
    "churn_date": "YYYY-MM-DD or null (if churn_probability >= 0.7, within cs_start_date to cs_end_date; else null)",
    "key_adoption_risks": [
      "string (specific, concrete risk, 5-10 words)",
      "string (specific, concrete risk, 5-10 words)",
      "string (specific, concrete risk, 5-10 words)",
      "string (specific, concrete risk, 5-10 words)"
    ],
    "recommended_support_frequency": "integer (calls per month, 2-12 range)"
  }}
}}

Rules:
- onboarding_start_date must be 1-2 days after deal_close_date and on or before cs_end_date.
- initial_sentiment must always be "positive".
- primary_blocker must be specific and directly match the adoption_challenge.
- support_contact_initiator can be a UUID of a support engineer or a realistic name string.
- churn_date: if churn_probability >= 0.7, generate a date within cs_start_date to cs_end_date; otherwise set to null.
- key_adoption_risks must have exactly 4 entries, each specific and tied to the adoption_challenge and company context.
- recommended_support_frequency must reflect the support_contact_frequency parameter (low: 2-3, medium: 5-7, high: 10-12).
- All text fields: use ONLY alphanumeric characters, spaces, hyphens, apostrophes, periods, and commas. NO quotes, NO ampersands, NO parentheses, NO slashes, NO newlines.

Return only the JSON object, no other text."""

# ============= STAGE 2 CS: Support Event Timeline =============

STAGE_2_CS_PROMPT_TEMPLATE = """Generate a support event timeline scaffold for this customer success engagement.

Deal Foundation:
{stage1_json}

Sales Timeline:
{stage2_json}

CS Context:
{cs_context_json}

Timeline Configuration:
- Deal close date: {deal_close_date}
- CS start date: {cs_start_date}
- CS end date: {cs_end_date}
- Support contact frequency: {support_contact_frequency}
- Churn probability: {churn_probability}
- Churn date: {churn_date}

Return a JSON array of support event scaffold objects. Each object must have these fields:

For ALL event types:
- "id": uuid4 string
- "record_type": "support_ticket" | "support_call"
- "date": "YYYY-MM-DD"
- "timestamp": ISO 8601 (business hours 08:00-18:00, Monday-Friday only)
- "sentiment": one of [positive, neutral, concerned, negative]
- "days_since_close": integer (days between deal_close_date and event date)

For "support_ticket" events additionally:
- "ticket_type": one of [onboarding_issue, feature_request, bug_report, adoption_blocker, churn_risk, billing_issue]
- "priority": "low" | "medium" | "high"
- "description_preview": "string (10-15 word preview, non-detailed)"
- "from_company": boolean (true if customer reported; false if support-initiated)

For "support_call" events additionally:
- "call_type": one of [onboarding, check_in, troubleshooting, escalation, executive_review]
- "call_duration_minutes": integer (30-60)
- "participants": array of {{ "name": string, "role": "support_engineer" | "customer_contact" }}

Ordering and distribution rules:
1. First event must be a support_call with call_type "onboarding" on onboarding_start_date (1-2 days after deal_close_date).
2. All timestamps must fall within cs_start_date to cs_end_date, Monday-Friday, 08:00-18:00.
3. Distribute events based on support_contact_frequency:
   - "low": 2-3 total interactions
   - "medium": 5-7 total interactions
   - "high": 8-12 total interactions
4. Maintain 60% support_ticket, 40% support_call ratio across all events.
5. If churn_date is not null: final event must be a support_call with call_type "escalation" on churn_date - 1 or churn_date - 2.
6. Sentiment distribution: begin with "positive", shift toward "concerned" or "negative" if churn is expected; remain "positive"/"neutral" if healthy engagement.
7. Events must be strictly chronologically ordered by timestamp.
8. ticket_type and call_type must reflect actual CS activities (onboarding, adoption help, troubleshooting, churn mitigation).

Return only the JSON array, no other text."""

# ============= STAGE 3 CS: Support Ticket & Call Content =============

STAGE_3_SUPPORT_TICKET_PROMPT_TEMPLATE = """Generate the full content for this customer support ticket.

Deal Context:
- Company: {company_name} ({industry})
- Days since close: {days_since_close}
- Adoption challenge: {adoption_challenge}
- Expected churn status: {expected_churn_status}

Support Event:
{event_scaffold_json}

Prior support summary:
{prior_support_summary}

Return a JSON object:
{{
  "description": "2-3 sentences. Realistic customer complaint, frustrated or neutral tone. Specific, mentions adoption challenge or operational issue. Avoid generic language.",
  "sentiment": "positive" | "neutral" | "concerned" | "negative"
}}

Rules:
- description must be 2-3 sentences and reflect customer frustration or concern proportional to expected_churn_status.
- If expected_churn_status is "high", use a more frustrated, critical tone.
- If expected_churn_status is "low", use neutral or slightly positive tone.
- sentiment must match the tone and context.
- Text fields: use ONLY alphanumeric characters, spaces, hyphens, apostrophes, periods, and commas. NO quotes, NO ampersands, NO parentheses, NO slashes, NO newlines.

Return only the JSON object, no other text."""

STAGE_3_SUPPORT_CALL_PROMPT_TEMPLATE = """Generate the full content for this customer support call.

Deal Context:
- Company: {company_name} ({industry})
- Adoption challenge: {adoption_challenge}
- Support engineer: {support_engineer}

Support Event:
{event_scaffold_json}

Related ticket summary:
{related_ticket_summary}

Prior support summary:
{prior_support_summary}

Return a JSON object:
{{
  "transcript": "Multi-speaker transcript using Name: dialogue format per turn. 200-300 words. 2-3 speaker turns minimum. Natural, realistic support conversation. Include specific problem discussion, troubleshooting, and resolution attempt. Reflect sentiment and call_type. If escalation: show frustration and urgency.",
  "resolution": "string (specific resolution or action taken) or null (if unresolved)",
  "sentiment": "positive" | "neutral" | "concerned" | "negative"
}}

Rules:
- transcript must be 200-300 words with realistic speaker turns (customer, support engineer, possibly manager).
- Use format: Speaker: dialogue text (one speaker per line, no nested quotes).
- resolution can be a concrete action/fix, a workaround, or null if the call ended unresolved.
- sentiment must reflect the conversation tone and outcome.
- Text fields: use ONLY alphanumeric characters, spaces, hyphens, apostrophes, periods, and commas. NO quotes (except escaped \"), NO ampersands, NO parentheses, NO slashes, NO newlines in string values.

Return only the JSON object, no other text."""

# ============= STAGE 2: Timeline Scaffold =============

STAGE_2_PROMPT_TEMPLATE = """Given this deal foundation, generate a complete chronological timeline scaffold.

Deal Foundation:
{stage1_json}

Configuration:
- Deal start date: {deal_start_date}
- Deal end date: {deal_end_date}
- Number of calls: {num_calls}
- Emails per stage: {emails_per_stage}
- Champion enters: {champion_entry}
- Complexity: {complexity}
- Main objection: {main_objection}

Return a JSON array of event scaffold objects. Each object must have these fields:

For ALL event types:
- "id": uuid4 string
- "record_type": "call" | "email" | "crm_note"
- "date": "YYYY-MM-DD"
- "timestamp": ISO 8601 (set time to a realistic business hour, Monday-Friday only)
- "stage": one of [Prospecting, Discovery, Demo, Evaluation, Negotiation, Closed]
- "sentiment": one of [positive, neutral, concerned, negative] matching the sentiment_arc for this stage

For "call" events additionally:
- "title": string
- "call_type": one of [Discovery, Demo, Technical Validation, Security Review, Procurement, Negotiation, Executive Alignment]
- "participants": array of {{ "stakeholder_id": uuid4 or null, "name": string, "role": "buyer" | "seller" }}

For "email" events additionally:
- "subject": string
- "thread_id": uuid4
- "reply_to_id": uuid4 or null
- "is_forward": boolean
- "purpose": one of [outbound, follow_up, scheduling, pricing, security, procurement, approval]
- "sender": {{ "stakeholder_id": uuid4 or null, "name": string, "email": string }}
- "recipients": array of {{ "name": string, "email": string }}
- "cc": array of {{ "name": string, "email": string }}

For "crm_note" events additionally:
- "note_preview": string (10-15 word preview used as prompt for Stage 3)
- "author": string (sales rep name)
- "is_internal": true

Ordering and distribution rules:
1. First event must be an outbound email (record_type: "email", purpose: "outbound").
2. Second event must be a prospect reply email.
3. Distribute {num_calls} calls across stages: 1 in Discovery, 1 in Demo, remainder in Evaluation/Negotiation.
4. Generate {emails_per_stage} emails per active stage forming reply chains within each stage.
5. Add CRM notes after each call, when an objection is introduced, when champion appears, and when a risk event occurs.
6. Champion appearance rule — insert a CRM note with note_preview "Champion [name] emerged and aligned internally" at:
   - "before_discovery": after outbound email, before discovery call
   - "during_discovery": after discovery call
   - "after_demo": after demo call
   - "during_procurement": during Evaluation stage
   - "late_stage_rescue": during Negotiation stage
   - "none": do not add any champion note
7. If complexity is "messy": add CRM notes in Evaluation with note_preview containing "procurement delay", "budget concern", "timeline slippage", and "champion risk".
8. If deal_outcome is "closed_lost": final event must be a CRM note with note_preview "Deal lost — [reason]".
9. All timestamps must be weekdays between 08:00 and 18:00.
10. Events must be strictly chronologically ordered.

Return only the JSON array, no other text."""

# ============= STAGE 3: Content Generation =============

STAGE_3_CALL_PROMPT_TEMPLATE = """Generate the full content for this sales call.

Deal Context:
- Company: {company_name} ({industry}, {deal_size})
- Vendor: {vendor_company}
- Sales Rep: {sales_rep_name}, {sales_rep_title}
- Stage: {stage}
- Complexity: {complexity}
- Main Objection: {main_objection}
- Current Sentiment: {sentiment}
- Champion Status: {champion_context}

Stakeholders on this call:
{participants_detail}

All stakeholders in this deal:
{all_stakeholders_summary}

Call scaffold:
{event_scaffold_json}

Prior interactions:
{prior_events_summary}

Return a JSON object:
{{
  "transcript": "Multi-speaker transcript. Use 'Name: dialogue\\n' format per turn. 400-600 words. Reflect the call_type, sentiment, and stage accurately. Include realistic back-and-forth and follow-up questions. If the main objection is relevant, surface it explicitly. If a champion is present, show them supporting the deal.",
  "summary": "2-3 sentences covering what was discussed and decided.",
  "objections_raised": ["verbatim short form of any objection raised in this call"],
  "next_steps": ["specific action item agreed on this call"]
}}"""

STAGE_3_EMAIL_PROMPT_TEMPLATE = """Generate the full content for this sales email.

Deal Context:
- Company: {company_name} ({industry})
- Vendor: {vendor_company}
- Stage: {stage}
- Sentiment: {sentiment}
- Purpose: {purpose}

Email scaffold:
{event_scaffold_json}

{reply_context}

Prior interactions:
{prior_events_summary}

Return a JSON object:
{{
  "body": "Email body. Professional but human and specific. No generic openers. Reference specific details from the deal context. Length: 100-200 words. Tone must match sentiment and purpose."
}}"""

STAGE_3_CRM_NOTE_PROMPT_TEMPLATE = """Generate the full content for this internal CRM note.

Deal Context:
- Company: {company_name}
- Sales Rep: {sales_rep_name}
- Stage: {stage}
- Sentiment: {sentiment}

Note trigger: {note_preview}

Return a JSON object:
{{
  "content": "1 to 3 sentences. Blunt, factual, first-person sales-rep voice. No formatting or bullet points. Should read like something typed quickly into Salesforce. Examples: 'Champion aligned after demo. Marcus pushing procurement to accelerate.' / 'Security team blocked on SOC2. Need to loop in compliance ASAP.' / 'Procurement stalling. Budget freeze mentioned. Deal at risk.'"
}}"""
