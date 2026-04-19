# CloseCheck — Claude Code Prompts por Día
> Copia y pega cada prompt directamente en Claude Code al inicio de cada sesión.
> Días 1 y 2 ya completados. Empieza desde el Día 3.

---

## PROMPT DE ARRANQUE (usar si la sesión se reinicia)

```
Lee PROJECT.md en la raíz del proyecto y revisa el estado actual de todos
los archivos existentes. Resume en 5 bullets qué está implementado y qué
falta según el sprint del PROJECT.md. Luego continúa con el siguiente día
pendiente sin preguntarme nada — solo ejecuta.
```

---

## DÍA 3 — Claude Integration: Document Classifier + Field Extractor

```
Lee PROJECT.md. Estado actual del proyecto:
- Día 1 completo: scaffolding, Docker Compose, FastAPI skeleton, DB models
  (ValidationJob, ValidationResult), POST /api/v1/validate acepta archivos,
  GET /api/v1/results/{job_id} retorna status
- Día 2 completo: parser.py con PyMuPDF → pdfplumber fallback compatible
  con Python 3.13, ingestion.py con save_extracted_texts/load_extracted_texts,
  _process_job extrae texto y persiste extracted.json por job, 8 tests verdes

Día 3: Integración con Claude API — clasificador de documentos + extractor de campos.

Implementa exactamente según la estructura del PROJECT.md:

1. backend/app/llm/client.py
   - Wrapper del Anthropic SDK usando CLAUDE_MODEL del .env (claude-sonnet-4-6)
   - Retry logic: 3 intentos con exponential backoff en errores 429/500
   - Método call(prompt: str, system: str = None, max_tokens: int = 1024) -> str
   - Error handling: loggear errores, raise ClaudeAPIError con mensaje claro

2. backend/app/llm/prompts.py
   - CLASSIFIER_PROMPT: usa el template exacto de la sección 5.1 del PROJECT.md
     Categorías: purchase_agreement, title_commitment, closing_disclosure, hud1,
     loan_note, mortgage_deed, insurance_binder, survey, hoa_document,
     tax_certificate, id_document, wire_instructions, other
     Output: {"document_type": "...", "confidence": 0.0-1.0, "notes": "..."}
   - EXTRACTOR_PROMPT: usa el template exacto de la sección 5.2 del PROJECT.md
   - CONSISTENCY_PROMPT: usa el template exacto de la sección 5.3 del PROJECT.md

3. backend/app/services/classifier.py
   - classify_document(text: str) -> dict
     Llama a llm/client.py con CLASSIFIER_PROMPT
     Parsea JSON response, retorna {"document_type": str, "confidence": float, "notes": str}
     Si confidence < 0.5, retorna document_type = "other"

4. backend/app/services/extractor.py
   - Campos a extraer por document_type:
     purchase_agreement: buyer_name, seller_name, property_address,
       purchase_price, closing_date, earnest_money, contingencies
     title_commitment: property_address, buyer_name, effective_date,
       expiration_date, open_liens, exceptions
     closing_disclosure: buyer_name, loan_amount, purchase_price,
       closing_date, cash_to_close, seller_credits, total_closing_costs
     hud1: buyer_name, seller_name, purchase_price, settlement_date,
       cash_to_close, total_settlement_charges
     loan_note: borrower_name, loan_amount, interest_rate, loan_type,
       maturity_date
     mortgage_deed: borrower_name, property_address, loan_amount
     insurance_binder: insured_name, property_address, coverage_amount,
       effective_date, expiration_date, mortgagee, flood_zone
     survey: property_address, surveyor_name, survey_date
     hoa_document: hoa_name, monthly_dues, outstanding_balance,
       property_address
     tax_certificate: property_address, tax_status, delinquent_amount
     wire_instructions: bank_name, account_number, routing_number,
       beneficiary_name
   - extract_fields(text: str, document_type: str) -> dict
     Llama a EXTRACTOR_PROMPT con field_list del tipo de documento
     Retorna JSON con campos extraídos, null si no encontrado

5. Actualizar backend/app/services/ingestion.py — _process_job():
   Después de guardar extracted.json, para cada archivo:
   a. Llamar classifier.classify_document(text)
   b. Llamar extractor.extract_fields(text, document_type)
   c. Guardar en fields.json por job:
      {
        "filename.pdf": {
          "document_type": "purchase_agreement",
          "confidence": 0.97,
          "fields": { "buyer_name": "Carlos Martinez", ... }
        }
      }
   d. Actualizar ValidationJob en DB: document_types JSON field con clasificaciones

6. Tests en backend/tests/unit/:
   - test_classifier.py: mock del Claude client, verificar parsing de response,
     manejo de confidence < 0.5, manejo de JSON malformado
   - test_extractor.py: mock del Claude client, verificar extracción por tipo,
     manejo de campos null, manejo de response vacío
   - test_llm_client.py: mock de anthropic SDK, verificar retry logic en 429

Criterio de éxito del Día 3:
- POST /api/v1/validate con un PDF de muestra genera fields.json con
  document_type detectado y campos extraídos
- Todos los tests nuevos pasan (green)
- Sin llamadas reales a Claude API en tests (todos mockeados)
```

---

## DÍA 4 — Rule Engine: BaseRule + Purchase Agreement + Title Rules

