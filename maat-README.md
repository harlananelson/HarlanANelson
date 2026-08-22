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
| **Voice + AI** | `assistant.html?mode=mic` | Tailscale + tesla-bridge |
| **Assistant** | `assistant.html` | same bridge |
| **reMarkable** | tailnet `:9443` | Tailscale + phone-bridge |
| **Music** | tailnet `:8444` | Tailscale + musiclab |
| **About** | built-in copy | nothing |

Settings (gear) let you override each mode’s URL (e.g. tailnet same-origin translator on iPad).

### Deep links

| Intent | URL |
|--------|-----|
| Practice (last language) | `maat.html#practice` or `?mode=practice` |
| Practice Spanish | `maat.html#practice?lang=es` or `?mode=practice&lang=es` |
| Listen | `?mode=sermon` (alias: `listen`) |
| Voice mic | `?mode=voice` |
| Assistant | `?mode=assistant` |

`lang` is allowlisted to `es` \| `en` \| `ja` \| `sw`.

### Public vs private

**Practice** embeds the public Languages hub (sandboxed iframe; no `allow-top-navigation`). Direct URLs (`languages.html`, `*-speech-drill.html`) stay shareable for learners who should not see Tailscale tools. Listen / Voice / Music / reMarkable remain private-backend modes.

## What it is not

- **Not** a replacement for `live-translator.html`, `assistant.html`, or `languages.html` (those stay; bookmarks keep working).
- **Not** yet the final IA (Converse merge + Tools fold are later PRs). Practice-in-shell is PR1 of that plan.

## How to test

1. Open `/maat.html` (after deploy) or local file over https/localhost.
2. **Add to Home Screen** for full-screen Maat.
3. Tap **Practice** — should load Languages with last language (or `?lang=`).
4. Open `maat.html#practice?lang=es` — should land on Spanish drills.
5. **Listen / Voice:** Tailscale on; start services as in About tab.
6. Configure bridge URL + token inside the Voice/Assistant page (same as today).

## Related

- `languages.html` — ES / EN / JA / SW drills, remembers last language  
- `apps.html` — older hub (Assistant / Translate / reMarkable)  
- IA design: `~/projects/grok/projects/harlananelson/docs/maat-ia/maat-ia-design.md`  
- Inventory: `~/projects/grok/projects/harlananelson/docs/do-everything-app-inventory.md`
