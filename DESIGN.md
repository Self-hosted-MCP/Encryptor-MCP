---
name: Encryptor MCP
description: A vault is a ruled index card, lent to an AI app until a stamped time.
colors:
  ink: "#1b2130"
  ink-soft: "#4d5566"
  stamp: "#4b3a8f"
  stamp-soft: "#ece8f7"
  marker: "#ffe27a"
  marker-2: "#e6defc"
  red: "#b5361f"
  red-soft: "#fbeae6"
  margin: "#e3897d"
  card: "#fdfdfb"
  desk: "#e7ebf1"
  rule: "#d6e1ef"
  lines: "#e8eef6"
  line: "#c9d2de"
  ink-dark: "#eef1f6"
  ink-soft-dark: "#a9b1c1"
  stamp-dark: "#b9a8f2"
  stamp-soft-dark: "#272240"
  marker-dark: "rgba(232,180,40,.42)"
  marker-2-dark: "rgba(150,125,240,.30)"
  red-dark: "#ff8a73"
  red-soft-dark: "#3a1d18"
  margin-dark: "#7a3b33"
  card-dark: "#191d27"
  desk-dark: "#10131a"
  rule-dark: "#262c3a"
  lines-dark: "#1f2430"
  line-dark: "#323a4b"
typography:
  headline:
    fontFamily: "ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Helvetica Neue, sans-serif"
    fontSize: "26px"
    fontWeight: 700
    lineHeight: "28px"
    letterSpacing: "-0.02em"
  title:
    fontFamily: "ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Helvetica Neue, sans-serif"
    fontSize: "20px"
    fontWeight: 700
    lineHeight: "28px"
    letterSpacing: "-0.01em"
  body:
    fontFamily: "ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Helvetica Neue, sans-serif"
    fontSize: "16px"
    fontWeight: 400
    lineHeight: "28px"
  body-strong:
    fontFamily: "ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Helvetica Neue, sans-serif"
    fontSize: "16px"
    fontWeight: 600
    lineHeight: "28px"
  label:
    fontFamily: "ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Helvetica Neue, sans-serif"
    fontSize: "13px"
    fontWeight: 400
    lineHeight: "28px"
  stamp:
    fontFamily: "ui-monospace, SF Mono, Menlo, Consolas, monospace"
    fontSize: "13px"
    fontWeight: 600
    lineHeight: 1.25
    letterSpacing: "0.08em"
  stamp-time:
    fontFamily: "ui-monospace, SF Mono, Menlo, Consolas, monospace"
    fontSize: "20px"
    fontWeight: 600
    lineHeight: 1.25
    letterSpacing: "0.04em"
  record-time:
    fontFamily: "ui-monospace, SF Mono, Menlo, Consolas, monospace"
    fontSize: "13px"
    fontWeight: 500
    lineHeight: "28px"
rounded:
  none: "0px"
  stamp: "3px"
  card: "4px"
  dot: "50%"
spacing:
  gutter-phone: "14px"
  gutter: "20px"
  card-gap: "22px"
  rule: "28px"
  margin-indent: "58px"
  margin-indent-phone: "40px"
  measure: "600px"
  measure-wide: "760px"
components:
  button-primary:
    backgroundColor: "{colors.ink}"
    textColor: "{colors.card}"
    rounded: "{rounded.card}"
    padding: "12px 18px"
    height: "44px"
  button-primary-hover:
    backgroundColor: "{colors.card}"
    textColor: "{colors.ink}"
  button-plain:
    backgroundColor: "{colors.card}"
    textColor: "{colors.ink}"
    rounded: "{rounded.card}"
    padding: "12px 18px"
    height: "44px"
  button-plain-hover:
    backgroundColor: "{colors.ink}"
    textColor: "{colors.card}"
  button-irreversible:
    backgroundColor: "{colors.card}"
    textColor: "{colors.red}"
    rounded: "{rounded.card}"
    padding: "12px 18px"
    height: "44px"
  button-irreversible-hover:
    backgroundColor: "{colors.red}"
    textColor: "{colors.card}"
  button-small:
    typography: "{typography.label}"
    rounded: "{rounded.card}"
    padding: "7px 12px"
    height: "36px"
  card:
    backgroundColor: "{colors.card}"
    textColor: "{colors.ink}"
    rounded: "{rounded.card}"
    padding: "28px 26px 28px 58px"
  stamp:
    textColor: "{colors.stamp}"
    typography: "{typography.stamp}"
    rounded: "{rounded.stamp}"
    padding: "5px 9px 4px"
  stamp-locked:
    textColor: "{colors.ink-soft}"
    rounded: "{rounded.stamp}"
  input:
    textColor: "{colors.ink}"
    rounded: "{rounded.none}"
    padding: "6px 2px"
    height: "44px"
  message-ok:
    backgroundColor: "{colors.stamp-soft}"
    textColor: "{colors.stamp}"
    rounded: "{rounded.card}"
    padding: "14px"
  message-error:
    backgroundColor: "{colors.red-soft}"
    textColor: "{colors.red}"
    rounded: "{rounded.card}"
    padding: "14px"
