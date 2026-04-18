#!/usr/bin/env python3
"""Transform spanish-speech-drill.html into english-speech-drill.html.

Replaces the exercise data, definitions, constants, and UI text.
"""

import json
import re
from pathlib import Path

PROJECT = Path(__file__).parent.parent
HTML_FILE = PROJECT / "english-speech-drill.html"
EXERCISES_FILE = PROJECT / "python" / "output" / "english_exercises.json"
DEFINITIONS_FILE = PROJECT / "python" / "output" / "english_definitions.json"


def load_json(path):
    with open(path) as f:
        return json.load(f)


def format_exercises_js(exercises):
    """Format exercises as JavaScript array literal."""
    return json.dumps(exercises, indent=2, ensure_ascii=False)


def format_definitions_js(definitions):
    """Format definitions as JavaScript object literal."""
    lines = []
    for verb, defn in definitions.items():
        lines.append(f'  {verb}:"{defn}"')
    return "{\n" + ",\n".join(lines) + "\n}"


def main():
    exercises = load_json(EXERCISES_FILE)
    definitions = load_json(DEFINITIONS_FILE)

    with open(HTML_FILE, "r") as f:
        html = f.read()

    # ── 1. HTML meta and head ────────────────────────────────────────
    html = html.replace('lang="es"', 'lang="en"', 1)
    html = html.replace('<title>Práctica oral de español</title>',
                        '<title>English Speech Drill</title>', 1)

    # ── 2. UI text in body ───────────────────────────────────────────
    html = html.replace(
        '<h1>Práctica oral de español</h1>',
        '<h1>English Speech Drill</h1>', 1)
    html = html.replace(
        'La interacción principal es por voz: la app lee la consigna, escucha tu respuesta y la revisa por ideas clave, no por una sola frase exacta.',
        'The main interaction is by voice: the app reads the prompt, listens to your response, and checks it for key ideas — not a single exact phrase.', 1)
    html = html.replace(
        'aria-label="Configuración de voz">Voz</button>',
        'aria-label="Voice settings">Voice</button>', 1)
    html = html.replace(
        'aria-label="Cambiar tema">Tema</button>',
        'aria-label="Toggle theme">Theme</button>', 1)

    # Settings modal
    html = html.replace('<h2>Configuración de voz</h2>',
                        '<h2>Voice Settings</h2>', 1)
    html = html.replace(
        'Para voz de alta calidad, introduce tu clave de ElevenLabs. Se guarda solo en tu navegador (localStorage).',
        'For high-quality voice, enter your ElevenLabs key. Stored only in your browser (localStorage).', 1)
    html = html.replace(
        'API Key de ElevenLabs',
        'ElevenLabs API Key', 1)
    html = html.replace(
        'Busca voces en español en elevenlabs.io/voices',
        'Find English voices at elevenlabs.io/voices', 1)
    html = html.replace(
        'Usar ElevenLabs (desmarcar = voz del navegador)',
        'Use ElevenLabs (uncheck = browser voice)', 1)
    html = html.replace('>Cancelar</button>\n          <button class="btn primary" id="settingsSaveBtn">Guardar</button>',
                        '>Cancel</button>\n          <button class="btn primary" id="settingsSaveBtn">Save</button>', 1)

    # Tense filter pills — replace entire block
    old_pills = '''    <div class="tense-filter" id="tenseFilter">
      <button class="tense-pill active" data-tense="todos">Todos</button>
      <button class="tense-pill" data-tense="presente">Presente</button>
      <button class="tense-pill" data-tense="futuro">Futuro</button>
      <button class="tense-pill" data-tense="condicional">Condicional</button>
      <button class="tense-pill" data-tense="subjuntivo">Subjuntivo</button>
      <button class="tense-pill" data-tense="subj_imperfecto">Subj. imperfecto</button>
      <button class="tense-pill" data-tense="subj_pluscuam">Subj. pluscuam.</button>
      <button class="tense-pill" data-tense="puntual">Puntual</button>
      <button class="tense-pill" data-tense="habitual">Habitual</button>
      <button class="tense-pill" data-tense="fondo">Fondo</button>
      <button class="tense-pill" data-tense="anterior">Anterior</button>
    </div>'''
    new_pills = '''    <div class="tense-filter" id="tenseFilter">
      <button class="tense-pill active" data-tense="all">All</button>
      <button class="tense-pill" data-tense="simple_present">Simple Present</button>
      <button class="tense-pill" data-tense="present_continuous">Present Continuous</button>
      <button class="tense-pill" data-tense="simple_past">Simple Past</button>
      <button class="tense-pill" data-tense="past_continuous">Past Continuous</button>
      <button class="tense-pill" data-tense="present_perfect">Present Perfect</button>
      <button class="tense-pill" data-tense="past_perfect">Past Perfect</button>
      <button class="tense-pill" data-tense="simple_future">Simple Future</button>
      <button class="tense-pill" data-tense="future_continuous">Future Continuous</button>
      <button class="tense-pill" data-tense="conditional">Conditional</button>
      <button class="tense-pill" data-tense="used_to">Used To</button>
      <button class="tense-pill" data-tense="present_perfect_cont">Pres. Perfect Cont.</button>
      <button class="tense-pill" data-tense="past_perfect_cont">Past Perfect Cont.</button>
    </div>'''
    html = html.replace(old_pills, new_pills, 1)

    # Main UI labels
    html = html.replace('<h2>Consigna actual</h2>', '<h2>Current Exercise</h2>', 1)
    html = html.replace('>Estado: nuevo</span>', '>Status: new</span>', 1)
    html = html.replace('>Repaso: 0</span>', '>Review: 0</span>', 1)
    html = html.replace('>Micrófono: listo</span>', '>Mic: ready</span>', 1)

    # Buttons
    html = html.replace('>Oír contexto</button>', '>Hear context</button>', 1)
    html = html.replace('>Oír verbo</button>', '>Hear verb</button>', 1)
    html = html.replace('>Oír pista</button>', '>Hear hint</button>', 1)
    html = html.replace('>Decir respuesta</button>', '>Say answer</button>', 1)
    html = html.replace('>Escuchar y responder</button>', '>Listen & respond</button>', 1)
    html = html.replace('>Repetir ejercicio</button>', '>Repeat exercise</button>', 1)
    html = html.replace('>Oír frase modelo</button>', '>Hear model sentence</button>', 1)
    html = html.replace('>Oír instrucciones</button>', '>Hear instructions</button>', 1)
    html = html.replace('>Siguiente</button>', '>Next</button>', 1)

    # Response area
    html = html.replace('>Respuesta detectada</div>', '>Detected response</div>', 1)
    html = html.replace('>Todavía no hay respuesta.</div>', '>No response yet.</div>', 1)

    # Feedback
    html = html.replace(
        '>Pulsa "Escuchar y responder". La app leerá la consigna y después activará el micrófono.</div>',
        '>Press "Listen & respond". The app will read the prompt and then activate the mic.</div>', 1)

    # Stats
    html = html.replace('<span>Correctas</span>', '<span>Correct</span>', 1)
    html = html.replace('<span>Para repasar</span>', '<span>To review</span>', 1)
    html = html.replace('<span>En cola</span>', '<span>In queue</span>', 1)

    # Log section
    html = html.replace('<h2>Registro</h2>', '<h2>Log</h2>', 1)
    html = html.replace(
        'Cada intento se guarda y la app vuelve más tarde a lo que te cuesta decir.',
        'Each attempt is saved and the app returns later to what you find difficult.', 1)
    html = html.replace('>Leer resumen</button>', '>Read summary</button>', 1)
    html = html.replace('>Exportar</button>', '>Export</button>', 1)

    # ── 3. Replace exercise data ─────────────────────────────────────
    # Find the actividades array and replace it
    pattern = r'const actividades = \[.*?\n\];'
    replacement = f'const exercises = {format_exercises_js(exercises)};'
    html = re.sub(pattern, replacement, html, count=1, flags=re.DOTALL)

    # ── 4. Replace definitions ───────────────────────────────────────
    pattern = r'const definiciones = \{.*?\n\};'
    replacement = f'const definitions = {format_definitions_js(definitions)};'
    html = re.sub(pattern, replacement, html, count=1, flags=re.DOTALL)

    # ── 5. Replace JS constants and logic ────────────────────────────
    # TENSE_NAMES
    old_tense_names = '''const TENSE_NAMES = {
  presente:        'Presente',
  futuro:          'Futuro',
  condicional:     'Condicional',
  subjuntivo:      'Subjuntivo',
  subj_imperfecto: 'Subj. imperf.',
  subj_pluscuam:   'Subj. plusc.',
  puntual:         'Puntual',
  habitual:        'Habitual',
  fondo:           'Fondo',
  anterior:        'Anterior'
};'''
    new_tense_names = '''const TENSE_NAMES = {
  simple_present:       'Simple Present',
  present_continuous:   'Present Continuous',
  simple_past:          'Simple Past',
  past_continuous:      'Past Continuous',
  present_perfect:      'Present Perfect',
  past_perfect:         'Past Perfect',
  simple_future:        'Simple Future',
  future_continuous:    'Future Continuous',
  conditional:          'Conditional',
  used_to:              'Used To',
  present_perfect_cont: 'Pres. Perfect Cont.',
  past_perfect_cont:    'Past Perfect Cont.'
};'''
    html = html.replace(old_tense_names, new_tense_names, 1)

    # ALL_TENSES
    old_all = "const ALL_TENSES = ['presente','futuro','condicional','subjuntivo','subj_imperfecto','subj_pluscuam','puntual','habitual','fondo','anterior'];"
    new_all = "const ALL_TENSES = ['simple_present','present_continuous','simple_past','past_continuous','present_perfect','past_perfect','simple_future','future_continuous','conditional','used_to','present_perfect_cont','past_perfect_cont'];"
    html = html.replace(old_all, new_all, 1)

    # ── 6. Replace references to actividades → exercises, definiciones → definitions ──
    html = html.replace('actividades.find(', 'exercises.find(', )
    html = html.replace('definiciones[', 'definitions[', )
    # actividadesFiltradas function
    html = html.replace(
        'function actividadesFiltradas(){',
        'function filteredExercises(){', 1)
    html = html.replace(
        'return actividades.filter(',
        'return exercises.filter(', 1)
    html = html.replace(
        'return actividades;',
        'return exercises;', 1)
    html = html.replace(
        'const pool = actividadesFiltradas();',
        'const pool = filteredExercises();', 1)

    # ── 7. Replace speech recognition language ───────────────────────
    html = html.replace("reconocimiento.lang = 'es-ES'", "reconocimiento.lang = 'en-US'", 1)

    # ── 8. Replace TTS language ──────────────────────────────────────
    html = html.replace("u.lang = 'es-ES'", "u.lang = 'en-US'")

    # Browser voice selection: es → en
    html = html.replace("/^es[-_]/i.test(v.lang)", "/^en[-_]/i.test(v.lang)")
    html = html.replace("/es[-_]ES/i.test(v.lang)", "/en[-_]US/i.test(v.lang)")
    html = html.replace("/es[-_]MX/i.test(v.lang)", "/en[-_]GB/i.test(v.lang)")

    # ── 9. Replace 'todos' with 'all' in filter logic ────────────────
    html = html.replace("tense === 'todos'", "tense === 'all'")
    html = html.replace("data-tense=\"todos\"", "data-tense=\"all\"")

    # ── 10. Replace Spanish UI strings in JS ─────────────────────────
    # Speech recognition UI
    html = html.replace("'Escuchando...'", "'Listening...'")
    html = html.replace("'Micrófono: escuchando'", "'Mic: listening'")
    html = html.replace("'Escuchando'", "'Listening'")
    html = html.replace("'Todavía no hay respuesta.'", "'No response yet.'")
    html = html.replace("'Micrófono: listo'", "'Mic: ready'")

    # Feedback strings
    html = html.replace(
        "'Escucha el ejercicio y responde en voz alta cuando termine.'",
        "'Listen to the exercise and respond out loud when it finishes.'")
    html = html.replace(
        "'Di tu respuesta ahora. La aplicación la revisará al terminar.'",
        "'Say your answer now. The app will check it when you finish.'")
    html = html.replace(
        "'No se detectó ninguna respuesta.'",
        "'No response was detected.'")

    # Status
    html = html.replace("'Estado: repaso'", "'Status: review'")
    html = html.replace("'Estado: nuevo'", "'Status: new'")

    # Labels
    html = html.replace("`Repaso: ${", "`Review: ${")
    html = html.replace("`Verbo: ${", "`Verb: ${")
    html = html.replace("`Contexto: ${", "`Context: ${")
    html = html.replace("`Pista: ${", "`Hint: ${")

    # Feedback
    html = html.replace(
        "'Pulsa \"Escuchar y responder\". La app leerá la consigna y después activará el micrófono.'",
        "'Press \"Listen & respond\". The app will read the prompt and then activate the mic.'")
    html = html.replace(
        "'No hay ejercicios para los filtros seleccionados.'",
        "'No exercises match the selected filters.'")

    # Review feedback
    html = html.replace("'Correcto.'", "'Correct.'")
    html = html.replace("`Correcto. ${", "`Correct. ${")
    html = html.replace("'Revisa esta idea.'", "'Review this.'")
    html = html.replace("`Revisa esta idea. ${", "`Review this. ${")
    html = html.replace(
        "'Pulsa \"Siguiente\" para continuar.'",
        "'Press \"Next\" to continue.'")
    html = html.replace(
        "' Inténtalo otra vez con el mismo ejercicio.'",
        "' Try again with the same exercise.'")

    # Log entries
    html = html.replace("'correcta'", "'correct'")
    html = html.replace("'revisar'", "'review'")
    html = html.replace("'repaso'", "'review'")
    html = html.replace("Tu voz:", "Your voice:")
    html = html.replace("Modelo:", "Model:")
    html = html.replace("Ideas clave:", "Key ideas:")
    html = html.replace("Observación:", "Note:")

    # Summary
    html = html.replace(
        "`Correctas: ${conteo.correctas}. Para repasar: ${conteo.incorrectas}. En cola: ${colaRepaso.length}. Más difíciles: ${top}.`",
        "`Correct: ${conteo.correctas}. To review: ${conteo.incorrectas}. In queue: ${colaRepaso.length}. Hardest: ${top}.`")
    html = html.replace(
        "'Todavía no hay errores repetidos.'",
        "'No repeated errors yet.'")

    # Export filename
    html = html.replace(
        "'registro-practica-espanol.json'",
        "'practice-log-english.json'")

    # Instructions text
    html = html.replace(
        "'Escucha el ejercicio. Después responde con una sola oración completa en español. La aplicación escuchará tu respuesta y la revisará automáticamente.'",
        "'Listen to the exercise. Then respond with one complete sentence in English. The app will listen to your response and check it automatically.'")

    # Speech recognition error
    html = html.replace(
        "'<span class=\"bad\">El reconocimiento de voz no está disponible en este navegador.</span> Chrome o Edge suelen funcionar mejor.'",
        "'<span class=\"bad\">Speech recognition is not available in this browser.</span> Chrome or Edge usually work best.'")

    # Voice pill
    html = html.replace("'Voz: ElevenLabs'", "'Voice: ElevenLabs'")
    html = html.replace("'Voz: navegador'", "'Voice: browser'")

    # ── 11. Replace feedbackPorTiempo ────────────────────────────────
    old_feedback = '''function feedbackPorTiempo(tense, item, u){
  const notas = [];
  switch(tense){
    case 'puntual':
      notas.push('Recuerda usar el pretérito indefinido: una acción acabada en un momento concreto.');
      break;
    case 'habitual':
      if (!/(aba|aban|abamos|abas|ia|ian|iamos|ias)/.test(u)) notas.push('Piensa en una costumbre pasada: usa el imperfecto.');
      break;
    case 'fondo':
      if (!/(aba|aban|abamos|abas|ia|ian|iamos|ias|era|eran)/.test(u)) notas.push('La frase describe un fondo o estado: usa el imperfecto.');
      break;
    case 'anterior':
      if (!/(habia|habias|habiamos|habian)/.test(u)) notas.push('Fíjate en la secuencia temporal: algo pasó antes de otra cosa. Necesitas había + participio.');
      break;
    case 'presente':
      notas.push('Recuerda conjugar en presente indicativo.');
      break;
    case 'futuro':
      if (!/...(re|ras|ra|remos|reis|ran)$/.test(u.split(' ').find(w => w.length > 4) || '')) notas.push('Conjuga en futuro simple: infinitivo + -é, -ás, -á, -emos, -éis, -án.');
      break;
    case 'condicional':
      notas.push('Conjuga en condicional: infinitivo + -ía, -ías, -ía, -íamos, -íais, -ían.');
      break;
    case 'subjuntivo':
      if (!/(espero que|quiero que|es necesario|ojalá|dudo que|es posible|para que|antes de que)/.test(u)) notas.push('No olvides la frase que activa el subjuntivo (espero que, quiero que, etc.).');
      notas.push('Recuerda: -ar → -e, -er/-ir → -a en el presente de subjuntivo.');
      break;
    case 'subj_imperfecto':
      notas.push('Usa la forma -ra o -se del imperfecto de subjuntivo.');
      break;
    case 'subj_pluscuam':
      if (!/(hubiera|hubiese|hubieras|hubieses|hubieramos|hubiesemos|hubieran|hubiesen)/.test(u)) notas.push('Necesitas hubiera/hubiese + participio pasado.');
      break;
  }
  return notas;
}'''
    new_feedback = r'''function feedbackPorTiempo(tense, item, u){
  const notas = [];
  switch(tense){
    case 'simple_present':
      if (/\b(is|are|am)\s+\w+ing\b/.test(u)) notas.push('You used the continuous form. This exercise needs the simple present (e.g., "walks", "plays").');
      else notas.push('Remember: add -s/-es for he/she/it in the simple present.');
      break;
    case 'present_continuous':
      if (!/\b(is|are|am)\s+\w+ing\b/.test(u)) notas.push('Use am/is/are + verb-ing for the present continuous.');
      break;
    case 'simple_past':
      if (/\b(was|were)\s+\w+ing\b/.test(u)) notas.push('You used the past continuous. This needs the simple past (e.g., "walked", "went").');
      else notas.push('Use the past form: regular verbs add -ed; check irregular forms.');
      break;
    case 'past_continuous':
      if (!/\b(was|were)\s+\w+ing\b/.test(u)) notas.push('Use was/were + verb-ing for the past continuous.');
      break;
    case 'present_perfect':
      if (!/\b(have|has)\s+/.test(u)) notas.push('Use have/has + past participle for the present perfect.');
      break;
    case 'past_perfect':
      if (!/\bhad\s+/.test(u)) notas.push('Use had + past participle for the past perfect.');
      break;
    case 'simple_future':
      if (!/\b(will|going to)\b/.test(u)) notas.push('Use "will" or "going to" + base form for the future.');
      break;
    case 'future_continuous':
      if (!/\bwill be\s+\w+ing\b/.test(u)) notas.push('Use will be + verb-ing for the future continuous.');
      break;
    case 'conditional':
      if (!/\bwould\b/.test(u)) notas.push('Use "would" + base form for the conditional.');
      break;
    case 'used_to':
      if (!/\bused to\b/.test(u)) notas.push('Use "used to" + base form for past habits.');
      break;
    case 'present_perfect_cont':
      if (!/\b(have|has) been\s+\w+ing\b/.test(u)) notas.push('Use have/has been + verb-ing for the present perfect continuous.');
      break;
    case 'past_perfect_cont':
      if (!/\bhad been\s+\w+ing\b/.test(u)) notas.push('Use had been + verb-ing for the past perfect continuous.');
      break;
  }
  return notas;
}'''
    html = html.replace(old_feedback, new_feedback, 1)

    # ── 12. Replace TENSE_DESCRIPTIONS ───────────────────────────────
    old_descs = '''const TENSE_DESCRIPTIONS = {
  presente: {nombre:'Presente de indicativo', regla:'Acciones actuales, habituales o verdades generales.', conjugacion:'-ar: -o, -as, -a, -amos, -áis, -an | -er: -o, -es, -e, -emos, -éis, -en | -ir: -o, -es, -e, -imos, -ís, -en'},
  futuro: {nombre:'Futuro simple', regla:'Acciones que ocurrirán. También predicciones y probabilidad.', conjugacion:'infinitivo + -é, -ás, -á, -emos, -éis, -án. Irregulares: tendr-, pondr-, saldr-, vendr-, podr-, sabr-, querr-, har-, dir-, valdr-'},
  condicional: {nombre:'Condicional', regla:'Hipótesis, cortesía, consejo. "¿Qué harías si…?"', conjugacion:'infinitivo + -ía, -ías, -ía, -íamos, -íais, -ían. Mismos irregulares que el futuro.'},
  subjuntivo: {nombre:'Presente de subjuntivo', regla:'Deseos, dudas, emociones, necesidad. Aparece tras "que".', conjugacion:'-ar → -e, -es, -e, -emos, -éis, -en | -er/-ir → -a, -as, -a, -amos, -áis, -an'},
  subj_imperfecto: {nombre:'Imperfecto de subjuntivo', regla:'Hipótesis pasadas, cláusulas con "si", deseos irreales.', conjugacion:'raíz del pretérito + -ra/-se, -ras/-ses, -ra/-se, -ramos/-semos, -rais/-seis, -ran/-sen'},
  subj_pluscuam: {nombre:'Pluscuamperfecto de subjuntivo', regla:'Acciones pasadas no realizadas. "Si hubiera sabido…"', conjugacion:'hubiera/hubiese + participio (-ado/-ido). Irregulares: hecho, dicho, puesto, visto, escrito, abierto, vuelto, roto, muerto'},
  puntual: {nombre:'Pretérito indefinido', regla:'Acción terminada en un momento concreto del pasado.', conjugacion:'-ar: -é, -aste, -ó, -amos, -asteis, -aron | -er/-ir: -í, -iste, -ió, -imos, -isteis, -ieron'},
  habitual: {nombre:'Pretérito imperfecto (habitual)', regla:'Acción repetida o costumbre en el pasado.', conjugacion:'-ar: -aba, -abas, -aba, -ábamos, -abais, -aban | -er/-ir: -ía, -ías, -ía, -íamos, -íais, -ían'},
  fondo: {nombre:'Pretérito imperfecto (fondo)', regla:'Describe estados, escenas o circunstancias de fondo en el pasado.', conjugacion:'Mismas terminaciones que habitual. Solo 3 irregulares: era (ser), iba (ir), veía (ver).'},
  anterior: {nombre:'Pretérito pluscuamperfecto', regla:'Acción pasada anterior a otra acción pasada. "Ya había comido cuando llegó."', conjugacion:'había/habías/había/habíamos/habíais/habían + participio (-ado/-ido)'}
};'''
    new_descs = '''const TENSE_DESCRIPTIONS = {
  simple_present: {nombre:'Simple Present', regla:'Habitual actions, general truths, schedules. "She walks to school every day."', conjugacion:'Base form; add -s/-es for he/she/it. Irregular: am/is/are, have/has, do/does'},
  present_continuous: {nombre:'Present Continuous', regla:'Actions happening right now or temporary situations. "She is walking to school."', conjugacion:'am/is/are + verb-ing. Drop silent -e (make→making), double final consonant (run→running)'},
  simple_past: {nombre:'Simple Past', regla:'Completed actions at a specific past time. "She walked to school yesterday."', conjugacion:'Regular: +ed. Irregular: went, saw, took, made, came, knew, thought, got, said, gave'},
  past_continuous: {nombre:'Past Continuous', regla:'Actions in progress at a past time, or background for another event. "She was walking when it rained."', conjugacion:'was/were + verb-ing.'},
  present_perfect: {nombre:'Present Perfect', regla:'Past actions connected to the present: experience, recent events. "She has walked there many times."', conjugacion:'have/has + past participle. Regular: -ed. Irregular: gone, seen, taken, made, done, been'},
  past_perfect: {nombre:'Past Perfect', regla:'An action completed before another past action. "She had already left when he arrived."', conjugacion:'had + past participle.'},
  simple_future: {nombre:'Simple Future', regla:'Predictions, promises, spontaneous decisions. "She will walk to school tomorrow."', conjugacion:'will + base form. Also: am/is/are going to + base form.'},
  future_continuous: {nombre:'Future Continuous', regla:'Actions in progress at a future time. "She will be walking at 8am."', conjugacion:'will be + verb-ing.'},
  conditional: {nombre:'Conditional', regla:'Hypothetical situations, polite requests. "She would walk if it were sunny."', conjugacion:'would + base form. Also: could, might for possibility.'},
  used_to: {nombre:'Used To (Habitual Past)', regla:'Past habits no longer true. "She used to walk to school."', conjugacion:"used to + base form. Negative: didn't use to. Question: Did you use to...?"},
  present_perfect_cont: {nombre:'Present Perfect Continuous', regla:'Actions from past to present, emphasizing duration. "She has been walking for an hour."', conjugacion:'have/has been + verb-ing.'},
  past_perfect_cont: {nombre:'Past Perfect Continuous', regla:'Ongoing action before another past event. "She had been walking for an hour when it rained."', conjugacion:'had been + verb-ing.'}
};'''
    html = html.replace(old_descs, new_descs, 1)

    # ── 13. Replace text normalization with English contraction expansion ──
    old_normalize = '''function convertirHoraYNumeroBasico(t){'''
    # Find and replace the whole function block — use regex
    pattern = r'function convertirHoraYNumeroBasico\(t\)\{.*?\n\}'
    match = re.search(pattern, html, re.DOTALL)
    if match:
        new_normalize = '''function expandContractions(t){
  return t
    .replace(/\\bi'm\\b/gi, 'i am')
    .replace(/\\bhe's\\b/gi, 'he is')
    .replace(/\\bshe's\\b/gi, 'she is')
    .replace(/\\bit's\\b/gi, 'it is')
    .replace(/\\bwe're\\b/gi, 'we are')
    .replace(/\\bthey're\\b/gi, 'they are')
    .replace(/\\byou're\\b/gi, 'you are')
    .replace(/\\bdon't\\b/gi, 'do not')
    .replace(/\\bdoesn't\\b/gi, 'does not')
    .replace(/\\bdidn't\\b/gi, 'did not')
    .replace(/\\bwon't\\b/gi, 'will not')
    .replace(/\\bcan't\\b/gi, 'cannot')
    .replace(/\\bcouldn't\\b/gi, 'could not')
    .replace(/\\bwouldn't\\b/gi, 'would not')
    .replace(/\\bshouldn't\\b/gi, 'should not')
    .replace(/\\bhaven't\\b/gi, 'have not')
    .replace(/\\bhasn't\\b/gi, 'has not')
    .replace(/\\bhadn't\\b/gi, 'had not')
    .replace(/\\bisn't\\b/gi, 'is not')
    .replace(/\\baren't\\b/gi, 'are not')
    .replace(/\\bwasn't\\b/gi, 'was not')
    .replace(/\\bweren't\\b/gi, 'were not')
    .replace(/\\bi've\\b/gi, 'i have')
    .replace(/\\bwe've\\b/gi, 'we have')
    .replace(/\\bthey've\\b/gi, 'they have')
    .replace(/\\byou've\\b/gi, 'you have')
    .replace(/\\bi'd\\b/gi, 'i would')
    .replace(/\\bhe'd\\b/gi, 'he would')
    .replace(/\\bshe'd\\b/gi, 'she would')
    .replace(/\\bwe'd\\b/gi, 'we would')
    .replace(/\\bthey'd\\b/gi, 'they would')
    .replace(/\\bi'll\\b/gi, 'i will')
    .replace(/\\bhe'll\\b/gi, 'he will')
    .replace(/\\bshe'll\\b/gi, 'she will')
    .replace(/\\bwe'll\\b/gi, 'we will')
    .replace(/\\bthey'll\\b/gi, 'they will')
    .replace(/\\byou'll\\b/gi, 'you will');
}'''
        html = html[:match.start()] + new_normalize + html[match.end():]

    # Replace references to convertirHoraYNumeroBasico
    html = html.replace('convertirHoraYNumeroBasico(', 'expandContractions(')

    # Replace quitarExtrasComunes with simpler English version
    pattern = r'function quitarExtrasComunes\(t\)\{.*?\n\}'
    match = re.search(pattern, html, re.DOTALL)
    if match:
        new_extras = '''function removeCommonExtras(t){
  return t.replace(/\\s+/g, ' ').trim();
}'''
        html = html[:match.start()] + new_extras + html[match.end():]

    html = html.replace('quitarExtrasComunes(', 'removeCommonExtras(')

    # ── 14. Replace faltan/notas messages in analizar ────────────────
    html = html.replace(
        "`Faltan ${faltan.length} idea(s) clave de ${grupos.length}.`",
        "`Missing ${faltan.length} key idea(s) out of ${grupos.length}.`")

    # ── 15. Fix export ───────────────────────────────────────────────
    html = html.replace('{conteo, debiles, registro}', '{conteo, debiles, registro}')  # keep var names

    with open(HTML_FILE, "w") as f:
        f.write(html)

    print(f"Transformed {HTML_FILE}")
    print(f"  - Replaced exercise data ({len(exercises)} exercises)")
    print(f"  - Replaced definitions ({len(definitions)} verbs)")
    print(f"  - Updated UI text to English")
    print(f"  - Updated tense system (12 English tenses)")


if __name__ == "__main__":
    main()
