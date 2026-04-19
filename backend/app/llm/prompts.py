"""
All Claude prompt templates in one place.
Use .format(**kwargs) to fill in variables.
"""

CLASSIFIER_PROMPT = """
Classify the following real estate document into exactly one of these categories:
{document_types}

Respond with valid JSON only, no explanation:
{{
  "document_type": "<category>",
  "confidence": <0.0-1.0>,
  "notes": "<brief reason for classification>"
}}

Document text (first 8000 characters):
---
{text}
---
""".strip()


FIELD_EXTRACTOR_PROMPT = """
You are a real estate closing specialist. Extract the following fields from the document below.
Return null for any field not found -- never infer or guess values.

Fields to extract:
{fields_json}

Respond with valid JSON only, mapping each field name to its extracted value or null.

Document text:
---
{text}
---
""".strip()


CONSISTENCY_CHECK_PROMPT = """
Compare these values extracted from multiple real estate closing documents.
Identify any inconsistencies or mismatches between documents.

Values to compare:
{comparison_json}

Respond with valid JSON only:
{{
  "consistent": <true|false>,
  "mismatches": [
    {{
      "field": "<field name>",
      "values": {{"<doc_type>": "<value>", ...}},
      "explanation": "<what differs and why it matters>"
    }}
  ],
  "notes": "<overall assessment>"
}}
""".strip()


EXECUTIVE_BRIEF_PROMPT = """
You are a real estate closing specialist reviewing a pre-close validation report.
Based on the validation results below, write exactly 5 concise bullet points for a closing coordinator.
Focus on what needs immediate attention. Be specific with amounts, names, and dates when available.
If everything looks good, say so clearly.

Validation results:
{rule_results_json}

Return valid JSON only:
{{
  "bullets": [
    "<bullet 1>",
    "<bullet 2>",
    "<bullet 3>",
    "<bullet 4>",
    "<bullet 5>"
  ]
}}
""".strip()


ACTION_PLAN_PROMPT = """
You are a real estate closing coordinator. Based on the conflicts and failures below,
generate a prioritized action plan to resolve all issues before closing.

Conflicts and failures:
{conflicts_json}

Return a valid JSON array of action items ordered by urgency (most urgent first):
[
  {{
    "title": "<short action title>",
    "description": "<specific steps to resolve>",
    "urgency": "now" | "today" | "soon",
    "owner": "coordinator" | "lender" | "title" | "buyer" | "seller",
    "is_blocker": true | false
  }}
]
""".strip()


EMAIL_DRAFT_PROMPT = """
You are a real estate closing coordinator drafting emails to resolve a specific issue.

Issue details:
{conflict_json}

Recipient: {recipient}

Write two email variants for the same issue:
1. Professional & direct: polite, gives the recipient space to respond, normal relationship tone
2. Urgent: hard deadline language, clearly documents closing risk, implies consequences if unresolved

Return valid JSON only:
{{
  "subject_pro": "<professional subject line>",
  "body_pro": "<professional email body — use \\n for line breaks>",
  "subject_urg": "<urgent subject line starting with URGENT:>",
  "body_urg": "<urgent email body — use \\n for line breaks>"
}}
""".strip()


# Field schemas per document type -- used by the extractor
FIELDS_BY_DOC_TYPE: dict[str, list[str]] = {
    "purchase_agreement": [
        "buyer_name", "seller_name", "property_address", "purchase_price",
        "closing_date", "earnest_money", "signatures_present", "contingencies",
    ],
    "title_commitment": [
        "legal_description", "effective_date", "insurance_amount",
        "schedule_b_exceptions", "open_liens", "judgments",
    ],
    "closing_disclosure": [
        "cash_to_close", "seller_credits", "prorated_taxes",
        "total_closing_costs", "lender_fees",
    ],
    "hud1": [
        "cash_to_close", "seller_credits", "prorated_taxes", "total_closing_costs",
    ],
    "loan_note": [
        "borrower_name", "loan_amount", "interest_rate", "loan_type", "maturity_date",
    ],
    "mortgage_deed": [
        "borrower_name", "lender_name", "property_address", "loan_amount",
    ],
    "insurance_binder": [
        "coverage_amount", "mortgagee", "effective_date", "expiration_date",
        "policy_number", "flood_zone",
    ],
    "hoa_document": [
        "hoa_name", "monthly_dues", "outstanding_balance", "transfer_fee",
    ],
    "tax_certificate": [
        "delinquent", "amount_due", "tax_year", "property_id",
    ],
    "wire_instructions": [
        "bank_name", "account_number", "routing_number", "beneficiary",
    ],
    "id_document": [
        "id_type", "name", "id_number", "expiration_date",
    ],
}
