# MechTech — Phase 1 Implementation Requirements

**Phase:** Design system and Liquid Glass foundation  
**Prerequisite:** Phase 0 repository audit completed and reviewed  
**Scope:** Frontend design tokens, themes, glass CSS primitives and foundational tests  
**Themes:** Light, dark and system

> This specification is implementation-ready after the Phase 0 audit resolves the actual file paths, Tailwind generation/version, component conventions and package compatibility. Do not assume a file path or install/upgrade a package without checking the repository.

## 1. Objective

Create a centralized, reusable design foundation for the MechTech Liquid Glass interface. The result must provide consistent materials and semantic tokens across the application without changing business logic, backend APIs, authentication or database behavior.

## 2. Required outcomes

1. Semantic design tokens for both themes.
2. Light, dark and system theme preference.
3. Theme persistence and startup initialization without visible theme flash.
4. Reusable glass surface CSS variants.
5. A React GlassSurface primitive.
6. Reduced-transparency and unsupported-browser fallback.
7. Reduced-motion-aware foundational behavior.
8. A component playground or isolated demo page.
9. Unit tests for theme and component behavior.
10. Documentation of tokens, variants and usage rules.

## 3. Theme requirements

### Modes

- `light`: always use the light palette.
- `dark`: always use the dark palette.
- `system`: follow the operating system preference.

### Persistence

- Use the existing project preference mechanism if one exists.
- Otherwise use local storage for the non-sensitive UI preference.
- Do not store credentials, access tokens or personal data in the theme preference.
- Apply the effective theme before the first visible application paint where the existing app architecture permits.
- Listen for system preference changes only while `system` mode is active.
- Avoid hydration or first-render mismatches if server rendering is ever introduced.

### Semantic tokens

Define tokens for:

- App background.
- Primary and elevated surfaces.
- Primary, secondary and muted text.
- Accent and interactive states.
- Success, warning, danger and informational status.
- Glass background and border.
- Glass highlight and shadow.
- Blur levels.
- Corner radii.
- Focus ring.
- Overlay/scrim.
- Chart series and chart grid/axis colors.

Suggested initial palette, subject to contrast validation:

**Light**
- Canvas: `#F3F6FA`
- Surface: `#FFFFFF`
- Raised: `#E5EBF3`
- Text: `#182333`
- Secondary text: `#64748B`
- Accent: `#286CC4`

**Dark**
- Canvas: `#080D16`
- Surface: `#151E2C`
- Raised: `#253348`
- Text: `#F2F6FC`
- Secondary text: `#A0AEC0`
- Accent: `#83B9FF`

Status colors must be distinguishable and must not rely on color alone.

## 4. Glass material requirements

Implement four named variants:

| Variant | Initial blur target | Intended use |
|---|---:|---|
| subtle | 8px | Small controls and low-emphasis surfaces |
| standard | 16px | Cards and panels |
| floating | 24px | Navigation and floating toolbars |
| modal | 28px | Dialogs and prominent overlays |

These are initial design targets, not performance guarantees. Tune after browser/device testing.

Each variant should support:
- Theme-specific background opacity.
- Fine border.
- Restrained inner highlight.
- Controlled shadow.
- Optional specular gradient.
- Consistent radius.
- Fallback surface when blur is unsupported or reduced.

Do not apply `backdrop-filter` to every nested child. Avoid stacking multiple blurred surfaces.

## 5. GlassSurface component requirements

Proposed API; adapt naming to existing conventions:

```tsx
type GlassSurfaceProps = {
  variant?: "subtle" | "standard" | "floating" | "modal";
  asChild?: boolean;
  interactive?: boolean;
  className?: string;
  children: React.ReactNode;
};
```

Requirements:
- Render a semantic wrapper by default.
- Accept children and class names.
- Keep styling independent from business logic.
- Do not introduce click behavior unless the surface is explicitly interactive.
- Do not make a non-button surface keyboard-interactive by default.
- Preserve valid HTML semantics.
- Allow custom content and responsive sizing.
- Avoid embedding a second theme system inside the component.

If the project already has a polymorphic or Slot-based component convention, follow it rather than adding a new dependency.

## 6. CSS and Tailwind requirements

