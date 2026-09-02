import SwiftUI
import WebKit

/// Full-screen WKWebView of live Maat. Native job is on-device ASR (Neural Engine
/// via Speech.framework). The web UI stays the product.
struct MaatWebView: UIViewRepresentable {
    func makeCoordinator() -> AsrBridge { AsrBridge() }

    func makeUIView(context: Context) -> WKWebView {
        let conf = WKWebViewConfiguration()
        conf.allowsInlineMediaPlayback = true
        conf.mediaTypesRequiringUserActionForPlayback = []
        let uc = conf.userContentController
        uc.add(context.coordinator, name: "maatAsr")
        uc.addUserScript(WKUserScript(
            source: "window.__MAAT_NATIVE__={asr:true,engine:'apple-on-device'};",
            injectionTime: .atDocumentStart,
            forMainFrameOnly: true
        ))
        let view = WKWebView(frame: .zero, configuration: conf)
        view.scrollView.bounces = false
        context.coordinator.webView = view
        if let url = URL(string: "https://harlananelson.com/maat.html") {
            view.load(URLRequest(url: url, cachePolicy: .reloadIgnoringLocalCacheData))
        }
        return view
    }

    func updateUIView(_ uiView: WKWebView, context: Context) {}
}
