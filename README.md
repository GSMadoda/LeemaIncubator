# Leema Township Incubator — website

The public site for **Leema Township Incubator**, the programme run by
**LEEMA Incubation NPC** from Bodirelo Industrial Park in Mogwase, North West.

The site is about the incubator and the enterprises in it: who they are, where
they trade, what they sell, and what they are asking the centre for. It follows
*LEEMA Incubation NPC · Brand guidelines, Version 1, September 2026* for colour,
type, layout, motion and voice.

One file, no build step, no framework, no third-party request at run time.
This repository is the site: `index.html` is served at the root.

## What's here

| Path | Purpose |
|------|---------|
| `index.html` | The whole site. Markup, styles, the cohort data, the circuit-board engine and the directory are inline. |
| `assets/leema-mark-white.png` | The supplied mark, keyed to transparency. White on ink — the primary version. |
| `assets/leema-mark-ink.png` | The same geometry in ink, for use on paper. |
| `assets/leema-share.png` | Open Graph card: the primary lockup on ink. |
| `assets/leema-type.css` | `@font-face` rules for the three brand faces. |
| `assets/fonts/` | Sora, Newsreader and IBM Plex Mono, self-hosted (Latin and Latin Extended). |

The mark is never redrawn, restyled or recoloured; the ink version is the same
alpha mask filled with `--ink-1000`.

## The cohort

Nine enterprises took intake in August and September 2026. Their profiles are
transcribed from LEEMA's portfolio report to SEDFA and live in the `COHORT`
array at the top of the inline `<script>`:

| Enterprise | Footing | Where |
|---|---|---|
| Reve P Catering | Incubatee | Pretoria (Ninapark), Gauteng |
| Moela Energies | Incubatee | Mahikeng, North West |
| TM Leasure Homes | Incubatee | Mahikeng, North West |
| Far Out Excellent Trading and Projects | Reseller | Mafikeng, North West |
| Lomatlhola Trading Enterprise | Reseller | Klerksdorp, North West |
| Thakaramo Security Solution and Training | Reseller | Kathu, Northern Cape |
| Lokissa Business Solutions | Reseller | Gauteng |
| Motsogapele Food Produce | Strategic partner | Mafikeng, North West |
| MIDC | Exploring | Johannesburg, Gauteng |

The directory searches every field, filters by footing, province and what each
enterprise is asking the centre for, and opens a full record in place.

### What is deliberately not published

Two things on each intake form stay off the public site:

- **The contact person, telephone number and email address.** Enquiries route
  through the centre on 014 403 5209 and `info@leemaincubation.co.za`.
- **Each enterprise's funding gap, cash-flow position and stated weakness.**
  Those were submitted to the incubator and its funder, not to the public.
  Publishing "biggest challenge: cash flow" beside a named business can cost it
  the contract it is trying to win.

The barrier data appears in **aggregate only** — seven of the nine name funding
or working capital, two name market access — which is the form in which it makes
the case for a funding intervention without naming which business is short of it.
If the owners consent to their details being listed, add `contact` fields to the
`COHORT` entries and a row to `record()`.

### Figures are computed, never typed

Every count on the portfolio page — by footing, by province, by what the cohort
is asking for — is tallied from the `COHORT` array at run time, so the charts and
the profiles cannot drift apart. Edit a profile and the figures follow.

Two figures in the source report's summary table disagree with its own profiles,
and this site follows the profiles:

- Relationship split. The summary says *5 resellers, no exploring*; the nine
  profiles show **4 resellers, 1 exploring** (plus 3 incubatees and 1 strategic
  partner).
- Geographic split. The summary says *North West 66%, Gauteng 33%*; the profiles
  give **North West 5 of 9, Gauteng 3, Northern Cape 1** — and the Northern Cape
  is missing from that summary altogether.

Jobs are reported as projections: fifteen across the cohort — ten at Reve P
Catering once the resort is operating, five at Far Out Excellent. Neither is
counted as a job created.

## The design

The mark is heavy square capitals whose counters are filled with printed-circuit
traces. The site is the rest of that board. Traces route on a fixed grid and turn
only at ninety degrees, signal packets run along them, the pointer energises what
it passes, and a click sends a square probe pulse outward.

Two rules from the guidelines are enforced by the code rather than described:

- **Nothing enters the mark's clear space.** The renderer draws the board, then
  clears the mark's live clear-space rectangle — a margin equal to the height of
  the E in LEEMA — out of every frame.
- **No scroll-triggered animation on anything a funder will see.** The board is
  substrate, never content: no figure, table or quotation moves. **Report mode**
  in the header goes further and stills the board itself; the choice persists in
  `localStorage`.

There are no gradients anywhere in the stylesheet, by grep.

`⌘K` (or `Ctrl K`, or `/`) opens a command palette over the whole page: every
enterprise by name, every section, every kind of support as a filter, and the
centre's phone number and address — all keyboard-driven.

## Accessibility and behaviour

- Every text pair meets WCAG AA; most meet AAA. Accent colours used as non-text
  markers clear 3:1.
- Heading levels run without skips. Every focusable control has an accessible
  name. Records open with Enter or Space as well as a click.
- `prefers-reduced-motion: reduce` stills the board and disables every transition.
- Pointer and probe effects are off on coarse-pointer devices; the board pauses
  when the tab is hidden.
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

---

LEEMA Incubation NPC · Stand 43, Factory A, Bodirelo Industrial Park, Mogwase,
North West · 014 403 5209 · info@leemaincubation.co.za
