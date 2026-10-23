# ShopLedger — Frontend Integration Audit (Step 0)

## Executive Summary
This document provides a comprehensive architectural and integration audit of the supplied Claude-built React frontend for **ShopLedger**. Per project requirements, this frontend is treated as the **authoritative source of truth** for design aesthetics, user flows, copy, components, interaction design, and accessibility. No visual redesign or frontend refactoring is permitted; our mandate is to build a reliable, secure FastAPI + SQLite backend that integrates seamlessly with minimal frontend modifications.

---

## 1. Framework, Version & Folder Structure

### Tech Stack Versions
- **Core Library**: React `^18.3.1`, React DOM `^18.3.1`
- **Build Tooling**: Vite `^6.0.0` with `@vitejs/plugin-react` `^4.3.1`
- **Type Checking**: TypeScript `^5.5.4`
- **Styling**: Tailwind CSS `^4.0.0` with `@tailwindcss/vite` `^4.0.0`
- **Font Stack**: Google Fonts (`Noto Sans` and `Noto Sans Devanagari` in weights 400, 600, 700) loaded via `index.html`
- **Routing**: Lightweight native browser hash routing via custom `useHash` hook in `App.tsx`
- **State Management**: Built-in React hooks (`useState`, `useEffect`, `useCallback`, `useContext`)
- **Icons**: Accessible native Unicode symbols (`✎`, `✓`, `⚠`, `✕`, `→`, `←`) — no third-party icon bundle needed

### Existing Folder Structure
```text
/Users/devgarg/Obsidian_Labs/Obsidian_Labs/
├── .env.example              # Frontend environment template (VITE_API_BASE_URL)
├── .git/                     # Git tracking
├── index.html                # HTML entrypoint loading Google Fonts & Noto Sans
├── package.json              # Frontend dependencies and dev scripts
├── README.md                 # Frontend run instructions & API overview
├── tsconfig.json             # TypeScript configuration
├── vite.config.ts            # Vite configuration with React + Tailwind v4 plugins
└── src/
    ├── App.tsx               # Main application component with all page views & routes
    ├── api.ts                # API client service layer with toggleable mock/network mode
    ├── i18n.tsx              # Localization provider, language context, and formatters
    ├── index.css             # Tailwind v4 import and base typography/colors
    ├── main.tsx              # React DOM entrypoint wrapping App in I18n provider
    ├── mock.ts               # Stand-in in-memory mock backend
    ├── types.ts              # Domain interfaces, statuses, and category definitions
    └── locales/
        ├── en.json           # English translation strings (46 keys)
        └── hi.json           # Hindi translation strings (46 keys in Devanagari)
```

---

## 2. Pages, Components & Routes

The application uses hash-based client-side routing (`useHash()` listening to `window.location.hash`).

| Route Hash | Screen / View Component | Purpose & Description |
| :--- | :--- | :--- |
| `#/` or `""` | `Home` | Shop overview dashboard: confirmed total spend, confirmed receipt count, pending review count, waiting receipts list, category spend breakdown, and top vendor breakdown. |
| `#/upload` | `Upload` | Receipt ingestion screen: file picker, client-side MIME validation, upload progress indicators, Gemini extraction trigger, and success redirection. |
| `#/receipt/:id` | `ReceiptPage` | Multi-mode review and detail screen: editable receipt form side-by-side with receipt image/preview; duplicate warning comparison (`Dup`); confirmation and discard actions. |
| `#/ledger` | `Ledger` | Filterable and searchable ledger of confirmed receipts (search query `q`, category dropdown, date range `from`/`to`, vendor dropdown) and CSV download action. Supports query strings like `#/ledger?category=inventory` or `#/ledger?vendor=...`. |
| `#/ask` | `Ask` | Small-business expense Q&A interface: 5 quick-prompt suggestion chips, free-form query input, answer display, and clickable source receipt list. |

