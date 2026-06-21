# Database Design — ZIMSEC STEM Revision Platform

PostgreSQL is the system of record. `pgvector` extension is used for embeddings (no separate vector DB needed at launch scale).

## 1. Entity Relationship Diagram

```mermaid
erDiagram
    USER ||--o| STUDENT_PROFILE : has
    USER ||--o{ AUDIT_LOG : performs
    USER }o--o{ SUBJECT : "selects (via StudentSubject)"
    SUBJECT ||--o{ TOPIC : has
    TOPIC ||--o{ SUBTOPIC : has
    SUBJECT ||--o{ PAST_PAPER : has
    PAST_PAPER ||--o| MARKING_SCHEME : has
    SUBJECT ||--o{ NOTE : has
    TOPIC ||--o{ NOTE : has
    SUBTOPIC ||--o{ NOTE : has
    SUBJECT ||--o{ QUESTION : has
    TOPIC ||--o{ QUESTION : has
    USER ||--o{ QUIZ : generates
    SUBJECT ||--o{ QUIZ : scoped_by
    QUIZ ||--o{ QUIZ_QUESTION : contains
    QUESTION ||--o{ QUIZ_QUESTION : referenced_by
    USER ||--o{ QUIZ_ATTEMPT : attempts
    QUIZ ||--o{ QUIZ_ATTEMPT : has
    QUIZ_ATTEMPT ||--o{ QUIZ_ANSWER : contains
    QUESTION ||--o{ QUIZ_ANSWER : answered_in
    USER ||--o{ STUDY_PLAN : owns
    STUDY_PLAN ||--o{ STUDY_SESSION : contains
    SUBJECT ||--o{ STUDY_SESSION : scoped_by
    TOPIC ||--o{ STUDY_SESSION : scoped_by
    USER ||--o{ CONVERSATION : participates
    CONVERSATION ||--o{ MESSAGE : contains
    USER ||--o{ AI_SESSION : owns
    AI_SESSION ||--o{ MESSAGE : contains
    KNOWLEDGE_DOCUMENT ||--o{ EMBEDDING : chunked_into
    SUBJECT ||--o{ KNOWLEDGE_DOCUMENT : tagged_by
    USER ||--o{ ANALYTICS_RECORD : measured_for
    SUBJECT ||--o{ ANALYTICS_RECORD : scoped_by
    TOPIC ||--o{ ANALYTICS_RECORD : scoped_by

    USER {
        uuid id PK
        string email
        string phone_number
        string password_hash
        string role
        bool is_active
        datetime date_joined
    }
    STUDENT_PROFILE {
        uuid id PK
        uuid user_id FK
        string level
        string exam_year
        string school
        jsonb preferences
    }
    SUBJECT {
        uuid id PK
        string name
        string code
        string tier
        string level
        bool is_active
    }
    TOPIC {
        uuid id PK
        uuid subject_id FK
        string name
        int order
    }
    SUBTOPIC {
        uuid id PK
        uuid topic_id FK
        string name
        int order
    }
    PAST_PAPER {
        uuid id PK
        uuid subject_id FK
        int year
        string session
        string paper_number
        string paper_type
        string file_url
        uuid marking_scheme_id FK
    }
    MARKING_SCHEME {
        uuid id PK
        string file_url
    }
    NOTE {
        uuid id PK
        uuid subject_id FK
        uuid topic_id FK
        uuid subtopic_id FK
        string title
        text content
        jsonb media
    }
    QUESTION {
        uuid id PK
        uuid subject_id FK
        uuid topic_id FK
        string question_type
        string difficulty
        text question_text
        jsonb options
        text answer
        text explanation
        int marks
    }
    QUIZ {
        uuid id PK
        uuid created_by_id FK
        uuid subject_id FK
        uuid topic_id FK
        string difficulty
        string source_channel
        datetime created_at
    }
    QUIZ_QUESTION {
        uuid id PK
        uuid quiz_id FK
        uuid question_id FK
        int order
    }
    QUIZ_ATTEMPT {
        uuid id PK
        uuid quiz_id FK
        uuid user_id FK
        float score
        datetime started_at
        datetime completed_at
    }
    QUIZ_ANSWER {
        uuid id PK
        uuid attempt_id FK
        uuid question_id FK
        text student_answer
        bool is_correct
        int marks_awarded
    }
    STUDY_PLAN {
        uuid id PK
        uuid user_id FK
        date start_date
        date exam_date
        string status
    }
    STUDY_SESSION {
        uuid id PK
        uuid study_plan_id FK
        uuid subject_id FK
        uuid topic_id FK
        date scheduled_date
        string status
    }
    CONVERSATION {
        uuid id PK
        uuid user_id FK
        string channel
        datetime started_at
    }
    MESSAGE {
        uuid id PK
        uuid conversation_id FK
        uuid ai_session_id FK
        string sender
        text content
        jsonb metadata
        datetime created_at
    }
    AI_SESSION {
        uuid id PK
        uuid user_id FK
        string channel
        jsonb memory_summary
        datetime last_active_at
    }
    KNOWLEDGE_DOCUMENT {
        uuid id PK
        uuid subject_id FK
        string source_type
        string title
        string file_url
        datetime ingested_at
    }
    EMBEDDING {
        uuid id PK
        uuid document_id FK
        text chunk_text
        vector embedding
        int chunk_index
    }
    ANALYTICS_RECORD {
        uuid id PK
        uuid user_id FK
        uuid subject_id FK
        uuid topic_id FK
        string metric
        float value
        date recorded_date
    }
    AUDIT_LOG {
        uuid id PK
        uuid user_id FK
        string action
        jsonb metadata
        datetime created_at
    }
```

