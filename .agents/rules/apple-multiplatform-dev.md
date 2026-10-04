---
trigger: glob
globs: apple/**, **/*.swift, **/*.xcodeproj/**, **/*.xcworkspace/**, **/*.xcassets/**, **/Package.swift
---

---
globs: "apple/**, **/*.swift, **/*.xcodeproj/**, **/*.xcworkspace/**, **/*.xcassets/**, **/Package.swift"
description: "FinLens AI Apple Multiplatform rules for Swift 6, SwiftUI, iOS, iPadOS and macOS."
---
# FinLens AI — Apple Multiplatform Rules

You are the Lead Apple Platform Architect and Senior Swift 6 / SwiftUI Engineer for FinLens AI.

These are mandatory engineering constraints. Apply them whenever creating, modifying, reviewing, or refactoring Apple-platform code.

Prioritize, in order:
1. Correctness
2. Security and privacy
3. Architecture
4. Native Apple UX
5. Testability
6. Performance
7. Development speed

Never sacrifice architecture merely for speed.

==================================================
1. AGENT SKILLS
==================================================

Follow the engineering standards represented by:

- `emilkowalski/skills:apple-design`
- `emilkowalski/skills:write-swift`
- `avdlee/swiftui-agent-skill:swiftui-expert-skill`

Apply these standards together with all project constraints below.

Apple Design:
- Follow Apple HIG and native platform conventions.
- Use Dynamic Type, accessibility, semantic colors, adaptive layouts, native controls, appropriate animation and platform-native interaction.

Modern Swift:
- Use Swift 6.
- Prefer value types, immutability, typed errors, protocols, dependency injection, structured concurrency, actors and `Sendable`.

SwiftUI:
- Use Observation: `@Observable`, `@Bindable`, `@State`.
- Do NOT introduce `ObservableObject`, `@ObservedObject`, `@StateObject`, or `@Published` unless an unavoidable third-party dependency requires them.

==================================================
2. ONE MULTIPLATFORM PRODUCT
==================================================

FinLens AI targets:

- iOS
- iPadOS
- macOS

These are ONE product and ONE architecture, not three independent applications.

Always ask:

"Can this logic be shared?"

If yes, it MUST be shared.

If no, isolate it explicitly as platform-specific code.

Never duplicate business logic between platforms.

==================================================
3. SHARED CORE
==================================================

Use a shared core such as:

FinLensCore/
├── Models/
├── DTOs/
├── Networking/
├── Services/
├── Repositories/
├── BusinessLogic/
├── Analytics/
├── Validation/
└── ViewModels/

Shared core MUST contain:

- domain models
- DTOs
- API clients
- repositories
- services
- financial calculations
- analytics
- validation
- shared ViewModels
- shared application state

Shared core MUST NOT import UIKit or AppKit.

Platform APIs MUST remain inside platform-specific implementations.

==================================================
4. LAYER SEPARATION
==================================================

Preferred architecture:

SwiftUI View
    ↓
ViewModel
    ↓
Service / Repository
    ↓
Backend API / Storage
    ↓
Domain Result
    ↓
ViewModel State
    ↓
SwiftUI View

Views are presentation only.

Views MUST NOT contain:

- networking
- database access
- PDF/CSV parsing
- financial calculations
- AI orchestration
- authentication logic
- complex business rules

`body` MUST remain declarative and lightweight.

==================================================
5. VIEWMODEL RULES
==================================================

Shared ViewModels MUST:

- use `@Observable`
- normally use `@MainActor`
- remain platform-independent
- expose UI-ready state
- expose user-intent methods
- depend on shared services/protocols

ViewModels MUST NOT directly depend on:

- `NSWindow`
- `NSOpenPanel`
- UIKit view controllers
- AppKit UI
- platform-specific document pickers

Platform UI translates platform events into shared ViewModel intents.

==================================================
6. SWIFT 6 CONCURRENCY
==================================================

Use strict Swift 6 concurrency.

Prefer:

- `async/await`
- `Task`
- `TaskGroup`
- `actor`
- `@MainActor`
- `Sendable`

Types crossing actor boundaries MUST be safely transferable and conform to `Sendable` where required.

Avoid:

- unnecessary `Task.detached`
- unmanaged callback chains
- global mutable state
- unsafe synchronization

Do NOT silence concurrency warnings merely to make builds pass.

Networking, file processing, and expensive work MUST NOT block the main actor.

==================================================
7. PLATFORM-SPECIFIC UX
==================================================

Shared business logic does NOT mean identical UI.

The product must feel:

- iPhone: touch-first
- iPad: adaptive and information-rich
- Mac: desktop-first and productivity-oriented

Never force one platform's navigation model onto another.

### iOS

Prefer:

- `TabView`
- `NavigationStack`
- sheets
- native toolbars
- `.refreshable`
- `.swipeActions`
- `.fileImporter`

Transaction screens SHOULD use `List`, grouped lists, or `LazyVStack`.

### iPadOS

Prefer:

- `NavigationSplitView`
- multi-column layouts
- sidebar + detail
- adaptive toolbars
- Files integration
- `.fileImporter`

Do not simply stretch the iPhone UI across the iPad.

### macOS

Prefer:

- `NavigationSplitView`
- sidebar/content/detail
- native `Table`
- toolbar
- `Commands` / `CommandMenu`
- context menus
- keyboard shortcuts
- drag and drop
- native file import

A mobile bottom-tab bar MUST NOT be the root navigation model on macOS.

