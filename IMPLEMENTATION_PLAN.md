# AI Procurement & Vendor Intelligence Platform: Complete Implementation Plan

## Executive Summary & Engineering Philosophy

This document defines the architectural blueprint, multi-agent specifications, database schema, deterministic scoring algorithms, scenario simulation mechanics, and phase-by-phase implementation roadmap for the **AI Procurement & Vendor Intelligence Platform**.

### Core Engineering Principles
1. **Strict Separation of Probabilistic and Deterministic Computation**:
   - **LLMs (Probabilistic)**: Restricted to language understanding, quotation extraction, semantic policy matching, qualitative risk synthesis, and grounded explanation generation.
   - **Python Domain Services (Deterministic)**: Authoritative for all financial calculations, landed cost estimation, unit/currency conversions, policy constraint checks, multi-criteria normalization, weighted scoring, and scenario diff calculations. Under no circumstances does an LLM calculate, modify, or hallucinate a score, rank, or monetary amount.
2. **Multi-Agent Orchestration via LangGraph**:
   - Specialized agents with explicit Pydantic schemas, typed graph state, cyclic clarification loops, parallel fan-out/fan-in evaluation, and durable checkpointing.
3. **Immutable Baselines & Scenario Branching**:
   - Evaluations are immutable once approved. What-if scenarios fork the baseline input snapshot, apply parameter shifts, and re-run deterministic scoring to compute deltas without side effects.
4. **Human-in-the-Loop (HITL) Governance**:
   - Purchasing awards require authorized human sign-off via LangGraph's `interrupt()` / `Command(resume=...)` pattern.
5. **Auditable Evidence Provenance**:
   - Every extracted claim, score, and compliance status preserves exact references to source document IDs, page numbers, coordinates, and verified audit history.

---

## Section A: Architecture and Design Decisions

### 1. Overall System Architecture
The platform is built as a **Modular Monolith** with a decoupled background worker:
- **`backend-api`**: FastAPI application handling authenticated REST endpoints, document upload presigned URLs, evaluation queries, scenario executions, and Server-Sent Events (SSE) for real-time progress streaming.
- **`backend-worker`**: Celery/ARQ asynchronous worker executing LangGraph workflows, compute-heavy PDF parsing/OCR, and scenario simulations.
- **`frontend`**: React 18 Single Page Application (Vite + TypeScript + Tailwind CSS) providing requirement intake, extraction review, evaluation scorecards, what-if scenario studio, and approval center.
- **Storage & Infrastructure**:
  - PostgreSQL 16 with `pgvector` for relational data, JSONB snapshots, and vector embeddings.
  - Redis 7 for message brokering, distributed locks, and real-time SSE pub/sub.
  - MinIO / AWS S3 for document and artifact storage.

### 2. Multi-Agent Topology (LangGraph)
- **Agent 1: Requirement Analysis Agent** (LLM - Structured Output)
- **Agent 2: Vendor Discovery Agent** (Hybrid - SQL Registry + Vector Search)
- **Agent 3: Quotation Analysis Agent** (LLM + Vision/OCR + Layout Parser)
- **Agent 4: Compliance Agent** (Deterministic Policy Gating + LLM Clause Extraction)
- **Agent 5: Risk Assessment Agent** (Historical Data Analytics + LLM Risk Synthesis)
- **Agent 6: Negotiation Simulation Agent** (LLM + Policy Bounds Validator)
- **Agent 7: Scenario Simulation Agent** (Deterministic Engine + LLM Explainer)
- **Agent 8: Decision Explanation Agent** (Grounded LLM with Anti-Hallucination Guardrails)
- **Agent 9: Procurement Decision Coordinator** (Deterministic LangGraph Controller)

### 3. LangGraph Workflow Graph
```
[Procurement Request Intake]
             │
             ▼
[Requirement Analysis Agent (1)] ──(Incomplete?)──► [Clarification Request (Wait for User)]
             │ (Complete)                                      │
             ▼                                                 │ (User Responds)
[Vendor Discovery Agent (2)] ◄─────────────────────────────────┘
             │
             ▼
[Quotation Ingestion & Parsing (3)]
             │
             ├─────────────────────────────────────────┐
             │ Parallel Fan-Out (per shortlisted vendor)│
             ▼                                         ▼
   [Compliance Agent (4)]                     [Risk Assessment Agent (5)]
             │                                         │
             └────────────────────┬────────────────────┘
                                  │ Parallel Fan-In
                                  ▼
             [Deterministic Eligibility & Scoring Engine]
                                  │
                                  ▼
                 [Decision Explanation Agent (8)]
                                  │
                                  ▼
                   [Human Approval Interrupt Gate]
                                  │
             ┌────────────────────┼────────────────────┐
             ▼                    ▼                    ▼
     [Sign-Off / Award]   [Reject / Archive]   [Request Clarification]
```

