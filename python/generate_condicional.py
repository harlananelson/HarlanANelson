#!/usr/bin/env python3
"""Generate conditional tense exercises for Spanish Speech Drill."""

import json
import os
import unicodedata

OUTPUT_DIR = "/home/harlan/projects/harlananelson/python/output/condicional"
os.makedirs(OUTPUT_DIR, exist_ok=True)

VERBS = [
    "abandonar", "abrir", "acabar", "aceptar", "acercar", "acompañar", "acordar",
    "actuar", "admitir", "aforar", "agradecer", "alcanzar", "alegrar", "alejar",
    "amar", "andar", "aparecer", "apartar", "apostar", "apoyar", "aprender",
    "arreglar", "asegurar", "asesinar", "asustar", "atacar", "atrapar", "averiguar",
    "ayudar", "bailar", "bajar", "bastar", "beber", "besar", "buscar", "caer",
    "callar", "calmar", "cambiar", "caminar", "cantar", "casar", "cerrar", "coger",
    "comenzar", "comer", "cometer", "compartir", "comprar", "comprender", "conducir",
    "confiar", "conocer", "conseguir", "considerar", "construir", "contar", "contestar",
    "continuar", "controlar", "convertir", "correr", "cortar", "costar", "crear",
    "crecer", "creer", "cubrir", "cuidar", "cumplir", "dar", "deber", "decidir",
    "decir", "defender", "dejar", "demostrar", "depender", "desaparecer", "desarrollar",
    "descubrir", "desear", "despedir", "despertar", "destruir", "detener", "devolver",
    "dirigir", "disculpar", "discutir", "disfrutar", "disparar", "dormir", "echar",
    "elegir", "empezar", "encantar", "encontrar", "enfrentar", "engañar", "enseñar",
    "entender", "enterar", "entrar", "entregar", "enviar", "escapar", "esconder",
    "escribir", "escuchar", "esperar", "estar", "estudiar", "evitar", "existir",
    "explicar", "formar", "funcionar", "ganar", "golpear", "gritar", "guardar",
    "gustar", "haber", "hablar", "hacer", "hallar", "huir", "imaginar", "importar",
    "incluir", "informar", "intentar", "interesar", "invitar", "ir", "joder", "jugar",
    "jurar", "leer", "levantar", "llamar", "llegar", "llevar", "llorar", "lograr",
    "luchar", "mandar", "manejar", "mantener", "marchar", "matar", "mencionar",
    "mentir", "merecer", "meter", "mirar", "molestar", "morir", "mostrar", "mover",
    "nacer", "necesitar", "negar", "observar", "obtener", "ocupar", "ocurrir", "odiar",
    "ofrecer", "oír", "olvidar", "pagar", "parar", "parecer", "partir", "pasar",
    "pedir", "pegar", "pelear", "pensar", "perder", "perdonar", "permanecer",
    "permitir", "pertenecer", "pesar", "poder", "poner", "preferir", "preguntar",
    "preocupar", "preparar", "presentar", "prestar", "probar", "producir", "prometer",
    "proteger", "quedar", "querer", "quitar", "realizar", "recibir", "recoger",
    "reconocer", "recordar", "recuperar", "referir", "regresar", "reír", "repetir",
    "representar", "resolver", "responder", "resultar", "reunir", "revisar", "robar",
    "romper", "saber", "sacar", "salir", "salvar", "seguir", "señalar", "sentar",
    "sentir", "ser", "servir", "significar", "soler", "soltar", "sonar", "subir",
    "suceder", "sufrir", "superar", "suponer", "temer", "tener", "terminar", "tirar",
    "tocar", "tomar", "trabajar", "traer", "tranquilar", "tratar", "unir", "usar",
    "utilizar", "valer", "vender", "venir", "ver", "viajar", "vivir", "volar", "volver"
]

# Irregular conditional stems (same as future tense)
IRREGULAR_STEMS = {
    "tener": "tendr",
    "venir": "vendr",
    "poner": "pondr",
    "salir": "saldr",
    "poder": "podr",
    "saber": "sabr",
    "haber": "habr",
    "querer": "querr",
    "hacer": "har",
    "decir": "dir",
    "valer": "valdr",
    "mantener": "mantendr",
    "obtener": "obtendr",
    "detener": "detendr",
    "devolver": "devolver",  # regular -er
    "suponer": "supondr",
    "contener": "contendr",
    "convenir": "convendr",
}

