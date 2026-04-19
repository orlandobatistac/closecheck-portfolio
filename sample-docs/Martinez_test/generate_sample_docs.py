"""
Generate 4 sample PDFs for the Martinez_test closing package.
Intentional mismatches:
  - Purchase price: PA=$385,000 vs CD=$387,500 (triggers PA-003/CD mismatch)
  - Buyer name: PA/title="Carlos Martinez" vs lender="Carlos Martínez" (triggers PA-001)
  - builder_invoice absent (no PR-005 docs present)
"""
from datetime import date, timedelta
from pathlib import Path

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from reportlab.lib import colors

OUT = Path(__file__).parent
TODAY = date.today()
CLOSING = TODAY + timedelta(days=30)
EXPIRY = TODAY + timedelta(days=60)
CLOSING_STR = CLOSING.strftime("%B %d, %Y")
EXPIRY_STR = EXPIRY.strftime("%B %d, %Y")
TODAY_STR = TODAY.strftime("%B %d, %Y")


def _doc(filename: str):
    path = OUT / filename
    doc = SimpleDocTemplate(str(path), pagesize=letter,
                             leftMargin=inch, rightMargin=inch,
                             topMargin=inch, bottomMargin=inch)
    return doc, path


def _styles():
    s = getSampleStyleSheet()
    h1 = ParagraphStyle("H1", parent=s["Heading1"], fontSize=14, spaceAfter=12)
    h2 = ParagraphStyle("H2", parent=s["Heading2"], fontSize=11, spaceAfter=8)
    body = ParagraphStyle("Body", parent=s["Normal"], fontSize=10, spaceAfter=6, leading=14)
    return h1, h2, body


def make_purchase_agreement():
    doc, path = _doc("purchase_agreement.pdf")
    h1, h2, body = _styles()
    story = [
        Paragraph("RESIDENTIAL PURCHASE AGREEMENT", h1),
        Paragraph("This Purchase Agreement is entered into as of " + TODAY_STR, body),
        Spacer(1, 0.2 * inch),
        Paragraph("PARTIES", h2),
        Paragraph("Buyer Name: Carlos Martinez", body),
        Paragraph("Seller Name: John and Susan Sellars", body),
        Spacer(1, 0.1 * inch),
        Paragraph("PROPERTY", h2),
        Paragraph("Property Address: 4521 Oak Lane, Charlotte, NC 28277", body),
        Spacer(1, 0.1 * inch),
        Paragraph("TERMS", h2),
        Paragraph("Purchase Price: $385,000", body),
        Paragraph("Earnest Money Deposit: $5,000", body),
        Paragraph("Closing Date: " + CLOSING_STR, body),
        Spacer(1, 0.1 * inch),
        Paragraph("CONTINGENCIES", h2),
        Paragraph("This Agreement is contingent upon the following:", body),
        Paragraph("1. Inspection contingency — Buyer has 10 days to inspect the property.", body),
        Paragraph("2. Financing contingency — Subject to buyer obtaining mortgage approval.", body),
        Paragraph("3. Appraisal contingency — Property must appraise at or above purchase price.", body),
        Spacer(1, 0.1 * inch),
        Paragraph("SIGNATURES", h2),
        Paragraph("This document has been signed by all required parties.", body),
        Paragraph("Buyer Signature: ________________________  Date: " + TODAY_STR, body),
        Paragraph("Seller Signature: _______________________  Date: " + TODAY_STR, body),
    ]
    doc.build(story)
    print(f"Created: {path}")


def make_closing_disclosure():
    doc, path = _doc("closing_disclosure.pdf")
    h1, h2, body = _styles()
    story = [
        Paragraph("CLOSING DISCLOSURE", h1),
        Paragraph("This form is a statement of final loan terms and closing costs.", body),
        Spacer(1, 0.2 * inch),
        Paragraph("TRANSACTION INFORMATION", h2),
        Paragraph("Borrower: Carlos Martinez", body),
        Paragraph("Property: 4521 Oak Lane, Charlotte, NC 28277", body),
        Paragraph("Closing Date: " + CLOSING_STR, body),
        Spacer(1, 0.1 * inch),
        Paragraph("LOAN INFORMATION", h2),
        # INTENTIONAL MISMATCH: $387,500 vs PA $385,000
        Paragraph("Purchase Price: $387,500", body),
        Paragraph("Loan Amount: $308,000", body),
        Paragraph("Loan Type: Conventional", body),
        Paragraph("Interest Rate: 6.75%", body),
        Spacer(1, 0.1 * inch),
        Paragraph("CLOSING COSTS SUMMARY", h2),
        Paragraph("Cash to Close: $82,500", body),
        Paragraph("Seller Credits: $0", body),
        Paragraph("Total Closing Costs: $9,250", body),
        Paragraph("Prorated Property Taxes: $1,420", body),
        Spacer(1, 0.1 * inch),
        Paragraph("LENDER FEES", h2),
        Paragraph("Origination Fee: $1,540", body),
        Paragraph("Appraisal Fee: $550", body),
        Paragraph("Title Insurance: $1,200", body),
        Paragraph("Recording Fees: $125", body),
    ]
    doc.build(story)
    print(f"Created: {path}")