### Key Shared UI Components (in `App.tsx`)
- `Badge({ s })`: Renders status indicator chip (`draft`: `✎ Waiting for your check`, `confirmed`: `✓ Confirmed`, `duplicate`: `⚠ Possible repeat`).
- `RList({ rs })`: Renders a list of receipt cards displaying vendor, date, category, formatted currency total, and status badge. Clicking navigates to `#/receipt/${r.id}`.
- `Rows({ rows })`: Renders tabular breakdown rows (for category totals and top vendors) with links directly into filtered ledger views.
- `State({ l, e, run, children })`: Generic wrapper for asynchronous data loading, displaying centered loading text or error card with retry button.
- `F({ label, warn, children })`: Accessible form control wrapper with bold label and optional contextual warning badge (`⚠ rv.unclear`).
- `Side({ x, h })`: Receipt summary card with thumbnail image used in side-by-side duplicate comparison.
- `Dup({ r, busy, onDiscard, onKeep })`: Duplicate resolution panel displaying the new upload alongside the existing confirmed receipt, offering explicit "Discard" or "Keep separate" decisions.

---

## 3. API Client Layer & Mock Integration

The existing frontend is already designed with an API abstraction layer in `src/api.ts`:
- Environment Variable: `VITE_API_BASE_URL`
- When `VITE_API_BASE_URL` is empty or undefined, all API functions fall back to simulated async operations in `src/mock.ts`.
- When `VITE_API_BASE_URL` is defined (e.g., `http://localhost:8000`), calls are dispatched over HTTP using `fetch()`.
- Standard Envelope:
  ```json
  {
    "success": true,
    "data": { ... },
    "error": null
  }
  ```
  On error (`!res.ok || !j?.success`), the client rejects with `j?.error?.message ?? j?.error ?? 'Request failed'`.

### Complete Inventory of API Calls

| API Function | HTTP Method & Path | Payload / Headers | Expected Response Data |
| :--- | :--- | :--- | :--- |
| `upload(file)` | `POST /api/receipts/upload` | `multipart/form-data` with field `file` | `{ "id": string }` |
| `extract(id)` | `POST /api/receipts/{id}/extract` | `application/json` (empty body) | `Receipt` object |
| `get(id)` | `GET /api/receipts/{id}` | None | `Receipt` object |
| `save(r)` | `PATCH /api/receipts/{id}` | `{ vendor, date, currency, items, total, category }` | `Receipt` object |
| `confirm(id)` | `POST /api/receipts/{id}/confirm` | `application/json` (empty body) | `Receipt` object (status `confirmed`) |
| `discard(id)` | `POST /api/receipts/{id}/discard-duplicate` | `application/json` (empty body) | `void` / `{}` |
| `keepSeparate(id)` | `POST /api/receipts/{id}/keep-separate` | `application/json` (empty body) | `Receipt` object (status `draft`) |
| `list(filters)` | `GET /api/receipts?q=&from=&to=&category=&vendor=&status=` | Query parameters | `Receipt[]` |
| `summary()` | `GET /api/dashboard/summary` | None | `Summary` object |
| `categories()` | `GET /api/dashboard/categories` | None | `CategoryTotal[]` |
| `ask(question, lang)` | `POST /api/questions/ask` | `{ "question": string, "lang": "en" \| "hi" }` | `Answer` object |
| `exportCsv()` | `GET /api/export/csv` | None | Direct file download (`text/csv` blob) |

---

## 4. Inferred Data Contracts & Field Shapes

### Domain Types (`src/types.ts`)

