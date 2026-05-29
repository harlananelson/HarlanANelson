import Foundation

enum TextNormalizer {

    /// Port of convertirHoraYNumeroBasico() from the web app
    private static let timeReplacements: [(pattern: String, replacement: String)] = [
        ("\\b1:00\\b", "una"),
        ("\\b2:00\\b", "dos"),
        ("\\b3:00\\b", "tres"),
        ("\\b4:00\\b", "cuatro"),
        ("\\b5:00\\b", "cinco"),
        ("\\b6:00\\b", "seis"),
        ("\\b7:00\\b", "siete"),
        ("\\b8:00\\b", "ocho"),
        ("\\b9:00\\b", "nueve"),
        ("\\b10:00\\b", "diez"),
        ("\\b11:00\\b", "once"),
        ("\\b12:00\\b", "doce"),
        ("\\b15\\b", "quince"),
    ]

    /// Port of quitarExtrasComunes() — common spoken variations
    private static let commonSubstitutions: [(pattern: String, replacement: String)] = [
        ("\\bhasta este dia\\b", "hasta ese dia"),
        ("\\bayer en la tarde\\b", "ayer por la tarde"),
        ("\\bpor la tarde ayer\\b", "ayer por la tarde"),
    ]

    /// Port of textoPlano() — normalize text for comparison
    static func normalize(_ text: String) -> String {
        var t = text.lowercased()

        // Strip accents: NFD decomposition + remove combining marks
        t = t.decomposedStringWithCanonicalMapping
        t = t.unicodeScalars.filter {
            !($0.value >= 0x0300 && $0.value <= 0x036F)
        }.map { String($0) }.joined()

        // Remove punctuation
        t = t.replacingOccurrences(of: "[¿?¡!.,;]", with: "", options: .regularExpression)

        // Collapse whitespace
        t = t.replacingOccurrences(of: "\\s+", with: " ", options: .regularExpression).trimmingCharacters(in: .whitespaces)

        // Convert time/number patterns
        for (pattern, replacement) in timeReplacements {
            t = t.replacingOccurrences(of: pattern, with: replacement, options: .regularExpression)
        }

        // Common substitutions
        for (pattern, replacement) in commonSubstitutions {
            t = t.replacingOccurrences(of: pattern, with: replacement, options: .regularExpression)
        }

        return t.trimmingCharacters(in: .whitespaces)
    }
}