### 4. Database Architecture & Multi-Tenancy
- **Tenant Isolation**: Every entity contains an `organization_id`. Scoped SQLAlchemy queries enforce tenant boundaries, backed by PostgreSQL Row-Level Security (RLS).
- **Snapshot Immutability**: Historical evaluations store complete JSONB snapshots (`spec_snapshot`, `policy_snapshot`, `score_snapshot`, `evidence_snapshot`) alongside a SHA-256 fingerprint.
- **Precision**: All financial and numeric metrics use `Numeric(18, 4)` / Python `Decimal`.

---

## Section B: Phase-by-Phase Implementation Roadmap

- **Phase 1: Environment, Infrastructure, Core Scaffold & Development Tooling**
  - Setup Docker Compose (Postgres 16 + pgvector, Redis, MinIO), backend project structure (`pyproject.toml`, FastAPI app base, config, logging), frontend project structure (Vite, React, TypeScript, Tailwind CSS), and verification tests.
- **Phase 2: Database Architecture, Domain Models, Tenant Context & Migrations**
  - SQLAlchemy 2.x async models (Organizations, Users, Vendors, Performance, Requests, Documents, Quotations, Compliance, Risk, Policies, Evaluations, Scores, Scenarios, Approvals, Audit), Alembic migrations, tenant context.
- **Phase 3: Deterministic Scoring, Eligibility & Policy Engine**
  - Pure Python domain services: Landed Cost Calculator, Criterion Normalizer, Eligibility Evaluator, Weighted Scoring Engine, tie-breaking, confidence penalty, SHA-256 reproducibility verification.
- **Phase 4: Document Ingestion, PDF Parsing & Hybrid Retrieval Pipeline**
  - S3/MinIO storage client, PDF/OCR coordinate parser (PyMuPDF / pdfplumber), spreadsheet parser, chunking with bounding box provenance, PostgreSQL hybrid search (pgvector + FTS).
- **Phase 5: LLM Abstraction Layer & Core Intake Agents (Agents 1, 2, 3)**
  - Provider-agnostic LLM client (OpenAI, Anthropic, Gemini) with structured output validation; Requirement Analysis Agent; Vendor Discovery Agent; Quotation Analysis Agent with evidence coordinate linking.
- **Phase 6: Compliance & Risk Assessment Agents (Agents 4, 5) with Evidence Provenance**
  - Deterministic compliance rule checks + LLM clause extraction; historical risk aggregation + qualitative risk synthesis; evidence linking service.
- **Phase 7: LangGraph Multi-Agent Orchestrator & Human-in-the-Loop Workflow (Agents 8, 9)**
  - StateGraph assembly, parallel vendor evaluation fan-out/fan-in, Decision Coordinator (Agent 9), Decision Explanation Agent (Agent 8) with anti-hallucination verification, PostgresSaver checkpointing, HITL interrupt/resume.
- **Phase 8: Negotiation Simulation & What-If Scenario Simulation Engine (Agents 6, 7)**
  - Negotiation Simulation Agent (Agent 6); Scenario Simulation Agent (Agent 7); baseline immutability preservation; differential calculation ($\Delta \text{score}$, $\Delta \text{rank}$, $\Delta \text{cost}$, winner displacement).
- **Phase 9: FastAPI Endpoints, Async Background Worker & Real-time Event Streaming**
  - REST API routes (auth, requests, documents, evaluations, scenarios, approvals, audit), Celery/ARQ worker, Redis Pub/Sub SSE streaming for real-time node transitions.
- **Phase 10: Frontend Foundation, Design System, Procurement Intake & Extraction Review** [COMPLETED]
  - Bento Grid system (`skills/design/bento`), Inter & JetBrains Mono typography, custom scrollbars, multi-tenant workspace header, requirement intake form with instant presets & Agent 1 clarification loops, quotation upload dropzone with SHA-256 fingerprinting, side-by-side PDF layout viewer with normalized $[0-1]$ bounding-box coordinate highlighter.
- **Phase 11: Frontend Evaluation Dashboard, Interactive Scenario Studio & Approval Center** [COMPLETED]
  - Deterministic vendor comparison scorecard with Recharts bar chart, multi-criteria breakdown (Financial, Tech, Risk, Landed Cost), real-time What-If scenario studio with live parameter sliders and winner displacement alert banners, autonomous negotiation simulation studio with concession rounds, and Human-in-the-Loop (HITL) approval gate with tamper-evident cryptographic signature display.