# Conditional endings
ENDINGS = {
    "yo": "ía",
    "tú": "ías",
    "él": "ía",
    "ella": "ía",
    "usted": "ía",
    "nosotros": "íamos",
    "vosotros": "íais",
    "ellos": "ían",
    "ellas": "ían",
    "ustedes": "ían",
}

def get_conditional_stem(verb):
    """Get the conditional stem for a verb."""
    if verb in IRREGULAR_STEMS:
        return IRREGULAR_STEMS[verb]
    # Regular: full infinitive is the stem
    return verb


def conjugate_conditional(verb, subject):
    """Conjugate a verb in the conditional tense for a given subject."""
    stem = get_conditional_stem(verb)
    ending = ENDINGS[subject]
    return stem + ending


def remove_accents(text):
    """Remove accent marks from text."""
    nfkd = unicodedata.normalize('NFKD', text)
    return ''.join(c for c in nfkd if unicodedata.category(c) != 'Mn')


# Exercise templates - varied contexts and sentence patterns
# Each template: (subject, context_phrase, sentence_template, hint, complement_template)
# sentence_template uses {subject}, {verb}, {complement}, {context}

EXERCISE_TEMPLATES = [
    # --- Templates for exercise index 0 (first per verb) ---
    {
        "subjects": ["yo", "tú", "él", "ella", "nosotros", "ellos", "usted"],
        "templates": [
            {
                "subject": "yo",
                "context": "en tu lugar",
                "sentence": "yo {verb} {complement} en tu lugar.",
                "hint": "Expresa lo que harías en la situación de otra persona.",
                "complement_pool": [
                    "la verdad", "con más cuidado", "sin dudar", "de otra manera",
                    "lo mismo", "algo diferente", "con calma", "todo lo posible",
                    "las cosas bien", "mejor", "con más esfuerzo", "sin miedo"
                ]
            },
            {
                "subject": "tú",
                "context": "si pudieras",
                "sentence": "tú {verb} {complement} si pudieras.",
                "hint": "Expresa una acción hipotética que depende de una condición.",
                "complement_pool": [
                    "sin pensarlo", "con gusto", "en seguida", "con alegría",
                    "sin problema", "de inmediato", "con entusiasmo", "mucho más",
                    "algo mejor", "con más frecuencia", "con facilidad", "todo el tiempo"
                ]
            },
            {
                "subject": "él",
                "context": "con más tiempo",
                "sentence": "él {verb} {complement} con más tiempo.",
                "hint": "Describe lo que alguien haría si tuviera más tiempo.",
                "complement_pool": [
                    "con más detalle", "mejor", "de otra forma", "sin prisa",
                    "todo bien", "con más calma", "algo nuevo", "con dedicación",
                    "de manera diferente", "las cosas bien", "con esmero", "con paciencia"
                ]
            },
        ]
    },
    # --- Templates for exercise index 1 (second per verb) ---
    {
        "subjects": ["ella", "nosotros", "usted", "yo", "tú", "ellos", "ustedes"],
        "templates": [
            {
                "subject": "ella",
                "context": "en esa situación",
                "sentence": "ella {verb} {complement} en esa situación.",
                "hint": "Imagina cómo reaccionaría alguien en una situación específica.",
                "complement_pool": [
                    "con valentía", "sin miedo", "de otra manera", "con prudencia",
                    "lo necesario", "mejor", "con más cuidado", "sin vacilar",
                    "con determinación", "algo distinto", "con serenidad", "con firmeza"
                ]
            },
            {
                "subject": "nosotros",
                "context": "si fuera posible",
                "sentence": "nosotros {verb} {complement} si fuera posible.",
                "hint": "Expresa un deseo grupal condicionado a una posibilidad.",
                "complement_pool": [
                    "con mucho gusto", "sin dudar", "todos juntos", "con alegría",
                    "lo antes posible", "con entusiasmo", "todo el día", "de buena gana",
                    "con ilusión", "mucho más", "con ganas", "cada semana"
                ]
            },
            {
                "subject": "usted",
                "context": "con más dinero",
                "sentence": "usted {verb} {complement} con más dinero.",
                "hint": "Habla de lo que haría alguien con más recursos.",
                "complement_pool": [
                    "sin preocupaciones", "algo mejor", "con tranquilidad", "más seguido",
                    "con más libertad", "lo que quisiera", "sin límites", "con más comodidad",
                    "algo especial", "con más frecuencia", "mucho más", "todo lo necesario"
                ]
            },
        ]
    },
    # --- Templates for exercise index 2 (third per verb) ---
    {
        "subjects": ["ellos", "ustedes", "yo", "tú", "ella", "nosotros", "él"],
        "templates": [
            {
                "subject": "ellos",
                "context": "en un mundo ideal",
                "sentence": "ellos {verb} {complement} en un mundo ideal.",
                "hint": "Describe una situación ideal e imaginaria.",
                "complement_pool": [
                    "sin problemas", "con total libertad", "todo el tiempo", "sin esfuerzo",
                    "con más frecuencia", "sin preocupaciones", "cada día", "con alegría",
                    "algo maravilloso", "de la mejor manera", "con armonía", "sin límites"
                ]
            },
            {
                "subject": "ustedes",
                "context": "de ser posible",
                "sentence": "ustedes {verb} {complement} de ser posible.",
                "hint": "Presenta una acción cortés condicionada a la posibilidad.",
                "complement_pool": [
                    "con gusto", "en seguida", "sin demora", "con mucho cuidado",
                    "lo antes posible", "con más atención", "sin falta", "con dedicación",
                    "mejor", "de otra forma", "con más esfuerzo", "con prontitud"
                ]
            },
            {
                "subject": "yo",
                "context": "con más experiencia",
                "sentence": "yo {verb} {complement} con más experiencia.",
                "hint": "Reflexiona sobre lo que harías con más conocimiento.",
                "complement_pool": [
                    "de otra manera", "con más confianza", "mejor", "sin errores",
                    "con más seguridad", "algo diferente", "las cosas bien", "con más habilidad",
                    "sin tantas dudas", "con más criterio", "todo de forma distinta", "con más eficiencia"
                ]
            },
        ]
    },
]

