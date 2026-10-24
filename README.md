# Vyapar Mitra (व्यापार मित्र — डिजिटल बहीखाता)

A reliable, small-business expense management and receipt auditing web application built for an Indian stationery shop owner.

The app pairs an accessible, Claude-built React + TypeScript frontend (supporting full English and Hindi) with a Python FastAPI + SQLite backend powered by Google Gemini for structured receipt extraction.

---

## Core Architectural Principle

> **AI proposes; the owner verifies; application code calculates.**  
> Gemini is an extraction and natural-language assistance tool. Gemini is **never** authoritative for financial data, never performs monetary arithmetic, and never executes arbitrary database queries. All calculations are performed in verified application code using integer paise (`1 Rupee = 100 paise`).

---

## Features

- **Receipt Ingestion**: Supports JPG, PNG, and short receipt-style PDFs with SHA-256 deduplication and MIME validation.
- **Structured Gemini Extraction**: Extracts vendor, date, currency, line items, and receipt total into typed Pydantic models. Flags blurry or ambiguous fields without guessing.
- **Side-by-Side Verification**: Original receipt image or PDF displayed directly beside an editable review form.
- **Owner-Confirmed Ledger**: Unconfirmed receipts never impact financial metrics. Only explicit owner confirmation enters receipts into the trusted expense ledger.
- **Duplicate Detection**: Flags exact file duplicates (SHA-256) and similar purchases (vendor + date + total matching confirmed receipts). The owner explicitly chooses to discard or keep as separate purchases.
- **Live Spending Dashboard**: Real-time spending summaries, category spend breakdown, and top vendor charts calculated strictly from confirmed records.
- **Safe Expense Q&A**: Answers 5 targeted financial questions with supporting receipt links using fixed safe queries.
- **Formula-Safe CSV Export**: Generates ledger exports with formula-injection defenses (`=`, `+`, `-`, `@` escaped).
- **Full Bilingual Support (EN / HI)**: Complete English and natural Devanagari Hindi interface with instant language switching and persistent preferences.
- **Owner Account & Settings**: One-time owner signup, password login, secure server-side sessions, editable business profile, language/currency preferences, password changes, and ledger exports.

---

## Project Structure

```text
.
├── frontend_integration_audit.md   # Complete frontend audit (Step 0)
├── implementation_plan.md          # Full architectural plan & 12-step build order
├── task_list.md                    # Step-by-step progress tracking
├── README.md                       # Project documentation
├── .env.example                    # Global environment configuration template
├── package.json                    # Frontend dependencies & scripts
├── vite.config.ts                  # Vite build config with Tailwind v4 & proxy
├── tsconfig.json                   # TypeScript config
├── src/                            # Claude-built React frontend (Source of Truth)
│   ├── App.tsx                     # Main application layout, components & routes
│   ├── api.ts                      # Network client layer
│   ├── account.tsx                 # Signup/login and account settings
│   ├── i18n.tsx                    # Bilingual provider & currency/date formatters
│   ├── index.css                   # Tailwind v4 import & typography
│   ├── main.tsx                    # Entrypoint
│   ├── mock.ts                     # Stand-in mock backend
│   ├── types.ts                    # TypeScript domain interfaces
│   └── locales/
│       ├── en.json                 # English copy dictionary
│       └── hi.json                 # Hindi copy dictionary
└── backend/                        # Python FastAPI Backend (Steps 1-11)
    ├── .env.example                # Backend environment template
    ├── requirements.txt            # Python dependencies
    ├── app/
    │   ├── main.py                 # FastAPI application
    │   ├── config.py               # Settings & environment validation
    │   ├── database.py             # SQLite WAL database & schema migrations
    │   ├── models.py               # Pydantic schemas
    │   ├── services/               # Extraction, duplicate, dashboard & question logic
    │   └── routers/                # REST API route handlers
    └── data/
        ├── shopledger.db           # SQLite database
        └── uploads/                # Stored receipt images & PDFs
```

---

## Quick Start & Running Locally

### 1. Environment Setup

Copy `.env.example` to create your local `.env` file:
```bash
cp .env.example .env
```

To enable live Gemini extraction in the backend, obtain an API key from Google AI Studio and configure:
```env
GEMINI_API_KEY=your_gemini_api_key_here
```

### 2. Frontend Development Server

