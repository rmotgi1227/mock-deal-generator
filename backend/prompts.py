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
{ae_name_line}
{ae_profile_line}
{se_name_line}
{se_profile_line}
{business_use_case_line}
{vendor_company_line}

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
  "sales_engineer": {{
    "name": "string",
    "email": "string (firstname.lastname@vendorcompany.com)",
    "vendor_company": "string (same as sales_rep vendor_company)"
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
- sentiment_arc: start={starting_sentiment}, end={ending_sentiment}, natural progression.
- stage_progression dates within {deal_start_date} to {deal_end_date}.
- exactly {num_stakeholders} stakeholders. One is_champion: true unless champion_entry="none".
- Text fields: alphanumeric, spaces, hyphens, apostrophes, periods, commas ONLY. No quotes, ampersands, parens, slashes.
- simple: 1-2 objections all resolved, mostly supporters. normal: 3-4 objections mostly resolved, one skeptic. messy: 5+ objections some unresolved, one blocker, include budget/security/procurement.
- closed_lost: at least one objection unresolved.
- ae_name if provided: use exactly. ae_experience: junior=uncertain/playbook-reliant, mid=competent, senior=confident/reframes. ae_style: consultative=educates/low-pressure, assertive=direct/pushes next steps, relationship_focused=rapport/personal.
- se_name if provided: use exactly. se_technical_depth: shallow=overview only, competent=standard Q&A, deep=custom solutions. se_involvement: light=demo only, standard=demo+eval, heavy=all calls.
- sales_engineer uses same vendor_company as sales_rep. SE appears in demo and evaluation calls.
- AE/SE profile shapes transcripts, emails, objection handling, CRM notes.
- business_use_case if provided: shapes objections, stakeholder archetypes, deal narrative.
- vendor_company if provided: use exactly for sales_rep AND sales_engineer vendor_company AND email domain (firstname.lastname@vendorcompany.com, lowercase, no spaces). Otherwise generate fictional SaaS vendor name."""

# ============= STAGE 1 CS: Customer Success Context =============

STAGE_1_CS_USER_TEMPLATE = """Generate the post-close customer success context for this deal.

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
- "timestamp": ISO 8601 (business hours '08:00-18:00', Monday-Friday only)
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
2. All timestamps must fall within cs_start_date to cs_end_date, Monday-Friday, '08:00-18:00'.
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

STAGE_2_CS_USER_TEMPLATE = """Generate a support event timeline scaffold for this customer success engagement.

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
- "timestamp": ISO 8601 (business hours '08:00-18:00', Monday-Friday only)
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
2. All timestamps must fall within cs_start_date to cs_end_date, Monday-Friday, '08:00-18:00'.
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

# ============= STAGE 2: Chunked Timeline Scaffold =============

STAGE_2_CALLS_PROMPT_TEMPLATE = """Given this deal foundation, generate CALL EVENTS ONLY.

Configuration:
- Deal start date: {deal_start_date}
- Deal end date: {deal_end_date}
- Number of calls: {num_calls}
- Champion enters: {champion_entry}
- Complexity: {complexity}
- Is series: {is_series}

Return a JSON array of CALL event scaffolds ONLY:

For each call:
- "id": uuid4
- "record_type": "call"
- "date": "YYYY-MM-DD"
- "timestamp": ISO 8601
- "stage": [Prospecting, Discovery, Demo, Evaluation, Negotiation, Closed]
- "sentiment": [positive, neutral, concerned, negative]
- "title": string
- "call_type": [Discovery, Demo, Technical Validation, Security Review, Procurement, Negotiation, Executive Alignment, Cold Call - Initial Outreach]
- "participants": array of {{stakeholder_id, name, role}}

Rules:
1. Distribute calls across stages: 1 Discovery, 1 Demo, remainder in Evaluation/Negotiation
2. If is_series true: first event must be "Cold Call - Initial Outreach"
3. All timestamps weekdays 08:00-18:00
4. Chronologically ordered by date
5. Do NOT include any emails or CRM notes

Return only JSON array, no other text."""

STAGE_2_EMAILS_PROMPT_TEMPLATE = """Given this deal foundation and call schedule, generate EMAIL EVENTS ONLY.

Call Events (for reference):
{call_events_json}

Configuration:
- Deal start date: {deal_start_date}
- Deal end date: {deal_end_date}
- Emails per stage: {emails_per_stage}
- Main objection: {main_objection}

Return a JSON array of EMAIL event scaffolds ONLY:

For each email:
- "id": uuid4
- "record_type": "email"
- "date": "YYYY-MM-DD"
- "timestamp": ISO 8601
- "stage": [Prospecting, Discovery, Demo, Evaluation, Negotiation, Closed]
- "sentiment": [positive, neutral, concerned, negative]
- "subject": string
- "thread_id": uuid4
- "reply_to_id": uuid4 or null
- "is_forward": boolean
- "purpose": [outbound, follow_up, scheduling, pricing, security, procurement, approval]
- "sender": {{stakeholder_id, name, email}}
- "recipients": array of {{name, email}}
- "cc": array of {{name, email}}

Rules:
1. First event overall must be outbound email (before any calls)
2. Second event must be prospect reply
3. Generate {emails_per_stage} emails per stage, forming reply chains within stages
4. Space emails between calls (don't cluster them)
5. Threads should have 2-4 related emails (outbound → reply → follow-up)
6. All timestamps weekdays 08:00-18:00
7. Chronologically ordered by date
8. Do NOT include any calls or CRM notes

Return only JSON array, no other text."""

STAGE_2_CRM_NOTES_PROMPT_TEMPLATE = """Given this deal foundation and existing events, generate CRM NOTE EVENTS ONLY.

Existing Events (calls + emails):
- Calls: {call_events_json}
- Emails: {email_events_json}

Configuration:
- Deal start date: {deal_start_date}
- Deal end date: {deal_end_date}
- Champion entry: {champion_entry}
- Complexity: {complexity}
- Deal outcome: {deal_outcome}

Return a JSON array of CRM NOTE event scaffolds ONLY:

For each CRM note:
- "id": uuid4
- "record_type": "crm_note"
- "date": "YYYY-MM-DD"
- "timestamp": ISO 8601
- "stage": [Prospecting, Discovery, Demo, Evaluation, Negotiation, Closed]
- "sentiment": [positive, neutral, concerned, negative]
- "note_preview": string (10-15 words, will be used as prompt seed in Stage 3)
- "author": string (sales rep name)
- "is_internal": true

Rules:
1. Add CRM note after each call with note_preview summarizing call outcome
2. Add note when objection is introduced in emails/calls
3. Add note when champion appears (per champion_entry timing)
4. If complexity "messy": add risk notes about "procurement delay", "budget concern", "timeline slippage"
5. If deal_outcome "closed_lost": final note with "Deal lost — [reason]"
6. All timestamps weekdays 08:00-18:00
7. Chronologically ordered by date
8. Dates should align with existing calls/emails (same day or next business day after triggering event)
9. Do NOT include any calls or emails

Return only JSON array, no other text."""

# ============= STAGE 2: Timeline Scaffold (Legacy - kept for backward compat) =============

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
3. If is_series is true: the first event in the Prospecting stage must be a call with call_type "Cold Call - Initial Outreach".
4. Distribute {num_calls} calls across stages: 1 in Discovery, 1 in Demo, remainder in Evaluation/Negotiation.
5. Generate {emails_per_stage} emails per active stage forming reply chains within each stage.
6. Add CRM notes after each call, when an objection is introduced, when champion appears, and when a risk event occurs.
7. Champion appearance rule — insert a CRM note with note_preview "Champion [name] emerged and aligned internally" at:
   - "before_discovery": after outbound email, before discovery call
   - "during_discovery": after discovery call
   - "after_demo": after demo call
   - "during_procurement": during Evaluation stage
   - "late_stage_rescue": during Negotiation stage
   - "none": do not add any champion note
8. If complexity is "messy": add CRM notes in Evaluation with note_preview containing "procurement delay", "budget concern", "timeline slippage", and "champion risk".
9. If deal_outcome is "closed_lost": final event must be a CRM note with note_preview "Deal lost — [reason]".
10. All timestamps must be weekdays between '08:00' and '18:00'.
11. Events must be strictly chronologically ordered.

Return only the JSON array, no other text."""

# ============= STAGE 3: Content Generation =============

STAGE_3_CALL_PROMPT_TEMPLATE = """Generate content for this sales call. Deal context, stakeholders, and timeline are in the system prompt.

Stage: {stage}
Sentiment: {sentiment}
Champion Status: {champion_context}

Participants on this call:
{participants_detail}

Call scaffold:
{event_scaffold_json}

Prior interactions:
{prior_events_summary}

Return a JSON object:
{{
  "transcript": "Multi-speaker transcript. Use 'Name: dialogue' format per turn. 400-600 words. Reflect the call_type, sentiment, and stage. Include realistic back-and-forth. If the main objection is relevant, surface it explicitly. If a champion is present, show them supporting the deal.",
  "summary": "2-3 sentences covering what was discussed and decided.",
  "objections_raised": ["verbatim short form of any objection raised in this call"],
  "next_steps": ["specific action item agreed on this call"]
}}"""

STAGE_3_EMAIL_PROMPT_TEMPLATE = """Generate content for this sales email. Deal context is in the system prompt.

Stage: {stage}
Sentiment: {sentiment}
Purpose: {purpose}

Email scaffold:
{event_scaffold_json}

{reply_context}

Prior interactions:
{prior_events_summary}

Return a JSON object:
{{
  "body": "Email body. Professional but human and specific. No generic openers. Reference specific details from the deal context. Length: 100-200 words. Tone must match sentiment and purpose."
}}"""

STAGE_3_CRM_NOTE_PROMPT_TEMPLATE = """Generate content for this internal CRM note. Deal context is in the system prompt.

Stage: {stage}
Sentiment: {sentiment}
Note trigger: {note_preview}

Return a JSON object:
{{
  "content": "1 to 3 sentences. Blunt, factual, first-person sales-rep voice. No formatting or bullet points. Should read like something typed quickly into Salesforce."
}}"""

# ============= STAGE 3 Slack: Channel & Message Generation =============

STAGE_3_SLACK_PROMPT_TEMPLATE = """Generate realistic internal sales team Slack messages for this deal.

Deal: {company_name} | {industry} | {deal_size} | complexity={complexity_mode} | outcome={outcome}
AE: {ae_name} | SE: {se_name}
Objections: {objections}
Timeline: {timeline_summary}
Calls: {calls_summary}
Emails: {emails_summary}

Generate actual back-and-forth team conversations — NOT status updates. Messages must feel like real people talking:
- AE posts something specific ("just got off the call, their security team pushed back hard on data residency"), Manager or SE replies ("expected — did you send the compliance docs yet?"), AE replies back
- Threads form around key deal moments: after demo, when an objection surfaces, when a risk appears, at close
- Senders react to each other, ask questions, give advice, express concern or excitement
- Reference specific names, objections, and dates from the deal
- Tone: casual, direct, no corporate speak. Short messages (1-3 sentences). No emoji.

Channels: Simple=1 (#deal-companyname), Normal=1-2 (#deal-companyname + #at-risk if major objection), Messy=2-3
sender MUST be ONLY ONE of: AE, SDR, Manager, SE, Legal, CS, Rep
sender_name: use the real name for AE ({ae_name}) and SE ({se_name}). For Manager, SDR, CS, Legal invent a realistic full name.
6-10 messages per channel. Use is_thread_reply=true and thread_parent_id to create reply chains under key messages.
Each message MUST have channel_id matching its channel.

JSON array of SlackChannel objects: [{{"channel_id": "ch_uuid", "name": "deal-companyname", "topic": "", "is_shared": false, "created_at": "ISO", "messages": [{{"message_id": "msg_uuid", "channel_id": "ch_uuid", "sender": "AE", "sender_name": "Sarah Martinez", "body": "", "timestamp": "ISO", "reactions": [], "is_thread_reply": false, "thread_parent_id": null}}]}}]"""

STAGE_3_SLACK_SERIES_PROMPT_TEMPLATE = """Generate realistic internal sales team Slack messages for this deal.

Rep: {rep_name} | SE: {se_name} | Deal: {current_deal_name} | Stage: {current_deal_stage} | Outcome: {current_deal_outcome}
Quarter health: {quarter_health}
Timeline: {timeline_summary}

Generate actual back-and-forth team conversations — NOT status updates. Messages must feel like real people talking:
- AE posts something specific about the deal, Manager or SE replies, others chime in
- Threads form around key moments: risks, blockers, wins, close
- Reference specific deal details, express real concern or excitement
- Tone: casual, direct, short messages (1-3 sentences). No emoji.

Channels: #deal-[name] only. Do NOT generate pipeline or rep-level channels.
sender MUST be ONLY ONE of: AE, SDR, Manager, SE, Legal, CS, Rep
sender_name: use real name for AE ({rep_name}) and SE ({se_name}). For Manager, SDR, CS, Legal invent a realistic full name.
6-10 messages in deal channel. Use is_thread_reply=true and thread_parent_id for reply chains.
Each message MUST have channel_id matching its channel.

JSON array of SlackChannel objects: [{{"channel_id": "ch_uuid", "name": "deal-companyname", "topic": "", "is_shared": false, "created_at": "ISO", "messages": [{{"message_id": "msg_uuid", "channel_id": "ch_uuid", "sender": "AE", "sender_name": "Sarah Martinez", "body": "", "timestamp": "ISO", "reactions": [], "is_thread_reply": false, "thread_parent_id": null}}]}}]"""