#### 1. Receipt Interface
```typescript
export type Status = 'draft' | 'confirmed' | 'duplicate'

export interface Item {
  name: string
  amount: number
}

export interface Receipt {
  id: string
  vendor: string
  date: string          // 'YYYY-MM-DD' or '' if unreadable/ambiguous
  currency: string      // e.g. 'INR'
  items: Item[]         // parsed line items
  total: number | null  // Rupee decimal float/int, null if unreadable
  category: string      // 'inventory' | 'packaging' | 'transport' | 'utilities' | 'rent' | 'repairs' | 'other'
  status: Status        // 'draft' | 'confirmed' | 'duplicate'
  fileUrl: string       // accessible URL or endpoint to view receipt image/PDF
  fileName: string      // original filename (e.g. 'sharma_bill.jpg')
  flags: string[]       // list of flagged fields needing review, e.g. ['date', 'vendor', 'total']
  duplicateOfId?: string // ID of conflicting earlier receipt if status === 'duplicate'
}
```

#### 2. Summary Interface
```typescript
export interface Summary {
  totalSpent: number     // calculated server-side from confirmed receipts only
  confirmedCount: number // count of confirmed receipts
  reviewCount: number    // count of pending receipts needing owner review
  topVendors: { vendor: string; amount: number }[] // top 3-5 vendors by spend
}
```

#### 3. Category Total Interface
```typescript
export interface CategoryTotal {
  category: string       // matches one of CATEGORIES
  amount: number         // sum of confirmed spend for category
}
```

#### 4. Q&A Answer Interface
```typescript
export interface Answer {
  answer: string         // natural language answer in requested language
  supported: boolean     // true if mapped to a supported intent; false otherwise
  receipts: Receipt[]    // supporting confirmed receipts proving the calculation
}
```

#### 5. Search & Filter Parameters
```typescript
export interface Filters {
  q?: string             // search text matching vendor or item name
  from?: string          // ISO date lower bound 'YYYY-MM-DD'
  to?: string            // ISO date upper bound 'YYYY-MM-DD'
  category?: string      // exact category filter
  vendor?: string        // exact vendor filter
  status?: 'confirmed' | 'pending' // filter confirmed ledger vs pending review
}
```

---

## 5. UI States Across All Screens

| Screen | Idle / Default State | Loading State | Success State | Error & Validation States | Retry Mechanism |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Home (`/`)** | Displays 3 metric cards, waiting list, category rows, vendor rows | `State` component displays `common.loading` ("Please wait…") | Complete dashboard populated | Card showing `common.error` with alert role | "Try again" button calling `useLoad.run()` |
| **Home Empty** | When `confirmedCount === 0`, shows helpful card `home.empty` ("No confirmed receipts yet...") | — | Card includes primary button `home.add` linking to `#/upload` | — | — |
| **Upload (`/upload`)** | File selection button + helper instructions | `st === 'up'`: `up.sending`<br/>`st === 'read'`: `up.reading` + progress bar | `st === 'done'`: `✓ up.done` + button linking to `#/receipt/${id}` | `up.badType` for non-JPG/PNG/PDF;<br/>`up.fail` on network/server error | Retry button `common.retry` replaces upload button |
| **Review (`/receipt/:id`)** | Receipt preview beside editable form with inputs for vendor, date, currency, items, total, category | `rv.saving` ("Please wait…") during save or confirmation | Note banner: `✓ rv.saved` or `✓ rv.confirmed`; inputs lock to read-only when confirmed | Field warnings (`⚠ rv.unclear`) on flagged fields; inline error `common.error` on failed save | User can re-edit and press Save or Confirm again |
| **Duplicate (`/receipt/:id` when duplicate)** | Side-by-side comparison of new upload vs original receipt | Handled by `State` during fetching of `duplicateOfId` | Discard shows `✓ rv.gone` + link to Home; Keep Separate unlocks review | Inline alert if discard or keep request fails | Buttons remain active to retry |
| **Ledger (`/ledger`)** | Filter bar + list of confirmed receipts | `State` loading spinner/text while filtering or paginating | Populated list with vendor, date, category, total | `lg.empty` ("No receipts found.") when no matches; network error card | Clear filters button resets state; retry button reloads |
| **CSV Export** | "Download expenses (CSV)" button | `lg.exporting` ("Preparing your file…") | `✓ lg.exportOk` ("Your file is ready and has been downloaded") | `⚠ lg.exportErr` ("We could not prepare your file...") | Inline "Try again" button re-triggers export |
| **Ask (`/ask`)** | 5 prompt chips + search input | `qa.thinking` ("Finding the answer…") | Answer card + list of supporting source receipts | Error card `common.error` | "Try again" button re-submits the query |

