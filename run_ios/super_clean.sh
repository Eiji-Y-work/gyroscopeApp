#!/bin/bash

echo "=== Flutter プロジェクト徹底クリーンアップスクリプト v3.0 ==="

# ローカルビルドディレクトリの完全クリーンアップ
echo "🧹 Flutterプロジェクトのビルドディレクトリをクリーンアップ中..."
rm -rf build/
rm -rf ios/build/

# iOS関連の一時ファイルをクリーンアップ
echo "🧹 iOSビルドファイルをクリーンアップ中..."
rm -rf ios/Pods
rm -rf ios/Flutter/Flutter.podspec
rm -f ios/Podfile.lock
rm -rf ios/.symlinks
rm -rf ios/Flutter/ephemeral

# Flutterキャッシュをクリーンアップ
echo "🧹 Flutterキャッシュをクリーンアップ中..."
flutter clean

# Xcodeの徹底的なクリーンアップ
echo "🧹 Xcodeのキャッシュを徹底的にクリーンアップ中..."
bash "$(dirname "$0")/xcode_cleanup.sh" "$(cd .. && pwd)"

# 問題のあるパッケージを直接クリーンアップ
echo "🧹 問題のあるパッケージをクリーンアップ中..."
PROBLEM_PACKAGES=("audioplayers_darwin" "vibration" "device_info_plus" "sensors_plus" "path_provider_foundation" "shared_preferences_foundation")

for pkg in "${PROBLEM_PACKAGES[@]}"; do
  echo "🔍 $pkg パッケージを処理中..."
  
  # 各パッケージのbackupsディレクトリを完全削除
  for dir in $(find "$HOME/.pub-cache/hosted/pub.dev" -name "${pkg}*" -type d 2>/dev/null); do
    echo "  📂 $dir を処理中..."
    
    # backupsディレクトリを削除
    if [ -d "$dir/ios" ]; then
      find "$dir/ios" -type d -name "backups" -exec rm -rf {} \; 2>/dev/null
    fi
    
    # バックアップファイルを削除
    find "$dir" -type f \( -name "*.bak" -o -name "*.bak.*" -o -name "*.original" \) -exec rm -f {} \; 2>/dev/null
    
    echo "  ✅ 処理完了"
  done
done

# Podspecファイルを修正（問題が生じやすいため）
for podspec in $(find "$HOME/.pub-cache" -name "*.podspec" 2>/dev/null); do
  if grep -q "s.pod_target_xcconfig.*=.*{.*'DEFINES_MODULE'" "$podspec"; then
    echo "🔧 Podspecファイルを修正: $podspec"
    sed -i .bak 's/s.pod_target_xcconfig.*=.*{.*"DEFINES_MODULE"/s.pod_target_xcconfig = { "DEFINES_MODULE"/g' "$podspec" 2>/dev/null
    rm -f "${podspec}.bak" 2>/dev/null
  fi
done

# 依存関係を再構築
echo "🔄 依存関係を再構築中..."
flutter pub get

# CocoaPodsを再インストール
echo "🔄 CocoaPodsを再インストール中..."
cd ios && pod install --repo-update

echo "✅ クリーンアップが完了しました"
exit 0