# Additional context/complement variations for specific verb types
# to make exercises more natural

VERB_SPECIFIC = {
    # Movement verbs
    "caminar": ["por el parque", "hasta la playa", "por la ciudad"],
    "correr": ["por la mañana", "en el maratón", "más rápido"],
    "bailar": ["toda la noche", "con alegría", "en la fiesta"],
    "volar": ["a otro país", "por todo el mundo", "a casa"],
    "nadar": ["en el mar", "cada mañana", "con los amigos"],
    "subir": ["la montaña", "las escaleras", "al tren"],
    "bajar": ["las escaleras", "del autobús", "al valle"],
    "viajar": ["por el mundo", "a España", "con la familia"],
    "andar": ["por el campo", "sin prisa", "por la calle"],
    "ir": ["al cine", "de vacaciones", "a la playa"],
    "venir": ["a la fiesta", "con nosotros", "más temprano"],
    "salir": ["a cenar", "de viaje", "con los amigos"],
    "entrar": ["en la casa", "al edificio", "con cuidado"],
    "llegar": ["a tiempo", "más temprano", "antes que nadie"],
    "partir": ["mañana mismo", "hacia el norte", "sin mirar atrás"],
    "regresar": ["a casa", "al pueblo", "con buenas noticias"],
    "marchar": ["hacia el sur", "sin despedirse", "con determinación"],
    "escapar": ["de la rutina", "a un lugar tranquilo", "sin dejar rastro"],
    "huir": ["del peligro", "a otro lugar", "sin mirar atrás"],
    "acercar": ["la silla", "el libro", "a los amigos"],
    "alejar": ["las dudas", "los problemas", "las preocupaciones"],

    # Communication verbs
    "hablar": ["con más claridad", "en español", "con la familia"],
    "decir": ["la verdad", "algo importante", "todo lo necesario"],
    "contar": ["la historia", "un secreto", "lo que pasó"],
    "explicar": ["el problema", "la situación", "todo con calma"],
    "preguntar": ["por el camino", "sobre el tema", "con respeto"],
    "contestar": ["con sinceridad", "todas las preguntas", "sin rodeos"],
    "gritar": ["de alegría", "con fuerza", "su nombre"],
    "callar": ["por respeto", "la verdad", "un momento"],
    "escribir": ["una carta", "un libro", "la historia"],
    "leer": ["más libros", "cada noche", "con atención"],
    "escuchar": ["con atención", "buena música", "los consejos"],
    "llamar": ["por teléfono", "a la puerta", "al médico"],
    "cantar": ["una canción", "con el corazón", "en público"],
    "mencionar": ["el tema", "algo importante", "su nombre"],
    "informar": ["a todos", "sobre el avance", "con detalle"],
    "señalar": ["el camino", "la solución", "el error"],
    "repetir": ["la lección", "el ejercicio", "las palabras"],
    "responder": ["con calma", "la pregunta", "de inmediato"],
    "referir": ["el caso", "la situación", "los hechos"],
    "prometer": ["algo mejor", "un cambio", "su apoyo"],

    # Emotion/state verbs
    "amar": ["con todo el corazón", "sin condiciones", "más profundamente"],
    "odiar": ["menos cosas", "la injusticia", "la mentira"],
    "temer": ["menos cosas", "el fracaso", "la soledad"],
    "sentir": ["más alegría", "menos miedo", "más gratitud"],
    "gustar": ["más la vida", "el nuevo trabajo", "mucho eso"],
    "encantar": ["a todos", "la idea", "el viaje"],
    "alegrar": ["a la familia", "el día", "el ambiente"],
    "molestar": ["a nadie", "menos", "a los vecinos"],
    "preocupar": ["menos", "a los padres", "la situación"],
    "interesar": ["a más personas", "al público", "a los jóvenes"],
    "importar": ["la opinión", "el resultado", "cada detalle"],
    "asustar": ["a cualquiera", "al niño", "a los demás"],
    "llorar": ["de felicidad", "de emoción", "sin parar"],
    "reír": ["más seguido", "con ganas", "de alegría"],
    "disfrutar": ["cada momento", "la vida", "del viaje"],
    "sufrir": ["menos", "por los demás", "en silencio"],

    # Action/work verbs
    "trabajar": ["con más ganas", "en equipo", "desde casa"],
    "estudiar": ["más idiomas", "con dedicación", "cada día"],
    "crear": ["algo nuevo", "una empresa", "una obra de arte"],
    "construir": ["una casa", "un futuro mejor", "algo grande"],
    "producir": ["más resultados", "algo valioso", "con eficiencia"],
    "hacer": ["las cosas bien", "un cambio", "algo diferente"],
    "preparar": ["la cena", "todo con tiempo", "un plan"],
    "formar": ["un equipo", "una alianza", "a los jóvenes"],
    "desarrollar": ["un proyecto", "nuevas ideas", "una estrategia"],
    "resolver": ["el problema", "la situación", "el conflicto"],
    "arreglar": ["la casa", "el problema", "todo rápido"],
    "revisar": ["el documento", "cada detalle", "el plan"],
    "realizar": ["el sueño", "un proyecto", "un viaje"],
    "representar": ["al grupo", "a la empresa", "un papel"],
    "dirigir": ["la empresa", "el proyecto", "con sabiduría"],
    "manejar": ["mejor las cosas", "la situación", "con cuidado"],
    "controlar": ["la situación", "los gastos", "mejor las emociones"],
    "organizar": ["la fiesta", "el evento", "todo bien"],

    # Perception/cognition verbs
    "ver": ["las cosas diferentes", "el mundo", "con otros ojos"],
    "mirar": ["con más atención", "hacia el futuro", "el paisaje"],
    "observar": ["con cuidado", "cada detalle", "la naturaleza"],
    "pensar": ["con más calma", "en el futuro", "dos veces"],
    "creer": ["en ti mismo", "en el proyecto", "en la justicia"],
    "conocer": ["más países", "a más personas", "la verdad"],
    "entender": ["mejor la situación", "el problema", "a los demás"],
    "comprender": ["mejor el tema", "la lección", "el significado"],
    "imaginar": ["un mundo mejor", "las posibilidades", "un futuro brillante"],
    "reconocer": ["el error", "el esfuerzo", "la verdad"],
    "recordar": ["los buenos tiempos", "cada momento", "con cariño"],
    "descubrir": ["nuevos lugares", "la verdad", "algo increíble"],
    "encontrar": ["la solución", "un camino mejor", "la respuesta"],
    "hallar": ["la respuesta", "una solución", "el sentido"],
    "considerar": ["todas las opciones", "la propuesta", "un cambio"],
    "elegir": ["con más cuidado", "lo mejor", "otra opción"],
    "decidir": ["con más calma", "por ti mismo", "sin presión"],
    "averiguar": ["la verdad", "lo que pasó", "todos los detalles"],

    # Giving/receiving verbs
    "dar": ["más tiempo", "una oportunidad", "lo mejor de mí"],
    "recibir": ["con gratitud", "a los invitados", "buenas noticias"],
    "ofrecer": ["mi ayuda", "algo mejor", "una solución"],
    "enviar": ["un mensaje", "las flores", "la carta"],
    "entregar": ["el informe", "el paquete", "los documentos"],
    "devolver": ["el favor", "el libro", "la llamada"],
    "pagar": ["con gusto", "la cuenta", "todas las deudas"],
    "comprar": ["una casa nueva", "algo especial", "regalos para todos"],
    "vender": ["la casa", "el coche", "los productos"],
    "prestar": ["más atención", "el libro", "mi ayuda"],
    "robar": ["el corazón", "la atención", "un beso"],
    "guardar": ["el secreto", "los recuerdos", "la calma"],

    # Life/existence verbs
    "vivir": ["en otro país", "con más tranquilidad", "sin preocupaciones"],
    "morir": ["de vergüenza", "por probar eso", "de risa"],
    "nacer": ["en otra época", "en otro lugar", "de nuevo"],
    "existir": ["sin problemas", "en paz", "de otra forma"],
    "ser": ["más paciente", "mejor persona", "más valiente"],
    "estar": ["más tranquilo", "en la playa", "con la familia"],
    "parecer": ["más joven", "más seguro", "más fuerte"],
    "resultar": ["más fácil", "interesante", "beneficioso"],
    "suceder": ["algo diferente", "lo mismo", "algo inesperado"],
    "ocurrir": ["algo bueno", "lo contrario", "algo diferente"],

    # Desire/intention verbs
    "querer": ["más tiempo libre", "viajar al mundo", "un cambio"],
    "desear": ["lo mejor", "más tranquilidad", "un futuro mejor"],
    "preferir": ["quedarse en casa", "otra opción", "algo más sencillo"],
    "esperar": ["con paciencia", "buenas noticias", "lo mejor"],
    "intentar": ["otra vez", "algo nuevo", "con más fuerza"],
    "lograr": ["el objetivo", "más cosas", "grandes metas"],
    "conseguir": ["lo que quiero", "un mejor trabajo", "más apoyo"],
    "buscar": ["una solución", "un nuevo camino", "la felicidad"],
    "necesitar": ["más tiempo", "tu ayuda", "un descanso"],
    "pedir": ["un favor", "perdón", "más tiempo"],
    "permitir": ["más libertad", "la entrada", "un cambio"],
    "poder": ["hacer más", "ayudar a todos", "cambiar las cosas"],
    "deber": ["estudiar más", "ser más responsable", "actuar mejor"],
    "soler": ["ir al parque", "leer por las noches", "cocinar en casa"],

    # Physical action verbs
    "comer": ["más sano", "en un buen restaurante", "con la familia"],
    "beber": ["más agua", "un buen vino", "con moderación"],
    "dormir": ["más horas", "mejor", "toda la noche"],
    "despertar": ["más temprano", "con energía", "sin alarma"],
    "cortar": ["el césped", "las flores", "con cuidado"],
    "golpear": ["la mesa", "la puerta", "con fuerza"],
    "disparar": ["al aire", "con precisión", "sin dudar"],
    "tirar": ["la basura", "la pelota", "con fuerza"],
    "mover": ["los muebles", "la ficha", "con cuidado"],
    "cubrir": ["la mesa", "las necesidades", "todo bien"],
    "abrir": ["la puerta", "un negocio", "nuevos caminos"],
    "cerrar": ["la ventana", "el trato", "con llave"],
    "romper": ["las reglas", "el silencio", "con la rutina"],
    "tocar": ["la guitarra", "el piano", "una canción"],
    "pegar": ["el cartel", "los pedazos", "con cinta"],
    "meter": ["la mano", "las cosas en la maleta", "un gol"],
    "sacar": ["buenas notas", "la basura", "conclusiones"],
    "echar": ["de menos a todos", "una mano", "un vistazo"],
    "levantar": ["la mano", "la voz", "más peso"],
    "sentar": ["a los invitados", "las bases", "un precedente"],
    "soltar": ["la cuerda", "una carcajada", "la verdad"],
    "coger": ["el autobús", "la oportunidad", "el tren"],
    "recoger": ["la mesa", "los juguetes", "las flores"],

    # Change/transformation verbs
    "cambiar": ["de opinión", "el mundo", "de trabajo"],
    "convertir": ["la idea en realidad", "el problema en solución", "el sueño en meta"],
    "crecer": ["más rápido", "como persona", "sin límites"],
    "mejorar": ["cada día", "la situación", "las condiciones"],
    "superar": ["los obstáculos", "las dificultades", "el miedo"],
    "destruir": ["los prejuicios", "las barreras", "todo lo malo"],
    "recuperar": ["la confianza", "el tiempo perdido", "la salud"],

    # Social verbs
    "invitar": ["a todos", "a cenar", "a la boda"],
    "acompañar": ["a mi madre", "con gusto", "al hospital"],
    "compartir": ["la comida", "el momento", "con los demás"],
    "casar": ["por amor", "en la playa", "con una gran fiesta"],
    "reunir": ["a la familia", "a los amigos", "al equipo"],
    "unir": ["a las personas", "fuerzas", "los esfuerzos"],
    "separar": ["las cosas", "lo bueno de lo malo"],
    "ayudar": ["a los demás", "con el proyecto", "sin pedir nada"],
    "apoyar": ["la decisión", "al equipo", "con todo"],
    "proteger": ["a la familia", "el medio ambiente", "a los niños"],
    "defender": ["la verdad", "los derechos", "a los débiles"],
    "atacar": ["el problema", "con estrategia", "de frente"],
    "perdonar": ["con el corazón", "los errores", "sin rencor"],
    "disculpar": ["la tardanza", "el error", "la confusión"],
    "confiar": ["en ti", "más en los demás", "en el proceso"],
    "engañar": ["a nadie", "menos", "a los competidores"],
    "mentir": ["menos", "a nadie", "por ninguna razón"],
    "jurar": ["decir la verdad", "lealtad", "por mi honor"],
    "tratar": ["con respeto", "mejor a todos", "de entender"],

    # Other specific verbs
    "acabar": ["a tiempo", "el trabajo", "con los problemas"],
    "comenzar": ["de nuevo", "un proyecto", "desde cero"],
    "empezar": ["mañana mismo", "con buen pie", "sin retraso"],
    "terminar": ["a tiempo", "el libro", "con éxito"],
    "continuar": ["adelante", "el camino", "con esfuerzo"],
    "seguir": ["adelante", "el plan", "con la misión"],
    "parar": ["un momento", "la discusión", "de preocuparme"],
    "funcionar": ["mejor", "sin problemas", "de otra manera"],
    "costar": ["menos esfuerzo", "más barato", "un poco más"],
    "bastar": ["con poco", "para todos", "una explicación"],
    "valer": ["la pena", "mucho más", "cada centavo"],
    "significar": ["mucho", "un gran cambio", "algo especial"],
    "pertenecer": ["al grupo", "a la comunidad", "a otro lugar"],
    "depender": ["de ti", "de las circunstancias", "de la suerte"],
    "pesar": ["menos", "más que antes", "lo justo"],

    "admitir": ["el error", "la verdad", "nuevos miembros"],
    "asegurar": ["el éxito", "la victoria", "el futuro"],
    "abandonar": ["los malos hábitos", "el barco", "la idea"],
    "acordar": ["un plan", "una reunión", "los términos"],
    "actuar": ["con más calma", "de otra manera", "con responsabilidad"],
    "aforar": ["el lugar", "el recinto", "la sala"],
    "agradecer": ["la ayuda", "cada momento", "con sinceridad"],
    "alcanzar": ["la meta", "el éxito", "la cima"],
    "apartar": ["los obstáculos", "las dudas", "las distracciones"],
    "apostar": ["por el cambio", "al favorito", "con prudencia"],
    "aprender": ["más rápido", "otro idioma", "de los errores"],
    "atrapar": ["al ladrón", "la pelota", "el momento"],
    "conducir": ["con cuidado", "por la autopista", "hasta la ciudad"],
    "cumplir": ["la promesa", "con mi deber", "los objetivos"],
    "demostrar": ["la verdad", "su inocencia", "con hechos"],
    "desaparecer": ["sin dejar rastro", "por completo", "de la vista"],
    "despedir": ["con un abrazo", "a los invitados", "con cariño"],
    "discutir": ["el tema", "con argumentos", "sin pelear"],
    "enfrentar": ["el desafío", "la realidad", "los problemas"],
    "enseñar": ["con paciencia", "a los niños", "el camino"],
    "enterar": ["a todos", "de la noticia", "al jefe"],
    "esconder": ["la sorpresa", "los regalos", "la verdad"],
    "evitar": ["los problemas", "el conflicto", "errores"],
    "incluir": ["a todos", "más opciones", "los detalles"],
    "jugar": ["con los niños", "al fútbol", "más seguido"],
    "luchar": ["por los derechos", "con valor", "hasta el final"],
    "mandar": ["un mensaje", "las flores", "saludos"],
    "matar": ["el tiempo", "el aburrimiento", "dos pájaros de un tiro"],
    "merecer": ["un descanso", "una oportunidad", "lo mejor"],
    "mostrar": ["el camino", "los resultados", "la verdad"],
    "negar": ["las acusaciones", "la entrada", "la evidencia"],
    "ocupar": ["el primer lugar", "más espacio", "un puesto importante"],
    "olvidar": ["los problemas", "el pasado", "las preocupaciones"],
    "pasar": ["más tiempo juntos", "un buen rato", "por tu casa"],
    "pelear": ["por lo justo", "con honor", "menos"],
    "permanecer": ["en silencio", "tranquilo", "firme"],
    "perder": ["menos tiempo", "el miedo", "la paciencia"],
    "probar": ["algo nuevo", "la comida", "suerte"],
    "quedar": ["en casa", "más tiempo", "con los amigos"],
    "quitar": ["las dudas", "el estrés", "los obstáculos"],
    "salvar": ["la situación", "al mundo", "muchas vidas"],
    "servir": ["con honor", "la cena", "de ejemplo"],
    "tener": ["más paciencia", "más tiempo", "más suerte"],
    "tomar": ["una decisión", "un descanso", "las riendas"],
    "traer": ["buenas noticias", "la comida", "un regalo"],
    "tranquilar": ["a los niños", "la situación", "los ánimos"],
    "usar": ["mejor el tiempo", "la tecnología", "las herramientas"],
    "utilizar": ["los recursos", "otra estrategia", "la lógica"],
    "convertir": ["la idea en realidad", "el obstáculo en oportunidad", "el sueño en meta"],
    "detener": ["el avance", "el tiempo", "la caída"],
    "haber": ["más oportunidades", "menos problemas", "más tiempo"],
    "joder": ["menos las cosas", "la situación", "el ambiente"],
    "sonar": ["la alarma", "el teléfono", "la campana"],
    "suponer": ["un gran cambio", "un reto", "una mejora"],
}


