#!/usr/bin/env python3
"""Generate present subjunctive speech drill exercises for 260 verbs."""

import json
import os
import unicodedata

OUTPUT_DIR = "/home/harlan/projects/harlananelson/python/output/subjuntivo"

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


def strip_accents(s):
    """Remove accents from a string."""
    nfkd = unicodedata.normalize('NFKD', s)
    return ''.join(c for c in nfkd if unicodedata.category(c) != 'Mn')


# Complete subjunctive conjugation table
# Keys: infinitive -> {subject: conjugated_form}
SUBJUNCTIVE = {}

# Regular -ar verbs: stem + e, es, e, emos, éis, en
def conjugate_ar_regular(verb):
    stem = verb[:-2]
    return {
        "yo": stem + "e",
        "tú": stem + "es",
        "él": stem + "e",
        "ella": stem + "e",
        "usted": stem + "e",
        "nosotros": stem + "emos",
        "ellos": stem + "en",
        "ellas": stem + "en",
        "ustedes": stem + "en",
    }

# Regular -er verbs: stem + a, as, a, amos, áis, an
def conjugate_er_regular(verb):
    stem = verb[:-2]
    return {
        "yo": stem + "a",
        "tú": stem + "as",
        "él": stem + "a",
        "ella": stem + "a",
        "usted": stem + "a",
        "nosotros": stem + "amos",
        "ellos": stem + "an",
        "ellas": stem + "an",
        "ustedes": stem + "an",
    }

# Regular -ir verbs: stem + a, as, a, amos, áis, an
def conjugate_ir_regular(verb):
    stem = verb[:-2]
    return {
        "yo": stem + "a",
        "tú": stem + "as",
        "él": stem + "a",
        "ella": stem + "a",
        "usted": stem + "a",
        "nosotros": stem + "amos",
        "ellos": stem + "an",
        "ellas": stem + "an",
        "ustedes": stem + "an",
    }


def make_conj(forms_dict):
    """Helper: given a dict of (subject -> form), return the full subject mapping."""
    base = {}
    for subj, form in forms_dict.items():
        base[subj] = form
    return base