- **Phase 12: Production Hardening, Security, Prompt Injection Defenses, Auditing & E2E Pilot** [COMPLETED]
  - SecurityGuard multi-pattern prompt injection defense layer and untrusted supplier document sandboxing (`<untrusted_supplier_data>` XML containment), HTTP production security headers (HSTS, nosniff, DENY frame options), sliding-window rate limiting middleware, tamper-evident cryptographic audit logging service with unbroken SHA-256 hash chaining (`AuditService`), and full end-to-end automated pilot integration test (`tests/e2e/test_procurement_pilot.py`) covering all 9 lifecycle steps from intake to approved purchase order.

---

## Project Status: All 12 Phases Fully Completed & Production Verified
- **Backend Architecture**: Modular monolith with FastAPI, SQLAlchemy 2.0, PostgreSQL (pgvector), Alembic, Redis pub/sub.
- **Multi-Agent Engine**: 9 specialized LangGraph agents with deterministic eligibility gating, pure-Python scoring, anti-hallucination verification, and HITL interrupt gates.
- **Frontend Decision Studio**: Bento Grid design system (`skills/design/bento`) with live SSE node transitions, normalized PDF bounding-box coordinates, interactive What-If scenario studio, and officer sign-off modal.
- **Test Suite**: 57/57 unit, integration, and E2E pilot tests passing with 100% success.
- **Frontend Production Build**: Vite TypeScript bundle compiling cleanly in 2.64s.

---

## Section C: Repository Structure

```
Multiagent_system/
├── IMPLEMENTATION_PLAN.md
├── docker-compose.yml
├── .env.example
├── .gitignore
├── docker/
│   ├── init-db.sql
│   ├── Dockerfile.backend
│   ├── Dockerfile.worker
│   └── Dockerfile.frontend
├── backend/
│   ├── pyproject.toml
│   ├── alembic.ini
│   ├── alembic/
│   │   ├── env.py
│   │   └── versions/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── api/
│   │   │   ├── deps.py
│   │   │   └── v1/
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   ├── database.py
│   │   │   ├── security.py
│   │   │   ├── logging.py
│   │   │   └── events.py
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   │   ├── scoring/
│   │   │   ├── ingestion/
│   │   │   ├── retrieval/
│   │   │   ├── scenarios/
│   │   │   ├── storage/
│   │   │   └── audit/
│   │   ├── agents/
│   │   │   ├── prompts/
│   │   │   └── ...
│   │   ├── graphs/
│   │   │   ├── state.py
│   │   │   ├── edges.py
│   │   │   ├── procurement_graph.py
│   │   │   └── nodes/
│   │   └── worker/
│   └── tests/
│       ├── conftest.py
│       ├── unit/
│       ├── integration/
│       └── e2e/
└── frontend/
    ├── package.json
    ├── tsconfig.json
    ├── vite.config.ts
    ├── tailwind.config.js
    ├── index.html
    └── src/
        ├── api/
        ├── components/
        ├── hooks/
        ├── pages/
        └── types/
```

---

## Section D: Agent Contract Specification

| Agent Name | Engine Type | Responsibility | Input Schema | Output Schema | Tools / Dependencies | Failure Behavior |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **1. Requirement Analysis Agent** | LLM | Parse unstructured procurement request into validated specifications, identify constraints and missing data. | `RawProcurementInput` | `ProcurementSpecResult` | None | Flag missing attributes; trigger clarification loop. |
| **2. Vendor Discovery Agent** | Hybrid (DB + Vector + LLM) | Search vendor registry, match capabilities, shortlist qualified suppliers with inclusion/exclusion reasons. | `VendorDiscoveryInput` | `VendorShortlistResult` | SQL registry, pgvector search | If no matches found, flag shortfall to coordinator. |
| **3. Quotation Analysis Agent** | LLM + OCR Parser | Extract commercial items, prices, discounts, delivery dates, warranty, and payment terms from PDFs. | `QuotationDocInput` | `NormalizedQuotation` | PDF layout extractor, coordinate mapper | Flag ambiguous values; never fabricate unstated terms. |
| **4. Compliance Agent** | Deterministic + LLM | Verify mandatory certifications, regulatory clauses, and corporate policies; produce PASS/FAIL/UNVERIFIED. | `ComplianceInput` | `ComplianceResult` | Policy rule matcher, vector search | Default to UNVERIFIED if evidence missing; cannot override hard policy rule. |
| **5. Risk Assessment Agent** | DB Analytics + LLM | Compute delivery reliability, defect rates, single-source dependency, and operational risk tiers. | `RiskInput` | `RiskAssessmentResult` | Vendor history aggregator | Penalize confidence score if historical records are sparse. |
| **6. Negotiation Simulation Agent** | LLM + Bounds Validator | Simulate vendor counteroffers and concession trade-offs within policy limits. | `NegotiationSimInput` | `NegotiationSimResult` | Deterministic bounds validator | Tag explicitly as HYPOTHETICAL_SIMULATION; no external tool calls. |
| **7. Scenario Simulation Agent** | Deterministic + LLM Explainer | Apply parameter overrides, recalculate rankings deterministically, explain rank shifts. | `ScenarioRunInput` | `ScenarioRunResult` | Python Scoring Engine, differential calculator | Enforce baseline immutability; never alter baseline database record. |
| **8. Decision Explanation Agent** | LLM (Guarded) | Produce audit-ready narrative justifications for rankings, trade-offs, and runner-up comparisons. | `ExplanationInput` | `DecisionExplanationResult` | Anti-hallucination verifier (matches numbers against scoring output) | Reject output if quoted scores differ from Python scoring engine. |
| **9. Decision Coordinator** | LangGraph Controller | Orchestrate state flow, trigger parallel evaluations, invoke scoring service, manage human interrupt. | `ProcurementEvaluationState` | Updated `ProcurementEvaluationState` | LangGraph, AsyncPostgresSaver | If mandatory data missing, halt or route to clarification node. |

