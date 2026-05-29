import AVFoundation

@Observable
final class SpeechService {
    private let synthesizer = AVSpeechSynthesizer()
    private(set) var isSpeaking = false
    private(set) var selectedVoice: AVSpeechSynthesisVoice?
    private(set) var availableVoices: [AVSpeechSynthesisVoice] = []
    private(set) var hasHighQualityVoice = false

    var rate: Float = 0.35
    var pitch: Float = 1.05

    private var delegate: SpeechDelegate?

    init() {
        delegate = SpeechDelegate(service: self)
        synthesizer.delegate = delegate
        selectBestVoice()
    }

    func selectBestVoice() {
        let allVoices = AVSpeechSynthesisVoice.speechVoices()
        availableVoices = allVoices.filter { $0.language.hasPrefix("es") }

        // Score voices by quality and locale preference
        var bestVoice: AVSpeechSynthesisVoice?
        var bestScore: Int = -1

        for voice in availableVoices {
            var score = 0

            // Quality preference
            switch voice.quality {
            case .premium: score += 30
            case .enhanced: score += 20
            case .default: score += 10
            @unknown default: score += 5
            }

            // Locale preference
            if voice.language.hasPrefix("es-ES") {
                score += 5
            } else if voice.language.hasPrefix("es-MX") {
                score += 3
            }

            if score > bestScore {
                bestScore = score
                bestVoice = voice
            }
        }

        selectedVoice = bestVoice ?? availableVoices.first
        hasHighQualityVoice = bestScore >= 20 // enhanced or premium
    }

    func setVoice(_ voice: AVSpeechSynthesisVoice) {
        selectedVoice = voice
    }

    func speak(_ text: String, rate: Float? = nil, completion: (() -> Void)? = nil) {
        synthesizer.stopSpeaking(at: .immediate)

        let utterance = AVSpeechUtterance(string: text)
        utterance.voice = selectedVoice
        utterance.rate = rate ?? self.rate
        utterance.pitchMultiplier = pitch
        utterance.volume = 1.0

        delegate?.onFinish = { [weak self] in
            self?.isSpeaking = false
            completion?()
        }

        isSpeaking = true
        synthesizer.speak(utterance)
    }

    func stop() {
        synthesizer.stopSpeaking(at: .immediate)
        isSpeaking = false
    }
}

private class SpeechDelegate: NSObject, AVSpeechSynthesizerDelegate {
    weak var service: SpeechService?
    var onFinish: (() -> Void)?

    init(service: SpeechService) {
        self.service = service
    }

    func speechSynthesizer(_ synthesizer: AVSpeechSynthesizer, didFinish utterance: AVSpeechUtterance) {
        Task { @MainActor in
            onFinish?()
            onFinish = nil
        }
    }
}
