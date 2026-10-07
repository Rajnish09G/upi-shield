# UPI Shield

UPI Shield is a starter platform for triaging suspected payment-brand phishing
sites using crawler, visual, behavioral, and graph signals.

## Project layout

- `backend/`: FastAPI service and detection pipeline modules.
- `frontend/`: Next.js/TypeScript triage UI starter.
- `brands/`: reference screenshots, organized by brand.
- `data/`: crawler seeds and labelled examples.

## Local development

1. Copy `.env` to a local environment file and replace development passwords.
2. Start infrastructure:

   ```text
   docker compose up -d
   ```

3. Install Python dependencies and start the API:

   ```text
   pip install -r requirements.txt
   uvicorn backend.main:app --reload
   ```

The base requirements target the crawler, API, pHash detector, graph, and
reporting features. Optional CNN/OCR dependencies are listed in
`requirements-ml.txt` and may require a compatible Python/PyTorch build.

4. Open `http://localhost:8000/health`.

The crawler and takedown modules are intentionally conservative starter
interfaces. Add authorization, rate limits, legal review, and provider-specific
policies before crawling or reporting real sites.

## End-to-end demo flow

1. Start Docker and the API.
2. Open `http://localhost:8000/docs`.
3. Use `POST /captures` with an authorized URL to capture, score, and persist a
   detection in PostgreSQL.
4. Review records at `GET /detections` or in the frontend at
   `http://localhost:3000`.
5. Open a record’s detail view and download its PDF evidence report.
6. Add labelled local rows to `data/labels.csv` with URL, brand, screenshot,
   DOM, and label (`phishing` or `benign`), then call `GET /evaluation`.
   Official Paytm, PhonePe, Google Pay, and SBI domains receive a domain brand
   hint and are kept benign when no suspicious form, sensitive input, or
   redirect signal is present. Off-domain pages still rely on visual and
   behavioural evidence.
7. Use `POST /discover` for analyst, message, or CT-log URL batches. APK files
   can be inspected statically with `POST /apps/inspect`; never execute
   untrusted packages.
