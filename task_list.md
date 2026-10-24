# ShopLedger — Task Tracking List

## Overview
This task list tracks the execution of each authorized step for **ShopLedger**. Per the project governance workflow, work is executed strictly one step at a time, requiring explicit approval (`"Approved. Proceed."`) before beginning the next step.

---

## Current Status Summary
- **Completed Steps**:
  - **Step 0 — Frontend Audit and Project Plan** [x]
  - **Step 1 — Backend Foundation** [x]
  - **Step 2 — Upload Service & Storage** [x]
  - **Step 3 — Gemini Structured Extraction Service** [x]
  - **Step 4 — Review & Confirmation Workflow** [x]
  - **Step 5 — Ledger & Search Filtering** [x]
  - **Step 6 — Duplicate Detection & Frontend Schema Integration** [x]
  - **Step 7 — Dashboard Aggregations & Evidence** [x]
  - **Step 8 — Safe Question Answering Engine** [x]
  - **Step 9 — Formula-Injection Safe CSV Export** [x]
  - **Step 10 — Bilingual Interface, Accessibility & Polish** [x]
  - **Step 11 — Demo Readiness & Test Dataset** [x]
  - **Step 12 — Voice Assistant Quick-Log (< ₹1,000) & Data Column** [ ]
- **Current Authorized Step**: **Step 12 — Voice Assistant Quick-Log (< ₹1,000) & Data Column (Awaiting Approval)**
- **Overall Progress**: 12 / 13 Steps Completed (92% Complete)

---

## Detailed Task Breakdown

### Step 0: Frontend Audit & Project Plan (COMPLETED)
- [x] Inspect Claude-built React frontend structure, dependencies, and configuration.
- [x] Verify routing, components, accessibility, and state management patterns.
- [x] Audit network calls in `src/api.ts` and in-memory behaviors in `src/mock.ts`.
- [x] Audit bilingual localization files (`en.json`, `hi.json`) and string completeness.
- [x] Map UI states (idle, loading, error, empty, success, retry) across all 5 views.
- [x] Identify contract mismatches (status enums, file URLs, paise vs rupees, categories).
- [x] Create `frontend_integration_audit.md` with complete documentation.
- [x] Create `implementation_plan.md` defining architecture, SQLite schema, and API contracts.
- [x] Create `task_list.md` for continuous step-by-step progress tracking.
- [x] Create/update root `.env.example` and `.env` with Gemini API key (git-ignored).
- [x] Update `README.md` with full architecture, setup, and run instructions.
- [x] Verify frontend builds and runs cleanly (`npm run build` and `npm run dev`).

---

### Step 1: Backend Foundation (COMPLETED)
- [x] Initialize Python backend directory structure (`backend/app/...`).
- [x] Create `backend/requirements.txt` (`fastapi`, `uvicorn`, `pydantic-settings`, `google-genai`, `pytest`, `httpx`).
- [x] Implement `app/config.py` with Pydantic settings loading `.env`.
- [x] Implement `app/database.py` with SQLite connection, WAL mode, foreign keys, and tables (`receipts`, `receipt_items`, `receipt_events`).
- [x] Implement standardized response envelope middleware (`{"success": true, "data": ..., "error": null}`).
- [x] Implement centralized error handlers returning standard error envelopes without leaking stack traces.
- [x] Configure CORS for frontend dev server (`http://localhost:5173`).
- [x] Configure Vite proxy in `vite.config.ts` to seamlessly route `/api` requests to backend.
- [x] Create health check endpoint `GET /api/health`.
- [x] Run automated pytest tests for database schema, migrations, and envelope consistency (5/5 passed).
- [x] Verify live proxy forwarding between Vite (`5173`) and FastAPI (`8000`).

---

### Step 2: Upload Service & Storage (COMPLETED)
- [x] Create storage directories (`backend/data/uploads/`).
- [x] Implement file upload validation (JPG, PNG, PDF; MIME check; max 10MB; filename sanitization).
- [x] Implement SHA-256 calculation on uploaded streams.
- [x] Implement `POST /api/receipts/upload` endpoint returning `{ "id": string }`.
- [x] Implement file retrieval endpoint `GET /api/receipts/{id}/file` (and HEAD support) with proper MIME headers.
- [x] Implement `receipt_service.py` to handle storage and database record creation (`status = 'uploaded'`).
- [x] Add automated pytest tests for upload success, invalid file types, size limits, and SHA-256 calculation (7/7 passed).
- [x] Verify live upload and file streaming through Vite proxy (`http://localhost:5173/api/receipts/upload`).