## 2. Model Notes

- **User / StudentProfile**: `User` is the auth model (email or phone login, JWT). `StudentProfile` is 1:1, holds level (O-Level/A-Level), exam year, school. `role` field drives RBAC (`student`, `content_admin`, `superadmin`, `support`).
- **Subject / Topic / Subtopic**: pure data — `tier` (1/2/3) and `is_active` let new subjects go live without a deploy. This is the mechanism satisfying "add subjects without code changes."
- **PastPaper / MarkingScheme**: files stored in object storage; DB holds metadata + URL/key. Indexed on `(subject_id, year, paper_type)` for fast filtering.
- **Note**: supports topic or subtopic granularity (both FKs nullable, at least one required — enforced at the service layer). `media` is a JSON list of image/diagram URLs.
- **Question**: `question_type` enum (`mcq`, `structured`, `essay`, `practical`); `options` JSON for MCQ; `answer`/`explanation` always present for instant marking.
- **Quiz / QuizQuestion / QuizAttempt / QuizAnswer**: `Quiz` is a generated instance (ephemeral definition); `QuizAttempt` is the scored run. Denormalized `score` on attempt for fast leaderboards/analytics; `QuizAnswer` rows are the source of truth for per-question correctness used by weak-topic detection.
- **StudyPlan / StudySession**: plan is the container (start date → exam date); sessions are daily/topic-scoped goals with `status` (`pending`, `done`, `skipped`).
- **Conversation / Message**: channel-agnostic (`web`, `whatsapp`) chat log, shared by AI Tutor and (optionally) human support.
- **AISession**: holds the *summarized* long-term memory (`memory_summary` JSON) per user+channel so prompts don't replay full history; `Message` rows with `ai_session_id` set are the AI Tutor's turn-by-turn record, distinct from generic `Conversation` messages if needed, or unified — final call left to implementation, modeled here as compatible with either.
- **KnowledgeDocument / Embedding**: ingestion pipeline writes one `KnowledgeDocument` per source file (past paper, marking scheme, note, curriculum doc) and N `Embedding` chunks (pgvector `vector` column) per document for RAG retrieval.
- **AnalyticsRecord**: one row per (user, subject, topic, metric, date) — e.g. `metric='topic_accuracy'`. Aggregated by Celery Beat tasks rather than computed on read, for dashboard performance.
- **AuditLog**: append-only, indexed on `(user_id, created_at)` and `action`.

## 3. Indexing Strategy

| Table | Index | Reason |
|---|---|---|
| `past_paper` | `(subject_id, year, paper_type)` | Browse/filter by subject+year is the primary access pattern |
| `note` | `(subject_id, topic_id, subtopic_id)` | Topic navigation |
| `question` | `(subject_id, topic_id, difficulty, question_type)` | Quiz generation query |
| `quiz_attempt` | `(user_id, quiz_id)`, `(user_id, completed_at)` | Progress/history lookups |
| `analytics_record` | `(user_id, subject_id, topic_id, recorded_date)` | Dashboard + weak-topic queries |
| `message` | `(conversation_id, created_at)`, `(ai_session_id, created_at)` | Chat history pagination |
| `embedding` | pgvector HNSW/IVFFlat index on `embedding` | Similarity search for RAG |
| `audit_log` | `(user_id, created_at)` | Compliance queries |

All FK columns get a btree index by default (Django auto-creates these); the table above lists *additional* composite indexes.

## 4. Scaling Considerations

- **Read-heavy tables** (`subject`, `topic`, `subtopic`, `question`, `note`) are small relative to write-heavy ones (`message`, `quiz_attempt`, `analytics_record`) — cache the former in Redis, let the latter scale on Postgres directly with partitioning by date considered post-launch (`message`, `analytics_record`) if volume warrants.
- **Embeddings**: pgvector is sufficient through tens of millions of chunks with HNSW indexing; migrate to a dedicated vector DB (e.g. Qdrant/pgvector-scale) only if RAG latency becomes a bottleneck at scale.
- **Connection pooling** via pgbouncer once Celery workers + Gunicorn workers exceed Postgres `max_connections` comfortably.
- **Soft deletes / archiving**: `quiz_attempt`, `message`, `audit_log` should support archiving older rows to cold storage once retention policy is defined, rather than unbounded growth.
