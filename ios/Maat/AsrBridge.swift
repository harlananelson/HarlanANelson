import WebKit
import UIKit

/// JS → native: webkit.messageHandlers.maatAsr.postMessage({cmd, language, session})
/// native → JS:  window.__maatAsr({type, text, ...})
///
/// NOT BUILT (2026-11-15 review, R1-02/03/05/06): written on a machine with no
/// Xcode. Needs a device test; see the PR description.
final class AsrBridge: NSObject, WKScriptMessageHandler, WKNavigationDelegate, WKUIDelegate {
    weak var webView: WKWebView?
    private let asr = OnDeviceASR()
    /// The frame that sent `start`. Listen runs in a cross-origin iframe, and
    /// `window.__maatAsr` lives THERE; evaluateJavaScript(_:) alone targets the
    /// main frame (maat.html), which defines nothing, so every event was
    /// dropped (R1-02).
    private var asrFrame: WKFrameInfo?
    /// Bumped by every start and stop. A start that was suspended on the
    /// speech-permission prompt checks it afterwards, so a Stop (or a newer
    /// Start) pressed meanwhile cancels it. Touched only inside the
    /// @MainActor Tasks below.
    private var generation = 0

    private static let shellHosts: Set<String> = ["harlananelson.com", "www.harlananelson.com"]
    private static let tailnetHost = "harlan-b550-aorus-pro-ac.taila21a91.ts.net"

    /// Only Maat's own main frame, or Listen on the tailnet :8443 page, may drive the mic (R1-06).
    private func isTrusted(_ frame: WKFrameInfo) -> Bool {
        let o = frame.securityOrigin
        guard o.protocol == "https" else { return false }
        let host = o.host.lowercased()
        if frame.isMainFrame { return AsrBridge.shellHosts.contains(host) }
        // NOT DONE (review #119 item d): a Listen frame on a machine set in
        // Settings is a different host and is refused here. Trusting "the host
        // the shell actually loaded" needs the shell (maat.html, main frame
        // only) to tell native which host it chose, e.g. a new `cmd` on
        // maatAsr. That message does not exist yet, so it is not guessed at.
        return host == AsrBridge.tailnetHost && o.port == 8443
    }

    func userContentController(_ userContentController: WKUserContentController,
                               didReceive message: WKScriptMessage) {
        guard message.name == "maatAsr" else { return }
        guard isTrusted(message.frameInfo) else { return }
        let body = message.body as? [String: Any] ?? [:]
        let cmd = (body["cmd"] as? String) ?? ""
        let frame = message.frameInfo
        Task { @MainActor in
            switch cmd {
            case "start":
                let lang = (body["language"] as? String) ?? "en-US"
                let session = (body["session"] as? String) ?? "transcript"
                self.generation += 1
                let gen = self.generation
                self.asrFrame = frame
                let ok = await asr.authorize()
                // Stop (or a newer Start) ran while the permission prompt was up.
                guard gen == self.generation else { return }
                guard ok else {
                    post(["type": "error", "text": "Speech recognition not authorized"])
                    return
                }
                do {
                    try asr.start(locale: lang, session: session) { [weak self] event in
                        self?.post(event)
                    }
                    // Keep the iPad awake while recording: an idle auto-lock
                    // backgrounds the app and stops the mic (R1-03).
                    UIApplication.shared.isIdleTimerDisabled = true
                    self.post(["type": "status", "state": "listening",
                               "engine": "apple-on-device"])
                } catch {
                    UIApplication.shared.isIdleTimerDisabled = false
                    self.post(["type": "error", "text": error.localizedDescription])
                }
            case "stop":
                self.generation += 1
                asr.stop()
                UIApplication.shared.isIdleTimerDisabled = false
                post(["type": "status", "state": "stopped"])
            default:
                break
            }
        }
    }

    private func post(_ event: [String: Any]) {
        guard let data = try? JSONSerialization.data(withJSONObject: event),
              let json = String(data: data, encoding: .utf8) else { return }
        let js = "window.__maatAsr && window.__maatAsr(\(json));"
        // Deliver to the frame that asked (Listen), not the main frame.
        webView?.evaluateJavaScript(js, in: asrFrame, in: .page) { _ in }
    }

