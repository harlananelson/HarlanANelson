#!/usr/bin/env python3
"""Generate Spanish present indicative speech drill exercises for 260 verbs."""

import json
import os
import random

random.seed(42)

OUTPUT_DIR = "/home/harlan/projects/harlananelson/python/output/presente"

# All 260 verbs in order
VERBS = [
    "abandonar", "abrir", "acabar", "aceptar", "acercar", "acompañar", "acordar", "actuar",
    "admitir", "aforar", "agradecer", "alcanzar", "alegrar", "alejar", "amar", "andar",
    "aparecer", "apartar", "apostar", "apoyar", "aprender", "arreglar", "asegurar", "asesinar",
    "asustar", "atacar", "atrapar", "averiguar", "ayudar", "bailar", "bajar", "bastar",
    "beber", "besar", "buscar", "caer", "callar", "calmar", "cambiar", "caminar",
    "cantar", "casar", "cerrar", "coger", "comenzar", "comer", "cometer", "compartir",
    "comprar", "comprender", "conducir", "confiar", "conocer", "conseguir", "considerar", "construir",
    "contar", "contestar", "continuar", "controlar", "convertir", "correr", "cortar", "costar",
    "crear", "crecer", "creer", "cubrir", "cuidar", "cumplir", "dar", "deber",
    "decidir", "decir", "defender", "dejar", "demostrar", "depender", "desaparecer", "desarrollar",
    "descubrir", "desear", "despedir", "despertar", "destruir", "detener", "devolver", "dirigir",
    "disculpar", "discutir", "disfrutar", "disparar", "dormir", "echar", "elegir", "empezar",
    "encantar", "encontrar", "enfrentar", "engañar", "enseñar", "entender", "enterar", "entrar",
    "entregar", "enviar", "escapar", "esconder", "escribir", "escuchar", "esperar", "estar",
    "estudiar", "evitar", "existir", "explicar", "formar", "funcionar", "ganar", "golpear",
    "gritar", "guardar", "gustar", "haber", "hablar", "hacer", "hallar", "huir",
    "imaginar", "importar", "incluir", "informar", "intentar", "interesar", "invitar", "ir",
    "joder", "jugar", "jurar", "leer", "levantar", "llamar", "llegar", "llevar",
    "llorar", "lograr", "luchar", "mandar", "manejar", "mantener", "marchar", "matar",
    "mencionar", "mentir", "merecer", "meter", "mirar", "molestar", "morir", "mostrar",
    "mover", "nacer", "necesitar", "negar", "observar", "obtener", "ocupar", "ocurrir",
    "odiar", "ofrecer", "oír", "olvidar", "pagar", "parar", "parecer", "partir",
    "pasar", "pedir", "pegar", "pelear", "pensar", "perder", "perdonar", "permanecer",
    "permitir", "pertenecer", "pesar", "poder", "poner", "preferir", "preguntar", "preocupar",
    "preparar", "presentar", "prestar", "probar", "producir", "prometer", "proteger", "quedar",
    "querer", "quitar", "realizar", "recibir", "recoger", "reconocer", "recordar", "recuperar",
    "referir", "regresar", "reír", "repetir", "representar", "resolver", "responder", "resultar",
    "reunir", "revisar", "robar", "romper", "saber", "sacar", "salir", "salvar",
    "seguir", "señalar", "sentar", "sentir", "ser", "servir", "significar", "soler",
    "soltar", "sonar", "subir", "suceder", "sufrir", "superar", "suponer", "temer",
    "tener", "terminar", "tirar", "tocar", "tomar", "trabajar", "traer", "tranquilar",
    "tratar", "unir", "usar", "utilizar", "valer", "vender", "venir", "ver",
    "viajar", "vivir", "volar", "volver"
]

assert len(VERBS) == 260, f"Expected 260 verbs, got {len(VERBS)}"

# Time phrases with usage tracking
TIME_PHRASES = [
    "ahora", "hoy", "esta mañana", "esta tarde", "esta noche",
    "en este momento", "ahora mismo", "actualmente",
    "todos los días", "cada semana", "normalmente", "siempre",
    "a veces", "por lo general", "cada vez que", "mientras"
]

time_phrase_counts = {tp: 0 for tp in TIME_PHRASES}

def get_time_phrase():
    """Pick a time phrase, preferring less-used ones. Cap at ~50 each."""
    available = [tp for tp in TIME_PHRASES if time_phrase_counts[tp] < 50]
    if not available:
        available = TIME_PHRASES  # fallback
    # Weight by inverse usage
    weights = [1.0 / (time_phrase_counts[tp] + 1) for tp in available]
    chosen = random.choices(available, weights=weights, k=1)[0]
    time_phrase_counts[chosen] += 1
    return chosen

def remove_accents(s):
    """Remove accent marks for grupos."""
    replacements = {
        'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u',
        'ü': 'u', 'ñ': 'n',
        'Á': 'A', 'É': 'E', 'Í': 'I', 'Ó': 'O', 'Ú': 'U',
        'Ü': 'U', 'Ñ': 'N'
    }
    for acc, plain in replacements.items():
        s = s.replace(acc, plain)
    return s

# Subject forms: (subject_in_sentence, subject_for_grupo_unaccented)
SUBJECTS = [
    ("yo", "yo"),
    ("tú", "tu"),
    ("él", "el"),
    ("ella", "ella"),
    ("nosotros", "nosotros"),
    ("ellos", "ellos"),
    ("ellas", "ellas"),
    ("usted", "usted"),
    ("ustedes", "ustedes"),
]

# Conjugation table for presente indicativo
# Format: {verb: {subject_key: conjugated_form}}
# subject_key: yo, tu, el, nosotros, ellos, usted, ustedes
# usted = el form, ustedes = ellos form

def get_regular_ar(stem):
    return {"yo": stem+"o", "tu": stem+"as", "el": stem+"a",
            "nosotros": stem+"amos", "ellos": stem+"an"}

def get_regular_er(stem):
    return {"yo": stem+"o", "tu": stem+"es", "el": stem+"e",
            "nosotros": stem+"emos", "ellos": stem+"en"}

def get_regular_ir(stem):
    return {"yo": stem+"o", "tu": stem+"es", "el": stem+"e",
            "nosotros": stem+"imos", "ellos": stem+"en"}

def get_stem_eie_ar(stem, strong_stem):
    """e->ie stem changing -ar verb."""
    return {"yo": strong_stem+"o", "tu": strong_stem+"as", "el": strong_stem+"a",
            "nosotros": stem+"amos", "ellos": strong_stem+"an"}

def get_stem_eie_er(stem, strong_stem):
    return {"yo": strong_stem+"o", "tu": strong_stem+"es", "el": strong_stem+"e",
            "nosotros": stem+"emos", "ellos": strong_stem+"en"}

def get_stem_eie_ir(stem, strong_stem):
    return {"yo": strong_stem+"o", "tu": strong_stem+"es", "el": strong_stem+"e",
            "nosotros": stem+"imos", "ellos": strong_stem+"en"}

def get_stem_oue_ar(stem, strong_stem):
    return {"yo": strong_stem+"o", "tu": strong_stem+"as", "el": strong_stem+"a",
            "nosotros": stem+"amos", "ellos": strong_stem+"an"}

def get_stem_oue_er(stem, strong_stem):
    return {"yo": strong_stem+"o", "tu": strong_stem+"es", "el": strong_stem+"e",
            "nosotros": stem+"emos", "ellos": strong_stem+"en"}

def get_stem_oue_ir(stem, strong_stem):
    return {"yo": strong_stem+"o", "tu": strong_stem+"es", "el": strong_stem+"e",
            "nosotros": stem+"imos", "ellos": strong_stem+"en"}

def get_stem_ei_ir(stem, strong_stem):
    """e->i stem changing -ir verb."""
    return {"yo": strong_stem+"o", "tu": strong_stem+"es", "el": strong_stem+"e",
            "nosotros": stem+"imos", "ellos": strong_stem+"en"}


# Build conjugation dictionary for all 260 verbs
CONJUGATIONS = {}

# Regular -ar verbs (the default for -ar endings)
regular_ar = [
    "abandonar", "acabar", "aceptar", "actuar", "alegrar", "alejar", "amar",
    "apartar", "apoyar", "arreglar", "asegurar", "asesinar", "asustar", "atacar",
    "atrapar", "averiguar", "ayudar", "bailar", "bajar", "bastar", "besar", "buscar",
    "callar", "calmar", "cambiar", "caminar", "cantar", "casar",
    "cometer", "comprar", "confiar", "considerar", "contestar",
    "controlar", "crear", "cuidar", "cumplir",
    "dejar", "desarrollar", "desear", "dirigir",
    "disculpar", "discutir", "disfrutar", "disparar", "echar",
    "enfrentar", "engañar", "enseñar", "enterar", "entrar",
    "entregar", "enviar", "escapar", "esconder", "escuchar", "esperar",
    "estudiar", "evitar", "explicar", "formar", "funcionar", "ganar", "golpear",
    "gritar", "guardar", "hablar", "imaginar", "informar",
    "intentar", "invitar",
    "jurar", "levantar", "llamar", "llegar", "llevar",
    "llorar", "lograr", "luchar", "mandar", "manejar", "marchar", "matar",
    "mencionar", "mirar", "molestar",
    "necesitar", "observar", "ocupar", "odiar", "olvidar", "pagar", "parar",
    "pasar", "pegar", "pelear", "perdonar",
    "pesar", "preguntar", "preocupar",
    "preparar", "presentar", "prestar", "prometer", "quedar",
    "quitar", "realizar", "regresar",
    "representar", "resultar",
    "revisar", "robar", "sacar", "salvar",
    "señalar", "significar",
    "superar", "terminar", "tirar", "tocar", "tomar", "trabajar",
    "tranquilar", "tratar", "unir", "usar", "utilizar", "viajar"
]

for v in regular_ar:
    stem = v[:-2]
    CONJUGATIONS[v] = get_regular_ar(stem)

# Regular -er verbs
regular_er = [
    "beber", "comer", "comprender", "correr", "creer",
    "deber", "depender", "meter", "responder", "temer", "vender"
]
for v in regular_er:
    stem = v[:-2]
    CONJUGATIONS[v] = get_regular_er(stem)

# Regular -ir verbs
regular_ir = [
    "abrir", "admitir", "compartir", "cubrir", "decidir", "descubrir",
    "escribir", "existir", "ocurrir", "partir", "permitir", "recibir",
    "subir", "suceder", "sufrir", "vivir"
]
for v in regular_ir:
    stem = v[:-2]
    CONJUGATIONS[v] = get_regular_ir(stem)

# Fix: suceder and temer are -er
CONJUGATIONS["suceder"] = get_regular_er("suced")
# sufrir, subir are -ir (already set)

