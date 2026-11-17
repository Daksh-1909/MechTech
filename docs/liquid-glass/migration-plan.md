# MechTech — Liquid Glass Migration Plan

**Scope:** Complete frontend visual transformation  
**Themes:** Light, dark and system preference  
**Approach:** Incremental migration; preserve existing domain logic and backend contracts.

## 1. Goals

- Establish a distinctive MechTech visual language inspired by Apple's Liquid Glass.
- Deliver consistent light and dark appearances.
- Create reusable accessible glass components.
- Migrate all existing frontend routes and workflows.
- Add restrained motion and selected advanced 3D refraction.
- Preserve authentication, authorization, API behavior and diagnostic correctness.
- Maintain responsive performance on lower-end devices.

## 2. Non-goals

This initiative does not authorize:

- Rewriting the backend.
- Changing database schemas.
- Changing diagnostic rules or ML behavior.
- Changing knowledge-graph reasoning.
- Changing registration approval or authorization policy.
- Replacing every chart or graph library.
- Rebuilding all routes solely to match a proposed folder structure.
- Adding paid dependencies or services.
- Making every surface transparent or refractive.

## 3. Migration principles

1. Audit before editing.
2. Design tokens before page styling.
3. Primitive components before feature migration.
4. One feature area at a time.
5. Preserve component contracts where practical.
6. Keep data fetching out of visual primitives.
7. Use CSS glass for ordinary surfaces; reserve WebGL refraction for selected 3D elements.
8. Keep a working fallback for reduced transparency and unsupported devices.
9. Test light and dark modes during every phase.
10. Keep each change reversible.

## 4. Phases and exit gates

### Phase 0 — Repository audit

**Work**
- Inspect repository, routes, dependencies, styles, auth, API and tests.
- Establish baseline build/test results.
- Map existing files to the target architecture.
- Identify blockers and migration risks.

**Deliverables**
- `00-repository-audit.md`
- `current-frontend-map.md`
- `dependency-compatibility.md`
- Updated migration plan

**Exit gate:** Evidence-based repository map and approved file-level migration strategy.

### Phase 1 — Design system

**Work**
- Define light/dark/system theme behavior.
- Add semantic color, surface, border, radius, shadow and blur tokens.
- Add glass material variants.
- Add typography, spacing and elevation rules.
- Add reduced-transparency and reduced-motion behavior.
- Build a visual playground/demo route or isolated component page.

**Deliverables**
- `tokens.css`
- `themes.css`
- `glass.css`
- `motion.css`
- Theme provider
- Glass surface primitive
- Design-system documentation

**Exit gate:** Tokens and materials are validated on representative backgrounds in both themes.

### Phase 2 — Reusable components

**Work**
- Build GlassSurface, GlassPanel, GlassCard and GlassButton.
- Add input, select, badge, tooltip, dropdown and dialog variants.
- Add navigation components.
- Preserve Radix accessibility and shadcn component APIs where possible.
- Add component tests and visual states.

**Exit gate:** Components support loading, disabled, hover, focus, active and error states as appropriate; light/dark and keyboard checks pass.

### Phase 3 — Application shell and authentication

**Work**
- Migrate auth layouts.
- Migrate app shell, sidebar, navbar and responsive navigation.
- Add theme control and persistence.
- Add page transitions and notification surface.
- Preserve registration approval, session handling and role guards.

**Exit gate:** Authentication and navigation workflows pass regression tests.

### Phase 4 — Feature migration

Migrate actual existing features in dependency order:

1. Dashboard.
2. Equipment inventory and detail.
3. Monitoring.
4. Diagnostics.
5. Predictions and explanations.
6. Knowledge graph.
7. Maintenance.
8. Notifications.
9. User administration.
10. Settings.

For each feature:
- Record existing behavior.
- Identify API/data dependencies.
- Update shared surfaces and controls.
- Preserve loading, empty, error and permission states.
- Verify data formatting and status semantics.
- Run focused tests before moving on.

**Exit gate:** All existing routes and workflows are migrated and regression-tested.

### Phase 5 — 3D and advanced motion

**Work**
- Lazy-load motor scene.
- Verify model license and component hierarchy.
- Add camera controls and component selection.
- Add diagnostic highlighting driven by backend results.
- Add contextual glass panels.
- Use Drei transmission materials only for selected visual elements.
- Provide static/2D fallback.

**Exit gate:** Selection and overlays are correct; performance is acceptable on a representative lower-end device.

### Phase 6 — QA and optimization

**Work**
- Test desktop, tablet and mobile.
- Test light, dark and system modes.
- Test keyboard and screen-reader behavior.
- Test reduced motion and reduced transparency.
- Check contrast and status communication.
- Profile blur, chart and 3D performance.
- Run frontend and backend regression suites.
- Verify no API or database changes occurred accidentally.

**Exit gate:** Acceptance checklist passes and known limitations are documented.

## 5. Feature migration worksheet

Copy one worksheet per feature.

```text
Feature:
Existing route:
Existing source files:
User roles:
Current workflows:
API endpoints:
WebSocket/events:
Loading state:
Empty state:
Error state:
Permission-denied state:
Existing tests:
Proposed shared components:
Proposed feature changes:
Files to modify:
Files to create:
Regression tests:
Acceptance evidence:
```

## 6. Rollback strategy

- Keep changes in small Git commits or isolated branches.
- Do not mix dependency upgrades with visual changes.
- Preserve existing components until their replacements pass tests.
- Prefer feature flags or route-level toggles for risky visual migrations.
- Keep the original chart and 3D data paths intact.
- Revert the smallest failing change rather than resetting unrelated work.

## 7. Risk register

| Risk | Impact | Mitigation |
|---|---|---|
| Version mismatch | Build failure | Audit lockfile and peer ranges |
| CSS/theme leakage | Inconsistent appearance | Scoped tokens and component variants |
| Excessive backdrop filters | Poor frame rate | Limit blur layers and profile |
| WebGL cost | Slow/failed 3D experience | Lazy-load and provide fallback |
| Reduced readability | Incorrect interpretation | Contrast and solid chart surfaces |
| Auth regression | Security risk | Preserve guards and test roles |
| API regression | Broken workflows | Keep API contracts unchanged |
| Large migration | Difficult rollback | Migrate incrementally |

## 8. Release acceptance checklist

- [ ] All current routes accounted for.
- [ ] Existing user workflows preserved.
- [ ] Light/dark/system modes work.
- [ ] Theme preference persists.
- [ ] No theme flash on startup.
- [ ] Glass components are reusable.
- [ ] Keyboard and focus behavior works.
- [ ] Reduced motion is respected.
- [ ] Reduced transparency fallback works.
- [ ] Mobile layouts are usable.
- [ ] Charts remain readable.
- [ ] 3D is lazy-loaded and has a fallback.
- [ ] Diagnostic display is grounded in actual results.
- [ ] Authentication and role checks are unchanged.
- [ ] Frontend tests and build pass.
- [ ] Backend regression tests pass.
- [ ] Performance findings are documented.