Install frontend dependencies and start the Vite dev server:
```bash
npm install
npm run dev
```
The frontend will be available at [http://localhost:5173](http://localhost:5173).
The Vite development server proxies `/api` to `http://localhost:8000` by default. For a separate backend URL, set `VITE_API_BASE_URL` in `.env`. The legacy data mock can be selected with `VITE_API_BASE_URL=mock`; authentication and settings require the backend.

### 3. Backend Server (FastAPI)

Set up a Python virtual environment and run the backend:
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r backend/requirements.txt
python backend/run_server.py
```
The backend API server runs at [http://localhost:8000](http://localhost:8000). Interactive OpenAPI documentation is available at [http://localhost:8000/docs](http://localhost:8000/docs).

### Streamlit Community Cloud (FastAPI backend)

To host the FastAPI API on Streamlit Community Cloud, set **Main file path** to `main.py` in the repository root. This root-level ASGI entry point exposes the backend app; it does not host the React/Vite frontend, which must still be deployed separately. Configure `GEMINI_API_KEY` in Streamlit's app secrets/environment settings if receipt extraction is needed.

### First sign-in

On first launch, create the shop's single owner account with your name, email, business details, preferred language, display currency, and a password. Passwords must be at least 12 characters and include uppercase and lowercase letters, a number, and a symbol; signup also asks you to confirm the password. The backend stores only a salted PBKDF2 password hash and issues an HTTP-only session cookie. Email/OTP verification is not enabled because this project has no email delivery service configured.

After setup, use the email and password to sign in. The **Settings** page lets you edit your profile, language and display currency, change your password, export CSV/PDF reports, or sign out. Changing your password revokes other sessions. Currency selection changes display formatting only; it does not perform exchange-rate conversion.

---

## API Specifications

All JSON endpoints follow a consistent envelope structure:
- **Success**: `{"success": true, "data": { ... }, "error": null}`
- **Error**: `{"success": false, "data": null, "error": {"code": "ERROR_CODE", "message": "User-friendly description"}}`

| Endpoint | Method | Purpose |
| :--- | :---: | :--- |
| `/api/receipts/upload` | `POST` | Upload receipt image/PDF (returns `{ "id": string }`) |
| `/api/auth/status` | `GET` | Check whether owner setup is complete and the browser is signed in |
| `/api/auth/setup` | `POST` | Create the one-time owner account |
| `/api/auth/login` | `POST` | Start an owner session |
| `/api/auth/logout` | `POST` | End the current owner session |
| `/api/auth/profile` | `PATCH` | Update owner, business, and display preferences |
| `/api/auth/password` | `POST` | Change password and rotate active sessions |
| `/api/receipts/{id}/extract` | `POST` | Trigger structured Gemini extraction on uploaded receipt |
| `/api/receipts/{id}` | `GET` | Retrieve receipt details, extracted items, and flags |
| `/api/receipts/{id}/file` | `GET` | Stream original receipt image or PDF |
| `/api/receipts/{id}` | `PATCH` | Update receipt fields (vendor, date, total, items, category) |
| `/api/receipts/{id}/confirm` | `POST` | Validate and confirm receipt into immutable expense ledger |
| `/api/receipts/{id}/discard-duplicate` | `POST` | Discard flagged duplicate upload |
| `/api/receipts/{id}/keep-separate` | `POST` | Retain flagged duplicate as a distinct purchase |
| `/api/receipts` | `GET` | Search and filter confirmed receipts (`q`, `from`, `to`, `category`, `vendor`) |
| `/api/dashboard/summary` | `GET` | Retrieve total spend, confirmed count, pending review count, and top vendors |
| `/api/dashboard/categories` | `GET` | Retrieve spending aggregated by category |
| `/api/questions/ask` | `POST` | Ask a supported question (`{ "question": string, "lang": "en" \| "hi" }`) |
| `/api/export/csv` | `GET` | Download confirmed expense ledger as CSV |
| `/api/export/pdf` | `GET` | Download the payment summary as PDF |

Receipt, dashboard, and export endpoints require an authenticated owner session. The health endpoint and owner setup/login endpoints remain public.

---

## Testing & Verification

Run the full automated pytest suite covering database transactions, schema migrations, file uploads, Gemini structured parsing, validation, duplicate matching, dashboard aggregations, question answering, formula-safe CSV export, and synthetic test fixtures:

```bash
# Run all 40 automated tests
PYTHONPATH=. backend/.venv/bin/pytest backend/tests
```

### Reset / Seed Demo Data
To reset the development database to realistic stationery shop expenses at any time:
```bash
backend/.venv/bin/python3 backend/scripts/seed_demo_data.py
```

### Synthetic Test Dataset (20 Real-World Fixtures)
Located in `backend/data/test_fixtures/` with complete `ground_truth.json`:
- **8 Clear Invoices**: `fixture_01_clear.png` to `fixture_08_clear.png` (Classmate notebooks, Reynolds pens, JK Copier A4 paper, Kangaro staplers, etc.)
- **4 Wholesale PDFs**: `fixture_09_pdf.pdf` to `fixture_12_pdf.pdf` (Navneet Publications, Kokuyo Camlin, Pidilite, Freight Carriers)
- **3 Blurry / Ambiguous Invoices**: `fixture_13_blurry.png` (faint thermal print), `fixture_14_blurry.png` (ambiguous date), `fixture_15_blurry.png` (faint vendor banner)
- **3 Duplicate Scenarios**: `fixture_16_exact_dup.png` (exact SHA-256 duplicate), `fixture_17_fuzzy_dup1.png` & `fixture_18_fuzzy_dup2.png` (same vendor, date, and amount)
- **2 Incomplete Invoices**: `fixture_19_torn_total.png` (torn total edge), `fixture_20_missing_vendor.png` (cash memo without printed header)

---

## Hackathon Demo Script (3-Minute Walkthrough)

1. **Dashboard Overview ([http://localhost:5173](http://localhost:5173))**:
   - Show verified financial metrics calculated strictly on the backend: Total spent (`₹19,830.00`), Confirmed receipts (`4`), and Action required (`2`).
   - Click on "Sharma Wholesale Traders" in top vendors to jump directly to the filtered ledger.
2. **Bilingual Switcher**:
   - Click the language toggle button in the header (`हिन्दी` / `English`). Notice immediate translation of all cards, metrics, and labels with zero page reload. Reload the page to demonstrate `localStorage` persistence.
3. **Upload & Gemini Extraction**:
   - Click **Add Receipt** and upload `backend/data/test_fixtures/fixture_02_clear.png` (JK Paper Mart).
   - Watch the structured extraction parse the vendor, date, items, line prices, and total.
   - Edit any line item or change category, then click **Add Receipt** to verify and confirm.
4. **Duplicate Protection**:
   - Re-upload the same file or `fixture_16_exact_dup.png`.
   - The app detects the duplicate and displays a side-by-side comparison with the earlier receipt.
   - Choose **"Discard this upload as a duplicate"** or **"Keep as a separate purchase"**.
5. **Ledger & CSV Export**:
   - Navigate to **My Expenses** (`#/ledger`).
   - Filter by date range or category (`Inventory/Stock`, `Packaging`, `Utilities`).
   - Click **Download expenses (CSV)**. Open the downloaded file to verify formula injection protection (cells starting with `=`, `+`, `-`, `@` are safely neutralized).
6. **Natural Language Q&A**:
   - Navigate to **Ask a question** (`#/ask`).
   - Tap example questions: *"How much have I spent in total?"* or type *"मैंने कुल कितना खर्च किया?"*.
   - View verified figures calculated in Python and phrased naturally with clickable supporting receipt evidence cards.

---

## Build Order & Project Governance (100% Complete)

Development strictly adhered to the incremental 12-step approval workflow. All steps are fully completed and tested:

- [x] **Step 0 — Frontend Audit & Project Plan**: Audited supplied Claude frontend; mapped state machines, routes, envelopes, and contracts.
- [x] **Step 1 — Backend Foundation**: FastAPI app, SQLite database with WAL mode and foreign keys, standard error envelopes, Vite dev proxy.
- [x] **Step 2 — Upload Service & Storage**: Multipart streaming, 10MB limit, SHA-256 hash generation, binary stream retrieval.
- [x] **Step 3 — Gemini Structured Extraction**: Structured JSON prompt with `google-genai` SDK, Pydantic validation, raw extraction persistence, paise arithmetic.
- [x] **Step 4 — Review & Confirmation**: Draft saves (`PATCH /api/receipts/{id}`), strict financial validations, explicit confirmation to immutable ledger (`POST /api/receipts/{id}/confirm`).
- [x] **Step 5 — Ledger & Search Filtering**: Filtered queries by vendor, date range, search terms, and category (`GET /api/receipts`).
- [x] **Step 6 — Duplicate Detection & Schema Integration**: Exact SHA-256 file matching, fuzzy financial matching, side-by-side comparison, discard/keep actions.
- [x] **Step 7 — Dashboard Aggregations**: Backend-calculated confirmed metrics (`totalSpent`, `confirmedCount`, `reviewCount`, `topVendors`), category breakdown, evidence links.
- [x] **Step 8 — Safe Question Answering**: Fixed safe query dispatcher for 5 supported intents, application calculations, Gemini natural language phrasing, safe fallbacks.
- [x] **Step 9 — Formula-Safe CSV Export**: Server-side CSV streaming with formula injection protection (escaped `=`, `+`, `-`, `@`), RFC 4180 compliance.
- [x] **Step 10 — Bilingual Interface, Accessibility & Polish**: 100% key parity (145 keys in `en.json` and `hi.json`), persistent language toggle, 48px mobile touch targets, double-submit protection.
- [x] **Step 11 — Demo Readiness & Test Dataset**: 20 synthetic fixtures with `ground_truth.json`, seed data script, full end-to-end journey verification, 40/40 tests passing.
