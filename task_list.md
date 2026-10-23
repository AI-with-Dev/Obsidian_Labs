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
- **Current Authorized Step**: **Step 4 — Review & Confirmation Workflow (IN PROGRESS)**
- **Overall Progress**: 3 / 12 Steps Completed; Step 4 In Progress

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

### Step 4: Review & Confirmation Workflow (CURRENT AUTHORIZED STEP - IN PROGRESS)
- [/] Define Pydantic schema for receipt edits (`ReceiptUpdate`, `ItemUpdate`).
- [/] Implement `save_receipt_draft(id, payload)` in `receipt_service.py`.
- [/] Implement `confirm_receipt(id)` with strict validation in `receipt_service.py`.
- [/] Implement `PATCH /api/receipts/{id}` endpoint in `routers/receipts.py`.
- [/] Implement `POST /api/receipts/{id}/confirm` endpoint in `routers/receipts.py`.
- [/] Transition confirmed receipts to status `confirmed` with `confirmed_at` timestamp.
- [/] Log audit events (`EDITED`, `CONFIRMED`) in `receipt_events`.
- [/] Add automated pytest tests for review, editing, validation, and confirmation.
- [ ] Stop and present Step 4 results for review.

---

### Step 5: Ledger & Search Filtering (PENDING APPROVAL)
- [ ] Connect full `Ledger` view to live API.
- [ ] Verify text search across vendors and line item descriptions.
- [ ] Verify category and date-range filters.
- [ ] Verify clicking any receipt opens its detail view.
- [ ] Stop and present Step 5 results for review.

---

### Step 6: Duplicate Detection (Exact & Similar) (PENDING APPROVAL)
- [ ] Implement exact SHA-256 duplicate detection during ingestion.
- [ ] Implement similar duplicate detection (normalized vendor + date + total_paise matching confirmed receipt).
- [ ] Populate `duplicate_of_receipt_id` and set `status = 'duplicate'`.
- [ ] Implement `POST /api/receipts/{id}/discard-duplicate` (marks `discarded_duplicate`).
- [ ] Implement `POST /api/receipts/{id}/keep-separate` (resets to `needs_review`).
- [ ] Connect frontend `Dup` component for side-by-side comparison.
- [ ] Verify both "Discard" and "Keep Separate" owner decisions.
- [ ] Stop and present Step 6 results for review.

---

### Step 7: Dashboard Aggregations & Evidence (PENDING APPROVAL)
- [ ] Ensure `GET /api/dashboard/summary` computes totals strictly from `confirmed` records.
- [ ] Ensure `GET /api/dashboard/categories` aggregates category spending.
- [ ] Compute all monetary figures using integer paise arithmetic in application code (never floating-point, never Gemini).
- [ ] Connect `Home` view metrics and breakdown rows to live API.
- [ ] Verify category and vendor breakdown rows navigate to filtered ledger with evidence.
- [ ] Stop and present Step 7 results for review.

---

### Step 8: Safe Question Answering Engine (PENDING APPROVAL)
- [ ] Implement intent classifier supporting strictly 5 allowed intents:
  1. Overall spend & receipt count
  2. Spend by category
  3. Highest spend vendor
  4. Spend between specific dates
  5. Receipts waiting for review
- [ ] Execute fixed safe SQL queries in application code.
- [ ] Format numerical answers using verified calculations; use Gemini solely to phrase naturally in English/Hindi.
- [ ] Handle unsupported queries with standard scope explanation message.
- [ ] Connect `Ask` view and verify clicking source receipts loads evidence.
- [ ] Stop and present Step 8 results for review.

---

### Step 9: Formula-Injection Safe CSV Export (PENDING APPROVAL)
- [ ] Implement `GET /api/export/csv` generating CSV of confirmed receipts.
- [ ] Escape leading dangerous characters (`=`, `+`, `-`, `@`) with prepended single quote.
- [ ] Verify currency totals match ledger calculations exactly.
- [ ] Connect frontend CSV download button and verify file in browser.
- [ ] Stop and present Step 9 results for review.

---

### Step 10: Bilingual Interface, Accessibility & Polish (PENDING APPROVAL)
- [ ] Verify complete English and Hindi parity across all screens and notifications.
- [ ] Verify persistent language choice across page reloads via `localStorage`.
- [ ] Verify high contrast, large tap targets, and responsive layout on mobile screens.
- [ ] Test keyboard navigation and ARIA attributes (`role="status"`, `role="alert"`).
- [ ] Verify double-submit prevention on upload and confirmation buttons.
- [ ] Stop and present Step 10 results for review.

---

### Step 11: Demo Readiness & Test Dataset (PENDING APPROVAL)
- [ ] Prepare 20 synthetic receipts with `ground_truth.json` (images, PDFs, blurry, duplicates, missing data).
- [ ] Seed database with initial stationery shop expenses for smooth demo walkthrough.
- [ ] Verify full end-to-end user journey (upload -> Gemini extract -> review/correct -> confirm -> ledger -> dashboard -> question -> CSV).
- [ ] Finalize `README.md` with complete local run and testing commands.
- [ ] Stop and present full project demonstration for final sign-off.
