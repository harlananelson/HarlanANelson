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
| **Tools** | Music (`:8444`) + reMarkable (`:9443`) | Tailscale + musiclab / phone-bridge |
| **About** | built-in copy | nothing |

Settings (gear) let you override each mode’s / tool’s URL.

### Converse (Voice + Assistant merged)

Type and mic are **one utility**. Open Converse for chat; **⋯ More → Switch to mic mode** (or a deep link) for voice-first Driving / Desk / Meeting.

### Tools (Music + reMarkable folded)

Opens the **last-used** tool immediately (default Music). Chip bar switches tools; **long-press** the Tools tab for a jump picker. Speech (Listen) and music capture stay separate pipelines.

### Deep links

| Intent | URL |
|--------|-----|
| Practice (last language) | `maat.html#practice` or `?mode=practice` |
| Practice Spanish | `maat.html#practice?lang=es` |
| Converse (type) | `#converse` |
| Converse (mic) | `#converse?input=mic` |
| Tools (last) | `#tools` |
| Tools → Music | `#tools?tool=music` or `?mode=music` |
| Tools → reMarkable | `#tools?tool=remarkable` or `?mode=remarkable` |
| Listen | `?mode=sermon` (alias: `listen`) |
| Legacy Voice / Assistant | `?mode=voice` / `?mode=assistant` |

`lang` allowlist: `es` \| `en` \| `ja` \| `sw`.  
`input` allowlist: `mic` \| `type`.  
`tool` allowlist: `music` \| `remarkable`.

### Public vs private

**Practice** embeds the public Languages hub (sandboxed iframe). Direct drill URLs stay shareable. Listen / Converse / Tools remain private-backend modes (Tailscale).

## What it is not

- **Not** a replacement for `live-translator.html`, `assistant.html`, or `languages.html` (bookmarks keep working).
- **Not** yet PR4 shell polish (fixed Converse landing, site navbar collapse, broader CSP).

## How to test

1. Open `/maat.html` after deploy (or local https).
2. Thumb bar: Listen · Practice · Converse · **Tools** · About (+ gear) — no separate Music / reMarkable tabs.
3. Tap **Tools** — last tool loads (Music by default).
4. Switch chips Music ↔ reMarkable; reopen Tools — last choice sticks.
5. Long-press **Tools** — picker; choose reMarkable.
6. `#tools?tool=music` and `?mode=remarkable` land correctly.
7. Practice / Converse / Listen unchanged; Practice works without Tailscale.

## Related

- `languages.html` — ES / EN / JA / SW drills  
- `assistant.html` — Converse surface  
- IA design: `~/projects/grok/projects/harlananelson/docs/maat-ia/maat-ia-design.md`