---

### Step 3: Gemini Structured Extraction Service (COMPLETED)
- [x] Implement `app/services/gemini_service.py` using `google-genai` SDK and configured `gemini-3.5-flash` model.
- [x] Formulate strict system instructions (prompt injection defense, no hallucinations, null for unreadable).
- [x] Define Pydantic schema for structured receipt extraction (`ReceiptExtractionResult`, `ExtractedLineItem`).
- [x] Implement `POST /api/receipts/{id}/extract` endpoint returning live extracted `Receipt` object.
- [x] Implement `GET /api/receipts/{id}` endpoint returning `Receipt` object with line items.
- [x] Implement `GET /api/receipts` supporting query params (`status=pending`, search, etc.).
- [x] Implement dashboard summary and category routes (`/api/dashboard/summary`, `/api/dashboard/categories`).
- [x] Save raw Gemini JSON response in `receipts.raw_extraction_json` for auditing.
- [x] Store monetary amounts as integer paise (`line_total_paise`, `total_paise`).
- [x] Add automated pytest tests for Gemini extraction service (14/14 tests passing).
- [x] Verify live extraction on sample stationery bill extracting vendor, date, items, total, and category.
- [x] Connect frontend to live backend via `VITE_API_BASE_URL=http://localhost:8000`.

---

### Step 4: Review & Confirmation Workflow (COMPLETED)
- [x] Present Step 4 Scope, File Impact, API Contracts, Validation Rules, and UI States.
- [x] Receive explicit approval ("Approved. Proceed.") before implementing code.
- [x] Implement `save_receipt_draft(id, payload)` in `receipt_service.py` to persist edits (`PATCH /api/receipts/{id}`).
- [x] Implement `confirm_receipt(id)` with strict financial validations in `receipt_service.py` (`POST /api/receipts/{id}/confirm`).
- [x] Implement `PATCH /api/receipts/{id}` and `POST /api/receipts/{id}/confirm` in `routers/receipts.py`.
- [x] Transition confirmed receipts to status `confirmed` with `confirmed_at` timestamp.
- [x] Log audit events (`EDITED`, `CONFIRMED`) in `receipt_events`.
- [x] Add automated pytest tests for review, editing, validation, and confirmation (`tests/test_review_confirmation.py` - 3/3 passed).
- [x] Verify live review screen interaction (save draft, validation error, confirm, read-only lock).
- [x] Stop and present Step 4 results for review.

---

### Step 5: Ledger & Search Filtering (COMPLETED)
- [x] Present Step 5 Scope, File Impact, API Contracts, Query Filters, and UI States.
- [x] Implement `list_receipts` in `receipt_service.py` with multi-parameter filtering (`q`, `from_date`, `to_date`, `category`, `vendor`, `status_filter`).
- [x] Query param mapping for `from` alias via `Query(None, alias="from")` in `routers/receipts.py`.
- [x] Text search filtering across vendor names and line item descriptions.
- [x] Ledger view hooked to live backend endpoint with status filter (`confirmed` for ledger, `pending` for home review list).
- [x] Confirmed receipts ordered by date descending.
- [x] Stop and present Step 5 results for review.

---

