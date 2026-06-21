# Roadmap — ZIMSEC STEM Revision Platform

## Phase 1 — Foundation

**Deliverables**:
- Repo scaffolding: Django project + modular app structure (`accounts`, `subjects`, `papers`, `notes`, `questions`, `quizzes`, `study_plans`, `analytics`, `ai_tutor`, `knowledge_base`, `whatsapp`, `conversations`, `files`, `audit`).
- Docker Compose for local dev (Postgres + pgvector, Redis, Django, Celery, Celery Beat).
- Base settings (env-driven config, no hardcoded secrets), CI skeleton (GitHub Actions: lint, test).
- Core shared models: `User`, `StudentProfile`, base audit/timestamp mixins.

**Dependencies**: None (first phase).
**Risks**: Under-designing the modular boundaries now causes rework later — mitigate by following the service-layer pattern in `ARCHITECTURE.md` from day one.
**Estimated Effort**: 1–1.5 weeks.

---

## Phase 2 — Core Backend

**Deliverables**:
- Subjects/Topics/Subtopics CRUD + data-driven tier system.
- Past Papers + Marking Schemes models, storage integration (object storage), search/filter API.
- Revision Notes models + API.
- Question Bank models (MCQ/structured/essay/practical) + API.
- Quiz Engine: generation, attempt submission, instant marking, scoring.
- JWT auth, RBAC roles, DRF throttling.
- API documentation via `drf-spectacular`.

**Dependencies**: Phase 1 scaffolding.
**Risks**: Quiz generation query performance at scale (mitigate with the indexing strategy in `DATABASE.md`); file upload security (validate MIME/size, scan if feasible).
**Estimated Effort**: 3–4 weeks.

---

## Phase 3 — Admin Portal

**Deliverables**:
- Next.js admin portal (content_admin/superadmin): manage subjects/topics/papers/notes/questions.
- Audit log viewer.
- Platform-wide analytics dashboard (basic).
- Reuse `django-jazzmin`-style conventions and JWT/role patterns identified in `REPOSITORY_ANALYSIS.md` for the Django admin as an interim/secondary tool.

**Dependencies**: Phase 2 APIs.
**Risks**: Scope creep into full BI tooling — keep to operational content management for launch.
**Estimated Effort**: 2 weeks.

---

## Phase 4 — Student Portal

**Deliverables**:
- Next.js student web app: registration/login/profile, subject selection, past paper browsing/download, revision notes browsing, quiz interface, progress dashboard.
- Mobile-responsive, accessible UI (ShadCN UI + Tailwind).

**Dependencies**: Phase 2 APIs.
**Risks**: Performance on low-end devices/slow connections common among target users — prioritize lightweight pages, lazy-loaded media.
**Estimated Effort**: 3–4 weeks (can partially overlap Phase 3).

---

## Phase 5 — WhatsApp Integration

**Deliverables**:
- WhatsApp Cloud API client (ported/adapted from `Kali-Safaris`/`hanna`/`sungrip-chatbot` per `REPOSITORY_ANALYSIS.md`).
- Webhook endpoint with signature verification + async Celery dispatch.
- Conversation state machine (flow engine) driving Main Menu, Past Paper, Revision, Quiz, Study Plan, Progress flows per `WHATSAPP_FLOWS.md`.
- Reuses Phase 2 services — no duplicated business logic.

**Dependencies**: Phase 2 (services to call), Meta WhatsApp Business app approval/setup.
**Risks**: Meta approval/review delays (external dependency, start early); message-template approval for proactive notifications; rate limits from Meta.
**Estimated Effort**: 3 weeks.

---

## Phase 6 — AI Tutor

**Deliverables**:
- Knowledge base ingestion pipeline (PDF/text extraction, chunking, embeddings via pgvector).
- RAG retrieval service.
- Gemini integration (`AIProvider` model, encrypted key storage, structured-output parsing — per `AI_ARCHITECTURE.md`).
- AI Tutor agent: intent classification + tool calling (knowledge search, quiz generation, study plan generation, step-by-step solving).
- Memory: short-term session + long-term summarization.
- Hallucination guardrails: source citation, confidence/uncertainty handling, scope restriction.
- AI Tutor available on both web and WhatsApp channels.

