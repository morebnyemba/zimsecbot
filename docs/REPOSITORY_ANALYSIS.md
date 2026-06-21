# Repository Analysis

Analysis of sibling repositories under `morebnyemba` to identify reusable code, patterns, and architecture for the ZIMSEC STEM Revision Platform.

> **Note on access**: `hanna`, `Kali-Safaris`, and `sungrip-chatbot` are public and were analyzed via their GitHub web interface (file browsing + raw file fetch) since this session's GitHub API scope is restricted to `morebnyemba/zimsecbot`. `bubi-rural` is **private** and could not be analyzed — direct repo access (cloning or adding it to this session's GitHub scope) is required to review it.

---

## 1. hanna

**Purpose**: "HANNA" is an Installation Lifecycle Operating System — a CRM managing Solar/Starlink/Custom-Furniture/Hybrid installations end-to-end (sales → install → warranty → service). It is domain-specific to installation/warranty/retail logistics, not conversational tutoring, but has mature WhatsApp + AI plumbing.

**Technologies**: Django + DRF, `djangorestframework-simplejwt`, `django-cors-headers`, `django-filter`, `drf-nested-routers`, Celery + Redis + django-celery-beat/results, Channels + channels-redis + Daphne (WebSockets), `google-genai` (Gemini `gemini-2.5-flash`, used for document extraction not chat), `paynow`, pdf2image/pdfminer.six/Pillow/pytesseract (OCR), django-jazzmin, drf-spectacular, django-prometheus, django-csp, imapclient. PostgreSQL, Docker Compose, Nginx + Let's Encrypt. Two frontends (React/Vite dashboard, Next.js multi-portal).

**Strengths**:
- HMAC-SHA256 webhook signature verification (`meta_integration/views.py`) against `X-Hub-Signature-256`.
- Async-first webhook handling — inbound messages queued to Celery immediately, not processed in the request/response cycle.
- DB-driven config for Meta credentials and AI provider keys (`AIProvider` model, single-active-provider-per-type via `clean()`), enabling key rotation without redeploy.
- Idempotent webhook event logging via `update_or_create` (`WebhookEventLog`) — handles Meta's at-least-once delivery.
- Structured Gemini prompting: forces strict JSON output schema with `parse_json_robustly()` and `validate_gemini_response_structure()` — defensive against LLM output drift.
- Clean app separation: `meta_integration` (transport), `conversations` (persistence + WebSocket consumers), `flows` (workflow engine), `ai_integration` (provider credentials), `users` (auth/roles).

**Weaknesses**:
- `ai_integration/views.py` is empty boilerplate; actual Gemini usage lives in `email_integration/tasks.py` — AI app is underdeveloped/misplaced.
- API key stored as plain `CharField` with a comment admitting it should be encrypted (django-cryptography / Vault) — not yet done.
- Signature verification is explicitly bypassed (with logging) when app secrets are unconfigured — a footgun if misdeployed.
- Many one-off shell scripts at repo root for SSL/migration fixes — signals recurring ops pain rather than fixed-by-design infra.
- No RAG/vector store/conversation-memory system — Gemini usage is single-shot document extraction, not multi-turn chat. **No AI tutor/conversation-memory pattern to lift directly.**

**Reusable Components**:
- `meta_integration/utils.py` — `send_whatsapp_message()`, `send_read_receipt_api()`, `download_whatsapp_media()`, payload builders for text/interactive-button/interactive-list messages. Directly portable WhatsApp Cloud API client.
- `meta_integration/views.py` — webhook signature verification (`_verify_signature`) + Celery-dispatch-on-receipt pattern.
- `ai_integration/models.py` — `AIProvider`/`AIProviderManager` (DB-stored key, single-active-per-type, rate-limit tracking fields).
- `email_integration/tasks.py` — the actual Gemini call pattern: `genai.Client(api_key=...)`, `client.models.generate_content(...)`, strict-JSON prompting + defensive parsing/validation.
- `users/` — JWT auth (simplejwt), WhatsApp-delivered password reset, role-based permissions (`IsAdminUser`, `IsRetailer`, etc.).
- `conversations/consumers.py` + `routing.py` — working Channels/WebSocket pattern for live conversation updates to an admin dashboard.

**Recommended Integrations**:
1. Port `meta_integration/utils.py` wholesale as the WhatsApp Cloud API client layer.
2. Reuse the webhook skeleton (signature verification + Celery dispatch) so the webhook never blocks on slow Gemini calls.
3. Adopt the `AIProvider` DB-config model for the Gemini key, **fixing the known weakness** by encrypting the key at rest.
4. Reuse the strict-JSON-prompt + defensive-parsing pattern for structured AI Tutor outputs (e.g. grading rubrics, topic classification) — build multi-turn memory fresh, since hanna has none.
5. Reuse JWT + role-permission pattern for the admin/teacher dashboard.

---

## 2. Kali-Safaris

**Purpose**: A WhatsApp-based CRM for a safari/tourism business (`whatsapp-crm-backend` + React frontend), automating customer interactions, bookings/inquiries, and notifications via configurable conversational flows, with AI (Gemini) and payment (Paynow) add-ons.

