import WebKit

/// JS → native: webkit.messageHandlers.maatAsr.postMessage({cmd, language, session})
/// native → JS:  window.__maatAsr({type, text, ...})
final class AsrBridge: NSObject, WKScriptMessageHandler {
    weak var webView: WKWebView?
    private let asr = OnDeviceASR()

    func userContentController(_ userContentController: WKUserContentController,
                               didReceive message: WKScriptMessage) {
        guard message.name == "maatAsr" else { return }
        let body = message.body as? [String: Any] ?? [:]
        let cmd = (body["cmd"] as? String) ?? ""
        Task { @MainActor in
            switch cmd {
            case "start":
                let lang = (body["language"] as? String) ?? "en-US"
                let session = (body["session"] as? String) ?? "transcript"
                let ok = await asr.authorize()
                guard ok else {
                    post(["type": "error", "text": "Speech recognition not authorized"])
                    return
                }
                do {
                    try asr.start(locale: lang, session: session) { [weak self] event in
                        self?.post(event)
                    }
                    self.post(["type": "status", "state": "listening",
                               "engine": "apple-on-device"])
                } catch {
                    self.post(["type": "error", "text": error.localizedDescription])
                }
            case "stop":
                asr.stop()
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
        webView?.evaluateJavaScript(js, completionHandler: nil)
    }
}