### Step 6: Duplicate Detection (Exact & Similar) & Frontend Schema Integration (COMPLETED)
- [x] Present Step 6 Scope, File Impact, API Contracts, Database Schema Updates, and UI States.
- [x] Receive explicit approval ("Approved. Proceed.") before implementing code.
- [x] Backend database schema migration for new user frontend fields (`invoice_number`, `tax_paise`, `discount_paise`, `payment_method`, `notes`, item `quantity` and `unit_price_paise`).
- [x] Update `backend/app/models.py` (`ReceiptUpdatePayload`, `ItemPayload`) to receive new frontend fields.
- [x] Update `backend/app/services/receipt_service.py` (`get_receipt_details`, `save_receipt_draft`) to serialize/persist new fields.
- [x] Update `src/api.ts` `save` function to forward all new fields to `PATCH /api/receipts/{id}`.
- [x] Implement exact SHA-256 duplicate detection during ingestion/upload and set `duplicate_of_receipt_id` and `status = 'duplicate'`.
- [x] Implement similar duplicate detection during extraction: normalized vendor (alphanumeric lowercase) + date + `total_paise` matching any existing confirmed receipt.
- [x] Return conflicting receipt details in `duplicateOf` object so the owner can compare both receipts side-by-side.
- [x] Verify `POST /api/receipts/{id}/discard-duplicate` (marks `status = 'discarded_duplicate'`).
- [x] Verify `POST /api/receipts/{id}/keep-separate` (resets to `status = 'needs_review'` and clears `duplicate_of_receipt_id`).
- [x] Connect and verify `ReviewReceiptModal` duplicate warning card and owner resolution actions ("Discard upload as duplicate" vs "Keep as separate purchase").
- [x] Add automated pytest tests for exact SHA-256 duplicate detection, similar fuzzy match, discard, and keep-separate actions (`tests/test_duplicate_detection.py` - 5/5 passed).
- [x] Stop and present Step 6 results for review.

---

### Step 7: Dashboard Aggregations & Evidence (COMPLETED)
- [x] Present Step 7 Scope, File Impact, API Contracts, Aggregation Rules, and UI States.
- [x] Receive explicit approval ("Approved. Proceed.") before implementing code.
- [x] Ensure `GET /api/dashboard/summary` computes totals strictly from `confirmed` records.
- [x] Ensure `GET /api/dashboard/categories` aggregates category spending strictly from `confirmed` records.
- [x] Compute all monetary figures using integer paise arithmetic in application code (never floating-point, never Gemini).
- [x] Verify `Home` view stats cards, category progress bars, and top vendor rows reflect live calculations.
- [x] Verify category and top vendor breakdown links navigate to filtered ledger (`/#/ledger?category=...` and `/#/ledger?vendor=...`).
- [x] Add automated pytest tests for dashboard calculations, zero-state behavior, and evidence isolation (`tests/test_dashboard.py` - 3/3 passed).
- [x] Stop and present Step 7 results for review.

---

### Step 8: Safe Question Answering Engine (COMPLETED)
- [x] Present Step 8 Scope, File Impact, API Contracts, Query Dispatcher, and UI States.
- [x] Receive explicit approval ("Approved. Proceed.") before implementing code.
- [x] Implement `POST /api/questions/ask` with strict intent validation supporting only 5 safe queries:
  1. `TOTAL_SPEND`: Overall confirmed spend and receipt count.
  2. `CATEGORY_SPEND`: Confirmed spend broken down by category.
  3. `TOP_VENDOR`: Shop/supplier with highest confirmed spend.
  4. `DATE_RANGE`: Confirmed spend between dates.
  5. `WAITING_REVIEW`: Receipts waiting for owner check.
- [x] Execute fixed safe SQL queries in application code; never allow Gemini to generate SQL or query the database directly.
- [x] Calculate all financial metrics in application code; use Gemini solely to phrase verified results in natural English/Hindi.
- [x] Return standard friendly fallback for unsupported questions: *"I can answer simple questions about your confirmed expenses. I cannot calculate profit because sales revenue is not recorded."*
- [x] Return supporting receipt objects/IDs so the frontend can display clickable evidence cards.
- [x] Add automated pytest tests for all 5 intents, unsupported question handling, and bilingual responses (`tests/test_questions.py` - 5/5 passed).
- [x] Stop and present Step 8 results for review.

---

### Step 9: Formula-Injection Safe CSV Export (COMPLETED)
- [x] Present Step 9 Scope, File Impact, API Contracts, Security Checks, and UI States.
- [x] Receive explicit approval ("Approved. Proceed.") before implementing code.
- [x] Implement `GET /api/export/csv` generating CSV of confirmed receipts strictly (`backend/app/routers/export.py`).
- [x] Prepend single quote `'` to any cell starting with formula trigger characters (`=`, `+`, `-`, `@`) to neutralize CSV injection attacks in Excel / Google Sheets.
- [x] Escape double quotes and commas following standard RFC 4180 CSV specifications via standard Python `csv.writer`.
- [x] Include `Vendor, Date, Category, Currency, Total` formatted exactly to match frontend `shopledger-expenses.csv`.
- [x] Verify currency totals match ledger calculations exactly (positive float with 2 decimal places from `total_paise / 100.0`).
- [x] Verify frontend CSV download button in `Ledger` view (`ShopLedger Expenses.csv`) via Vite proxy.
- [x] Add automated pytest tests for CSV content, formula injection mitigation, and column formatting (`tests/test_csv_export.py` - 4/4 passed).
- [x] Stop and present Step 9 results for review.

