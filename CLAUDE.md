# Camp Life — Landing Page · Build Brief for Claude Code

> **This file is the project brief.** Read it fully before starting. It describes what to build, the design system, the content, and the conventions to follow. A complete working reference implementation lives in `reference/landing-demo-full.html` — open it in a browser to see the target.

---

## 1. What we're building

A **standalone marketing landing page** for **Camp Life** — the parent/family hub for **Camp Sol Taplin**, a summer camp operated by the **Michael-Ann Russell Jewish Community Center (MARJCC)** in Aventura, Florida.

This is **not** part of the main JCC WordPress site. It's a separate, fast, self-contained landing page. Target URL: `camplife.marjcc.org` or `marjcc.org/camplife` (TBD).

**Primary goal:** Inform families about Summer 2026 and drive **camp registrations**.
**Secondary goal:** Serve as the always-current reference for schedules, carpool, policies, and dates (replacing/complementing a printed PDF handbook).

**Audience:** Parents of campers ages 2–15. Warm, trustworthy, energetic tone. Bilingual community (English primary; the team is Spanish-speaking internally but all family-facing content is English).

---

## 2. ⚙️ DECISIONS — all settled

All three setup questions are answered. No need to ask the owner — proceed directly to building.

**Summary:** Astro (static) → GitHub → Render.com auto-deploy. PDF coexists as a download button.

### ✅ Tech stack — RECOMMEND ASTRO (static)
The owner delegated the stack choice to you, and hosting is now settled (GitHub + Render — see below). For a mostly-static marketing landing with light vanilla-JS interactivity and **no backend, no forms, no CMS** (the Register button links out to CampMinder), the right call is:

**→ Astro, configured as a static site (`output: 'static'`).**

Why: component-based authoring (clean one-file-per-section split), ships near-zero JS, builds to plain static HTML/CSS/JS, and Render has first-class support for Astro static sites. Don't use Next.js — it's overkill here and adds maintenance cost with no benefit. (If the owner later prefers zero tooling, plain HTML/CSS/JS is a valid fallback, but Astro is recommended.)

Port the reference into Astro components: one `.astro` component per section (`Hero.astro`, `WhyCST.astro`, `Tribe.astro`, `Carpool.astro`, etc.), a shared `Layout.astro`, and reusable bits (`Button.astro`, `SectionHead.astro`, `Eyebrow.astro`). Keep the vanilla JS from `src/scripts/main.js` — Astro ships it as-is via a `<script>` in the layout; no need to convert to a framework.

### ✅ Hosting — SETTLED: GitHub + Render.com
**Deploy flow:** push to GitHub → Render auto-deploys on every commit to the production branch.

