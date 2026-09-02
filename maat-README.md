# Maat

**URL:** https://harlananelson.com/maat.html  
**File:** `maat.html`

## Idea

*Right order for a whole digital life.* One app under **your** control — work and data held together, not scattered across silos.

## Destinations (≤ 4 + gear)

| Mode | Loads | Needs |
|------|--------|--------|
| **Listen** | `live-translator.html` | Tailscale + biblestudy GPU |
| **Practice** | `languages.html` | Public — no Tailscale |
| **Converse** | `assistant.html` (± mic) | Tailscale + tesla-bridge |
| **Tools** | Music `:8444` + reMarkable `:9443` | Tailscale + home services |
| ⚙️ gear | About + URL overrides | — |

**Cold open** always lands on **Converse** (deep links override). Last destination is not restored.

### Site navbar

Public site nav points at **Maat**, **Languages**, and **Listen** (`maat.html?mode=sermon`) — not four separate drill links. Individual `*-speech-drill.html` URLs remain bookmarkable.

### Deep links

| Intent | URL |
|--------|-----|
| Practice / Spanish | `#practice` / `#practice?lang=es` |
| Converse type / mic | `#converse` / `#converse?input=mic` |
| Tools | `#tools?tool=music\|remarkable` |
| Listen | `?mode=sermon` |
| Legacy | `?mode=voice\|assistant\|music\|remarkable` |

Unknown `mode` / `lang` / `input` / `tool` values are ignored (allowlists).

### Security / degradation

- `Referrer-Policy: no-referrer`; `frame-src` CSP for `'self'` + known tailnet hosts
- Practice iframe sandboxed (no top-navigation) — stops accidental shell navigation; not an XSS boundary for same-origin drills
- **Failure-driven** banners only: if a private iframe times out / errors, the shell warns (Tailscale or service). No false “connect Tailscale” banner just because Maat is served from harlananelson.com
- Deep links append `lang=` / `mode=` onto the existing Settings URL (they do not replace a custom host)

## How to test

1. Open `/maat.html` → lands on **Converse** (not last tab)
2. Thumb bar: Listen · Practice · Converse · Tools · ⚙️ only (no About tab)
3. ⚙️ shows About blurb + URL fields
4. Public PWA origin + Tailscale up: Converse/Tools load with **no** false connect banner
5. Services truly down: Tools/Listen/Converse banner after iframe timeout; Practice still loads
6. Settings Converse URL on a tailnet host survives `#converse?input=mic` (host kept, `mode=mic` added)
7. Site navbar: no per-language Drill entries; Languages + Maat + Listen remain
8. Deep links and legacy aliases still work

## Related

- **Feature map (agent GUI):** [`FEATURE-MAP.md`](FEATURE-MAP.md) — how to reach each destination, DOM ids, deep links, traps. YAML lookup in `.features/`.
- IA design: `~/projects/grok/projects/harlananelson/docs/maat-ia/maat-ia-design.md`
- `languages.html`, `assistant.html`
