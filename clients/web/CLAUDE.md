# Web Client — Artic

Next.js 15 landing page + docs site. Dark-only. shadcn/ui + Tailwind CSS v4.

## Key Files

| File | Purpose |
|------|---------|
| `app/page.tsx` | Landing page (all sections composed) |
| `app/docs/layout.tsx` | Docs sidebar + content layout |
| `app/docs/*/page.mdx` | Documentation pages (10 total) |
| `components/landing/*` | Landing page section components |
| `components/docs/*` | Docs-specific components (sidebar, mobile nav) |
| `mdx-components.tsx` | MDX element styling overrides |
| `lib/docs-nav.ts` | Docs sidebar navigation structure |
| `app/globals.css` | Design system tokens (colors, animations) |

## Commands

- `bun dev` — dev server
- `bun run build` — production build
- `bun run lint` — ESLint

## Design System

Colors defined as CSS custom properties in `globals.css`:
- Orange: `--color-orange` (#DA7756), `-light` (#E8A080), `-text` (#F0C4A8), `-hover` (#C46A4A)
- Red: `--color-red` (#E4473B), `-light` (#F07870)
- Teal: `--color-teal` (#1D9E75), `-light` (#5DCAA5)
- Blue accent: `--color-blue-accent` (#378ADD), `-light` (#85B7EB)
- Surface bg: `--color-surface` (#0A0A0F)

## Conventions

- All colors from design system in globals.css, never hardcode hex in components
- Landing components in `components/landing/`
- Docs components in `components/docs/`
- MDX pages for docs, TSX for landing/jobs/blog
- Dark-only — no light theme, no toggle
- shadcn v2 (base-ui) — use `buttonVariants()` + Link, not `asChild`
- Base-ui uses `render` prop, not Radix `asChild`

## Adding Docs Pages

1. Create `app/docs/<slug>/page.mdx`
2. Add entry to `lib/docs-nav.ts`
3. MDX components auto-styled via `mdx-components.tsx`
