# Fakturama Image-to-Cash Automation

A take-home exercise: take a single order image and drive **Fakturama** (a Java/SWT
desktop invoicing application) to a saved, verified **Order** and a linked **Invoice**.
The system extracts the source data, resolves or creates the Debtor and Product master
records, applies the payment status, and verifies each saved record.

The UI is driven with **Microsoft UI Automation (UIA)** — controls are found by name,
label-relative geometry, or clipboard readback, never by hardcoded coordinates. Data
is extracted with **RapidOCR** and optionally an **LLM** vision pass, then validated by
deterministic code before any UI interaction.

## Status

| Part | State |
|---|---|
| 1. Design document | [`docs/design.md`](docs/design.md) |
| 2. Implementation | extraction + validation complete; spine flow (existing debtor/product) verified |

Implemented:

- **Extraction** — RapidOCR produces text, confidence and boxes; a deterministic
  label/table parser turns them into a typed order; an optional LLM (vision) stage can
  replace the parser when an endpoint is configured.
- **Validation** — schema and format checks, line and document totals recomputed from
  the primitives, and every SKU/company/reference cross-checked against the raw OCR
  text. Any failure raises `ManualReviewRequired` and stops the run.
- **CLI + tests** — `python -m src.extract`, `python -m tests.test_extract`.
- **Spine flow** (verified) — New Order → existing debtor → existing product →
  totals check → save → linked Invoice → PAID + date + value → totals check.
  Run it with `python -m src.flows.spine samples\spine_order.json`.

In progress:

- Creation branches for a missing debtor, payment method, VAT rate and product
  (needed to process the sample image end to end).
- The sample-image run (the spine currently uses `samples/spine_order.json`).

## Repository layout

```
.
├── README.md
├── requirements.txt
├── .env.example
├── docs/
│   └── design.md            Part 1 design document
├── samples/
│   ├── order_sample.png     supplied order image
│   └── expected.json        ground-truth fixture
├── src/
│   ├── config.py            .env loader (no extra dependency)
│   ├── errors.py            ManualReviewRequired
│   └── extract/
│       ├── schema.py        typed model + price helpers
│       ├── ocr.py           RapidOCR wrapper (text, score, boxes)
│       ├── parser.py        deterministic label/table parser (offline)
│       ├── llm.py           optional Anthropic vision stage
│       ├── validate.py      formats + totals + OCR cross-check
│       ├── extract.py       image -> validated order orchestrator
│       └── __main__.py      CLI
└── tests/
    └── test_extract.py
```

## Requirements

- Windows (the UI automation is Windows/UIA only).
- Fakturama installed and running for the UI flow.
- Python 3.12+ (developed on 3.14).
- RapidOCR ships its own ONNX models; no separate Tesseract install is needed.

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env   # optional: fill in LLM settings
```

## Run the extraction

```powershell
# OCR + deterministic parser (works offline)
python -m src.extract samples\order_sample.png

# Use the LLM vision stage (requires credentials in .env or the environment)
python -m src.extract samples\order_sample.png --llm
```

Run the tests:

```powershell
python -m tests.test_extract
```

## Run the spine (existing master data)

Start Fakturama and make sure the **MAMarine** debtor and **TST-A-01** product
exist, then:

```powershell
python -m src.flows.spine samples\spine_order.json
```

It opens an Order, resolves the existing debtor and product, checks the totals,
saves the Order, creates the linked Invoice, applies PAID + date + value, and
verifies the invoice totals. If the debtor or product is missing it stops with
`ManualReviewRequired` (creation branches are not implemented yet).

## Configuration

`.env` (git-ignored). Values in `.env` take precedence over the process
environment (blank values are ignored):

| Variable | Purpose |
|---|---|
| `ANTHROPIC_API_KEY` / `ANTHROPIC_AUTH_TOKEN` | LLM credentials (optional) |
| `ANTHROPIC_BASE_URL` | Messages API base URL |
| `ANTHROPIC_MODEL` | vision-capable model name |
| `FAKTURAMA_USE_LLM` | `1` to enable the LLM stage by default |

The pipeline runs fully offline with OCR when no LLM is configured or the endpoint is
unreachable; the validator still applies to both paths.

## How it works

1. **OCR** (`src/extract/ocr.py`) returns each text line with confidence and its box.
2. **Parse** (`parser.py`) anchors field values to labels (`ORDER DATE`, `PAYMENT
   METHOD`, ...) and slices item rows by horizontal position. The LLM stage (`llm.py`)
   is an alternative for the same schema.
3. **Validate** (`validate.py`) recomputes `qty × unit net × (1 − discount)` per line,
   then net/VAT/gross, and refuses to continue on any mismatch or on a value that is
   absent from the raw OCR text.
4. **Drive the UI** (planned) — one state machine with a verification gate after every
   step and a single `ManualReviewRequired` stop condition.

## Notes and known quirks

- **Currency mismatch.** The sample image is in EUR; this Fakturama installation shows
  GBP. No step in the spec sets currency, so it is left as-is.
- **Clipboard.** Custom-drawn tables and the Items grid are read by selecting a row and
  pressing Ctrl+C. The clipboard is read through the Windows API (the tkinter clipboard
  crashed the process), and the automation overwrites the user's clipboard.
- **Foreground desktop.** The UI flow needs a real, unlocked desktop session.
- **Consultant.** Selecting a debtor auto-fills `Consultant`; the flow leaves it
  unchanged.
- **Discounts** display as negative percentages in the grid; money appears as `£`,
  `GBP` or a plain float depending on where it is read — one parser normalises them.
- **ZIP with country prefix.** The invoice address box can show `EG-316924`; ZIP and
  city are compared separately, never as whole lines.
- **Customer ID.** The image shows `CUST-1007`, but the spec says to keep Fakturama's
  proposed Customer ID, so it is extracted but not typed.
- **Different billing/delivery addresses.** The spec only describes the identical case;
  the sample needs a second address with the Delivery role.

## What is skipped

- The creation branches (new debtor, payment method, VAT rate, product) are not
  wired up yet, so the sample image cannot run end to end.
- Documents-list readback is not automated yet; the saved Order/Invoice tabs are
  read back and verified instead.
- Annotated screenshots / a recording will be added.

## If I had 3 more hours

Resume and clean-up logic for leftover unsaved records; a test harness with recorded
UIA trees and more sample images (rotated, photographed, multi-page); self-healing
locators using OCR-derived column positions; stronger extraction with a second model
pass and confidence thresholds; support for order-level discounts, shipping and
multiple payment methods; locale-independent date and number entry; and a recorded run
with a structured JSON report.
