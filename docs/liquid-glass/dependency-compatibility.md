# MechTech — Dependency Compatibility

**Status:** Compatibility policy and verification checklist.  
**Do not install or upgrade packages solely from this document.** The actual package versions must first be read from the repository lockfile.

## 1. Dependency principles

1. Keep the current working versions unless a concrete incompatibility blocks the implementation.
2. Use the existing package manager and lockfile.
3. Make dependency changes in small, reviewable groups.
4. Avoid duplicate animation, state, styling or chart libraries.
5. Verify peer dependencies before installation.
6. Record the reason for every version change.
7. Run build, type-check, tests and relevant visual checks after changes.

## 2. Expected technology inventory

| Capability | Preferred technology | Verification |
|---|---|---|
| UI framework | React | Check installed version |
| Build tool | Vite | Check installed version and plugins |
| Language | TypeScript | Check compiler version and strictness |
| CSS utilities | Tailwind CSS | Determine v3/v4 setup |
| UI primitives | shadcn/ui + Radix UI | Inspect generated components and peer deps |
| Animation | Existing Framer Motion or Motion | Avoid installing both unnecessarily |
| Icons | Lucide React | Check existing icon package |
| Server state | TanStack Query | Check existing hooks/provider |
| Client state | Zustand | Check if already used |
| Forms | React Hook Form + Zod | Check existing validation approach |
| Charts | Recharts / Apache ECharts | Use existing chart library where suitable |
| Graphs | React Flow | Verify package generation/version |
| 3D engine | Three.js | Check version |
| React 3D renderer | React Three Fiber | Verify React peer compatibility |
| 3D helpers | Drei | Verify Fiber/Three peer compatibility |
| Unit tests | Vitest | Check Vite integration |
| E2E tests | Playwright | Check browser setup |

## 3. Critical compatibility checks

### React and React Three Fiber

- Confirm the installed React major version.
- Confirm the installed `@react-three/fiber` major version.
- Verify peer dependency requirements from the package metadata.
- Common compatibility guidance: Fiber v8 targets React 18; Fiber v9 targets React 19. Verify the exact installed package release before acting.
- Verify Drei against the installed Fiber and Three.js versions.
- Do not force peer dependency resolution to silence a genuine mismatch.

### Tailwind CSS

Determine whether the project uses Tailwind v3 or v4.

For Tailwind v3, inspect the configuration file, content globs and PostCSS setup.

For Tailwind v4, inspect the CSS-first import/configuration and installed Vite/PostCSS integration.

Do not paste v3 configuration patterns into a v4 project or vice versa. Confirm that custom glass CSS, theme variables and utility classes are loaded once.

### shadcn/ui and Radix UI

- Inspect `components.json`.
- Inspect aliases and generated component locations.
- Preserve Radix keyboard behavior, focus management and accessible names.
- Prefer adding variants/wrappers over replacing generated primitives.
- Verify the actual dialog, sheet, dropdown and popover APIs before styling them.

### Framer Motion / Motion

- If `framer-motion` is already used, retain it for the initial migration.
- If starting fresh, evaluate the current `motion` package and `motion/react` imports.
- Do not install both packages without a documented reason.
- Centralize animation presets and support reduced motion.

### Three.js, Fiber and Drei

- Keep the 3D stack in a separate, lazy-loaded module.
- Confirm GLTF loader and asset pipeline behavior.
- Test transmission materials on target devices.
- Avoid updating React state every rendered frame.
- Reuse geometries and materials where possible.
- Verify the license and provenance of motor models and textures.

## 4. Commands for the audit agent

First identify the package manager and inspect scripts.

```bash
node --version
npm --version
```

For npm projects:

```bash
npm ls --depth=0
npm ls react react-dom vite typescript tailwindcss
npm ls three @react-three/fiber @react-three/drei
npm ls framer-motion motion
```

For pnpm projects, use the corresponding `pnpm list` / `pnpm why` commands. For Yarn, use `yarn why` and `yarn list` as appropriate.

Inspect scripts:

```bash
npm run
```

Do not run npm commands if the project uses a different package manager. Do not use `--force` or `--legacy-peer-deps` as a routine fix.

## 5. Compatibility record

Fill this table using actual lockfile/package metadata.

| Package | Installed version | Required peer range | Compatible? | Action |
|---|---|---|---|---|
| react | Not inspected | N/A | Unknown | Inspect |
| react-dom | Not inspected | React alignment | Unknown | Inspect |
| vite | Not inspected | Plugin compatibility | Unknown | Inspect |
| typescript | Not inspected | Tooling compatibility | Unknown | Inspect |
| tailwindcss | Not inspected | v3/v4 integration | Unknown | Inspect |
| framer-motion / motion | Not inspected | React compatibility | Unknown | Inspect |
| three | Not inspected | Fiber peer range | Unknown | Inspect |
| @react-three/fiber | Not inspected | React + Three | Unknown | Inspect |
| @react-three/drei | Not inspected | Fiber + Three | Unknown | Inspect |
| recharts | Not inspected | React compatibility | Unknown | Inspect |
| @xyflow/react | Not inspected | React compatibility | Unknown | Inspect |
| vitest | Not inspected | Vite compatibility | Unknown | Inspect |
| playwright | Not inspected | Browser/runtime | Unknown | Inspect |

## 6. Dependency change proposal format

For each proposed change, document:

- Current package and version.
- Proposed package and version.
- Why the change is needed.
- Peer dependency evidence.
- Breaking changes considered.
- Files/configuration affected.
- Validation commands and results.
- Rollback approach.

## 7. Completion criteria

- [ ] Package manager identified.
- [ ] Exact installed versions recorded.
- [ ] React/Fiber/Three compatibility checked.
- [ ] Tailwind generation/version identified.
- [ ] shadcn/Radix setup understood.
- [ ] Animation library duplication ruled out.
- [ ] No unnecessary dependency upgrades proposed.
- [ ] Build and test baseline recorded.
