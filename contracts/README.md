# LandmarkAR API Contract

Single source of truth for the HTTP API shared between the React Native (Expo)
frontend and the Python backend. There are only three endpoints — keep it that way.

## Endpoints

| Method | Path             | Purpose                                                            |
| ------ | ---------------- | ------------------------------------------------------------------ |
| POST   | `/v1/jobs`       | Submit camera frame + lat/long as a background recognition job.    |
| GET    | `/v1/jobs/{jobId}` | Poll the job; read the recognized place from `result`.           |
| GET    | `/v1/health`     | Connectivity / version check.                                      |

## The core flow

1. App captures a frame and reads GPS (`latitude`, `longitude`).
2. App posts `multipart/form-data` to `POST /v1/jobs`:
   - `image` — raw JPEG/PNG bytes (max 8 MB)
   - `latitude`, `longitude` — WGS84 degrees
   - `headingDegrees` — optional compass facing (0–360, 0 = north) to help pick
     the place in front of the user
   - Returns `202` with a `jobId` (UUID).
3. App polls `GET /v1/jobs/{jobId}` every 1–2 s (exponential backoff, cap 10 s)
   until `status` is `succeeded` or `failed`.
4. On `succeeded`, `result` is the `Place`: `title`, `description`, plus useful
   details (`category`, `address`, `openingHours`, `imageUrl`, `sourceUrl`,
   `distanceMeters`). Show title + description on the AR overlay and detail card.
5. On `failed`, `error.code` explains why (e.g. `NO_PLACE_FOUND` — the app
   shows "keep scanning" and tries again).

## Conventions

- **Coords:** WGS84 degrees. Latitude `-90..90`, longitude `-180..180`.
- **Distances:** meters.
- **Timestamps:** ISO 8601 UTC (`2026-08-13T09:30:00Z`).
- **IDs:** `jobId` is a UUID; `place.id` is a stable slug (`pl_paris_eiffel_tower`).
- **Images:** accept `image/jpeg` and `image/png`, max 8 MB (`413` above).
- **Errors:** always `{ "code", "message", "requestId" }`; `code` is a stable
  machine-readable string. Honor `Retry-After` on `429`.

## Validate the contract

```bash
npx @redocly/cli@latest lint contracts/openapi.yaml
```

## Generate code from it

### Frontend (TypeScript — Expo)

```bash
npx openapi-typescript contracts/openapi.yaml -o frontend/src/api/schema.ts
```

This generates types only; wrap them in two small functions built on
`fetch`/`FormData`: `createJob(image, lat, lon)` and `getJob(jobId)`.

### Backend (Python — FastAPI)

FastAPI auto-generates its own OpenAPI. Either generate Pydantic models from the
contract:

```bash
pip install datamodel-code-generator
datamodel-codegen --input contracts/openapi.yaml --input-file-type openapi \
  --output backend/app/models.py
```

Or implement by hand and confirm parity: run FastAPI and compare
`http://127.0.0.1:8000/openapi.json` against `contracts/openapi.yaml`. FastAPI
returns `422` for validation errors — treat it as the `InvalidRequest` case here.

## Versioning

- Contract version lives in `info.version` (semver).
- **Breaking** changes (renamed fields, removed endpoints, changed status codes)
  bump the major version and update the `servers` URL accordingly.
- Non-breaking additions (new optional field) bump minor.

## Environments

The app should read the base URL from config per environment
(`EXPO_PUBLIC_API_URL` for dev). Keep `http://127.0.0.1:8000` for local
development against the Python backend.
