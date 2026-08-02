# Maat

**URL:** https://harlananelson.com/maat.html  
**File:** `maat.html`

## Idea

*Right order for a whole digital life.* One app under **your** control — work and data held together, not scattered across silos.

**Maat** is an ancient word for right order and balance (not a living religious title we are borrowing lightly). We use it for a simple product idea: one place for personal tools, with the data under the person who lives it.

## What v1 is

A thin **installable shell** (PWA). Modes load **existing** apps in iframes — **no backend change**, no rewrite of sermon or bridge:

| Mode | Loads | Needs |
|------|--------|--------|
| **Sermon** | `live-translator.html` | Tailscale + `biblestudy` GPU server for home quality |
| **Voice + AI** | `tesla-assistant.html?mode=mic` | Tailscale + tesla-bridge |
| **Assistant** | `tesla-assistant.html` | same bridge |
| **About** | built-in copy | nothing |

Settings (gear) let you override each mode’s URL (e.g. tailnet same-origin translator on iPad).

Deep link: `maat.html?mode=sermon` | `voice` | `assistant` | `about`.

## What it is not

- **Not** a replacement for `live-translator.html` or `tesla-assistant.html` (those stay; bookmarks keep working).
- **Not** the language drills — public multi-language practice is **`languages.html`**.

## How to test

1. Open `/maat.html` (after deploy) or local file over https/localhost.
2. **Add to Home Screen** for full-screen Maat.
3. **Sermon / Voice:** Tailscale on; start services as in About tab.
4. Configure bridge URL + token inside the Voice/Assistant page (same as today).

## Related

- `languages.html` — ES / EN / JA / SW drills, remembers last language  
- `apps.html` — older hub (Assistant / Translate / reMarkable)  
- Inventory: `~/projects/grok/projects/harlananelson/docs/do-everything-app-inventory.md`
