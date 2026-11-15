# Documentation claim auditor

An offline audit tool comparing Markdown promises about structured Carte Vitale fields with Python source fingerprints. It does not process card images or extract their data. Python 3.9 or newer is required; there are no runtime dependencies.

```text
french-health-card-extraction-claim-audit 0.1.0
```

## Usage

```sh
python3 -m pip install .
french-health-card-extraction-claim-audit audit [repo] --json --fail-on medium
python3 -m french_health_card_extraction_claim_audit audit . --verbose --ignore vendor --ignore .verification
french-health-card-extraction-claim-audit --version
```

The repository defaults to the current directory. Each ignore option takes one path prefix and may be repeated before or after the repository argument. The threshold accepts lowercase high (default) or medium. Exit status is 0 when no finding reaches the threshold, 2 when one does, and 1 for usage or I/O errors. JSON includes verdict, findings, claims, evidence, and source_files; each finding contains rule, severity, message, and claims. A MEDIUM finding still makes the report verdict FAIL even when the default threshold returns 0.

## Matching and evidence

Only root README.md and Markdown files beneath any docs path component supply claims. Blank lines delimit paragraphs. Matching lowercases text, expands contractions, replaces hyphens with spaces, collapses whitespace, and uses word boundaries with longest phrases first and alphabetical ties. Denial spans are removed before positive matching. Backtick and tilde fences with up to three leading spaces are excluded; inline code counts.

Python files are parsed using AST and never executed. Symlink files and directories are excluded. Fixtures, docs, and examples path components cannot supply evidence; tests paths and test filename conventions supply test evidence only. Invalid syntax supplies none. Each route must occur in one module. Imports and aliases are resolved, with local function, method, class, assignment, annotated assignment, and context-manager bindings suppressing shadowed names.

A promise without production evidence is HIGH, or MEDIUM when evidence exists only in tests. A denial contradicted by production evidence is HIGH. There is one finding per family. With no Python files, a promise is HIGH and a denial passes.

```text
documented-french-health-card-extraction-claim-false
documented-no-french-health-card-extraction-claim-false
```

The accepted typed route is a mindee Client construction plus an attribute parse call passing HealthCardV1 as any positional or keyword argument, as a Name or an Attribute. An import of mindee is required in that module. Qualified generic calls also count independently, as attributes on any base or imported names, including aliases. Bare unimported names and mere references do not count.

HealthCardV1 is a 4.x-only fingerprint (present in mindee 4.22.0); it was removed from the mindee 5.x v1 namespace (absent in 5.4.0). The tool detects the call in source, not whether it succeeds against a current API version or which SDK is installed. The product supplies given_names, surname, social_security (French NIR), and issuance_date only. It has no insurer name, member ID, group number, payer ID, copays, or prescription information (RxBIN, RxPCN, RxGrp, RxId); those belong to the US insurance-card domain.

## Differentiation

This family checks the French Carte Vitale fields, while adjacent families check their own document types or page grouping. OCR returns text and table extraction returns tables; neither establishes the four structured card fields. US insurance cards, French identity cards, and vehicle registration cards are separate domains. These sibling families do not establish this audit's evidence:

```text
invoice / receipt / financial-document / id-document / bank-check /
bank-statement / tax-form / pay-stub / health-insurance-card /
business-card / credit-card / contract / mortgage / resume /
bill-of-lading / delivery-note / carte-grise / energy-bill /
marriage-certificate / bank-account-details / nutrition-facts-label /
material-certificate / us-mail / invoice-splitter / multi-receipts-detection
```

## Limitations

Static patterns are not semantic judgement. Dead code counts; unsupported alias chains are missed. Exact wording and a finite denial list limit matching. Hardware chip reading, physical reader devices, archival image capture, document verification, a French insurer's differently structured card, and classification can produce false positives. Qualified reader or scan calls can also refer to hardware. Review findings in context.

The complete documented hazards and exclusions follow as quoted reference material. These describe the audited projects and the scanner's limits, not capabilities of this audit tool.