# Irregular and stem-changing verb conjugations
IRREGULAR_SUBJ = {
    "ser": {"yo": "sea", "tú": "seas", "él": "sea", "ella": "sea", "usted": "sea",
            "nosotros": "seamos", "ellos": "sean", "ellas": "sean", "ustedes": "sean"},
    "estar": {"yo": "esté", "tú": "estés", "él": "esté", "ella": "esté", "usted": "esté",
              "nosotros": "estemos", "ellos": "estén", "ellas": "estén", "ustedes": "estén"},
    "ir": {"yo": "vaya", "tú": "vayas", "él": "vaya", "ella": "vaya", "usted": "vaya",
           "nosotros": "vayamos", "ellos": "vayan", "ellas": "vayan", "ustedes": "vayan"},
    "haber": {"yo": "haya", "tú": "hayas", "él": "haya", "ella": "haya", "usted": "haya",
              "nosotros": "hayamos", "ellos": "hayan", "ellas": "hayan", "ustedes": "hayan"},
    "saber": {"yo": "sepa", "tú": "sepas", "él": "sepa", "ella": "sepa", "usted": "sepa",
              "nosotros": "sepamos", "ellos": "sepan", "ellas": "sepan", "ustedes": "sepan"},
    "dar": {"yo": "dé", "tú": "des", "él": "dé", "ella": "dé", "usted": "dé",
            "nosotros": "demos", "ellos": "den", "ellas": "den", "ustedes": "den"},
    "hacer": {"yo": "haga", "tú": "hagas", "él": "haga", "ella": "haga", "usted": "haga",
              "nosotros": "hagamos", "ellos": "hagan", "ellas": "hagan", "ustedes": "hagan"},
    "decir": {"yo": "diga", "tú": "digas", "él": "diga", "ella": "diga", "usted": "diga",
              "nosotros": "digamos", "ellos": "digan", "ellas": "digan", "ustedes": "digan"},
    "tener": {"yo": "tenga", "tú": "tengas", "él": "tenga", "ella": "tenga", "usted": "tenga",
              "nosotros": "tengamos", "ellos": "tengan", "ellas": "tengan", "ustedes": "tengan"},
    "venir": {"yo": "venga", "tú": "vengas", "él": "venga", "ella": "venga", "usted": "venga",
              "nosotros": "vengamos", "ellos": "vengan", "ellas": "vengan", "ustedes": "vengan"},
    "poner": {"yo": "ponga", "tú": "pongas", "él": "ponga", "ella": "ponga", "usted": "ponga",
              "nosotros": "pongamos", "ellos": "pongan", "ellas": "pongan", "ustedes": "pongan"},
    "salir": {"yo": "salga", "tú": "salgas", "él": "salga", "ella": "salga", "usted": "salga",
              "nosotros": "salgamos", "ellos": "salgan", "ellas": "salgan", "ustedes": "salgan"},
    "poder": {"yo": "pueda", "tú": "puedas", "él": "pueda", "ella": "pueda", "usted": "pueda",
              "nosotros": "podamos", "ellos": "puedan", "ellas": "puedan", "ustedes": "puedan"},
    "querer": {"yo": "quiera", "tú": "quieras", "él": "quiera", "ella": "quiera", "usted": "quiera",
               "nosotros": "queramos", "ellos": "quieran", "ellas": "quieran", "ustedes": "quieran"},
    "oír": {"yo": "oiga", "tú": "oigas", "él": "oiga", "ella": "oiga", "usted": "oiga",
            "nosotros": "oigamos", "ellos": "oigan", "ellas": "oigan", "ustedes": "oigan"},
    "traer": {"yo": "traiga", "tú": "traigas", "él": "traiga", "ella": "traiga", "usted": "traiga",
              "nosotros": "traigamos", "ellos": "traigan", "ellas": "traigan", "ustedes": "traigan"},
    "caer": {"yo": "caiga", "tú": "caigas", "él": "caiga", "ella": "caiga", "usted": "caiga",
             "nosotros": "caigamos", "ellos": "caigan", "ellas": "caigan", "ustedes": "caigan"},
    "valer": {"yo": "valga", "tú": "valgas", "él": "valga", "ella": "valga", "usted": "valga",
              "nosotros": "valgamos", "ellos": "valgan", "ellas": "valgan", "ustedes": "valgan"},
    "ver": {"yo": "vea", "tú": "veas", "él": "vea", "ella": "vea", "usted": "vea",
            "nosotros": "veamos", "ellos": "vean", "ellas": "vean", "ustedes": "vean"},
    # conducir -> conduzc-
    "conducir": {"yo": "conduzca", "tú": "conduzcas", "él": "conduzca", "ella": "conduzca", "usted": "conduzca",
                 "nosotros": "conduzcamos", "ellos": "conduzcan", "ellas": "conduzcan", "ustedes": "conduzcan"},
    "producir": {"yo": "produzca", "tú": "produzcas", "él": "produzca", "ella": "produzca", "usted": "produzca",
                 "nosotros": "produzcamos", "ellos": "produzcan", "ellas": "produzcan", "ustedes": "produzcan"},
    # -cer/-cir verbs with zc
    "conocer": {"yo": "conozca", "tú": "conozcas", "él": "conozca", "ella": "conozca", "usted": "conozca",
                "nosotros": "conozcamos", "ellos": "conozcan", "ellas": "conozcan", "ustedes": "conozcan"},
    "aparecer": {"yo": "aparezca", "tú": "aparezcas", "él": "aparezca", "ella": "aparezca", "usted": "aparezca",
                 "nosotros": "aparezcamos", "ellos": "aparezcan", "ellas": "aparezcan", "ustedes": "aparezcan"},
    "desaparecer": {"yo": "desaparezca", "tú": "desaparezcas", "él": "desaparezca", "ella": "desaparezca", "usted": "desaparezca",
                    "nosotros": "desaparezcamos", "ellos": "desaparezcan", "ellas": "desaparezcan", "ustedes": "desaparezcan"},
    "agradecer": {"yo": "agradezca", "tú": "agradezcas", "él": "agradezca", "ella": "agradezca", "usted": "agradezca",
                  "nosotros": "agradezcamos", "ellos": "agradezcan", "ellas": "agradezcan", "ustedes": "agradezcan"},
    "crecer": {"yo": "crezca", "tú": "crezcas", "él": "crezca", "ella": "crezca", "usted": "crezca",
               "nosotros": "crezcamos", "ellos": "crezcan", "ellas": "crezcan", "ustedes": "crezcan"},
    "merecer": {"yo": "merezca", "tú": "merezcas", "él": "merezca", "ella": "merezca", "usted": "merezca",
                "nosotros": "merezcamos", "ellos": "merezcan", "ellas": "merezcan", "ustedes": "merezcan"},
    "ofrecer": {"yo": "ofrezca", "tú": "ofrezcas", "él": "ofrezca", "ella": "ofrezca", "usted": "ofrezca",
                "nosotros": "ofrezcamos", "ellos": "ofrezcan", "ellas": "ofrezcan", "ustedes": "ofrezcan"},
    "parecer": {"yo": "parezca", "tú": "parezcas", "él": "parezca", "ella": "parezca", "usted": "parezca",
                "nosotros": "parezcamos", "ellos": "parezcan", "ellas": "parezcan", "ustedes": "parezcan"},
    "permanecer": {"yo": "permanezca", "tú": "permanezcas", "él": "permanezca", "ella": "permanezca", "usted": "permanezca",
                   "nosotros": "permanezcamos", "ellos": "permanezcan", "ellas": "permanezcan", "ustedes": "permanezcan"},
    "pertenecer": {"yo": "pertenezca", "tú": "pertenezcas", "él": "pertenezca", "ella": "pertenezca", "usted": "pertenezca",
                   "nosotros": "pertenezcamos", "ellos": "pertenezcan", "ellas": "pertenezcan", "ustedes": "pertenezcan"},
    "nacer": {"yo": "nazca", "tú": "nazcas", "él": "nazca", "ella": "nazca", "usted": "nazca",
              "nosotros": "nazcamos", "ellos": "nazcan", "ellas": "nazcan", "ustedes": "nazcan"},
    "reconocer": {"yo": "reconozca", "tú": "reconozcas", "él": "reconozca", "ella": "reconozca", "usted": "reconozca",
                  "nosotros": "reconozcamos", "ellos": "reconozcan", "ellas": "reconozcan", "ustedes": "reconozcan"},
    "encantar": {"yo": "encante", "tú": "encantes", "él": "encante", "ella": "encante", "usted": "encante",
                 "nosotros": "encantemos", "ellos": "encanten", "ellas": "encanten", "ustedes": "encanten"},
    # stem-changing: e->ie
    "cerrar": {"yo": "cierre", "tú": "cierres", "él": "cierre", "ella": "cierre", "usted": "cierre",
               "nosotros": "cerremos", "ellos": "cierren", "ellas": "cierren", "ustedes": "cierren"},
    "comenzar": {"yo": "comience", "tú": "comiences", "él": "comience", "ella": "comience", "usted": "comience",
                 "nosotros": "comencemos", "ellos": "comiencen", "ellas": "comiencen", "ustedes": "comiencen"},
    "empezar": {"yo": "empiece", "tú": "empieces", "él": "empiece", "ella": "empiece", "usted": "empiece",
                "nosotros": "empecemos", "ellos": "empiecen", "ellas": "empiecen", "ustedes": "empiecen"},
    "pensar": {"yo": "piense", "tú": "pienses", "él": "piense", "ella": "piense", "usted": "piense",
               "nosotros": "pensemos", "ellos": "piensen", "ellas": "piensen", "ustedes": "piensen"},
    "despertar": {"yo": "despierte", "tú": "despiertes", "él": "despierte", "ella": "despierte", "usted": "despierte",
                  "nosotros": "despertemos", "ellos": "despierten", "ellas": "despierten", "ustedes": "despierten"},
    "negar": {"yo": "niegue", "tú": "niegues", "él": "niegue", "ella": "niegue", "usted": "niegue",
              "nosotros": "neguemos", "ellos": "nieguen", "ellas": "nieguen", "ustedes": "nieguen"},
    "sentar": {"yo": "siente", "tú": "sientes", "él": "siente", "ella": "siente", "usted": "siente",
               "nosotros": "sentemos", "ellos": "sienten", "ellas": "sienten", "ustedes": "sienten"},
    "entender": {"yo": "entienda", "tú": "entiendas", "él": "entienda", "ella": "entienda", "usted": "entienda",
                 "nosotros": "entendamos", "ellos": "entiendan", "ellas": "entiendan", "ustedes": "entiendan"},
    "perder": {"yo": "pierda", "tú": "pierdas", "él": "pierda", "ella": "pierda", "usted": "pierda",
               "nosotros": "perdamos", "ellos": "pierdan", "ellas": "pierdan", "ustedes": "pierdan"},
    "defender": {"yo": "defienda", "tú": "defiendas", "él": "defienda", "ella": "defienda", "usted": "defienda",
                 "nosotros": "defendamos", "ellos": "defiendan", "ellas": "defiendan", "ustedes": "defiendan"},
    "sentir": {"yo": "sienta", "tú": "sientas", "él": "sienta", "ella": "sienta", "usted": "sienta",
               "nosotros": "sintamos", "ellos": "sientan", "ellas": "sientan", "ustedes": "sientan"},
    "mentir": {"yo": "mienta", "tú": "mientas", "él": "mienta", "ella": "mienta", "usted": "mienta",
               "nosotros": "mintamos", "ellos": "mientan", "ellas": "mientan", "ustedes": "mientan"},
    "preferir": {"yo": "prefiera", "tú": "prefieras", "él": "prefiera", "ella": "prefiera", "usted": "prefiera",
                 "nosotros": "prefiramos", "ellos": "prefieran", "ellas": "prefieran", "ustedes": "prefieran"},
    "referir": {"yo": "refiera", "tú": "refieras", "él": "refiera", "ella": "refiera", "usted": "refiera",
                "nosotros": "refiramos", "ellos": "refieran", "ellas": "refieran", "ustedes": "refieran"},
    "convertir": {"yo": "convierta", "tú": "conviertas", "él": "convierta", "ella": "convierta", "usted": "convierta",
                  "nosotros": "convirtamos", "ellos": "conviertan", "ellas": "conviertan", "ustedes": "conviertan"},
    # stem-changing: o->ue
    "contar": {"yo": "cuente", "tú": "cuentes", "él": "cuente", "ella": "cuente", "usted": "cuente",
               "nosotros": "contemos", "ellos": "cuenten", "ellas": "cuenten", "ustedes": "cuenten"},
    "encontrar": {"yo": "encuentre", "tú": "encuentres", "él": "encuentre", "ella": "encuentre", "usted": "encuentre",
                  "nosotros": "encontremos", "ellos": "encuentren", "ellas": "encuentren", "ustedes": "encuentren"},
    "recordar": {"yo": "recuerde", "tú": "recuerdes", "él": "recuerde", "ella": "recuerde", "usted": "recuerde",
                 "nosotros": "recordemos", "ellos": "recuerden", "ellas": "recuerden", "ustedes": "recuerden"},
    "acordar": {"yo": "acuerde", "tú": "acuerdes", "él": "acuerde", "ella": "acuerde", "usted": "acuerde",
                "nosotros": "acordemos", "ellos": "acuerden", "ellas": "acuerden", "ustedes": "acuerden"},
    "costar": {"yo": "cueste", "tú": "cuestes", "él": "cueste", "ella": "cueste", "usted": "cueste",
               "nosotros": "costemos", "ellos": "cuesten", "ellas": "cuesten", "ustedes": "cuesten"},
    "demostrar": {"yo": "demuestre", "tú": "demuestres", "él": "demuestre", "ella": "demuestre", "usted": "demuestre",
                  "nosotros": "demostremos", "ellos": "demuestren", "ellas": "demuestren", "ustedes": "demuestren"},
    "mostrar": {"yo": "muestre", "tú": "muestres", "él": "muestre", "ella": "muestre", "usted": "muestre",
                "nosotros": "mostremos", "ellos": "muestren", "ellas": "muestren", "ustedes": "muestren"},
    "probar": {"yo": "pruebe", "tú": "pruebes", "él": "pruebe", "ella": "pruebe", "usted": "pruebe",
               "nosotros": "probemos", "ellos": "prueben", "ellas": "prueben", "ustedes": "prueben"},
    "apostar": {"yo": "apueste", "tú": "apuestes", "él": "apueste", "ella": "apueste", "usted": "apueste",
                "nosotros": "apostemos", "ellos": "apuesten", "ellas": "apuesten", "ustedes": "apuesten"},
    "volar": {"yo": "vuele", "tú": "vueles", "él": "vuele", "ella": "vuele", "usted": "vuele",
              "nosotros": "volemos", "ellos": "vuelen", "ellas": "vuelen", "ustedes": "vuelen"},
    "sonar": {"yo": "suene", "tú": "suenes", "él": "suene", "ella": "suene", "usted": "suene",
              "nosotros": "sonemos", "ellos": "suenen", "ellas": "suenen", "ustedes": "suenen"},
    "soltar": {"yo": "suelte", "tú": "sueltes", "él": "suelte", "ella": "suelte", "usted": "suelte",
               "nosotros": "soltemos", "ellos": "suelten", "ellas": "suelten", "ustedes": "suelten"},
    "devolver": {"yo": "devuelva", "tú": "devuelvas", "él": "devuelva", "ella": "devuelva", "usted": "devuelva",
                 "nosotros": "devolvamos", "ellos": "devuelvan", "ellas": "devuelvan", "ustedes": "devuelvan"},
    "volver": {"yo": "vuelva", "tú": "vuelvas", "él": "vuelva", "ella": "vuelva", "usted": "vuelva",
               "nosotros": "volvamos", "ellos": "vuelvan", "ellas": "vuelvan", "ustedes": "vuelvan"},
    "resolver": {"yo": "resuelva", "tú": "resuelvas", "él": "resuelva", "ella": "resuelva", "usted": "resuelva",
                 "nosotros": "resolvamos", "ellos": "resuelvan", "ellas": "resuelvan", "ustedes": "resuelvan"},
    "mover": {"yo": "mueva", "tú": "muevas", "él": "mueva", "ella": "mueva", "usted": "mueva",
              "nosotros": "movamos", "ellos": "muevan", "ellas": "muevan", "ustedes": "muevan"},
    "dormir": {"yo": "duerma", "tú": "duermas", "él": "duerma", "ella": "duerma", "usted": "duerma",
               "nosotros": "durmamos", "ellos": "duerman", "ellas": "duerman", "ustedes": "duerman"},
    "morir": {"yo": "muera", "tú": "mueras", "él": "muera", "ella": "muera", "usted": "muera",
              "nosotros": "muramos", "ellos": "mueran", "ellas": "mueran", "ustedes": "mueran"},
    # stem-changing: e->i
    "pedir": {"yo": "pida", "tú": "pidas", "él": "pida", "ella": "pida", "usted": "pida",
              "nosotros": "pidamos", "ellos": "pidan", "ellas": "pidan", "ustedes": "pidan"},
    "seguir": {"yo": "siga", "tú": "sigas", "él": "siga", "ella": "siga", "usted": "siga",
               "nosotros": "sigamos", "ellos": "sigan", "ellas": "sigan", "ustedes": "sigan"},
    "conseguir": {"yo": "consiga", "tú": "consigas", "él": "consiga", "ella": "consiga", "usted": "consiga",
                  "nosotros": "consigamos", "ellos": "consigan", "ellas": "consigan", "ustedes": "consigan"},
    "repetir": {"yo": "repita", "tú": "repitas", "él": "repita", "ella": "repita", "usted": "repita",
                "nosotros": "repitamos", "ellos": "repitan", "ellas": "repitan", "ustedes": "repitan"},
    "servir": {"yo": "sirva", "tú": "sirvas", "él": "sirva", "ella": "sirva", "usted": "sirva",
               "nosotros": "sirvamos", "ellos": "sirvan", "ellas": "sirvan", "ustedes": "sirvan"},
    "elegir": {"yo": "elija", "tú": "elijas", "él": "elija", "ella": "elija", "usted": "elija",
               "nosotros": "elijamos", "ellos": "elijan", "ellas": "elijan", "ustedes": "elijan"},
    "reír": {"yo": "ría", "tú": "rías", "él": "ría", "ella": "ría", "usted": "ría",
             "nosotros": "riamos", "ellos": "rían", "ellas": "rían", "ustedes": "rían"},
    "despedir": {"yo": "despida", "tú": "despidas", "él": "despida", "ella": "despida", "usted": "despida",
                 "nosotros": "despidamos", "ellos": "despidan", "ellas": "despidan", "ustedes": "despidan"},
    # -ger/-gir verbs: g->j before a
    "coger": {"yo": "coja", "tú": "cojas", "él": "coja", "ella": "coja", "usted": "coja",
              "nosotros": "cojamos", "ellos": "cojan", "ellas": "cojan", "ustedes": "cojan"},
    "recoger": {"yo": "recoja", "tú": "recojas", "él": "recoja", "ella": "recoja", "usted": "recoja",
                "nosotros": "recojamos", "ellos": "recojan", "ellas": "recojan", "ustedes": "recojan"},
    "proteger": {"yo": "proteja", "tú": "protejas", "él": "proteja", "ella": "proteja", "usted": "proteja",
                 "nosotros": "protejamos", "ellos": "protejan", "ellas": "protejan", "ustedes": "protejan"},
    "dirigir": {"yo": "dirija", "tú": "dirijas", "él": "dirija", "ella": "dirija", "usted": "dirija",
                "nosotros": "dirijamos", "ellos": "dirijan", "ellas": "dirijan", "ustedes": "dirijan"},
    # -uir verbs: add y
    "construir": {"yo": "construya", "tú": "construyas", "él": "construya", "ella": "construya", "usted": "construya",
                  "nosotros": "construyamos", "ellos": "construyan", "ellas": "construyan", "ustedes": "construyan"},
    "destruir": {"yo": "destruya", "tú": "destruyas", "él": "destruya", "ella": "destruya", "usted": "destruya",
                 "nosotros": "destruyamos", "ellos": "destruyan", "ellas": "destruyan", "ustedes": "destruyan"},
    "huir": {"yo": "huya", "tú": "huyas", "él": "huya", "ella": "huya", "usted": "huya",
             "nosotros": "huyamos", "ellos": "huyan", "ellas": "huyan", "ustedes": "huyan"},
    "incluir": {"yo": "incluya", "tú": "incluyas", "él": "incluya", "ella": "incluya", "usted": "incluya",
                "nosotros": "incluyamos", "ellos": "incluyan", "ellas": "incluyan", "ustedes": "incluyan"},
    "concluir": {"yo": "concluya", "tú": "concluyas", "él": "concluya", "ella": "concluya", "usted": "concluya",
                 "nosotros": "concluyamos", "ellos": "concluyan", "ellas": "concluyan", "ustedes": "concluyan"},
    # -car verbs: c->qu before e
    "buscar": {"yo": "busque", "tú": "busques", "él": "busque", "ella": "busque", "usted": "busque",
               "nosotros": "busquemos", "ellos": "busquen", "ellas": "busquen", "ustedes": "busquen"},
    "sacar": {"yo": "saque", "tú": "saques", "él": "saque", "ella": "saque", "usted": "saque",
              "nosotros": "saquemos", "ellos": "saquen", "ellas": "saquen", "ustedes": "saquen"},
    "tocar": {"yo": "toque", "tú": "toques", "él": "toque", "ella": "toque", "usted": "toque",
              "nosotros": "toquemos", "ellos": "toquen", "ellas": "toquen", "ustedes": "toquen"},
    "atacar": {"yo": "ataque", "tú": "ataques", "él": "ataque", "ella": "ataque", "usted": "ataque",
               "nosotros": "ataquemos", "ellos": "ataquen", "ellas": "ataquen", "ustedes": "ataquen"},
    "explicar": {"yo": "explique", "tú": "expliques", "él": "explique", "ella": "explique", "usted": "explique",
                 "nosotros": "expliquemos", "ellos": "expliquen", "ellas": "expliquen", "ustedes": "expliquen"},
    "significar": {"yo": "signifique", "tú": "signifiques", "él": "signifique", "ella": "signifique", "usted": "signifique",
                   "nosotros": "signifiquemos", "ellos": "signifiquen", "ellas": "signifiquen", "ustedes": "signifiquen"},
    # -gar verbs: g->gu before e
    "llegar": {"yo": "llegue", "tú": "llegues", "él": "llegue", "ella": "llegue", "usted": "llegue",
               "nosotros": "lleguemos", "ellos": "lleguen", "ellas": "lleguen", "ustedes": "lleguen"},
    "pagar": {"yo": "pague", "tú": "pagues", "él": "pague", "ella": "pague", "usted": "pague",
              "nosotros": "paguemos", "ellos": "paguen", "ellas": "paguen", "ustedes": "paguen"},
    "jugar": {"yo": "juegue", "tú": "juegues", "él": "juegue", "ella": "juegue", "usted": "juegue",
              "nosotros": "juguemos", "ellos": "jueguen", "ellas": "jueguen", "ustedes": "jueguen"},
    "entregar": {"yo": "entregue", "tú": "entregues", "él": "entregue", "ella": "entregue", "usted": "entregue",
                 "nosotros": "entreguemos", "ellos": "entreguen", "ellas": "entreguen", "ustedes": "entreguen"},
    # -zar verbs: z->c before e
    "alcanzar": {"yo": "alcance", "tú": "alcances", "él": "alcance", "ella": "alcance", "usted": "alcance",
                 "nosotros": "alcancemos", "ellos": "alcancen", "ellas": "alcancen", "ustedes": "alcancen"},
    "realizar": {"yo": "realice", "tú": "realices", "él": "realice", "ella": "realice", "usted": "realice",
                 "nosotros": "realicemos", "ellos": "realicen", "ellas": "realicen", "ustedes": "realicen"},
    "utilizar": {"yo": "utilice", "tú": "utilices", "él": "utilice", "ella": "utilice", "usted": "utilice",
                 "nosotros": "utilicemos", "ellos": "utilicen", "ellas": "utilicen", "ustedes": "utilicen"},
    # -guar verbs: gu->gü before e
    "averiguar": {"yo": "averigüe", "tú": "averigües", "él": "averigüe", "ella": "averigüe", "usted": "averigüe",
                  "nosotros": "averigüemos", "ellos": "averigüen", "ellas": "averigüen", "ustedes": "averigüen"},
    # mantener, detener, obtener (like tener)
    "mantener": {"yo": "mantenga", "tú": "mantengas", "él": "mantenga", "ella": "mantenga", "usted": "mantenga",
                 "nosotros": "mantengamos", "ellos": "mantengan", "ellas": "mantengan", "ustedes": "mantengan"},
    "detener": {"yo": "detenga", "tú": "detengas", "él": "detenga", "ella": "detenga", "usted": "detenga",
                "nosotros": "detengamos", "ellos": "detengan", "ellas": "detengan", "ustedes": "detengan"},
    "obtener": {"yo": "obtenga", "tú": "obtengas", "él": "obtenga", "ella": "obtenga", "usted": "obtenga",
                "nosotros": "obtengamos", "ellos": "obtengan", "ellas": "obtengan", "ustedes": "obtengan"},
    # suponer (like poner)
    "suponer": {"yo": "suponga", "tú": "supongas", "él": "suponga", "ella": "suponga", "usted": "suponga",
                "nosotros": "supongamos", "ellos": "supongan", "ellas": "supongan", "ustedes": "supongan"},
    # -iar verbs with accent shift: enviar, confiar
    "enviar": {"yo": "envíe", "tú": "envíes", "él": "envíe", "ella": "envíe", "usted": "envíe",
               "nosotros": "enviemos", "ellos": "envíen", "ellas": "envíen", "ustedes": "envíen"},
    "confiar": {"yo": "confíe", "tú": "confíes", "él": "confíe", "ella": "confíe", "usted": "confíe",
                "nosotros": "confiemos", "ellos": "confíen", "ellas": "confíen", "ustedes": "confíen"},
    # -uar verbs with accent shift: actuar, continuar
    "actuar": {"yo": "actúe", "tú": "actúes", "él": "actúe", "ella": "actúe", "usted": "actúe",
               "nosotros": "actuemos", "ellos": "actúen", "ellas": "actúen", "ustedes": "actúen"},
    "continuar": {"yo": "continúe", "tú": "continúes", "él": "continúe", "ella": "continúe", "usted": "continúe",
                  "nosotros": "continuemos", "ellos": "continúen", "ellas": "continúen", "ustedes": "continúen"},
    # reunir: accent on u in stressed forms
    "reunir": {"yo": "reúna", "tú": "reúnas", "él": "reúna", "ella": "reúna", "usted": "reúna",
               "nosotros": "reunamos", "ellos": "reúnan", "ellas": "reúnan", "ustedes": "reúnan"},
    # soler (o->ue)
    "soler": {"yo": "suela", "tú": "suelas", "él": "suela", "ella": "suela", "usted": "suela",
              "nosotros": "solamos", "ellos": "suelan", "ellas": "suelan", "ustedes": "suelan"},
    # andar (irregular, but regular in subjunctive)
    "andar": {"yo": "ande", "tú": "andes", "él": "ande", "ella": "ande", "usted": "ande",
              "nosotros": "andemos", "ellos": "anden", "ellas": "anden", "ustedes": "anden"},
    # creer - regular
    "creer": {"yo": "crea", "tú": "creas", "él": "crea", "ella": "crea", "usted": "crea",
              "nosotros": "creamos", "ellos": "crean", "ellas": "crean", "ustedes": "crean"},
    # leer - regular
    "leer": {"yo": "lea", "tú": "leas", "él": "lea", "ella": "lea", "usted": "lea",
             "nosotros": "leamos", "ellos": "lean", "ellas": "lean", "ustedes": "lean"},
    # joder - regular
    "joder": {"yo": "joda", "tú": "jodas", "él": "joda", "ella": "joda", "usted": "joda",
              "nosotros": "jodamos", "ellos": "jodan", "ellas": "jodan", "ustedes": "jodan"},
    # aforar - regular -ar
    "aforar": {"yo": "afore", "tú": "afores", "él": "afore", "ella": "afore", "usted": "afore",
               "nosotros": "aforemos", "ellos": "aforen", "ellas": "aforen", "ustedes": "aforen"},
    # tranquilar - regular -ar
    "tranquilar": {"yo": "tranquile", "tú": "tranquiles", "él": "tranquile", "ella": "tranquile", "usted": "tranquile",
                   "nosotros": "tranquilemos", "ellos": "tranquilen", "ellas": "tranquilen", "ustedes": "tranquilen"},
    # pegar - -gar verb
    "pegar": {"yo": "pegue", "tú": "pegues", "él": "pegue", "ella": "pegue", "usted": "pegue",
              "nosotros": "peguemos", "ellos": "peguen", "ellas": "peguen", "ustedes": "peguen"},
    # señalar - regular
    "señalar": {"yo": "señale", "tú": "señales", "él": "señale", "ella": "señale", "usted": "señale",
                "nosotros": "señalemos", "ellos": "señalen", "ellas": "señalen", "ustedes": "señalen"},
    # deber - regular
    "deber": {"yo": "deba", "tú": "debas", "él": "deba", "ella": "deba", "usted": "deba",
              "nosotros": "debamos", "ellos": "deban", "ellas": "deban", "ustedes": "deban"},
}


