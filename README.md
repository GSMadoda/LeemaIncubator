# Leema Township Incubator — website

The public site for **Leema Township Incubator**, the programme run by
**LEEMA Incubation NPC** in Mogwase, North West. It is a direct implementation of
*LEEMA Incubation NPC · Brand guidelines, Version 1, September 2026* — colour,
type, layout, motion and voice are the document's rules, not an interpretation
of them.

One file, no build step, no framework, no third-party request at run time.
This repository is the site: `index.html` is served at the root.

## What's here

| Path | Purpose |
|------|---------|
| `index.html` | The whole site. Markup, styles, the circuit-board engine and every instrument are inline. |
| `assets/leema-mark-white.png` | The supplied mark, keyed to transparency. White on ink — the primary version. |
| `assets/leema-mark-ink.png` | The same geometry in ink, for use on paper. |
| `assets/leema-share.png` | Open Graph card: the primary lockup on ink. |
| `assets/leema-type.css` | `@font-face` rules for the three brand faces. |
| `assets/fonts/` | Sora, Newsreader and IBM Plex Mono, self-hosted (Latin and Latin Extended). |

Both marks are derived from the artwork embedded in the guidelines PDF. The mark
is never redrawn, restyled or recoloured; the ink version is the same alpha mask
filled with `--ink-1000`.

## The idea

The mark is heavy square capitals whose counters are filled with printed-circuit
traces. The site is the rest of that board. Traces route on a fixed grid and turn
only at ninety degrees, signal packets run along them, the pointer energises what
it passes, and a click sends a square probe pulse outward.

Two rules from the guidelines are enforced by the code rather than described by it:

- **Nothing enters the mark's clear space.** The renderer draws the board, then
  clears the mark's live clear-space rectangle — a margin equal to the height of
  the E in LEEMA — out of every frame.
- **No scroll-triggered animation on anything a funder will see.** The board is
  substrate, never content: no figure, table or quotation ever moves. **Report
  mode** in the header goes further and stills the board itself. The choice
  persists in `localStorage`.

There are no gradients anywhere in the stylesheet, by grep.

## The instruments

Four parts of the page are working tools rather than pictures of tools.

- **Colour.** Every token is live. Click copies the `oklch()` value; shift-click
  copies the sRGB hex fallback.
- **Type.** A specimen with a body-size slider across all three faces. Drop below
  15px and the 15px floor fires as a visible failure.
- **The mark.** A width slider with the mark's real clear space drawn around it.
  Below the 120px floor the mark stops rendering and becomes the solid bar the
  guidelines say it becomes.
- **Voice.** The rules on page 07 made executable. It flags the banned words,
  exclamation marks, emoji, unnamed enterprises, claims without a number and
  uppercase in running text, and quotes the rule behind each finding. *Apply
  number conventions* rewrites amounts, dates, percentages and telephone numbers
  to South African form — `R1,250,000` becomes `R1 250 000`, `29/07/2025` becomes
  `29 July 2025`, `0144035209` becomes `014 403 5209`.

`⌘K` (or `Ctrl K`, or `/`) opens a command palette over the whole page: sections,
colour tokens, the phone number, the address and Report mode, all keyboard-driven.

## Content and unverified figures

All copy is drawn from the guidelines document and the organisation's own
correspondence quoted in it. Where a figure has not been verified against the
programme's register it is **not estimated** — it renders as a ruled slot naming
the number required, the same discipline the guidelines apply to image positions.
The single charted figure is the one the document states: three quarters of the
cohort names funding and market access.

Tier markers on the enterprise cards are labelled `placeholder` for the same
reason. The three enterprises named — Reve P Catering, Moela Energies, Thakaramo
Security Solution and Training — are the ones named in the guidelines.

To fill the slots, edit the data arrays at the top of the inline `<script>`:
`MEASURES`, `ENTERPRISES`, `TIERS`, `TOKENS` and `TRACK`. Nothing else needs to
change.

The one image position is a ruled placeholder naming the shot required. As the
guidelines put it: one commissioned day of photography at the Mogwase centre and
two or three enterprise sites would change the brand more than any other single
spend.

## Accessibility and behaviour

- Every text pair meets WCAG AA; most meet AAA. Accent colours used as non-text
  markers clear 3:1.
- Heading levels run 1 → 2 → 3 → 4 with no skips. Every focusable control has an
  accessible name.
- `prefers-reduced-motion: reduce` stills the board and disables every transition.
- The pointer and probe effects are off on coarse-pointer devices.
- The board pauses when the tab is hidden.
- No horizontal overflow at 390, 834, 1280 or 1440 pixels.
- Printing drops the board, the header and the rail.

## Run locally

```bash
python3 -m http.server 8000
# then open http://localhost:8000
```

## Deploy

Static files, so any host works with no build command.

**GitHub Pages** — Settings → Pages → Build and deployment → Source
*Deploy from a branch*, branch `main`, folder `/ (root)`, Save. The site then
publishes at `https://gsmadoda.github.io/LeemaIncubator/`. `.nojekyll` is present
so the files are served as-is.

**Anywhere else:**

```bash
npx wrangler deploy             # Cloudflare (wrangler.jsonc is configured)
netlify deploy --dir=. --prod   # Netlify
vercel --prod                   # Vercel
```

Every path inside `index.html` is relative, so the site works at a domain root
or under a subpath without editing.

For `www.leemaincubation.co.za`, point the domain at whichever host you pick and
add it as a custom domain there.

---

LEEMA Incubation NPC · Stand 43, Factory A, Bodirelo Industrial Park, Mogwase,
North West · 014 403 5209 · info@leemaincubation.co.za