def make_lender_commitment():
    doc, path = _doc("lender_commitment.pdf")
    h1, h2, body = _styles()
    story = [
        Paragraph("MORTGAGE LOAN COMMITMENT LETTER", h1),
        Paragraph("This letter confirms the lender's commitment to fund the following loan.", body),
        Spacer(1, 0.2 * inch),
        Paragraph("BORROWER INFORMATION", h2),
        # INTENTIONAL MISMATCH: accent in Martínez vs Martinez in other docs
        Paragraph("Borrower Name: Carlos Martínez", body),
        Paragraph("Co-Borrower: N/A", body),
        Spacer(1, 0.1 * inch),
        Paragraph("LOAN DETAILS", h2),
        Paragraph("Loan Amount: $308,000", body),
        Paragraph("Interest Rate: 6.75% Fixed", body),
        Paragraph("Loan Type: Conventional 30-Year Fixed", body),
        Paragraph("Lender: First National Mortgage Corp.", body),
        Paragraph("Commitment Expiration: " + EXPIRY_STR, body),
        Spacer(1, 0.1 * inch),
        Paragraph("CONDITIONS", h2),
        Paragraph("This commitment is subject to the following conditions:", body),
        Paragraph("1. Clear title at closing.", body),
        Paragraph("2. Homeowner's insurance binder must name lender as mortgagee.", body),
        Paragraph("3. Final inspection approval.", body),
        Spacer(1, 0.1 * inch),
        Paragraph("Lender Representative: ________________  Date: " + TODAY_STR, body),
    ]
    doc.build(story)
    print(f"Created: {path}")


def make_title_binder():
    doc, path = _doc("title_binder.pdf")
    h1, h2, body = _styles()
    story = [
        Paragraph("TITLE COMMITMENT / TITLE BINDER", h1),
        Paragraph("ALTA Commitment for Title Insurance", body),
        Spacer(1, 0.2 * inch),
        Paragraph("SCHEDULE A", h2),
        Paragraph("Commitment Date (Effective Date): " + TODAY_STR, body),
        Paragraph("Buyer / Proposed Insured: Carlos Martinez", body),
        Paragraph("Property Address: 4521 Oak Lane, Charlotte, NC 28277", body),
        Paragraph("Legal Description: Lot 12, Block 4, Oak Ridge Subdivision, Mecklenburg County, NC", body),
        Paragraph("Title Insurance Amount: $385,000", body),
        Spacer(1, 0.1 * inch),
        Paragraph("SCHEDULE B — EXCEPTIONS", h2),
        Paragraph("The following matters are excluded from coverage:", body),
        Paragraph("1. Current year property taxes, not yet due and payable.", body),
        Paragraph("2. Easement for utility lines along the north boundary.", body),
        Paragraph("3. Subdivision covenants and restrictions of record.", body),
        Spacer(1, 0.1 * inch),
        Paragraph("OPEN LIENS", h2),
        Paragraph("Open Liens: None", body),
        Paragraph("Judgments: None", body),
        Paragraph("Encumbrances: None other than noted in Schedule B.", body),
        Spacer(1, 0.1 * inch),
        Paragraph("This title commitment is issued by Oak State Title Company.", body),
        Paragraph("Authorized Signatory: ________________  Date: " + TODAY_STR, body),
    ]
    doc.build(story)
    print(f"Created: {path}")


if __name__ == "__main__":
    make_purchase_agreement()
    make_closing_disclosure()
    make_lender_commitment()
    make_title_binder()
    print("\nAll 4 sample PDFs created in", OUT)
    print(f"Intentional mismatches:")
    print(f"  PA-003: PA price=$385,000  vs  CD price=$387,500 ($2,500 gap)")
    print(f"  PA-001: 'Carlos Martinez' (PA/title) vs 'Carlos Martínez' (lender, accent)")
    print(f"  Missing: insurance_binder, id_document, builder_invoice")