def get_subjunctive(verb):
    """Get subjunctive conjugation for a verb."""
    if verb in IRREGULAR_SUBJ:
        return IRREGULAR_SUBJ[verb]

    # Auto-generate for regular verbs and some spelling-change patterns
    if verb.endswith("car"):
        # c -> qu before e
        stem = verb[:-3]
        return {
            "yo": stem + "que", "tú": stem + "ques", "él": stem + "que",
            "ella": stem + "que", "usted": stem + "que",
            "nosotros": stem + "quemos", "ellos": stem + "quen",
            "ellas": stem + "quen", "ustedes": stem + "quen",
        }
    elif verb.endswith("gar"):
        # g -> gu before e
        stem = verb[:-3]
        return {
            "yo": stem + "gue", "tú": stem + "gues", "él": stem + "gue",
            "ella": stem + "gue", "usted": stem + "gue",
            "nosotros": stem + "guemos", "ellos": stem + "guen",
            "ellas": stem + "guen", "ustedes": stem + "guen",
        }
    elif verb.endswith("zar"):
        # z -> c before e
        stem = verb[:-3]
        return {
            "yo": stem + "ce", "tú": stem + "ces", "él": stem + "ce",
            "ella": stem + "ce", "usted": stem + "ce",
            "nosotros": stem + "cemos", "ellos": stem + "cen",
            "ellas": stem + "cen", "ustedes": stem + "cen",
        }
    elif verb.endswith("cer") and verb not in IRREGULAR_SUBJ:
        # Most -cer verbs: c -> zc (if preceded by vowel)
        stem = verb[:-3]
        if stem and stem[-1] in "aeiou":
            return {
                "yo": stem + "zca", "tú": stem + "zcas", "él": stem + "zca",
                "ella": stem + "zca", "usted": stem + "zca",
                "nosotros": stem + "zcamos", "ellos": stem + "zcan",
                "ellas": stem + "zcan", "ustedes": stem + "zcan",
            }
        else:
            return conjugate_er_regular(verb)
    elif verb.endswith("cir") and verb not in IRREGULAR_SUBJ:
        stem = verb[:-3]
        if stem and stem[-1] in "aeiou":
            return {
                "yo": stem + "zca", "tú": stem + "zcas", "él": stem + "zca",
                "ella": stem + "zca", "usted": stem + "zca",
                "nosotros": stem + "zcamos", "ellos": stem + "zcan",
                "ellas": stem + "zcan", "ustedes": stem + "zcan",
            }
        else:
            return conjugate_ir_regular(verb)
    elif verb.endswith("ger") and verb not in IRREGULAR_SUBJ:
        # g -> j before a
        stem = verb[:-3]
        return {
            "yo": stem + "ja", "tú": stem + "jas", "él": stem + "ja",
            "ella": stem + "ja", "usted": stem + "ja",
            "nosotros": stem + "jamos", "ellos": stem + "jan",
            "ellas": stem + "jan", "ustedes": stem + "jan",
        }
    elif verb.endswith("gir") and verb not in IRREGULAR_SUBJ:
        stem = verb[:-3]
        return {
            "yo": stem + "ja", "tú": stem + "jas", "él": stem + "ja",
            "ella": stem + "ja", "usted": stem + "ja",
            "nosotros": stem + "jamos", "ellos": stem + "jan",
            "ellas": stem + "jan", "ustedes": stem + "jan",
        }
    elif verb.endswith("uir") and verb not in IRREGULAR_SUBJ:
        # add y
        stem = verb[:-2]  # remove "ir"
        return {
            "yo": stem + "ya", "tú": stem + "yas", "él": stem + "ya",
            "ella": stem + "ya", "usted": stem + "ya",
            "nosotros": stem + "yamos", "ellos": stem + "yan",
            "ellas": stem + "yan", "ustedes": stem + "yan",
        }
    elif verb.endswith("ar"):
        return conjugate_ar_regular(verb)
    elif verb.endswith("er"):
        return conjugate_er_regular(verb)
    elif verb.endswith("ir"):
        return conjugate_ir_regular(verb)
    else:
        # fallback: treat as -ar
        return conjugate_ar_regular(verb)


