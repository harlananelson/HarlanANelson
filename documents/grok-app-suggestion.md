Here's a **complete, single-document solution** with all the fixes we've discussed:

- Global state to prevent multiple overlapping recognition sessions
- Safe start/stop helpers that clean up before starting new actions
- Mic on/off toggle (with visual feedback)
- Live transcription display while listening
- Proper handling for hint buttons (stop listening before playing audio)
- Status messages and better error handling
- Protection against clicking "Escuchar y responder" multiple times or during other actions
- Recommended UI improvements

### Full Improved HTML Document (Replace or Merge with Your Current Page)

Copy the entire content below into a new file (or integrate the `<script>` and added HTML into your existing page). This version keeps your original ElevenLabs TTS and core logic while adding the robust fixes.

```html
<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Práctica oral de español</title>
  <style>
    body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
    button { padding: 10px 16px; margin: 5px; font-size: 16px; cursor: pointer; border: none; border-radius: 6px; }
    .primary { background: #007bff; color: white; }
    .danger { background: #dc3545; color: white; }
    .secondary { background: #6c757d; color: white; }
    #listening-status { font-weight: bold; min-height: 28px; margin: 10px 0; }
    #live-transcript { background: #f8f9fa; padding: 12px; border-radius: 6px; min-height: 80px; margin: 10px 0; border: 1px solid #ddd; white-space: pre-wrap; }
    .pulsing { animation: pulse 1.5s infinite; }
    @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.6; } }
    .mic-on { background: #dc3545 !important; }
  </style>
</head>
<body>
  <h1>Práctica oral de español</h1>
  <p>Practica hablando en español. La app lee la consigna y evalúa tus ideas clave (no la frase exacta).</p>

  <!-- Your existing controls (Voz Tema, tenses, etc.) go here -->

  <div id="consigna-section">
    <h2>Consigna actual</h2>
    <p id="consigna-text">Pulsa “Escuchar y responder” para comenzar.</p>
    <p>Estado: <span id="status-nuevo">nuevo</span> | Repaso: <span id="repaso">0</span></p>
  </div>

  <!-- Mic Toggle -->
  <div style="margin: 15px 0;">
    <button id="mic-toggle" class="secondary">🎤 Mic: OFF</button>
    <span id="mic-status" style="margin-left: 12px; font-weight: bold;">Listo</span>
  </div>

  <!-- Hint and Action Buttons -->
  <div>
    <button onclick="playHint('contexto')">Oír contexto</button>
    <button onclick="playHint('verbo')">Oír verbo</button>
    <button onclick="playHint('pista')">Oír pista</button>
    <button onclick="playHint('modelo')">Oír frase modelo</button>
    <button onclick="playHint('instrucciones')">Oír instrucciones</button>
    
    <button id="escuchar-btn" class="primary" onclick="toggleListen()">🎤 Escuchar y responder</button>
    
    <button onclick="nextExercise()">Siguiente</button>
    <button onclick="repeatExercise()">Repetir ejercicio</button>
  </div>

  <!-- Listening Status and Live Transcript -->
  <div id="listening-status"></div>
  <div id="live-transcript">Transcripción en vivo aparecerá aquí mientras hablas...</div>

  <!-- Your existing response / feedback area -->
  <div id="response-area">
    <h3>Respuesta detectada</h3>
    <p id="detected-response">Todavía no hay respuesta.</p>
    <div id="feedback"></div>
  </div>

  <!-- Stats -->
  <div>
    Correctas: <strong id="correctas">0</strong> | 
    Para repasar: <strong id="repasar">0</strong> | 
    En cola: <strong id="cola">0</strong>
  </div>

  <script>
    // ==================== GLOBAL STATE & HELPERS ====================
    let currentRecognition = null;
    let isRecognizing = false;
    let currentKeyIdeas = [];        // Store key ideas for current prompt (your logic)
    let finalTranscript = '';

    // Stop any active recognition safely
    function stopCurrentRecognition() {
      if (currentRecognition) {
        try {
          currentRecognition.stop();
        } catch (e) { console.warn("Stop error:", e); }
        currentRecognition = null;
      }
      isRecognizing = false;
      updateListeningUI(false);
    }

    // Update UI for listening state
    function updateListeningUI(listening) {
      const statusEl = document.getElementById('listening-status');
      const toggleBtn = document.getElementById('mic-toggle');
      
      if (listening) {
        statusEl.textContent = '🎤 Escuchando... habla ahora (pulsa el botón para parar)';
        statusEl.classList.add('pulsing');
        statusEl.style.color = '#28a745';
        toggleBtn.textContent = '⏹️ Detener micrófono';
        toggleBtn.classList.add('mic-on');
      } else {
        statusEl.textContent = '';
        statusEl.classList.remove('pulsing');
        toggleBtn.textContent = '🎤 Mic: OFF';
        toggleBtn.classList.remove('mic-on');
      }
    }

    // ==================== SPEECH RECOGNITION ====================
    function startListening() {
      stopCurrentRecognition(); // Clean up any previous session

      if (!('SpeechRecognition' in window || 'webkitSpeechRecognition' in window)) {
        alert("Tu navegador no soporta reconocimiento de voz. Usa Chrome o Edge en escritorio.");
        return;
      }

      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      currentRecognition = new SpeechRecognition();

      currentRecognition.lang = 'es-ES';
      currentRecognition.interimResults = true;
      currentRecognition.continuous = false;   // One utterance at a time works best for drills

      finalTranscript = '';

      currentRecognition.onresult = function(event) {
        let interim = '';
        for (let i = event.resultIndex; i < event.results.length; ++i) {
          const part = event.results[i][0].transcript;
          if (event.results[i].isFinal) {
            finalTranscript += part + ' ';
          } else {
            interim += part;
          }
        }
        document.getElementById('live-transcript').textContent = (finalTranscript + interim).trim();
      };

      currentRecognition.onerror = function(event) {
        console.error("Recognition error:", event.error);
        let msg = "Error en el micrófono.";
        if (event.error === 'no-speech') msg = "No se detectó habla. Inténtalo de nuevo.";
        document.getElementById('listening-status').textContent = msg;
        stopCurrentRecognition();
      };

      currentRecognition.onend = function() {
        isRecognizing = false;
        if (finalTranscript.trim()) {
          processUserResponse(finalTranscript.trim());   // ← Your existing evaluation function
        }
        stopCurrentRecognition();
      };

      try {
        currentRecognition.start();
        isRecognizing = true;
        updateListeningUI(true);
      } catch (err) {
        console.error("Start failed:", err);
        stopCurrentRecognition();
        alert("No se pudo activar el micrófono. Verifica permisos.");
      }
    }

    // Toggle function for main button and mic toggle
    function toggleListen() {
      if (isRecognizing) {
        stopCurrentRecognition();
      } else {
        // Load current prompt key ideas here if needed
        // currentKeyIdeas = getCurrentKeyIdeas();
        startListening();
      }
    }

    // ==================== MIC TOGGLE BUTTON ====================
    document.getElementById('mic-toggle').addEventListener('click', toggleListen);

    // ==================== HINT BUTTONS (ElevenLabs TTS) ====================
    function playHint(type) {
      stopCurrentRecognition();           // Critical: stop listening before speaking
      
      // speechSynthesis.cancel();        // If you also use browser TTS as fallback

      // Your existing ElevenLabs code here, for example:
      // speakWithElevenLabs(getTextForHint(type));
      
      console.log(`Reproduciendo hint: ${type}`); // Placeholder
      // After audio finishes, you can optionally restart listening if desired
    }

    // ==================== YOUR EXISTING FUNCTIONS ====================
    // Replace these placeholders with your real functions
    function processUserResponse(transcript) {
      document.getElementById('detected-response').textContent = transcript;
      
      // Your key-ideas matching logic here
      // const score = evaluateAgainstKeyIdeas(transcript, currentKeyIdeas);
      
      document.getElementById('feedback').innerHTML = `<p>✅ Respuesta procesada. Ideas clave detectadas.</p>`;
      // Update stats, etc.
      console.log("Processed response:", transcript);
    }

    function nextExercise() {
      stopCurrentRecognition();
      // Your logic to load next prompt
      document.getElementById('live-transcript').textContent = '';
      console.log("Next exercise");
    }

    function repeatExercise() {
      stopCurrentRecognition();
      console.log("Repeat exercise");
    }

    // Optional: Stop everything when page unloads
    window.addEventListener('beforeunload', stopCurrentRecognition);

    // Initial message
    console.log("✅ Spanish Speech Drill with robust mic handling loaded.");
  </script>
</body>
</html>
```

### How to Integrate
1. Replace placeholder functions (`processUserResponse`, `playHint`, `nextExercise`, etc.) with your actual code.
2. Keep your ElevenLabs TTS calls inside `playHint()` — just make sure to call `stopCurrentRecognition()` first.
3. If you have a separate JS file, move the script section there and keep the new HTML elements.

This version greatly reduces the chance of the app getting confused from multiple button presses. The global `stopCurrentRecognition()` call at the start of most actions is the key safeguard.

Test it thoroughly:
- Click "Escuchar y responder" multiple times quickly.
- Click hint buttons while listening.
- Use the mic toggle to manually stop/start.

Would you like me to adjust anything (e.g., make the toggle separate from the main button, add more visual polish, or handle browser TTS fallback)? Just let me know how it performs or share any remaining issues!