---

### Step 10: Bilingual Interface, Accessibility & Polish (COMPLETED)
- [x] Present Step 10 Scope, File Impact, Localization Parity, Accessibility, and UI States.
- [x] Receive explicit approval ("Approved. Proceed.") before implementing code.
- [x] Verify complete English and Hindi parity across all screens, modals, badges, and alerts (145 keys synchronized in `en.json` and `hi.json` with 0 mismatches).
- [x] Localized all previously hardcoded UI strings (`rv.showPreview`, `rv.hidePreview`, `rv.autoFill`, `rv.cancelFinishLater`, `qa.assistant`, `common.dismiss`).
- [x] Verify persistent language choice across page reloads via `localStorage` with dynamic `document.documentElement.lang` and `document.title`.
- [x] Verify high contrast, large tap targets (minimum 48px), and responsive layout on mobile screens (`btn` min-h 48px, `field` min-h 48px).
- [x] Test keyboard navigation, focus outlines, and ARIA attributes (`role="status"`, `role="alert"`, `aria-live="polite"`, `aria-label`, `aria-modal="true"`).
- [x] Verify double-submit prevention across all async triggers (`uploading`, `isSubmitting`, `dupResolving`, `ex === 'busy'`, `l || !q.trim()`).
- [x] Verified clean TypeScript compilation and Vite build (`tsc --noEmit && vite build`).
- [x] Stop and present Step 10 results for review.

---

### Step 11: Demo Readiness & Test Dataset (COMPLETED)
- [x] Present Step 11 Scope, File Impact, Test Dataset Composition, End-to-End Walkthrough Plan.
- [x] Receive explicit approval ("Approved. Proceed.") before implementing code.
- [x] Prepare 20 synthetic receipt fixtures with `ground_truth.json` (images, PDFs, blurry, duplicates, missing data) in `backend/data/test_fixtures/`.
- [x] Seed database with realistic stationery shop expenses for smooth demo walkthrough (`backend/scripts/seed_demo_data.py`).
- [x] Verify full end-to-end user journey (upload -> Gemini extract -> review/correct -> confirm -> ledger -> dashboard -> question -> CSV).
- [x] Finalize `README.md` with complete local run, testing commands, and 3-minute hackathon demo script.
- [x] Add automated test suite for dataset and fixture verification (`tests/test_dataset_fixtures.py` - 3/3 passed).
- [x] Full test suite passing across all 10 test modules (40/40 passed).
- [x] All 12 initial build order steps (Steps 0 through 11) successfully delivered and verified!

---

### Step 12: Voice Assistant Quick-Log (< ₹1,000) & Data Column (COMPLETED)
- [x] Present Step 12 Scope, File Impact, API Contracts, Database Schema Updates, and UI States.
- [x] Receive explicit approval ("add voice feature beside add receit picture") before implementing code.
- [x] Backend database migration: add `data TEXT` and `type TEXT DEFAULT 'expense'` columns to `receipts` table in `backend/app/database.py`.
- [x] Implement `POST /api/receipts/voice-quick-entry` in `backend/app/routers/receipts.py` and `backend/app/services/receipt_service.py`:
  - Logs as `type = 'income'` (money added, rendered in bold green with `+` sign).
  - Generate voucher record and SVG file placeholder in `backend/data/uploads` (`VOICE MONEY ADDED VOUCHER` with `+ INR ...`).
  - Store spoken text / calculations in `receipts.data`.
  - Save as `status = 'confirmed'`, insert line items and `VOICE_QUICK_ENTRY` event log.
- [x] Update `Receipt` type in `src/types.ts` and serialization in `receipt_service.py` to include `data` and `type: 'income'`.
- [x] Implement browser Web Speech API voice assistant (`SpeechRecognition`) in frontend:
  - Clean button showing Microphone icon with "Add audio" (`voice.addAudio`) positioned beside "Add Receipt Picture" button.
  - Removed `< 1000` limit and `entry<1000` button text; allows adding any audio amounts.
  - Live preview and transaction row always display as money added with bold green font and `+` sign (`+ ₹...`).
  - Bilingual recognition: Hindi (`hi-IN`) and English (`en-IN`).
  - Spoken number and amount parsing (e.g., "Chai 40", "Cash 500").
  - Instant ledger logging and toast notification.