# Exercise templates: (trigger, hint_es, subject_pool, complement_template)
# Each trigger phrase requires subjunctive for a specific reason
EXERCISE_TEMPLATES = [
    # Desire/wish triggers
    {
        "trigger": "espero que",
        "hint": "El verbo 'esperar' expresa un deseo, lo cual requiere el subjuntivo.",
        "complements": [
            ("{subj} {verb} la verdad pronto", "la verdad pronto"),
            ("{subj} {verb} sin problemas", "sin problemas"),
            ("{subj} {verb} bien esta semana", "bien esta semana"),
            ("{subj} {verb} con cuidado", "con cuidado"),
            ("{subj} {verb} a tiempo", "a tiempo"),
        ]
    },
    {
        "trigger": "quiero que",
        "hint": "El verbo 'querer' con un sujeto diferente exige el subjuntivo.",
        "complements": [
            ("{subj} {verb} todo correctamente", "todo correctamente"),
            ("{subj} {verb} lo antes posible", "lo antes posible"),
            ("{subj} {verb} de manera diferente", "de manera diferente"),
            ("{subj} {verb} en este momento", "en este momento"),
            ("{subj} {verb} con nosotros", "con nosotros"),
        ]
    },
    {
        "trigger": "ojalá",
        "hint": "'Ojalá' siempre requiere el subjuntivo para expresar un deseo.",
        "complements": [
            ("{subj} {verb} hoy", "hoy"),
            ("{subj} {verb} pronto", "pronto"),
            ("{subj} {verb} mañana", "mañana"),
            ("{subj} {verb} esta noche", "esta noche"),
            ("{subj} {verb} este fin de semana", "este fin de semana"),
        ]
    },
    # Necessity/importance triggers
    {
        "trigger": "es necesario que",
        "hint": "La expresión impersonal 'es necesario que' exige el subjuntivo.",
        "complements": [
            ("{subj} {verb} antes del viernes", "antes del viernes"),
            ("{subj} {verb} sin demora", "sin demora"),
            ("{subj} {verb} con atención", "con atención"),
            ("{subj} {verb} de inmediato", "de inmediato"),
            ("{subj} {verb} cada día", "cada día"),
        ]
    },
    {
        "trigger": "es importante que",
        "hint": "'Es importante que' expresa una valoración y necesita el subjuntivo.",
        "complements": [
            ("{subj} {verb} con responsabilidad", "con responsabilidad"),
            ("{subj} {verb} de forma adecuada", "de forma adecuada"),
            ("{subj} {verb} bien", "bien"),
            ("{subj} {verb} en equipo", "en equipo"),
            ("{subj} {verb} sin errores", "sin errores"),
        ]
    },
    # Doubt/denial triggers
    {
        "trigger": "dudo que",
        "hint": "El verbo 'dudar' expresa incertidumbre y requiere el subjuntivo.",
        "complements": [
            ("{subj} {verb} a tiempo", "a tiempo"),
            ("{subj} {verb} sin ayuda", "sin ayuda"),
            ("{subj} {verb} tan rápido", "tan rapido"),
            ("{subj} {verb} correctamente", "correctamente"),
            ("{subj} {verb} antes del lunes", "antes del lunes"),
        ]
    },
    {
        "trigger": "no creo que",
        "hint": "'No creo que' expresa duda y necesita el subjuntivo.",
        "complements": [
            ("{subj} {verb} esta vez", "esta vez"),
            ("{subj} {verb} tan fácilmente", "tan facilmente"),
            ("{subj} {verb} sin problemas", "sin problemas"),
            ("{subj} {verb} solo", "solo"),
            ("{subj} {verb} hoy", "hoy"),
        ]
    },
    # Possibility trigger
    {
        "trigger": "es posible que",
        "hint": "'Es posible que' expresa posibilidad y requiere el subjuntivo.",
        "complements": [
            ("{subj} {verb} mañana", "mañana"),
            ("{subj} {verb} la próxima semana", "la proxima semana"),
            ("{subj} {verb} más tarde", "mas tarde"),
            ("{subj} {verb} pronto", "pronto"),
            ("{subj} {verb} este mes", "este mes"),
        ]
    },
    # Purpose trigger
    {
        "trigger": "para que",
        "hint": "'Para que' introduce un propósito y siempre lleva subjuntivo.",
        "complements": [
            ("{subj} {verb} mejor", "mejor"),
            ("{subj} {verb} con éxito", "con exito"),
            ("{subj} {verb} sin dificultad", "sin dificultad"),
            ("{subj} {verb} tranquilamente", "tranquilamente"),
            ("{subj} {verb} a gusto", "a gusto"),
        ]
    },
    # Temporal trigger
    {
        "trigger": "antes de que",
        "hint": "'Antes de que' indica un evento futuro e incierto, por eso lleva subjuntivo.",
        "complements": [
            ("{subj} {verb} demasiado tarde", "demasiado tarde"),
            ("{subj} {verb} otra vez", "otra vez"),
            ("{subj} {verb} sin permiso", "sin permiso"),
            ("{subj} {verb} de nuevo", "de nuevo"),
            ("{subj} {verb} por la noche", "por la noche"),
        ]
    },
    # Concessive trigger
    {
        "trigger": "aunque",
        "hint": "'Aunque' con subjuntivo indica una situación hipotética o no confirmada.",
        "complements": [
            ("{subj} {verb} poco", "poco"),
            ("{subj} {verb} mal", "mal"),
            ("{subj} {verb} tarde", "tarde"),
            ("{subj} {verb} despacio", "despacio"),
            ("{subj} {verb} solo una vez", "solo una vez"),
        ]
    },
    # Other triggers
    {
        "trigger": "hasta que",
        "hint": "'Hasta que' con una acción futura requiere el subjuntivo.",
        "complements": [
            ("{subj} {verb} por completo", "por completo"),
            ("{subj} {verb} bien", "bien"),
            ("{subj} {verb} todo", "todo"),
            ("{subj} {verb} de verdad", "de verdad"),
            ("{subj} {verb} suficiente", "suficiente"),
        ]
    },
    {
        "trigger": "a menos que",
        "hint": "'A menos que' introduce una condición y siempre lleva subjuntivo.",
        "complements": [
            ("{subj} {verb} primero", "primero"),
            ("{subj} {verb} ahora mismo", "ahora mismo"),
            ("{subj} {verb} con tiempo", "con tiempo"),
            ("{subj} {verb} rápidamente", "rapidamente"),
            ("{subj} {verb} con cuidado", "con cuidado"),
        ]
    },
    {
        "trigger": "sin que",
        "hint": "'Sin que' expresa una acción que no ocurre y necesita el subjuntivo.",
        "complements": [
            ("{subj} {verb} nada", "nada"),
            ("{subj} {verb} mucho", "mucho"),
            ("{subj} {verb} antes", "antes"),
            ("{subj} {verb} demasiado", "demasiado"),
            ("{subj} {verb} algo", "algo"),
        ]
    },
]

