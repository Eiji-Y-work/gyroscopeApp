#!/bin/bash

echo "=== audioplayers_darwin 直接Swift修正スクリプト v1.0 ==="

PACKAGE_PATH="$HOME/.pub-cache/hosted/pub.dev/audioplayers_darwin-5.0.2"
SWIFT_FILE="$PACKAGE_PATH/ios/Classes/SwiftAudioplayersDarwinPlugin.swift"

if [ ! -f "$SWIFT_FILE" ]; then
  echo "⚠️ Swift ファイルが見つかりません: $SWIFT_FILE"
  
  # 他の可能性のあるパスを検索
  for dir in $(find "$HOME/.pub-cache/hosted/pub.dev" -name "audioplayers_darwin*" -type d 2>/dev/null); do
    possible_file="$dir/ios/Classes/SwiftAudioplayersDarwinPlugin.swift"
    if [ -f "$possible_file" ]; then
      SWIFT_FILE="$possible_file"
      echo "代替ファイルを見つけました: $SWIFT_FILE"
      break
    fi
  done
  
  if [ ! -f "$SWIFT_FILE" ]; then
    echo "❌ Swift ファイルが見つかりません。"
    exit 1
  fi
fi

# バックアップ作成
BACKUP_FILE="${SWIFT_FILE}.bak.$(date +%s)"
cp "$SWIFT_FILE" "$BACKUP_FILE"
echo "✅ バックアップを作成しました: $BACKUP_FILE"

# ターゲット行を直接修正するファイルを生成
LINE_99=$(sed '99q;d' "$SWIFT_FILE" 2>/dev/null || echo "")
LINE_291=$(sed '291q;d' "$SWIFT_FILE" 2>/dev/null || echo "")
LINE_374=$(sed '374q;d' "$SWIFT_FILE" 2>/dev/null || echo "")

echo "修正前の行:"
[ -n "$LINE_99" ] && echo "行 99: $LINE_99"
[ -n "$LINE_291" ] && echo "行 291: $LINE_291"
[ -n "$LINE_374" ] && echo "行 374: $LINE_374"

# 各行の修正バージョンを準備
FIXED_LINE_99=$(echo "$LINE_99" | sed 's/\.apply(args: call\.arguments as! \[String : Any\])/\.apply(call.arguments as? String ?? "")/g')
FIXED_LINE_291=$(echo "$LINE_291" | sed 's/\.apply(args: call\.arguments as! \[String : Any\])/\.apply(call.arguments as? String ?? "")/g')
FIXED_LINE_374=$(echo "$LINE_374" | sed 's/\.dispose([^)]*)/\.dispose()/g')

# ファイル全体に正規表現パターンを適用
sed -i '' 's/\.apply(args: call\.arguments as! \[String : Any\])/\.apply(call.arguments as? String ?? "")/g' "$SWIFT_FILE"
sed -i '' 's/\.dispose([^)]*)/\.dispose()/g' "$SWIFT_FILE"

echo "✅ Swift ファイルの修正が完了しました"
echo "-------------------------------------"
exit 0
