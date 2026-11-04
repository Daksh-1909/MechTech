# MechTech Frontend

React + TypeScript + Vite frontend for MechTech.

## Scripts

```powershell
npm run dev        # Vite dev server on http://localhost:5173
npm run build      # type-check and production build
npm run typecheck  # TypeScript project build
npm run lint       # oxlint
npm run format     # Prettier
npm test           # Vitest
npm run test:e2e   # Playwright
```

The dev server proxies `/api` and `/ws` to `http://127.0.0.1:8000`.

## UI

- Tailwind CSS v4 is configured through `@tailwindcss/vite` and `src/index.css`.
- shadcn/ui configuration is in `components.json`; primitives live in
  `src/components/ui`.
- The design tokens use a dark industrial palette (navy/charcoal surfaces,
  teal accent, amber warning, red critical, green normal) with Inter and
  JetBrains Mono fonts bundled locally via Fontsource.

> Note: the shadcn CLI currently writes `import { cn } from "cn"` on this
> setup. If you add components, change it to `@/lib/utils`.
