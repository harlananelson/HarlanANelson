import Foundation

enum Tense: String, Codable, CaseIterable, Identifiable {
    case presente
    case futuro
    case condicional
    case subjuntivo
    case subj_imperfecto
    case subj_pluscuam
    case puntual
    case habitual
    case fondo
    case anterior

    var id: String { rawValue }

    var displayName: String {
        switch self {
        case .presente: "Presente"
        case .futuro: "Futuro"
        case .condicional: "Condicional"
        case .subjuntivo: "Subjuntivo"
        case .subj_imperfecto: "Subj. imperf."
        case .subj_pluscuam: "Subj. plusc."
        case .puntual: "Puntual"
        case .habitual: "Habitual"
        case .fondo: "Fondo"
        case .anterior: "Anterior"
        }
    }

    /// Extract tense from an exercise ID like "hablar-presente-2860"
    static func extract(from id: String) -> Tense {
        for tense in Tense.allCases {
            if id.contains("-\(tense.rawValue)-") {
                return tense
            }
        }
        return .presente
    }
}

struct Exercise: Codable, Identifiable, Hashable {
    let id: String
    let verbo: String
    let contexto: String
    let respuesta: String
    let pista: String
    let grupos: [[String]]

    var tense: Tense {
        Tense.extract(from: id)
    }

    func hash(into hasher: inout Hasher) {
        hasher.combine(id)
    }

    static func == (lhs: Exercise, rhs: Exercise) -> Bool {
        lhs.id == rhs.id
    }
}
