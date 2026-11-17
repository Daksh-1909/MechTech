# MechTech — Current Frontend Map

**Status:** Completed repository map  
**Date:** 2026-11-17  
**Branch:** `main`  
**Purpose:** Reconciles target architecture with verified existing implementation.

---

## 1. Target application domains

| Domain | Intended Responsibility | Current Route / Component | Status |
|---|---|---|---|
| **Authentication** | Login, registration request, session restore | `/login` (`LoginPage.tsx`), `/register` (`RegisterPage.tsx`), `AuthContext.tsx` | Verified & Active |
| **Dashboard** | Fleet health overview, KPIs, 3D motor preview, scenario injection | `/dashboard` (`DashboardPage.tsx`) | Verified & Active |
| **Equipment** | Motor asset list, search/filter, 3D exploded view, technical specs | `/equipment` (`EquipmentListPage.tsx`), `/equipment/:id` (`EquipmentDetailPage.tsx`) | Verified & Active |
| **Monitoring** | Live sensor telemetry streaming, threshold monitoring rules | `/monitoring` (`MonitoringPage.tsx`) | Verified & Active |
| **Diagnostics** | Heuristic rules findings & advisory human review | `/diagnostics` (`DiagnosticsPage.tsx`) | Verified & Active |
| **Predictions** | Scikit-learn Random Forest inference & probability distributions | Incorporated in `/diagnostics` (Layer 2) | Verified & Active |
| **Knowledge Graph** | NetworkX ontology traversal, procedures & repair actions | Incorporated in `/diagnostics` (Layer 3) | Verified & Active |
| **Maintenance** | Corrective & preventive work orders, attachments, supervisor sign-off | `/maintenance` (`MaintenancePage.tsx`) | Verified & Active |
| **Notifications** | Active anomaly alerts, acknowledge/resolve/dismiss workflows | `/alerts` (`AlertsPage.tsx`) | Verified & Active |
| **Users / Admin** | Pending registration approval queue, immutable audit trail | `/admin` (`AdminPage.tsx`) | Verified & Active |
| **Landing** | Public presentation, feature overview, CTA links | `/` (`LandingPage.tsx`) | Verified & Active |

---

## 2. Intended target frontend structure

The proposed destination structure adapts cleanly to the existing codebase:

```text
frontend/src/
├── app/                  # (Future Phase: App.tsx & routing re-export)
├── components/
│   ├── glass/            # Reusable Liquid Glass primitives (GlassSurface, GlassCard, GlassPanel, GlassButton)
│   ├── layout/           # AppLayout.tsx shell, navigation, header
│   ├── motor3d/          # MotorScene.tsx procedural 3D digital twin
│   └── ui/               # button.tsx, badge.tsx (CVA & Radix primitives)
├── context/
│   ├── AuthContext.tsx   # User sessions, login, register, RBAC
│   └── ThemeContext.tsx  # Phase 1: Light, Dark, System theme provider
├── lib/
│   ├── api.ts            # Fetch wrapper with CSRF injection & ApiError
│   └── utils.ts          # clsx + tailwind-merge (cn)
├── pages/                # Route entry pages (Dashboard, Equipment, Monitoring, Alerts, Diagnostics, Maintenance, Admin, Auth)
├── styles/               # Phase 1: tokens.css, glass.css, motion.css
├── test/                 # Test setup (setup.ts)
└── types/
    └── api.ts            # Complete domain TypeScript schemas
```

---

## 3. Layer responsibilities

| Layer | Responsibility | Must not own |
|---|---|---|
| **App / Routes** | Route composition, lazy loading, and `ProtectedRoute` guards | Diagnostic business logic |
| **Layouts** | Page shell, sidebar navigation, responsive drawer, advisory banner | Direct data mutation rules |
| **Glass components** | Reusable visual primitives (GlassSurface, GlassPanel, GlassCard, GlassButton) | Feature-specific API fetching |
| **Feature pages** | Domain workflows, forms, tables, and modal triggers | Low-level CSS glass duplication |
| **API layer** | HTTP requests, cookie session tokens, CSRF injection, typed schemas | Visual presentation |
| **Theme system** | Semantic color tokens, light/dark/system mode persistence | Domain business state |
| **Motion system** | Spring physics, fluid hover transitions, reduced-motion fallbacks | Business logic |
| **3D layer** | Procedural Three.js motor mesh, OrbitControls, exploded view, raycasting | Source-of-truth diagnostic calculations |
| **Backend** | RBAC, telemetry ingestion, rules evaluation, ML inference, graph reasoning | Frontend presentation |

---

## 4. Data flow