---

# Design System: Encryptor MCP

## Overview

**Creative North Star: "The Due-Date Card"**

Every page is a library index card laid on a cool grey desk. The card has hairline blue rules every 28px and one red margin line down its left side; text sits on the rules the way handwriting would. While a vault is open it is "lent" to an AI app, and the time it is due back is pressed onto the card in a violet rubber stamp at the top right. What changed is written line by line on the same card as a record, with the time in violet. Actions are written in ink; red appears only where something cannot be taken back.

The system is calm, slim and quiet: one card (sometimes two) per page, a single primary action in solid ink, everything else outlined or underlined. It deliberately refuses the shield-and-badge security dashboard: no shields, padlock heroes, status badges, gradients or glowing "secure" chrome. Security is told plainly by facts on the card (lent to, access, kept open, locks after), not by decoration.

All pages are server-rendered HTML with one inline stylesheet, no scripts and no external requests (strict Content Security Policy). Light is the default for everyone. Dark is opt-in: a no-script switch in the top bar (a form button with a 16px moon or sun icon and the word "Dark" or "Light") posts to the server, which remembers the choice in a cookie for one year in that browser. Dark tokens apply only under `:root[data-theme="dark"]` on the html element; the device's own setting is not followed.

**Key Characteristics:**
- Ruled card stock: blue hairlines on a 28px rule grid, one red margin line.
- Violet stamp ink for time and focus; ink black for actions; red only for the irreversible.
- Page titles underlined by a yellow highlighter stroke across the lower half of the text.
- System UI type, four sizes (13/16/20/26px), all on the 28px rule.
- Flat-ish paper: one soft card shadow, nothing else lifts.
- Small, square-ish corners (3-4px); inputs are bare underlines.

## Colors

Cool paper and ink, with two pigments that each carry one meaning: violet means time and attention, red means loss.

### Primary
- **Ledger Ink** (ink): every action. Solid fill for the one primary button per card, outline for secondary buttons, checked segment fill, checkbox accent, headings and body text. In dark mode it flips to a near-white ink (ink-dark).

### Secondary
- **Date-Stamp Violet** (stamp): the due-back stamp, record timestamps, the "open" dot, app names highlighted in row meta, the brand mark, success messages, and every focus ring. Its soft tint (stamp-soft) backs success messages only.

### Tertiary
- **Irreversible Red** (red): only "Delete for good" (outlined, fills on hover), the "Delete the trash for good" disclosure, and error messages (on red-soft). Never decoration.
- **Margin Red** (margin): a pale coral used only as a ruling: the vertical margin line on every card. It is paper printing, not a signal, and is kept visibly paler than Irreversible Red.

### Highlighter
- **Marker Yellow** (marker): only the highlighter stroke behind page titles (h1). In dark mode it is a translucent amber (marker-dark) so light ink stays readable over it.
- **Marker Lavender** (marker-2): a softer, thinner highlighter behind section titles (h2), the complement of the yellow and kin to the violet stamp. Dark: marker-2-dark.

### Neutral
- **Card Stock** (card): the card surface; also the text color on ink-filled buttons.
- **Desk** (desk): the page background around the cards.
- **Blue Rule** (rule): dividers between list rows and record lines.
- **Faint Lines** (lines): the repeating background rules on the card, deliberately lighter than the dividers so content lines read over them.
- **Soft Ink** (ink-soft): secondary text: fact labels, meta lines, notes, crumbs, nav links, input underlines, the locked stamp.
- **Pencil Line** (line): quiet borders: segment dividers, link underlines at rest, locked stamp and empty dot outlines.

### Named Rules
**The Red-Means-Loss Rule.** Irreversible Red appears only on actions that destroy data or on errors. If an action can be undone, it is ink.

**The Two Reds Rule.** Margin Red rules the paper; Irreversible Red warns. Never use Margin Red on a control, and never use Irreversible Red as a ruling.

**The Softer-Than-Dividers Rule.** The background rules (lines) stay lighter than the row dividers (rule) in both themes. The rules were softened at the user's request and kept; do not darken them back or remove them.

## Typography

**Body Font:** the device's system UI font (ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Helvetica Neue, sans-serif)
**Label/Mono Font:** the system monospace (ui-monospace, SF Mono, Menlo, Consolas)

