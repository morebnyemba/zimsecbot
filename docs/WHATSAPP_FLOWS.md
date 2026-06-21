# WhatsApp Assistant — Conversation Flows

All flows are driven by a DB-backed state machine (`whatsapp.ConversationState`: current flow, current step, context JSON), modeled after the `flows`/`FlowSession` pattern found in `Kali-Safaris` and `sungrip-chatbot` (see `REPOSITORY_ANALYSIS.md`). Every flow ultimately calls the same backend services used by the web API — WhatsApp is just another channel.

## 1. Main Menu Flow

```mermaid
flowchart TD
    START([User messages bot]) --> CHECK{Registered?}
    CHECK -- No --> REG[Collect name + link/create account]
    REG --> MENU
    CHECK -- Yes --> MENU[Send Main Menu]
    MENU --> M1[1. Past Papers]
    MENU --> M2[2. Revision Notes]
    MENU --> M3[3. Practice Quiz]
    MENU --> M4[4. Ask AI Tutor]
    MENU --> M5[5. Study Plan]
    MENU --> M6[6. My Progress]
    M1 --> PAST_PAPER_FLOW[[Past Paper Flow]]
    M2 --> REVISION_FLOW[[Revision Flow]]
    M3 --> QUIZ_FLOW[[Quiz Flow]]
    M4 --> AI_TUTOR_FLOW[[AI Tutor Flow]]
    M5 --> STUDY_PLAN[[Study Plan Flow]]
    M6 --> PROGRESS_FLOW[[Progress Flow]]
    PAST_PAPER_FLOW --> MENU
    REVISION_FLOW --> MENU
    QUIZ_FLOW --> MENU
    AI_TUTOR_FLOW --> MENU
    STUDY_PLAN --> MENU
    PROGRESS_FLOW --> MENU
```

## 2. Past Paper Flow

```mermaid
flowchart TD
    A[Select: Past Papers] --> B[Choose Level: O-Level / A-Level]
    B --> C[Choose Subject - list message]
    C --> D[Choose Year - list message]
    D --> E{Papers found?}
    E -- Yes --> F[Send paper as document + marking scheme link]
    E -- No --> G[No papers found, suggest nearby years]
    F --> H{Another paper?}
    H -- Yes --> C
    H -- No --> RETURN[Return to Main Menu]
    G --> RETURN
```

## 3. Revision Flow

```mermaid
flowchart TD
    A[Select: Revision Notes] --> B[Choose Subject]
    B --> C[Choose Topic - list message]
    C --> D{Has subtopics?}
    D -- Yes --> E[Choose Subtopic]
    D -- No --> F[Send Note content]
    E --> F
    F --> G[Send diagrams/images if any]
    G --> H{More on this topic / another topic?}
    H -- Topic --> C
    H -- Done --> RETURN[Return to Main Menu]
```

## 4. Quiz Flow

```mermaid
flowchart TD
    A[Select: Practice Quiz] --> B[Choose Subject]
    B --> C[Choose Topic or 'Whole Subject']
    C --> D[Choose Difficulty: Easy/Medium/Hard]
    D --> E[Generate quiz via Quiz Service]
    E --> F[Send Question 1 - interactive buttons/list for MCQ]
    F --> G[Receive answer]
    G --> H[Mark instantly, send correctness + explanation]
    H --> I{More questions?}
    I -- Yes --> F
    I -- No --> J[Send final score + weak areas]
    J --> K[Trigger async analytics update]
    K --> RETURN[Return to Main Menu]
```

## 5. AI Tutor Flow

```mermaid
flowchart TD
    A[Select: Ask AI Tutor] --> B[Prompt: 'Ask me anything STEM']
    B --> C[Receive free-text question]
    C --> D[Enqueue to AI Tutor Service - async, Celery cpu_heavy queue]
    D --> E[RAG retrieval against Knowledge Base]
    E --> F[Gemini generates grounded response]
    F --> G[Send step-by-step answer + source note if available]
    G --> H{Follow-up question?}
    H -- Yes --> C
    H -- No --> I[Summarize session into AISession memory]
    I --> RETURN[Return to Main Menu]
```

**Note**: because Gemini calls are slow, the webhook ACKs Meta immediately and the reply is sent as a follow-up outbound message once generation completes (matches the async-dispatch pattern used in all three reference repos).

## 6. Study Plan Flow

```mermaid
flowchart TD
    A[Select: Study Plan] --> B{Existing active plan?}
    B -- Yes --> C[Show today's goal + completion status]
    B -- No --> D[Ask exam date + subjects to prioritize]
    D --> E[Generate plan via Study Plan Service]
    E --> C
    C --> F{Mark today's session done?}
    F -- Yes --> G[Update StudySession status]
    F -- No --> RETURN[Return to Main Menu]
    G --> RETURN
```

Daily goals are also pushed **proactively** via a Celery Beat task (opt-in reminder) rather than only on-demand.

## 7. Progress Flow

```mermaid
flowchart TD
    A[Select: My Progress] --> B[Fetch AnalyticsRecord summary]
    B --> C[Send: overall performance, streak]
    C --> D[Send: weak topics list]
    D --> E[Send: recommended revision plan/CTA]
    E --> RETURN[Return to Main Menu]
```

## 8. Cross-Cutting Behavior

- **Timeout/abandonment**: if no reply within N minutes mid-flow, state resets to Main Menu on next message (context preserved for resumption where sensible, e.g. quiz progress saved).
- **Global commands**: `menu`/`0` always returns to Main Menu from any step; `help` sends usage instructions.
- **Media**: papers/marking schemes sent as WhatsApp `document` messages; notes' diagrams sent as `image` messages; quiz MCQs use `interactive list/button` messages where option count allows (≤3 buttons / ≤10 list items per Meta limits), falling back to numbered text for larger option sets.
- **Idempotency**: inbound webhook events are deduplicated by Meta `message_id` before flow processing (per the `WebhookEventLog`/`update_or_create` pattern from `hanna`/`Kali-Safaris`).