```text
User interaction
      │
      ▼
Feature page / component (e.g. DiagnosticsPage / MonitoringPage)
      │
      ├───► Local UI state (modal open, selected tab, exploded 3D toggle)
      │
      ▼
TanStack Query (`useQuery` / `useMutation`)
      │
      ▼
API Client (`src/lib/api.ts` with auto CSRF & HttpOnly session cookie)
      │
      ▼
FastAPI backend (`http://127.0.0.1:8000/api/v1/...`)
      │
      ▼
SQLAlchemy / SQLite / Rules Engine / Random Forest / NetworkX
      │
      ▼
Typed JSON response
      │
      ▼
TanStack Query cache & React re-render
      │
      ├───► Recharts dual-axis sensor plots / evidence breakdown
      │
      └───► 3D Motor digital twin (emissive alert pulses, component isolation)
```

---

## 5. Route inventory (Verified)

| Route | Existing File | Access Rule | Main Components | Data Dependencies |
|---|---|---|---|---|
| `/` | `pages/LandingPage.tsx` | Public | Marketing hero, capability cards, CTA buttons | None (Static / AuthContext) |
| `/login` | `pages/LoginPage.tsx` | Public | Credentials form, 1-click demo logins (Admin, Maintainer, Viewer) | `POST /api/v1/auth/login` |
| `/register` | `pages/RegisterPage.tsx` | Public | Access request form (name, email, password, organization) | `POST /api/v1/auth/register` |
| `/dashboard` | `pages/DashboardPage.tsx` | Authenticated | Health tiles, 3D motor preview, fault injector, telemetry preview | `/equipment`, `/alerts`, `/diagnoses` |
| `/equipment` | `pages/EquipmentListPage.tsx` | Authenticated | Asset grid, search input, status filter pills, motor cards | `GET /api/v1/equipment` |
| `/equipment/:id` | `pages/EquipmentDetailPage.tsx` | Authenticated | 3D component inspector with exploded toggle, nameplate specs, sensors | `GET /api/v1/equipment/:id`, `/sensors` |
| `/monitoring` | `pages/MonitoringPage.tsx` | Authenticated | Recharts dual-channel plot, fault simulator pills, rules table, rule modal | `GET/POST /monitoring/rules`, `POST /readings/batch` |
| `/alerts` | `pages/AlertsPage.tsx` | Authenticated | Anomaly table, severity/status filters, triage buttons, resolve modal | `GET /alerts`, `POST /alerts/:id/acknowledge`, `POST /alerts/:id/resolve` |
| `/diagnostics` | `pages/DiagnosticsPage.tsx` | Authenticated | 3-layer evidence explorer (Rule, ML, Graph), advisory banner, review modal | `GET /diagnoses`, `POST /diagnoses/generate`, `POST /diagnoses/:id/review` |
| `/maintenance` | `pages/MaintenancePage.tsx` | Authenticated | Work order queue, inspection details, attachment uploader, verify modal | `GET/POST /maintenance`, `/verify`, `/attachments` |
| `/admin` | `pages/AdminPage.tsx` | `platform_admin` | Pending approvals table, approve/reject buttons, immutable audit trail | `GET /admin/registrations`, `/approve`, `/audit-logs` |

---

## 6. Component migration map

| Existing Component | Proposed Destination | Migration Approach |
|---|---|---|
| `components/ui/button.tsx` | `components/glass/GlassButton.tsx` + CVA button | Preserve Radix/CVA API; add glass material variants |
| Inline card containers | `components/glass/GlassCard.tsx` | Abstract repeated `.glass-panel` into reusable primitive |
| Inline modal sheets | `components/glass/GlassDialog.tsx` | Wrap Radix Dialog with glass backdrop-blur & spring animation |
| `components/layout/AppLayout.tsx` | Enhanced `AppLayout.tsx` | Add light/dark/system theme switch; wrap sidebar in GlassSurface |
| Inline search/select controls | `components/glass/GlassInput.tsx` | Centralize frosted input styles with focus-visible specular highlights |
| Recharts time-series | Existing Recharts wrappers | Style tooltips, legends, and grid lines for light and dark glass |
| `components/motor3d/MotorScene.tsx` | `components/motor3d/MotorScene.tsx` | Keep lazy-loaded; update floating HUD overlays to GlassSurface |

---

## 7. Completion criteria

- [x] Every existing route is verified and documented with actual source files.
- [x] Role-based access rules and route guards are documented.
- [x] Shared UI primitives, icons, and fonts are inventoried.
- [x] API, authentication, and CSRF token handling mapped.
- [x] Procedural Three.js 3D motor and Recharts visualization mapped.
- [x] Quality baseline confirmed (`npm run build`, `npm run typecheck`, `npm run test` all passing).
- [x] Migration plan reconciled with actual React 19 + Tailwind v4 project structure.
