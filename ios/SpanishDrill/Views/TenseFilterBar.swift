import SwiftUI

struct TenseFilterBar: View {
    @Binding var activeTenses: Set<Tense>

    var body: some View {
        ScrollView(.horizontal, showsIndicators: false) {
            HStack(spacing: 8) {
                TensePill(label: "Todos", isActive: activeTenses.isEmpty) {
                    activeTenses.removeAll()
                }

                ForEach(Tense.allCases) { tense in
                    TensePill(
                        label: tense.displayName,
                        isActive: activeTenses.contains(tense)
                    ) {
                        if activeTenses.contains(tense) {
                            activeTenses.remove(tense)
                        } else {
                            activeTenses.insert(tense)
                        }
                    }
                }
            }
            .padding(.horizontal)
        }
    }
}

private struct TensePill: View {
    let label: String
    let isActive: Bool
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            Text(label)
                .font(.subheadline)
                .fontWeight(isActive ? .semibold : .regular)
                .padding(.horizontal, 14)
                .padding(.vertical, 8)
                .background(isActive ? Color.accentColor : Color(.secondarySystemBackground))
                .foregroundStyle(isActive ? .white : .secondary)
                .clipShape(Capsule())
        }
        .buttonStyle(.plain)
    }
}
