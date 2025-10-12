# Implementation Plan: WhatsApp Chatbot Boilerplate

**Branch**: `001-create-a-whatsapp` | **Date**: 2025-10-05 | **Spec**: [/specs/001-create-a-whatsapp/spec.md](spec.md)
**Input**: Feature specification from `/specs/001-create-a-whatsapp/spec.md`

## Execution Flow (/plan command scope)
```
1. Confirmed feature spec exists and clarifications resolved (Session 2025-10-05).
2. Extracted Technical Context incorporating user input on FastAPI, Arq, Upstash Redis, whatsapp-python, pydantic-settings, loguru, BetterStack.
3. Evaluated constitution principles, captured gating notes, recorded Initial Constitution Check = PASS.
4. Ran Phase 0 research to document technology, hosting, and configuration decisions in research.md.
5. Completed Phase 1 design artifacts: data-model.md, contracts/webhook.yml, quickstart.md, and updated constitution check (Post-Design = PASS).
6. Described Phase 2 task generation strategy (no tasks.md created per workflow guidance).
7. Updated progress tracking, ensuring NEEDS CLARIFICATION markers closed and no complexity deviations.
8. STOP – ready for `/tasks`.
```

## Summary
Deliver a production-ready WhatsApp chatbot boilerplate that exposes a FastAPI webhook, hands off processing to Arq workers backed by Upstash Redis, and showcases an inventory sales representative conversation flow. The project bundles observability via loguru + BetterStack, configuration through pydantic-settings, Docker-based local/staging environments, and automated unit/integration tests that enforce constitutional quality, UX, and performance guarantees.

## Technical Context
**Language/Version**: Python 3.13 (pinned via uv)  
**Primary Dependencies**: FastAPI, Arq, whatsapp-python, pydantic-settings, loguru, httpx, BetterStack logging exporter  
**Storage**: Upstash Redis (managed) for queues and conversation state; local Redis container for dev/test  
**Testing**: pytest + pytest-asyncio, respx/httpx mocks, VCR fixtures for WhatsApp payloads  
**Target Platform**: Containerized Linux (Docker + Docker Compose, GitHub Actions CI)  
**Project Type**: Single-service backend with async worker (`src/whatsapp_bot`)  
**Performance Goals**: p95 ≤1s and p99 ≤2s webhook-to-response latency for ≤50 concurrent conversations; worker RSS <250MB  
**Constraints**: Must ACK WhatsApp webhooks with HTTP 200 immediately; distinct dev/staging/prod configs (Redis, BetterStack tokens); enforce retry/backoff aligned with WhatsApp limits; engineering lead approves conversation copy  
**Scale/Scope**: Boilerplate targets 50 concurrent sessions with room to scale via worker autoscaling and Upstash tier upgrades

## Constitution Check
*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- [x] **Code Quality Discipline** → Lint/format via `uvx ruff format` + `uvx ruff check`; enforce docstrings and ADR capture; plan references README/runbook updates.
- [x] **Test-Driven Reliability** → Define failing unit/integration tests for webhook, worker retry, inventory flow, consent hooks, BetterStack logging; 90% coverage target documented.
- [x] **Cohesive User Experience** → Quickstart will host approved sales-rep script; localization placeholders mandated; engineering lead sign-off captured.
- [x] **Performance & Resilience Guarantees** → Load validation (Locust/pytest-benchmark) and circuit breaker/backoff strategy outlined; Upstash rate-limit handling included.

## Project Structure

### Documentation (this feature)
```
specs/001-create-a-whatsapp/
├── plan.md              # This file (/plan command output)
├── research.md          # Phase 0 decisions & references
├── data-model.md        # Phase 1 entity schemas & lifecycles
├── quickstart.md        # Conversation script, setup & validation
├── contracts/           # OpenAPI + payload fixtures
└── tasks.md             # Generated later by /tasks (not created here)
```

