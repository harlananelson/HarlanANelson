import SwiftUI

@main
struct MaatApp: App {
    var body: some Scene {
        WindowGroup {
            MaatWebView()
                .ignoresSafeArea()
        }
    }
}