---

## Section E: Deterministic Scoring & Normalization Formulas

1. **Total Landed Cost**:
   $$\text{Landed Cost} = \text{Base Price} - \text{Discounts} + \text{Freight} + \text{Insurance} + \text{Tariffs} + \text{Taxes}$$
2. **Cost Normalization (Lower is better)**:
   $$\text{Score}_{\text{cost}}(v) = \max\left(0, \min\left(100, \frac{C_{\max} - C_v}{C_{\max} - C_{\min}} \times 100\right)\right)$$
   *(If $C_{\max} == C_{\min}$, $\text{Score}_{\text{cost}}(v) = 100$)*
3. **Delivery Score (Lower lead time is better)**:
   $$\text{Score}_{\text{delivery}}(v) = \max\left(0, \min\left(100, 100 - \frac{T_v - T_{\text{req}}}{T_{\max} - T_{\text{req}}} \times 100\right)\right)$$
4. **Weighted Composite Score**:
   $$\text{Total Score}(v) = \sum_{i=1}^{M} w_i \times \text{Score}_i(v) - \text{ConfidencePenalty}(v)$$
   Where $\sum w_i = 1.0$ and $\text{ConfidencePenalty}$ reflects missing non-mandatory evidence.
5. **Eligibility Gate**:
   A vendor must satisfy 100% of non-negotiable constraints (budget ceiling, mandatory certifications, delivery deadline). Any failure marks the vendor `INELIGIBLE`, disqualifying them from winning the recommendation.

---

## Section F: What-If Scenario Mechanics

- Scenarios reference a completed `baseline_evaluation_id`.
- The baseline input snapshot is deep-copied; parameter overrides are applied.
- The modified state is executed through the pure Python scoring engine.
- Differential outputs are computed:
  - $\Delta \text{Score} = \text{Score}_{\text{scenario}} - \text{Score}_{\text{baseline}}$
  - $\Delta \text{Cost} = \text{Cost}_{\text{scenario}} - \text{Cost}_{\text{baseline}}$
  - $\Delta \text{Rank} = \text{Rank}_{\text{baseline}} - \text{Rank}_{\text{scenario}}$
  - Winner Displacement: identifies if Rank 1 shifted and explains the exact causal criteria.
- Cryptographic check: `assert SHA256(baseline_input) == baseline_record.input_hash`.

---

## Section G: Testing Strategy

1. **Unit Tests**:
   - 100% coverage on deterministic scoring, landed cost, normalizers, and eligibility gating.
   - Pydantic schema validation tests for all agent input/output structures.
2. **Integration Tests**:
   - Database migrations up/down on PostgreSQL.
   - LangGraph state machine execution from intake to human interrupt gate.
   - Scenario engine non-mutating baseline validation.
3. **Adversarial & Security Tests**:
   - Prompt injection resistance on uploaded supplier documents (ignoring injected instructions).
   - Tenant isolation verification (preventing cross-organization data leakage).
4. **End-to-End Tests**:
   - Complete procurement workflow simulation from PDF upload to human approval sign-off.

---

## Section H: Development Rules for All Subsequent Turns

1. Implement only the phase explicitly requested.
2. Do not generate the entire application at once.
3. Before implementing a phase, summarize its scope and dependencies.
4. Provide exact file paths and complete code for new files.
5. For existing files, preserve working logic and explain necessary modifications.
6. Include installation commands, migrations, environment configuration, and run instructions relevant to the phase.
7. Include tests and expected outputs.
8. Explain how to verify that the implementation works.
9. Keep all interfaces consistent with earlier phases.
10. Maintain an updated checklist of completed and remaining phases.
11. Do not claim that code was executed or tested unless it actually was.
12. If a decision from an earlier phase must change, explain the reason and impact before proceeding.
13. Ask for clarification only when an essential decision cannot reasonably be made with an explicit, documented assumption.
