#!/bin/bash

echo "=== audioplayers_darwin Swift修正スクリプト v3.0 ==="

# パッケージのパスを設定
PACKAGE_PATH="$HOME/.pub-cache/hosted/pub.dev/audioplayers_darwin-5.0.2"
SWIFT_FILE="$PACKAGE_PATH/ios/Classes/SwiftAudioplayersDarwinPlugin.swift"

if [ ! -d "$PACKAGE_PATH" ]; then
  echo "⚠️ audioplayers_darwin パッケージが見つかりません: $PACKAGE_PATH"
  exit 1
fi

if [ ! -f "$SWIFT_FILE" ]; then
  echo "⚠️ Swift ファイルが見つかりません: $SWIFT_FILE"
  exit 1
fi

# ファイルのバックアップ
cp "$SWIFT_FILE" "${SWIFT_FILE}.bak"
echo "バックアップを作成しました: ${SWIFT_FILE}.bak"

echo "SwiftAudioplayersDarwinPlugin.swift を修正中..."

# 1. 行99と291の修正: args: ラベルを削除し、型変換の問題を修正
sed -i '' 's/\.apply(args: call\.arguments as! \[String : Any\])/\.apply(call.arguments as? String ?? "")/g' "$SWIFT_FILE"

# 2. 行374の修正: 引数を取らない関数への引数渡しを修正
sed -i '' 's/\.dispose([^)]*)/\.dispose()/g' "$SWIFT_FILE"

echo "✅ SwiftAudioplayersDarwinPlugin.swift の修正完了"
echo "------------------------------------"
echo "✅ audioplayers_darwin パッケージの修正が完了しました"
exit 0
