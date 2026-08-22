# Maat

**URL:** https://harlananelson.com/maat.html  
**File:** `maat.html`

## Idea

*Right order for a whole digital life.* One app under **your** control — work and data held together, not scattered across silos.

**Maat** is an ancient word for right order and balance (not a living religious title we are borrowing lightly). We use it for a simple product idea: one place for personal tools, with the data under the person who lives it.

## What v1 is

A thin **installable shell** (PWA). Modes load **existing** apps in iframes — **no backend change**, no rewrite of Listen, bridge, or drills:

| Mode | Loads | Needs |
|------|--------|--------|
| **Listen** | `live-translator.html` | Tailscale + `biblestudy` GPU server for home quality |
| **Practice** | `languages.html` | Nothing private — public drills, shareable |
| **Converse** | `assistant.html` (± `?mode=mic`) | Tailscale + tesla-bridge |
| **reMarkable** | tailnet `:9443` | Tailscale + phone-bridge |
| **Music** | tailnet `:8444` | Tailscale + musiclab |
| **About** | built-in copy | nothing |

Settings (gear) let you override each mode’s URL (e.g. tailnet same-origin translator on iPad).

### Converse (Voice + Assistant merged)

Type and mic are **one utility** — input modality, not separate products. Open Converse for chat; use **⋯ More → Switch to mic mode** inside the page (or a deep link) for voice-first Driving / Desk / Meeting. “over” / “out” still work on the open channel.

### Deep links

| Intent | URL |
|--------|-----|
| Practice (last language) | `maat.html#practice` or `?mode=practice` |
| Practice Spanish | `maat.html#practice?lang=es` or `?mode=practice&lang=es` |
| Converse (type) | `#converse` or `?mode=converse` |
| Converse (mic) | `#converse?input=mic` |
| Listen | `?mode=sermon` (alias: `listen`) |
| Legacy Voice tab | `?mode=voice` → Converse + mic |
| Legacy Assistant tab | `?mode=assistant` → Converse |

`lang` is allowlisted to `es` \| `en` \| `ja` \| `sw`.  
`input` is allowlisted to `mic` \| `type`.

### Public vs private

**Practice** embeds the public Languages hub (sandboxed iframe; no `allow-top-navigation`). Direct URLs (`languages.html`, `*-speech-drill.html`) stay shareable for learners who should not see Tailscale tools. Listen / Converse / Music / reMarkable remain private-backend modes.

## What it is not

- **Not** a replacement for `live-translator.html`, `assistant.html`, or `languages.html` (those stay; bookmarks keep working).
- **Not** yet the final IA (Tools fold is PR3). Practice + Converse are PR1–PR2 of that plan.

## How to test

1. Open `/maat.html` (after deploy) or local file over https/localhost.
2. **Add to Home Screen** for full-screen Maat.
3. Confirm there is **one** Converse tab (no separate Voice + AI / Assistant).
4. Tap **Practice** — Languages with last language.
5. Open `maat.html#converse?input=mic` — voice-first assistant.
6. Open `maat.html?mode=voice` — same as Converse+mic (alias).
7. Inside Converse, **⋯ More** switches mic ↔ type without leaving Maat.
8. **Listen:** Tailscale on; start services as in About tab.

## Related

- `languages.html` — ES / EN / JA / SW drills, remembers last language  
- `assistant.html` — Converse surface (type + mic)  
- `apps.html` — older hub (Assistant / Translate / reMarkable)  
- IA design: `~/projects/grok/projects/harlananelson/docs/maat-ia/maat-ia-design.md`  
- Inventory: `~/projects/grok/projects/harlananelson/docs/do-everything-app-inventory.md`
