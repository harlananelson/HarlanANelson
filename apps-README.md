# My Apps — the home hub (`apps.html`)

One installable PWA that fronts the personal services running on the home
workstation. It's a thin shell: a bottom tab bar where each tab loads an
existing app page in an iframe — **no backend change**. Tab URLs are editable
and stored per-browser, so it also works as a launcher for anything added later.

| Tab | Loads | Backend it talks to | Server must be running |
|---|---|---|---|
| 🤖 Assistant | `tesla-assistant.html` (this site) | tesla-bridge, **tailnet-only** `…ts.net` | `bin/serve` (tmux `tesla-bridge`) |
| 🌐 Translate | `live-translator.html` (this site) | home-GPU translator, **`wss://…:8443/ws`** | `~/projects/biblestudy/server/run.sh` (tmux `translator-gpu`) |
| 📝 reMarkable | its own bridge UI (pre-filled `:9443`) | reMarkable phone-bridge, **tailnet `:9443`** | remarkable phone-bridge (`:8787`) |

**Every tab's backend is on the tailnet and must be running** (none auto-start
on boot). The Translate tab's GPU server (large-v3 on the 3090 + gemma
translation) is launched with `cd ~/projects/biblestudy && bash server/run.sh`
— it serves `wss://<host>.ts.net:8443/ws` directly with the tailnet TLS cert
(NOT behind `tailscale serve`). As of 2026-07-18 it's the one confirmed-working
CUDA whisper on this box (see the tesla-bridge README's GPU status).

Install: open `harlananelson.com/apps.html` on the device → **Add to Home
Screen** → a full-screen "My Apps" icon. Tabs lazy-load (a tab's app doesn't
start until first opened, so three mics/websockets/pollers don't all fire at
once). The reMarkable tab needs its URL set once in ⚙ Settings.

## Reaching it from a privacy phone (UP Phone, GrapheneOS, /e/OS, or any device)

The hub **page** is public static HTML served over HTTPS (Netlify), so it loads
anywhere. But almost every app it fronts lives **behind Tailscale** — the
Assistant bridge is tailnet-only, reMarkable is tailnet `:9443`, and the
translator points at a home-GPU `wss://` endpoint. So:

> The shell loads without Tailscale; the **tabs won't reach their backends
> until Tailscale is connected.** Symptom of "hub opens but tabs spin / show a
> red status / fail to connect" = Tailscale is off. Turn it on.

### A privacy phone's built-in VPN does NOT provide this

Privacy phones (the UP Phone included) ship an **anonymity/exit VPN** — it
routes your outbound traffic through the vendor's servers to hide your IP. That
is the opposite of what the hub needs, which is a path to your **own**
workstation.

- **Anonymity / exit VPN** (the built-in one): makes *you* anonymous to the
  public internet. Gives **no** route to your home machine → the tabs stay dead.
- **Mesh / overlay VPN** (Tailscale): connects **your own devices** over
  WireGuard so the phone reaches each tab's backend at its private address.
  This is the one you need.

**Catch: Android (and iOS) run one VPN tunnel at a time.** A privacy phone's
*always-on* exit VPN and Tailscale can't both be active — pick one. Options,
best-fit first:

1. **Tailscale, doing both jobs.** Reach the backends over Tailscale *and* get
   anonymity from a Tailscale **exit node** (your own, or its Mullvad
   integration). One tunnel, no conflict.
2. **Self-hosted WireGuard.** Tailscale is WireGuard underneath; run a WireGuard
   server on the workstation and import a config into the phone's WireGuard
   client. Fully self-hosted, no third-party coordinator — fits a privacy phone.
   You manage keys + a public endpoint yourself.
3. **Headscale.** Self-hosted Tailscale control server: keep the easy Tailscale
   client, drop Tailscale Inc. from the path.

None of these need anything from the phone vendor — the device just has to allow
a VPN app (the UP Phone and other de-Googled Android builds do; iPhone/iPad do).

### Why not just expose the hub's backends publicly?

You could (a Tailscale Funnel per service), but the Assistant bridge runs coding
agents that execute tools on the workstation — you don't want that on the open
internet behind a single token. Tailnet-only + a mesh VPN keeps every backend
reachable **only** from your own logged-in devices. The one exception is the
Tesla console browser (can't run Tailscale); that path uses a temporary public
funnel and isn't needed while driving. See the tesla-bridge README's
*Reachability* and *Security* sections for the per-service detail.
