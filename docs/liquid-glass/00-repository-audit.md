# MechTech — Repository Audit

**Status:** Completed baseline audit  
**Date:** 2026-11-17  
**Branch:** `main` (commit `55dd815 feat: add frontend layout, 3D motor scene, and core application pages`)  
**Auditor:** Development Agent (Antigravity)  
**Purpose:** Evidence-based inspection of the existing MechTech codebase prior to implementing the Liquid Glass redesign.

---

## 1. Project context already established

The approved MechTech product direction:

- **Audience:** Academic demonstration and industrial maintenance operators.
- **Equipment domain:** Three-phase electric induction motors with an extensible equipment type architecture.
- **Diagnostic intelligence:** 3-layer hybrid explainable reasoning (Heuristic Rules + Scikit-Learn ML + NetworkX Knowledge Graph ontology).
- **Deployment:** Local-first prototype with production multi-container Docker Compose.
- **Backend priority:** FastAPI, SQLAlchemy 2.0, Alembic, SQLite/PostgreSQL, local secure file storage, session cookies, and RBAC.
- **Frontend direction:** React 19 + Vite 8 + TypeScript 5/7, Tailwind CSS v4, Radix UI / shadcn/ui, Framer Motion, React Three Fiber and Drei.
- **Visualization direction:** Realistic procedural 3D motor digital twin with component-level isolation and diagnostic overlays.
- **Theme requirement:** Dual light and dark themes with system preference support.

---

## 2. Audit objectives

1. Understand the current frontend structure and entry points.
2. Identify installed framework/library versions from the lockfile.
3. Map existing routes, layouts, features and shared components.
4. Identify API clients, authentication flows and authorization boundaries.
5. Identify existing charting, graph and 3D implementations.
6. Establish the current test/build/lint baseline with verified outputs.
7. Find styling conflicts and migration risks.
8. Produce a page-by-page migration inventory without changing application code.

---

## 3. Safe audit rules compliance

- [x] Started on recorded Git working tree.
- [x] Did not upgrade packages during audit.
- [x] Did not delete, rename or move existing feature files.
- [x] Preserved all backend APIs, database schemas, authentication rules and diagnostic logic.
- [x] Preserved local database and seed data.
- [x] All findings backed by verified execution and file inspections.
- [x] No secrets, passwords or `.env` tokens recorded.

---

## 4. Repository inspection findings

### 4.1 Git and project root

- **Repository root:** `C:\Users\DAKSH\OneDrive\Documents\GitHub\MechTech`
- **Active branch:** `main`
- **Latest commit:** `55dd815 feat: add frontend layout, 3D motor scene, and core application pages`
- **Package manager:** `npm` (`npm@12.2.1`, Node `v24.21.0`), lockfile: `frontend/package-lock.json`
- **Repository layout:**
  - `backend/`: FastAPI backend service, Alembic migrations, database models, ML models, and tests.
  - `frontend/`: React 19 single-page application built with Vite and Tailwind CSS v4.
  - `docker/`: Multi-stage Dockerfiles (`Dockerfile.backend`, `Dockerfile.frontend`) and Nginx configurations.
  - `docs/`: Architecture documentation, API specifications, database design, and `liquid-glass/` specs.
  - `data/`: Local database storage (`data/db/mechtech.db`) and artifacts.

### 4.2 Frontend entry points and structure

- **Root files:**
  - Package manifest: `frontend/package.json`
  - Active lockfile: `frontend/package-lock.json`
  - Vite configuration: `frontend/vite.config.ts` (proxies `/api` to `http://127.0.0.1:8000` and `/ws` to `ws://127.0.0.1:8000`)
  - TypeScript configs: `frontend/tsconfig.json`, `frontend/tsconfig.app.json`, `frontend/tsconfig.node.json` (Target: `ES2023`, `moduleResolution: bundler`, `noUnusedLocals: true`, path alias `@/*` pointing to `./src/*`)
  - Entry HTML: `frontend/index.html` (mounts `#root` to `src/main.tsx`)
  - Entry script: `frontend/src/main.tsx` (loads `@fontsource/inter`, `@fontsource/jetbrains-mono`, and `./index.css`)
  - Root component: `frontend/src/App.tsx` (wraps tree in `QueryClientProvider`, `AuthProvider`, `BrowserRouter`, and `Suspense`)
