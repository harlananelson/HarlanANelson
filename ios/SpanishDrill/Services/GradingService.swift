import Foundation
import NaturalLanguage

@Observable
final class GradingService {

    // MARK: - Grupo Matching (Layer 1)

    func grade(userResponse: String, exercise: Exercise) -> GradingResult {
        let normalized = TextNormalizer.normalize(userResponse)

        if normalized.isEmpty {
            return GradingResult(
                correct: false,
                notes: ["No se detectó ninguna respuesta."],
                missing: exercise.grupos,
                aciertos: 0,
                total: exercise.grupos.count
            )
        }

        let missing = exercise.grupos.filter { grupo in
            !grupo.contains { alternative in
                normalized.contains(TextNormalizer.normalize(alternative))
            }
        }

        let aciertos = exercise.grupos.count - missing.count
        let correct = missing.isEmpty

        var notes: [String] = []
        if !correct {
            let tenseHints = feedbackForTense(exercise.tense, exercise: exercise, normalizedResponse: normalized)
            notes.append(contentsOf: tenseHints)
            if notes.isEmpty {
                notes.append("Faltan \(missing.count) idea(s) clave de \(exercise.grupos.count).")
            }

            // Layer 3: NLTagger lemmatization check
            let lemmaNote = checkVerbLemma(userResponse: userResponse, expectedVerb: exercise.verbo)
            if let lemmaNote {
                notes.append(lemmaNote)
            }
        }

        return GradingResult(
            correct: correct,
            notes: notes,
            missing: missing,
            aciertos: aciertos,
            total: exercise.grupos.count
        )
    }

    // MARK: - Tense-specific Feedback (port of feedbackPorTiempo)

    private func feedbackForTense(_ tense: Tense, exercise: Exercise, normalizedResponse u: String) -> [String] {
        var notes: [String] = []

        switch tense {
        case .puntual:
            if exercise.contexto.contains("ya"),
               u.range(of: "(habia|habian|habiamos|habias)", options: .regularExpression) == nil {
                notes.append("Fíjate en la palabra ya y en la relación entre dos momentos del pasado.")
            }
        case .habitual:
            if u.range(of: "(aba|aban|abamos|abas|ia|ian|iamos|ias)", options: .regularExpression) == nil {
                notes.append("Piensa en una acción repetida: necesitas el imperfecto.")
            }
        case .fondo:
            if u.range(of: "(aba|aban|abamos|abas|ia|ian|iamos|ias|era|eran)", options: .regularExpression) == nil {
                notes.append("La frase describe un fondo o estado: usa el imperfecto.")
            }
        case .anterior:
            if u.range(of: "(habia|habias|habiamos|habian)", options: .regularExpression) == nil {
                notes.append("Fíjate en la secuencia temporal: algo pasó antes de otra cosa. Necesitas había + participio.")
            }
        case .presente:
            notes.append("Recuerda conjugar en presente indicativo.")
        case .futuro:
            notes.append("Conjuga en futuro simple: infinitivo + -é, -ás, -á, -emos, -éis, -án.")
        case .condicional:
            notes.append("Conjuga en condicional: infinitivo + -ía, -ías, -ía, -íamos, -íais, -ían.")
        case .subjuntivo:
            if u.range(of: "(espero que|quiero que|es necesario|ojala|dudo que|es posible|para que|antes de que)", options: .regularExpression) == nil {
                notes.append("No olvides la frase que activa el subjuntivo (espero que, quiero que, etc.).")
            }
            notes.append("Recuerda: -ar → -e, -er/-ir → -a en el presente de subjuntivo.")
        case .subj_imperfecto:
            notes.append("Usa la forma -ra o -se del imperfecto de subjuntivo.")
        case .subj_pluscuam:
            if u.range(of: "(hubiera|hubiese|hubieras|hubieses|hubieramos|hubiesemos|hubieran|hubiesen)", options: .regularExpression) == nil {
                notes.append("Necesitas hubiera/hubiese + participio pasado.")
            }
        }

        return notes
    }

    // MARK: - NLTagger Lemmatization (Layer 3)

    private func checkVerbLemma(userResponse: String, expectedVerb: String) -> String? {
        let tagger = NLTagger(tagSchemes: [.lemma])
        tagger.string = userResponse
        tagger.setLanguage(.spanish, range: userResponse.startIndex..<userResponse.endIndex)

        var foundExpectedVerb = false

        tagger.enumerateTags(in: userResponse.startIndex..<userResponse.endIndex,
                             unit: .word,
                             scheme: .lemma) { tag, _ in
            if let lemma = tag?.rawValue,
               TextNormalizer.normalize(lemma) == TextNormalizer.normalize(expectedVerb) {
                foundExpectedVerb = true
                return false // stop enumeration
            }
            return true // continue
        }

        if !foundExpectedVerb {
            return "Parece que usaste un verbo diferente. El verbo esperado es \"\(expectedVerb)\"."
        }
        return nil
    }

    // MARK: - Foundation Models (Layer 2) — placeholder for iOS 26

    func requestAIFeedback(exercise: Exercise, userResponse: String) async -> String? {
        // Foundation Models (@Generable) will be available on iOS 26 devices
        // with Apple Intelligence. For now, return nil to use template feedback.
        //
        // When iOS 26 SDK is available, implement:
        // 1. Check SystemLanguageModel.default.isAvailable
        // 2. Create @Generable struct GrammarFeedback
        // 3. Generate structured feedback for incorrect answers
        return nil
    }
}
