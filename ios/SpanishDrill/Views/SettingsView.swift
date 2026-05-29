import SwiftUI
import AVFoundation

struct SettingsView: View {
    @Bindable var speechService: SpeechService

    var body: some View {
        Form {
            Section("Velocidad de voz") {
                VStack(alignment: .leading) {
                    Text("Velocidad: \(speechService.rate, specifier: "%.2f")")
                        .font(.subheadline)
                    Slider(value: $speechService.rate, in: 0.1...0.6, step: 0.05)
                }

                VStack(alignment: .leading) {
                    Text("Tono: \(speechService.pitch, specifier: "%.2f")")
                        .font(.subheadline)
                    Slider(value: $speechService.pitch, in: 0.5...1.5, step: 0.05)
                }

                Button("Probar voz") {
                    speechService.speak("Hola, esta es una prueba de la voz seleccionada.")
                }
            }

            Section("Voz seleccionada") {
                if let voice = speechService.selectedVoice {
                    Text("\(voice.name) (\(voice.language))")
                        .font(.subheadline)
                }

                if !speechService.hasHighQualityVoice {
                    VStack(alignment: .leading, spacing: 4) {
                        Label("Descarga mejores voces", systemImage: "info.circle")
                            .font(.subheadline)
                            .foregroundStyle(.orange)
                        Text("Ve a Ajustes → Accesibilidad → Contenido hablado → Voces → Español para descargar voces Premium o Enhanced.")
                            .font(.caption)
                            .foregroundStyle(.secondary)
                    }
                }

                ForEach(speechService.availableVoices, id: \.identifier) { voice in
                    Button {
                        speechService.setVoice(voice)
                    } label: {
                        HStack {
                            VStack(alignment: .leading) {
                                Text(voice.name)
                                    .font(.subheadline)
                                Text("\(voice.language) — \(qualityLabel(voice.quality))")
                                    .font(.caption)
                                    .foregroundStyle(.secondary)
                            }
                            Spacer()
                            if voice.identifier == speechService.selectedVoice?.identifier {
                                Image(systemName: "checkmark")
                                    .foregroundStyle(.accentColor)
                            }
                        }
                    }
                    .foregroundStyle(.primary)
                }
            }
        }
        .navigationTitle("Ajustes")
    }

    private func qualityLabel(_ quality: AVSpeechSynthesisVoiceQuality) -> String {
        switch quality {
        case .premium: "Premium"
        case .enhanced: "Enhanced"
        case .default: "Default"
        @unknown default: "Unknown"
        }
    }
}