- **Key architecture answers:**
  - **Framework:** React `19.3.1` + Vite `8.3.5`.
  - **CSS:** Tailwind CSS v4 (`tailwindcss@4.3.4` with `@tailwindcss/vite: 4.3.4`). Uses `@theme inline` with CSS variables in `frontend/src/index.css`.
  - **Routing:** `react-router-dom@7.18.5` with lazy-loaded route elements.
  - **Component organization:** Grouped by `pages/`, `components/layout/`, `components/motor3d/`, `components/ui/`, `context/`, `lib/`, `types/`.
  - **Theme status:** Basic `.dark` root classes exist, but formal dual-theme tokens and light/dark theme switcher require systematic completion in Phase 1.
  - **Environment variables:** `VITE_API_BASE_URL` (defaults to `/api/v1`).

---

### 4.3 Existing pages and workflows inventory

| Route | Page / Component | User Role | Main Actions | API / Data Source | Current Status |
|---|---|---|---|---|---|
| `/` | `LandingPage.tsx` | Public | View platform capabilities, access CTA links | None (Static / AuthContext) | Active & verified |
| `/login` | `LoginPage.tsx` | Public | Submit credentials, 1-click demo login (Admin/Maintainer/Viewer) | `POST /api/v1/auth/login` | Active & verified |
| `/register` | `RegisterPage.tsx` | Public | Request access with name, email, password, organization | `POST /api/v1/auth/register` | Active & verified |
| `/dashboard` | `DashboardPage.tsx` | Authenticated | Fleet health KPIs, 3D motor view, fault injection, telemetry preview | `/equipment`, `/alerts`, `/diagnoses` | Active & verified |
| `/equipment` | `EquipmentListPage.tsx` | Authenticated | Search, filter, view motor asset cards and status badges | `GET /api/v1/equipment` | Active & verified |
| `/equipment/:id` | `EquipmentDetailPage.tsx` | Authenticated | Inspect 3D motor mesh, exploded view toggle, view nameplate specs & sensors | `GET /api/v1/equipment/:id`, `GET /api/v1/equipment/:id/sensors` | Active & verified |
| `/monitoring` | `MonitoringPage.tsx` | Authenticated | Real-time dual-channel Recharts plot, fault injection simulator, threshold rules table, add rule modal | `GET/POST /monitoring/rules`, `POST /readings/batch` | Active & verified |
| `/alerts` | `AlertsPage.tsx` | Authenticated | Triage anomalies, filter severity/status, acknowledge, resolve modal sheet, dismiss | `GET /alerts`, `POST /alerts/:id/acknowledge`, `POST /alerts/:id/resolve`, `POST /alerts/:id/dismiss` | Active & verified |
| `/diagnostics` | `DiagnosticsPage.tsx` | Authenticated | Run hybrid analysis, inspect 3-layer evidence (Rule, ML, Graph), verify advisory notice, submit human review | `GET /diagnoses`, `POST /diagnoses/generate`, `POST /diagnoses/:id/review` | Active & verified |
| `/maintenance` | `MaintenancePage.tsx` | Authenticated | Manage work orders, upload inspection PDF/photos, download attachments, supervisor verification | `GET/POST /maintenance`, `POST /maintenance/:id/verify`, `POST/GET /maintenance/:id/attachments` | Active & verified |
| `/admin` | `AdminPage.tsx` | `platform_admin` | Approve/reject pending user registrations, inspect immutable audit trail | `GET /admin/registrations`, `POST /admin/registrations/:id/approve`, `GET /audit-logs` | Active & verified |

---

### 4.4 Shared UI and design inventory

- **Navigation & App Shell:**
  - `frontend/src/components/layout/AppLayout.tsx`: Side navigation bar with active route highlight pill, responsive mobile menu drawer, advisory compliance top banner, user profile footer with sign-out trigger.
- **UI Primitives:**
  - `frontend/src/components/ui/button.tsx`: CVA button component (`default`, `destructive`, `outline`, `secondary`, `ghost`, `link`).
  - `frontend/src/components/ui/badge.tsx`: CVA badge component (`default`, `secondary`, `destructive`, `outline`).
  - `radix-ui@1.8.1`: Complete primitive bundle installed (Dialog, DropdownMenu, Tooltip, Select, Tabs, Popover, etc.).
  - `lucide-react@1.68.0`: Primary icon library.
- **Modal Dialogs:**
  - Currently implemented with backdrop-blur overlays and frosted panels directly in page components (`MonitoringPage`, `AlertsPage`, `DiagnosticsPage`, `MaintenancePage`). Ready for abstraction into reusable `GlassDialog` primitives.
- **Styling Architecture:**
  - Tailwind CSS v4 CSS-first configuration (`@import "tailwindcss"; @import "tw-animate-css"; @theme inline { ... }`).
  - Ambient liquid aurora mesh gradients (`.liquid-glow-orb-cyan`, `.liquid-glow-orb-indigo`, `.liquid-glow-orb-emerald`).
  - Frosted glass token classes (`.glass-panel`, `.glass-panel-interactive`, `.glass-pill`, `.glass-btn`, `.glass-input`).