- First identify Tailwind v3 versus v4.
- Keep theme tokens in CSS custom properties.
- Use the project's existing CSS entry point.
- Avoid duplicating Tailwind configuration or importing global styles multiple times.
- Use `backdrop-filter` and `-webkit-backdrop-filter` where appropriate.
- Include an opaque/translucent fallback surface.
- Ensure focus rings and status indicators are visible on glass.
- Keep pseudo-element highlights pointer-transparent.
- Ensure decorative layers do not cover interactive content.

Do not use a v3 `@layer`/`@apply` recipe blindly in a v4 project. Choose syntax compatible with the audited setup.

## 7. Accessibility requirements

- Text contrast must be validated over representative backgrounds, not only flat token swatches.
- Controls need visible focus states.
- Glass decoration must not intercept pointer events.
- Status must include text/icon semantics, not color alone.
- Respect `prefers-reduced-motion`.
- Provide a reduced-transparency or solid-surface option where practical.
- Preserve labels, descriptions and error announcements for form controls.
- Do not use blur as the only distinction between interactive and non-interactive content.

## 8. Performance requirements

- Prefer opacity and transform for motion.
- Avoid animating blur radius continuously.
- Limit the number and area of simultaneous backdrop-filter surfaces.
- Do not place large glass overlays over continuously updating charts.
- Keep the 3D renderer out of the Phase 1 critical path.
- Measure on at least one lower-end or integrated-GPU device if available.
- Record before/after measurements rather than claiming an unmeasured improvement.

## 9. Suggested implementation files

Confirm exact paths during Phase 0.

```text
src/
├── app/
│   └── providers/
│       └── ThemeProvider.tsx
├── components/
│   └── glass/
│       └── GlassSurface.tsx
├── hooks/
│   └── useTheme.ts
├── styles/
│   ├── tokens.css
│   ├── themes.css
│   ├── glass.css
│   └── index.css
└── ...
```

Avoid creating duplicate providers, hooks or style entry points if equivalent project infrastructure already exists.

## 10. Implementation sequence

1. Review Phase 0 findings.
2. Confirm Tailwind version and CSS entry point.
3. Define semantic tokens.
4. Implement theme resolution and persistence.
5. Implement glass material variants.
6. Implement GlassSurface.
7. Add reduced-motion and reduced-transparency handling.
8. Create an isolated design-system preview.
9. Add unit/component tests.
10. Run type-check, lint, build and test scripts.
11. Record screenshots and any known limitations.

## 11. Testing requirements

### Theme tests

- Light mode applies the light token set.
- Dark mode applies the dark token set.
- System mode follows the OS preference.
- Explicit user preference overrides system mode.
- Preference persists after reload.
- System changes update the theme only in system mode.
- No incorrect theme flash in the supported startup flow.

### GlassSurface tests

- All variants render.
- Children render correctly.
- Custom class names are retained.
- Default semantics are valid.
- Decorative layers do not intercept pointer events.
- Interactive behavior is not added implicitly.
- Reduced-transparency fallback remains usable.

### Visual verification

Capture representative examples for:
- Light background.
- Dark background.
- Busy background.
- Behind a chart.
- Modal overlay.
- Mobile viewport.

Review contrast and visual hierarchy manually.

## 12. Phase 1 acceptance criteria

- [ ] Theme tokens are centralized.
- [ ] Light, dark and system modes work.
- [ ] Theme preference persists.
- [ ] Startup theme is applied without a visible incorrect-theme flash.
- [ ] Four glass variants are available.
- [ ] GlassSurface is reusable and documented.
- [ ] Unsupported/reduced transparency fallback works.
- [ ] Focus and status visibility are preserved.
- [ ] Reduced-motion behavior is supported.
- [ ] No backend/API/database behavior changed.
- [ ] Type-check, lint, build and relevant tests pass.
- [ ] Visual examples are reviewed in both themes.
- [ ] Phase 1 limitations and measurements are documented.

## 13. Agent execution constraints

Before editing:
- Read `00-repository-audit.md`.
- Read `current-frontend-map.md`.
- Read `dependency-compatibility.md`.
- Confirm the actual repository paths and versions.
- Report any contradiction between this specification and the repository.

During implementation:
- Make only Phase 1 changes.
- Do not migrate all pages in this phase.
- Do not introduce 3D refraction in this phase.
- Do not change backend files.
- Do not upgrade dependencies without approval and a documented need.

At completion, report:
- Files created/modified.
- Design tokens and variants implemented.
- Theme behavior.
- Tests and commands run, with actual results.
- Screenshots or preview route.
- Known issues and recommended next step.
