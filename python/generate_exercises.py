#!/usr/bin/env python3
"""Generate Spanish speech drill exercises via Claude API.

Usage:
    python generate_exercises.py                    # all tenses
    python generate_exercises.py --tense presente   # single tense
    python generate_exercises.py --tense presente --batch 3  # single batch
    python generate_exercises.py --dry-run           # show what would be generated

Resume-safe: skips already-generated batch files on re-run.
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path

import anthropic

SCRIPT_DIR = Path(__file__).parent
PROMPTS_DIR = SCRIPT_DIR / "prompts"
OUTPUT_DIR = SCRIPT_DIR / "output"

# All 260 verbs from existing exercises
VERBS = [
    "abandonar","abrir","acabar","aceptar","acercar","acompañar","acordar","actuar",
    "admitir","aforar","agradecer","alcanzar","alegrar","alejar","amar","andar",
    "aparecer","apartar","apostar","apoyar","aprender","arreglar","asegurar","asesinar",
    "asustar","atacar","atrapar","averiguar","ayudar","bailar","bajar","bastar",
    "beber","besar","buscar","caer","callar","calmar","cambiar","caminar",
    "cantar","casar","cerrar","coger","comenzar","comer","cometer","compartir",
    "comprar","comprender","conducir","confiar","conocer","conseguir","considerar","construir",
    "contar","contestar","continuar","controlar","convertir","correr","cortar","costar",
    "crear","crecer","creer","cubrir","cuidar","cumplir","dar","deber",
    "decidir","decir","defender","dejar","demostrar","depender","desaparecer","desarrollar",
    "descubrir","desear","despedir","despertar","destruir","detener","devolver","dirigir",
    "disculpar","discutir","disfrutar","disparar","dormir","echar","elegir","empezar",
    "encantar","encontrar","enfrentar","engañar","enseñar","entender","enterar","entrar",
    "entregar","enviar","escapar","esconder","escribir","escuchar","esperar","estar",
    "estudiar","evitar","existir","explicar","formar","funcionar","ganar","golpear",
    "gritar","guardar","gustar","haber","hablar","hacer","hallar","huir",
    "imaginar","importar","incluir","informar","intentar","interesar","invitar","ir",
    "joder","jugar","jurar","leer","levantar","llamar","llegar","llevar",
    "llorar","lograr","luchar","mandar","manejar","mantener","marchar","matar",
    "mencionar","mentir","merecer","meter","mirar","molestar","morir","mostrar",
    "mover","nacer","necesitar","negar","observar","obtener","ocupar","ocurrir",
    "odiar","ofrecer","oír","olvidar","pagar","parar","parecer","partir",
    "pasar","pedir","pegar","pelear","pensar","perder","perdonar","permanecer",
    "permitir","pertenecer","pesar","poder","poner","preferir","preguntar","preocupar",
    "preparar","presentar","prestar","probar","producir","prometer","proteger","quedar",
    "querer","quitar","realizar","recibir","recoger","reconocer","recordar","recuperar",
    "referir","regresar","reír","repetir","representar","resolver","responder","resultar",
    "reunir","revisar","robar","romper","saber","sacar","salir","salvar",
    "seguir","señalar","sentar","sentir","ser","servir","significar","soler",
    "soltar","sonar","subir","suceder","sufrir","superar","suponer","temer",
    "tener","terminar","tirar","tocar","tomar","trabajar","traer","tranquilar",
    "tratar","unir","usar","utilizar","valer","vender","venir","ver",
    "viajar","vivir","volar","volver"
]

# Tenses and how many exercises per verb for each
TENSES = {
    # New tenses: 3 exercises per verb
    "presente": 3,
    "futuro": 3,
    "condicional": 3,
    "subjuntivo": 3,
    "subj_imperfecto": 3,
    "subj_pluscuam": 3,
    # Existing tenses: extra variety
    "puntual": 2,
    "habitual": 2,
    "fondo": 1,
    "anterior": 1,
}

BATCH_SIZE = 15  # verbs per API call


def load_prompt(tense: str) -> str:
    prompt_file = PROMPTS_DIR / f"{tense}.txt"
    if not prompt_file.exists():
        raise FileNotFoundError(f"Prompt template not found: {prompt_file}")
    return prompt_file.read_text()


def batch_verbs(verbs: list, size: int) -> list:
    return [verbs[i:i + size] for i in range(0, len(verbs), size)]


def generate_batch(client, tense: str, verb_batch: list, exercises_per_verb: int) -> list:
    """Call Claude API to generate exercises for a batch of verbs."""
    system_prompt = load_prompt(tense)
    verb_list = ", ".join(verb_batch)

    user_msg = f"""Generate {exercises_per_verb} exercise(s) per verb for these {len(verb_batch)} verbs:
{verb_list}