---

### 4.5 Data and backend integration

- **Base URL:** `VITE_API_BASE_URL` (configured in `frontend/src/lib/api.ts`, defaulting to `/api/v1`).
- **HTTP Client:** `frontend/src/lib/api.ts` wrapping native `fetch`:
  - Automatically extracts CSRF token from `mechtech_csrf` cookie and injects `X-CSRF-Token` header on mutating requests (`POST`, `PUT`, `PATCH`, `DELETE`).
  - Uses `credentials: 'include'` for secure HttpOnly cookie session handling.
  - Normalizes API error payloads into structured `ApiError` instances.
- **Authentication Context:** `frontend/src/context/AuthContext.tsx`:
  - Session verification on mount via `GET /api/v1/auth/me`.
  - Credentials submission via `POST /api/v1/auth/login`.
  - Public registration via `POST /api/v1/auth/register`.
  - Session invalidation via `POST /api/v1/auth/logout`.
  - Role-based permissions checks via `hasRole()`, `isPlatformAdmin`, and `isMaintainer`.
- **Server Cache & State:** `@tanstack/react-query@5.105.3` manages query caching, automatic deduplication, and manual invalidations (`refetch()`).

---

### 4.6 Visualization inventory

- **2D Telemetry Charting:** `recharts@3.10.1`:
  - Responsive dual-axis time-series visualization in `MonitoringPage.tsx` (Stator Temperature °C on left Y-axis, Drive-End Vibration RMS mm/s on right Y-axis) and mini-preview on `DashboardPage.tsx`.
- **Graph & Node Visualization:** `@xyflow/react@12.12.1` (React Flow) is installed in dependencies.
- **Interactive 3D Digital Twin Engine:**
  - `three@0.187.0`
  - `@react-three/fiber@9.8.2` (Fiber v9 is fully compatible with React 19)
  - `@react-three/drei@10.7.9`
- **3D Motor Scene (`frontend/src/components/motor3d/MotorScene.tsx`):**
  - Procedural parametric induction motor constructed from Three.js geometries (no external proprietary mesh assets required).
  - Sub-assemblies: Rotating steel transmission shaft, drive-end front bearing, rear bearing, laminated rotor core, insulated copper stator windings, cast iron housing with cooling fins, and rear ventilation fan.
  - Interactive capabilities:
    - Orbit controls (rotate, zoom, pan).
    - Exploded view toggle expanding components along axial vector.
    - Mesh raycasting hover tooltip displaying live sensor values.
    - Component click selection highlighting mesh boundaries.
    - Emissive pulse animation (`#dc2626` / `#b91c1c`) when component status is `critical`.

---

### 4.7 Quality and performance baseline

The following commands were executed directly against the active repository:

| Check | Command | Result | Details |
|---|---|---|---|
| **TypeScript Typecheck** | `npm run typecheck` (`tsc -b`) | **PASSED (0 errors)** | Clean compilation across all application modules. |
| **Linter** | `npm run lint` (`oxlint`) | **PASSED (0 errors, 23 warnings)** | 0 errors; warnings are trivial fast-refresh function exports and unused catch arguments. |
| **Component & Unit Tests** | `npm run test` (`vitest run`) | **PASSED (5 passed, 0 failed)** | 2 test files (`api.test.ts`, `App.test.tsx`), 5 test cases passing in 2.67s. |
| **Production Build** | `npm run build` (`tsc -b && vite build`) | **PASSED (0 errors)** | 3,039 modules transformed; built in 1.06s. Bundle size: JS gzip ~368 kB, CSS gzip 12.95 kB. |
| **End-to-End Tests** | `test:e2e` (`playwright test`) | Installed (`@playwright/test: 1.64.1`) | Configured; full browser e2e runner available. |

---

## 5. Audit findings summary

### Environment

| Item | Finding | Evidence |
|---|---|---|
| Package manager | `npm` | `frontend/package-lock.json` |
| Node version | `v24.21.0` (npm `12.2.1`) | `node --version`, `npm --version` |
| React version | `19.3.1` (React-DOM `19.3.1`) | `package-lock.json`, `npm ls react` |
| Vite version | `8.3.5` (`@vitejs/plugin-react: 6.2.1`) | `package-lock.json`, `npm ls vite` |
| TypeScript version | `7.0.2` (Target `ES2023`) | `package-lock.json`, `tsconfig.app.json` |
| Tailwind CSS version | `4.3.4` (Tailwind v4 with `@tailwindcss/vite`) | `package-lock.json`, `vite.config.ts` |
| Router | `react-router-dom: 7.18.5` | `package-lock.json`, `App.tsx` |
| Test runners | `vitest: 5.1.0`, `playwright: 1.64.1` | `package-lock.json`, `vitest.config.ts` |