```
Lee PROJECT.md. Estado actual:
- Días 1-3 completos: pipeline de ingestion, extracción OCR,
  clasificación con Claude, fields.json con document_type y campos por job

Día 4: Rule Engine — BaseRule + reglas de Purchase Agreement y Title.

Implementa exactamente según PROJECT.md sección 4:

1. backend/app/rules/base.py — BaseRule
   - Clase abstracta con:
     rule_id: str
     category: str
     description: str
     severity: Literal["FAIL", "WARNING", "INFO"]
     método abstracto check(fields: dict) -> RuleResult
   - RuleResult dataclass:
     rule_id, category, description, severity, status (PASS/FAIL/WARNING/SKIP),
     detail (str), documents_referenced (list[str])

2. backend/app/rules/purchase_agreement.py
   Implementa todas las reglas de la sección 4.1 del PROJECT.md:
   - PA-001 FAIL: buyer_name y seller_name presentes y consistentes
     (usar fuzzy match: difflib.SequenceMatcher ratio > 0.85,
     normalizar acentos con unicodedata.normalize)
   - PA-002 FAIL: property_address consistente en todos los docs
     (comparar normalized address: lowercase, strip punctuation)
   - PA-003 FAIL: purchase_price presente y matches HUD/CD
     (parsear como float, diferencia <= $1 aceptable por redondeo)
   - PA-004 FAIL: closing_date presente y no expirada
     (parsear fecha, verificar >= hoy)
   - PA-005 WARNING: earnest_money documentado (campo no null)
   - PA-006 FAIL: si el texto del doc contiene "signature" o "signed",
     verificar que no diga "unsigned" o "missing signature"
   - PA-007 INFO: contingencies detectadas (buscar keywords:
     inspection, financing, appraisal en fields o texto)

3. backend/app/rules/title.py
   Implementa todas las reglas de la sección 4.2 del PROJECT.md:
   - TC-001 FAIL: title_commitment presente en los docs clasificados
   - TC-002 FAIL: property_address en title_commitment matches purchase_agreement
   - TC-003 WARNING: effective_date del title dentro de últimos 6 meses
   - TC-004 WARNING: exceptions field no null y reviewed
   - TC-005 FAIL: open_liens field es null o lista vacía
   - TC-006 FAIL: campo judgments/encumbrances null o vacío
   - TC-007 WARNING: title insurance amount (si presente) >= purchase_price

4. backend/app/services/validator.py
   - run_rules(fields_by_doc: dict, rule_modules: list) -> list[RuleResult]
   - Recibe fields.json del job, ejecuta todas las reglas disponibles
   - Para reglas cross-document: pasa dict completo {filename: fields}
   - Retorna lista de RuleResult ordenada por severity (FAIL primero)

5. Actualizar _process_job en ingestion.py:
   Después de generar fields.json:
   a. Llamar validator.run_rules con PA y TC rules
   b. Guardar results preliminares en ValidationResult en DB
   c. Actualizar job status a "processing_rules"

6. Tests en backend/tests/unit/test_rules.py:
   - Test PA-001: nombres consistentes → PASS, diferentes → FAIL,
     variación de acento (Martinez/Martínez) → FAIL con detail claro
   - Test PA-002: address igual → PASS, diferente → FAIL
   - Test PA-003: precio igual → PASS, diferencia $2500 → FAIL con detail
   - Test PA-004: fecha futura → PASS, fecha pasada → FAIL
   - Test TC-001: doc presente → PASS, ausente → FAIL
   - Test TC-005: lien presente → FAIL, sin liens → PASS

Criterio de éxito del Día 4:
- validator.run_rules() ejecuta PA y TC rules contra fields.json del Martinez test
- PA-003 detecta el mismatch de $2,500 como FAIL
- PA-001 detecta "Martinez" vs "Martínez" como FAIL con fuzzy match
- Todos los tests pasan (green)
```

---

## DÍA 5 — Rule Engine: Loan, Closing Disclosure, Insurance, Compliance Rules

```
Lee PROJECT.md. Estado actual:
- Días 1-4 completos: pipeline completo de ingestion + extracción +
  clasificación, rule engine con BaseRule, PA rules y TC rules funcionando,
  validator.run_rules() integrado en _process_job

Día 5: Completar el rule engine con las categorías restantes.

Implementa exactamente según PROJECT.md sección 4:

1. backend/app/rules/loan.py
   Reglas sección 4.3:
   - LN-001 FAIL: loan_amount consistente con purchase_price - down_payment
     (loan_amount <= purchase_price, diferencia razonable para down payment)
   - LN-002 FAIL: borrower_name en loan_note matches buyer_name en PA
     (usar mismo fuzzy match que PA-001)
   - LN-003 WARNING: interest_rate y loan_type presentes y no null
   - LN-004 FAIL: loan_note document presente en la clasificación
   - LN-005 FAIL: mortgage_deed document presente en la clasificación
   - LN-006 WARNING: LTV = loan_amount / purchase_price <= 0.97
     (conventional max 97%, FHA 96.5%)

2. backend/app/rules/closing_disclosure.py
   Reglas sección 4.4:
   - CD-001 FAIL: closing_disclosure o hud1 presente en docs clasificados
   - CD-002 FAIL: cash_to_close no null y > 0
   - CD-003 WARNING: seller_credits en CD matches seller_credits en PA
     (si ambos presentes, diferencia <= $100)
   - CD-004 WARNING: prorated_taxes campo presente en CD
   - CD-005 INFO: lender fees itemizadas (total_closing_costs no null)
   - CD-006 WARNING: total_closing_costs / purchase_price <= 0.05

3. backend/app/rules/property.py
   Reglas sección 4.5:
   - PR-001 FAIL: tax_status en tax_certificate != "delinquent"
     (si tax_certificate presente)
   - PR-002 WARNING: survey presente si transaction_type == "residential"
     y lender lo requiere (campo en fields)
   - PR-003 WARNING: hoa_document presente si campos HOA detectados en PA
   - PR-004 FAIL: outstanding_balance en hoa_document == 0 o null
   - PR-005 WARNING: certificate_of_occupancy presente si new construction
     detectado en PA (keywords: "new construction", "builder", "new home")

4. backend/app/rules/insurance.py
   Reglas sección 4.6:
   - IN-001 FAIL: insurance_binder presente en docs clasificados
   - IN-002 FAIL: coverage_amount >= loan_amount
   - IN-003 FAIL: mortgagee field contiene nombre del lender
     (fuzzy match con lender_name extraído del loan_note)
   - IN-004 FAIL: flood insurance presente si flood_zone != null
     y flood_zone != "X" (zona de bajo riesgo)
   - IN-005 FAIL: effective_date en insurance <= closing_date en PA

5. backend/app/rules/compliance.py
   Reglas sección 4.7:
   - IC-001 FAIL: id_document presente en docs clasificados
   - IC-002 WARNING: firpta_certificate presente si seller es foreign person
     (detectar en PA: keywords "foreign", "non-resident alien", "FIRPTA")
   - IC-003 FAIL: wire_instructions presentes y no modificadas
     (si wire_instructions doc presente, verificar que routing/account no null)
   - IC-004 FAIL: power_of_attorney presente y notarized si detectado en PA
     (keyword "power of attorney" o "POA" en PA)

6. backend/app/services/consistency.py
   Cross-document consistency usando CONSISTENCY_PROMPT de Claude:
   - check_consistency(fields_by_doc: dict) -> list[dict]
   - Agrupa campos clave por nombre (buyer_name, purchase_price,
     property_address, closing_date) de todos los docs
   - Llama Claude con CONSISTENCY_PROMPT para detectar mismatches sutiles
   - Retorna lista de inconsistencias con formato RuleResult compatible

7. Actualizar validator.py para correr TODAS las reglas:
   run_all_rules(fields_by_doc, transaction_type) que ejecuta
   PA + TC + LN + CD + PR + IN + IC rules y consistency checks

8. Actualizar _process_job para usar run_all_rules completo

9. Tests en backend/tests/unit/test_rules.py — agregar:
   - Test LN-001: loan > purchase_price → FAIL
   - Test LN-006: LTV 0.80 → PASS, LTV 0.98 → WARNING
   - Test IN-002: coverage < loan → FAIL, coverage >= loan → PASS
   - Test IN-005: insurance effective después del closing → FAIL
   - Test CD-006: closing costs 6% → WARNING, 4% → PASS
   - Test IC-003: wire instructions con routing null → FAIL

Criterio de éxito del Día 5:
- run_all_rules() ejecuta las 42 reglas contra un job de prueba
- GET /api/v1/results/{job_id} retorna results array con todas las reglas evaluadas
- summary.total_rules == 42 (o número real de reglas implementadas)
- Todos los tests pasan (green)
```