# Stem-changing e->ie
# -ar: cerrar, pensar, comenzar, empezar, apostar (o->ue actually), despertar, negar, sentar
CONJUGATIONS["cerrar"] = get_stem_eie_ar("cerr", "cierr")
CONJUGATIONS["pensar"] = get_stem_eie_ar("pens", "piens")
CONJUGATIONS["comenzar"] = get_stem_eie_ar("comenz", "comienz")
CONJUGATIONS["empezar"] = get_stem_eie_ar("empez", "empiez")
CONJUGATIONS["despertar"] = get_stem_eie_ar("despert", "despiert")
CONJUGATIONS["negar"] = get_stem_eie_ar("neg", "nieg")
CONJUGATIONS["sentar"] = get_stem_eie_ar("sent", "sient")
CONJUGATIONS["acercar"] = get_regular_ar("acerc")  # regular
CONJUGATIONS["alcanzar"] = get_regular_ar("alcanz")  # regular

# -er: entender, perder, defender, querer
CONJUGATIONS["entender"] = get_stem_eie_er("entend", "entiend")
CONJUGATIONS["perder"] = get_stem_eie_er("perd", "pierd")
CONJUGATIONS["defender"] = get_stem_eie_er("defend", "defiend")
CONJUGATIONS["querer"] = get_stem_eie_er("quer", "quier")

# -ir: sentir, preferir, mentir, convertir, referir
CONJUGATIONS["sentir"] = get_stem_eie_ir("sent", "sient")
CONJUGATIONS["preferir"] = get_stem_eie_ir("prefer", "prefier")
CONJUGATIONS["mentir"] = get_stem_eie_ir("ment", "mient")
CONJUGATIONS["convertir"] = get_stem_eie_ir("convert", "conviert")
CONJUGATIONS["referir"] = get_stem_eie_ir("refer", "refier")

# Stem-changing o->ue
# -ar: acordar, apostar, contar, encontrar, recordar, mostrar, costar, demostrar, soltar, sonar, volar
CONJUGATIONS["acordar"] = get_stem_oue_ar("acord", "acuerd")
CONJUGATIONS["apostar"] = get_stem_oue_ar("apost", "apuest")
CONJUGATIONS["contar"] = get_stem_oue_ar("cont", "cuent")
CONJUGATIONS["encontrar"] = get_stem_oue_ar("encontr", "encuentr")
CONJUGATIONS["recordar"] = get_stem_oue_ar("record", "recuerd")
CONJUGATIONS["mostrar"] = get_stem_oue_ar("mostr", "muestr")
CONJUGATIONS["costar"] = get_stem_oue_ar("cost", "cuest")
CONJUGATIONS["demostrar"] = get_stem_oue_ar("demostr", "demuestr")
CONJUGATIONS["soltar"] = get_stem_oue_ar("solt", "suelt")
CONJUGATIONS["sonar"] = get_stem_oue_ar("son", "suen")
CONJUGATIONS["volar"] = get_stem_oue_ar("vol", "vuel")
CONJUGATIONS["probar"] = get_stem_oue_ar("prob", "prueb")
CONJUGATIONS["rogar"] = get_stem_oue_ar("rog", "rueg")  # not in list but just in case

# -er: poder, volver, mover, soler, devolver, resolver
CONJUGATIONS["poder"] = get_stem_oue_er("pod", "pued")
CONJUGATIONS["volver"] = get_stem_oue_er("volv", "vuelv")
CONJUGATIONS["mover"] = get_stem_oue_er("mov", "muev")
CONJUGATIONS["soler"] = get_stem_oue_er("sol", "suel")
CONJUGATIONS["devolver"] = get_stem_oue_er("devolv", "devuelv")
CONJUGATIONS["resolver"] = get_stem_oue_er("resolv", "resuelv")

# -ir: dormir, morir
CONJUGATIONS["dormir"] = get_stem_oue_ir("dorm", "duerm")
CONJUGATIONS["morir"] = get_stem_oue_ir("mor", "muer")

# u->ue: jugar
CONJUGATIONS["jugar"] = {"yo": "juego", "tu": "juegas", "el": "juega",
                          "nosotros": "jugamos", "ellos": "juegan"}

# Stem-changing e->i (-ir verbs)
CONJUGATIONS["pedir"] = get_stem_ei_ir("ped", "pid")
CONJUGATIONS["seguir"] = {"yo": "sigo", "tu": "sigues", "el": "sigue",
                           "nosotros": "seguimos", "ellos": "siguen"}
CONJUGATIONS["repetir"] = get_stem_ei_ir("repet", "repit")
CONJUGATIONS["servir"] = get_stem_ei_ir("serv", "sirv")
CONJUGATIONS["elegir"] = {"yo": "elijo", "tu": "eliges", "el": "elige",
                           "nosotros": "elegimos", "ellos": "eligen"}
CONJUGATIONS["conseguir"] = {"yo": "consigo", "tu": "consigues", "el": "consigue",
                              "nosotros": "conseguimos", "ellos": "consiguen"}
CONJUGATIONS["despedir"] = get_stem_ei_ir("desped", "despid")
CONJUGATIONS["reír"] = {"yo": "río", "tu": "ríes", "el": "ríe",
                         "nosotros": "reímos", "ellos": "ríen"}

# -cer/-cir verbs (yo -> -zco)
CONJUGATIONS["conocer"] = {"yo": "conozco", "tu": "conoces", "el": "conoce",
                            "nosotros": "conocemos", "ellos": "conocen"}
CONJUGATIONS["parecer"] = {"yo": "parezco", "tu": "pareces", "el": "parece",
                            "nosotros": "parecemos", "ellos": "parecen"}
CONJUGATIONS["ofrecer"] = {"yo": "ofrezco", "tu": "ofreces", "el": "ofrece",
                            "nosotros": "ofrecemos", "ellos": "ofrecen"}
CONJUGATIONS["aparecer"] = {"yo": "aparezco", "tu": "apareces", "el": "aparece",
                             "nosotros": "aparecemos", "ellos": "aparecen"}
CONJUGATIONS["desaparecer"] = {"yo": "desaparezco", "tu": "desapareces", "el": "desaparece",
                                "nosotros": "desaparecemos", "ellos": "desaparecen"}
CONJUGATIONS["agradecer"] = {"yo": "agradezco", "tu": "agradeces", "el": "agradece",
                              "nosotros": "agradecemos", "ellos": "agradecen"}
CONJUGATIONS["crecer"] = {"yo": "crezco", "tu": "creces", "el": "crece",
                           "nosotros": "crecemos", "ellos": "crecen"}
CONJUGATIONS["merecer"] = {"yo": "merezco", "tu": "mereces", "el": "merece",
                            "nosotros": "merecemos", "ellos": "merecen"}
CONJUGATIONS["permanecer"] = {"yo": "permanezco", "tu": "permaneces", "el": "permanece",
                               "nosotros": "permanecemos", "ellos": "permanecen"}
CONJUGATIONS["pertenecer"] = {"yo": "pertenezco", "tu": "perteneces", "el": "pertenece",
                               "nosotros": "pertenecemos", "ellos": "pertenecen"}
CONJUGATIONS["reconocer"] = {"yo": "reconozco", "tu": "reconoces", "el": "reconoce",
                              "nosotros": "reconocemos", "ellos": "reconocen"}
CONJUGATIONS["conducir"] = {"yo": "conduzco", "tu": "conduces", "el": "conduce",
                             "nosotros": "conducimos", "ellos": "conducen"}
CONJUGATIONS["producir"] = {"yo": "produzco", "tu": "produces", "el": "produce",
                             "nosotros": "producimos", "ellos": "producen"}

# -uir verbs (add y)
CONJUGATIONS["incluir"] = {"yo": "incluyo", "tu": "incluyes", "el": "incluye",
                            "nosotros": "incluimos", "ellos": "incluyen"}
CONJUGATIONS["construir"] = {"yo": "construyo", "tu": "construyes", "el": "construye",
                              "nosotros": "construimos", "ellos": "construyen"}
CONJUGATIONS["destruir"] = {"yo": "destruyo", "tu": "destruyes", "el": "destruye",
                             "nosotros": "destruimos", "ellos": "destruyen"}
CONJUGATIONS["huir"] = {"yo": "huyo", "tu": "huyes", "el": "huye",
                         "nosotros": "huimos", "ellos": "huyen"}
CONJUGATIONS["reunir"] = {"yo": "reúno", "tu": "reúnes", "el": "reúne",
                           "nosotros": "reunimos", "ellos": "reúnen"}
CONJUGATIONS["continuar"] = get_regular_ar("continu")  # stress shift but spelling regular in present

# Highly irregular verbs
CONJUGATIONS["ser"] = {"yo": "soy", "tu": "eres", "el": "es",
                        "nosotros": "somos", "ellos": "son"}
CONJUGATIONS["estar"] = {"yo": "estoy", "tu": "estás", "el": "está",
                          "nosotros": "estamos", "ellos": "están"}
CONJUGATIONS["ir"] = {"yo": "voy", "tu": "vas", "el": "va",
                       "nosotros": "vamos", "ellos": "van"}
CONJUGATIONS["haber"] = {"yo": "he", "tu": "has", "el": "ha",
                          "nosotros": "hemos", "ellos": "han"}
CONJUGATIONS["tener"] = {"yo": "tengo", "tu": "tienes", "el": "tiene",
                          "nosotros": "tenemos", "ellos": "tienen"}
CONJUGATIONS["hacer"] = {"yo": "hago", "tu": "haces", "el": "hace",
                          "nosotros": "hacemos", "ellos": "hacen"}
CONJUGATIONS["decir"] = {"yo": "digo", "tu": "dices", "el": "dice",
                          "nosotros": "decimos", "ellos": "dicen"}
CONJUGATIONS["venir"] = {"yo": "vengo", "tu": "vienes", "el": "viene",
                          "nosotros": "venimos", "ellos": "vienen"}
CONJUGATIONS["poner"] = {"yo": "pongo", "tu": "pones", "el": "pone",
                          "nosotros": "ponemos", "ellos": "ponen"}
CONJUGATIONS["salir"] = {"yo": "salgo", "tu": "sales", "el": "sale",
                          "nosotros": "salimos", "ellos": "salen"}
CONJUGATIONS["dar"] = {"yo": "doy", "tu": "das", "el": "da",
                        "nosotros": "damos", "ellos": "dan"}
CONJUGATIONS["saber"] = {"yo": "sé", "tu": "sabes", "el": "sabe",
                          "nosotros": "sabemos", "ellos": "saben"}
CONJUGATIONS["oír"] = {"yo": "oigo", "tu": "oyes", "el": "oye",
                        "nosotros": "oímos", "ellos": "oyen"}
CONJUGATIONS["caer"] = {"yo": "caigo", "tu": "caes", "el": "cae",
                         "nosotros": "caemos", "ellos": "caen"}
CONJUGATIONS["traer"] = {"yo": "traigo", "tu": "traes", "el": "trae",
                          "nosotros": "traemos", "ellos": "traen"}
CONJUGATIONS["valer"] = {"yo": "valgo", "tu": "vales", "el": "vale",
                          "nosotros": "valemos", "ellos": "valen"}
CONJUGATIONS["ver"] = {"yo": "veo", "tu": "ves", "el": "ve",
                        "nosotros": "vemos", "ellos": "ven"}