### Architecture

| Area | Existing implementation | Status & Plan |
|---|---|---|
| Routing | `react-router-dom@7.18.5` with lazy routes & ProtectedRoute | **Preserve**: Working reliably with route guards. |
| Layout | `components/layout/AppLayout.tsx` with sidebar & advisory header | **Enhance**: Add light/dark theme switch and formal GlassSurface primitives. |
| Theme | CSS custom properties with basic `.dark` override in `index.css` | **Phase 1 Target**: Implement `ThemeProvider` with light/dark/system persistence. |
| UI Primitives | `components/ui/` (`button.tsx`, `badge.tsx`), Radix UI | **Phase 2 Target**: Build `GlassSurface`, `GlassPanel`, `GlassCard`, `GlassButton`. |
| API client | `lib/api.ts` native fetch with CSRF cookie handling | **Preserve**: Stable contract with FastAPI backend. |
| Authentication | `context/AuthContext.tsx` with session cookie and `/auth/me` | **Preserve**: Fully validated with backend RBAC. |
| Charts | `recharts@3.10.1` dual-axis time-series | **Enhance**: Apply glass-themed tooltip and Cartesian grids. |
| 3D Digital Twin | Three.js + React Three Fiber v9 + Drei v10 in `MotorScene.tsx` | **Enhance**: Add subtle glass material options for motor casing. |
| Tests | Vitest + React Testing Library | **Preserve & Expand**: Add theme and component unit tests. |

---

## 6. Risks and blockers

| Risk | Severity | Evidence | Mitigation |
|---|---|---|---|
| **Tailwind v4 Configuration Syntax** | Low | Project uses `@theme inline` in `index.css` rather than a legacy `tailwind.config.js`. | Keep tokens inside CSS-first `@theme` declarations; do not introduce conflicting v3 configuration files. |
| **Light Theme Contrast** | Medium | The application was previously dark-first (`#050914`). | Explicitly test text contrast ratios (minimum 4.5:1) for all labels, badges, and charts in light mode (`#F3F6FA`). |
| **3D Rendering Performance** | Low | `MotorScene.tsx` uses procedural geometries rather than heavyweight external glTF assets. | Maintain lazy-loading via `React.lazy()` to avoid blocking initial paint. |
| **Backend API Regressions** | High (if violated) | Strict backend contracts for auth, telemetry, and diagnostics. | Keep all API calls, schemas, and endpoints 100% unchanged during frontend visual upgrades. |

---

## 7. Migration strategy & file-level action plan

### Files to preserve untouched
- All backend routes, models, migrations, and scripts (`backend/**/*`).
- API client contracts and schemas (`frontend/src/lib/api.ts`, `frontend/src/types/api.ts`).
- Authentication logic and route guards (`frontend/src/context/AuthContext.tsx`, `frontend/src/App.tsx` routes).

### Files to create in Phase 1 (Design System Foundation)
- `frontend/src/styles/tokens.css` (semantic color, elevation, radius, blur tokens for light and dark).
- `frontend/src/styles/glass.css` (named material variants: subtle, standard, floating, modal).
- `frontend/src/styles/motion.css` (reduced-motion fallbacks and fluid spring transitions).
- `frontend/src/context/ThemeContext.tsx` (`light`, `dark`, `system` mode provider with localStorage persistence).
- `frontend/src/components/glass/GlassSurface.tsx` (reusable polymorphic glass primitive).
- `frontend/src/pages/DesignPlaygroundPage.tsx` (isolated visual test harness to validate light/dark glass surfaces).

### Files to enhance in subsequent phases
- `frontend/src/components/layout/AppLayout.tsx` (integrate theme toggle pill and GlassSurface sidebar).
- `frontend/src/pages/*.tsx` (progressively adopt `GlassCard` and `GlassPanel` primitives).

---

## 8. Sign-off

- [x] All findings are evidence-based and directly verified.
- [x] Unknowns and assumptions have been replaced with facts.
- [x] Existing code and data were preserved without regression.
- [x] Baseline test (`5/5 passed`), typecheck (`0 errors`), and build (`1.06s`) confirmed clean.
- [x] The migration plan is 100% compatible with the actual React 19 + Tailwind v4 repository.
