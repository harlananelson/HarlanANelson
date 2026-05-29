import SwiftUI

struct LogView: View {
    let history: [AttemptRecord]

    var body: some View {
        List {
            if history.isEmpty {
                Text("Todavía no hay intentos.")
                    .foregroundStyle(.secondary)
            } else {
                ForEach(history) { record in
                    LogEntry(record: record)
                }
            }
        }
        .navigationTitle("Registro")
    }
}

private struct LogEntry: View {
    let record: AttemptRecord

    var body: some View {
        VStack(alignment: .leading, spacing: 6) {
            HStack(spacing: 6) {
                Tag(
                    label: record.correct ? "correcta" : "revisar",
                    color: record.correct ? .green : .red
                )
                if record.isReview {
                    Tag(label: "repaso", color: .orange)
                }
                Tag(label: record.tense.displayName, color: .teal)
                Spacer()
                Text("\(record.aciertos)/\(record.total)")
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }

            Text(record.verbo)
                .font(.headline)

            Group {
                Text("Contexto: \(record.contexto)")
                Text("Tu voz: \(record.userResponse.isEmpty ? "—" : record.userResponse)")
                Text("Modelo: \(record.respuesta)")
            }
            .font(.caption)
            .foregroundStyle(.secondary)

            if !record.notes.isEmpty {
                Text("Observación: \(record.notes.joined(separator: " "))")
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }
        }
        .padding(.vertical, 4)
    }
}

private struct Tag: View {
    let label: String
    let color: Color

    var body: some View {
        Text(label)
            .font(.caption2.weight(.semibold))
            .padding(.horizontal, 8)
            .padding(.vertical, 3)
            .background(color.opacity(0.12))
            .foregroundStyle(color)
            .clipShape(Capsule())
    }
}
