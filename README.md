# Camp Life Landing — Project Handoff

This folder is a ready-to-build package for the **Camp Sol Taplin "Camp Life" landing page**, prepared to hand to **Claude Code**.

## What's in here

```
camplife_handoff/
├── CLAUDE.md                      ← START HERE. Full build brief for Claude Code.
├── README.md                      ← This file.
├── CONTENT.md                     ← Editable content reference (dates, contacts, copy).
├── reference/
│   ├── landing-demo-full.html     ← The complete working demo. Open in a browser.
│   └── body.html                  ← Just the page markup (pre-split).
├── src/
│   ├── styles/main.css            ← All styles (CSS variables + components).
│   ├── scripts/main.js            ← All interactivity (vanilla JS, no deps).
│   └── assets/*.png               ← Logos + Sunny mascot.
└── public/
    └── Camp_Life_Parents_Handbook_2026.pdf   ← Printable handbook (PDF download target).
```

## How to use this with Claude Code

1. Open this folder in your terminal.
2. Run Claude Code in the folder (`claude` if you have the CLI installed).
3. Tell it: **"Read CLAUDE.md and build the landing page."**
4. It builds the site in **Astro** (static), wires up the PDF download, and sets up **GitHub → Render.com** auto-deploy. No setup questions — everything's decided.
5. Review, fill in the `[FILL IN]` markers, push to GitHub, and connect the repo to Render once.

**All decisions are locked in (CLAUDE.md §2):**
- **Stack:** Astro, static output (`output: 'static'`).
- **Hosting:** GitHub → Render.com Static Site, auto-deploy on push. `render.yaml` blueprint included.
- **PDF:** web + a "Download PDF Guide" button — wired to the handbook PDF in `public/`.

## Deploy flow (once Claude Code builds it)

1. Push the repo to GitHub.
2. In Render: **New → Static Site → pick the GitHub repo**. Render reads `render.yaml` (build: `npm install && npm run build`, publish: `dist`).
3. Every `git push` to `main` auto-rebuilds and redeploys.
4. Custom domain (e.g. `camplife.marjcc.org`): add it in the Render dashboard and point a CNAME in DNS (your IT — Hamilton — handles this).

## Want to preview the design first?

Open `reference/landing-demo-full.html` in any browser. That's exactly what the finished landing should look and behave like — everything is interactive (the checklist even saves your progress). Claude Code's job is to rebuild this cleanly in a real project structure, not to redesign it.

## Before launch — resolve these

Search the project for `[FILL IN]` and `[ASSUMPTION]`:
- Real camp photos for the "Moments" gallery (currently Sunny placeholders)
- Hillel & Savage Playground assigned camps + entry routes
- July 3 holiday confirmation
- FAQ age ranges / lunch-by-camp details

## Questions

Camp specifics → the CST / MARJCC Hebraica team. Design is approved.