---

## DÍA 6 — Report Builder + Cross-Doc Consistency + Executive Summary

```
Lee PROJECT.md. Estado actual:
- Días 1-5 completos: pipeline completo de ingestion, extracción,
  clasificación, y rule engine completo con las 42 reglas en 7 categorías.
  GET /api/v1/results/{job_id} retorna results array básico.

Día 6: Report Builder — agregar executive summary, conflict cards,
action plan y cross-doc consistency al response final.

Implementa:

1. backend/app/services/report_builder.py
   build_report(job_id, fields_by_doc, rule_results, consistency_results) -> dict
   Genera el response completo de GET /api/v1/results/{job_id} según
   el API contract exacto del PROJECT.md sección 7:
   {
     "job_id": uuid,
     "status": "completed",
     "overall": "PASS" | "WARNING" | "FAIL",  // FAIL si hay 1+ FAIL, WARNING si hay 1+ WARNING sin FAILs
     "summary": {
       "total_rules": N,
       "passed": N,
       "warnings": N,
       "failed": N
     },
     "documents": [
       {"filename": str, "document_type": str, "confidence": float, "status": "ok"|"warn"|"missing"}
     ],
     "results": [ ...RuleResult objects... ],
     "executive_brief": [ ...5 bullet strings... ],
     "conflicts": [ ...conflict cards... ],
     "action_plan": [ ...action items... ],
     "completed_at": datetime
   }

2. Agregar executive_brief al report via Claude:
   - Llamar Claude con este prompt:
     "You are a real estate closing specialist. Based on these validation
     results, write exactly 5 concise bullet points for a closing coordinator.
     Focus on what needs immediate attention. Be specific with amounts and names.
     Validation results: {rule_results_json}
     Return JSON: {"bullets": ["...", "...", "...", "...", "..."]}"
   - Implementar en llm/prompts.py como EXECUTIVE_BRIEF_PROMPT

3. Agregar conflicts array (las conflict cards del UI):
   Solo los rules con status FAIL o WARNING que tienen doc_a/doc_b comparison:
   {
     "rule_id": "PA-003",
     "type": "Price mismatch",
     "severity": "FAIL",
     "field": "purchase_price",
     "doc_a": "purchase_agreement.pdf",
     "value_a": "$385,000",
     "doc_b": "closing_disclosure.pdf",
     "value_b": "$387,500",
     "message": "Purchase price mismatch of $2,500",
     "resolved": false
   }

4. Agregar action_plan via Claude:
   - Llamar Claude con este prompt:
     "You are a real estate closing coordinator. Based on these conflicts,
     generate a prioritized action plan. Return JSON array of action items:
     [{"title": str, "description": str, "urgency": "now"|"today"|"soon",
       "owner": "coordinator"|"lender"|"builder"|"buyer",
       "is_blocker": bool}]
     Order by urgency. Conflicts: {conflicts_json}"
   - Implementar en llm/prompts.py como ACTION_PLAN_PROMPT

5. Agregar endpoint de email draft:
   POST /api/v1/jobs/{job_id}/draft-email
   Body: {"conflict_rule_id": "PA-003", "recipient": "lender"}
   Responde con:
   {"subject": str, "body": str}
   Usando Claude con el contexto del conflict específico.
   Implementar en api/v1/validate.py

6. Actualizar GET /api/v1/results/{job_id} para retornar el report completo
   del report_builder (no solo rule_results básicos)

7. Tests en backend/tests/unit/test_report_builder.py:
   - Test overall FAIL: 1+ FAIL rules → overall = "FAIL"
   - Test overall WARNING: 0 FAILs, 1+ WARNINGs → overall = "WARNING"
   - Test overall PASS: 0 FAILs, 0 WARNINGs → overall = "PASS"
   - Test conflicts extraction: solo rules con FAIL/WARNING status
   - Test documents status: doc clasificado con confianza → "ok",
     doc requerido ausente → "missing"
   - Mock Claude para executive_brief y action_plan

8. Test de integración en backend/tests/integration/test_validate_endpoint.py:
   - POST /validate con archivos PDF de muestra (crear fixtures mínimos)
   - Verificar response 202 con job_id
   - GET /results/{job_id} eventualmente retorna status "completed"
   - Response incluye executive_brief, conflicts, action_plan

Criterio de éxito del Día 6:
- GET /api/v1/results/{job_id} retorna el objeto completo con:
  overall triage, summary stats, documents list, rule results,
  executive_brief (5 bullets), conflicts array, action_plan
- POST /draft-email retorna subject + body listo para enviar
- Todos los tests pasan (green)
```

---

## DÍA 7 — Frontend: Upload Page + FileDropzone + API Integration