**Character:** Plain, native type that feels like the person's own computer, with monospace used as stamp ink for times. No fonts are embedded or downloaded; this is a recorded product decision (PRODUCT.md, Brand Commitments) and can be revisited.

### Hierarchy
- **Headline** (700, 26px, 28px line, -0.02em): the card title, one per page, sitting on the top rule, its text marked by the yellow highlighter stroke. Balanced wrapping; long names break anywhere.
- **Title** (700, 20px, 28px line, -0.01em): section heads inside a card (Record, Trash, Vaults, Add a vault, Auto-lock, Connected AI apps).
- **Body** (400/600, 16px, 28px line): running text, fact values (600), labels and legends (600), buttons (600), row names (650).
- **Label** (400-500, 13px, 28px line): row meta, nav links, segment options, small buttons, record sub-lines.
- **Stamp** (600 mono, 13px uppercase, 0.08em): the stamp's caption ("Due back", "Locked"); the time itself in mono 20px, 0.04em.
- **Record time** (500 mono, 13px, 28px line) in violet: the "when" column of the record.

### Named Rules
**The Four-Size Rule.** Only 13, 16, 20 and 26px exist. A new role picks one of them.

**The On-The-Rule Rule.** Every text line box is 28px (body is 16px/1.75). Margins between blocks are 28px (the gap under the headline is 26.5px in code, a leftover from the removed 1.5px head rule), so text keeps landing on the card's rules.

**The Highlighter Rule.** Page titles (h1 only) get the marker stroke: a yellow band from 53% to 90% of the line height, angled 176deg, with uneven rounded ends (0.25em 0.6em 0.35em 0.5em), 0.18em padding and -0.1em margin, cloned on every wrapped line. Section titles (h2) get a softer lavender stroke (marker-2, 61% to 92%, angled 177deg, 0.2em padding); body text never gets either.

