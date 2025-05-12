#!/bin/bash

echo "=== Xcode プロジェクト完全リセットスクリプト v1.0 ==="

# プロジェクトのルートディレクトリを特定
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
echo "プロジェクトルート: $PROJECT_ROOT"

# 古いビルド成果物を完全に削除
echo "🧹 古いビルド成果物を削除しています..."
rm -rf "$PROJECT_ROOT/build"
rm -rf "$PROJECT_ROOT/ios/build"
rm -rf "$PROJECT_ROOT/ios/Runner.build"
rm -rf "$PROJECT_ROOT/ios/Pods"
rm -f "$PROJECT_ROOT/ios/Podfile.lock"
rm -f "$PROJECT_ROOT/ios/.symlinks"

# Xcodeのユーザー固有の設定を削除
echo "🧹 Xcodeの設定ファイルをクリーンアップしています..."
rm -rf "$PROJECT_ROOT/ios/Runner.xcodeproj/project.xcworkspace/xcuserdata"
rm -rf "$PROJECT_ROOT/ios/Runner.xcworkspace/xcuserdata"
rm -f "$PROJECT_ROOT/ios/Runner.xcodeproj/project.xcworkspace/xcshareddata/IDEWorkspaceChecks.plist"

# プロジェクトファイルのバックアップを作成
PBXPROJ="$PROJECT_ROOT/ios/Runner.xcodeproj/project.pbxproj"
if [ -f "$PBXPROJ" ]; then
  cp "$PBXPROJ" "${PBXPROJ}.bak"
  echo "✅ プロジェクトファイルのバックアップを作成しました"

  # プロジェクトファイルからStaleファイル参照を削除
  echo "🔧 プロジェクトファイルから古いパス参照を削除しています..."
  sed -i.tmp "s|path = .*build/ios/Debug.*|path = \"\";|g" "$PBXPROJ"
  sed -i.tmp "s|sourceTree = BUILT_PRODUCTS_DIR|sourceTree = DEVELOPER_DIR|g" "$PBXPROJ"
  rm -f "${PBXPROJ}.tmp"
fi

# DerivedDataディレクトリからプロジェクト関連のキャッシュを削除
echo "🧹 Xcodeのキャッシュを削除しています..."
DERIVED_DATA="$HOME/Library/Developer/Xcode/DerivedData"
if [ -d "$DERIVED_DATA" ]; then
  for dir in $(find "$DERIVED_DATA" -name "*Runner*" -o -name "*gyroscope*" -type d); do
    echo "削除: $dir"
    rm -rf "$dir"
  done
fi

# Xcodeのモジュールキャッシュをクリア
MODULE_CACHE="$HOME/Library/Developer/Xcode/DerivedData/ModuleCache.noindex"
if [ -d "$MODULE_CACHE" ]; then
  echo "モジュールキャッシュを削除しています..."
  # 全削除ではなく一部のみ削除
  find "$MODULE_CACHE" -type d -name "*Flutter*" -o -name "*Swift*" | xargs rm -rf
fi

# Flutter関連のキャッシュをクリア
echo "🧹 Flutterのキャッシュをクリアしています..."
cd "$PROJECT_ROOT" && flutter clean

# CocoaPodsをリセット
echo "🔄 CocoaPodsを再インストールしています..."
cd "$PROJECT_ROOT/ios" && pod deintegrate || true
cd "$PROJECT_ROOT/ios" && pod setup
cd "$PROJECT_ROOT/ios" && rm -f Podfile.lock && pod install --repo-update

echo "✅ Xcodeプロジェクトのリセットが完了しました"
echo "ℹ️ 次回のビルド前にXcodeを再起動することをお勧めします"
exit 0