def get_complement(verb, exercise_idx, template_idx):
    """Get a complement for the verb, preferring verb-specific ones."""
    if verb in VERB_SPECIFIC:
        specifics = VERB_SPECIFIC[verb]
        idx = (exercise_idx * 3 + template_idx) % len(specifics)
        return specifics[idx]
    # Fall back to template's complement pool
    return None


def generate_exercises():
    """Generate all 780 exercises."""
    all_exercises = []

    for verb_idx, verb in enumerate(VERBS):
        for ex_idx in range(3):
            template_group = EXERCISE_TEMPLATES[ex_idx]
            # Pick a template from the group, cycling through
            tmpl_idx = verb_idx % len(template_group["templates"])
            tmpl = template_group["templates"][tmpl_idx]

            subject = tmpl["subject"]
            context_phrase = tmpl["context"]

            # Get complement
            complement = get_complement(verb, ex_idx, tmpl_idx)
            if complement is None:
                comp_idx = (verb_idx * 3 + ex_idx) % len(tmpl["complement_pool"])
                complement = tmpl["complement_pool"][comp_idx]

            # Conjugate
            conjugated = conjugate_conditional(verb, subject)

            # Build sentence
            sentence = tmpl["sentence"].format(
                verb=conjugated,
                complement=complement,
                context=context_phrase
            )

            # Build contexto field
            contexto = f"{subject}, {context_phrase}, {complement}"

            # Build hint
            hint = tmpl["hint"]

            # Build grupos (no accents)
            subject_unaccented = remove_accents(subject)
            verb_unaccented = remove_accents(conjugated)
            complement_unaccented = remove_accents(complement)
            context_unaccented = remove_accents(context_phrase)

            grupos = [
                [subject_unaccented],
                [verb_unaccented],
                [complement_unaccented],
                [context_unaccented]
            ]

            exercise = {
                "id": f"{verb}-condicional-{ex_idx}",
                "verbo": verb,
                "contexto": contexto,
                "respuesta": sentence,
                "pista": hint,
                "grupos": grupos
            }

            all_exercises.append(exercise)

    return all_exercises