### Source Code (repository root)
```
src/
└── whatsapp_bot/
    ├── api/
    │   ├── routers/
    │   │   └── webhook.py
    │   └── dependencies.py
    ├── workers/
    │   ├── dispatcher.py
    │   └── handlers.py
    ├── services/
    │   ├── messaging_service.py
    │   ├── inventory_service.py
    │   └── consent_service.py
    ├── schemas/
    │   ├── whatsapp.py
    │   └── conversations.py
    ├── config/
    │   └── settings.py
    └── logging/
        └── betterstack.py

tests/
├── unit/
│   ├── test_settings.py
│   ├── test_inventory_service.py
│   └── test_webhook_router.py
├── integration/
│   ├── test_webhook_flow.py
│   └── test_worker_retry.py
└── contract/
    ├── test_openapi_contract.py
    └── test_whatsapp_examples.py

docker/
├── Dockerfile
├── docker-compose.dev.yml
└── docker-compose.staging.yml

infra/
└── arq/
    └── worker.py
```

**Structure Decision**: Single backend project with dedicated API + worker modules, mirrored test layout, and Docker assets for environment parity.

## Phase 0: Outline & Research
1. Researched FastAPI + Arq integration patterns, Upstash Redis connectivity, consent hook expectations, BetterStack ingestion, and Dockerized uv workflows.
2. Documented retry/backoff defaults, environment configuration separation, and observability instrumentation in `research.md`.
3. Identified ADR requirements and future work for catalog connectors and inventory data sources.

**Output**: [`research.md`](research.md)

## Phase 1: Design & Contracts
*Prerequisite: research.md complete*

1. Captured entities (`BotConfiguration`, `ConversationState`, `InventoryItem`, `MessageTemplate`, `ConsentHook`) in `data-model.md` with fields, validation, persistence, and lifecycle notes.
2. Authored `contracts/webhook.yml` OpenAPI describing `/webhooks/whatsapp` POST, `/healthz` GET, schemas for inbound/outbound payloads, and BetterStack log event shape.
3. Listed integration/contract test scenarios covering webhook ACK, inventory lookup, worker retry, consent hook dispatch, and logging fan-out.
4. Drafted `quickstart.md` to guide engineers through uv environment setup, Docker Compose orchestration (dev vs staging), configuration of WhatsApp sandbox credentials, and manual conversation verification steps.
5. Re-ran constitution check → PASS; agent context update deferred until code exists.

**Outputs**: [`data-model.md`](data-model.md), [`contracts/webhook.yml`](contracts/webhook.yml), [`quickstart.md`](quickstart.md)

## Phase 2: Task Planning Approach
*(Executed later by `/tasks`; approach captured here.)*

**Task Generation Strategy**:
- Derive setup, contract, integration, implementation, UX, performance, and observability tasks directly from plan artifacts.
- Require failing tests for webhook routing, worker retry, consent hook, inventory service, BetterStack logging, Docker configuration, and load validation prior to implementation.
- Include UX validation tasks ensuring engineering-lead sign-off on conversation copy and localization placeholders.
- Add performance & resilience tasks: load test suite, backoff/circuit breaker verification, chaos drills for WhatsApp/Redis outages.

**Ordering Strategy**:
- Setup (uv, Docker, linting) → Contract/integration tests → Domain models/services → API/worker implementation → Observability + consent hooks → UX & performance polish.
- Mark [P] for independent file work (e.g., parallel unit tests in distinct modules).

**Estimated Output**: ~28 tasks generated by `/tasks`.

## Phase 3+: Future Implementation
- **Phase 3**: `/tasks` command generates tasks.md.
- **Phase 4**: Execute tasks, build features, update docs.
- **Phase 5**: Validate via pytest suite, load tests, quickstart run, BetterStack dashboards.

## Complexity Tracking
No constitutional deviations anticipated; single-service with worker remains within baseline complexity.

## Progress Tracking
**Phase Status**:
- [x] Phase 0: Research complete (/plan command)
- [x] Phase 1: Design complete (/plan command)
- [x] Phase 2: Task planning complete (/plan command - describe approach only)
- [ ] Phase 3: Tasks generated (/tasks command)
- [ ] Phase 4: Implementation complete
- [ ] Phase 5: Validation passed

**Gate Status**:
- [x] Initial Constitution Check: PASS
- [x] Post-Design Constitution Check: PASS
- [x] All NEEDS CLARIFICATION resolved
- [ ] Complexity deviations documented (not required)

---
*Based on Constitution v1.0.0 - See `/memory/constitution.md`*
# Implementation Plan: [FEATURE]

**Branch**: `[###-feature-name]` | **Date**: [DATE] | **Spec**: [link]
**Input**: Feature specification from `/specs/[###-feature-name]/spec.md`

