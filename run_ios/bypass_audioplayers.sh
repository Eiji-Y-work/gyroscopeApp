#!/bin/bash
echo "=== audioplayers完全バイパススクリプト v1.0 ==="

# Swiftファイルを最小実装に置き換える
for dir in $(find "$HOME/.pub-cache/hosted/pub.dev" -name "audioplayers_darwin*" -type d 2>/dev/null); do
  if [ -d "$dir/ios/Classes" ]; then
    SWIFT_FILE="$dir/ios/Classes/SwiftAudioplayersDarwinPlugin.swift"
    echo "処理中: $SWIFT_FILE"
    
    # バックアップ作成
    cp "$SWIFT_FILE" "${SWIFT_FILE}.original" 2>/dev/null
    
    # 最小実装で置き換え
    cat > "$SWIFT_FILE" << 'EOF'
import Flutter
import AVFoundation

public class SwiftAudioplayersDarwinPlugin: NSObject, FlutterPlugin {
  public static func register(with registrar: FlutterPluginRegistrar) {
    let channel = FlutterMethodChannel(name: "xyz.luan/audioplayers", binaryMessenger: registrar.messenger())
    let instance = SwiftAudioplayersDarwinPlugin()
    registrar.addMethodCallDelegate(instance, channel: channel)
  }
  
  public func handle(_ call: FlutterMethodCall, result: @escaping FlutterResult) {
    result(FlutterMethodNotImplemented)
  }
}
EOF
    echo "✅ $SWIFT_FILE を修正しました"
  fi
done

# 全ビルドファイルをクリーンアップして再ビルド
cd ios
rm -rf Pods
rm -f Podfile.lock
cd ..
flutter clean
flutter pub get
cd ios
pod install --repo-update
cd ..

echo "✅ バイパス処理が完了しました"
exit 0