**The Mono-Is-Time Rule.** Monospace appears only for stamped times (the stamp and the record's when column).

## Layout

A single centered column on the desk: 600px wide (760px for list-heavy pages: control center, settings, browse files), with a 20px gutter. Above it, a slim header row holds the brand mark and name ("Encryptor MCP") at left and the text nav at right. Cards stack with a 22px gap.

Inside a card the vertical rhythm is the 28px rule: padding 28px top and bottom, the headline on the first rule, sections separated by 28px. Horizontally, content starts 58px in, to the right of the red margin line at 41px. Facts are a two-column definition grid (label in soft ink, value in 600 ink, 18px column gap). Actions are a wrapping row with 10px gaps, 28px below the content.

List rows (vaults, apps, trash, files) are at least 56px tall (two rules), with a name line and a 13px meta line, actions pushed right.

**Phone (560px and below):** gutters drop to 14px; the margin line moves to 27px and content starts 40px in; the keep-open segment becomes a 2x2 grid; action buttons stretch to share the row; list-row actions wrap under the text; the record table becomes stacked blocks with its Undo button pinned top-right.

## Elevation & Depth

Paper on a desk: the card is the only lifted object, with one soft, two-part shadow (a 1px contact shadow plus a long, diffuse ambient one). Everything inside the card is flat and separated by rules, not by layers. The stamp gets its double-struck look from inset rings, not elevation.

### Shadow Vocabulary
- **Card on desk** (`0 1px 2px rgba(27,33,48,.06), 0 8px 24px -12px rgba(27,33,48,.22)`; dark: `0 1px 2px rgba(0,0,0,.3), 0 10px 28px -14px rgba(0,0,0,.7)`): every card, nothing else.

### Named Rules
**The One-Lift Rule.** Only the card casts a shadow. Buttons, messages, rows and stamps stay flat.

## Shapes

Small, nearly square corners: 4px on cards, buttons, the segmented control and messages; 3px on the stamp. Inputs and selects have no box at all, only a 1.5px underline, like writing on a line. Strokes are 1.5px for meaningful edges (button borders, the stamp, input underlines) and 1px for dividers. The stamp is tilted -2deg and double-ruled (a 1.5px border plus an inset ring); a locked stamp loses the tilt and the second ring. The only circle is the 8px status dot.

## Components

### Buttons
- **Shape:** gently squared (4px), 1.5px border, 44px minimum height (36px for small), 600 weight, optional 18px stroke icon before the label.
- **Primary (ink):** solid ink with card-colored text. One per card: Unlock, Lock now, Sign in, Connect, Add vault.
- **Plain:** ink outline on transparent. Browse files, Open, Undo, Restore, Download, Save, Disconnect.
- **Irreversible (red):** red outline on transparent; only "Delete for good", behind a disclosure and a required confirm checkbox.
- **Hover:** each variant swaps fill and text (solid becomes outline, outline becomes solid) over 0.15s.
- **Focus:** a 2.5px violet outline, 2px offset, on every focusable element.
- **Text link button:** plain ink text with a pencil-line underline that darkens on hover (Remove in settings).

### Cards / Containers
- **Corner Style:** 4px.
- **Background:** card stock, printed with the faint 28px rules and the margin-red line.
- **Shadow Strategy:** the single card-on-desk shadow (see Elevation & Depth).
- **Internal Padding:** 28px 26px 28px 58px (phone: 28px 16px 28px 40px).

### Inputs / Fields
- **Style:** transparent, no box, 1.5px soft-ink underline, 44px tall; label above in 600 on its own rule.
- **Focus:** underline turns violet and thickens to 3px (border plus a 1.5px shadow).
- **Select:** same underline, with a small drawn chevron in soft ink.
- **Checkbox:** 20px, ink accent, label in 500 on the rule.
- **Segmented choice (keep open):** four equal cells in a 1.5px ink frame; the chosen cell fills with ink; focus shows a violet inset outline.

### Navigation
- **Style:** a slim top row: brand (violet tag icon plus "Encryptor MCP" in 650) at left, text links in 13px soft ink at right with 18px gaps.
- **States:** hover and current page turn ink with an underline (3px offset). Sign out and the light/dark switch are form buttons styled as the same link; the switch, last in the nav on every page, carries a 16px moon or sun stroke icon before its word.

### Messages
- **Success:** violet text on stamp-soft, 600 weight, 14px padding, 4px corners, at the top of the card.
- **Error:** red text on red-soft, same shape, announced as an alert.

### The Due-Back Stamp (signature)
The violet rubber stamp at the right end of the title row: uppercase mono caption "Due back" with the time below in 20px mono, 1.5px border, inset double ring, tilted -2deg, bottom-aligned beside the highlighted title (the row has no rule beneath it). On the unlock page it reads "Locked" in soft ink, untilted. A **mini** stamp (no ring, 13px) appears in vault rows on the control center, reading "Due" plus the time.

### The Record
The change log written on the card: a borderless table, one line per change on the rules, the time in violet mono, the change in body text with the app and purpose as a 13px soft-ink sub-line, and a small plain Undo at the right. Undone lines are struck through in soft ink.

### List Rows
Vaults, apps, trash and files: a 20px stroke icon (files) or status dot (vaults), name in 650, a 13px meta line, actions at the right, separated by 1px blue rules. An open vault's dot is filled violet; a locked one is an empty soft-ink ring.

## Do's and Don'ts

### Do:
- **Do** keep one solid-ink primary action per card; everything else is plain (outlined) or a text link.
- **Do** put the time a vault is due back in the violet stamp, in the title row, at the top right of the card.
- **Do** set every line box and block gap to the 28px rule.
- **Do** mark every page title with the highlighter stroke, and only page titles.
- **Do** keep the faint background rules (lines) lighter than the row dividers (rule) in both themes.
- **Do** use only 13/16/20/26px and the system UI font; monospace only for stamped times.
- **Do** give each light token its dark counterpart under `:root[data-theme="dark"]`; light is the default and dark is chosen only through the top-bar switch.
- **Do** keep pages script-free and self-contained: inline CSS, inline SVG icons, data-URI favicon.
- **Do** say "Encryptor MCP" wherever the name shows.

### Don't:
- **Don't** use shields, security badges, glowing locks, gradients or dashboard tiles; facts on the card carry the security story.
- **Don't** use Irreversible Red for anything that can be undone, and don't use Margin Red on a control.
- **Don't** draw a rule under titles; the highlighter replaced the red head line.
- **Don't** add a second shadow or lift anything but the card.
- **Don't** box inputs; they are underlines on the card.
- **Don't** embed or download fonts, or load anything from another origin.
- **Don't** preview PDFs in the page; they download only.
- **Don't** follow `prefers-color-scheme` or switch themes with script; the theme is the person's explicit choice, stored server-side in a cookie.

## Additions (2026-10-16)

- **Tagline:** under the "Encryptor MCP" name on every page, 13px ink-2: "Encrypted vaults for your AI agents. You hold the keys."
- **Vault lists** (Your vaults, Settings > Vaults): each vault gets 14px above and below, separated by a 1.5px dashed `--line` divider; other lists keep the hairline on the rule.
- **Settings** is a stack of cards: Vaults, Add a vault, Auto-lock, Safety, Connect an AI app (server only), Signed-in browsers with the 7-day sign-in log, About and help. Each vault has its own settings page (the AI may, default vault, its own auto-lock, name and folder, remove).

