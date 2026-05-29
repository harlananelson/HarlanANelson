import SwiftUI

struct FeedbackCard: View {
    let result: GradingResult?
    let exercise: Exercise?
    let aiFeedback: String?

    var body: some View {
        if let result, let exercise {
            VStack(alignment: .leading, spacing: 12) {
                // Correct / Incorrect header
                HStack {
                    Image(systemName: result.correct ? "checkmark.circle.fill" : "xmark.circle.fill")
                        .foregroundStyle(result.correct ? .green : .red)
                    Text(result.correct ? "Correcto" : "Revisa esta idea")
                        .font(.headline)
                        .foregroundStyle(result.correct ? .green : .red)
                    Spacer()
                    Text("\(result.aciertos)/\(result.total)")
                        .font(.subheadline)
                        .foregroundStyle(.secondary)
                }

                // Model answer
                Text(exercise.respuesta)
                    .font(.body)

                // Notes / hints
                if !result.notes.isEmpty {
                    ForEach(result.notes, id: \.self) { note in
                        Text(note)
                            .font(.subheadline)
                            .foregroundStyle(.secondary)
                    }
                }

                // AI feedback (Layer 2)
                if let aiFeedback, !aiFeedback.isEmpty {
                    Text(aiFeedback)
                        .font(.subheadline)
                        .foregroundStyle(.orange)
                        .padding(.top, 4)
                }

                // Tense info card (on correct answers)
                if result.correct, let tenseInfo = TenseInfo.descriptions[exercise.tense] {
                    TenseInfoCard(info: tenseInfo)
                }

                if !result.correct {
                    Text("Pulsa \"Siguiente\" para continuar o inténtalo otra vez.")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }
            }
            .padding()
            .background(Color(.secondarySystemBackground))
            .clipShape(RoundedRectangle(cornerRadius: 12))
        } else {
            Text("Pulsa \"Escuchar y responder\". La app leerá la consigna y después activará el micrófono.")
                .font(.subheadline)
                .foregroundStyle(.secondary)
                .padding()
                .frame(maxWidth: .infinity, alignment: .leading)
                .background(Color(.secondarySystemBackground))
                .clipShape(RoundedRectangle(cornerRadius: 12))
        }
    }
}

private struct TenseInfoCard: View {
    let info: TenseInfo

    var body: some View {
        VStack(alignment: .leading, spacing: 6) {
            Text(info.nombre)
                .font(.subheadline.bold())
                .foregroundStyle(.teal)
            Text(info.regla)
                .font(.caption)
            Text("Conjugación: \(info.conjugacion)")
                .font(.caption2)
                .foregroundStyle(.secondary)
        }
        .padding(10)
        .background(Color.teal.opacity(0.08))
        .clipShape(RoundedRectangle(cornerRadius: 8))
        .overlay(
            RoundedRectangle(cornerRadius: 8)
                .stroke(Color.teal.opacity(0.2), lineWidth: 1)
        )
    }
}