```
Lee PROJECT.md. Estado actual:
- Días 1-6 completos: backend 100% funcional.
  GET /api/v1/results/{job_id} retorna triage, summary, documents,
  rule results, executive_brief, conflicts, action_plan.
  POST /draft-email genera email por conflict.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️  REFERENCIA DE DISEÑO OBLIGATORIA — LEER PRIMERO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Antes de escribir una sola línea de frontend, abre y lee
docs/ui-reference/pre_close_validator_ux.html en su totalidad.
Este es el diseño aprobado del producto. Toda implementación
del frontend debe replicarlo fielmente. No improvises colores,
tipografía, ni spacing — replica exactamente lo que está en ese HTML.

TIPOGRAFÍA (obligatoria):
  - Sora: body, UI labels, botones, tabs, navegación
  - DM Mono: valores numéricos, file badges, campos extraídos,
    montos ($385,000), fechas en campos técnicos
  - Importar ambas desde Google Fonts en index.html
  - NUNCA usar Inter, Roboto, Arial ni system fonts

PALETA DE COLORES — usar exactamente estos hex values:
  Backgrounds:
    --bg:           #ffffff   (primary surfaces)
    --bg-secondary: #f7f7f5   (hover states, headers de cards)
    --bg-tertiary:  #f0efe9   (page background)
  Text:
    --text-primary:   #1a1a18
    --text-secondary: #5f5e5a
    --text-tertiary:  #888780
  Borders:
    default: 0.5px solid rgba(0,0,0,0.10)
    hover:   0.5px solid rgba(0,0,0,0.18)
    NUNCA usar 1px borders (excepto featured/accent items)
  Status amber (Needs review):
    bg #FAEEDA · text #854F0B · border #FAC775
  Status green (Ready):
    bg #EAF3DE · text #3B6D11 · border #C0DD97
  Status red (Blocked):
    bg #FCEBEB · text #A32D2D · border #F09595
  Conflict mismatch value: bg #FCEBEB · text #A32D2D
  Conflict ok value: text #3B6D11 (sin background)

COMPONENTES DEL HTML A REPLICAR EXACTAMENTE:
  .topbar       → logo "CloseCheck" (uppercase, letter-spacing 0.08em)
                  + file badge en DM Mono (pill redondeado)
  .tabs         → 3 tabs con border-bottom 2px activo, sin fondo
  .triage-hero  → status pill (border-radius 40px) + brief bullets
                  con dot indicator (4px circle) por bullet
  .conflict-card → border 0.5px, border-radius 12px
                   header con bg-secondary, type label + severity badge
                   body: 3 columnas (ok-value | ≠ | mismatch-value)
                   footer: botones "Mark resolved" + "Escalate"
  .doc-chip     → border 0.5px, icon cuadrado 20px, status dot 6px
  .drop-zone    → border 1.5px dashed, SVG icon 22px, copy exacto
  .bottom-bar   → border-top 0.5px, next step text + primary button
  .scan-overlay → fondo rgba(255,255,255,0.96), spinner CSS puro

COMPORTAMIENTO INTERACTIVO (preservar del HTML):
  - Tab switching: sin reload, border-bottom activo se mueve
  - toggleResolved(): "Mark resolved" → "Done ✓" + clase .resolved
    (bg #EAF3DE, color #3B6D11, border #C0DD97)
  - startScan(): 5 steps secuenciales con 900ms de intervalo:
    "Ingesting documents" → "Running OCR…" → "Extracting key fields…"
    → "Cross-referencing docs…" → "Generating executive brief…"
  - Hover en conflict-card: border-color cambia a rgba(0,0,0,0.18)
  - Hover en doc-chip: mismo efecto de border

TAILWIND CONFIG:
  En tailwind.config.js agregar:
  theme: {
    extend: {
      fontFamily: {
        sans: ['Sora', 'sans-serif'],
        mono: ['DM Mono', 'monospace'],
      },
      colors: {
        'cc-amber': { bg: '#FAEEDA', text: '#854F0B', border: '#FAC775' },
        'cc-green': { bg: '#EAF3DE', text: '#3B6D11', border: '#C0DD97' },
        'cc-red':   { bg: '#FCEBEB', text: '#A32D2D', border: '#F09595' },
      },
      borderWidth: { 'half': '0.5px' },
    }
  }
  Para bordes 0.5px y colores exactos no disponibles en Tailwind base,
  usar CSS inline o clases @layer components en index.css.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Día 7: Frontend — Upload page + FileDropzone + conexión a API.

Implementa exactamente según la estructura del PROJECT.md sección 6 frontend/src/:

1. frontend/src/api/client.js
   - Axios instance con baseURL = VITE_API_BASE_URL
   - Header X-API-Key: VITE_API_KEY en cada request
   - Funciones:
     submitJob(files, transactionType) → POST /api/v1/validate multipart
     getResults(jobId) → GET /api/v1/results/{job_id}
     draftEmail(jobId, ruleId, recipient) → POST /api/v1/jobs/{job_id}/draft-email

2. frontend/src/hooks/useValidationJob.js
   - submitJob(files) → llama API, guarda job_id en state
   - pollStatus(jobId) → polling cada 2s a getResults
   - Para cuando status === "completed" o "failed"
   - Expone: { jobId, status, isLoading, error, submit }

3. frontend/src/pages/Upload.jsx
   Replicar el tab "New file" del mockup docs/ui-reference/pre_close_validator_ux.html:
   - Topbar con logo "CLOSECHECK" + badge con nombre del archivo activo
   - DropZone con:
     - Border 1.5px dashed rgba(0,0,0,0.18)
     - SVG upload icon 22px en container 44px bg-secondary border-radius 8px
     - Texto: "Drop the closing file folder here" (Sora 14px, font-weight 500)
     - Subtext: "PDF, DOCX — up to 20 files, 25MB each" (12px, text-tertiary)
     - Hover: border-color rgba(0,0,0,0.30), bg-secondary
   - Lista de archivos seleccionados: nombre en DM Mono + tamaño
   - Botón "Validate File →" (primary): bg text-primary, color white,
     border-radius 20px, Sora 12px font-weight 500
   - Al submitJob exitoso → navegar a /processing/{job_id}

4. frontend/src/components/FileDropzone.jsx
   - Drag-and-drop con react-dropzone
   - Accept: application/pdf, .docx
   - Max 20 files, max 25MB each
   - Mostrar error si se exceden límites (texto en cc-red.text)
   - Prop: onFilesSelected(files)

5. frontend/src/pages/Processing.jsx
   Replicar el .scan-overlay del mockup exactamente:
   - Background: rgba(255,255,255,0.96) fijo sobre toda la pantalla
   - Spinner: div 48x48px, border 2px solid rgba(0,0,0,0.10),
     border-top-color #1a1a18, border-radius 50%
     Animación CSS: @keyframes spin { to { transform: rotate(360deg) } }
     animation: spin 1s linear infinite
   - Texto principal: "Reviewing file…" (Sora 14px, font-weight 500,
     color text-secondary)
   - Subtext dinámico (DM Mono 12px, text-tertiary), cambia cada 900ms:
     "Ingesting documents" → "Running OCR…" →
     "Extracting key fields…" → "Cross-referencing docs…" →
     "Generating executive brief…"
   - useValidationJob polling en background
   - Cuando status === "completed" → navegar a /results/{job_id}
   - Cuando status === "failed" → mostrar error y botón "Try again"

6. frontend/src/utils/severity.js
   - severityColor(s): "FAIL"→"#A32D2D", "WARNING"→"#854F0B", "PASS"→"#3B6D11"
   - severityBg(s): "FAIL"→"#FCEBEB", "WARNING"→"#FAEEDA", "PASS"→"#EAF3DE"
   - severityBorder(s): "FAIL"→"#F09595", "WARNING"→"#FAC775", "PASS"→"#C0DD97"
   - triageLabel(o): "FAIL"→"Blocked", "WARNING"→"Needs review", "PASS"→"Ready to close"

7. frontend/src/utils/formatters.js
   - formatCurrency(str): "$385000" o 385000 → "$385,000"
   - formatDate(str): parsear ISO y formatear a "Apr 25, 2026"
   - truncateFilename(name, maxLen=20): cortar con "..."

8. Configuración base:
   - vite.config.js: proxy /api → http://localhost:8000 (dev)
   - tailwind.config.js: Sora en fontFamily.sans, tokens cc-* (ver arriba)
   - index.html: import Google Fonts (Sora 300,400,500 + DM Mono 400,500)
   - React Router: rutas /, /processing/:jobId, /results/:jobId
   - App.jsx con BrowserRouter y rutas

Criterio de éxito del Día 7:
- http://localhost:3000 muestra Upload page idéntica al tab "New file" del mockup
- Drag-and-drop de PDFs muestra lista de archivos con nombres en DM Mono
- Click "Validate File →" hace POST al backend y navega a /processing/{job_id}
- Processing page muestra spinner y steps animados idénticos al scan-overlay del mockup
- Cuando el job completa, navega automáticamente a /results/{job_id}
- Colores, tipografía y borders son pixel-faithful al HTML de referencia
```

