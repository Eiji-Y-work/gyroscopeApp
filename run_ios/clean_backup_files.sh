#!/bin/bash

echo "=== バックアップファイル完全削除ツール v1.0 ==="
echo "警告の原因となっているバックアップファイルを削除します"

# パスを定義
FLUTTER_ROOT="${HOME}/.pub-cache/hosted/pub.dev"
IOS_DIR="/Users/owner/Desktop/Flutter/Eiji/gyroscopeApp/ios"
PODS_DIR="${IOS_DIR}/Pods"

# 1. audioplayers_darwinのバックアップファイル削除
echo "🔍 audioplayers_darwin のバックアップファイルを検索しています..."
AUDIOPLAYERS_DIR="${FLUTTER_ROOT}/audioplayers_darwin-5.0.2"
if [ -d "${AUDIOPLAYERS_DIR}" ]; then
  echo "📂 ${AUDIOPLAYERS_DIR} を処理しています"
  
  # backupsディレクトリを削除
  find "${AUDIOPLAYERS_DIR}" -type d -name "backups" | while read dir; do
    echo "🗑️ ディレクトリを削除: ${dir}"
    rm -rf "${dir}"
  done
  
  # .bakと.originalファイルを削除
  find "${AUDIOPLAYERS_DIR}" -type f \( -name "*.bak" -o -name "*.original" -o -name "*.bak.*" \) | while read file; do
    echo "🗑️ ファイル削除: ${file}"
    rm -f "${file}"
  done
fi

# 2. vibrationのバックアップファイル削除
echo "🔍 vibration のバックアップファイルを検索しています..."
VIBRATION_DIR="${FLUTTER_ROOT}/vibration-1.9.0"
if [ -d "${VIBRATION_DIR}" ]; then
  echo "📂 ${VIBRATION_DIR} を処理しています"
  
  # .bakと.originalファイルを削除
  find "${VIBRATION_DIR}" -type f \( -name "*.bak" -o -name "*.original" \) | while read file; do
    echo "🗑️ ファイル削除: ${file}"
    rm -f "${file}"
  done
fi

# 3. xcodeからの参照を削除するためにプロジェクトファイルを修正
echo "🔧 Xcodeプロジェクトからのバックアップファイル参照を削除しています..."

# plugin_registrantファイルを再作成
flutter clean
cd "${IOS_DIR}" && pod deintegrate
cd "${IOS_DIR}" && rm -rf Pods Podfile.lock .symlinks
cd "${IOS_DIR}/.." && flutter pub get 

echo "✅ バックアップファイルの削除が完了しました"
echo "🔄 CocoaPodsを再インストールしています..."
cd "${IOS_DIR}" && pod install --repo-update

echo "🚀 以下のコマンドでXcodeプロジェクトを開いてビルドしてください:"
echo "open ${IOS_DIR}/Runner.xcworkspace"
