#!/bin/bash

echo "=== audioplayers_darwin Swift修正スクリプト v2.0 ==="

# パッケージパス検索
SEARCH_DIR="$HOME/.pub-cache/hosted/pub.dev"
PACKAGE_DIRS=$(find "$SEARCH_DIR" -maxdepth 1 -name "audioplayers_darwin-*" -type d 2>/dev/null)

if [ -z "$PACKAGE_DIRS" ]; then
  echo "⚠️ audioplayers_darwinパッケージが見つかりません"
  exit 0
fi

for PACKAGE_PATH in $PACKAGE_DIRS; do
  echo "パッケージを処理中: $PACKAGE_PATH"
  CONTEXT_PATH="$PACKAGE_PATH/ios/Classes/AudioContext.swift"
  PLUGIN_PATH="$PACKAGE_PATH/ios/Classes/SwiftAudioplayersDarwinPlugin.swift"

  # バックアップディレクトリ作成
  mkdir -p "$PACKAGE_PATH/ios/Classes/backups"
  
  # AudioContext.swift 修正
  if [ -f "$CONTEXT_PATH" ]; then
    echo "AudioContext.swiftを修正..."
    cp -f "$CONTEXT_PATH" "$PACKAGE_PATH/ios/Classes/backups/AudioContext.swift.$(date +%s).bak"
    
    cat > "$CONTEXT_PATH" << 'EOF'
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
EOF
    echo "✅ AudioContext.swift の修正完了"
  else
    echo "⚠️ AudioContext.swift が見つかりません: $CONTEXT_PATH"
  fi

  # SwiftAudioplayersDarwinPlugin.swift の修正
  if [ -f "$PLUGIN_PATH" ]; then
    echo "SwiftAudioplayersDarwinPlugin.swift を修正中..."
    cp -f "$PLUGIN_PATH" "$PACKAGE_PATH/ios/Classes/backups/SwiftAudioplayersDarwinPlugin.swift.$(date +%s).bak"
    
    # ファイルの内容を取得
    PLUGIN_CONTENT=$(cat "$PLUGIN_PATH")

    # バグ修正 1: AudioContextの初期化
    PLUGIN_CONTENT=$(echo "$PLUGIN_CONTENT" | sed 's/var globalContext = AudioContext()/var globalContext = AudioContext(AudioContextMode.ambient)/g')
    
    # バグ修正 2: args: パラメータのエラー修正（行番号 99, 291, 374付近）
    PLUGIN_CONTENT=$(echo "$PLUGIN_CONTENT" | sed 's/AudioPlayer(playerId: playerId, args: args)/AudioPlayer(playerId: playerId)/g')
    PLUGIN_CONTENT=$(echo "$PLUGIN_CONTENT" | sed 's/AudioPlayer(playerId: currentPlayerId, args: args)/AudioPlayer(playerId: currentPlayerId)/g')
    PLUGIN_CONTENT=$(echo "$PLUGIN_CONTENT" | sed 's/onAudioplayer(player: globalPlayer)/onAudioplayer(player: globalPlayer)/g')

    # 変更をファイルに書き込み
    echo "$PLUGIN_CONTENT" > "$PLUGIN_PATH"
    
    echo "✅ SwiftAudioplayersDarwinPlugin.swift の修正完了"
  else
    echo "⚠️ SwiftAudioplayersDarwinPlugin.swift が見つかりません: $PLUGIN_PATH"
  fi
  
  echo "------------------------------------"
done

echo "✅ audioplayers_darwin パッケージの修正が完了しました"
exit 0
