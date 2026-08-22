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

- `Referrer-Policy: no-referrer`, `Permissions-Policy` (mic self), `frame-src` CSP for `'self'` + known tailnet hosts
- Practice iframe sandboxed (no top-navigation)
- Opening Listen / Converse / Tools off Tailscale shows a connect banner; Practice still works

## How to test

1. Open `/maat.html` → lands on **Converse** (not last tab)
2. Thumb bar: Listen · Practice · Converse · Tools · ⚙️ only (no About tab)
3. ⚙️ shows About blurb + URL fields
4. Off Tailscale, tap Tools → banner; Practice still loads
5. Site navbar: no Spanish/English/Swahili/Japanese Drill entries; Languages + Maat + Listen remain
6. Deep links and legacy aliases still work

## Related

- IA design: `~/projects/grok/projects/harlananelson/docs/maat-ia/maat-ia-design.md`
- `languages.html`, `assistant.html`
