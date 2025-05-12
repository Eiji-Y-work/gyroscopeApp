#!/bin/bash

echo "=== AudioPlayers プラグイン修復スクリプト v1.0 ==="
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
echo "プロジェクトルート: $PROJECT_ROOT"

# pubspec.lockをバックアップして削除（強制的に依存関係を再解決させる）
if [ -f "$PROJECT_ROOT/pubspec.lock" ]; then
  cp "$PROJECT_ROOT/pubspec.lock" "$PROJECT_ROOT/pubspec.lock.bak"
  rm "$PROJECT_ROOT/pubspec.lock"
  echo "✅ pubspec.lockをリセットしました"
fi

# AudioPlayerのポッドファイル修正
POD_DIR="$HOME/.pub-cache/hosted/pub.dev"
for audio_dir in $(find "$POD_DIR" -name "audioplayers_darwin*" -type d); do
  echo "🔧 処理中: $audio_dir"
  
  # Podspecファイルを修正
  PODSPEC_FILE=$(find "$audio_dir" -name "*.podspec" -type f)
  if [ -n "$PODSPEC_FILE" ]; then
    echo "  修正: $PODSPEC_FILE"
    sed -i.bak 's/s.pod_target_xcconfig.*=.*{.*"DEFINES_MODULE"/s.pod_target_xcconfig = { "DEFINES_MODULE"/g' "$PODSPEC_FILE"
    
    # iOS 12.0以上を要求するように
    sed -i.bak 's/s.platform[ ]*=[ ]*:ios.*/s.platform = :ios, "12.0"/g' "$PODSPEC_FILE"
    
    # 元のSwiftファイルを確認
    SWIFT_DIR="$audio_dir/ios/Classes"
    if [ -d "$SWIFT_DIR" ]; then
      echo "  Swiftファイルディレクトリ: $SWIFT_DIR"
      for swift_file in $(find "$SWIFT_DIR" -name "*.swift"); do
        base_name=$(basename "$swift_file")
        cp "$swift_file" "$swift_file.original"
        echo "  バックアップ: $swift_file → $swift_file.original"
      done
    fi
  fi
done

# プラグインの再インストール
echo "🔄 Flutterプラグインを再インストールしています..."
cd "$PROJECT_ROOT" && flutter pub cache repair
cd "$PROJECT_ROOT" && flutter clean
cd "$PROJECT_ROOT" && flutter pub get

# iOSビルドファイルの完全クリーンアップ
echo "🧹 iOSビルドファイルをクリーンアップしています..."
rm -rf "$PROJECT_ROOT/ios/Pods"
rm -rf "$PROJECT_ROOT/ios/.symlinks"
rm -f "$PROJECT_ROOT/ios/Podfile.lock"

# CocoaPodsの再インストール
echo "🔄 CocoaPodsを再インストールしています..."
cd "$PROJECT_ROOT/ios" && pod deintegrate || true
cd "$PROJECT_ROOT/ios" && pod install --repo-update

echo "✅ AudioPlayersプラグイン修復が完了しました"
exit 0