---

## 6. Localization & i18n Architecture

### Existing Implementation
- **Provider**: `I18n` context provider in `src/i18n.tsx`.
- **Dictionaries**: Full parity between `src/locales/en.json` (46 keys) and `src/locales/hi.json` (46 keys).
- **Language Switch**: One-tap toggle button in the global header displaying `English` when in Hindi, or `हिन्दी` when in English.
- **Persistence**: User preference stored in `localStorage.getItem('lang')` / `localStorage.setItem('lang', l)`.
- **HTML Document Sync**: Automatically updates `document.documentElement.lang = lang` on change.
- **Currency & Date Formatting**:
  - `money(n, lang, currency)` formats using `Intl.NumberFormat(lang === 'hi' ? 'hi-IN' : 'en-IN', { style: 'currency', currency })`.
  - `day(date, lang)` formats using `toLocaleDateString(lang === 'hi' ? 'hi-IN' : 'en-IN', ...)`.
- **Hindi Quality**: Uses natural, respectful Devanagari Hindi phrases appropriate for Indian small-shop owners (e.g., "आपकी दुकान, एक नज़र में", "माल / स्टॉक", "पक्की रसीदें", "आपकी जाँच बाकी है").

### Localization Integration Plan for Backend
1. **Zero Translation Discrepancy**: Backend error messages should return machine-readable error codes (e.g., `VALIDATION_ERROR`, `RECEIPT_NOT_FOUND`, `DUPLICATE_FILE`, `UNSUPPORTED_FILE_TYPE`), allowing the frontend to present localized error copy.
2. **Q&A Endpoint Language Parameter**: The frontend already passes `lang` (`'en' | 'hi'`) in `POST /api/questions/ask`. The backend dispatcher will use this parameter to format the exact numerical answer in the selected language.

---

## 7. Gaps, Missing Functionality & Conflicting Assumptions

Through detailed line-by-line inspection, the following gaps and conflicting assumptions were identified between the frontend code and backend specifications:

### Gap 1: Status Enum Discrepancy
- **Specification**: Status state machine defines `uploaded`, `extracting`, `extraction_failed`, `needs_review`, `confirmed`, `discarded_duplicate`.
- **Frontend Code**: `types.ts` defines `export type Status = 'draft' | 'confirmed' | 'duplicate'`.
- **Impact**: `App.tsx` contains `icon = { draft: '✎', confirmed: '✓', duplicate: '⚠' }` and calls `t('status.' + s)`. If the backend returns `needs_review` or `discarded_duplicate`, the badge icon will fail and localization will render missing keys.
- **Resolution**: The backend DB will track full internal lifecycle states (`uploaded`, `extracting`, `extraction_failed`, `needs_review`, `confirmed`, `discarded_duplicate`), but the API response serializer will map:
  - `needs_review` -> `draft`
  - `confirmed` -> `confirmed`
  - `duplicate` (or duplicate flag detected) -> `duplicate`
  - When discarded, record transitions to `discarded_duplicate` and `discard` endpoint returns success.

### Gap 2: File Serving Endpoint URL (`fileUrl`)
- **Frontend Code**: `ReceiptPage` renders `<img src={f.fileUrl} .../>` and `<a href={f.fileUrl} target="_blank">`.
- **Existing Mock**: Produced SVG data URIs (`data:image/svg+xml...`).
- **Real Backend Requirement**: The backend must serve uploaded receipts securely.
- **Resolution**: Backend will provide `GET /api/receipts/{id}/file` streaming the original image or PDF. The `fileUrl` property on `Receipt` will be populated with `/api/receipts/${id}/file` (or fully-qualified URL based on `BASE_URL`).

