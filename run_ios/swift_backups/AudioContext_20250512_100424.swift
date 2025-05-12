import AVFoundation

/// The input mode that's used to determine which `AVAudioSessionCategory` to use.
/// This allows different audio apps to properly coexist on a device.
@objc public enum AudioContextMode: Int {
    /// This is for playing audio like music, podcasts, etc.
    case ambient
    /// This is for audio that should play even when the iOS device is muted.
    case audioProcessing  // deprecated but kept for compatibility
    /// This is for playing back recorded audio.
    case spatialMultitrack
    /// This is for voice chat and VOIP apps.
    case voiceChat
}

/// Represents the setup of an audio context necessary to play sounds with
/// `AudioPlayer` instances.
@objc public class AudioContext: NSObject {
    
    /// Same as `new AudioContext(AudioContextMode.ambient)`
    @objc public static let ambient = AudioContext(AudioContextMode.ambient)
    
    /// Same as `new AudioContext(AudioContextMode.audioProcessing)`
    @objc public static let audioProcessing = AudioContext(AudioContextMode.audioProcessing)
    
    /// Same as `new AudioContext(AudioContextMode.spatialMultitrack)`
    @objc public static let spatialMultitrack = AudioContext(AudioContextMode.spatialMultitrack)
    
    /// Same as `new AudioContext(AudioContextMode.voiceChat)`
    @objc public static let voiceChat = AudioContext(AudioContextMode.voiceChat)
    
    /// The input mode of this `AudioContext` instance.
    @objc public let mode: AudioContextMode
    
    /// Allows public creation of `AudioContext` instances.
    @objc public init(_ mode: AudioContextMode) {
        self.mode = mode
    }
    
    /// 静的メソッド - 文字列からコンテキストを作成
    @objc public static func parse(_ contextStr: String?) -> AudioContext {
        if contextStr == "audioProcessing" {
            return AudioContext.audioProcessing
        } else if contextStr == "spatialMultitrack" {
            return AudioContext.spatialMultitrack
        } else if contextStr == "voiceChat" {
            return AudioContext.voiceChat
        } else {
            return AudioContext.ambient
        }
    }
    
    /// オーディオセッションを設定・アクティブ化
    @objc public func apply() {
        setup()
    }
    
    /// Activates the audio session with this context's settings
    @objc public func activateAudioSession() {
        setup()
    }
    
    /// Determines the appropriate `AVAudioSessionCategory` for this
    /// `AudioContext` based on its input mode.
    var category: AVAudioSession.Category? {
        switch mode {
        case .ambient:
            return .ambient
        case .audioProcessing:
            return .playback
        case .spatialMultitrack:
            return .playback
        case .voiceChat:
            return .playAndRecord
        }
    }
    
    /// Sets the category and activates the session.
    @objc public func setup() {
        if let category = category {
            do {
                try AVAudioSession.sharedInstance().setCategory(category)
                try AVAudioSession.sharedInstance().setActive(true)
            } catch {
                print("An error occured while setting up the audio context: \(error.localizedDescription)")
            }
        }
    }
}