---

## DÍA 8 — Frontend: Report Page + Componentes de UI

```
Lee PROJECT.md. Estado actual:
- Días 1-7 completos: backend 100% funcional, frontend con Upload y
  Processing pages funcionando, polling conectado al backend.
  Navegación Upload → Processing → Results (placeholder) funciona.
  Tailwind configurado con tokens cc-*, fuentes Sora + DM Mono activas.

Día 8: Frontend — Report page completa con todos los componentes del mockup.

⚠️  El diseño de referencia está en docs/ui-reference/pre_close_validator_ux.html.
Ábrelo y léelo completo antes de implementar cualquier componente.
Todos los estilos, colores, bordes y tipografía del Día 7 aplican aquí también.
El tab "Result" del HTML es el Report page. Replica pixel-faithful.

Implementa exactamente los componentes del PROJECT.md sección 6:

1. frontend/src/components/SummaryBanner.jsx
   Basado en el "triage-hero" del mockup:
   - Pill de triage: verde/ámbar/rojo según overall
   - Label: "Ready to close" | "Needs review" | "Blocked"
   - Executive brief: 5 bullets del response
     Bullet con flagged styling (color ámbar) si contiene precio/monto
   - Props: { overall, executiveBrief }

2. frontend/src/components/RuleResult.jsx — ConflictCard
   Basado en las conflict cards del mockup:
   - Header: conflict type (rule description) + severity badge
   - Body: dos columnas lado a lado
     Doc A: nombre del doc + valor (en verde si es el "correcto")
     Símbolo ≠ en el centro
     Doc B: nombre del doc + valor (en rojo con background si es el mismatch)
   - Footer: botones "Mark resolved" + "Escalate"
     "Mark resolved" toggle estado local (verde cuando done)
   - Props: { conflict, onResolve, onEscalate }

3. frontend/src/components/CategorySection.jsx
   Para mostrar reglas agrupadas por categoría:
   - Header con nombre de categoría e ícono
   - Lista de RuleResult cards filtradas por categoría
   - Collapsible (expandir/colapsar sección)
   - Props: { category, rules, defaultExpanded }

4. frontend/src/components/ProgressBar.jsx — DocGrid
   Basado en el tab "Documents" del mockup:
   - Grid de chips por documento
   - Cada chip: ícono del tipo (PDF/DOCX) + nombre truncado + dot de status
     Verde: clasificado sin conflictos
     Ámbar: tiene warnings
     Rojo: falta o tiene FAILs
   - Props: { documents }

5. frontend/src/components/DownloadButton.jsx
   - Botón "Download Report" que llama GET /api/v1/report/{job_id}/pdf
   - Loading state mientras descarga
   - Props: { jobId }

6. frontend/src/hooks/useReport.js
   - fetchReport(jobId) → GET /api/v1/results/{job_id}
   - Expone: { report, isLoading, error }
   - No pollea (el job ya completó al llegar aquí)

7. frontend/src/pages/Report.jsx
   Layout completo del mockup — 3 tabs:

   TAB "Result":
   - SummaryBanner (triage + executive brief)
   - Sección "Conflicts detected — N of M docs"
   - Lista de ConflictCards para cada conflict
   - Bottom bar: "Suggested: [next step]" + botón "Generate action plan →"
     El botón abre ActionPlanModal

   TAB "Documents":
   - DocGrid con todos los documentos procesados

   TAB "Rules":
   - CategorySection por cada categoría (PA, TC, LN, CD, PR, IN, IC)
   - Cada sección colapsable, FAIL primero

8. ActionPlanModal (component inline en Report.jsx):

   ⚠️  REFERENCIA DE DISEÑO OBLIGATORIA PARA ESTE COMPONENTE:
   Abre y lee C:\Dev\apps\closecheck\docs\ui-reference\martinez_action_plan.html
   ANTES de escribir una sola línea de este componente.
   Replica pixel-faithful ese HTML. No improvises layout, colores ni spacing.

   Especificaciones exactas del HTML de referencia:

   ESTRUCTURA GENERAL:
   - Modal con max-width 680px, padding 24px, bg #ffffff
   - border 0.5px solid rgba(0,0,0,0.10), border-radius 12px

   FILE ROW (parte superior):
   - Izquierda: file ID en DM Mono 12px color #888780
     Formato: "{buyer}_{address} — Action Plan"
   - Derecha: triage badge pill
     bg #FAEEDA · color #854F0B · border 0.5px #FAC775
     font-size 11px · font-weight 500 · border-radius 20px · padding 4px 12px

   METRIC CARDS (grid 4 columnas):
   - background #f7f7f5, border-radius 8px, padding 12px
   - Label: 10px, font-weight 500, letter-spacing 0.08em, uppercase, color #888780
   - Valor: 14px, font-weight 500, color #1a1a18
   - Valor danger (conflicts, missing): color #A32D2D
   - Gap entre cards: 10px

   BLOCKER BOX:
   - border 0.5px solid #F09595, border-radius 12px
   - background #FCEBEB, padding 14px, margin-bottom 28px
   - Label: 10px uppercase, font-weight 500, color #A32D2D, letter-spacing 0.08em
   - Items: font-size 12px, color #791F1F, line-height 1.6
   - Dot por item: 4px circle, background #E24B4A, posición absoluta left 0

   ACTION ITEMS (lista vertical, gap 8px):
   Cada item: border 0.5px solid rgba(0,0,0,0.10), border-radius 12px

   Header del item (padding 12px 14px):
   - Step number circle 22x22px, border-radius 50%:
     Steps 1-2 (Do now):   bg #FCEBEB · color #A32D2D
     Step 3 (Today):       bg #FAEEDA · color #854F0B
     Step 4 (After/Soon):  bg #f7f7f5 · color #5f5e5a
   - Title: 13px, font-weight 500, color #1a1a18, flex:1
   - Urgency tag pill (margin-left auto):
     "Do now":         bg #FCEBEB · color #A32D2D
     "Today":          bg #FAEEDA · color #854F0B
     "After steps 1–3": bg #f7f7f5 · color #5f5e5a
     font-size 10px, font-weight 500, border-radius 20px, padding 2px 8px

   Body del item (padding 10px 14px 13px 48px):
   - border-top 0.5px solid rgba(0,0,0,0.10)
   - Descripción: 12px, color #5f5e5a, line-height 1.6
   - Who-row: flex, gap 6px, margin-top 8px
   - Who chips: 10px, bg #f7f7f5, color #5f5e5a,
     padding 2px 8px, border-radius 20px, border 0.5px
   - "Mark done" button (margin-left auto):
     Default: 11px, font-weight 500, padding 4px 12px,
       border-radius 20px, border 0.5px solid rgba(0,0,0,0.18),
       bg transparent, color #5f5e5a
     Completed (.completed): bg #EAF3DE, color #3B6D11, border-color #C0DD97
     Texto completado: "Done ✓"

   BOTTOM ROW (border-top 0.5px, padding-top 8px):
   - Progress area (flex:1):
     Label: "N of 4 steps completed" — 11px, color #888780, margin-bottom 6px
     Track: height 4px, bg #f7f7f5, border-radius 4px
     Fill: height 4px, bg #639922, border-radius 4px
     Transition: width 0.4s ease — se actualiza al marcar cada step
   - "Draft lender email →" button:
     bg #1a1a18, color #ffffff, font-size 12px, font-weight 500
     border-radius 20px, padding 8px 16px, border none

   INTERACTIVIDAD a implementar en React:
   - Estado local: completedSteps = {} (objeto por step index)
   - markDone(stepIndex): toggle completed[stepIndex]
     Actualiza label "N of 4 steps completed" y ancho del fill
   - "Draft lender email →": llama onDraftEmail() prop → abre EmailDraftModal

9. EmailDraftModal — frontend/src/components/EmailDraftModal.jsx

   ⚠️  REFERENCIA DE DISEÑO OBLIGATORIA PARA ESTE COMPONENTE:
   Abre y lee C:\Dev\apps\closecheck\docs\ui-reference\email_draft_modal.html
   ANTES de escribir una sola línea de este componente.
   Replica pixel-faithful ese HTML. No improvises layout, colores ni spacing.

   PROPS del componente:
   {
     isOpen: bool,
     onClose: () => void,
     jobId: string,
     conflict: { rule_id, type, field, doc_a, value_a, doc_b, value_b },
     closingDate: string,
     onDraftLoaded: (draft) => void
   }

   ESTRUCTURA EXACTA (replicar del HTML de referencia):

   TOPBAR:
   - Logo "CloseCheck" (Sora 13px, uppercase, letter-spacing 0.08em, color #5f5e5a)
   - Conflict pill (derecha):
     bg #FCEBEB · color #A32D2D · border 0.5px #F09595 · border-radius 20px
     dot 6px circle + texto "{conflict.type} — {conflict.rule_id}"
     Sora 11px font-weight 500

   CONTEXT BAR (bg #f7f7f5, border-bottom 0.5px):
   4 ítems separados por divisores verticales 0.5px de 28px de alto:
   - File: valor en DM Mono 12px — "{buyer}_{address}" del job
   - Recipient: "Lender — closing dept."
   - Discrepancy: valor en DM Mono, color #A32D2D — diferencia calculada
   - Closing date: fecha en DM Mono del job
   Cada ítem: label 10px uppercase color #888780 + valor debajo

   VARIANT TABS (padding 16px 24px 0, gap 8px):
   Dos botones tab:
   - "Professional & direct" (tab-pro):
     Default: bg #f7f7f5, color #5f5e5a, border 0.5px rgba(0,0,0,0.10)
     Active:  bg #ffffff, color #1a1a18, border 0.5px rgba(0,0,0,0.18)
   - "Urgent — closing at risk" (tab-urg):
     Default: bg #f7f7f5, color #5f5e5a, border 0.5px rgba(0,0,0,0.10)
     Active:  bg #FCEBEB, color #A32D2D, border 0.5px #F09595
   border-radius 8px, Sora 12px font-weight 500, padding 8px 16px

   PANE PROFESIONAL (visible por defecto):
   - Tone tag: bg #f7f7f5, color #5f5e5a, border 0.5px
     Texto: "Normal lender relationship · gives space to respond"
   - Subject row: label "SUBJECT" + valor en DM Mono 12px
     bg #f7f7f5, padding 6px 10px, border-radius 8px, border 0.5px
   - Textarea email body:
     font-family DM Mono 12px, line-height 1.7
     bg #f7f7f5, border 0.5px, border-radius 12px, padding 14px
     min-height 240px, resize vertical
     Focus: border-color rgba(0,0,0,0.30)
   - Char count: DM Mono 10px, color #888780, text-align right, margin-top 4px

   PANE URGENTE (oculto por defecto, visible al click tab-urg):
   - Tone tag: bg #FCEBEB, color #A32D2D, border 0.5px #F09595
     Texto: "Hard deadline · documents closing risk"
   - Subject row: igual pero subject-val con:
     color #A32D2D, bg #FCEBEB, border-color #F09595
   - Textarea: mismos estilos que pane pro
   - Char count: igual

   CONTENIDO DE LOS EMAILS (poblar desde POST /draft-email):
   La API retorna { subject_pro, body_pro, subject_urg, body_urg }.
   Mientras carga: mostrar spinner centrado en lugar del pane
   (spinner: 32px circle, border 1.5px, border-top-color #1a1a18, spin 1s)

   BOTTOM ACTIONS (border-top 0.5px, padding 14px 24px):
   - Izquierda: note bar
     dot 5px circle bg #EF9F27 + texto 11px color #888780:
     "Both paths documented — corrected CD or written confirmation"
   - Derecha: btn-group (gap 8px)
     "Copy email" (btn-outline):
       border 0.5px rgba(0,0,0,0.18), bg transparent, color #5f5e5a
       Al copiar: color #3B6D11, bg #EAF3DE, border #C0DD97, texto "Copied ✓"
       Vuelve a estado default después de 2000ms
     "Open in Mail →" (btn-primary):
       Pro:    bg #1a1a18, color #ffffff
       Urgente: bg #A32D2D, color #ffffff
       border-radius 20px, Sora 12px font-weight 500

   COMPORTAMIENTO INTERACTIVO en React:
   - Estado: activeVariant ('pro' | 'urg'), emailDraft (null | {subject_pro, body_pro, subject_urg, body_urg})
   - Al abrir el modal (isOpen = true):
     1. Mostrar spinner de loading
     2. Llamar draftEmail(jobId, conflict.rule_id, 'lender')
     3. Poblar ambos panes con la respuesta
     4. Mostrar pane pro por defecto
   - switchVariant(v): toggle activeVariant, actualizar clases de tabs
     y cambiar color del btn "Open in Mail →"
   - copyEmail(): copiar "Subject: {subj}\n\n{body}" al clipboard
     Usar navigator.clipboard.writeText(), fallback con execCommand('copy')
   - openMail(): construir mailto: con subject y body del pane activo
     window.location.href = 'mailto:?subject=...&body=...'
   - El textarea es editable — el coordinador puede modificar antes de enviar
   - updateCount(): actualizar char count en tiempo real con oninput

   PRESENTACIÓN COMO MODAL:
   - Overlay: fondo rgba(0,0,0,0.35) sobre toda la pantalla
   - Modal centrado: max-width 720px, max-height 90vh, overflow-y auto
   - Cerrar al click en overlay o botón X en topbar (agregar X button)
   - Usar z-index 200 (sobre el ActionPlanModal que es z-index 100)

Criterio de éxito del Día 8:
- /results/{job_id} muestra el Report completo con las 3 tabs funcionando
- ConflictCards muestran el mismatch side-by-side con datos reales del backend
- "Mark resolved" toggle funciona en estado local
- ActionPlanModal es pixel-faithful a C:\Dev\apps\closecheck\docs\ui-reference\martinez_action_plan.html
- Progress bar se actualiza en tiempo real al marcar steps
- EmailDraftModal es pixel-faithful a C:\Dev\apps\closecheck\docs\ui-reference\email_draft_modal.html
- Tab "Professional & direct" activo por defecto, "Urgent" cambia colores a rojo
- "Copy email" copia subject + body al clipboard con feedback "Copied ✓"
- "Open in Mail →" abre cliente de email nativo con datos pre-llenados
- El flujo completo Upload → Processing → Report → ActionPlan → EmailDraft funciona end-to-end
```

