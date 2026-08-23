# Unified visual system and layout contract

Status: design contract candidate  
Working direction pending Management interview: calm technical editorial,
with expressive overview graphics and solemn evidence-first governance views.

## 1. Design principles

1. **Evidence before decoration.** Visual polish clarifies identity, state,
   hierarchy, and causality. Evidentiary regions avoid glass, gradients, and
   ambiguous ornament.
2. **One product, several modes.** Documentation, governance, reports,
   curation, review, and discussion share one shell and component grammar.
3. **Overview, inspect, act.** Dashboards summarize; record pages prove;
   action flows change state. Critical mutations never live inside charts.
4. **Calm at distance, dense on demand.** Default pages breathe; expert tables
   have a persistent compact mode without reducing targets or legibility.
5. **Status is language.** Text, icon, and shape carry meaning; color reinforces.
6. **Motion explains continuity.** Motion is brief, interruptible, and removed
   under `prefers-reduced-motion`; no decorative background motion.

## 2. Brand character

The visual metaphor is a well-made engineering atlas: warm neutral paper-like
surfaces, deep ink, precise teal navigation, and restrained semantic colors.
It should feel contemporary and unmistakably technical without imitating an
IDE, cockpit, or generic SaaS dashboard.

Typography uses a highly legible variable sans for UI and prose, a technical
mono for identifiers/code only, and tabular numerals for metrics. Prefer
locally hosted open fonts with complete Arabic/Devanagari/CJK fallback; if the
font budget cannot cover this, use a tested system stack rather than loading
multiple remote families.

## 3. Semantic color tokens

Illustrative light values; final values require automated contrast proof in
light, dark, and forced-colors modes.

```css
:root {
  color-scheme: light dark;
  --color-canvas: #f5f4ef;
  --color-surface: #ffffff;
  --color-surface-subtle: #eceae3;
  --color-ink: #172126;
  --color-ink-muted: #566269;
  --color-border: #c9cdca;
  --color-accent: #006d73;
  --color-accent-strong: #004e53;
  --color-focus: #7c3aed;
  --color-info: #1769aa;
  --color-success: #18794e;
  --color-warning: #9a6700;
  --color-danger: #b42318;
  --color-neutral: #65727a;
}
```

No semantic state is assigned a raw palette token. Components consume
`status-verified-*`, `status-stale-*`, `status-blocked-*`, etc., with tested
foreground/background/border/icon combinations. Red is reserved for blocking,
invalid, destructive, or security-critical conditions—not ordinary negative
chart values.

Contrast gates: 4.5:1 for normal text, 3:1 for large text and UI graphics,
visible focus at 3:1 against adjacent colors. Forced-colors uses system colors
and preserves borders/icons. Print uses black/white patterns and labels.

## 4. Type, spacing, and shape

```text
Type scale: 12, 14, 16, 18, 22, 28, 36, 48 px with 1.2–1.65 line-height
Space scale: 2, 4, 8, 12, 16, 24, 32, 48, 64 px
Radius: 4 controls, 8 records, 12 overview cards; pills only for short tags
Borders: 1 px default, 2 px focus/selected; shadows only for overlays
Prose measure: 65–78 characters; data regions may be full width
Targets: 44×44 CSS px or WCAG spacing exception with equivalent separation
```

Heading hierarchy is semantic, with one H1. Technical values never use
forced uppercase. Long IDs wrap only at safe delimiters; full values remain
copyable and accessible.

## 5. Responsive shell

- **Wide (≥1280):** 12-column grid; 272 px collapsible domain navigation;
  max-width prose; full-bleed data lane; optional 320 px contextual rail.
- **Medium (768–1279):** compact side rail; eight columns; context becomes
  drawer; tables use priority columns plus row detail.
- **Narrow (320–767):** one column; top app bar and domain drawer; identity
  and typed states remain visible; actions move to labelled action sheet.
- **Print:** navigation/actions removed; record identity, exact ref/digest,
  as-of, classification, verification, URL, and page numbers repeated.

Use container queries and logical properties. Reflow must work at 320 CSS px,
400% browser zoom, and 200% text zoom. Horizontal scroll is limited to explicit
code/data scrollers; the document itself never overflows.

## 6. Shared application shell

