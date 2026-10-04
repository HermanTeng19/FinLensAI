# FinLens AI

> **Understand Your Spending with AI**  
> Production-oriented AI Financial Intelligence Application for the Apple Ecosystem.

FinLens AI is a multiplatform Apple financial intelligence application designed to ingest bank statements (PDF / CSV) and transform raw, unstructured transactions into structured, deterministic analytics, pattern discovery, and grounded AI insights.

---

## Target Platforms

- **iOS** (iPhone 17/18, iOS 18+) — Touch-first, mobile transaction browsing, fast AI inquiry.
- **iPadOS** (iPad Pro / Air, iPadOS 18+) — Adaptive `NavigationSplitView`, multi-column analytics, side-by-side reconciliation.
- **macOS** (macOS 15/26+) — Native desktop financial tool, native `Table`, toolbar, keyboard shortcuts (`⌘O`, `⌘F`, `⌘R`), drag-and-drop file ingestion.

---

## Architectural Principles

1. **Deterministic Calculations First**: The Large Language Model (LLM) is **never** the authoritative calculator. All balances, category totals, net cash flow, and period comparisons are computed with exact decimal math.
2. **Apple Multiplatform Shared Core**: Business models, validation, ViewModels (`@Observable`), and API clients reside in `FinLensCore` (Swift Package), maximizing code reuse while providing tailored native UI for each device form factor.
3. **No Financial Credentials**: Users upload bank statements directly. The app never requests or stores online banking passwords, PINs, or MFA codes.
4. **Agentic Tooling & Grounded Answers**: The AI Assistant interacts with financial data strictly through structured deterministic tools (`search_transactions`, `get_spending_by_category`, etc.) with runtime grounding validation.

---

## Repository Structure

```
finlens-ai/
├── apple/                   # Apple Multiplatform Xcode Project & Shared Core
│   ├── FinLens/             # Native Application Shell (iOS, iPadOS, macOS)
│   └── FinLensCore/         # Shared Swift Package (Models, ViewModels, Services)
├── backend/                 # Python FastAPI Backend & Intelligence Services
│   └── app/                 # API routes, Agents, Tools, Deterministic Engine
├── document-ai/             # Statement Ingestion & Parsing Pipeline (PDF/CSV)
├── evaluation/              # AI Accuracy, Extraction & Grounding Benchmarks
├── infrastructure/          # Docker Compose, Database migrations, deployment
├── docs/                    # Technical specs, architecture docs, API reference
├── scripts/                 # Development & CI automation scripts
└── README.md
```

---

## Quick Start

### 1. Apple Application (iOS / iPadOS / macOS)
Open `apple/FinLens.xcodeproj` in Xcode (or build via command-line using `xcodebuild`).

### 2. Backend (Python 3.12 / FastAPI)
```bash
cd backend
source .venv/bin/activate
uv pip install -e .
uvicorn app.main:app --reload
```

---

## License
Proprietary - FinLens AI Team.