---

## DÍA 9 — PDF Report Generation

```
Lee PROJECT.md. Estado actual:
- Días 1-8 completos: frontend y backend completamente integrados.
  Flujo Upload → Processing → Report funciona end-to-end.
  Todos los componentes del Report page funcionando.

Día 9: Generación de PDF report descargable.

Implementa:

1. backend/app/api/v1/reports.py — GET /api/v1/report/{job_id}/pdf
   - Recibe job_id, carga el report del DB
   - Genera PDF y retorna como FileResponse
   - Content-Type: application/pdf
   - Filename: CloseCheck_{job_id[:8]}.pdf

2. PDF con ReportLab (preferido) o WeasyPrint:
   Si ReportLab:
     pip install reportlab
   Si WeasyPrint (más fácil de estilizar con CSS):
     pip install weasyprint

   Estructura del PDF (1-3 páginas):

   PÁGINA 1 — Executive Summary:
   - Header: logo "CloseCheck" + fecha + job ID
   - Triage badge grande: PASS / WARNING / FAIL en verde/ámbar/rojo
   - Summary stats: total rules, passed, warnings, failed en grid 2x2
   - Executive brief: 5 bullets
   - Lista de documentos procesados con status dots

   PÁGINA 2 — Conflicts & Action Plan:
   - Sección "Conflicts Detected" con tabla:
     | Rule ID | Type | Severity | Doc A | Value A | Doc B | Value B |
   - Sección "Action Plan" con lista numerada de action items
     con urgency y owner indicados

   PÁGINA 3 — Full Rule Results:
   - Tabla completa de todas las reglas agrupadas por categoría
   - Columnas: Rule ID | Description | Status | Detail
   - Color coding: rojo para FAIL, ámbar para WARNING, verde para PASS

3. backend/app/services/pdf_generator.py
   - generate_pdf(report: dict, output_path: str) -> str
   - Recibe el report dict completo del report_builder
   - Guarda en REPORTS_DIR/{job_id}.pdf
   - Retorna path del archivo

4. Actualizar reports.py router:
   - Si el PDF ya existe en REPORTS_DIR, servirlo directamente (cache)
   - Si no existe, generarlo y servirlo

5. Actualizar DownloadButton.jsx en frontend:
   - Llamar GET /api/v1/report/{job_id}/pdf
   - Trigger download con blob URL
   - Mostrar loading mientras genera
   - Mostrar error si falla

6. Tests en backend/tests/unit/test_report_builder.py:
   - Test generate_pdf: mock del report dict, verificar que se crea archivo
   - Test endpoint: GET /report/{job_id}/pdf retorna 200 con content-type PDF

Criterio de éxito del Día 9:
- Click en "Download Report" en el frontend descarga un PDF real
- PDF tiene al menos 2 páginas con summary y conflict table
- Triage badge visible en color correcto en la página 1
- PDF se cachea: segunda descarga es instantánea
```