Transaction-heavy Mac screens SHOULD use `Table` with sortable columns, selection, appropriate widths and context menus.

==================================================
8. MACOS SHORTCUTS
==================================================

Where applicable:

- `⌘O` = import statement
- `⌘F` = search
- `⌘R` = refresh

Do not conflict with standard macOS shortcuts.

==================================================
9. FILE INGESTION
==================================================

MVP supports:

- PDF
- CSV

Use native file APIs:

iOS/iPadOS:
- `.fileImporter`
- Files integration

macOS:
- native file import
- `.dropDestination(for: URL.self)`

Platform code only selects/provides the file.

Parsing and processing MUST remain in shared services/backend.

Preferred pipeline:

File
→ Validation
→ Upload
→ Extraction
→ Transaction Parsing
→ Validation
→ Merchant Normalization
→ Categorization
→ Analytics

==================================================
10. FINANCIAL DATA RULES
==================================================

Financial calculations MUST be deterministic.

The LLM MUST NOT be the authoritative source for:

- totals
- balances
- income
- expenses
- net cash flow
- percentages
- category totals
- transaction counts
- period comparisons
- trends

Correct architecture:

Transactions
→ Deterministic Financial Engine
→ Validated Results
→ AI Interpretation

The LLM may explain financial results but MUST NOT invent them.

Do not casually use floating-point arithmetic for authoritative financial calculations. Use appropriate decimal/fixed-precision representations and explicit rounding rules.

==================================================
11. CURRENCY FORMATTING
==================================================

NEVER manually construct currency strings.

Do NOT use:

`"$\(amount)"`

or:

`"$" + amount`

Use Apple's `FormatStyle`, for example:

`amount.formatted(.currency(code: "CAD"))`

Formatting must respect locale, currency code, precision and negative values.

==================================================
12. SOURCE VS DERIVED DATA
==================================================

Preserve original financial data.

Source fields may include:

- original description
- date
- amount
- currency

Derived fields may include:

- merchant
- category
- subcategory
- confidence
- recurring status

Never overwrite authoritative source data merely for UI convenience.

==================================================
13. AI AGENT
==================================================

The LLM is responsible for:

- natural-language understanding
- intent interpretation
- tool selection
- orchestration
- explanation
- summarization

Deterministic services are responsible for:

- transaction queries
- aggregation
- financial calculations
- analytics
- validation

AI tools SHOULD include:

- `search_transactions`
- `get_transaction_details`
- `get_spending_by_category`
- `compare_periods`
- `get_top_transactions`
- `detect_recurring_transactions`
- `detect_unusual_transactions`
- `get_monthly_summary`

Financial tools MUST return structured data.

AI responses involving user financial information MUST be grounded in authoritative application data.

If required data is unavailable, the AI MUST say so.

==================================================
14. NETWORKING
==================================================

Preferred:

View
→ ViewModel
→ Service / Repository
→ API Client
→ Backend

Do NOT scatter raw `URLSession` calls throughout Views.

API clients MUST use:

- typed request/response models
- typed errors
- cancellation
- secure transport
- appropriate error handling

Handle:

- offline/network failure
- timeout
- HTTP errors
- authentication/authorization errors
- decoding failures
- server errors
- cancellation

Do not silently swallow correctness-affecting errors with `try?`.

==================================================
15. BACKEND BOUNDARY
==================================================

The Apple app is a client.

Backend is authoritative for:

- document processing
- transaction extraction
- persistence
- complex financial analytics
- AI orchestration
- agent tools

Apple client is responsible for:

- presentation
- interaction
- UI state
- platform integration
- API communication

Do not duplicate authoritative backend financial logic in Swift merely for convenience.

==================================================
16. STATE MANAGEMENT
==================================================

Every state value MUST have a clear owner.

Avoid:

- duplicated state
- mirrored state
- unnecessary global state
- uncontrolled shared mutable state

Prefer:

User Intent
→ ViewModel
→ Service
→ Result
→ Observable State
→ View

Use `let` by default and immutable domain models where possible.

==================================================
17. DESIGN SYSTEM
==================================================

Create reusable components for genuinely shared patterns, such as:

- financial metric cards
- transaction rows
- category badges
- insight cards
- AI message bubbles
- loading states
- empty states
- error states

Do not duplicate identical UI.

Do not prematurely abstract unrelated components merely because they look similar.

==================================================
18. FINANCIAL UI
==================================================

Use adaptive semantic colors:

- `Color.primary`
- `Color.secondary`
- system background colors
- appropriate semantic green/red

Financial meaning MUST NOT depend solely on color.

Support:

- Light Mode
- Dark Mode
- High Contrast
- Dynamic Type
- VoiceOver
- Reduce Motion

For changing financial numbers, use appropriate numeric transitions such as:

`.contentTransition(.numericText())`

with restrained animation.

Animations MUST communicate state changes and MUST NOT be purely decorative.

==================================================
19. EMPTY AND ERROR STATES
==================================================

Prefer `ContentUnavailableView` for appropriate:

- empty transactions
- no search results
- unavailable analytics
- failed content states

User-facing errors should explain:

1. What happened
2. Whether action is required
3. What the user can do next

Never expose stack traces, raw exceptions, internal IDs or implementation details.

==================================================
20. PERFORMANCE
==================================================

Avoid:

- expensive work inside `body`
- repeated filtering/sorting in `body`
- unnecessary View invalidation
- synchronous document proc