### Gap 3: Monetary Decimal Representation vs. Integer Paise
- **Specification**: Store all currency as integer paise (`₹1,800.50 = 180050`). Never use floating-point arithmetic for financial calculations.
- **Frontend Code**: `Receipt.total` is `number | null` (in Rupees, e.g. `12450` or `1800.50`). Items are `{ name: string, amount: number }`.
- **Resolution**: The backend DB schema strictly uses `total_paise` and `line_total_paise` (INTEGER).
  - Incoming `PATCH`: Converts Rupee float/decimal to integer paise via `round(Decimal(str(val)) * 100)`.
  - Outgoing JSON: Converts `total_paise` to Rupee float via `paise / 100.0`.
  - All aggregations (sums, category totals, vendor totals) are computed in SQLite and Python using pure integer arithmetic before converting to Rupee decimals for JSON response.

### Gap 4: Category List Parity
- **Specification Text**: Mentions "categories Inventory, Packaging, Transport, Utilities, Other".
- **Frontend Code**: `CATEGORIES = ['inventory', 'packaging', 'transport', 'utilities', 'rent', 'repairs', 'other']`. Both `en.json` and `hi.json` have translations for all 7.
- **Resolution**: Backend validation and Gemini prompts will support all 7 categories defined in the frontend to avoid breaking existing UI options or mock data.

### Gap 5: Q&A Intent Scope & Fixed Dispatcher
- **Frontend Code**: 5 example question chips in `Ask`:
  1. `qa.ex1`: "How much have I spent in total?"
  2. `qa.ex2`: "How much did I spend on each type?"
  3. `qa.ex3`: "Which shop did I spend most at?"
  4. `qa.ex4`: "What did I spend between 1 and 15 October?"
  5. `qa.ex5`: "Which receipts are waiting for review?"
- **Specification**: Backend must validate query intent, run fixed safe SQL queries (no model-generated SQL), calculate results in Python, and return supporting receipts.
- **Resolution**: Implement intent classifier matching 5 allowed intents + fallback. Calculations run in Python; Gemini only assists in natural language phrasing in English or Hindi based on the verified backend calculation.

---

## 8. Minimal Proposed Frontend Changes

To maintain the Claude-built frontend as the definitive source of truth while ensuring seamless real backend connectivity:

1. **Proxy Configuration (`vite.config.ts`)**:
   Add a standard development proxy forwarding `/api` requests to `http://localhost:8000` so that relative URLs like `/api/receipts/{id}/file` resolve cleanly without CORS hurdles during local evaluation.
2. **Environment Variable Configuration (`.env`)**:
   Document setting `VITE_API_BASE_URL=http://localhost:8000` (or leaving empty to use Vite proxy).
3. **No Component or CSS Alterations**:
   Zero structural modifications to `App.tsx`, `index.css`, or locale files are required for Step 0 or initial backend integration.

---

## 9. Key Questions Resolved for Backend Architecture

1. **How should files be accessed?**
   Via `GET /api/receipts/{id}/file`, returning binary content with proper `Content-Type` (`image/jpeg`, `image/png`, `application/pdf`).
2. **How should duplicate detection present to the user?**
   When a newly extracted receipt matches SHA-256 or has vendor + date + total identical to an existing confirmed receipt, set `status = 'duplicate'` and populate `duplicateOfId` with the ID of the matched receipt. The frontend `Dup` component will automatically display the side-by-side comparison.
3. **Are unconfirmed receipts ever counted in dashboard metrics?**
   **Never.** Only `status = 'confirmed'` receipts are queried for `totalSpent`, category breakdowns, top vendors, and ledger exports.

---

*Audit completed on Step 0. Ready for user review and approval.*
