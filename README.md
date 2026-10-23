# ShopLedger (दुकान का खाता)

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
├── account.tsx                 # Signup/login and account settings
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

## Build Order & Project Governance

Development strictly follows an incremental 12-step approval workflow. Each step requires explicit user sign-off before proceeding:

0. **Frontend Audit and Project Plan** *(Completed)*
1. **Backend Foundation** *(FastAPI, SQLite schema, response envelope, dev proxy)*
2. **Upload Service** *(File validation, SHA-256 hash, storage, upload UI connection)*
3. **Gemini Extraction** *(Structured JSON prompt, Pydantic validation, error handling)*
4. **Review & Confirmation** *(Editable form APIs, validation, explicit confirmation)*
5. **Ledger** *(Confirmed receipts list, search/filtering, detail view)*
6. **Duplicate Detection** *(SHA-256 exact match, similar purchase match, comparison UI)*
7. **Dashboard** *(Backend-calculated metrics, category sums, clickable evidence)*
8. **Question Answering** *(5 supported intents, safe dispatcher, natural phrasing)*
9. **CSV Export** *(Backend CSV generation, formula-injection protection, download)*
10. **Hindi UI & Accessibility** *(Bilingual verification, high-contrast, tap targets)*
11. **Demo Readiness** *(20 synthetic receipts, full journey verification, final walkthrough)*