---

## DÍA 10 — End-to-End Testing + Demo Prep + README

```
Lee PROJECT.md. Estado actual:
- Días 1-9 completos: producto funcional end-to-end.
  Upload → OCR → Clasificación → 42 Reglas → Report → PDF descargable.

Día 10: Testing con docs reales + edge cases + pulir para portfolio.

1. Sample docs de prueba — crear en /sample-docs/Martinez_test/:
   Generar 4 PDFs de prueba con Python (usando reportlab) que simulen:

   a. purchase_agreement.pdf:
      - buyer_name: "Carlos Martinez"
      - seller_name: "John and Susan Sellars"
      - property_address: "4521 Oak Lane, Charlotte, NC 28277"
      - purchase_price: "$385,000"
      - closing_date: 30 días desde hoy (fecha dinámica)
      - earnest_money: "$5,000"

   b. closing_disclosure.pdf:
      - buyer_name: "Carlos Martinez"
      - purchase_price: "$387,500"   ← MISMATCH INTENCIONAL con PA
      - loan_amount: "$308,000"
      - cash_to_close: "$82,500"
      - closing_date: misma fecha que PA

   c. lender_commitment.pdf:
      - buyer_name: "Carlos Martínez"  ← MISMATCH INTENCIONAL (acento)
      - loan_amount: "$308,000"
      - interest_rate: "6.75%"
      - loan_type: "Conventional"
      - expiration_date: 60 días desde hoy

   d. title_binder.pdf:
      - property_address: "4521 Oak Lane, Charlotte, NC 28277"
      - buyer_name: "Carlos Martinez"
      - effective_date: fecha de hoy
      - open_liens: "None"

   (builder_invoice AUSENTE — otro conflict intencional)

2. Test end-to-end con Martinez_test/:
   Script backend/tests/integration/test_martinez_e2e.py:
   - POST /validate con los 4 PDFs
   - Polling hasta status "completed"
   - Verificar:
     overall == "FAIL" (por mismatch de precio PA-003)
     PA-001 FAIL detectado (Martinez vs Martínez)
     PA-003 FAIL detectado ($385,000 vs $387,500)
     PR-005 WARNING (builder invoice ausente — nuevo construction check)
     executive_brief menciona ambas inconsistencias
     action_plan tiene al menos 2 is_blocker == true
     conflicts array tiene 2+ items

3. Edge cases — tests adicionales:
   - POST /validate con 0 archivos → 422
   - POST /validate con archivo .xlsx → 422 (formato no soportado)
   - POST /validate con PDF corrupto → job status "failed" con error message
   - GET /results/{uuid-inexistente} → 404
   - POST /validate con 21 archivos → 422 (max 20)

4. Performance check:
   - Medir tiempo total del flujo Martinez (4 PDFs):
     target < 30 segundos end-to-end
   - Si > 30s, identificar bottleneck (OCR vs Claude API calls)
   - Agregar timing logs en _process_job para cada fase

5. README.md en la raíz del proyecto:
   # CloseCheck — AI Pre-Close File Validator
   
   Secciones:
   - What it does (2 párrafos, orientado a portfolio)
   - Tech stack (tabla del PROJECT.md)
   - Architecture diagram (ASCII del PROJECT.md)
   - Quick start:
     git clone ...
     cp backend/.env.example backend/.env
     # Add ANTHROPIC_API_KEY to .env
     docker-compose up
     # Open http://localhost:3000
   - Demo walkthrough (5 pasos con screenshots placeholder)
   - Validation rules (42 reglas en tabla, referencia al PROJECT.md)
   - API reference (2 endpoints principales)
   - Portfolio note: "Built in 2 weeks as a portfolio piece demonstrating
     AI document intelligence for real estate closing operations."

6. Pulir para demo:
   - Asegurar que docker-compose up funciona limpio en cold start
   - Verificar que .env.example tiene todas las variables documentadas
   - Agregar health check endpoint: GET /api/v1/health → {"status": "ok"}
   - Verificar CORS configurado correctamente para localhost:3000
   - Screenshot del Report page con datos del Martinez test para README

Criterio de éxito del Día 10:
- Test Martinez e2e pasa: overall FAIL, PA-001 y PA-003 detectados
- docker-compose up && open http://localhost:3000 funciona de cero
- README listo para pegar en GitHub como portfolio piece
- El flujo completo corre en < 30 segundos
- Zero errores 500 en los edge cases probados
```

