# API Specification — ZIMSEC STEM Revision Platform

Base URL: `/api/v1/`. All endpoints return JSON. Auth via JWT bearer tokens unless noted public.

## 1. Authentication

| Method | Endpoint | Description | Auth |
|---|---|---|---|
| POST | `/auth/register/` | Create account (email/phone + password) | Public |
| POST | `/auth/login/` | Obtain access + refresh JWT | Public |
| POST | `/auth/refresh/` | Refresh access token | Public (refresh token) |
| POST | `/auth/logout/` | Blacklist refresh token | Authenticated |
| POST | `/auth/password-reset/` | Request reset link/code | Public |
| POST | `/auth/password-reset/confirm/` | Confirm new password | Public (reset token) |

**Request — `POST /auth/login/`**
```json
{ "email": "student@example.com", "password": "********" }
```
**Response — 200**
```json
{ "access": "<jwt>", "refresh": "<jwt>", "user": { "id": "uuid", "role": "student" } }
```
**Errors**: `400` validation, `401` invalid credentials, `429` rate-limited.

## 2. Profile & Subjects

| Method | Endpoint | Description |
|---|---|---|
| GET | `/profile/me/` | Current student profile |
| PATCH | `/profile/me/` | Update profile (level, exam year, school) |
| GET | `/subjects/` | List subjects (filter: `tier`, `level`, `is_active`) |
| GET | `/subjects/{id}/topics/` | List topics for a subject |
| GET | `/topics/{id}/subtopics/` | List subtopics |
| POST | `/profile/me/subjects/` | Select subjects for the student |
| DELETE | `/profile/me/subjects/{subject_id}/` | Remove a selected subject |

## 3. Past Papers

| Method | Endpoint | Description |
|---|---|---|
| GET | `/papers/` | List/search/filter papers (`subject`, `year`, `paper_type`, `session`) |
| GET | `/papers/{id}/` | Paper detail incl. marking scheme link |
| GET | `/papers/{id}/download/` | Signed download URL |

**Response — `GET /papers/?subject=physics&year=2023`**
```json
{
  "count": 4,
  "results": [
    {
      "id": "uuid", "subject": "Physics", "year": 2023, "session": "June",
      "paper_number": 1, "paper_type": "Multiple Choice",
      "file_url": "https://.../paper.pdf",
      "marking_scheme": { "id": "uuid", "file_url": "https://.../scheme.pdf" }
    }
  ]
}
```

## 4. Revision Notes

| Method | Endpoint | Description |
|---|---|---|
| GET | `/notes/` | Search/filter notes (`subject`, `topic`, `subtopic`, `q`) |
| GET | `/notes/{id}/` | Note detail (content, diagrams, images) |

## 5. Question Bank & Quizzes

| Method | Endpoint | Description |
|---|---|---|
| GET | `/questions/` | Browse questions (admin/content use; filter by subject/topic/difficulty/type) |
| POST | `/quizzes/generate/` | Generate a quiz (subject, topic, difficulty, count) |
| GET | `/quizzes/{id}/` | Quiz detail (questions, no answers exposed until submitted) |
| POST | `/quizzes/{id}/attempts/` | Submit answers for grading |
| GET | `/quizzes/attempts/{id}/` | Attempt result (score, per-question correctness, explanations) |
| GET | `/quizzes/attempts/` | List my past attempts |

**Request — `POST /quizzes/generate/`**
```json
{ "subject_id": "uuid", "topic_id": "uuid", "difficulty": "medium", "question_count": 10 }
```
**Request — `POST /quizzes/{id}/attempts/`**
```json
{ "answers": [ { "question_id": "uuid", "student_answer": "B" } ] }
```
**Response — 201**
```json
{
  "id": "uuid", "score": 80.0, "total_marks": 10, "marks_awarded": 8,
  "answers": [ { "question_id": "uuid", "is_correct": true, "explanation": "..." } ]
}
```

## 6. Study Plans

| Method | Endpoint | Description |
|---|---|---|
| POST | `/study-plans/` | Generate a study plan (exam date, subjects) |
| GET | `/study-plans/active/` | Current active plan with sessions |
| PATCH | `/study-plans/sessions/{id}/` | Mark a session done/skipped |
| GET | `/study-plans/{id}/progress/` | Completion percentage, streak |

## 7. Analytics

| Method | Endpoint | Description |
|---|---|---|
| GET | `/analytics/overview/` | Subject performance summary |
| GET | `/analytics/topics/weak/` | Weak topics (below threshold accuracy) |
| GET | `/analytics/trends/` | Score trend over time (chart-ready series) |
| GET | `/analytics/streaks/` | Current/longest study streak |