    // MARK: WKNavigationDelegate (R1-06): the shell has no browser chrome, so
    // a main-frame navigation away from Maat cannot be undone. Keep Maat's own
    // pages in the web view; open everything else in Safari.

    func webView(_ webView: WKWebView,
                 decidePolicyFor navigationAction: WKNavigationAction,
                 decisionHandler: @escaping (WKNavigationActionPolicy) -> Void) {
        guard let url = navigationAction.request.url,
              let scheme = url.scheme?.lowercased(), scheme == "http" || scheme == "https" else {
            decisionHandler(.allow)      // about:blank, blob:, data: and friends
            return
        }
        let isMain = navigationAction.targetFrame?.isMainFrame ?? true   // nil target = new window
        if isMain && !AsrBridge.shellHosts.contains((url.host ?? "").lowercased()) {
            UIApplication.shared.open(url)
            decisionHandler(.cancel)
            return
        }
        decisionHandler(.allow)
    }

    // MARK: WKUIDelegate (R1-05). Without these WKWebView answers confirm()
    // with false and ignores alert()/prompt() and window.open, so Maat's
    // "Listen is recording. Leave it?" guard silently swallowed every tab tap.

    /// Returns false when there is nothing to present on. The caller MUST then
    /// call the JS completion handler itself: WKWebView waits for it forever,
    /// which would freeze the page's confirm()/prompt().
    private func present(_ alert: UIAlertController) -> Bool {
        let scene = UIApplication.shared.connectedScenes
            .compactMap { $0 as? UIWindowScene }
            .first { $0.activationState == .foregroundActive }
        var top = scene?.windows.first { $0.isKeyWindow }?.rootViewController
        while let next = top?.presentedViewController { top = next }
        guard let presenter = top else { return false }
        presenter.present(alert, animated: true)
        return true
    }

    func webView(_ webView: WKWebView,
                 runJavaScriptAlertPanelWithMessage message: String,
                 initiatedByFrame frame: WKFrameInfo,
                 completionHandler: @escaping () -> Void) {
        let a = UIAlertController(title: nil, message: message, preferredStyle: .alert)
        a.addAction(UIAlertAction(title: "OK", style: .default) { _ in completionHandler() })
        if !present(a) { completionHandler() }
    }

    func webView(_ webView: WKWebView,
                 runJavaScriptConfirmPanelWithMessage message: String,
                 initiatedByFrame frame: WKFrameInfo,
                 completionHandler: @escaping (Bool) -> Void) {
        let a = UIAlertController(title: nil, message: message, preferredStyle: .alert)
        a.addAction(UIAlertAction(title: "Cancel", style: .cancel) { _ in completionHandler(false) })
        a.addAction(UIAlertAction(title: "OK", style: .default) { _ in completionHandler(true) })
        if !present(a) { completionHandler(false) }
    }

    func webView(_ webView: WKWebView,
                 runJavaScriptTextInputPanelWithPrompt prompt: String,
                 defaultText: String?,
                 initiatedByFrame frame: WKFrameInfo,
                 completionHandler: @escaping (String?) -> Void) {
        let a = UIAlertController(title: nil, message: prompt, preferredStyle: .alert)
        a.addTextField { $0.text = defaultText }
        a.addAction(UIAlertAction(title: "Cancel", style: .cancel) { _ in completionHandler(nil) })
        a.addAction(UIAlertAction(title: "OK", style: .default) { _ in
            completionHandler(a.textFields?.first?.text)
        })
        if !present(a) { completionHandler(nil) }
    }

    /// window.open / target=_blank: hand the URL to Safari instead of dropping it.
    func webView(_ webView: WKWebView,
                 createWebViewWith configuration: WKWebViewConfiguration,
                 for navigationAction: WKNavigationAction,
                 windowFeatures: WKWindowFeatures) -> WKWebView? {
        if let url = navigationAction.request.url,
           let scheme = url.scheme?.lowercased(), scheme == "http" || scheme == "https" {
            UIApplication.shared.open(url)
        }
        return nil
    }
}