---

## PROMPTS DE DEBUGGING (usar si algo falla)

### Si Claude API no responde:
```
El Claude API client está fallando. Revisa backend/app/llm/client.py.
Verifica que ANTHROPIC_API_KEY está en .env y que el modelo es claude-sonnet-4-6.
Agrega logging detallado de cada request/response. Corre un test minimal
que llame al client directamente y muestra el error exacto.
```

### Si el OCR no extrae bien el texto:
```
El parser.py no está extrayendo bien el texto de los PDFs de prueba.
Revisa backend/app/services/parser.py. Prueba primero con pdfplumber
(más robusto para PDFs complejos). Agrega un endpoint de debug:
GET /api/v1/debug/extract/{job_id} que retorne el texto crudo extraído
de cada archivo para poder inspeccionarlo.
```

### Si los tests fallan por imports:
```
Los tests están fallando por ImportError o ModuleNotFoundError.
Verifica que backend/app/__init__.py y todos los __init__.py de
subdirectorios existen. Asegura que conftest.py en tests/ agrega
el path correcto con sys.path. Muéstrame el error exacto del
stack trace y lo resolvemos.
```

### Si el frontend no conecta al backend:
```
El frontend no está llegando al backend. Verifica:
1. vite.config.js tiene el proxy correcto: /api → http://localhost:8000
2. El backend tiene CORS habilitado para http://localhost:3000
3. frontend/.env tiene VITE_API_BASE_URL=http://localhost:8000
Agrega un test simple: fetch('/api/v1/health') desde la consola del browser.
```

---

*Generado el 2026-04-19 | CloseCheck MVP Sprint — RDApps.com*