## 7a. Billing & Gating (see MONETIZATION.md §7 for full detail)

| Method | Endpoint | Description |
|---|---|---|
| GET | `/billing/plans/` | List active plans (public) |
| GET | `/billing/subscription/` | Current user's subscription + entitlements |
| POST | `/billing/subscribe/` | Start a subscription/payment for a plan |
| POST | `/billing/webhook/paynow/` | Paynow payment confirmation webhook (signature-verified, not JWT) |
| POST | `/billing/cancel/` | Cancel auto-renew |
| GET | `/billing/usage/` | Current usage vs. quota for gated features |
| POST | `/schools/` | Create a school (institutional onboarding, admin-only) |
| POST | `/schools/{id}/seats/` | Assign/revoke a student seat |
| GET | `/schools/{id}/analytics/` | Class-level performance analytics (School tier) |

Any endpoint can be feature-gated by plan/quota (e.g. `/papers/{id}/download/`, `/ai-tutor/sessions/{id}/messages/`). A blocked request returns `402`-style error with an `upgrade_url`:
```json
{ "error": { "code": "feature_locked", "message": "Daily AI Tutor limit reached on Free plan", "upgrade_url": "/billing/plans/" } }
```

## 8. AI Tutor

| Method | Endpoint | Description |
|---|---|---|
| POST | `/ai-tutor/sessions/` | Start a tutor session |
| POST | `/ai-tutor/sessions/{id}/messages/` | Send a message, get tutor reply (RAG-grounded) |
| GET | `/ai-tutor/sessions/{id}/` | Session history |
| POST | `/ai-tutor/sessions/{id}/end/` | End session (triggers memory summarization) |

**Request — `POST /ai-tutor/sessions/{id}/messages/`**
```json
{ "message": "Explain how to balance this chemical equation: Fe + O2 -> Fe2O3" }
```
**Response — 200**
```json
{
  "reply": "Step 1: ... Step 2: ...",
  "sources": [ { "type": "note", "id": "uuid", "title": "Balancing Equations" } ],
  "confidence": "high"
}
```

## 9. WhatsApp Webhook (internal, Meta-facing)

| Method | Endpoint | Description |
|---|---|---|
| GET | `/whatsapp/webhook/` | Meta verification challenge |
| POST | `/whatsapp/webhook/` | Inbound message/event delivery |

Not part of the public API surface; secured via Meta app secret + HMAC signature, not JWT.

## 10. Admin / Content Management

| Method | Endpoint | Description |
|---|---|---|
| POST/PATCH/DELETE | `/admin/subjects/`, `/admin/topics/`, `/admin/papers/`, `/admin/notes/`, `/admin/questions/` | CRUD for content, `content_admin`/`superadmin` only |
| GET | `/admin/analytics/platform/` | Platform-wide usage metrics |
| GET | `/admin/audit-logs/` | Audit trail, `superadmin` only |

## 11. Authentication & Permissions

- All non-public endpoints require `Authorization: Bearer <access_token>`.
- Roles: `student` (default), `content_admin`, `superadmin`, `support`, `school_admin`. Enforced via DRF permission classes per viewset.
- Object-level permissions: students can only read/write their own `QuizAttempt`, `StudyPlan`, `AISession`, profile, `Subscription`.
- Plan/quota permissions: gated endpoints additionally run the shared `AccessGate` permission class (see `MONETIZATION.md` §4) on top of role/object checks.

## 12. Error Handling

Standard error envelope:
```json
{ "error": { "code": "validation_error", "message": "...", "details": { "field": ["..."] } } }
```

| Status | Meaning |
|---|---|
| 400 | Validation error |
| 401 | Missing/invalid/expired token |
| 402 | Feature/quota locked by current plan (`feature_locked`, see `MONETIZATION.md`) |
| 403 | Authenticated but not permitted (role/object ownership) |
| 404 | Resource not found |
| 429 | Rate limited (per-user or per-IP, DRF throttling) |
| 500 | Unhandled server error (logged, generic message returned) |

## 13. Rate Limiting

- Auth endpoints: stricter throttle (e.g. 5/min per IP) to deter brute force.
- AI Tutor endpoints: per-user throttle tied to Gemini quota/cost (e.g. 20/min, configurable).
- General API: standard per-user throttle (e.g. 100/min).

## 14. Documentation Tooling

API schema generated via `drf-spectacular` → OpenAPI 3 → Swagger UI at `/api/docs/`, kept in sync with code (no hand-maintained Postman collections).
