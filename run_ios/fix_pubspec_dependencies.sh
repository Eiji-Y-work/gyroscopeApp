#!/bin/bash

echo "=== Flutter 依存関係修正スクリプト v1.0 ==="
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
echo "プロジェクトルート: $PROJECT_ROOT"

PUBSPEC="$PROJECT_ROOT/pubspec.yaml"

# バックアップ作成
cp "$PUBSPEC" "${PUBSPEC}.bak"
echo "✅ pubspec.yamlのバックアップを作成しました: ${PUBSPEC}.bak"

# audioplayers_darwinのバージョンを更新
echo "🔧 audioplayers_darwinのバージョン制約を更新しています..."
sed -i.tmp 's/audioplayers_darwin: .*/audioplayers_darwin: ^5.0.2/g' "$PUBSPEC"
rm -f "${PUBSPEC}.tmp"

echo "✅ pubspec.yamlを更新しました"

# 依存関係の再解決
echo "🔄 依存関係を再解決しています..."
cd "$PROJECT_ROOT" && flutter pub get

# CocoaPodsのセットアップ
echo "🔄 CocoaPodsをセットアップしています..."
cd "$PROJECT_ROOT/ios" && flutter precache --ios
cd "$PROJECT_ROOT/ios" && rm -rf Pods .symlinks Podfile.lock
cd "$PROJECT_ROOT" && flutter pub get
cd "$PROJECT_ROOT/ios" && pod install

echo "✅ 依存関係の修正が完了しました"
exit 0