# Subject pools for variety
SUBJECTS_BY_PERSON = [
    # 3 different subjects per verb, rotating
    ("tú", "él", "ellos"),
    ("ella", "nosotros", "ustedes"),
    ("usted", "ellas", "yo"),
    ("tú", "ella", "nosotros"),
    ("él", "ustedes", "yo"),
    ("ellos", "usted", "tú"),
]


def build_exercises_for_verb(verb, verb_index):
    """Generate 3 exercises for a given verb."""
    conj = get_subjunctive(verb)
    exercises = []

    # Pick 3 different triggers and subjects
    # Use verb_index to rotate through templates and subjects
    template_indices = [
        verb_index % len(EXERCISE_TEMPLATES),
        (verb_index * 3 + 1) % len(EXERCISE_TEMPLATES),
        (verb_index * 7 + 2) % len(EXERCISE_TEMPLATES),
    ]
    # Ensure all 3 are different
    seen = set()
    final_indices = []
    for idx in template_indices:
        while idx in seen:
            idx = (idx + 1) % len(EXERCISE_TEMPLATES)
        seen.add(idx)
        final_indices.append(idx)

    subject_sets = [
        ("tú", "él", "nosotros"),
        ("ella", "ellos", "yo"),
        ("usted", "ustedes", "tú"),
    ]

    for ex_num in range(3):
        tmpl = EXERCISE_TEMPLATES[final_indices[ex_num]]
        trigger = tmpl["trigger"]
        hint = tmpl["hint"]

        # Pick subject
        subject = subject_sets[ex_num][verb_index % 3]

        # Get conjugated form for this subject
        verb_form = conj[subject]

        # Pick complement
        comp_idx = (verb_index + ex_num) % len(tmpl["complements"])
        comp_template, comp_unaccented_raw = tmpl["complements"][comp_idx]

        # Build the full sentence
        sentence_body = comp_template.format(subj=subject, verb=verb_form)
        full_sentence = f"{trigger} {sentence_body}."

        # Build contexto — use the complement hint, not the infinitive verb,
        # so the prompt doesn't reveal the answer.
        contexto = f"{trigger}, {subject}, {comp_unaccented_raw} (subjuntivo)"

        # Build grupos - must be unaccented
        trigger_unaccented = strip_accents(trigger)
        verb_form_unaccented = strip_accents(verb_form)
        subject_unaccented = strip_accents(subject)

        # Complement unaccented
        comp_unaccented = strip_accents(comp_unaccented_raw)

        grupos = [
            [trigger_unaccented],
            [verb_form_unaccented],
            [subject_unaccented],
            [comp_unaccented],
        ]

        exercise = {
            "id": f"{verb}-subjuntivo-{ex_num}",
            "verbo": verb,
            "contexto": contexto,
            "respuesta": full_sentence,
            "pista": hint,
            "grupos": grupos,
        }
        exercises.append(exercise)

    return exercises


