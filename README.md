# FinLens AI

<div align="center">

<img src="docs/images/app_icon_ios.png" width="128" height="128" alt="FinLens AI Icon" style="border-radius: 22%; box-shadow: 0 8px 24px rgba(0,0,0,0.25);" />

# FinLens AI
### Understand Your Spending with AI
**Production-Grade Intelligent Financial Analytics for the Apple Ecosystem**  
*Private, Deterministic, and Multiplatform Financial Intelligence for iOS, iPadOS & macOS*

**English** | [中文版](README_zh.md)

[![Platform](https://img.shields.io/badge/Platforms-iOS%20%7C%20iPadOS%20%7C%20macOS-000000.svg?logo=apple&logoColor=white)](https://developer.apple.com/swift/)
[![Swift](https://img.shields.io/badge/Swift-6.0-F05138.svg?logo=swift&logoColor=white)](https://swift.org)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![PostgreSQL](https://img.shields.io/badge/Database-PostgreSQL%2016-4169E1.svg?logo=postgresql&logoColor=white)](https://www.postgresql.org)
[![License](https://img.shields.io/badge/License-Proprietary-blue.svg)](LICENSE)

</div>

---

## 📖 Overview

**FinLens AI** is an intelligent personal financial analytics application engineered specifically for the Apple multiplatform ecosystem. It ingests bank statements (PDF / CSV) and leverages a robust Document AI pipeline to clean, deduplicate, and normalize unstructured transactions—delivering **exact, deterministic financial calculations, multi-dimensional spending patterns, and an AI financial assistant strictly grounded in authoritative records**.

---

## 🎨 App Icon Design System

To diverge from generic "AI-generated neon purple-blue gradients", FinLens AI features tailored app icons crafted strictly to **Apple's Human Interface Guidelines (HIG)**:

<table>
  <thead>
    <tr>
      <th width="50%" align="center"><b>iOS & iPadOS Official App Icon</b></th>
      <th width="50%" align="center"><b>macOS Desktop Pro App Icon</b></th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td align="center">
        <a href="docs/images/app_icon_ios.png"><img src="docs/images/app_icon_ios.png" width="240" alt="iOS App Icon" /></a><br />
        <b>Emerald & Obsidian</b><br />
        <sub>1024 × 1024 Full-Bleed Square Canvas</sub>
      </td>
      <td align="center">
        <a href="docs/images/app_icon_macos.png"><img src="docs/images/app_icon_macos.png" width="240" alt="macOS App Icon" /></a><br />
        <b>Sapphire & Titanium</b><br />
        <sub>1024 × 1024 Desktop Pro Tactile Depth</sub>
      </td>
    </tr>
    <tr>
      <td align="left" valign="top">
        <ul>
          <li><b>Design Metaphor:</b> Three stacked isometric frosted-glass sheets (representing structured financial statements) elegantly sweep upward into three ascending rounded bar chart pillars (representing financial growth and intelligence).</li>
          <li><b>Color Harmony:</b> Grounded financial <b>Emerald Green, Mint, and an Obsidian dark-forest gradient</b>—projecting trust, clarity, and institutional restraint.</li>
          <li><b>HIG Compliance:</b> Pure 1024×1024 square canvas with a 20% safe margin, allowing iOS/iPadOS SpringBoard to automatically render smooth continuous-curvature squircles without double-masking artifacts.</li>
        </ul>
      </td>
      <td align="left" valign="top">
        <ul>
          <li><b>Design Metaphor:</b> A desktop-class optical financial lens emblem featuring layered refractive frosted glass and precision micro-beveled metallic rings.</li>
          <li><b>Tactile Texture:</b> Soft studio top-down diffuse lighting, authentic subsurface scattering, and titanium slate gradients that blend seamlessly with macOS desktop aesthetics.</li>
          <li><b>Native Asset Suite:</b> Generates a complete 10-scale asset catalog (16×16 to 1024×1024) and native <code>AppIcon-macOS.icns</code>.</li>
        </ul>
      </td>
    </tr>
  </tbody>
</table>

---

## 📱 Multiplatform Device Showcase & UI Walkthrough

FinLens AI embraces the philosophy of **"One Architecture, Shared Core, Native Platform-Specific UX"**, tailoring interactions to the ergonomic strengths of iPhone, iPad, and Mac.

### 1. iPhone Mobile Experience (iOS)

The mobile experience prioritizes touch ergonomics, high-signal information density, and rapid AI financial inquiry.

<table>
  <thead>
    <tr>
      <th width="33%" align="center"><b>📊 Financial Dashboard</b></th>
      <th width="33%" align="center"><b>🤖 Grounded AI Assistant (Ask AI)</b></th>
      <th width="33%" align="center"><b>🔒 Statements & Privacy (Profile)</b></th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td align="center">
        <a href="docs/images/view_ios_dashboard.png"><img src="docs/images/view_ios_dashboard.png" width="250" alt="iOS Dashboard View" /></a>
      </td>
      <td align="center">
        <a href="docs/images/view_ios_ask_ai.png"><img src="docs/images/view_ios_ask_ai.png" width="250" alt="iOS Ask AI View" /></a>
      </td>
      <td align="center">
        <a href="docs/images/view_ios_statements.png"><img src="docs/images/view_ios_statements.png" width="250" alt="iOS Statements View" /></a>
      </td>
    </tr>
    <tr>
      <td align="left" valign="top">
        <b>【Cash Flow & Category Breakdown】</b><br />
        Metric cards display Total Expenses, Total Income, and Net Cash Flow computed via exact Decimal arithmetic (never floating-point). Top spending categories are visualized with dynamic ratios and smooth pull-to-refresh interactions.
      </td>
      <td align="left" valign="top">
        <b>【Strictly Grounded AI Chat】</b><br />
        An agentic financial copilot that never invents numbers. The assistant invokes deterministic analytical tools (e.g., <code>get_spending_by_category</code>), earning a verified <code>Grounded</code> badge with verifiable citation origins.
      </td>
      <td align="left" valign="top">
        <b>【Privacy-First Statement Ingestion】</b><br />
        Upload or delete bank PDFs and CSVs anytime. Highlights clear privacy guarantees: in-memory statement parsing, automatic PAN/SIN redaction, and atomic cascade purging with zero bank passwords requested.
      </td>
    </tr>
  </tbody>
</table>

---

### 2. iPadOS Large-Screen Productivity (iPadOS)

Leverages the larger display real estate through adaptive two-column and three-column `NavigationSplitView` architecture rather than stretched mobile views.

<table>
  <thead>
    <tr>
      <th width="65%" align="center"><b>💻 Adaptive Split-View Layout (NavigationSplitView)</b></th>
      <th width="35%" align="center"><b>📱 System Home Screen Presence</b></th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td align="center">
        <a href="docs/images/view_ipad_dashboard.png"><img src="docs/images/view_ipad_dashboard.png" width="520" alt="iPadOS Dashboard" /></a>
      </td>
      <td align="center">
        <a href="docs/images/view_ios_homescreen.png"><img src="docs/images/view_ios_homescreen.png" width="250" alt="iOS Home Screen" /></a>
      </td>
    </tr>
    <tr>
      <td align="left" valign="top">
        <b>【Multi-Column Spatial Information Density】</b><br />
        The persistent adaptive sidebar anchors navigation and recent statement digests, while the wide canvas simultaneously displays high-level financial metrics, top category rankings, and granular recent transactions for effortless auditing.
      </td>
      <td align="left" valign="top">
        <b>【Flawless iOS / iPadOS Squircle Adaptation】</b><br />
        Verified in simulator runtimes. SpringBoard automatically applies smooth continuous-curvature squircle masking with balanced perimeter safe margins across both Light and Dark wallpapers.
      </td>
    </tr>
  </tbody>
</table>

---

### 3. macOS Desktop-Class Experience (macOS)

Optimized for keyboard workflows (`⌘O`, `⌘F`, `⌘R`), drag-and-drop file ingestion, and native AppKit/SwiftUI integration.

<table>
  <thead>
    <tr>
      <th width="50%" align="center"><b>🖥️ macOS Dock Native Presence</b></th>
      <th width="50%" align="center"><b>📱 iPad mini (A17 Pro) Home & Dock</b></th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td align="center">
        <a href="docs/images/view_macos_dock.png"><img src="docs/images/view_macos_dock.png" width="460" alt="macOS Dock" /></a>
      </td>
      <td align="center">
        <a href="docs/images/view_ipad_homescreen.png"><img src="docs/images/view_ipad_homescreen.png" width="360" alt="iPad mini Dock" /></a>
      </td>
    </tr>
    <tr>
      <td align="left" valign="top">
        <b>【Tactile Glass & Metallic Dock Aesthetics】</b><br />
        Real-world macOS Dock capture. Compiled from <code>AppIcon-macOS.icns</code>, the desktop icon exhibits subtle micro-bevels and soft rim lighting, fitting right alongside pro-grade macOS applications.
      </td>
      <td align="left" valign="top">
        <b>【Full Discrete Resolution Support】</b><br />
        Provides comprehensive native resolution sets from <code>76pt @2x</code> to <code>83.5pt @2x</code>. Renders crisp and pixel-perfect on both the iPad home grid and the multi-tasking bottom Dock.
      </td>
    </tr>
  </tbody>
</table>

---

## 🏛️ Core Architectural Principles

1. **Deterministic Calculations First**:
   - The Large Language Model (LLM) is **never** the authoritative calculator.
   - All balances, category totals, net cash flow, and period comparisons are computed with exact decimal math by Python / Swift deterministic financial engines.
   - The LLM solely interprets intent, selects tools, and explains results.
2. **Apple Multiplatform Shared Core**:
   - Domain models, API networking, and ViewModel state (`@Observable`) live in `FinLensCore` (Swift Package).
   - Over 90% of business logic is shared across iOS, iPadOS, and macOS, while presentation layers respect platform-specific interaction models.
3. **Zero Financial Credentials Required**:
   - Users upload bank statements directly. The app **never** requests, collects, or stores online banking usernames, passwords, PINs, or MFA tokens.
4. **Agentic Tool Grounding & Verification**:
   - The AI Assistant queries financial data strictly through deterministic read-only tools (`search_transactions`, `get_spending_by_category`, etc.). All metrics in responses are validated against citation sources to eliminate hallucinations.

---

## 🛠️ Technology Stack

| Layer | Core Technologies & Frameworks | Key Architecture Highlights |
| :--- | :--- | :--- |
| **Apple Client** | Swift 6, SwiftUI, SwiftData, Observation | iOS 17+, iPadOS 17+, macOS 14+ native multiplatform client |
| **Shared Core** | Swift Package Manager (`FinLensCore`) | Platform-independent domain models, ViewModels & typed API clients |
| **Backend Services** | Python 3.12, FastAPI, Uvicorn, Pydantic v2 | High-concurrency async RESTful APIs with strict schema validation |
| **Data Persistence** | PostgreSQL 16, SQLAlchemy 2.0 (asyncpg), Alembic | ACID-compliant transactional persistence with relational modeling |
| **Document AI** | pdfplumber, pypdf, python-dateutil | Robust PDF/CSV ingestion, heuristic normalization, and categorization |
| **Build & Tooling** | XcodeGen, Docker, Docker Compose, uv | Automated Xcode project generation and reproducible containerization |

---

## 📂 Repository Structure

```
FinLensAI/
├── apple/                              # Apple Multiplatform Project
│   ├── FinLens/                        # Native Application Shell (iOS, iPadOS, macOS)
│   │   ├── Sources/                    # Adaptive SwiftUI presentation views
│   │   ├── Resources/Assets.xcassets/  # Multiplatform AppIcons & asset catalogs
│   │   └── project.yml                 # Declarative XcodeGen configuration
│   └── FinLensCore/                    # Shared Swift Package (Models, ViewModels, Services)
├── backend/                            # Python FastAPI Backend
│   ├── app/                            # API routes, Agents, Tools, Deterministic Engine
│   ├── tests/                          # Comprehensive unit & integration test suites
│   └── pyproject.toml                  # Python dependency specifications
├── infrastructure/                     # Infrastructure as Code
│   ├── docker-compose.yml              # Containerized multi-service orchestration
│   └── ci/ci.yml                       # GitHub Actions CI/CD pipeline
├── docs/                               # Documentation & Visual Assets
│   └── images/                         # Production screenshots and icon assets
├── scripts/                            # Automation Scripts (Assets, packaging, tests)
│   ├── deploy_app_icons.py             # Asset catalog multi-resolution deployment
│   └── package_apple.sh                # Apple multiplatform distribution packager
├── README.md                           # Primary English documentation
└── README_zh.md                        # 简体中文版说明文档
```

---

## 🚀 Quick Start

### 1. Backend & Database Setup

Ensure Docker or Python 3.12+ is installed on your machine:

```bash
# Start PostgreSQL database container
docker run -d --name finlens-postgres -p 5432:5432 \
  -e POSTGRES_USER=finlens_user \
  -e POSTGRES_PASSWORD=finlens_password \
  -e POSTGRES_DB=finlens_db \
  postgres:16-alpine

# Install backend dependencies and launch FastAPI
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Once running, explore:
- Interactive OpenAPI Docs: `http://127.0.0.1:8000/docs`
- Service Health Check: `http://127.0.0.1:8000/api/health`

### 2. Apple Application Setup (iOS / iPadOS / macOS)

```bash
cd apple/FinLens

# Regenerate Xcode project using XcodeGen
xcodegen generate

# Open the project in Xcode
open FinLens.xcodeproj
```

Select your desired run destination (**Mac (My Mac)**, **iPhone 18 Pro**, or **iPad Pro**) and press **Run (⌘R)** to start exploring!

---

## 🔒 Security & Privacy Architecture

FinLens AI is built with privacy-first engineering constraints:
- **In-Memory Processing**: Bank statement documents are parsed directly in volatile memory and are not retained in plaintext storage.
- **Sensitive Data Redaction**: Credit card PANs, account numbers, and government IDs (e.g. Canadian SINs) are automatically redacted before logging or analytics processing.
- **Atomic Cascade Purging**: Deleting an uploaded statement immediately and irreversibly cascades to remove all associated transactions, embeddings, and analytics records.
- **Zero Banking Password Footprint**: The application never acts as a credentials proxy or financial intermediary.

---

## 📜 License

Copyright © 2026 FinLens AI Team. All rights reserved.
