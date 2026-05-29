import Foundation

@Observable
final class ExerciseStore {
    private(set) var exercises: [Exercise] = []
    private(set) var definitions: [String: String] = [:]

    init() {
        loadExercises()
        loadDefinitions()
    }

    private func loadExercises() {
        guard let url = Bundle.main.url(forResource: "exercises", withExtension: "json") else {
            print("exercises.json not found in bundle")
            return
        }
        do {
            let data = try Data(contentsOf: url)
            exercises = try JSONDecoder().decode([Exercise].self, from: data)
        } catch {
            print("Failed to load exercises: \(error)")
        }
    }

    private func loadDefinitions() {
        guard let url = Bundle.main.url(forResource: "definitions", withExtension: "json") else {
            print("definitions.json not found in bundle")
            return
        }
        do {
            let data = try Data(contentsOf: url)
            definitions = try JSONDecoder().decode([String: String].self, from: data)
        } catch {
            print("Failed to load definitions: \(error)")
        }
    }

    func filtered(by activeTenses: Set<Tense>) -> [Exercise] {
        if activeTenses.isEmpty {
            return exercises
        }
        return exercises.filter { activeTenses.contains($0.tense) }
    }
}