**Technologies**: Django + DRF, PostgreSQL/SQLite, Celery + Redis (4 queues: `celery`, `flow`, `message_sending`, `cpu_heavy`), Django Channels/Daphne, `djangorestframework-simplejwt`, `django-jazzmin`, `google-genai`, `paynow`, Jinja2 templating, pdf2image/pytesseract/pdfminer.six (OCR/PDF), `drf-spectacular`, `django-prometheus`, `django-csp`. React+Vite frontend, Docker Compose, Nginx.

**Strengths**:
- Mature **state-machine flow engine** (`flows/services.py`, `flows/models.py`, `flows/schemas.py`) — `Flow`/`FlowStep`/`FlowTransition`/`ContactFlowState` model multi-step conversations with Pydantic-validated step configs and Jinja2-templated dynamic content (custom filters like `strftime`, `to_interactive_rows`).
- DB-driven Meta credentials (`MetaAppConfig`) instead of env vars, with `get_active_meta_config_for_sending()` guarding against zero/multiple active configs.
- Celery task routing by workload type (I/O vs flow logic vs message sending vs CPU-heavy AI/media), with `transaction.on_commit()` wrapping task dispatch to avoid races.
- Pluggable AI provider model (`AIProvider`/`AIProviderManager`) designed for future multi-provider support beyond Gemini.
- Webhook event logging (`WhatsAppWebhookEventLog`) for auditability/replay.

**Weaknesses**:
- Multiple committed `.env*` files and `db.sqlite3` checked into the repo — real secret-leak risk.
- A loose top-level test file outside any app's `tests.py` — ad hoc testing rather than a consistent structure.
- `MIGRATION_FIX_README.md` / `VERIFICATION_GUIDE.md` at root hint at past migration/data-integrity firefighting.
- App sprawl: 15 Django apps including narrow ones (`cbz_integration`, `omari_integration`, `paynow_integration`) — could indicate insufficient abstraction (one app per payment provider instead of a unified payments interface).
- README marks catalog/payment integration "(Planned)" despite the apps existing — docs out of sync with code.

**Reusable Components**:
1. `meta_integration/utils.py` — near-complete WhatsApp Cloud API client (send, read receipts, media download, interactive payload builders).
2. `MetaAppConfig` pattern — DB-stored, admin-editable API credentials with active-config enforcement.
3. `flows/` engine — directly adaptable to a "study plan" or "quiz session" conversational flow; an existing `question` step type already collects/validates user replies, useful for quiz answers.
4. `AIProvider` model with rate-limit tracking fields — useful for managing Gemini quota.
5. `notifications` app (`NotificationTemplate`, `queue_notifications_to_users()`) — reusable for revision reminders.
6. JWT auth + Jazzmin admin setup.
7. Celery queue topology (`flow`, `message_sending`, `cpu_heavy`) — maps directly to ZIMSEC needs (tutoring flow state, Gemini calls, WhatsApp delivery).

**Recommended Integrations**:
- Port `meta_integration/utils.py` and `MetaAppConfig` wholesale as the WhatsApp layer.
- Adapt the `flows` state machine to drive AI-tutor conversation and quiz/study-plan logic.
- Reuse `AIProvider` for Gemini key management; pull the actual `ai_integration/utils.py` Gemini wrapper before reuse (not fully retrievable via web fetch — get it from a real clone).
- Reuse the Celery queue separation and notification dispatch pattern for spaced-repetition/exam-countdown nudges.
- **Before reuse**: scrub committed `.env*`/`db.sqlite3` files; don't replicate that mistake in the new repo.

---

## 3. sungrip-chatbot

**Purpose**: A Django + DRF backend (with React frontend) powering a WhatsApp-based customer service/sales bot for "Sungrip Solar Energy Company" — quotes, product catalog, orders, GPS-tracked installations, role-based staff access. Not an AI tutoring system; AI is a planned, unimplemented add-on.

**Technologies**: Django 4.2.28 + DRF 3.14, PostgreSQL, `djangorestframework-simplejwt` + djoser, Celery 5.3 + Redis, Django Channels 4.0 + channels-redis, `google-generativeai==0.3.1` (in requirements only), django-jazzmin, Gunicorn/Daphne/Whitenoise, Docker Compose, Nginx. React 18 frontend.

**Strengths**:
- Clean separation: `meta_integration` (transport), `conversations` (chat/CRM + WebSocket consumers), `flows` (engine), `orders`/`products`/`customers`/`notifications` (domain apps).
- Webhook security done right: HMAC-SHA256 via `hmac.compare_digest`, `@transaction.atomic`, multi-tenant-ready via `phone_number_id`-based config lookup.
- Async-safe design: DB writes commit, then `transaction.on_commit()` queues Celery tasks — avoids races from tasks firing before the row exists.
- Real, reusable flow/state-machine engine (`FlowSession`: current_step, context_data, status) using Jinja2 templating, AST-based condition evaluation, and a `FlowActionRegistry` decorator pattern (`@register_flow_action`) for pluggable actions, explicitly built to avoid circular imports.
- Live WebSocket broadcast to a staff dashboard on each inbound message.

