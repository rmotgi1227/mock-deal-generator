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
