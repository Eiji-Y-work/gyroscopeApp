#!/bin/bash

echo "=== Flutter パッケージ完全クリーンアップスクリプト v2.0 ==="

# 問題が起きやすいパッケージを直接指定して処理
PROBLEM_PACKAGES=("audioplayers_darwin" "vibration" "device_info_plus")

for pkg in "${PROBLEM_PACKAGES[@]}"; do
  echo "🔍 $pkg パッケージを処理中..."
  for dir in $(find "$HOME/.pub-cache/hosted/pub.dev" -name "${pkg}*" -type d 2>/dev/null); do
    echo "📁 処理: $dir"
    
    # 特にiOSディレクトリに注目
    IOS_DIR="$dir/ios"
    if [ -d "$IOS_DIR" ]; then
      echo "- iOS ディレクトリを処理中..."
      
      # backupsディレクトリをまるごと削除
      find "$IOS_DIR" -type d -name "backups" -exec rm -rf {} \; 2>/dev/null || true
      echo "- バックアップディレクトリ削除完了"
      
      # バックアップファイルを削除
      find "$IOS_DIR" -type f \( -name "*.bak" -o -name "*.original" -o -name "*.bak.*" \) -exec rm -f {} \; 2>/dev/null || true
      echo "- バックアップファイル削除完了"
    fi
    
    # 残りのディレクトリも処理
    echo "- その他のバックアップファイルを削除中..."
    find "$dir" -type f \( -name "*.bak" -o -name "*.original" -o -name "*.bak.*" \) -exec rm -f {} \; 2>/dev/null || true
    
    echo "✅ $dir の処理完了"
  done
done

# 他のすべてのパッケージでバックアップファイルを検索
echo "🔍 すべてのFlutterパッケージからバックアップファイルを検索..."
find "$HOME/.pub-cache" -type f \( -name "*.bak" -o -name "*.original" -o -name "*.bak.*" \) -exec rm -f {} \; 2>/dev/null || true

# backupsディレクトリの検索と削除
echo "🔍 すべてのbackupsディレクトリを検索..."
find "$HOME/.pub-cache" -type d -name "backups" -exec rm -rf {} \; 2>/dev/null || true

# iOS関連ファイルのクリーンアップ
if [ -d "ios/Pods" ]; then
  echo "🧹 Podsディレクトリをクリーンアップ..."
  rm -rf ios/Pods
  echo "✅ Podsディレクトリを削除しました"
fi

if [ -f "ios/Podfile.lock" ]; then
  echo "🧹 Podfile.lockをクリーンアップ..."
  rm -f ios/Podfile.lock
  echo "✅ Podfile.lockを削除しました"
fi

echo "✅ クリーンアップが完了しました"
exit 0