- [x] Display `data` column/pill on the Transactions / Ledger view in `src/App.tsx`.
- [x] Add bilingual translation strings in `src/locales/en.json` and `src/locales/hi.json`.
- [x] Automated pytest tests verifying `type: 'income'`, green `+` sign voucher, and `data` column persistence (`backend/tests/test_voice_entry.py` - 3/3 passed).
- [x] Verify clean build (`npm run build`) and test suite (48/48 passed).
- [x] Step 12 successfully delivered and verified!

---

### Step 13: Enhanced Hindi & Haryanvi Audio Engine & Dialect Accent Parser (COMPLETED)
- [x] Implement comprehensive Hindi & Haryanvi accent and dialect recognition in `src/hindiSpeechParser.ts`:
  - Devanagari digit converter (`०, १, २, ३, ४, ५, ६, ७, ८, ९` -> `0-9`).
  - Haryanvi hundred multiplier normalization: automatically converts Haryanvi `सै` / `sai` when following numbers or fractions into `सौ` (e.g. `च्यार सै` -> 400, `दो सै` -> 200, `डेढ सै` -> 150, `ढाई सै` -> 250, `साढ़े तीन सै` -> 350).
  - Multi-dialect colloquial fractions: handles Haryanvi & rural spellings (`डेढ`, `डैढ`, `ढाई`, `साढे`, `साढै`, `सवाय`, `पौणे`, `पोने`).
  - Haryanvi & regional numerals: `दू`, `दोय` (2), `तीन्या` (3), `च्यार`, `चयार`, `chyaar` (4), `पंज` (5), `छे`, `छी`, `chhe` (6), `नू` (9), `दहे` (10), `ग्यारा` (11), `बारा` (12), `तेरा` (13), `चौदा` (14), `पंदरा` (15), `सोला` (16), `सतरा` (17), `अठारा` (18), `उगणीस`, `उगनीस`, `गुणीस`, `गुनीस` (19), `चाली` (40), `पचासे` (50), `हज्यार` (1000).
  - Regional additive conjunctions: splits and sums items connected by `अर`, `अरु`, `गैल`, `और`, `and`, `plus`, `+`, `तथा`, `जमा` (e.g. `डेढ सै चाय अर बीस बिस्कुट` -> 170).
  - Dialect transaction verbs & postpositions stripped from payer names: `रुपै`, `रूपै`, `रिपिए`, `रपिए`, `रुपिया`, `टका`, `आग्ये`, `आगे`, `आग्या`, `देग्या`, `देगे`, `देलक`, `मिलल`, `पागे`, `जोड़ ले`, `लिख ले`, `चढ़ा ले`, `धर दे`, `खाते म्ह`, `गल्ले म्ह`, `सूं`, `पै`, `पे`, `रोकड़`, `रोकड़ा`.
  - Preserves titles and customer names accurately: `ताऊ`, `ताऊ रामफल`, `चौधरी साहब`, `मास्टर जी`, `काका`, `लाला जी`, `पंडित जी`, `सरपंच`.
- [x] Upgrade `VoiceAssistantModal` in `src/App.tsx`:
  - Modal subtitle: `हिन्दी, हरियाणवी व देसी लहजे (Hindi & Haryanvi Accents)`.
  - Dialect helper card with visual indicator (`🎙️ हिन्दी, हरियाणवी व सभी देसी लहजे समर्थित हैं`).
  - Clickable dialect chips: `ताऊ 500 जोड़ ले (हरियाणवी)`, `च्यार सै रुपै (हरियाणवी)`, `डेढ सै + 20 (देसी जोड़)`, `चौधरी साहब 1200 आग्ये`, `दू सौ पचास (भोजपुरी)`, `मास्टर जी 750 नकद`.
  - Prominent bold green added money display (`+ ₹{amount}`) with breakdown indicator.
  - Editable payer/source and amount inputs.
- [x] Synchronize bilingual localization in `src/locales/en.json` and `src/locales/hi.json`.
- [x] Verified frontend build and backend tests (68 passed).
