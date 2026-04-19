# Getting Real Charlotte, NC Closing Documents

## Quick Access Links

### 📍 Mecklenburg County Public Records (Direct)
**Website:** https://www.meckdb.org/

**Steps:**
1. Go to https://www.meckdb.org/
2. Click "Public Records Search" (right sidebar)
3. Choose search type:
   - By Property Address → Find your test property
   - By Book/Page → Example: "Book 15824, Page 1" (recent deeds)
   - By Grantor/Grantee Name → "Smith" or "Johnson"
4. Click "View Document" → Download PDF
5. Save to: `sample-docs/charlotte_nc/`

### 🏛️ NC Judicial Branch (Statewide, Includes Mecklenburg)
**Website:** https://www.nccourts.org/

Navigate to:
- Criminal & Civil Case Search → Mecklenburg County
- Filter by document type (Deed, Mortgage, Lien)

### 📊 Zillow/Redfin (Historical Data)
- Search Charlotte, NC properties
- View property history → Download images of deeds

---

## What Documents You Need

For a realistic closing package, download:

1. **Deed (Grant Deed or Warranty Deed)** 
   - Shows property transfer
   - Book: 15800-15900 (recent)
   
2. **Mortgage / Deed of Trust**
   - Shows lender info
   - Usually same book as deed, next 10-20 pages
   
3. **Title Insurance Commitment** (if available)
   - Shows title company info
   - Sometimes on Register of Deeds

4. **Closing Disclosure** (if available)
   - CFPB-required form
   - Some counties file these (Mecklenburg usually doesn't)

---

## Mecklenburg County Book/Page Examples (Recent)

These are approximate book numbers for recent deeds in Charlotte:

```
Book 16000 — 2024 Q2
Book 15900 — 2024 Q1  
Book 15800 — 2023 Q4
Book 15700 — 2023 Q3
Book 15600 — 2023 Q2
```

**To find recent transactions:**
1. Go to https://www.meckdb.org/
2. Enter "Book 15850, Page 1" → searches that range
3. Browse next pages to find relevant properties

---

## Example: Getting a Real Charlotte Deed

1. **Visit:** https://www.meckdb.org/
2. **Search:** Enter "Book 15850, Page 50" (random recent deed)
3. **View:** Click result → see deed details
4. **Download:** "Download Full Document" → saves PDF
5. **Rename:** `Charlotte_Deed_15850_50.pdf`
6. **Place:** `sample-docs/charlotte_nc/Charlotte_Deed_15850_50.pdf`

---

## Alternative: Specific Charlotte High-Value Properties

Well-known Charlotte neighborhoods (good for realistic data):

- **Uptown Charlotte** — Recent developments, large transactions
- **South End** — Modern real estate, good public records
- **Myers Park** — Historic luxury homes, detailed records
- **Ballantyne** — Newer suburban properties

Search any street in these areas:
1. Google: "Charlotte NC property deed [address]"
2. Most will link to Mecklenburg County Register

---

## Preparing Downloaded Documents

Once you have real PDFs:

```bash
# Organize by type
sample-docs/charlotte_nc/
├── Deeds/
│   ├── Deed_Smith_123MainSt.pdf
│   ├── Deed_Johnson_456Park.pdf
│   └── ...
├── Mortgages/
│   ├── Mortgage_SmithJohnson.pdf
│   └── ...
└── Titles/
    └── (if available)
```

---

## Running CloseCheck with Charlotte Documents

Once you have 3-5 real complete closing packages:

```bash
# Backend running
python -m uvicorn app.main:app --reload

# Frontend (separate terminal)
npm run dev

# Upload sample-docs/charlotte_nc/ files
# Visit http://localhost:5173
# Select multiple PDFs → Validate
```

---

## Troubleshooting

**Q: meckdb.org blocked / not accessible?**  
A: Try NC Judicial Branch (nccourts.org) or contact Mecklenburg County Assessor's Office directly

**Q: Can't find Closing Disclosure?**  
A: Mecklenburg County may not file these. Use CFPB template instead: https://www.consumerfinance.gov/

**Q: Documents won't parse in CloseCheck?**  
A: Ensure PDFs are text-based (not scanned images). Try OCRing scanned documents first.

---

## For Testing Mismatches

Once you have real documents, **intentionally create variants** to test CloseCheck:
1. Copy a real Deed → Rename the buyer name slightly (Carlos → Carlos Martínez)
2. Modify prices by $5,000 between documents
3. Change closing dates across documents
4. Upload as a test package to trigger validation failures

This simulates real-world scenarios CloseCheck is built to catch.
