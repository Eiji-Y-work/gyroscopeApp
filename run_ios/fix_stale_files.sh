#!/bin/bash

echo "=== Xcode Stale Files 修正スクリプト v1.0 ==="
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
echo "プロジェクトルート: $PROJECT_ROOT"

# 1. ビルド成果物の完全削除
echo "🧹 すべてのビルド成果物を削除しています..."
rm -rf "$PROJECT_ROOT/build"
rm -rf "$PROJECT_ROOT/ios/build"
rm -rf "$PROJECT_ROOT/ios/DerivedData"
rm -rf "$PROJECT_ROOT/ios/.symlinks"

# 2. プロジェクトファイルの徹底的なクリーニング
echo "🔍 プロジェクトファイルを修正しています..."
PBXPROJ="$PROJECT_ROOT/ios/Runner.xcodeproj/project.pbxproj"
if [ -f "$PBXPROJ" ]; then
  # バックアップ作成
  cp "$PBXPROJ" "${PBXPROJ}.bak"
  echo "✅ プロジェクトファイルのバックアップを作成しました: ${PBXPROJ}.bak"
  
  # すべての絶対パス参照を修正 (これがstale file警告の主な原因)
  sed -i.tmp 's|/Users/owner/Desktop/Flutter/Eiji/gyroscopeApp/build/ios/Debug-iphoneos|$(BUILT_PRODUCTS_DIR)|g' "$PBXPROJ"
  # ファイルパス参照を相対パスに修正
  sed -i.tmp 's|path = .*build/ios/Debug.*|path = "";|g' "$PBXPROJ"
  
  # 不要な一時ファイルを削除
  rm -f "${PBXPROJ}.tmp"
  echo "✅ プロジェクトファイルを修正しました"
fi

# 3. プロジェクト設定ファイルのクリーンアップ
echo "🧹 Xcodeのキャッシュファイルを削除しています..."
rm -rf "$PROJECT_ROOT/ios/Runner.xcodeproj/xcuserdata"
rm -rf "$PROJECT_ROOT/ios/Runner.xcworkspace/xcuserdata"
rm -rf "$HOME/Library/Developer/Xcode/DerivedData/Runner-*"

# 4. Flutterキャッシュと設定をリセット
echo "🔄 Flutterキャッシュをリセットしています..."
cd "$PROJECT_ROOT" && flutter clean
cd "$PROJECT_ROOT" && flutter pub get

# 5. iOSプロジェクトを再生成
echo "🔄 iOSプロジェクトを再生成しています..."
cd "$PROJECT_ROOT" && flutter create --platforms=ios .

# 6. CocoaPodsの完全リセット
echo "🔄 CocoaPodsを再インストールしています..."
cd "$PROJECT_ROOT/ios" && pod deintegrate || true
cd "$PROJECT_ROOT/ios" && pod cache clean --all
cd "$PROJECT_ROOT/ios" && pod install --repo-update

echo "✅ 修正が完了しました"
echo "ℹ️ 重要: Xcodeを完全に終了し、再起動してから再ビルドしてください"
exit 0
