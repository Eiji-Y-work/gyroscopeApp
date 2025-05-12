#!/bin/bash

echo "=== Flutter パッケージ徹底クリーンアップスクリプト v1.0 ==="

# 全パッケージのバックアップファイルを検索して削除
echo "🔍 すべてのFlutterパッケージのバックアップファイルを検索中..."
FOUND_COUNT=0
for bak_file in $(find "$HOME/.pub-cache/hosted/pub.dev" -type f \( -name "*.bak*" -o -name "*.original" \) 2>/dev/null); do
  echo "削除: $bak_file"
  rm -f "$bak_file"
  FOUND_COUNT=$((FOUND_COUNT + 1))
done

echo "✅ 合計 $FOUND_COUNT 個のバックアップファイルを削除しました"

# 問題が報告されたパッケージを明示的にクリーンアップ
for pkg in "audioplayers_darwin" "vibration" "device_info_plus"; do
  echo "🔍 $pkg パッケージを検索中..."
  for dir in $(find "$HOME/.pub-cache/hosted/pub.dev" -name "${pkg}*" -type d 2>/dev/null); do
    echo "処理中: $dir"
    # すべてのサブディレクトリからバックアップファイルを探して削除
    find "$dir" -type d -name "backups" -exec rm -rf {} \; 2>/dev/null
    # 個別のバックアップファイルも削除
    find "$dir" -type f \( -name "*.bak*" -o -name "*.original" \) -exec rm -f {} \;
    echo "✅ $dir のクリーンアップ完了"
  done
done

# iOS関連の一時ファイルもクリーンアップ
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
