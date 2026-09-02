import Speech
import AVFoundation

/// Apple on-device speech (Neural Engine). `requiresOnDeviceRecognition` so a
/// dropped hotspot does not stop transcription. One recognition task is short
/// (Apple caps ~1 min); we restart the task on the same mic tap so a CRS
/// podcast can run for the whole hour.
final class OnDeviceASR {
    private var recognizer: SFSpeechRecognizer?
    private var request: SFSpeechAudioBufferRecognitionRequest?
    private var task: SFSpeechRecognitionTask?
    private let engine = AVAudioEngine()
    private var running = false
    private var localeId = "en-US"
    private var sessionName = "transcript"
    private var onEvent: (([String: Any]) -> Void)?

    func authorize() async -> Bool {
        await withCheckedContinuation { cont in
            SFSpeechRecognizer.requestAuthorization { status in
                cont.resume(returning: status == .authorized)
            }
        }
    }

    func start(locale: String, session: String,
               onEvent: @escaping ([String: Any]) -> Void) throws {
        stop()
        self.localeId = locale.hasPrefix("es") ? "es-ES"
            : (locale.hasPrefix("en") ? "en-US" : locale)
        self.sessionName = session
        self.onEvent = { ev in
            DispatchQueue.main.async { onEvent(ev) }
        }
        recognizer = SFSpeechRecognizer(locale: Locale(identifier: localeId))
        guard let recognizer else { throw ASRError.unavailable }

        let audio = AVAudioSession.sharedInstance()
        try audio.setCategory(.playAndRecord, mode: .measurement,
                              options: [.defaultToSpeaker])
        try audio.setActive(true)

        let input = engine.inputNode
        let fmt = input.outputFormat(forBus: 0)
        input.removeTap(onBus: 0)
        input.installTap(onBus: 0, bufferSize: 1024, format: fmt) { [weak self] buffer, _ in
            self?.request?.append(buffer)
        }
        engine.prepare()
        try engine.start()
        running = true
        try startTask()
    }

    private func startTask() throws {
        guard running, let recognizer else { return }
        request = SFSpeechAudioBufferRecognitionRequest()
        request?.shouldReportPartialResults = true
        request?.requiresOnDeviceRecognition = recognizer.supportsOnDeviceRecognition
        request?.addsPunctuation = true
        task = recognizer.recognitionTask(with: request!) { [weak self] result, error in
            guard let self, self.running else { return }
            if let result {
                let text = result.bestTranscription.formattedString
                if result.isFinal {
                    self.onEvent?(["type": "final", "text": text, "session": self.sessionName])
                    self.recycleTask()
                } else {
                    self.onEvent?(["type": "partial", "text": text])
                }
                return
            }
            if error != nil {
                self.recycleTask()
            }
        }
    }

    private func recycleTask() {
        task?.cancel()
        task = nil
        request?.endAudio()
        request = nil
        guard running else { return }
        try? startTask()
    }

    func stop() {
        running = false
        task?.cancel()
        task = nil
        request?.endAudio()
        request = nil
        if engine.isRunning { engine.stop() }
        engine.inputNode.removeTap(onBus: 0)
        try? AVAudioSession.sharedInstance()
            .setActive(false, options: .notifyOthersOnDeactivation)
        onEvent = nil
    }

    enum ASRError: LocalizedError {
        case unavailable
        var errorDescription: String? { "On-device speech recognizer unavailable" }
    }
}