1. skip link;
2. product/release identity;
3. global domains and omnibox;
4. locale, theme, density, notifications, and identity controls;
5. contextual breadcrumb;
6. record identity/state header;
7. local tabs (`Overview`, `Relations`, `Evidence`, `Reviews`, `History`,
   `Raw` as applicable);
8. main content and optional context rail;
9. source/freshness footer.

The shell renders meaningful content with no JavaScript. Capability islands
load only when the view declares them or the user invokes them.

## 7. Record identity and typed status

Every record header shows:

- kind and stable ID, title, release/version;
- source-of-truth versus derived-view label;
- source REF/digest, as-of, freshness, schema, classification;
- separate rows for implementation, claim, validation, Acceptance,
  checkpoint, integration, trust, transport, and permission where relevant;
- copy canonical link and exact-version link.

Badges use text + icon + border form. Example: `Implemented`, `Not accepted`,
`Checkpoint required`, `Integration pending`, `Current baseline`. A single
green `Done` is forbidden.

## 8. Component families

- app shell, breadcrumb, domain/local tabs, command palette;
- identity header, typed status group, freshness/classification banners;
- record field list, evidence citation, source locator, digest/REF control;
- data table, priority-column responsive row, filter bar, saved view;
- relationship graph, synchronized edge table/tree, legend, minimap;
- timeline, audit event, diff, code block, log viewer;
- report KPI, chart, finding, validation run, evidence manifest;
- curation comparison, annotation, thread, proposed change, submission receipt;
- conversation transcript, context manifest, AI provenance label;
- alert, toast, inline validation, skeleton, empty/error/offline/tombstone;
- modal/confirmation only when a separate page would break task continuity.

Tables remain primary for audit/comparison. Cards serve overviews only.
Virtualized tables retain accessible headers, row counts, keyboard traversal,
and export the exact filtered/as-of set.

## 9. Graph and diagram visual grammar

- node shape denotes entity kind; icon and text repeat it;
- edge stroke/pattern plus label denotes relation and assertion state;
- arrowheads and labels express direction; color is redundant;
- current selection has focus ring and synchronized table row;
- legend remains visible; deep links select and focus nodes;
- clusters progressively disclose 1–2 hops; cycles are explicit;
- redaction, missing, stale, conflicting, inferred, and rejected are distinct;
- SVG diagrams have title/description and textual adjacency/sequence views.

Raster imagery is allowed for editorial overview mood only, never as the sole
carrier of a route, state, identifier, diagram, or evidence relation.

## 10. Interaction and governance safety

Irreversible or authoritative actions show actor, assignment/authority source,
exact candidate/contract/prerequisite closure/digests, side effects, recovery,
and confirmation summary. Stale baseline, signature failure, lost authority,
network ambiguity, or optimistic-concurrency conflict fails closed.

Permission-denied controls may remain visible in disabled/read-only form when
their explanation aids comprehension. Hidden controls are not security.
Offline mode never submits, approves, accepts, integrates, or publishes; it can
export a clearly marked draft.

## 11. Themes and localization

Light, dark, high-contrast/forced-colors, and print are complete themes, not
filters over one palette. User selection can override OS and is independent of
locale. Motion and density are separate preferences.

Layouts use logical inline/block properties. Arabic mirrors navigation,
drawers, and directional affordances when meaning permits; code, hashes,
identifiers, timestamps, diffs, chronology, and graph semantics remain LTR or
unmirrored with bidi isolation. CJK line breaking, Devanagari metrics, long
German/Russian strings, and 60% pseudo-expansion are component fixtures.

## 12. Accessibility acceptance

WCAG 2.2 AA is the minimum. Gates include valid landmarks/headings, skip link,
visible focus, logical tab order, modal trap/return, no keyboard-only dead end,
screen-reader names/descriptions/live regions, linked error help, non-color
status, target size, reduced motion, 320 px reflow, 200% text zoom, 400% zoom,
and accessible graph/chart alternatives.

Automated HTML/axe/contrast checks are necessary but not sufficient. Manual
journeys cover keyboard, NVDA/Firefox, VoiceOver/Safari, zoom, forced colors,
and Arabic mixed-direction content.

## 13. Loading and failure states

Skeletons match final geometry and do not announce shimmer. Empty states
distinguish no entities, no filter matches, and no permission. Partial data
names missing sources. Stale/offline views show exact last-known as-of/ref.
Retry preserves filters, drafts, selection, and idempotency key. Unsupported
schema, redaction, tombstone, and invalid signature have distinct states.