CONJUGATIONS["suponer"] = {"yo": "supongo", "tu": "supones", "el": "supone",
                            "nosotros": "suponemos", "ellos": "suponen"}
CONJUGATIONS["detener"] = {"yo": "detengo", "tu": "detienes", "el": "detiene",
                            "nosotros": "detenemos", "ellos": "detienen"}
CONJUGATIONS["mantener"] = {"yo": "mantengo", "tu": "mantienes", "el": "mantiene",
                             "nosotros": "mantenemos", "ellos": "mantienen"}
CONJUGATIONS["obtener"] = {"yo": "obtengo", "tu": "obtienes", "el": "obtiene",
                            "nosotros": "obtenemos", "ellos": "obtienen"}
CONJUGATIONS["proteger"] = {"yo": "protejo", "tu": "proteges", "el": "protege",
                             "nosotros": "protegemos", "ellos": "protegen"}
CONJUGATIONS["recoger"] = {"yo": "recojo", "tu": "recoges", "el": "recoge",
                            "nosotros": "recogemos", "ellos": "recogen"}
CONJUGATIONS["coger"] = {"yo": "cojo", "tu": "coges", "el": "coge",
                          "nosotros": "cogemos", "ellos": "cogen"}
CONJUGATIONS["dirigir"] = {"yo": "dirijo", "tu": "diriges", "el": "dirige",
                            "nosotros": "dirigimos", "ellos": "dirigen"}
CONJUGATIONS["corregir"] = {"yo": "corrijo", "tu": "corriges", "el": "corrige",
                             "nosotros": "corregimos", "ellos": "corrigen"}
CONJUGATIONS["hallar"] = get_regular_ar("hall")
CONJUGATIONS["andar"] = get_regular_ar("and")  # regular in present

# gustar, encantar, importar, interesar, molestar - typically used with indirect object
# but conjugation itself is regular
CONJUGATIONS["gustar"] = get_regular_ar("gust")
CONJUGATIONS["encantar"] = get_regular_ar("encant")
CONJUGATIONS["importar"] = get_regular_ar("import")
CONJUGATIONS["interesar"] = get_regular_ar("interes")
CONJUGATIONS["molestar"] = get_regular_ar("molest")

# joder - regular -er
CONJUGATIONS["joder"] = get_regular_er("jod")

# leer - regular -er (but yo form is leo, regular)
CONJUGATIONS["leer"] = get_regular_er("le")

# cortar - regular -ar
CONJUGATIONS["cortar"] = get_regular_ar("cort")

# recuperar
CONJUGATIONS["recuperar"] = get_regular_ar("recuper")

# romper - regular -er
CONJUGATIONS["romper"] = get_regular_er("romp")

# aforar - regular -ar (o->ue? No, aforar is regular)
CONJUGATIONS["aforar"] = get_regular_ar("afor")

# acompañar
CONJUGATIONS["acompañar"] = get_regular_ar("acompañ")

# aprender - regular -er
CONJUGATIONS["aprender"] = get_regular_er("aprend")

# continuar - regular (accent on u in some forms but spelling is regular for our purposes)
# already set above

# correr - regular -er
CONJUGATIONS["correr"] = get_regular_er("corr")

# Now check which verbs are missing
missing = [v for v in VERBS if v not in CONJUGATIONS]
# Fill in any remaining with regular conjugation based on ending
for v in missing:
    if v.endswith("ar"):
        CONJUGATIONS[v] = get_regular_ar(v[:-2])
    elif v.endswith("er"):
        CONJUGATIONS[v] = get_regular_er(v[:-2])
    elif v.endswith("ir") or v.endswith("ír"):
        stem = v[:-2] if v.endswith("ir") else v[:-2]
        CONJUGATIONS[v] = get_regular_ir(stem)

# Double check all verbs have conjugations
for v in VERBS:
    assert v in CONJUGATIONS, f"Missing conjugation for {v}"

def get_conjugation(verb, subject_key):
    """Get conjugated form. subject_key is yo/tu/el/nosotros/ellos.
    usted uses el form, ustedes uses ellos form."""
    conj = CONJUGATIONS[verb]
    if subject_key in ("usted", "ustedes"):
        mapped = "el" if subject_key == "usted" else "ellos"
        return conj[mapped]
    return conj[subject_key]

def subject_key_from_subject(subj):
    """Map subject string to conjugation key."""
    mapping = {
        "yo": "yo", "tú": "tu", "él": "el", "ella": "el",
        "nosotros": "nosotros", "ellos": "ellos", "ellas": "ellos",
        "usted": "usted", "ustedes": "ustedes"
    }
    return mapping[subj]

# Context templates per verb - these provide the complement portion
# We need varied, natural sentences

# A large pool of complements for different verb types
# Format: (complement, hint_text)
# We'll build exercise data with specific templates per verb