## Execution Flow (/plan command scope)
```
1. Load feature spec from Input path
   → If not found: ERROR "No feature spec at {path}"
2. Fill Technical Context (scan for NEEDS CLARIFICATION)
   → Detect Project Type from file system structure or context (web=frontend+backend, mobile=app+api)
   → Set Structure Decision based on project type
3. Fill the Constitution Check section based on the current constitution (Code Quality, Test Discipline, UX Consistency, Performance Guarantees).
4. Evaluate Constitution Check section below
   → If violations exist: Document in Complexity Tracking with remediation path
   → If no justification possible: ERROR "Simplify approach first"
   → Update Progress Tracking: Initial Constitution Check
5. Execute Phase 0 → research.md
   → If NEEDS CLARIFICATION remain: ERROR "Resolve unknowns"
6. Execute Phase 1 → contracts, data-model.md, quickstart.md, agent-specific template file (e.g., `CLAUDE.md` for Claude Code, `.github/copilot-instructions.md` for GitHub Copilot, `GEMINI.md` for Gemini CLI, `QWEN.md` for Qwen Code, or `AGENTS.md` for all other agents).
7. Re-evaluate Constitution Check section
   → If new violations: Refactor design, return to Phase 1
   → Update Progress Tracking: Post-Design Constitution Check
8. Plan Phase 2 → Describe task generation approach (DO NOT create tasks.md)
9. STOP - Ready for /tasks command
```

**IMPORTANT**: The /plan command STOPS at step 7. Phases 2-4 are executed by other commands:
- Phase 2: /tasks command creates tasks.md
- Phase 3-4: Implementation execution (manual or via tools)

## Summary
[Extract from feature spec: primary requirement + technical approach from research]

## Technical Context
**Language/Version**: [e.g., Python 3.11, Swift 5.9, Rust 1.75 or NEEDS CLARIFICATION]  
**Primary Dependencies**: [e.g., FastAPI, UIKit, LLVM or NEEDS CLARIFICATION]  
**Storage**: [if applicable, e.g., PostgreSQL, CoreData, files or N/A]  
**Testing**: [e.g., pytest, XCTest, cargo test or NEEDS CLARIFICATION]  
**Target Platform**: [e.g., Linux server, iOS 15+, WASM or NEEDS CLARIFICATION]
**Project Type**: [single/web/mobile - determines source structure]  
**Performance Goals**: [domain-specific, e.g., 1000 req/s, 10k lines/sec, 60 fps or NEEDS CLARIFICATION]  
**Constraints**: [domain-specific, e.g., <200ms p95, <100MB memory, offline-capable or NEEDS CLARIFICATION]  
**Scale/Scope**: [domain-specific, e.g., 10k users, 1M LOC, 50 screens or NEEDS CLARIFICATION]

## Constitution Check
*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- [ ] **Code Quality Discipline** → Linting/static analysis plan defined; documentation updates identified; complexity justified.
- [ ] **Test-Driven Reliability** → Failing tests enumerated for each change; coverage strategy meets ≥90% for WhatsApp integration paths.
- [ ] **Cohesive User Experience** → Conversation copy, tone, and localization updates captured; UX approvals or needed decisions listed.
- [ ] **Performance & Resilience Guarantees** → Load/perf validation steps planned (p95 ≤1s, p99 ≤2s); resilience mechanisms (backoff, circuit breakers) accounted for.

## Project Structure

### Documentation (this feature)
```
specs/[###-feature]/
├── plan.md              # This file (/plan command output)
├── research.md          # Phase 0 output (/plan command)
├── data-model.md        # Phase 1 output (/plan command)
├── quickstart.md        # Phase 1 output (/plan command)
├── contracts/           # Phase 1 output (/plan command)
└── tasks.md             # Phase 2 output (/tasks command - NOT created by /plan)
```

### Source Code (repository root)
<!--
  ACTION REQUIRED: Replace the placeholder tree below with the concrete layout
  for this feature. Delete unused options and expand the chosen structure with
  real paths (e.g., apps/admin, packages/something). The delivered plan must
  not include Option labels.
