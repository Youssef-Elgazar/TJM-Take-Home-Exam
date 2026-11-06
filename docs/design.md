# Fakturama Image-to-Cash: Design Document

## 1. Goal and scope

The system takes one order image and produces, inside Fakturama (a Java/SWT desktop invoicing application), a saved and verified Order with a linked Invoice. It must work without hardcoded coordinates or a fixed UI layout. Where the data is ambiguous or conflicts with what already exists in Fakturama, it must stop for manual review instead of guessing.

The design has three layers: extraction (image to validated JSON), a UI driver (find, click, type, wait, read back), and a flow layer that runs the business steps in order and verifies each one against the extracted data.

## 2. Control discovery and grounding

I inspected the real application with UI Automation (UIA) dumps before designing this. Fakturama is built on Eclipse SWT. Native controls (edits, combo boxes, labels, checkboxes, toolbar buttons) are visible in UIA with useful names. Anything custom-drawn, such as the result tables in the selector dialogs and the Items grid, appears as a single empty pane. The grounding strategy therefore has three tiers, tried in this order.

**Tier 1: UIA by name and control type.** Most of the application is reachable this way: the toolbar buttons (for example "Create: New Order"), the left navigation entries, field edits such as Cust.Ref., Street, E-Mail, Alias name, Discount, and the combo boxes Payment and Net or Gross. Dialogs are found by title, such as "Select the address" and "Select a product". I never use automation IDs, because they change on every launch.

**Tier 2: UIA geometry relative to a label.** Some controls are unnamed: the Order date field, the Net/Gross price-mode combo, the two icons beside Addresses, the four icons beside Items, the first name and last name edits, the ZIP and City edits, and the payment-method combo on the Invoice. These are found by locating the neighbouring label and choosing the control in the expected position relative to it. A wrong guess is caught by asserting what opens next, for example the title of the dialog that appears after clicking an icon.

**Tier 3: clipboard readback and OCR for custom-drawn tables.** For the selector dialogs and the Items grid, I select a row, copy it with Ctrl+C, and parse the tab-separated text. This gave reliable, exact field values: item number, price and VAT for products; company, ZIP and city for debtors; and quantity, unit price, discount and line price for order lines. OCR is a fallback for locating grid columns from the header row, not the primary reader. I read the clipboard through the Windows API, because the Python tkinter clipboard crashed the process.

Two observations shaped this choice. First, layout is not stable: lists appear sometimes as docked panels and sometimes maximized, and the left navigation moved by about 23 pixels between two sessions. Fixed coordinates would have broken. Second, waiting must be condition-based (dialog exists, filter settled, tab title changed), never a fixed sleep.

## 3. Application behaviours the design accounts for

These were found empirically and drive specific decisions.

- **Segmented date field.** The Order, Invoice and payment dates are segmented controls. Setting the text snaps back to today. What works is clicking each segment (found by pressing UP/DOWN and seeing which part changes) and typing numbers: year, then month as a number, then day. The value is read back and compared.
- **Product selector.** Search is a substring match and also matches the product name, so searching for a SKU can return near-matches. When exactly one row remains, the dialog selects it and closes itself. The flow therefore sets the whole search text at once, then checks whether the dialog is still open, and compares each returned Item No. exactly. Case-only differences count as conflicts.
- **Address selector.** It filters live, and clearing the search box does not restore the full list, so the dialog is opened fresh for every lookup.
- **Dropdown caching.** A payment method created while the debtor editor is open does not appear in that editor's Payment dropdown. The flow therefore creates the payment method (and VAT rate, if needed) before opening the New Contact editor.
- **Additional addresses.** A second address is added with a plus button and appears as a second tab whose fields have the same names as the first. Fields are found inside the selected tab's bounds, never by name alone.
- **Discount and money formats.** A discount of 10 displays as a negative percentage in the grid, and money appears as £, "GBP" or a plain float depending on where it is read. One parsing function normalises these and compares numbers only.
- **Net mode.** A product stored with a gross price of 119.00 shows a unit price of 100.00 in Net mode, so the spec's gross formula and the on-screen net price agree.

## 4. Image extraction

Extraction is two-stage, then validated by code.

1. **OCR pass** (RapidOCR) produces text, confidence and bounding boxes. This is the literal-character source of truth.
2. **LLM pass** sends the image, and the OCR text, to Anthropic's Messages API using the vision-capable model `claude-sonnet-4-5` (configurable through `ANTHROPIC_MODEL`) and asks for JSON that follows a strict schema: order date, external reference, debtor (company, contact, alias, billing and delivery addresses), payment method, status and date, and the items with SKU, description, quantity, unit net price, VAT percentage, discount and line total. The model is better at layout; OCR is better at exact characters, so each checks the other. When no LLM endpoint is configured, a deterministic label/table parser produces the same schema from the OCR boxes, so the pipeline still runs offline.
3. **Deterministic validation** runs before any UI work: schema and type checks, date and email formats, and a SKU pattern; line totals recomputed as quantity x unit net x (1 - discount/100), then net, VAT and gross compared with the source totals; and every extracted SKU, company name and reference must also appear in the raw OCR text, which catches model invention. The contact name is split into first and last name here. One retry feeds the error back to the model; after that the run stops for manual review.

