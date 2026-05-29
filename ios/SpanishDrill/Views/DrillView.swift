import SwiftUI

struct DrillView: View {
    @State var session: SessionState
    let store: ExerciseStore
    @State var speechService = SpeechService()
    @State var recognitionService = RecognitionService()
    @State var gradingService = GradingService()

    @State private var currentResult: GradingResult?
    @State private var aiFeedback: String?
    @State private var hasAuthorization = false

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(spacing: 16) {
                    TenseFilterBar(activeTenses: $session.activeTenses)
                        .onChange(of: session.activeTenses) {
                            currentResult = nil
                            aiFeedback = nil
                            session.pickNext()
                        }

                    if let exercise = session.current {
                        exerciseCard(exercise)
                        actionButtons(exercise)
                        TranscriptionBox(
                            text: recognitionService.currentTranscription,
                            isListening: recognitionService.isListening
                        )
                        FeedbackCard(
                            result: currentResult,
                            exercise: currentResult != nil ? exercise : nil,
                            aiFeedback: aiFeedback
                        )
                        statsBar
                    } else {
                        ContentUnavailableView(
                            "No hay ejercicios",
                            systemImage: "text.book.closed",
                            description: Text("No hay ejercicios para los filtros seleccionados.")
                        )
                    }
                }
                .padding()
            }
            .navigationTitle("Práctica oral")
            .toolbar {
                ToolbarItem(placement: .topBarTrailing) {
                    NavigationLink {
                        LogView(history: session.history)
                    } label: {
                        Image(systemName: "list.bullet")
                    }
                }
                ToolbarItem(placement: .topBarTrailing) {
                    NavigationLink {
                        SettingsView(speechService: speechService)
                    } label: {
                        Image(systemName: "gearshape")
                    }
                }
                ToolbarItem(placement: .topBarTrailing) {
                    if let data = session.exportJSON() {
                        ShareLink(
                            item: data,
                            preview: SharePreview("registro-practica-espanol.json")
                        )
                    }
                }
            }
            .task {
                hasAuthorization = await recognitionService.requestAuthorization()
                if session.current == nil {
                    session.pickNext()
                }
            }
        }
    }

    // MARK: - Exercise Card

    @ViewBuilder
    private func exerciseCard(_ exercise: Exercise) -> some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Text("Verbo: \(exercise.verbo)")
                    .font(.title2.bold())
                Text(exercise.tense.displayName)
                    .font(.caption.weight(.semibold))
                    .padding(.horizontal, 10)
                    .padding(.vertical, 4)
                    .background(Color.accentColor)
                    .foregroundStyle(.white)
                    .clipShape(Capsule())
                Spacer()
                if session.isCurrentReview {
                    Text("repaso")
                        .font(.caption2.weight(.semibold))
                        .padding(.horizontal, 8)
                        .padding(.vertical, 3)
                        .background(Color.orange.opacity(0.12))
                        .foregroundStyle(.orange)
                        .clipShape(Capsule())
                }
            }

            if let definition = store.definitions[exercise.verbo] {
                Text(definition)
                    .font(.subheadline)
                    .foregroundStyle(.secondary)
                    .italic()
            }

            Text("Contexto: \(exercise.contexto)")
                .font(.title3)

            Text("Pista: \(exercise.pista)")
                .font(.subheadline)
                .foregroundStyle(.secondary)
        }
        .padding()
        .background(Color(.secondarySystemBackground))
        .clipShape(RoundedRectangle(cornerRadius: 16))
    }

    // MARK: - Action Buttons

    @ViewBuilder
    private func actionButtons(_ exercise: Exercise) -> some View {
        VStack(spacing: 10) {
            // Listen buttons row
            HStack(spacing: 10) {
                ActionButton(title: "Oír contexto", icon: "speaker.wave.2") {
                    speechService.speak(exercise.contexto)
                }
                ActionButton(title: "Oír verbo", icon: "textformat") {
                    speechService.speak(exercise.verbo)
                }
                ActionButton(title: "Oír pista", icon: "lightbulb") {
                    speechService.speak(exercise.pista)
                }
            }

            // Main action: listen and respond
            Button {
                startSequence(exercise)
            } label: {
                Label(
                    recognitionService.isListening ? "Escuchando..." : "Escuchar y responder",
                    systemImage: recognitionService.isListening ? "mic.fill" : "mic"
                )
                .font(.headline)
                .frame(maxWidth: .infinity)
                .padding(.vertical, 14)
            }
            .buttonStyle(.borderedProminent)
            .tint(recognitionService.isListening ? .red : .accentColor)
            .disabled(!hasAuthorization)

            // Secondary actions
            HStack(spacing: 10) {
                Button("Oír frase modelo") {
                    speechService.speak(exercise.respuesta, rate: 0.28)
                }
                .buttonStyle(.bordered)

                Button("Siguiente") {
                    currentResult = nil
                    aiFeedback = nil
                    recognitionService.currentTranscription = ""
                    session.pickNext()
                }
                .buttonStyle(.bordered)
            }
        }
    }

    // MARK: - Stats Bar

    private var statsBar: some View {
        HStack(spacing: 12) {
            StatBox(label: "Correctas", value: "\(session.correctCount)", color: .green)
            StatBox(label: "Para repasar", value: "\(session.incorrectCount)", color: .red)
            StatBox(label: "En cola", value: "\(session.reviewQueue.count)", color: .orange)
        }
    }

    // MARK: - Voice Sequence

    private func startSequence(_ exercise: Exercise) {
        if recognitionService.isListening {
            recognitionService.stopListening()
            // Grade what we have
            if !recognitionService.finalTranscription.isEmpty {
                gradeResponse(recognitionService.finalTranscription, exercise: exercise)
            }
            return
        }

        currentResult = nil
        aiFeedback = nil
        recognitionService.currentTranscription = ""

        let prompt = "\(exercise.verbo). \(exercise.contexto). \(exercise.pista)"
        speechService.speak(prompt) { [self] in
            // Small delay after TTS finishes, then start listening
            DispatchQueue.main.asyncAfter(deadline: .now() + 0.35) {
                do {
                    try recognitionService.startListening { text, isFinal in
                        if isFinal {
                            gradeResponse(text, exercise: exercise)
                        }
                    }
                } catch {
                    print("Failed to start listening: \(error)")
                }
            }
        }
    }

    private func gradeResponse(_ text: String, exercise: Exercise) {
        let result = gradingService.grade(userResponse: text, exercise: exercise)
        currentResult = result
        session.recordAttempt(userResponse: text, result: result)

        // Speak feedback
        if result.correct {
            speechService.speak("Correcto. \(exercise.respuesta)", rate: 0.28)
        } else {
            speechService.speak("Revisa esta idea. \(exercise.respuesta)", rate: 0.25)
        }

        // Request AI feedback for incorrect answers (async)
        if !result.correct {
            Task {
                aiFeedback = await gradingService.requestAIFeedback(
                    exercise: exercise,
                    userResponse: text
                )
            }
        }
    }
}

// MARK: - Subviews

private struct ActionButton: View {
    let title: String
    let icon: String
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            VStack(spacing: 4) {
                Image(systemName: icon)
                    .font(.title3)
                Text(title)
                    .font(.caption2)
            }
            .frame(maxWidth: .infinity)
            .padding(.vertical, 10)
        }
        .buttonStyle(.bordered)
    }
}

private struct StatBox: View {
    let label: String
    let value: String
    let color: Color

    var body: some View {
        VStack(spacing: 2) {
            Text(value)
                .font(.title2.bold())
                .foregroundStyle(color)
            Text(label)
                .font(.caption2)
                .foregroundStyle(.secondary)
        }
        .frame(maxWidth: .infinity)
        .padding(.vertical, 10)
        .background(Color(.secondarySystemBackground))
        .clipShape(RoundedRectangle(cornerRadius: 10))
    }
}
