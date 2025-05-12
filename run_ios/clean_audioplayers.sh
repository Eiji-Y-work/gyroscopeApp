#!/bin/bash

echo "=== audioplayers_darwin クリーンアップスクリプト v1.0 ==="

# audioplayers_darwinパッケージを探す
for dir in $(find "$HOME/.pub-cache/hosted/pub.dev" -name "audioplayers_darwin*" -type d 2>/dev/null); do
  echo "パッケージを処理中: $dir"
  CLASSES_DIR="$dir/ios/Classes"
  
  if [ -d "$CLASSES_DIR" ]; then
    # バックアップファイルをクリーンアップ
    find "$CLASSES_DIR" -name "*.bak" -o -name "*.original" | while read file; do
      echo "削除: $file"
      rm -f "$file"
    done
    
    echo "✅ $CLASSES_DIR のバックアップファイルをクリーンアップしました"
  fi
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