def make_exercises():
    """Generate 3 exercises per verb."""
    all_exercises = []

    # Track which subjects we've used per verb to ensure variety
    # We need 3 different subjects per verb

    # Define exercise templates for each verb
    # Each entry: (subject, complement, hint)

    verb_templates = {
        "abandonar": [
            ("yo", "la ciudad", "expressing a current decision"),
            ("ellos", "el proyecto", "describing what they do"),
            ("tú", "tus planes antiguos", "talking about a habit"),
        ],
        "abrir": [
            ("yo", "la puerta", "describing a current action"),
            ("ella", "el libro", "narrating what she does"),
            ("nosotros", "las ventanas", "describing a routine"),
        ],
        "acabar": [
            ("yo", "el trabajo", "expressing completion"),
            ("tú", "la tarea", "describing what you do"),
            ("ellos", "la comida", "narrating present actions"),
        ],
        "aceptar": [
            ("nosotros", "la oferta", "making a decision now"),
            ("él", "las condiciones", "describing his action"),
            ("yo", "la invitación", "expressing current acceptance"),
        ],
        "acercar": [
            ("yo", "la silla a la mesa", "describing a current action"),
            ("ella", "el vaso", "narrating present events"),
            ("ustedes", "los documentos", "addressing a group formally"),
        ],
        "acompañar": [
            ("yo", "a mi madre", "expressing a present action"),
            ("tú", "a tu amigo al hospital", "describing what you do"),
            ("nosotros", "a los niños a la escuela", "talking about a routine"),
        ],
        "acordar": [
            ("nosotros", "los términos del contrato", "reaching agreement now"),
            ("ellos", "una fecha para la reunión", "describing their action"),
            ("yo", "una cita con el doctor", "expressing current planning"),
        ],
        "actuar": [
            ("él", "en la película", "describing his current role"),
            ("yo", "con responsabilidad", "expressing how I behave"),
            ("ellas", "en el teatro", "narrating present activities"),
        ],
        "admitir": [
            ("yo", "mi error", "confessing something now"),
            ("tú", "la verdad", "describing what you do"),
            ("él", "sus problemas", "narrating his action"),
        ],
        "aforar": [
            ("nosotros", "el río", "describing a measurement activity"),
            ("él", "el caudal del agua", "expressing a technical action"),
            ("yo", "la capacidad del tanque", "talking about current work"),
        ],
        "agradecer": [
            ("yo", "tu ayuda", "expressing gratitude now"),
            ("nosotros", "la oportunidad", "showing appreciation"),
            ("ella", "el regalo", "describing her reaction"),
        ],
        "alcanzar": [
            ("tú", "tus metas", "describing achievement"),
            ("nosotros", "el objetivo", "expressing team progress"),
            ("ella", "el estante alto", "narrating a present action"),
        ],
        "alegrar": [
            ("yo", "a mis padres", "expressing what makes others happy"),
            ("ella", "a todos con su sonrisa", "describing her effect"),
            ("tú", "a tus amigos", "talking about your personality"),
        ],
        "alejar": [
            ("yo", "el peligro", "expressing a protective action"),
            ("nosotros", "las dudas", "describing what we eliminate"),
            ("tú", "los malos pensamientos", "giving advice about habits"),
        ],
        "amar": [
            ("yo", "a mi familia", "expressing deep feelings"),
            ("él", "a su esposa", "describing his devotion"),
            ("nosotros", "la naturaleza", "expressing shared passion"),
        ],
        "andar": [
            ("yo", "por el parque", "describing current movement"),
            ("ellos", "por la calle", "narrating what they do"),
            ("tú", "muy rápido", "commenting on speed"),
        ],
        "aparecer": [
            ("él", "en la televisión", "describing where he shows up"),
            ("yo", "en la lista", "expressing current status"),
            ("ellas", "en el escenario", "narrating an event"),
        ],
        "apartar": [
            ("yo", "los libros de la mesa", "describing a current action"),
            ("tú", "la mirada", "narrating a present moment"),
            ("ella", "las sillas", "describing what she does"),
        ],
        "apostar": [
            ("yo", "por el equipo local", "expressing a bet"),
            ("ellos", "mucho dinero", "describing their action"),
            ("tú", "por tu favorito", "talking about preferences"),
        ],
        "apoyar": [
            ("yo", "a mi hermano", "expressing support"),
            ("nosotros", "el proyecto", "describing team action"),
            ("tú", "a tus compañeros", "talking about helping others"),
        ],
        "aprender": [
            ("yo", "español", "expressing current learning"),
            ("tú", "algo nuevo", "describing habitual activity"),
            ("ellos", "a cocinar", "narrating what they do"),
        ],
        "arreglar": [
            ("yo", "el coche", "describing a repair"),
            ("él", "la computadora", "narrating his work"),
            ("nosotros", "la casa", "talking about home improvement"),
        ],
        "asegurar": [
            ("yo", "la puerta", "describing a safety action"),
            ("ella", "el éxito del evento", "narrating her effort"),
            ("nosotros", "los resultados", "expressing team responsibility"),
        ],
        "asesinar": [
            ("él", "al personaje en la novela", "narrating a fictional plot"),
            ("ellos", "al villano en la historia", "describing a story"),
            ("ella", "al rival en el videojuego", "talking about gaming"),
        ],
        "asustar": [
            ("tú", "a los niños", "describing a playful action"),
            ("él", "a su hermana", "narrating a prank"),
            ("yo", "a mi gato sin querer", "expressing an accident"),
        ],
        "atacar": [
            ("ellos", "al enemigo", "describing a conflict"),
            ("él", "el problema con determinación", "expressing determination"),
            ("nosotros", "la tarea difícil", "tackling something challenging"),
        ],
        "atrapar": [
            ("yo", "la pelota", "describing a catch"),
            ("ella", "al ladrón", "narrating an action"),
            ("tú", "las mariposas", "describing an activity"),
        ],
        "averiguar": [
            ("yo", "la verdad", "expressing investigation"),
            ("nosotros", "los hechos", "describing research"),
            ("tú", "la dirección", "talking about finding out"),
        ],
        "ayudar": [
            ("yo", "a mi vecino", "expressing willingness to help"),
            ("ella", "a los estudiantes", "describing her role"),
            ("nosotros", "a la comunidad", "talking about community service"),
        ],
        "bailar": [
            ("yo", "salsa", "expressing a hobby"),
            ("tú", "muy bien", "complimenting dance skills"),
            ("ellos", "en la fiesta", "narrating a party scene"),
        ],
        "bajar": [
            ("yo", "las escaleras", "describing movement"),
            ("él", "del autobús", "narrating arrival"),
            ("nosotros", "los precios", "expressing a business action"),
        ],
        "bastar": [
            ("eso", "para todos", "expressing sufficiency"),
            ("ella", "con su presencia", "describing enough"),
            ("ellos", "con poco dinero", "expressing adequacy"),
        ],
        "beber": [
            ("yo", "agua", "describing a healthy habit"),
            ("tú", "café", "talking about morning routine"),
            ("nosotros", "jugo de naranja", "describing breakfast habits"),
        ],
        "besar": [
            ("ella", "a su hijo", "expressing maternal affection"),
            ("yo", "a mi pareja", "describing a loving gesture"),
            ("ellos", "a sus abuelos", "narrating family customs"),
        ],
        "buscar": [
            ("yo", "mis llaves", "describing a search"),
            ("tú", "trabajo", "talking about job hunting"),
            ("nosotros", "una solución", "expressing problem-solving"),
        ],
        "caer": [
            ("yo", "al suelo", "describing an accident"),
            ("ella", "de la silla", "narrating a mishap"),
            ("ellos", "en la trampa", "describing a situation"),
        ],
        "callar": [
            ("yo", "cuando es necesario", "expressing self-control"),
            ("tú", "en clase", "describing behavior"),
            ("ellos", "durante la película", "narrating etiquette"),
        ],
        "calmar": [
            ("yo", "a mi hijo", "expressing a soothing action"),
            ("ella", "los nervios", "describing her method"),
            ("tú", "a tu perro", "giving advice about pets"),
        ],
        "cambiar": [
            ("yo", "de opinión", "expressing a change"),
            ("nosotros", "el plan", "describing team decision"),
            ("él", "de ropa", "narrating a daily action"),
        ],
        "caminar": [
            ("yo", "al trabajo", "describing a commute"),
            ("ellos", "por la playa", "narrating a leisure activity"),
            ("tú", "muy rápido", "commenting on pace"),
        ],
        "cantar": [
            ("ella", "una canción bonita", "describing a performance"),
            ("yo", "en la ducha", "expressing a fun habit"),
            ("nosotros", "en el coro", "talking about group activity"),
        ],
        "casar": [
            ("ella", "a las parejas en la iglesia", "describing a priest's duty"),
            ("yo", "los colores perfectamente", "expressing color matching"),
            ("ellos", "a su hija", "narrating a family event"),
        ],
        "cerrar": [
            ("yo", "la ventana", "describing an action"),
            ("tú", "la tienda", "talking about work duties"),
            ("ella", "los ojos", "narrating a peaceful moment"),
        ],
        "coger": [
            ("yo", "el autobús", "describing transportation"),
            ("tú", "un taxi", "suggesting a mode of travel"),
            ("nosotros", "las maletas", "describing trip preparation"),
        ],
        "comenzar": [
            ("nosotros", "el proyecto", "expressing a new start"),
            ("yo", "a estudiar", "describing the start of an activity"),
            ("él", "su nuevo trabajo", "narrating a career change"),
        ],
        "comer": [
            ("yo", "una ensalada", "describing a healthy choice"),
            ("tú", "demasiado rápido", "commenting on eating habits"),
            ("nosotros", "juntos en familia", "expressing family tradition"),
        ],
        "cometer": [
            ("yo", "un error", "expressing a mistake"),
            ("tú", "errores a veces", "talking about being human"),
            ("ellos", "faltas graves", "describing serious issues"),
        ],
        "compartir": [
            ("nosotros", "la comida", "expressing generosity"),
            ("yo", "mis ideas", "describing openness"),
            ("ella", "su experiencia", "narrating her contribution"),
        ],
        "comprar": [
            ("yo", "un regalo", "describing a purchase"),
            ("nosotros", "comida para la cena", "talking about meal planning"),
            ("tú", "ropa nueva", "describing shopping"),
        ],
        "comprender": [
            ("yo", "la situación", "expressing understanding"),
            ("tú", "el problema", "acknowledging awareness"),
            ("nosotros", "la lección", "describing learning"),
        ],
        "conducir": [
            ("yo", "el coche al trabajo", "describing a commute"),
            ("él", "con cuidado", "narrating safe driving"),
            ("tú", "muy bien", "complimenting driving skills"),
        ],
        "confiar": [
            ("yo", "en mi equipo", "expressing trust"),
            ("ella", "en sus amigos", "describing her relationships"),
            ("nosotros", "en el proceso", "expressing faith in method"),
        ],
        "conocer": [
            ("yo", "a mucha gente", "expressing social connections"),
            ("tú", "la ciudad muy bien", "describing familiarity"),
            ("ellos", "el camino", "narrating their knowledge"),
        ],
        "conseguir": [
            ("yo", "buenos resultados", "expressing achievement"),
            ("nosotros", "los boletos", "describing a successful purchase"),
            ("tú", "lo que quieres", "talking about determination"),
        ],
        "considerar": [
            ("yo", "todas las opciones", "expressing careful thought"),
            ("nosotros", "la propuesta", "describing evaluation"),
            ("ella", "las consecuencias", "narrating thoughtfulness"),
        ],
        "construir": [
            ("ellos", "una casa nueva", "describing a construction project"),
            ("yo", "un mueble", "expressing hands-on work"),
            ("nosotros", "un futuro mejor", "expressing hope and effort"),
        ],
        "contar": [
            ("yo", "una historia", "expressing storytelling"),
            ("ella", "los secretos a su amiga", "narrating a confidence"),
            ("tú", "el dinero", "describing a practical action"),
        ],
        "contestar": [
            ("yo", "el teléfono", "describing a response"),
            ("tú", "las preguntas", "talking about participation"),
            ("él", "los correos electrónicos", "narrating work habits"),
        ],
        "continuar": [
            ("nosotros", "con el plan", "expressing persistence"),
            ("yo", "mi camino", "describing forward movement"),
            ("ella", "sus estudios", "narrating her dedication"),
        ],
        "controlar": [
            ("yo", "mis emociones", "expressing self-discipline"),
            ("él", "la situación", "describing leadership"),
            ("nosotros", "los gastos", "talking about budgeting"),
        ],
        "convertir": [
            ("yo", "el agua en hielo", "describing a transformation"),
            ("ella", "sus sueños en realidad", "expressing ambition"),
            ("nosotros", "la idea en un proyecto", "describing innovation"),
        ],
        "correr": [
            ("yo", "en el parque", "describing exercise"),
            ("tú", "muy rápido", "commenting on speed"),
            ("ellos", "una maratón", "narrating an athletic event"),
        ],
        "cortar": [
            ("yo", "el pan", "describing food preparation"),
            ("ella", "las flores", "narrating a garden activity"),
            ("tú", "el papel", "describing a craft"),
        ],
        "costar": [
            ("eso", "mucho dinero", "expressing price"),
            ("los zapatos", "cien dólares", "describing a cost"),
            ("el viaje", "una fortuna", "talking about expenses"),
        ],
        "crear": [
            ("yo", "una obra de arte", "expressing creativity"),
            ("nosotros", "un plan", "describing planning"),
            ("ella", "música hermosa", "narrating artistic talent"),
        ],
        "crecer": [
            ("yo", "como persona", "expressing personal growth"),
            ("los niños", "muy rápido", "describing child development"),
            ("ella", "en su carrera", "narrating professional progress"),
        ],
        "creer": [
            ("yo", "en ti", "expressing faith"),
            ("nosotros", "en la justicia", "describing shared values"),
            ("tú", "en los milagros", "talking about beliefs"),
        ],
        "cubrir": [
            ("yo", "la mesa con un mantel", "describing a setup"),
            ("ella", "al bebé con una manta", "narrating care"),
            ("nosotros", "los gastos del viaje", "talking about finances"),
        ],
        "cuidar": [
            ("yo", "a mi abuela", "expressing care for family"),
            ("tú", "tu salud", "giving health advice"),
            ("nosotros", "el medio ambiente", "expressing environmental concern"),
        ],
        "cumplir": [
            ("yo", "mis promesas", "expressing reliability"),
            ("ella", "con sus obligaciones", "narrating responsibility"),
            ("nosotros", "los requisitos", "describing compliance"),
        ],
        "dar": [
            ("yo", "un consejo", "expressing advice-giving"),
            ("ella", "un regalo a su madre", "describing a generous act"),
            ("nosotros", "las gracias", "expressing gratitude"),
        ],
        "deber": [
            ("yo", "dinero al banco", "expressing a financial obligation"),
            ("tú", "mucho a tus padres", "describing gratitude owed"),
            ("nosotros", "terminar el proyecto", "expressing obligation"),
        ],
        "decidir": [
            ("yo", "mi futuro", "expressing a life choice"),
            ("nosotros", "juntos", "describing collective decision"),
            ("tú", "rápidamente", "commenting on decision speed"),
        ],
        "decir": [
            ("yo", "la verdad", "expressing honesty"),
            ("tú", "cosas interesantes", "describing someone's speech"),
            ("ellos", "muchas mentiras", "narrating dishonesty"),
        ],
        "defender": [
            ("yo", "mis derechos", "expressing self-advocacy"),
            ("ella", "a su familia", "narrating protection"),
            ("nosotros", "nuestra posición", "expressing team stance"),
        ],
        "dejar": [
            ("yo", "el café sobre la mesa", "describing a simple action"),
            ("tú", "todo en orden", "talking about tidiness"),
            ("ella", "de fumar", "narrating quitting a habit"),
        ],
        "demostrar": [
            ("yo", "mi capacidad", "expressing proof of ability"),
            ("él", "su talento", "narrating talent display"),
            ("nosotros", "los resultados", "presenting findings"),
        ],
        "depender": [
            ("eso", "de ti", "expressing reliance"),
            ("yo", "de mi trabajo", "describing financial dependence"),
            ("nosotros", "del clima", "expressing conditional planning"),
        ],
        "desaparecer": [
            ("él", "sin dejar rastro", "narrating a mystery"),
            ("yo", "de las redes sociales", "describing digital absence"),
            ("ellos", "entre la multitud", "narrating a crowded scene"),
        ],
        "desarrollar": [
            ("nosotros", "una aplicación nueva", "describing tech work"),
            ("yo", "mis habilidades", "expressing self-improvement"),
            ("ella", "un plan estratégico", "narrating professional work"),
        ],
        "descubrir": [
            ("yo", "algo nuevo", "expressing discovery"),
            ("tú", "la verdad", "describing revelation"),
            ("ellos", "un tesoro escondido", "narrating an adventure"),
        ],
        "desear": [
            ("yo", "paz en el mundo", "expressing a wish"),
            ("ella", "viajar por Europa", "describing her dreams"),
            ("nosotros", "un buen resultado", "expressing hope"),
        ],
        "despedir": [
            ("yo", "a mi amigo en el aeropuerto", "describing a farewell"),
            ("ella", "a los invitados", "narrating a goodbye"),
            ("nosotros", "el año viejo", "talking about New Year traditions"),
        ],
        "despertar": [
            ("yo", "a las seis de la mañana", "describing a morning routine"),
            ("tú", "muy temprano", "commenting on wake-up time"),
            ("ella", "al bebé sin querer", "narrating an accident"),
        ],
        "destruir": [
            ("ellos", "el edificio viejo", "describing demolition"),
            ("yo", "las pruebas", "narrating evidence destruction"),
            ("ella", "todo a su paso", "expressing figurative damage"),
        ],
        "detener": [
            ("yo", "el coche en el semáforo", "describing driving"),
            ("ella", "la pelea", "narrating intervention"),
            ("ellos", "al sospechoso", "describing law enforcement"),
        ],
        "devolver": [
            ("yo", "el libro a la biblioteca", "describing a return"),
            ("tú", "el dinero", "talking about repayment"),
            ("nosotros", "los productos defectuosos", "describing consumer rights"),
        ],
        "dirigir": [
            ("yo", "la empresa", "expressing leadership"),
            ("ella", "el equipo de ventas", "narrating management"),
            ("él", "la orquesta", "describing a conductor's role"),
        ],
        "disculpar": [
            ("yo", "a mi amigo", "expressing forgiveness"),
            ("ella", "el retraso", "apologizing for lateness"),
            ("nosotros", "los errores del pasado", "expressing understanding"),
        ],
        "discutir": [
            ("nosotros", "el tema en la reunión", "describing a meeting"),
            ("yo", "con mi hermano", "expressing family dynamics"),
            ("ellos", "sobre política", "narrating a debate"),
        ],
        "disfrutar": [
            ("yo", "la música", "expressing enjoyment"),
            ("tú", "cada momento", "giving advice about life"),
            ("nosotros", "las vacaciones", "describing a holiday"),
        ],
        "disparar": [
            ("él", "al blanco", "describing target practice"),
            ("yo", "la cámara fotográfica", "expressing photography"),
            ("ellos", "los fuegos artificiales", "narrating a celebration"),
        ],
        "dormir": [
            ("yo", "ocho horas", "describing a sleep schedule"),
            ("tú", "muy poco", "commenting on sleep habits"),
            ("ella", "profundamente", "narrating peaceful sleep"),
        ],
        "echar": [
            ("yo", "agua en el vaso", "describing pouring"),
            ("tú", "sal en la comida", "talking about cooking"),
            ("ella", "de menos a su familia", "expressing homesickness"),
        ],
        "elegir": [
            ("yo", "la mejor opción", "expressing decision-making"),
            ("nosotros", "un restaurante", "describing group choice"),
            ("tú", "tu camino", "talking about life choices"),
        ],
        "empezar": [
            ("yo", "a trabajar", "describing start of workday"),
            ("nosotros", "el proyecto", "expressing team initiative"),
            ("tú", "a entender", "describing growing comprehension"),
        ],
        "encantar": [
            ("yo", "a los niños con mis historias", "describing charm"),
            ("ella", "a todos con su talento", "narrating someone's appeal"),
            ("nosotros", "al público con el show", "describing audience reaction"),
        ],
        "encontrar": [
            ("yo", "mis llaves perdidas", "describing a discovery"),
            ("ella", "trabajo nuevo", "narrating job search success"),
            ("nosotros", "la solución al problema", "expressing problem-solving"),
        ],
        "enfrentar": [
            ("yo", "mis miedos", "expressing courage"),
            ("nosotros", "los desafíos", "describing team resilience"),
            ("tú", "la situación con calma", "giving advice about challenges"),
        ],
        "engañar": [
            ("él", "a sus clientes", "describing deception"),
            ("yo", "a nadie", "expressing honesty"),
            ("ellos", "al público", "narrating fraud"),
        ],
        "enseñar": [
            ("yo", "matemáticas", "describing a teaching role"),
            ("ella", "a sus hijos a leer", "narrating parental guidance"),
            ("nosotros", "con el ejemplo", "expressing leadership style"),
        ],
        "entender": [
            ("yo", "el problema", "expressing comprehension"),
            ("tú", "la lección", "describing learning progress"),
            ("nosotros", "la situación", "expressing shared understanding"),
        ],
        "enterar": [
            ("yo", "a todos de las noticias", "spreading news"),
            ("ella", "a su jefe de los cambios", "reporting updates"),
            ("nosotros", "a los vecinos del evento", "informing the community"),
        ],
        "entrar": [
            ("yo", "en la oficina", "describing arrival"),
            ("tú", "por la puerta principal", "giving directions"),
            ("ellos", "al edificio", "narrating entry"),
        ],
        "entregar": [
            ("yo", "el informe", "describing a delivery"),
            ("nosotros", "los paquetes", "expressing distribution"),
            ("ella", "las notas a los estudiantes", "narrating academic duties"),
        ],
        "enviar": [
            ("yo", "un mensaje", "describing communication"),
            ("tú", "un correo electrónico", "talking about email"),
            ("ella", "flores a su madre", "narrating a thoughtful gesture"),
        ],
        "escapar": [
            ("yo", "de la rutina", "expressing freedom"),
            ("ellos", "de la prisión", "narrating an escape"),
            ("él", "del peligro", "describing a narrow escape"),
        ],
        "esconder": [
            ("yo", "el regalo", "describing a surprise preparation"),
            ("tú", "tus emociones", "talking about emotional control"),
            ("ella", "las galletas de los niños", "narrating a playful act"),
        ],
        "escribir": [
            ("yo", "una carta", "describing a writing activity"),
            ("tú", "un libro", "talking about authorship"),
            ("nosotros", "un informe", "describing teamwork"),
        ],
        "escuchar": [
            ("yo", "música clásica", "describing a leisure activity"),
            ("tú", "con atención", "giving advice about listening"),
            ("nosotros", "las noticias", "describing a daily habit"),
        ],
        "esperar": [
            ("yo", "el autobús", "describing waiting"),
            ("nosotros", "buenas noticias", "expressing hope"),
            ("tú", "con paciencia", "giving advice about patience"),
        ],
        "estar": [
            ("yo", "en casa", "expressing location"),
            ("tú", "muy contento", "describing emotions"),
            ("nosotros", "listos para salir", "expressing readiness"),
        ],
        "estudiar": [
            ("yo", "para el examen", "describing preparation"),
            ("ella", "medicina", "narrating career path"),
            ("nosotros", "juntos en la biblioteca", "describing study habits"),
        ],
        "evitar": [
            ("yo", "los problemas", "expressing caution"),
            ("tú", "la comida chatarra", "giving health advice"),
            ("nosotros", "los conflictos", "describing team harmony"),
        ],
        "existir": [
            ("eso", "en la realidad", "expressing existence"),
            ("ellos", "en otro continente", "describing location of beings"),
            ("yo", "para ayudar", "expressing purpose"),
        ],
        "explicar": [
            ("yo", "la lección", "describing a teaching moment"),
            ("ella", "el proceso", "narrating instruction"),
            ("tú", "las reglas del juego", "describing game rules"),
        ],
        "formar": [
            ("nosotros", "un equipo nuevo", "describing team building"),
            ("yo", "parte del grupo", "expressing belonging"),
            ("ella", "a los nuevos empleados", "narrating training"),
        ],
        "funcionar": [
            ("el coche", "perfectamente", "describing machine status"),
            ("yo", "bien bajo presión", "expressing work style"),
            ("ellos", "como equipo", "describing teamwork"),
        ],
        "ganar": [
            ("yo", "el partido", "expressing victory"),
            ("nosotros", "experiencia", "describing learning"),
            ("tú", "un buen salario", "talking about compensation"),
        ],
        "golpear": [
            ("yo", "la mesa con frustración", "expressing frustration"),
            ("él", "la pelota con fuerza", "describing sports"),
            ("tú", "la puerta para entrar", "describing knocking"),
        ],
        "gritar": [
            ("yo", "de alegría", "expressing joy"),
            ("ellos", "en el estadio", "narrating a sports event"),
            ("tú", "demasiado fuerte", "commenting on volume"),
        ],
        "guardar": [
            ("yo", "los documentos importantes", "describing organization"),
            ("tú", "el secreto", "talking about trust"),
            ("nosotros", "comida para mañana", "describing meal planning"),
        ],
        "gustar": [
            ("yo", "a mis vecinos", "expressing being liked"),
            ("ella", "a todo el mundo", "describing someone's popularity"),
            ("nosotros", "a nuestros profesores", "expressing teacher approval"),
        ],
        "haber": [
            ("yo", "terminado el trabajo", "expressing completed actions"),
            ("tú", "estudiado mucho", "describing effort"),
            ("nosotros", "llegado temprano", "narrating timely arrival"),
        ],
        "hablar": [
            ("yo", "con mi amigo", "describing conversation"),
            ("ella", "tres idiomas", "narrating language skills"),
            ("nosotros", "sobre el futuro", "discussing plans"),
        ],
        "hacer": [
            ("yo", "la cena", "describing cooking"),
            ("tú", "ejercicio", "talking about fitness"),
            ("nosotros", "planes para el fin de semana", "planning activities"),
        ],
        "hallar": [
            ("yo", "la respuesta", "expressing discovery"),
            ("ella", "una solución creativa", "narrating problem-solving"),
            ("nosotros", "el camino correcto", "describing navigation"),
        ],
        "huir": [
            ("yo", "del peligro", "expressing escape"),
            ("ellos", "de la tormenta", "narrating weather escape"),
            ("él", "de la realidad", "describing avoidance"),
        ],
        "imaginar": [
            ("yo", "un mundo mejor", "expressing idealism"),
            ("tú", "las posibilidades", "encouraging creativity"),
            ("nosotros", "el futuro", "describing vision"),
        ],
        "importar": [
            ("yo", "productos del extranjero", "describing imports"),
            ("ella", "materiales de China", "narrating business"),
            ("nosotros", "tecnología nueva", "describing acquisition"),
        ],
        "incluir": [
            ("yo", "a todos en el plan", "expressing inclusiveness"),
            ("nosotros", "los detalles en el informe", "describing thoroughness"),
            ("ella", "una nota personal", "narrating a thoughtful addition"),
        ],
        "informar": [
            ("yo", "a mi jefe", "describing reporting"),
            ("ella", "a los medios", "narrating a press release"),
            ("nosotros", "al público", "expressing transparency"),
        ],
        "intentar": [
            ("yo", "algo nuevo", "expressing willingness to try"),
            ("tú", "resolver el problema", "describing effort"),
            ("nosotros", "mejorar cada día", "expressing aspiration"),
        ],
        "interesar": [
            ("yo", "a los estudiantes con mi clase", "expressing engagement"),
            ("ella", "a los inversores", "narrating a pitch"),
            ("nosotros", "a la audiencia", "describing audience capture"),
        ],
        "invitar": [
            ("yo", "a mis amigos a cenar", "describing hospitality"),
            ("tú", "a tu familia a la fiesta", "talking about social planning"),
            ("ella", "a sus colegas al evento", "narrating professional socializing"),
        ],
        "ir": [
            ("yo", "al supermercado", "describing an errand"),
            ("nosotros", "de vacaciones", "talking about travel"),
            ("tú", "a la escuela", "describing a daily routine"),
        ],
        "joder": [
            ("eso", "todo el plan", "expressing frustration about ruined plans"),
            ("yo", "la situación sin querer", "describing accidental mess-up"),
            ("ellos", "el proyecto", "narrating project disruption"),
        ],
        "jugar": [
            ("yo", "al fútbol", "describing a sport"),
            ("ellos", "en el parque", "narrating children playing"),
            ("tú", "videojuegos", "talking about gaming"),
        ],
        "jurar": [
            ("yo", "decir la verdad", "expressing a solemn promise"),
            ("él", "lealtad a su país", "describing patriotism"),
            ("nosotros", "proteger a nuestra familia", "expressing dedication"),
        ],
        "leer": [
            ("yo", "un libro interesante", "describing a reading habit"),
            ("tú", "el periódico", "talking about staying informed"),
            ("ella", "cuentos a los niños", "narrating bedtime stories"),
        ],
        "levantar": [
            ("yo", "la mano en clase", "describing classroom behavior"),
            ("tú", "pesas en el gimnasio", "talking about exercise"),
            ("nosotros", "la mesa después de comer", "describing cleanup"),
        ],
        "llamar": [
            ("yo", "a mi madre", "describing a phone call"),
            ("tú", "al doctor", "suggesting making an appointment"),
            ("ella", "a sus amigos", "narrating social contact"),
        ],
        "llegar": [
            ("yo", "a la oficina temprano", "describing punctuality"),
            ("nosotros", "al acuerdo", "expressing negotiation success"),
            ("tú", "tarde a clase", "commenting on tardiness"),
        ],
        "llevar": [
            ("yo", "una chaqueta", "describing clothing choice"),
            ("ella", "a los niños al colegio", "narrating parental duty"),
            ("tú", "el equipaje", "describing travel tasks"),
        ],
        "llorar": [
            ("ella", "de felicidad", "expressing happy tears"),
            ("yo", "cuando veo películas tristes", "describing emotional sensitivity"),
            ("ellos", "por la pérdida", "narrating grief"),
        ],
        "lograr": [
            ("yo", "mis objetivos", "expressing achievement"),
            ("nosotros", "un gran éxito", "describing team success"),
            ("tú", "todo lo que deseas", "encouraging someone"),
        ],
        "luchar": [
            ("yo", "por mis derechos", "expressing advocacy"),
            ("ella", "contra la injusticia", "narrating activism"),
            ("nosotros", "por un mundo mejor", "expressing shared ideals"),
        ],
        "mandar": [
            ("yo", "un paquete", "describing sending"),
            ("tú", "un mensaje de texto", "talking about texting"),
            ("ella", "flores a su amiga", "narrating a kind gesture"),
        ],
        "manejar": [
            ("yo", "la situación con calma", "expressing composure"),
            ("él", "el coche nuevo", "describing driving"),
            ("nosotros", "el presupuesto", "talking about management"),
        ],
        "mantener": [
            ("yo", "la calma", "expressing composure"),
            ("nosotros", "el orden", "describing organization"),
            ("tú", "tu promesa", "talking about reliability"),
        ],
        "marchar": [
            ("ellos", "por la calle principal", "describing a march"),
            ("yo", "hacia mi destino", "expressing determination"),
            ("nosotros", "juntos en la protesta", "narrating activism"),
        ],
        "matar": [
            ("él", "el tiempo leyendo", "describing leisure"),
            ("yo", "las horas en el trabajo", "expressing boredom"),
            ("ella", "mosquitos en verano", "describing a common annoyance"),
        ],
        "mencionar": [
            ("yo", "el tema en la reunión", "describing communication"),
            ("tú", "un dato importante", "talking about sharing info"),
            ("ella", "a su amigo en la conversación", "narrating a discussion"),
        ],
        "mentir": [
            ("él", "a sus padres", "describing dishonesty"),
            ("yo", "nunca a mis amigos", "expressing honesty"),
            ("ellos", "sobre su edad", "narrating a common deception"),
        ],
        "merecer": [
            ("tú", "un descanso", "expressing deserving rest"),
            ("ella", "el premio", "narrating recognition"),
            ("nosotros", "una oportunidad", "expressing worthiness"),
        ],
        "meter": [
            ("yo", "la ropa en la maleta", "describing packing"),
            ("tú", "las manos en los bolsillos", "narrating a gesture"),
            ("ella", "los libros en la mochila", "describing preparation"),
        ],
        "mirar": [
            ("yo", "por la ventana", "describing observation"),
            ("tú", "las estrellas", "talking about stargazing"),
            ("nosotros", "la televisión", "describing a leisure activity"),
        ],
        "molestar": [
            ("yo", "a mi hermano", "describing sibling dynamics"),
            ("tú", "a los vecinos con la música", "talking about noise"),
            ("ellos", "a los demás pasajeros", "narrating public annoyance"),
        ],
        "morir": [
            ("las plantas", "sin agua", "describing neglect consequences"),
            ("yo", "de hambre", "expressing extreme hunger figuratively"),
            ("él", "de risa con esa broma", "describing laughter"),
        ],
        "mostrar": [
            ("yo", "mis fotos del viaje", "describing sharing memories"),
            ("ella", "su nuevo diseño", "narrating a presentation"),
            ("nosotros", "los resultados del estudio", "presenting findings"),
        ],
        "mover": [
            ("yo", "los muebles", "describing rearrangement"),
            ("nosotros", "el coche del estacionamiento", "describing parking"),
            ("tú", "las piezas del ajedrez", "describing a game"),
        ],
        "nacer": [
            ("yo", "en una ciudad pequeña", "expressing origin"),
            ("los bebés", "en el hospital", "describing childbirth"),
            ("ella", "en primavera", "narrating a birth season"),
        ],
        "necesitar": [
            ("yo", "más tiempo", "expressing a need"),
            ("nosotros", "ayuda", "requesting assistance"),
            ("tú", "descansar", "giving advice"),
        ],
        "negar": [
            ("él", "las acusaciones", "describing denial"),
            ("yo", "la entrada a los menores", "expressing a rule"),
            ("ellos", "su participación", "narrating evasion"),
        ],
        "observar": [
            ("yo", "las aves en el parque", "describing birdwatching"),
            ("ella", "los detalles del cuadro", "narrating art appreciation"),
            ("nosotros", "el comportamiento de los animales", "describing study"),
        ],
        "obtener": [
            ("yo", "buenas calificaciones", "expressing academic success"),
            ("nosotros", "los permisos necesarios", "describing bureaucracy"),
            ("tú", "información valiosa", "talking about research"),
        ],
        "ocupar": [
            ("yo", "el primer lugar", "expressing ranking"),
            ("nosotros", "toda la oficina", "describing space usage"),
            ("ella", "un puesto importante", "narrating career position"),
        ],
        "ocurrir": [
            ("eso", "con frecuencia", "expressing frequency"),
            ("los accidentes", "en esa esquina", "describing a danger zone"),
            ("algo extraño", "en esta casa", "narrating a mystery"),
        ],
        "odiar": [
            ("yo", "la injusticia", "expressing strong dislike"),
            ("ella", "las mentiras", "describing her values"),
            ("nosotros", "la violencia", "expressing shared values"),
        ],
        "ofrecer": [
            ("yo", "mi ayuda", "expressing willingness"),
            ("ella", "una disculpa", "narrating an apology"),
            ("nosotros", "nuestros servicios", "describing business"),
        ],
        "oír": [
            ("yo", "un ruido extraño", "describing perception"),
            ("tú", "la música desde aquí", "expressing auditory experience"),
            ("nosotros", "las campanas de la iglesia", "narrating a sound"),
        ],
        "olvidar": [
            ("yo", "las llaves en casa", "describing forgetfulness"),
            ("tú", "la cita con el dentista", "talking about missed appointments"),
            ("ella", "su contraseña", "narrating a common problem"),
        ],
        "pagar": [
            ("yo", "la cuenta", "describing a payment"),
            ("nosotros", "el alquiler", "talking about housing costs"),
            ("tú", "con tarjeta de crédito", "describing payment method"),
        ],
        "parar": [
            ("yo", "el coche en la esquina", "describing stopping"),
            ("él", "de hablar un momento", "expressing a pause"),
            ("nosotros", "el trabajo a las cinco", "describing work schedule"),
        ],
        "parecer": [
            ("eso", "una buena idea", "expressing opinion"),
            ("él", "muy cansado", "describing appearance"),
            ("yo", "más joven de lo que soy", "expressing youthful appearance"),
        ],
        "partir": [
            ("yo", "el pastel en ocho pedazos", "describing cutting"),
            ("nosotros", "hacia la montaña", "expressing departure"),
            ("ella", "la fruta para todos", "describing sharing food"),
        ],
        "pasar": [
            ("yo", "por tu casa", "describing a visit"),
            ("tú", "mucho tiempo en el teléfono", "commenting on phone usage"),
            ("nosotros", "las vacaciones en la playa", "describing holiday plans"),
        ],
        "pedir": [
            ("yo", "un café", "describing an order"),
            ("tú", "ayuda cuando la necesitas", "giving advice about asking"),
            ("nosotros", "una pizza para cenar", "describing a dinner order"),
        ],
        "pegar": [
            ("yo", "el cartel en la pared", "describing attachment"),
            ("ella", "los sellos en el sobre", "narrating mail preparation"),
            ("tú", "las piezas con pegamento", "describing crafting"),
        ],
        "pelear": [
            ("ellos", "por el primer lugar", "describing competition"),
            ("yo", "por mis derechos", "expressing advocacy"),
            ("nosotros", "contra la corrupción", "narrating a cause"),
        ],
        "pensar": [
            ("yo", "en mi familia", "expressing thoughts"),
            ("tú", "demasiado", "commenting on overthinking"),
            ("nosotros", "en el futuro", "describing planning"),
        ],
        "perder": [
            ("yo", "las llaves con frecuencia", "expressing a recurring problem"),
            ("tú", "la paciencia", "describing frustration"),
            ("nosotros", "el tiempo con discusiones", "expressing wasted time"),
        ],
        "perdonar": [
            ("yo", "a mi amigo", "expressing forgiveness"),
            ("ella", "los errores de los demás", "narrating compassion"),
            ("nosotros", "con facilidad", "describing a character trait"),
        ],
        "permanecer": [
            ("yo", "en silencio", "expressing restraint"),
            ("ella", "en su puesto", "narrating dedication"),
            ("nosotros", "unidos", "expressing solidarity"),
        ],
        "permitir": [
            ("yo", "la entrada a todos", "expressing openness"),
            ("ella", "las visitas los domingos", "describing a policy"),
            ("nosotros", "los cambios necesarios", "expressing flexibility"),
        ],
        "pertenecer": [
            ("yo", "a este grupo", "expressing membership"),
            ("eso", "a mi abuelo", "describing ownership"),
            ("nosotros", "a la misma organización", "expressing shared affiliation"),
        ],
        "pesar": [
            ("yo", "los ingredientes antes de cocinar", "describing measurement"),
            ("ella", "las frutas en la balanza", "narrating market shopping"),
            ("tú", "el equipaje antes de viajar", "describing travel preparation"),
        ],
        "poder": [
            ("yo", "resolver el problema", "expressing ability"),
            ("tú", "hablar español", "describing language skills"),
            ("nosotros", "terminar a tiempo", "expressing team capability"),
        ],
        "poner": [
            ("yo", "la mesa para la cena", "describing dinner preparation"),
            ("tú", "atención en clase", "giving advice about focus"),
            ("ella", "música para relajarse", "narrating a relaxation method"),
        ],
        "preferir": [
            ("yo", "el café al té", "expressing preference"),
            ("nosotros", "caminar en vez de conducir", "describing lifestyle choice"),
            ("tú", "la comida casera", "talking about food preferences"),
        ],
        "preguntar": [
            ("yo", "la dirección", "describing asking for directions"),
            ("tú", "por tu madre", "expressing concern for family"),
            ("ella", "sobre el horario", "narrating an inquiry"),
        ],
        "preocupar": [
            ("yo", "a mis padres con mi comportamiento", "expressing concern caused"),
            ("eso", "a todos en la oficina", "describing workplace worry"),
            ("ella", "a su familia", "narrating family concern"),
        ],
        "preparar": [
            ("yo", "el desayuno", "describing morning routine"),
            ("nosotros", "la presentación", "expressing teamwork"),
            ("tú", "la maleta para el viaje", "describing travel preparation"),
        ],
        "presentar": [
            ("yo", "el informe al jefe", "describing a work delivery"),
            ("ella", "a su novio a la familia", "narrating introductions"),
            ("nosotros", "nuestra propuesta", "expressing business pitch"),
        ],
        "prestar": [
            ("yo", "dinero a mi amigo", "describing lending"),
            ("tú", "atención a los detalles", "expressing attentiveness"),
            ("ella", "sus libros a los compañeros", "narrating generosity"),
        ],
        "probar": [
            ("yo", "la comida antes de servirla", "describing tasting"),
            ("tú", "algo nuevo", "encouraging experimentation"),
            ("nosotros", "diferentes métodos", "describing problem-solving"),
        ],
        "producir": [
            ("yo", "contenido para las redes sociales", "describing content creation"),
            ("nosotros", "resultados excelentes", "expressing team output"),
            ("ella", "películas independientes", "narrating film production"),
        ],
        "prometer": [
            ("yo", "llegar a tiempo", "expressing a commitment"),
            ("tú", "no decir nada", "describing a promise"),
            ("nosotros", "hacer nuestro mejor esfuerzo", "expressing team dedication"),
        ],
        "proteger": [
            ("yo", "a mi familia", "expressing protection"),
            ("nosotros", "el medio ambiente", "describing conservation"),
            ("ella", "a los animales", "narrating animal welfare"),
        ],
        "quedar": [
            ("yo", "con mis amigos los viernes", "describing social plans"),
            ("nosotros", "en el restaurante a las ocho", "making plans"),
            ("tú", "en casa cuando llueve", "describing weather-based decisions"),
        ],
        "querer": [
            ("yo", "aprender a bailar", "expressing desire"),
            ("tú", "viajar por el mundo", "describing dreams"),
            ("nosotros", "lo mejor para todos", "expressing good intentions"),
        ],
        "quitar": [
            ("yo", "la mancha de la camisa", "describing cleaning"),
            ("tú", "los zapatos al entrar", "talking about customs"),
            ("ella", "las malas hierbas del jardín", "describing gardening"),
        ],
        "realizar": [
            ("yo", "un proyecto importante", "describing accomplishment"),
            ("nosotros", "cambios significativos", "expressing transformation"),
            ("ella", "su sueño de ser doctora", "narrating ambition fulfillment"),
        ],
        "recibir": [
            ("yo", "un paquete", "describing delivery"),
            ("tú", "buenas noticias", "expressing positive updates"),
            ("nosotros", "a los invitados en la puerta", "describing hospitality"),
        ],
        "recoger": [
            ("yo", "a los niños de la escuela", "describing parental duty"),
            ("tú", "la basura del suelo", "talking about cleanliness"),
            ("nosotros", "los resultados del análisis", "describing data collection"),
        ],
        "reconocer": [
            ("yo", "mi error", "expressing humility"),
            ("ella", "su voz al teléfono", "narrating recognition"),
            ("nosotros", "el esfuerzo de todos", "expressing appreciation"),
        ],
        "recordar": [
            ("yo", "los buenos tiempos", "expressing nostalgia"),
            ("tú", "la contraseña", "talking about memory"),
            ("ella", "su infancia con cariño", "narrating fond memories"),
        ],
        "recuperar": [
            ("yo", "mi salud", "expressing recovery"),
            ("nosotros", "el tiempo perdido", "describing making up for lost time"),
            ("ella", "su confianza poco a poco", "narrating emotional healing"),
        ],
        "referir": [
            ("yo", "al paciente al especialista", "describing a medical referral"),
            ("ella", "la historia con detalle", "narrating detailed storytelling"),
            ("nosotros", "el caso al departamento legal", "describing bureaucratic process"),
        ],
        "regresar": [
            ("yo", "a casa después del trabajo", "describing commute"),
            ("nosotros", "de las vacaciones", "narrating return from holiday"),
            ("tú", "a tu ciudad natal", "talking about homecoming"),
        ],
        "reír": [
            ("yo", "con mis amigos", "expressing social joy"),
            ("ella", "a carcajadas", "narrating loud laughter"),
            ("nosotros", "de los chistes", "describing shared humor"),
        ],
        "repetir": [
            ("yo", "la pregunta", "expressing repetition"),
            ("tú", "los mismos errores", "commenting on patterns"),
            ("ella", "la lección varias veces", "narrating thorough teaching"),
        ],
        "representar": [
            ("yo", "a mi país", "expressing national pride"),
            ("ella", "a los trabajadores", "narrating union role"),
            ("nosotros", "una obra de teatro", "describing a performance"),
        ],
        "resolver": [
            ("yo", "los problemas con calma", "expressing problem-solving"),
            ("nosotros", "el conflicto", "describing mediation"),
            ("tú", "la ecuación rápidamente", "narrating math skills"),
        ],
        "responder": [
            ("yo", "a todas las preguntas", "expressing thoroughness"),
            ("tú", "con sinceridad", "describing honest communication"),
            ("ella", "al correo electrónico", "narrating prompt response"),
        ],
        "resultar": [
            ("eso", "muy difícil", "expressing difficulty"),
            ("el plan", "exitoso", "describing success"),
            ("la reunión", "muy productiva", "narrating meeting outcome"),
        ],
        "reunir": [
            ("yo", "a toda la familia", "describing family gathering"),
            ("nosotros", "los fondos necesarios", "expressing fundraising"),
            ("ella", "la información para el proyecto", "narrating research"),
        ],
        "revisar": [
            ("yo", "el documento antes de enviarlo", "describing quality control"),
            ("tú", "las cuentas del mes", "talking about finances"),
            ("nosotros", "el equipo regularmente", "describing maintenance"),
        ],
        "robar": [
            ("él", "la atención de todos", "describing charisma figuratively"),
            ("ellos", "ideas de otras empresas", "narrating intellectual theft"),
            ("ella", "corazones con su sonrisa", "expressing charm figuratively"),
        ],
        "romper": [
            ("yo", "el silencio", "expressing breaking quiet"),
            ("tú", "las reglas", "describing rule-breaking"),
            ("ella", "el récord mundial", "narrating an achievement"),
        ],
        "saber": [
            ("yo", "la respuesta", "expressing knowledge"),
            ("tú", "cocinar muy bien", "describing a skill"),
            ("nosotros", "la verdad", "expressing shared knowledge"),
        ],
        "sacar": [
            ("yo", "buenas notas", "expressing academic success"),
            ("tú", "al perro a pasear", "describing a daily chore"),
            ("ella", "dinero del cajero", "narrating a bank transaction"),
        ],
        "salir": [
            ("yo", "de casa temprano", "describing a morning routine"),
            ("nosotros", "a cenar los viernes", "expressing a social habit"),
            ("tú", "con tus amigos", "talking about socializing"),
        ],
        "salvar": [
            ("él", "vidas como médico", "describing a doctor's role"),
            ("yo", "a los animales en peligro", "expressing animal rescue"),
            ("nosotros", "el bosque de la destrucción", "narrating conservation"),
        ],
        "seguir": [
            ("yo", "mis sueños", "expressing perseverance"),
            ("tú", "las instrucciones", "describing compliance"),
            ("nosotros", "adelante con el plan", "expressing continuation"),
        ],
        "señalar": [
            ("yo", "el error en el documento", "describing error identification"),
            ("ella", "la dirección correcta", "narrating guidance"),
            ("nosotros", "los puntos importantes", "describing highlighting"),
        ],
        "sentar": [
            ("yo", "a los invitados en la mesa", "describing seating arrangement"),
            ("ella", "al niño en la silla", "narrating childcare"),
            ("nosotros", "las bases del acuerdo", "expressing foundation-setting"),
        ],
        "sentir": [
            ("yo", "mucha alegría", "expressing happiness"),
            ("tú", "nostalgia por el pasado", "describing longing"),
            ("nosotros", "la presión del trabajo", "expressing work stress"),
        ],
        "ser": [
            ("yo", "profesor de historia", "expressing identity"),
            ("tú", "muy inteligente", "describing a trait"),
            ("nosotros", "un equipo fuerte", "expressing team identity"),
        ],
        "servir": [
            ("yo", "la comida a los invitados", "describing hosting"),
            ("ella", "café a los clientes", "narrating service"),
            ("nosotros", "a nuestra comunidad", "expressing community service"),
        ],
        "significar": [
            ("eso", "mucho para mí", "expressing importance"),
            ("ella", "todo para su familia", "describing someone's importance"),
            ("nosotros", "esperanza para los demás", "expressing symbolic meaning"),
        ],
        "soler": [
            ("yo", "despertarme temprano", "describing a usual habit"),
            ("ella", "cocinar los domingos", "narrating routine"),
            ("nosotros", "ir al cine los sábados", "describing weekend habit"),
        ],
        "soltar": [
            ("yo", "la cuerda", "describing letting go"),
            ("tú", "una carcajada", "describing spontaneous laughter"),
            ("ella", "al perro en el parque", "narrating pet freedom"),
        ],
        "sonar": [
            ("el teléfono", "durante la reunión", "describing an interruption"),
            ("la alarma", "a las seis", "narrating wake-up time"),
            ("eso", "interesante", "expressing curiosity"),
        ],
        "subir": [
            ("yo", "las escaleras", "describing physical activity"),
            ("tú", "al autobús", "describing boarding"),
            ("nosotros", "la montaña", "narrating a hike"),
        ],
        "suceder": [
            ("eso", "con frecuencia", "expressing recurrence"),
            ("algo extraño", "en la oficina", "narrating unusual events"),
            ("los problemas", "cuando menos lo esperas", "describing unexpected issues"),
        ],
        "sufrir": [
            ("yo", "de alergias en primavera", "describing health issues"),
            ("ella", "por la distancia", "narrating emotional pain"),
            ("nosotros", "las consecuencias de nuestras decisiones", "expressing accountability"),
        ],
        "superar": [
            ("yo", "mis miedos", "expressing overcoming fear"),
            ("tú", "todos los obstáculos", "encouraging perseverance"),
            ("nosotros", "las expectativas", "expressing exceeding expectations"),
        ],
        "suponer": [
            ("yo", "que es verdad", "expressing assumption"),
            ("eso", "un gran cambio", "describing implications"),
            ("nosotros", "que vendrá mañana", "expressing expectation"),
        ],
        "temer": [
            ("yo", "lo peor", "expressing fear"),
            ("ella", "la oscuridad", "narrating a phobia"),
            ("nosotros", "las consecuencias", "expressing worry about outcomes"),
        ],
        "tener": [
            ("yo", "dos hermanos", "describing family"),
            ("tú", "mucha suerte", "expressing fortune"),
            ("nosotros", "una reunión importante", "describing schedule"),
        ],
        "terminar": [
            ("yo", "el libro esta semana", "expressing completion"),
            ("nosotros", "el proyecto a tiempo", "describing deadline success"),
            ("tú", "tus tareas", "talking about responsibilities"),
        ],
        "tirar": [
            ("yo", "la basura", "describing a chore"),
            ("tú", "la pelota muy lejos", "describing a throw"),
            ("ella", "los papeles viejos", "narrating decluttering"),
        ],
        "tocar": [
            ("yo", "la guitarra", "describing a musical hobby"),
            ("ella", "el piano con maestría", "narrating musical talent"),
            ("nosotros", "en una banda", "describing group music"),
        ],
        "tomar": [
            ("yo", "una decisión importante", "expressing decision-making"),
            ("tú", "el sol en la playa", "describing sunbathing"),
            ("nosotros", "café en la mañana", "describing morning routine"),
        ],
        "trabajar": [
            ("yo", "en una empresa grande", "describing employment"),
            ("ella", "desde casa", "narrating remote work"),
            ("nosotros", "en equipo", "expressing teamwork"),
        ],
        "traer": [
            ("yo", "la comida para la fiesta", "describing contribution"),
            ("tú", "buenas noticias", "expressing positive delivery"),
            ("ella", "flores para la oficina", "narrating a kind gesture"),
        ],
        "tranquilar": [
            ("yo", "a los pasajeros nerviosos", "expressing calming others"),
            ("ella", "a su hijo antes de dormir", "narrating bedtime routine"),
            ("nosotros", "a los vecinos preocupados", "describing community reassurance"),
        ],
        "tratar": [
            ("yo", "de ser amable", "expressing effort to be kind"),
            ("nosotros", "a todos con respeto", "describing respectful behavior"),
            ("ella", "el tema con cuidado", "narrating tactful discussion"),
        ],
        "unir": [
            ("nosotros", "fuerzas para el proyecto", "expressing collaboration"),
            ("yo", "las piezas del rompecabezas", "describing assembly"),
            ("ella", "a la familia en momentos difíciles", "narrating family unity"),
        ],
        "usar": [
            ("yo", "el transporte público", "describing commuting"),
            ("tú", "mucha tecnología", "talking about tech habits"),
            ("nosotros", "materiales reciclados", "expressing eco-friendly choices"),
        ],
        "utilizar": [
            ("yo", "herramientas modernas", "describing tool usage"),
            ("nosotros", "energía renovable", "expressing sustainability"),
            ("ella", "métodos innovadores", "narrating creative approaches"),
        ],
        "valer": [
            ("eso", "mucho dinero", "expressing value"),
            ("yo", "por mis habilidades", "expressing self-worth"),
            ("el esfuerzo", "la pena", "describing worthwhile effort"),
        ],
        "vender": [
            ("yo", "productos artesanales", "describing a business"),
            ("tú", "tu coche viejo", "talking about selling possessions"),
            ("nosotros", "servicios de consultoría", "describing professional offerings"),
        ],
        "venir": [
            ("yo", "de una familia grande", "expressing origin"),
            ("ella", "a la reunión puntual", "narrating punctuality"),
            ("ellos", "de muy lejos", "describing long-distance travel"),
        ],
        "ver": [
            ("yo", "una película interesante", "describing entertainment"),
            ("tú", "el partido de fútbol", "talking about watching sports"),
            ("nosotros", "las noticias juntos", "describing a shared activity"),
        ],
        "viajar": [
            ("yo", "por Europa", "describing travel"),
            ("ella", "por trabajo", "narrating business travel"),
            ("nosotros", "en tren", "describing a mode of transport"),
        ],
        "vivir": [
            ("yo", "en una ciudad grande", "expressing where I live"),
            ("tú", "cerca del centro", "describing location"),
            ("nosotros", "una vida tranquila", "expressing lifestyle"),
        ],
        "volar": [
            ("yo", "a Madrid", "describing air travel"),
            ("nosotros", "en primera clase", "describing travel luxury"),
            ("ella", "a su destino favorito", "narrating travel plans"),
        ],
        "volver": [
            ("yo", "a casa después del trabajo", "describing return home"),
            ("tú", "a intentar", "encouraging persistence"),
            ("nosotros", "al mismo lugar cada año", "describing tradition"),
        ],
    }

    # Now build exercises
    exercises = []
    verb_idx = 0

    for verb in VERBS:
        templates = verb_templates.get(verb)
        if not templates:
            # Fallback: generate basic templates
            templates = [
                ("yo", "eso con cuidado", "expressing a careful action"),
                ("tú", "bien", "describing how you do things"),
                ("nosotros", "juntos", "expressing teamwork"),
            ]

        for ex_idx, (subject, complement, hint) in enumerate(templates):
            tp = get_time_phrase()

            # Get subject info
            if subject in ("eso", "los zapatos", "el viaje", "el coche", "las plantas",
                          "los niños", "los bebés", "el teléfono", "la alarma",
                          "algo extraño", "los accidentes", "los problemas",
                          "el plan", "la reunión", "el esfuerzo"):
                # Third-person subjects that aren't pronouns
                subj_key = "el"
                subj_grupo = remove_accents(subject)
            elif subject in ("ella", "él"):
                subj_key = "el"
                subj_grupo = remove_accents(subject)
            elif subject == "tú":
                subj_key = "tu"
                subj_grupo = "tu"
            elif subject == "usted":
                subj_key = "usted"
                subj_grupo = "usted"
            elif subject == "ustedes":
                subj_key = "ustedes"
                subj_grupo = "ustedes"
            elif subject == "ellas":
                subj_key = "ellos"
                subj_grupo = "ellas"
            elif subject == "ellos":
                subj_key = "ellos"
                subj_grupo = "ellos"
            elif subject == "nosotros":
                subj_key = "nosotros"
                subj_grupo = "nosotros"
            elif subject == "yo":
                subj_key = "yo"
                subj_grupo = "yo"
            else:
                subj_key = "el"
                subj_grupo = remove_accents(subject)

            # Get conjugated form
            conj_form = get_conjugation(verb, subj_key)
            conj_unaccented = remove_accents(conj_form)

            # Build respuesta (complete sentence)
            # Pattern: Subject + conjugated verb + complement + time phrase
            # But we want natural sentence order, sometimes time phrase first

            # Randomly decide time phrase position
            tp_position = random.choice(["start", "end"])

            if tp_position == "start":
                respuesta = f"{tp.capitalize()}, {subject} {conj_form} {complement}."
            else:
                respuesta = f"{subject.capitalize()} {conj_form} {complement} {tp}."

            # Fix capitalization for pronoun subjects
            # Build contexto (comma-separated fragments, verb NOT conjugated)
            contexto = f"{subject}, {tp}, {complement}"

            # Build grupos
            tp_unaccented = remove_accents(tp)
            complement_unaccented = remove_accents(complement)

            grupos = [
                [subj_grupo],
                [conj_unaccented],
                [complement_unaccented],
                [tp_unaccented]
            ]

            exercise = {
                "id": f"{verb}-presente-{ex_idx}",
                "verbo": verb,
                "contexto": contexto,
                "respuesta": respuesta,
                "pista": hint,
                "grupos": grupos
            }

            exercises.append(exercise)

    return exercises