Set it up as a **Render Static Site**:
- **Build command:** `npm install && npm run build`
- **Publish directory:** `dist` (Astro's default static output)
- **Auto-deploy:** on push to `main` (or whichever branch they designate as production)
- Render serves the static `dist/` over its CDN with free HTTPS.

Concrete tasks:
1. Initialize a Git repo (`git init`), sensible `.gitignore` already present (covers `node_modules/`, `dist/`, `.astro/`).
2. Create `render.yaml` (Render Blueprint) at the repo root so the service config is version-controlled and reproducible. Example:
   ```yaml
   services:
     - type: web
       name: camplife
       runtime: static
       buildCommand: npm install && npm run build
       staticPublishPath: ./dist
       autoDeploy: true
       # Optional SPA-style fallback not needed (multi-section single page).
       # Add a custom domain in the Render dashboard (e.g. camplife.marjcc.org).
   ```
3. Document in the README: connect the GitHub repo to Render once via the dashboard ("New → Static Site → pick the repo"), then every `git push` triggers a rebuild + deploy automatically.
4. Custom domain: they'll likely point `camplife.marjcc.org` (or similar) at Render — note the CNAME step in the README for whoever manages DNS (Hamilton/IT).

### ✅ PDF handbook — SETTLED
**Web and PDF coexist.** The page stays the primary, always-current source, and a **"Download PDF Guide"** button offers the printable handbook. Wire both "Download PDF Guide" buttons (final CTA + footer) to the PDF — place it in Astro's `public/` dir so it's served at `/Camp_Life_Parents_Handbook_2026.pdf`. Open in a new tab. Keep it as a download — don't render inline.

---

## 3. The reference implementation

`reference/landing-demo-full.html` is a **complete, working, single-file version** of the entire landing. Everything works: nav, scroll progress, reveal-on-scroll, TRIBE hover cards, horizontal day timeline, carpool location tabs, interactive pack checklist (with `localStorage`), activity filters, accordions, FAQ, dates timeline, final CTA, footer, WhatsApp FAB, and mobile sticky CTA.

**Your job is to port this into the chosen stack**, splitting it into maintainable components/partials, NOT to redesign it. The design is approved. Keep it faithful.

Pre-split source is provided for convenience:
- `src/styles/main.css` — all styles (CSS custom properties + components)
- `src/scripts/main.js` — all interactivity (vanilla JS, no dependencies)
- `reference/body.html` — the page markup (between `<body>` and the script)
- `src/assets/*.png` — logos and Sunny mascot images

---

## 4. Design system

### Brand colors (already in `:root` in main.css)
```
--sky:#29ABE2    --yellow:#FFC107    --navy:#1B3A8C    --navy-deep:#0E235C
--red:#E04A4A    --green:#3FA876     --coral:#FF7B5A
--cream:#FFFBF3  (warm off-white section bg)
--ink:#16203A    --ink-soft:#5A6485  (text)
```

### Typography (Google Fonts)
- **Display/headings:** Fraunces (serif, weights 400–900) — distinctive, warm, editorial.
- **Body/UI:** Plus Jakarta Sans (weights 400–800) — characterful geometric sans.
- **Handwritten accent:** Caveat (the red "script" labels, "Yalla!", etc.)

Do **not** swap these for Inter/Roboto/system fonts — the personality matters.

### Visual language
- Rounded cards (radius 12–28px), soft layered shadows, warm cream section alternation.
- Playful 3D "pushable" buttons (the yellow CTA has a `box-shadow` offset that compresses on `:active`).
- Sunny the dog mascot appears in hero, moments gallery, and final CTA.
- Wave divider between hero and content (inline SVG).
- Subtle paper-grain overlay on `body::before` for warmth.
- Each section has an `eyebrow` pill + serif headline (with one word highlighted in `--sky` or `--yellow` mark).
- Hover lifts, dashed rings, floating animations — but all respect `prefers-reduced-motion`.

---

## 5. Page structure (top → bottom)

The page is **ordered by what families need most**. The top zone is practical/actionable (the "essentials"); the bottom zone ("More about camp life") is aspirational/informational.

### Top zone — ESSENTIALS (priority)
| # | Section | Interactivity | Notes |
|---|---------|--------------|-------|
| 1 | Sticky nav + scroll progress | Scroll state, mobile menu | Links point to the essentials |
| 2 | Hero | Float, staggered fade-in | Camp Life + Sunny + Register |
| 3 | Trust bar | — | ACA, Jewish values, inclusion, vetted staff |
| 4 | **Quick Access Hub** | Hover lift | 9-card grid linking to all essentials — the heart of the page |
| 5 | **What to Bring** (checklist) | Checkboxes + localStorage + progress | Priority #1 — interactive pack list |
| 6 | **Carpool & Pickup** | Location tabs, animated pin | 2 windows, 3 locations, required strip, 3 auth steps |
| 7 | **Campanion tutorial** | Hover | 4 steps + App Store / Google Play buttons + phone mock |
| 8 | **Weekly Themes** | Hover | 9-week grid — `[FILL IN]` theme names/dates |
| 9 | **Forms** | Hover | Buy More T-Shirts + Birthday Celebration (external links) |
| 10 | **Lunch Menu** | — | Link/button to weekly menu |
| 11 | **Policies & Directory** | Hover | Camp Policies + Staff Directory (external links) |
| 12 | **Chat with Sunny** band | — | Dedicated WhatsApp CTA band (green) |

### Bottom zone — MORE ABOUT CAMP LIFE (secondary, after the "↓ More about camp life ↓" divider)
| # | Section | Interactivity | Notes |
|---|---------|--------------|-------|
| 13 | Why CST (6 benefit cards) | Hover lift | Emotional sell |
| 14 | Moments (photo mosaic) | Hover zoom | **[FILL IN] real camp photos** |
| 15 | TRIBE (5 pillars) | Hover reveal | Cultural framework |
| 16 | A Week at Camp (timeline) | Horizontal scroll | Day flow + special days |
| 17 | Activities (filter grid) | Filter pills | 6 categories |
| 18 | Code of Conduct (accordion) | Expand/collapse | ACA tags |
| 19 | Communication (4 cards) | Hover lift | Channels |
| 20 | Important Dates (timeline) | Hover slide | Key dates |
| 21 | FAQ (accordion) | Expand/collapse | 5 questions |
| 22 | Final CTA | Reveal | Register + Download PDF |
| 23 | Footer | — | 4 columns |
| 24 | WhatsApp FAB + mobile sticky CTA | — | Always visible |

**The 9 Quick Access Hub items are the essentials the owner prioritized:** What to Bring · Get Campanion · Camp Policies (link) · Staff Directory (link) · Weekly Themes · Forms · Carpool · Lunch Menu · Chat with Sunny.

One component per section is the right split. The Hub is its own component with a 9-card grid; cards link to in-page sections (`#pack`, `#carpool`, etc.) or external URLs (policies, staff directory, t-shirts, birthday, lunch, WhatsApp).

---

## 6. Content & data

All real content is already in the reference. Key facts (verify before launch):

- **Camp dates:** June 8 – August 7, 2026 (9 weeks)
- **Carpool:** drop-off 8:30–9:00 AM / pickup 3:30–4:00 PM. Three locations: Scheck Family Plaza, Hillel, Savage Playground.
- **Extended care (Kid Connection):** 7:30–8:30 AM / 4:00–6:00 PM (Fri until 5:30 PM)
- **Key dates:** Parents Orientation May 28 · Spring discount deadline May 31 · T-Shirt Distribution June 3 (4:00–7:30 PM, JCC Gym) · First day June 8 · Last day Aug 7
- **Contacts:** Reception 305.932.4200 x110, campsoltaplin@marjcc.org · Director Marleny Rosemberg (MarlenyR@marjcc.org) · Asst Director Ariel Hutnik (arih@marjcc.org)
- **WhatsApp Sunny:** (305) 916-3358 · link `https://wa.me/message/MMN7EUES6WOUF1`
- **Registration:** `https://marjcc.org/campregistration`
- **TRIBE pillars:** Tikkun (תיקון), Ruach (רוח), Israel (ישראל), Bayit (בית), Echad (אחד)
- **Mascot:** Sunny (the dog)

### ⚠️ `[FILL IN]` / `[ASSUMPTION]` markers — must be resolved before launch
Search the codebase for these literal strings:
- **External link URLs** — these are placeholders (`https://marjcc.org/PATH-...`) and must be replaced with real URLs:
  - `PATH-camp-policies` → Camp Policies page/PDF
  - `PATH-staff-directory` → Staff Directory page
  - `PATH-buy-tshirts` → Buy More T-Shirts form
  - `PATH-birthday-form` → Birthday Celebration form
  - `PATH-lunch-menu` → weekly Lunch Menu page/PDF
  - Campanion App Store / Google Play links — verify the real store URLs
- **Weekly Themes** — all 9 week theme names + descriptions are `[FILL IN]` (dates are pre-filled per the 9-week calendar but confirm).
- **Moments gallery** — replace Sunny placeholder tiles with **real camp photos**.
- **Carpool locations 2 & 3 (Hillel, Savage)** — assigned camps + entry routes are `[FILL IN]`.
- **July 3 holiday** — marked `[ASSUMPTION]`; confirm whether camp is closed.
- **FAQ** — age ranges and lunch-by-camp details marked `[FILL IN]`.

---

## 7. Technical requirements

- **Performance:** This is a landing — it must be fast. Lighthouse 95+ on mobile. Lazy-load images below the fold. Compress the Sunny PNGs (they're ~300–500KB each; run through an optimizer or convert to WebP with PNG fallback).
- **Responsive:** Works 320px → 1440px+. Breakpoints at 1024px and 640px are already in the CSS. Mobile gets a hamburger menu + sticky bottom Register CTA.
- **Accessibility:** Semantic HTML, alt text on all images, keyboard-navigable accordions/tabs, visible focus states, `prefers-reduced-motion` respected (already handled in CSS). Add ARIA where the interactive widgets need it (accordions: `aria-expanded`; tabs: `role="tab"`/`aria-selected`).
- **SEO:** Proper `<title>`, meta description (in reference), Open Graph + Twitter card tags (ADD — not in reference yet), favicon, sitemap, structured data (`SummerCamp` / `Organization` schema.org JSON-LD is a nice-to-have).
- **No tracking by default.** If the JCC wants analytics, add privacy-friendly (Plausible/Fathom) or GA4 per their decision — leave a clear, commented placeholder.
- **Forms:** There is no form on the page — the Register CTA links out to the existing CampMinder registration URL. Don't build a form.
- **Browser support:** Modern evergreen browsers. `IntersectionObserver`, `localStorage`, CSS custom properties all assumed available.

---

## 8. Conventions & house style (from the team)

- All **family-facing copy is in English**, even though internal notes may be in Spanish.
- Honor brand colors and fonts exactly — they're locked.
- Keep the **TRIBE** framework (Tikkun/Ruach/Israel/Bayit/Echad). Do **not** reintroduce older "PACK" or "B'Yachad" framing anywhere.
- Verify program availability / never invent specifics. Where a detail isn't confirmed, use a `[FILL IN]` marker rather than guessing.
- Don't add features the brief doesn't mention without flagging them.

---

## 9. Suggested build steps for Claude Code

1. Scaffold a new **Astro** project (`npm create astro@latest`), choose minimal/empty template, TypeScript optional.
2. Set `output: 'static'` in `astro.config.mjs` (it's the default, but be explicit).
3. Create `src/layouts/Layout.astro` holding `<head>` (fonts, SEO/OG meta, schema.org JSON-LD from `reference/seo-meta-snippet.html`), the global CSS import, and the shared `<script>` (porting `src/scripts/main.js`).
4. Move `src/styles/main.css` into the Astro project (e.g. `src/styles/main.css`, imported in the layout). Keep the CSS custom properties intact.
5. Port section by section from `reference/body.html` into `.astro` components — one per section (Nav, Hero, TrustBar, WhyCST, Moments, Tribe, Week, Carpool, Pack, Activities, Conduct, Communication, Dates, FAQ, FinalCTA, Footer, plus the WhatsApp FAB and mobile sticky CTA). Compose them in `src/pages/index.astro`.
6. Factor out reusable bits: `Button.astro`, `SectionHead.astro`, `Eyebrow.astro`, `Card.astro` where it reduces repetition.
7. Put images in `src/assets/` and use Astro's `<Image>` for optimization (or `public/` if you keep them static). Compress the heavy Sunny PNGs / offer WebP.
8. Put `Camp_Life_Parents_Handbook_2026.pdf` in `public/` and wire the two "Download PDF Guide" buttons to `/Camp_Life_Parents_Handbook_2026.pdf` (new tab).
9. Add favicon, OG image, sitemap (`@astrojs/sitemap`), and the schema.org JSON-LD.
10. Verify against `reference/landing-demo-full.html` at desktop + mobile.
11. `npm run build`, run Lighthouse on the `dist/` output, fix perf regressions (target 95+ mobile).
12. Add `render.yaml` (Blueprint) at repo root, `git init`, commit, push to GitHub.
13. Document the one-time Render connection (New → Static Site → select repo → it reads `render.yaml`) and the CNAME step for the custom domain. After that, every push auto-deploys.

---

## 10. What "done" looks like

- Pixel-faithful to the reference at desktop and mobile.
- All interactive widgets work (nav, tabs, accordions, filters, checklist + persistence, scroll reveal).
- "Download PDF Guide" buttons link to the handbook PDF and work.
- All `[FILL IN]` markers either resolved or clearly listed for the owner.
- Lighthouse 95+ mobile.
- One-command build (`npm run build`) + working **GitHub → Render auto-deploy** via `render.yaml`.
- README explaining how to edit content (especially dates, carpool, FAQ) for next summer, plus the Render/GitHub deploy flow and custom-domain CNAME step.

---

*Questions about camp specifics → the project owner (CST/MARJCC Hebraica team). Design is approved; build faithfully and flag anything ambiguous.*