```text

- The phrases "carte vitale extraction" / "extract carte vitale"
  / "carte vitale parser" are deliberately FRENCHHEALTHCARDEXTRACTION
  phrases: in document-tool docs they name pulling structured
  fields out of a French Carte Vitale. But "carte vitale" can also
  name a card-reader hardware step (reading the chip on the
  physical card) rather than extracting fields from a card image:
  a doc that means chip reading, not image field extraction, is a
  false positive; the tool flags the claim, only the code decides.
- "french health card extraction" / "extract french health card"
  are deliberately phrases. But "french health card" can also name
  the US-style health insurance card of a French insurer, or a
  French health card as a document to verify rather than to
  extract fields from: a doc that means verification or a
  differently-structured card, not Carte Vitale field extraction,
  is a false positive; the tool flags the claim, only the code
  decides.
- "carte vitale reader" / "french health card reader" are
  deliberately phrases. But a "reader" can also name a physical
  smart-card reader device (hardware) rather than a field
  extractor: a doc that means hardware, not extraction, is a false
  positive; the tool flags the claim, only the code decides.
- "scan carte vitale" / "scan french health card" are deliberately
  phrases. But "scan" can also name scanning the physical card
  for archival (producing an image file) rather than extracting
  its fields: a doc that means image capture, not field
  extraction, is a false positive; the tool flags the claim, only
  the code decides.
- "carte vitale recognition" / "recognize carte vitale" are
  deliberately phrases. But "recognition" can also name detecting
  whether a document IS a Carte Vitale (classification, one
  label) rather than extracting its fields: a doc that means
  classification, not field extraction, is a false positive; the
  tool flags the claim, only the code decides.
- HealthCardV1 extracts four fields only (given_names, surname,
  social_security, issuance_date). It carries no insurer name, no
  member ID, no group number, no payer ID, no copays, and no
  prescription info (RxBIN / RxPCN / RxGrp / RxId) — those are US
  health insurance card fields, the R196 family's domain. A tool
  that extracts those does so through some other route; this
  family checks for the HealthCardV1 call, not for those fields.
- A generic `read_carte_vitale(` / `scan_carte_vitale(` /
  `carte_vitale_reader(` call can name a hardware chip reader
  rather than an image field extractor: the tool counts the call,
  the claim plus the code decide — and a subprocess call invoking
  an external CLI is NOT evidence by design, so a thin wrapper
  that only calls subprocess fails.
- Mindee `parse` with HealthCardV1 counts as evidence: the
  product exists in mindee 4.22.0 (wheel inspected 2026-11-15).
  The tool detects the call in source, not whether the call
  succeeds against a current API version.
- Mindee `parse` with HealthCardV1 IS a 4.x-only fingerprint:
  mindee 5.x removed the health card product from the v1
  namespace (5.4.0 wheel inspected 2026-11-15 — zero files
  matching "health" anywhere in the wheel).
- A bare generic `extract_health_card(` / `parse_health_card(`
  call is NOT detected: those are the R196 US-card family's
  generic names, and a bare "health card" call with no "carte
  vitale" or "french health card" qualifier cannot be told apart
  from a US health insurance card call. Only the qualified names
  count.
- Mindee `parse` with HealthcareCardV1 alone is NOT detected:
  extracting fields from a US health insurance card is not
  extracting a French Carte Vitale, and the US-card route is the
  R196 family's domain.
- Mindee `parse` with IdCardV1 / IdCardV2 alone is NOT detected:
  extracting fields from a French national identity card is not
  extracting a Carte Vitale, and the ID-card route is the
  id-document family's domain.
- Mindee `parse` with CarteGriseV1 alone is NOT detected:
  extracting vehicle registration fields is not extracting a
  Carte Vitale.
- Mindee `parse` with ReceiptV5 / InvoiceV4 / InvoiceSplitterV1 /
  MultiReceiptsDetectorV1 / FinancialDocumentV1 / PassportV1 /
  BankCheckV1 / BankAccountDetailsV1 / BankAccountDetailsV2 /
  PayslipV2 / PayslipV3 / NutritionFactsLabelV1 / BusinessCardV1 /
  CustomV1 / GeneratedV1 / BillOfLadingV1 / ResumeV1 /
  DeliveryNoteV1 / DriverLicenseV1 / InternationalIdV2 /
  EnergyBillV1 / MaterialCertificateV1 / BarcodeReaderV1 /
  CropperV1 / UsMailV2 / UsMailV3 is NOT detected: those are other
  document types or other operations.
- Azure `begin_analyze_document` with ANY model id is NOT
  detected: Azure Document Intelligence has no Carte Vitale model
  (the Learn v4.0 GA prebuilt-model pages list no such model,
  verified 2026-11-15). prebuilt-healthInsuranceCard.us is the US
  card, the R196 family's domain.
- Veryfi has NO Carte Vitale method: the 5.1.0 wheel contains no
  file or method mentioning "carte vitale" or "health card"
  (verified 2026-11-15). Veryfi `process_document` /
  `process_any_document` / `split_and_process_pdf` and all other
  veryfi calls are NOT detected.
- Google Document AI `process_document` / `batch_process_documents`
  with ANY processor is NOT detected: Document AI has no Carte
  Vitale processor (the processors list page contains no such
  processor, verified 2026-11-15).
- Eden AI universal-ai calls with ANY model id are NOT detected:
  the model id is a plain string inside an arbitrary request
  payload, not a typed SDK call, so there is no fixed static
  fingerprint for the call itself.
- LlamaParse calls are NOT detected: its parsing API is
  generative with no fixed static fingerprint naming Carte Vitale
  extraction.
- Nanonets / Docsumo / ABBYY Vantage / Rossum / Klippa / Parseur /
  Extend calls are NOT detected: opaque model / skill / queue /
  template / workflow IDs, or a generic upload endpoint with the
  document type configured outside the call — no fixed fingerprint.
- Textract `analyze_document` / `analyze_expense` / `analyze_id` /
  `start_document_analysis` / `get_expense_analysis` are NOT
  detected: generic document, expense, and identity analysis of
  one document are not Carte Vitale extraction, and Textract has
  no Carte Vitale extraction operation.
- Generic OCR / table / regex-OCR / CSV calls (pytesseract
  image_to_string, pdfplumber / fitz extract_text, camelot /
  tabula table calls, pandas read_csv / read_excel) are NOT
  detected: plain text or tables are not Carte Vitale fields.
- Document classifier calls (classify_document, is_health_card, or
  any health-card-classification call) are NOT detected: returning
  one label is not extracting the card's fields. Say so in the
  README.
- A hand-rolled extraction from OCR text (`re.search` /
  `re.findall` on extracted text plus manual field assembly,
  no listed call) is NOT detected: the tool requires a listed call.
- The mindee CLI, the veryfi CLI, and any other external
  Carte Vitale extractor tool invoked through subprocess are NOT
  detected: subprocess calls invoking an external CLI are NOT
  evidence by design.
- Azure Document Intelligence, Mindee, and Veryfi are cloud APIs:
  the tool detects the client call in source, not whether
  credentials are configured or the call succeeds. Say so in the
  README.
- "extract health insurance card" / "health insurance card
  extraction" / "extract us health insurance card" claims are NOT
  in the phrase lists: extracting fields from a US health
  insurance card is a different operation from extracting a French
  Carte Vitale.
- "extract french id card" / "french id card extraction" claims
  are NOT in the phrase lists: extracting a French national
  identity card is a different operation from extracting a Carte
  Vitale.
- "extract invoices" / "invoice extraction", "extract receipts" /
  "receipt extraction", "extract financial documents" /
  "financial document extraction", "extract bank statements" /
  "statement extraction", "extract tax forms" / "extract w2 forms",
  "extract pay stubs" / "payslip extraction", "extract us mail" /
  "us mail extraction", "extract contracts" / "contract extraction",
  "extract resumes" / "resume extraction", "extract bills of
  lading" / "bill of lading extraction", "extract delivery notes" /
  "delivery note extraction", "extract carte grises" / "carte
  grise extraction", "extract energy bills" / "energy bill
  extraction", "extract marriage certificates" / "marriage
  certificate extraction", "extract bank account details" / "bank
  details extraction", "extract nutrition facts labels" /
  "nutrition facts label extraction", "extract material
  certificates" / "material certificate extraction", and "extract
  bank checks" / "check extraction" claims are NOT in the phrase
  lists: this family covers French health card extraction only.
- As with every family: static pattern matching, not semantic
  judgement; dead code counts; alias chains the tracer cannot follow
  are missed; exact phrases only, not semantics; denial handling
  depends on the denial phrase list; each route must sit in a single
  module.

```

## Vocabulary

The exact accepted vocabulary is listed for review.

```text
carte vitale extraction
extract carte vitale
extracts carte vitale
extracting carte vitale
extract carte vitales
extracts carte vitales
extracting carte vitales
carte vitale parsing
carte vitale parser
parse carte vitale
parses carte vitale
parse carte vitales
parses carte vitales
carte vitale data extraction
extract carte vitale data
carte vitale field extraction
carte vitale document extraction
extract carte vitale documents
carte vitale reader
carte vitale scanning
scan carte vitale
scans carte vitale
scanning carte vitale
carte vitale recognition
recognize carte vitale
french health card extraction
extract french health cards
extracts french health cards
extracting french health cards
extract french health card
extracts french health card
extracting french health card
french health card parsing
french health card parser
parse french health cards
parses french health cards
parse french health card
parses french health card
french health card data extraction
extract french health card data
french health card field extraction
french health card document extraction
extract french health card documents
french health card reader
french health card scanning
scan french health card
scans french health card
scanning french health card
french healthcard extraction
extract french healthcard
no carte vitale extraction
does not extract carte vitale
does not extract carte vitales
does not support carte vitale extraction
without carte vitale extraction
no carte vitale parser
does not parse carte vitale
does not parse carte vitales
no french health card extraction
does not extract french health cards
does not extract french health card
does not support french health card extraction
without french health card extraction
no french health card parser
does not parse french health cards
does not parse french health card
carte vitale extraction not supported
french health card extraction not supported
no french healthcard extraction
does not extract french healthcard
does not scan carte vitale
does not scan french health card
no carte vitale reader
no french health card reader
extract_carte_vitale
extract_carte_vitales
parse_carte_vitale
parse_carte_vitales
extract_french_health_card
extract_french_health_cards
parse_french_health_card
parse_french_health_cards
extract_french_healthcard
parse_french_healthcard
carte_vitale_extraction
french_health_card_extraction
extract_carte_vitale_data
parse_carte_vitale_data
extract_french_health_card_data
parse_french_health_card_data
read_carte_vitale
read_french_health_card
scan_carte_vitale
scan_french_health_card
carte_vitale_reader
french_health_card_reader
get_carte_vitale_data
get_french_health_card_data
```

## Development

```sh
python3 -m unittest discover
python3 -m build
```

MIT licensed.
