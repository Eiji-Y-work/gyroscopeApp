#!/bin/bash

echo "=== Xcode Stale Files 徹底修正ツール v3.0 ==="
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
echo "プロジェクトルート: $PROJECT_ROOT"

# 問題のパターン
STALE_PATH_BASE="/Users/owner/Desktop/Flutter/Eiji/gyroscopeApp/build/ios"
PBXPROJ="$PROJECT_ROOT/ios/Runner.xcodeproj/project.pbxproj"

if [ -f "$PBXPROJ" ]; then
  echo "🔍 プロジェクトファイルを詳細に検査しています..."
  cp "$PBXPROJ" "${PBXPROJ}.fullbackup"
  
  # すべてのバックアップファイルを探して削除（.bakと.original）
  echo "🧹 すべてのバックアップファイルを削除しています..."
  find "$PROJECT_ROOT/.pub-cache" -name "*.bak" -o -name "*.original" -type f -delete 2>/dev/null || true
  find "$HOME/.pub-cache" -name "*.bak" -o -name "*.original" -type f -delete 2>/dev/null || true
  
  # プロジェクト内のすべての参照パスをBUILT_PRODUCTS_DIRに置換
  echo "🔧 すべての絶対パス参照を修正しています..."
  
  # Debug-iphonesimulator参照も修正
  sed -i'.tmp' "s|$STALE_PATH_BASE/Debug-iphoneos|BUILT_PRODUCTS_DIR|g" "$PBXPROJ"
  sed -i'.tmp' "s|$STALE_PATH_BASE/Debug-iphonesimulator|BUILT_PRODUCTS_DIR|g" "$PBXPROJ"
  sed -i'.tmp' "s|$STALE_PATH_BASE/Release-iphoneos|BUILT_PRODUCTS_DIR|g" "$PBXPROJ"
  sed -i'.tmp' "s|$STALE_PATH_BASE/Release-iphonesimulator|BUILT_PRODUCTS_DIR|g" "$PBXPROJ"
  
  # すべての path = "..." エントリを空に
  sed -i'.tmp' 's|path = ".*/build/ios/.*"|path = ""|g' "$PBXPROJ"
  
  # sourceTreeをDEVELOPER_DIRに変更
  sed -i'.tmp' 's|sourceTree = BUILT_PRODUCTS_DIR|sourceTree = DEVELOPER_DIR|g' "$PBXPROJ"
  
  # 一時ファイルを削除
  rm -f "${PBXPROJ}.tmp"
  
  echo "✅ プロジェクトファイルを修正しました"
fi

# Podsディレクトリのバックアップファイルを削除
echo "🧹 Pods内のバックアップファイルを削除しています..."
find "$PROJECT_ROOT/ios/Pods" -name "*.bak" -o -name "*.original" -type f -delete 2>/dev/null || true

# 徹底的なクリーンアップ
echo "🧹 ビルド成果物を完全に削除しています..."
rm -rf "$PROJECT_ROOT/build"
rm -rf "$PROJECT_ROOT/ios/build"
rm -rf "$PROJECT_ROOT/ios/DerivedData"

# ビルドキャッシュのクリーンアップ
echo "🧹 Xcodeキャッシュを削除しています..."
rm -rf "$HOME/Library/Developer/Xcode/DerivedData/Runner-*"
flutter clean

# プロジェクトの修復
echo "🔄 プロジェクトを修復しています..."
# 以前: flutter create --platforms=ios . --project-name="$(basename "$PROJECT_ROOT")"
# 修正:
flutter create . --platforms=ios --project-name="$(basename "$PROJECT_ROOT")"

# 依存関係を再インストール
echo "🔄 依存関係を再インストールしています..."
cd "$PROJECT_ROOT" && flutter pub get
cd "$PROJECT_ROOT/ios" && pod install --repo-update

echo "✅ 修正が完了しました"
echo "ℹ️ Xcodeを再起動して、プロジェクトを開き直してください"
exit 0
