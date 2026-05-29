import Speech
import AVFoundation

@Observable
final class RecognitionService {
    enum State {
        case idle
        case listening
        case processing
        case error(String)
    }

    private(set) var state: State = .idle
    private(set) var currentTranscription: String = ""
    private(set) var finalTranscription: String = ""

    private var recognizer: SFSpeechRecognizer?
    private var recognitionRequest: SFSpeechAudioBufferRecognitionRequest?
    private var recognitionTask: SFSpeechRecognitionTask?
    private let audioEngine = AVAudioEngine()

    var isListening: Bool {
        if case .listening = state { return true }
        return false
    }

    init() {
        recognizer = SFSpeechRecognizer(locale: Locale(identifier: "es-ES"))
    }

    func requestAuthorization() async -> Bool {
        await withCheckedContinuation { continuation in
            SFSpeechRecognizer.requestAuthorization { status in
                continuation.resume(returning: status == .authorized)
            }
        }
    }

    func startListening(onResult: @escaping (String, Bool) -> Void) throws {
        // Cancel any previous task
        stopListening()

        guard let recognizer, recognizer.isAvailable else {
            state = .error("Reconocimiento de voz no disponible.")
            return
        }

        // Configure audio session
        let audioSession = AVAudioSession.sharedInstance()
        try audioSession.setCategory(.record, mode: .measurement, options: .duckOthers)
        try audioSession.setActive(true, options: .notifyOthersOnDeactivation)

        recognitionRequest = SFSpeechAudioBufferRecognitionRequest()
        guard let recognitionRequest else { return }

        recognitionRequest.shouldReportPartialResults = true
        recognitionRequest.requiresOnDeviceRecognition = recognizer.supportsOnDeviceRecognition

        let inputNode = audioEngine.inputNode
        let recordingFormat = inputNode.outputFormat(forBus: 0)

        inputNode.installTap(onBus: 0, bufferSize: 1024, format: recordingFormat) { buffer, _ in
            recognitionRequest.append(buffer)
        }

        audioEngine.prepare()
        try audioEngine.start()

        state = .listening
        currentTranscription = "Escuchando..."

        recognitionTask = recognizer.recognitionTask(with: recognitionRequest) { [weak self] result, error in
            guard let self else { return }

            if let result {
                let text = result.bestTranscription.formattedString
                Task { @MainActor in
                    self.currentTranscription = text
                    if result.isFinal {
                        self.finalTranscription = text
                        self.state = .idle
                        onResult(text, true)
                    } else {
                        onResult(text, false)
                    }
                }
            }

            if let error {
                Task { @MainActor in
                    // Don't report cancellation as error
                    if (error as NSError).code != 216 { // cancelled
                        self.state = .error("Error: \(error.localizedDescription)")
                    }
                    self.stopAudioEngine()
                }
            }
        }
    }

    func stopListening() {
        recognitionTask?.cancel()
        recognitionTask = nil
        recognitionRequest?.endAudio()
        recognitionRequest = nil
        stopAudioEngine()
        if case .listening = state {
            state = .idle
        }
    }

    private func stopAudioEngine() {
        audioEngine.stop()
        audioEngine.inputNode.removeTap(onBus: 0)
        try? AVAudioSession.sharedInstance().setActive(false, options: .notifyOthersOnDeactivation)
    }
}
