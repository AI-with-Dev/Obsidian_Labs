# ShopLedger (frontend only)
React + TypeScript + Vite + Tailwind v4. English and Hindi UI. Runs on mock data until a backend is connected.

## Run
```
npm install
npm run dev        # http://localhost:5173
npm run build      # type-checks, then builds
```

## Connect the backend (Antigravity)
1. Copy `.env.example` to `.env` and set `VITE_API_BASE_URL` (e.g. `http://localhost:8000`). Empty = mock mode.
2. All network code lives in `src/api.ts`. `src/mock.ts` is the fake backend; ignore or delete it once real.
3. Every endpoint must answer `{"success":true,"data":...,"error":null}` (the `/api/export/csv` call returns the raw CSV file).
   - `POST /api/receipts/upload` (multipart field `file`) -> `{id}`
   - `POST /api/receipts/{id}/extract` -> Receipt (status `draft`, or `duplicate` with `duplicateOfId`)
   - `GET /api/receipts/{id}` -> Receipt; `PATCH /api/receipts/{id}` body: vendor, date, currency, items, total, category -> Receipt
   - `POST /api/receipts/{id}/confirm` -> Receipt (status `confirmed`); `.../keep-separate` -> Receipt; `.../discard-duplicate` -> null
   - `GET /api/receipts?q&from&to&category&vendor&status=confirmed|pending` -> Receipt[]
   - `GET /api/dashboard/summary` -> Summary; `GET /api/dashboard/categories` -> CategoryTotal[]
   - `POST /api/questions/ask` body `{question, lang}` -> Answer (answer text in the requested `lang`, plus supporting `receipts`)
   - Shapes are in `src/types.ts`. Totals come from the server; the browser never sums money.

## Language
Strings live in `src/locales/en.json` and `hi.json` (same keys). Add a category: add it to `CATEGORIES` in `src/types.ts` and add `cat.<key>` to both files.