def validate_exercise(ex):
    """Validate that all grupo elements appear in the respuesta."""
    resp_lower = remove_accents(ex["respuesta"].lower().rstrip("."))
    errors = []
    for g_idx, grupo in enumerate(ex["grupos"]):
        for element in grupo:
            elem_lower = element.lower()
            if elem_lower not in resp_lower:
                errors.append(f"  grupo[{g_idx}] '{element}' not in respuesta '{ex['respuesta']}'")
    return errors


def main():
    exercises = generate_exercises()
    print(f"Generated {len(exercises)} exercises for {len(VERBS)} verbs")

    # Validate
    total_errors = 0
    for ex in exercises:
        errors = validate_exercise(ex)
        if errors:
            total_errors += len(errors)
            print(f"ERRORS in {ex['id']}:")
            for e in errors:
                print(e)

    print(f"Total validation errors: {total_errors}")

    # Check for accents in grupos
    accent_errors = 0
    for ex in exercises:
        for g_idx, grupo in enumerate(ex["grupos"]):
            for element in grupo:
                if element != remove_accents(element):
                    accent_errors += 1
                    print(f"ACCENT in grupo: {ex['id']} grupo[{g_idx}] '{element}'")

    print(f"Total accent errors in grupos: {accent_errors}")

    # Split into 18 batches of ~15 verbs each (260 verbs / 18 = ~14.4)
    # 15 verbs * 3 exercises = 45 exercises per batch for most
    # 260 = 15*14 + 14*1 + ... let's do 15 verbs for first 8 batches, 14 for next 10
    # Actually: 15*12 = 180, 14*8 = 112, 180+112 = 292 too many
    # 260 / 18 = 14.44 -> 14 batches of 15 verbs (210 verbs) + 4 batches of ... no
    # Let's just: first 8 batches get 15 verbs, next 10 get 14 verbs
    # 8*15 + 10*14 = 120 + 140 = 260. Yes!

    batch_sizes = [15]*8 + [14]*10  # 8*15 + 10*14 = 120 + 140 = 260
    assert sum(batch_sizes) == 260

    verb_offset = 0
    for batch_idx, batch_size in enumerate(batch_sizes):
        batch_verbs = VERBS[verb_offset:verb_offset + batch_size]
        batch_exercises = []
        for ex in exercises:
            if ex["verbo"] in batch_verbs:
                batch_exercises.append(ex)

        filename = os.path.join(OUTPUT_DIR, f"batch_{batch_idx:03d}.json")
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(batch_exercises, f, ensure_ascii=False, indent=2)

        print(f"Wrote {filename}: {len(batch_exercises)} exercises ({batch_size} verbs: {batch_verbs[0]}..{batch_verbs[-1]})")
        verb_offset += batch_size

    print(f"\nDone. {len(exercises)} exercises across {len(batch_sizes)} batch files.")


if __name__ == "__main__":
    main()