Matching against Fakturama is always exact. No fuzzy matching is used for SKUs, company names or payment methods.

## 5. Flow, verification and stop conditions

The flow is a state machine with a verification gate after every step. The same pattern repeats for debtor, payment method, VAT rate and product: try the existing selector, create only if there is no exact match, return to the same open Order, select the new record and verify that it appeared. One generic resolve-or-create routine is reused, with a small plug-in per entity.

Order of operations: open the New Order first and keep it open; set the date, Cust.Ref. and Net mode; resolve the debtor; resolve each product in source order and set quantity and discount; check totals against the source; save once and confirm one Order row in Documents; then create the Invoice from the Order's own follow-up area (not the top toolbar, so the Order link is kept); confirm the copied fields; set the payment method, and if the source says paid, tick paid, set the payment date and enter the full total as the value; save once and verify.

A single exception, ManualReviewRequired, stops the run. Triggers: several or conflicting debtor matches, conflicting product, VAT or payment-method definitions, a new product that does not appear after saving, an auto-selected line whose item number differs from the SKU, an unavailable invoice payment method, and any totals mismatch. Each run keeps a log and a screenshot per step.

## 6. Tradeoffs and risks

- **UIA vs OCR vs LLM for driving the UI.** I use UIA first because it is exact and cheap, and keep vision-based grounding only as a fallback for custom-drawn areas. An LLM driving the UI would be more flexible but slower, non-deterministic, and harder to verify.
- **Clipboard dependency.** Reading tables through Ctrl+C overwrites the user's clipboard and needs a real foreground desktop session. Copying from an empty grid row triggers a Fakturama internal error, so copies are made only from rows that must exist.
- **Idempotency and partial state.** A crash can leave an unsaved Order or Debtor. A re-run must look for leftover state and check selectors before creating, to avoid duplicates.
- **Locale.** The installation uses UK date and currency formats, while the sample order is in EUR. No step in the spec sets currency, so this is documented rather than changed.
- **Layout assumptions.** Tier 2 geometry depends on the label positions of this version of Fakturama. A different version or theme may need small adjustments, which the title assertions are designed to catch.

## 7. Gaps in the specification that the sample exposes

The sample order has different billing and delivery addresses, whereas the spec describes only the identical case, so a second address with the Delivery role is needed. The image shows a customer ID, but the spec says to keep Fakturama's proposed one. The image states EUR while the application shows GBP. The unit "pcs" is not used by any step. Each is recorded in the README rather than silently resolved.

## 8. If I had three more hours

- **Invoice verification layer.** After saving, reopen the Invoice and compare every persisted field (payment method, paid state, payment date, value, line items, totals) against the extracted order and the linked Order, with a structured pass/fail report. The current run verifies the totals and paid state but not every persisted field.
- **More UI interactions.** Cover the remaining document types (Delivery, Invoice Correction, Dunning), more selector edge cases (multiple exact matches, case-only conflicts), and other layouts, themes and DPI settings, so the flow is not tied to one window size or perspective.
- **Faster product grid.** Explore cheaper ways to ground the custom-drawn grid and cut the idle time spent waiting on the vision call: cache the layout per grid geometry, use OCR/geometry first and call the vision model only when the layout changes, and run extraction in parallel with UI setup. Target: a full sample under 200 s (currently 239.6 s).
- **Idempotency and resume.** Detect leftover unsaved Orders or Debtors and existing master data, then resume or clean up instead of duplicating it.
- **Resilience.** Retry transient UIA failures, dismiss Fakturama's "Internal Error" and "Save Parts" dialogs automatically, and recover from an empty-selector copy without hanging.
- **Structured run report.** Per-stage timings (extraction, vision grid, each UI step), screenshots on failure, and a JSON summary, so the 200 s target is measurable and regressions are obvious.
- **Locale independence.** Parse and enter dates, numbers and currency independently of the installation's UK format and the image's EUR currency.

## 9. Configuration and running

The LLM stage uses Anthropic's Messages API with **`claude-sonnet-4-5`** (override with `ANTHROPIC_MODEL`). Credentials go in `.env` (`ANTHROPIC_API_KEY` or `ANTHROPIC_AUTH_TOKEN`, optional `ANTHROPIC_BASE_URL`). Set `FAKTURAMA_USE_LLM=1` to enable the vision stage; otherwise the pipeline runs offline with OCR and the deterministic parser.

Setup and commands (from the repository root, in a virtual environment):

```powershell
pip install -r requirements.txt
Copy-Item .env.example .env      # fill in the Anthropic values
python -m src.extract samples\order_sample.png        # OCR path
python -m src.extract samples\order_sample.png --llm  # vision path
python -m tests.test_extract                          # offline tests
```

The spine run needs Fakturama open with the dummy debtor `MAMarine` and product `TST-A-01` already present:

```powershell
python -m src.flows.spine samples\spine_order.json
```