**Weaknesses**:
- **Gemini AI is unused**: the package and an API key setting exist, but a repo-wide search for `generativeai` found zero usages — aspirational/scaffolded only.
- No AI conversation-memory model at all (no embeddings/RAG/context-window storage).
- Two parallel ways to send WhatsApp messages (`services.py` class-based vs `utils.py` function-based) — a mid-refactor duplication/tech-debt smell.
- Flow engine loop capped at 50 iterations as a safety valve, implying past runaway-loop bugs.
- No visible CI/CD, no real test suite beyond stub `tests.py` files.

**Reusable Components**:
- `meta_integration/views.py` (`MetaWebhookAPIView`) — GET verify-token challenge + POST HMAC verification + routing by `phone_number_id`. Directly portable.
- `meta_integration/services.py` (`WhatsAppAPIService`) and `utils.py` — send/receive/media-download wrappers with timeout + logging.
- `conversations/models.py` (Contact, Conversation, Message with status enum pending/sent/delivered/read/failed) — solid base schema for any WhatsApp bot.
- `flows/` engine (FlowSession, schemas, action registry, Jinja2 templating, transition condition types like `user_reply_matches`, `interactive_reply_id_equals`) — generically reusable for menu-driven study flows.
- `jwt_middleware.py` + djoser/simplejwt settings — reusable JWT scaffold.
- Celery + Channels + Redis docker-compose setup as an infra template.

**Recommended Integrations**:
1. Port `MetaWebhookAPIView` + HMAC verification + send helpers wholesale — most mature, directly transferable piece across all three repos.
2. Reuse the Contact/Conversation/Message model shape, but add new models for Gemini (an `AITurn`/`ConversationContext` model storing role, prompt, response, token counts) since none exists here.
3. Don't expect to lift AI code from this repo — build the Gemini tutor fresh, modeled after the `@register_flow_action` pluggable-action pattern so "ask Gemini" becomes one more flow step type.
4. Adopt the flow engine for structured navigation (subject/topic/quiz menus), dropping into free-form Gemini Q&A only for open-ended tutoring — a hybrid flow+LLM design.
5. Reuse JWT/djoser setup and django-jazzmin styling for the admin dashboard.

---

## 4. bubi-rural

**Status**: **Not analyzed** — this repository is private and is not within this session's GitHub access scope (`morebnyemba/zimsecbot` only), and it isn't publicly fetchable over the web. To include it in this analysis, either add `morebnyemba/bubi-rural` to this session's repository scope, or share its structure/key files directly.

---

## Cross-Repository Synthesis

All three analyzed repos converge on a near-identical **WhatsApp Cloud API + Django + Celery + Flow-engine** architecture, independently re-implemented three times with diminishing AI maturity (hanna has the best Gemini patterns but single-shot only; Kali-Safaris has the best flow engine and queue topology; sungrip has the cleanest webhook security but no working AI). This convergence is strong evidence that a **shared, dedicated module** (not a fourth reimplementation) is the right call for ZIMSEC.

**Concrete reuse plan for the ZIMSEC platform**:

| Capability | Best source | Notes |
|---|---|---|
| WhatsApp Cloud API client (send/receive/media) | `Kali-Safaris/meta_integration/utils.py` (most complete) | Cross-checked against hanna/sungrip equivalents |
| Webhook signature verification + async dispatch | `sungrip-chatbot` or `hanna` `meta_integration/views.py` | Use `hmac.compare_digest`; never bypass on missing secret (fix hanna's footgun) |
| DB-driven Meta/AI credential config | `Kali-Safaris` `MetaAppConfig` + `AIProvider` | Encrypt API key fields (fix hanna's plaintext weakness) |
| Conversational flow/state machine | `Kali-Safaris/flows/` or `sungrip-chatbot/flows/` | Adapt for subject→topic→quiz navigation; reuse `@register_flow_action`-style pluggable actions for "ask AI Tutor" as a step type |
| Gemini call pattern (structured JSON output) | `hanna/email_integration/tasks.py` | Reuse `parse_json_robustly`/structure validation; must add multi-turn memory + RAG (none of the three repos have this) |
| Celery queue topology | `Kali-Safaris` (`flow`, `message_sending`, `cpu_heavy`) | Map directly: tutoring-flow queue, WhatsApp-send queue, Gemini/AI queue |
| Notification/reminder dispatch | `Kali-Safaris/notifications/` | For study reminders, streak nudges |
| JWT auth + RBAC | Any of the three (near-identical `simplejwt` setup) | Pair with hanna's role-permission classes |
| Admin UI | `django-jazzmin` (used in all three) | Reuse styling/setup conventions |

**Do not reuse**: committed `.env`/`db.sqlite3` files (Kali-Safaris), plaintext API key storage (hanna), or the duplicated send-message code path (sungrip). The RAG/knowledge-base/conversation-memory layer for the AI Tutor has no precedent in any of the three repos and must be built new — this is the one genuinely novel piece of the platform.