Return a single JSON array containing all exercises. Each exercise must have exactly these fields: id, verbo, contexto, respuesta, pista, grupos.

Remember:
- Use unaccented characters in ALL grupos elements
- Every grupo element must appear in the respuesta (after lowercasing and accent removal)
- The conjugated verb form must be its own grupo
- Use varied subjects and time phrases across exercises for the same verb
- Set id to "{'{verb}'}-{tense}-0" for now (IDs will be reassigned later)"""

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=8192,
        system=system_prompt,
        messages=[{"role": "user", "content": user_msg}],
    )

    # Extract JSON from response
    text = response.content[0].text.strip()
    # Handle cases where response is wrapped in markdown code blocks
    if text.startswith("```"):
        text = text.split("\n", 1)[1]  # remove first line
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()

    exercises = json.loads(text)

    # Basic validation
    for ex in exercises:
        required = {"id", "verbo", "contexto", "respuesta", "pista", "grupos"}
        missing = required - set(ex.keys())
        if missing:
            raise ValueError(f"Exercise missing fields {missing}: {ex.get('id', 'unknown')}")

    return exercises


def main():
    parser = argparse.ArgumentParser(description="Generate Spanish speech drill exercises")
    parser.add_argument("--tense", help="Generate only this tense")
    parser.add_argument("--batch", type=int, help="Generate only this batch number (0-indexed)")
    parser.add_argument("--dry-run", action="store_true", help="Show plan without generating")
    parser.add_argument("--batch-size", type=int, default=BATCH_SIZE)
    args = parser.parse_args()

    tenses = {args.tense: TENSES[args.tense]} if args.tense else TENSES
    batches = batch_verbs(VERBS, args.batch_size)
    total_batches = len(batches)

    if args.dry_run:
        for tense, per_verb in tenses.items():
            total_ex = len(VERBS) * per_verb
            print(f"{tense}: {total_ex} exercises ({total_batches} batches of ~{args.batch_size} verbs)")
        total = sum(len(VERBS) * pv for pv in tenses.values())
        print(f"\nTotal: {total} exercises, {total_batches * len(tenses)} API calls")
        return

    client = anthropic.Anthropic()
    total_generated = 0
    total_skipped = 0
    errors = []

    for tense, per_verb in tenses.items():
        tense_dir = OUTPUT_DIR / tense
        tense_dir.mkdir(parents=True, exist_ok=True)

        for batch_idx, verb_batch in enumerate(batches):
            if args.batch is not None and batch_idx != args.batch:
                continue

            batch_file = tense_dir / f"batch_{batch_idx:03d}.json"
            if batch_file.exists():
                existing = json.loads(batch_file.read_text())
                total_skipped += len(existing)
                print(f"  SKIP {tense} batch {batch_idx} ({len(existing)} exercises exist)")
                continue

            print(f"  GEN  {tense} batch {batch_idx}/{total_batches-1} ({len(verb_batch)} verbs)...", end=" ", flush=True)

            try:
                exercises = generate_batch(client, tense, verb_batch, per_verb)
                batch_file.write_text(json.dumps(exercises, ensure_ascii=False, indent=2))
                total_generated += len(exercises)
                print(f"OK ({len(exercises)} exercises)")
            except Exception as e:
                errors.append((tense, batch_idx, str(e)))
                print(f"ERROR: {e}")

            # Rate limiting: ~1 second between calls
            time.sleep(1.0)

    print(f"\nDone. Generated: {total_generated}, Skipped: {total_skipped}, Errors: {len(errors)}")
    if errors:
        print("\nErrors:")
        for tense, batch_idx, msg in errors:
            print(f"  {tense} batch {batch_idx}: {msg}")
        sys.exit(1)


if __name__ == "__main__":
    main()