**Dependencies**: Phase 2 (content to ingest), Phase 5 (WhatsApp channel for tutor access) — web-channel tutor can ship before WhatsApp if sequencing requires.
**Risks**: This is the highest-novelty component (no precedent in sibling repos) — budget extra time for prompt iteration and hallucination testing; Gemini cost/quota management.
**Estimated Effort**: 4–5 weeks.

---

## Phase 7 — Analytics

**Deliverables**:
- Performance tracking: subject/topic accuracy, quiz scores, study streaks, improvement trends.
- Weak-topic detection (threshold-based, computed via Celery Beat aggregation).
- Automated recommendations (e.g. "revise Topic X" surfaced on dashboard + WhatsApp Progress flow).
- Student-facing analytics dashboard (web) + Progress flow (WhatsApp).

**Dependencies**: Phase 2 (quiz attempts), Phase 4/5 (surfaces to display in).
**Risks**: Aggregation job cost at scale — pre-aggregate via scheduled tasks rather than on-demand queries.
**Estimated Effort**: 2 weeks.

---

## Phase 7.5 — Monetization & Gating

See `MONETIZATION.md` for full detail.

**Deliverables**:
- `billing` app: `Plan`, `Subscription`, `Payment`, `UsageRecord` models; `schools` app: `School`, `SchoolSeat`.
- Shared `AccessGate` service + DRF permission class, wired into gated web API endpoints (AI Tutor, paper downloads, quiz quotas).
- WhatsApp gating action (flow-guard) + upgrade flow (plan selection → Paynow mobile money push → webhook confirmation).
- Paynow integration (reusing the pattern from `hanna`/`Kali-Safaris` per `REPOSITORY_ANALYSIS.md`), with encrypted credential storage.
- Admin portal: plan/quota management UI, school onboarding + seat assignment UI.
- Free-tier quotas tuned to remain genuinely useful (acquisition/retention), not crippled.

**Dependencies**: Phase 2 (features to gate), Phase 6 (AI Tutor, the highest-value gated feature), Phase 5 (WhatsApp upgrade flow).
**Risks**: Payment webhook reliability (mitigate with a reconciliation job re-checking pending payments); mobile-money UX friction — validate the WhatsApp upgrade flow with real EcoCash/OneMoney prompts early; pricing sensitivity in market — keep Free tier useful while pricing is validated.
**Estimated Effort**: 2–3 weeks.

---

## Phase 8 — Production Hardening

**Deliverables**:
- Full test suite to ≥80% coverage (unit, integration, API, E2E for critical flows).
- Security review: rate limiting tuning, input validation audit, secure file upload audit, secrets management review, dependency vulnerability scan.
- Performance/load testing for target concurrency (thousands of students).
- Full Docker/Nginx/Coolify deployment configuration, GitHub Actions CI/CD to production.
- Observability: logging, error tracking, basic metrics/alerting.
- Documentation finalization (deployment runbook, on-call basics).

**Dependencies**: All prior phases feature-complete.
**Risks**: Hardening is often under-budgeted — treat as a real phase with its own timeline, not a buffer at the end.
**Estimated Effort**: 2–3 weeks.

---

## Summary Timeline (Sequential Estimate)

| Phase | Effort | Can overlap with |
|---|---|---|
| 1. Foundation | 1–1.5 wks | — |
| 2. Core Backend | 3–4 wks | — |
| 3. Admin Portal | 2 wks | Phase 4 |
| 4. Student Portal | 3–4 wks | Phase 3 |
| 5. WhatsApp Integration | 3 wks | Phase 3/4 (start Meta approval early) |
| 6. AI Tutor | 4–5 wks | Tail of Phase 5 |
| 7. Analytics | 2 wks | Tail of Phase 6 |
| 7.5. Monetization & Gating | 2–3 wks | Tail of Phase 6/7 |
| 8. Production Hardening | 2–3 wks | — |

**Total** (with reasonable overlap): roughly **18–22 weeks** for a single small team to reach production readiness for Tier 1 subjects, before Tier 2/3 subject content expansion (data entry, not engineering work, given the data-driven subject model).
