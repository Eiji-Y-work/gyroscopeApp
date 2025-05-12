#!/bin/bash

echo "=== iOS Swift パッケージ互換性修正スクリプト ==="
echo "実行環境: $(pwd)"

# パッケージキャッシュディレクトリを特定
PUB_CACHE_DIR="$HOME/.pub-cache/hosted/pub.dev"
echo "パッケージキャッシュ: $PUB_CACHE_DIR"

# audioplayers_darwinパッケージを検索
function find_audioplayers_darwin() {
  find "$PUB_CACHE_DIR" -maxdepth 1 -name "audioplayers_darwin-*" -type d 2>/dev/null
}

# メインの修正処理
function fix_audioplayer_swift() {
  PACKAGE_PATH="$1"
  CONTEXT_PATH="$PACKAGE_PATH/ios/Classes/AudioContext.swift"
  PLUGIN_PATH="$PACKAGE_PATH/ios/Classes/SwiftAudioplayersDarwinPlugin.swift"

  echo "処理対象: $PACKAGE_PATH"

  # AudioContext.swiftの修正
  if [ -f "$CONTEXT_PATH" ]; then
    echo "AudioContext.swiftを修正中..."
    mkdir -p "$PACKAGE_PATH/ios/Classes/backups"
    cp -f "$CONTEXT_PATH" "$PACKAGE_PATH/ios/Classes/backups/AudioContext.swift.bak.$(date +%s)"
    
    # AudioContextの完全置換
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
    echo "✅ AudioContext.swift の修正が完了"
  else
    echo "⚠️ AudioContext.swift が見つかりません: $CONTEXT_PATH"
  fi

  # SwiftAudioplayersDarwinPlugin.swiftの修正
  if [ -f "$PLUGIN_PATH" ]; then
    echo "SwiftAudioplayersDarwinPlugin.swift を確認中..."
    
    # バックアップ作成
    mkdir -p "$PACKAGE_PATH/ios/Classes/backups"
    cp -f "$PLUGIN_PATH" "$PACKAGE_PATH/ios/Classes/backups/SwiftAudioplayersDarwinPlugin.swift.bak.$(date +%s)"
    
    # ファイル内容確認
    PLUGIN_CONTENT=$(cat "$PLUGIN_PATH")
    
    # globalContext行の存在確認
    if grep -q "var globalContext" "$PLUGIN_PATH"; then
      echo "globalContext 行を検出しました"
      
      # 修正の必要があるか確認
      if grep -q "var globalContext = AudioContext(AudioContextMode.ambient)" "$PLUGIN_PATH"; then
        echo "✅ globalContext は既に正しく初期化されています - 修正不要"
      else 
        echo "⚠️ globalContext の初期化が不適切です - 修正を適用します"
        
        # 複数の修正パターンを試行
        # パターン1: AudioContext()のパターン
        sed -i.bak 's/globalContext\s*=\s*AudioContext()/globalContext = AudioContext(AudioContextMode.ambient)/g' "$PLUGIN_PATH"
        
        # パターン2: 任意のAudioContextイニシャライザを置換
        perl -i -pe 's/(var\s+globalContext\s*=\s*AudioContext\s*\([^)]*\))/var globalContext = AudioContext(AudioContextMode.ambient)/g' "$PLUGIN_PATH"
        
        echo "修正適用後の内容を確認中..."
        if grep -q "AudioContext(AudioContextMode.ambient)" "$PLUGIN_PATH"; then
          echo "✅ 修正に成功しました"
        else
          echo "⚠️ 修正の適用に失敗 - 緊急処置を実行します"
          
          # 行を特定して直接書き換え
          CONTEXT_LINE_NUM=$(grep -n "var globalContext" "$PLUGIN_PATH" | cut -d':' -f1)
          if [ -n "$CONTEXT_LINE_NUM" ]; then
            # 特定行の置換
            echo "globalContext を宣言している行番号: $CONTEXT_LINE_NUM"
            awk -v line="$CONTEXT_LINE_NUM" '{if(NR==line) print "  var globalContext = AudioContext(AudioContextMode.ambient)"; else print $0}' "$PLUGIN_PATH" > "${PLUGIN_PATH}.fixed"
            mv "${PLUGIN_PATH}.fixed" "$PLUGIN_PATH"
            echo "✅ awk による行置換で修正しました"
          else
            echo "⚠️ globalContext 行を特定できませんでした"
          fi
        fi
      fi
    else
      echo "⚠️ globalContext 行が見つかりません"
    fi

    # 最終確認
    if grep -q "var globalContext = AudioContext(AudioContextMode.ambient)" "$PLUGIN_PATH"; then
      echo "✅ 最終確認: SwiftAudioplayersDarwinPlugin.swift は正しく修正されています"
    else
      echo "⚠️ 最終確認: SwiftAudioplayersDarwinPlugin.swift の修正が不完全です"
    fi
  else
    echo "⚠️ SwiftAudioplayersDarwinPlugin.swift が見つかりません: $PLUGIN_PATH"
  fi
}

# 全てのaudioplayers_darwinバージョンを処理
PACKAGES=$(find_audioplayers_darwin)
if [ -z "$PACKAGES" ]; then
  echo "⚠️ audioplayers_darwinパッケージが見つかりません"
  exit 0
fi

echo "検出されたパッケージ:"
for PKG in $PACKAGES; do
  echo " - $PKG"
done

echo "====== 修正処理開始 ======"
for PKG in $PACKAGES; do
  fix_audioplayer_swift "$PKG"
  echo "-----------------------------------"
done

echo "✅ 全ての修正処理が完了しました"
echo "ビルドを続行してください"
exit 0
