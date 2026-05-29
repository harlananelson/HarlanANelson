import Foundation

struct AttemptRecord: Codable, Identifiable {
    let id: UUID
    let exerciseId: String
    let verbo: String
    let contexto: String
    let respuesta: String
    let userResponse: String
    let correct: Bool
    let notes: [String]
    let isReview: Bool
    let timestamp: Date
    let aciertos: Int
    let total: Int
    let tense: Tense

    init(exercise: Exercise, userResponse: String, correct: Bool, notes: [String],
         isReview: Bool, aciertos: Int, total: Int) {
        self.id = UUID()
        self.exerciseId = exercise.id
        self.verbo = exercise.verbo
        self.contexto = exercise.contexto
        self.respuesta = exercise.respuesta
        self.userResponse = userResponse
        self.correct = correct
        self.notes = notes
        self.isReview = isReview
        self.timestamp = Date()
        self.aciertos = aciertos
        self.total = total
        self.tense = exercise.tense
    }
}

struct GradingResult {
    let correct: Bool
    let notes: [String]
    let missing: [[String]]
    let aciertos: Int
    let total: Int
    var aiFeedback: String?
}

@Observable
final class SessionState {
    var current: Exercise?
    var reviewQueue: [Exercise] = []
    var weaknesses: [String: Int] = [:]
    var history: [AttemptRecord] = []
    var correctCount: Int = 0
    var incorrectCount: Int = 0
    var activeTenses: Set<Tense> = []
    var isCurrentReview: Bool = false

    private let store: ExerciseStore

    init(store: ExerciseStore) {
        self.store = store
        loadPersistedState()
    }

    func pickNext() {
        let pool = store.filtered(by: activeTenses)
        guard !pool.isEmpty else {
            current = nil
            return
        }

        let filteredReview = reviewQueue.filter { ex in
            activeTenses.isEmpty || activeTenses.contains(ex.tense)
        }

        let useReview = !filteredReview.isEmpty && Double.random(in: 0...1) < 0.45
        if useReview, let reviewExercise = filteredReview.first {
            current = reviewExercise
            reviewQueue.removeAll { $0.id == reviewExercise.id }
            isCurrentReview = true
        } else {
            current = pool.randomElement()
            isCurrentReview = false
        }
    }

    func recordAttempt(userResponse: String, result: GradingResult) {
        guard let exercise = current else { return }

        let record = AttemptRecord(
            exercise: exercise,
            userResponse: userResponse,
            correct: result.correct,
            notes: result.notes,
            isReview: isCurrentReview,
            aciertos: result.aciertos,
            total: result.total
        )
        history.insert(record, at: 0)

        if result.correct {
            correctCount += 1
        } else {
            incorrectCount += 1
            weaknesses[exercise.id, default: 0] += 1
            if !reviewQueue.contains(where: { $0.id == exercise.id }) {
                reviewQueue.append(exercise)
            }
        }

        persistState()
    }

    // MARK: - Persistence

    private var stateURL: URL {
        let docs = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask).first!
        return docs.appendingPathComponent("session_state.json")
    }

    private struct PersistedState: Codable {
        let history: [AttemptRecord]
        let weaknesses: [String: Int]
        let reviewQueueIds: [String]
        let correctCount: Int
        let incorrectCount: Int
    }

    private func persistState() {
        let state = PersistedState(
            history: history,
            weaknesses: weaknesses,
            reviewQueueIds: reviewQueue.map(\.id),
            correctCount: correctCount,
            incorrectCount: incorrectCount
        )
        do {
            let data = try JSONEncoder().encode(state)
            try data.write(to: stateURL)
        } catch {
            print("Failed to persist state: \(error)")
        }
    }

    private func loadPersistedState() {
        guard FileManager.default.fileExists(atPath: stateURL.path) else { return }
        do {
            let data = try Data(contentsOf: stateURL)
            let state = try JSONDecoder().decode(PersistedState.self, from: data)
            history = state.history
            weaknesses = state.weaknesses
            correctCount = state.correctCount
            incorrectCount = state.incorrectCount
            // Rebuild review queue from IDs
            let exerciseMap = Dictionary(uniqueKeysWithValues: store.exercises.map { ($0.id, $0) })
            reviewQueue = state.reviewQueueIds.compactMap { exerciseMap[$0] }
        } catch {
            print("Failed to load persisted state: \(error)")
        }
    }

    func exportJSON() -> Data? {
        let exportData: [String: Any] = [
            "conteo": ["correctas": correctCount, "incorrectas": incorrectCount],
            "debiles": weaknesses,
            "registro": history.map { record -> [String: Any] in
                [
                    "item": [
                        "id": record.exerciseId,
                        "verbo": record.verbo,
                        "contexto": record.contexto,
                        "respuesta": record.respuesta,
                    ],
                    "usuario": record.userResponse,
                    "correcto": record.correct,
                    "notas": record.notes,
                    "repaso": record.isReview,
                    "ts": ISO8601DateFormatter().string(from: record.timestamp),
                    "aciertos": record.aciertos,
                    "total": record.total,
                ]
            },
        ]
        return try? JSONSerialization.data(withJSONObject: exportData, options: .prettyPrinted)
    }
}
