import Foundation

struct TenseInfo {
    let nombre: String
    let regla: String
    let conjugacion: String

    static let descriptions: [Tense: TenseInfo] = [
        .presente: TenseInfo(
            nombre: "Presente de indicativo",
            regla: "Acciones actuales, habituales o verdades generales.",
            conjugacion: "-ar: -o, -as, -a, -amos, -áis, -an | -er: -o, -es, -e, -emos, -éis, -en | -ir: -o, -es, -e, -imos, -ís, -en"
        ),
        .futuro: TenseInfo(
            nombre: "Futuro simple",
            regla: "Acciones que ocurrirán. También predicciones y probabilidad.",
            conjugacion: "infinitivo + -é, -ás, -á, -emos, -éis, -án. Irregulares: tendr-, pondr-, saldr-, vendr-, podr-, sabr-, querr-, har-, dir-, valdr-"
        ),
        .condicional: TenseInfo(
            nombre: "Condicional",
            regla: "Hipótesis, cortesía, consejo. \"¿Qué harías si…?\"",
            conjugacion: "infinitivo + -ía, -ías, -ía, -íamos, -íais, -ían. Mismos irregulares que el futuro."
        ),
        .subjuntivo: TenseInfo(
            nombre: "Presente de subjuntivo",
            regla: "Deseos, dudas, emociones, necesidad. Aparece tras \"que\".",
            conjugacion: "-ar → -e, -es, -e, -emos, -éis, -en | -er/-ir → -a, -as, -a, -amos, -áis, -an"
        ),
        .subj_imperfecto: TenseInfo(
            nombre: "Imperfecto de subjuntivo",
            regla: "Hipótesis pasadas, cláusulas con \"si\", deseos irreales.",
            conjugacion: "raíz del pretérito + -ra/-se, -ras/-ses, -ra/-se, -ramos/-semos, -rais/-seis, -ran/-sen"
        ),
        .subj_pluscuam: TenseInfo(
            nombre: "Pluscuamperfecto de subjuntivo",
            regla: "Acciones pasadas no realizadas. \"Si hubiera sabido…\"",
            conjugacion: "hubiera/hubiese + participio (-ado/-ido). Irregulares: hecho, dicho, puesto, visto, escrito, abierto, vuelto, roto, muerto"
        ),
        .puntual: TenseInfo(
            nombre: "Pretérito indefinido",
            regla: "Acción terminada en un momento concreto del pasado.",
            conjugacion: "-ar: -é, -aste, -ó, -amos, -asteis, -aron | -er/-ir: -í, -iste, -ió, -imos, -isteis, -ieron"
        ),
        .habitual: TenseInfo(
            nombre: "Pretérito imperfecto (habitual)",
            regla: "Acción repetida o costumbre en el pasado.",
            conjugacion: "-ar: -aba, -abas, -aba, -ábamos, -abais, -aban | -er/-ir: -ía, -ías, -ía, -íamos, -íais, -ían"
        ),
        .fondo: TenseInfo(
            nombre: "Pretérito imperfecto (fondo)",
            regla: "Describe estados, escenas o circunstancias de fondo en el pasado.",
            conjugacion: "Mismas terminaciones que habitual. Solo 3 irregulares: era (ser), iba (ir), veía (ver)."
        ),
        .anterior: TenseInfo(
            nombre: "Pretérito pluscuamperfecto",
            regla: "Acción pasada anterior a otra acción pasada. \"Ya había comido cuando llegó.\"",
            conjugacion: "había/habías/había/habíamos/habíais/habían + participio (-ado/-ido)"
        ),
    ]
}