-->
```
# [REMOVE IF UNUSED] Option 1: Single project (DEFAULT)
src/
├── models/
├── services/
├── cli/
└── lib/

tests/
├── contract/
├── integration/
└── unit/

# [REMOVE IF UNUSED] Option 2: Web application (when "frontend" + "backend" detected)
backend/
├── src/
│   ├── models/
│   ├── services/
│   └── api/
└── tests/

frontend/
├── src/
│   ├── components/
│   ├── pages/
│   └── services/
└── tests/

# [REMOVE IF UNUSED] Option 3: Mobile + API (when "iOS/Android" detected)
api/
└── [same as backend above]

ios/ or android/
└── [platform-specific structure: feature modules, UI flows, platform tests]
```

**Structure Decision**: [Document the selected structure and reference the real
directories captured above]

## Phase 0: Outline & Research
1. **Extract unknowns from Technical Context** above:
   - For each NEEDS CLARIFICATION → research task
   - For each dependency → best practices task
   - For each integration → patterns task

2. **Generate and dispatch research agents**:
   ```
   For each unknown in Technical Context:
     Task: "Research {unknown} for {feature context}"
   For each technology choice:
     Task: "Find best practices for {tech} in {domain}"
   ```

3. **Consolidate findings** in `research.md` using format:
   - Decision: [what was chosen]
   - Rationale: [why chosen]
   - Alternatives considered: [what else evaluated]

**Output**: research.md with all NEEDS CLARIFICATION resolved

## Phase 1: Design & Contracts
*Prerequisites: research.md complete*

1. **Extract entities from feature spec** → `data-model.md`:
   - Entity name, fields, relationships
   - Validation rules from requirements
   - State transitions if applicable

2. **Generate API contracts** from functional requirements:
   - For each user action → endpoint
   - Use standard REST/GraphQL patterns
   - Output OpenAPI/GraphQL schema to `/contracts/`

3. **Generate contract tests** from contracts:
   - One test file per endpoint
   - Assert request/response schemas
   - Tests must fail (no implementation yet)

4. **Extract test scenarios** from user stories:
   - Each story → integration test scenario
   - Quickstart test = story validation steps

5. **Update agent file incrementally** (O(1) operation):
   - Run `.specify/scripts/bash/update-agent-context.sh copilot`
     **IMPORTANT**: Execute it exactly as specified above. Do not add or remove any arguments.
   - If exists: Add only NEW tech from current plan
   - Preserve manual additions between markers
   - Update recent changes (keep last 3)
   - Keep under 150 lines for token efficiency
   - Output to repository root

**Output**: data-model.md, /contracts/*, failing tests, quickstart.md, agent-specific file

## Phase 2: Task Planning Approach
*This section describes what the /tasks command will do - DO NOT execute during /plan*

**Task Generation Strategy**:
- Load `.specify/templates/tasks-template.md` as base
- Generate tasks from Phase 1 design docs (contracts, data model, quickstart)
- Each contract → contract test task [P]
- Each entity → model creation task [P] 
- Each user story → integration test task
- Quickstart conversation design → UX audit and localization tasks
- Performance budgets → load test and resilience verification tasks
- Implementation tasks to make tests pass

**Ordering Strategy**:
- TDD order: Tests before implementation 
- Dependency order: Models before services before UI
- Mark [P] for parallel execution (independent files)

**Estimated Output**: 25-30 numbered, ordered tasks in tasks.md

**IMPORTANT**: This phase is executed by the /tasks command, NOT by /plan

## Phase 3+: Future Implementation
*These phases are beyond the scope of the /plan command*

**Phase 3**: Task execution (/tasks command creates tasks.md)  
**Phase 4**: Implementation (execute tasks.md following constitutional principles)  
**Phase 5**: Validation (run tests, execute quickstart.md, performance validation)

## Complexity Tracking
*Fill ONLY if Constitution Check has violations that must be justified*

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |


## Progress Tracking
*This checklist is updated during execution flow*

**Phase Status**:
- [ ] Phase 0: Research complete (/plan command)
- [ ] Phase 1: Design complete (/plan command)
- [ ] Phase 2: Task planning complete (/plan command - describe approach only)
- [ ] Phase 3: Tasks generated (/tasks command)
- [ ] Phase 4: Implementation complete
- [ ] Phase 5: Validation passed

**Gate Status**:
- [ ] Initial Constitution Check: PASS
- [ ] Post-Design Constitution Check: PASS
- [ ] All NEEDS CLARIFICATION resolved
- [ ] Complexity deviations documented

---
*Based on Constitution v1.0.0 - See `/memory/constitution.md`*
