import SwiftUI

@main
struct SpanishDrillApp: App {
    @State private var store = ExerciseStore()

    var body: some Scene {
        WindowGroup {
            DrillView(
                session: SessionState(store: store),
                store: store
            )
        }
    }
}
