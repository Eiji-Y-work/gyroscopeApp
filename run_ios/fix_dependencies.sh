#!/bin/bash

echo "=== Flutter 依存関係修復スクリプト v1.0 ==="
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
echo "プロジェクトルート: $PROJECT_ROOT"

# まずはクリーンアップを行う
echo "🧹 プロジェクトをクリーンアップしています..."
cd "$PROJECT_ROOT" && flutter clean

# pubspec.lockを削除して依存関係を再解決
if [ -f "$PROJECT_ROOT/pubspec.lock" ]; then
  echo "🔄 pubspec.lockを削除して新しく依存関係を解決します..."
  rm "$PROJECT_ROOT/pubspec.lock"
fi

# 正しいコマンドで依存関係を取得
echo "🔄 正しいコマンドで依存関係を取得しています..."
cd "$PROJECT_ROOT" && flutter pub get

# iOS関連のファイルをクリーンアップして再生成
echo "🧹 iOSビルドファイルをクリーンアップしています..."
rm -rf "$PROJECT_ROOT/ios/Pods"
rm -rf "$PROJECT_ROOT/ios/.symlinks"
rm -f "$PROJECT_ROOT/ios/Podfile.lock"
rm -rf "$PROJECT_ROOT/ios/Flutter/Flutter.podspec"

# CocoaPodsのセットアップとインストール
echo "🔄 CocoaPodsを再インストールしています..."
cd "$PROJECT_ROOT/ios" && pod deintegrate || true
cd "$PROJECT_ROOT/ios" && pod install --repo-update

echo "✅ 依存関係の修復が完了しました"
exit 0
