# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users
Everyday people and tech-savvy people, equally (maintainer, 2026-10-16). Anyone who keeps private files in a Cryptomator vault and works with an AI app or agent: simple by default for people with no technical knowledge, with details (paths, modes, connected apps, server settings) available for self-hosters and developers. Usually at their own computer, sometimes on a phone through the hosted version.

## Product Purpose
Encryptor-MCP lets any AI app or agent open Cryptomator vaults: read, search and write files with the vault's own keys, while the vault password never passes through the chat. The main way to use it is talking to the AI. The pages exist for the person's own moments: unlocking (typing the password), seeing what is open and for how long, browsing files without the AI, undoing what the AI changed, emptying the trash, and settings. Success: the person always knows what is open, what the AI did, and can take it back.

## Positioning
The only way to give an AI access to an end-to-end encrypted Cryptomator vault where the password is typed only by the person, keys live only in memory, everything locks by itself, and every AI change is logged and undoable. Stays fully compatible with Cryptomator's own apps (same vaults, same format). Works with Cryptomator vaults; not made by or affiliated with Cryptomator.

## Operating Context
- Runs two ways from one code base: on a computer for AI apps (stdio, pages on 127.0.0.1) and on a server (VPS, hosting, own server) with a passphrase login over HTTPS, for phones and web AI apps.
- Pages: unlock (one-time link, 5 minutes), vault status (open/locked, time left, lock now), browse files, control center home (all vaults), settings (vaults, modes, auto-lock), AI-app login (pick vaults, allow changes), sign-in.
- Often opened from an AI app mid-conversation; the person types a password and returns to the chat.
- Mac extras: native password and approval boxes, "Show in Finder" mount.

## Capabilities and Constraints
- Server-rendered HTML with inline CSS only: no scripts, no external fonts or requests (strict Content Security Policy). Every value escaped.
- Light and dark (follow the device), phone-friendly, works in any browser.
- Vault modes: full, read, hidden (hidden from the AI only). Read-only sessions.
- Undo, versions and trash live inside the vault, encrypted.
- Plain words in English; no jargon on the main path.

## Brand Commitments
Name: "Encryptor MCP" everywhere people see it (pages, titles, the app name), not just "Encryptor" (maintainer, 2026-10-16). Repository and package: Encryptor-MCP / encryptor-mcp. No logo, colors or fonts exist yet; the look is open (the maintainer asked for clean, straightforward, slim, smart). Must not imitate Cryptomator's branding. Type: the device's own system UI font, no embedded fonts (decided 2026-10-16 under the maintainer's standing rule to take the safer, simpler option: fast, native on every device, nothing to download; a custom face can be revisited later).

## Evidence on Hand
No users, testimonials or audits yet. Test vaults only (tests/fixtures). Do not claim audits, user counts or certifications.

## Product Principles
1. Calm and in control: the person should always see at a glance what is open, for how long, and what the AI did.
2. The password and the keys belong to the person: nothing on a page ever suggests typing a password into the chat.
3. Everything is reversible except what the person explicitly confirms.
4. Simple by default, details on request: one obvious action per screen, expert information present but quiet.
5. Same everywhere: computer, server and phone show the same pages and words.

## Accessibility & Inclusion
Readable contrast in light and dark, full keyboard use, labels on every input, works with screen readers and at large text sizes; no information by color alone.