def validate_exercise(ex):
    """Validate that all grupo elements appear in the lowered, unaccented respuesta."""
    resp_clean = strip_accents(ex["respuesta"].lower().rstrip(".").rstrip())
    errors = []
    for grupo in ex["grupos"]:
        for element in grupo:
            if element.lower() not in resp_clean:
                errors.append(f"  '{element}' not found in '{resp_clean}'")
    return errors


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Generate all exercises
    all_exercises = []
    validation_errors = []

    for i, verb in enumerate(VERBS):
        exercises = build_exercises_for_verb(verb, i)
        for ex in exercises:
            errs = validate_exercise(ex)
            if errs:
                validation_errors.append((ex["id"], errs))
        all_exercises.extend(exercises)

    if validation_errors:
        print(f"VALIDATION ERRORS ({len(validation_errors)} exercises):")
        for eid, errs in validation_errors:
            print(f"  {eid}:")
            for e in errs:
                print(f"    {e}")
        print()

    print(f"Total exercises generated: {len(all_exercises)}")
    print(f"Total verbs: {len(VERBS)}")

    # Check for grupo accent violations
    accent_violations = 0
    for ex in all_exercises:
        for grupo in ex["grupos"]:
            for element in grupo:
                if element != strip_accents(element):
                    accent_violations += 1
                    print(f"ACCENT in grupo: '{element}' in {ex['id']}")

    print(f"Accent violations in grupos: {accent_violations}")

    # Split into 18 batches of ~15 verbs each (260 verbs / 18 = ~14.4)
    batch_size = 15  # verbs per batch
    num_batches = 18

    for batch_num in range(num_batches):
        start_verb = batch_num * batch_size
        if batch_num == num_batches - 1:
            # Last batch gets the remainder
            end_verb = len(VERBS)
        else:
            end_verb = start_verb + batch_size

        # Each verb has 3 exercises
        start_ex = start_verb * 3
        end_ex = end_verb * 3

        batch_exercises = all_exercises[start_ex:end_ex]
        batch_file = os.path.join(OUTPUT_DIR, f"batch_{batch_num:03d}.json")

        with open(batch_file, 'w', encoding='utf-8') as f:
            json.dump(batch_exercises, f, ensure_ascii=False, indent=2)

        print(f"Wrote {batch_file}: {len(batch_exercises)} exercises ({end_verb - start_verb} verbs)")


if __name__ == "__main__":
    main()
