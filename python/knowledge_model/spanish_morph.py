"""Regular Spanish conjugation for the drill's ten tense categories.

Used ONLY to classify (verb, tense) cells as regular or irregular by
comparing the generated regular form against the answer the exercise
actually expects. A cell whose observed forms all match the regular
generation shares that tense's family rule node in the knowledge graph;
a mismatch makes it verb-specific (irregular).
"""

PERSONS = ["1s", "2s", "3s", "1p", "2p", "3p"]

PRONOUNS = {
    "yo": "1s", "tú": "2s", "tu": "2s", "vos": "2s",
    "él": "3s", "el": "3s", "ella": "3s", "usted": "3s", "uno": "3s",
    "nosotros": "1p", "nosotras": "1p",
    "vosotros": "2p", "vosotras": "2p",
    "ellos": "3p", "ellas": "3p", "ustedes": "3p",
}

ENDINGS = {
    # simple tenses: {family: [endings by person]}
    "presente": {
        "ar": ["o", "as", "a", "amos", "áis", "an"],
        "er": ["o", "es", "e", "emos", "éis", "en"],
        "ir": ["o", "es", "e", "imos", "ís", "en"],
    },
    "puntual": {  # pretérito indefinido
        "ar": ["é", "aste", "ó", "amos", "asteis", "aron"],
        "er": ["í", "iste", "ió", "imos", "isteis", "ieron"],
        "ir": ["í", "iste", "ió", "imos", "isteis", "ieron"],
    },
    "imperfecto": {  # habitual + fondo
        "ar": ["aba", "abas", "aba", "ábamos", "abais", "aban"],
        "er": ["ía", "ías", "ía", "íamos", "íais", "ían"],
        "ir": ["ía", "ías", "ía", "íamos", "íais", "ían"],
    },
    "subjuntivo": {  # presente de subjuntivo
        "ar": ["e", "es", "e", "emos", "éis", "en"],
        "er": ["a", "as", "a", "amos", "áis", "an"],
        "ir": ["a", "as", "a", "amos", "áis", "an"],
    },
    "subj_imperfecto": {  # -ra forms
        "ar": ["ara", "aras", "ara", "áramos", "arais", "aran"],
        "er": ["iera", "ieras", "iera", "iéramos", "ierais", "ieran"],
        "ir": ["iera", "ieras", "iera", "iéramos", "ierais", "ieran"],
    },
}

# futuro / condicional attach to the full infinitive
FUT_COND_ENDINGS = {
    "futuro": ["é", "ás", "á", "emos", "éis", "án"],
    "condicional": ["ía", "ías", "ía", "íamos", "íais", "ían"],
}

# Auxiliary "haber" for the compound categories the drill uses.
HABER = {
    "anterior": ["había", "habías", "había", "habíamos", "habíais", "habían"],
    "perfecto": ["he", "has", "ha", "hemos", "habéis", "han"],
    "subj_pluscuam": ["hubiera", "hubieras", "hubiera", "hubiéramos", "hubierais", "hubieran"],
    "cond_perfecto": ["habría", "habrías", "habría", "habríamos", "habríais", "habrían"],
}

IRREGULAR_PARTICIPLES = {
    "abrir": "abierto", "cubrir": "cubierto", "descubrir": "descubierto",
    "decir": "dicho", "escribir": "escrito", "hacer": "hecho",
    "morir": "muerto", "poner": "puesto", "resolver": "resuelto",
    "romper": "roto", "ver": "visto", "volver": "vuelto",
    "devolver": "devuelto", "ir": "ido", "freír": "frito",
}


def family(verb):
    for f in ("ar", "er", "ir"):
        if verb.endswith(f):
            return f
    if verb.endswith("ír"):  # oír, reír
        return "ir"
    return None


def stem(verb):
    return verb[:-2]


def participle(verb):
    if verb in IRREGULAR_PARTICIPLES:
        return IRREGULAR_PARTICIPLES[verb]
    f = family(verb)
    return stem(verb) + ("ado" if f == "ar" else "ido")


def regular_forms(verb, tense):
    """All six regular person-forms for a (verb, drill-tense) pair.

    Returns {person: form} or None if the tense is unknown. Compound
    categories return 'aux participle' strings.
    """
    f = family(verb)
    if f is None:
        return None
    if tense in ("habitual", "fondo"):
        key = "imperfecto"
    else:
        key = tense
    if key in ENDINGS:
        s = stem(verb)
        return {p: s + e for p, e in zip(PERSONS, ENDINGS[key][f])}
    if key in FUT_COND_ENDINGS:
        return {p: verb + e for p, e in zip(PERSONS, FUT_COND_ENDINGS[key])}
    if key == "anterior":
        part = participle(verb)
        return {p: aux + " " + part for p, aux in zip(PERSONS, HABER["anterior"])}
    if key == "subj_pluscuam":
        part = participle(verb)
        return {p: aux + " " + part for p, aux in zip(PERSONS, HABER["subj_pluscuam"])}
    return None