exercises = make_exercises()
print(f"Total exercises generated: {len(exercises)}")

# Verify time phrase distribution
print("\nTime phrase distribution:")
for tp, count in sorted(time_phrase_counts.items(), key=lambda x: -x[1]):
    print(f"  {tp}: {count}")

# Split into 18 batches
# 260 verbs, 3 exercises each = 780 exercises
# 780 / 18 = 43.33... exercises per batch
# But we want to split by verb groups (~15 verbs per batch)
# 8 batches × 15 verbs × 3 = 360
# 10 batches × 14 verbs × 3 = 420
# Total = 780

batches = []
verb_start = 0
for batch_idx in range(18):
    if batch_idx < 8:
        n_verbs = 15
    else:
        n_verbs = 14

    # Ensure we don't go over
    if verb_start + n_verbs > 260:
        n_verbs = 260 - verb_start

    start_ex = verb_start * 3
    end_ex = (verb_start + n_verbs) * 3
    batch = exercises[start_ex:end_ex]
    batches.append(batch)

    verb_start += n_verbs

# Verify
total_in_batches = sum(len(b) for b in batches)
print(f"\nTotal exercises in batches: {total_in_batches}")
print(f"Number of batches: {len(batches)}")
for i, b in enumerate(batches):
    print(f"  batch_{i:03d}.json: {len(b)} exercises ({len(b)//3} verbs)")

# Write batch files
for batch_idx, batch in enumerate(batches):
    filepath = os.path.join(OUTPUT_DIR, f"batch_{batch_idx:03d}.json")
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(batch, f, ensure_ascii=False, indent=2)
    print(f"Wrote {filepath}")

print("\nDone!")

# Validation checks
print("\n--- Validation ---")
errors = 0
for ex in exercises:
    # Check that grupo elements appear in respuesta (lowercased, unaccented)
    resp_lower = remove_accents(ex["respuesta"].lower().rstrip("."))
    for grupo in ex["grupos"]:
        for elem in grupo:
            if elem.lower() not in resp_lower:
                print(f"ERROR: '{elem}' not found in respuesta '{ex['respuesta']}' (id: {ex['id']})")
                errors += 1

    # Check that grupos don't contain accented chars (except ñ which we remove)
    for grupo in ex["grupos"]:
        for elem in grupo:
            for ch in elem:
                if ch in 'áéíóúüÁÉÍÓÚÜ':
                    print(f"ERROR: Accented char '{ch}' in grupo element '{elem}' (id: {ex['id']})")
                    errors += 1

print(f"Total errors: {errors}")
