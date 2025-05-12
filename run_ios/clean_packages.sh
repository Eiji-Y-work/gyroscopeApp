#!/bin/bash

echo "=== Flutter パッケージクリーンアップスクリプト v1.0 ==="

# audioplayers_darwin パッケージのクリーンアップ
echo "🔍 audioplayers_darwin のクリーンアップ..."
for dir in $(find "$HOME/.pub-cache/hosted/pub.dev" -name "audioplayers_darwin*" -type d 2>/dev/null); do
  echo "処理中: $dir"
  # バックアップファイル削除 - サブディレクトリも含む
  find "$dir" -type f \( -name "*.bak*" -o -name "*.original" \) -exec rm -f {} \;
  echo "✅ バックアップファイル削除完了: $dir"
done

# vibration パッケージのクリーンアップ
echo "🔍 vibration のクリーンアップ..."
for dir in $(find "$HOME/.pub-cache/hosted/pub.dev" -name "vibration*" -type d 2>/dev/null); do
  echo "処理中: $dir"
  # バックアップファイル削除
  find "$dir" -type f \( -name "*.bak*" -o -name "*.original" \) -exec rm -f {} \;
  echo "✅ バックアップファイル削除完了: $dir"
done

# device_info_plus パッケージのクリーンアップ 
echo "🔍 device_info_plus のクリーンアップ..."
for dir in $(find "$HOME/.pub-cache/hosted/pub.dev" -name "device_info_plus*" -type d 2>/dev/null); do
  echo "処理中: $dir"
  # バックアップファイル削除
  find "$dir" -type f \( -name "*.bak*" -o -name "*.original" \) -exec rm -f {} \;
  echo "✅ バックアップファイル削除完了: $dir"
done

# その他すべてのパッケージの .bak ファイルを検索して削除
echo "🔍 その他のパッケージのバックアップファイルを検索中..."
FOUND_COUNT=0
for bak_file in $(find "$HOME/.pub-cache/hosted/pub.dev" -type f \( -name "*.bak*" -o -name "*.original" \) 2>/dev/null); do
  echo "削除: $bak_file"
  rm -f "$bak_file"
  FOUND_COUNT=$((FOUND_COUNT + 1))
done

echo "✅ 合計 $FOUND_COUNT 個のバックアップファイルを削除しました"

# iOS関連の一時ファイルをクリーンアップ
if [ -d "ios/Pods" ]; then
  echo "Podsディレクトリをクリーンアップしています..."
  rm -rf ios/Pods
  echo "✅ Podsディレクトリを削除しました"
fi

if [ -f "ios/Podfile.lock" ]; then
  echo "Podfile.lockをクリーンアップしています..."
  rm -f ios/Podfile.lock
  echo "✅ Podfile.lockを削除しました"
fi

echo "✅ クリーンアップが完了しました"
exit 0
