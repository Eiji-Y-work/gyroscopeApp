#!/bin/bash

echo "=== Xcode Stale Files 直接修正ツール v2.0 ==="
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
echo "プロジェクトルート: $PROJECT_ROOT"

# プロジェクトファイル内の参照を直接修正
PBXPROJ="$PROJECT_ROOT/ios/Runner.xcodeproj/project.pbxproj"
if [ -f "$PBXPROJ" ]; then
  # バックアップの作成
  cp "$PBXPROJ" "${PBXPROJ}.original"
  echo "✅ プロジェクトファイルのバックアップを作成しました"

  # 問題のパス参照を直接置換
  echo "🔍 問題のパス参照を検索して修正しています..."
  STALE_PATH="/Users/owner/Desktop/Flutter/Eiji/gyroscopeApp/build/ios/Debug-iphoneos"
  
  # カウントして存在を確認
  MATCHES=$(grep -c "$STALE_PATH" "$PBXPROJ")
  echo "問題のパス参照: $MATCHES 件見つかりました"
  
  # 直接置換（Stale file問題を解消するための重要なステップ）
  sed -i'.tmp' "s|$STALE_PATH|BUILT_PRODUCTS_DIR|g" "$PBXPROJ"
  # name = Runner.app の参照を修正
  sed -i'.tmp' "s|name = Runner.app; path = .*|name = Runner.app; path = \"\";|g" "$PBXPROJ"
  # LaunchScreen.storyboardc の参照を修正
  sed -i'.tmp' "s|path = .*LaunchScreen.storyboardc|path = \"\"|g" "$PBXPROJ"
  
  # 一時ファイルを削除
  rm -f "${PBXPROJ}.tmp"
  
  # 検証
  REMAINING=$(grep -c "$STALE_PATH" "$PBXPROJ")
  if [ "$REMAINING" -eq 0 ]; then
    echo "✅ 問題のパス参照をすべて修正しました"
  else
    echo "⚠️ まだ $REMAINING 件のパス参照が残っています"
  fi
fi

# Xcodeのプロジェクトキャッシュを確実に削除
echo "🧹 Xcodeのプロジェクトキャッシュを削除しています..."
rm -rf "$PROJECT_ROOT/ios/Runner.xcodeproj/project.xcworkspace/xcuserdata"
rm -rf "$PROJECT_ROOT/ios/Runner.xcworkspace/xcuserdata"

# Xcodeのキャッシュを徹底的に削除
echo "🧹 Xcodeのキャッシュを徹底的に削除しています..."
DERIVED_DATA="$HOME/Library/Developer/Xcode/DerivedData"
if [ -d "$DERIVED_DATA" ]; then
  # Runnerプロジェクト関連のキャッシュを探して削除
  find "$DERIVED_DATA" -name "*Runner*" -type d -exec rm -rf {} \; 2>/dev/null || true
  find "$DERIVED_DATA" -name "*gyroscope*" -type d -exec rm -rf {} \; 2>/dev/null || true
fi

# すべてのビルド成果物を削除
echo "🧹 ビルド成果物を削除しています..."
rm -rf "$PROJECT_ROOT/build"
rm -rf "$PROJECT_ROOT/ios/build"
rm -rf "$PROJECT_ROOT/ios/Pods"
rm -f "$PROJECT_ROOT/ios/Podfile.lock"

# iOSプロジェクトを再生成（最終手段）
echo "🔄 iOSプロジェクトファイルを再生成します..."
cd "$PROJECT_ROOT" && flutter clean
cd "$PROJECT_ROOT" && rm -rf ios/.symlinks
cd "$PROJECT_ROOT" && flutter create --platforms=ios --org com.example .

# 依存関係を再インストール
echo "🔄 依存関係を再インストールしています..."
cd "$PROJECT_ROOT" && flutter pub get
cd "$PROJECT_ROOT/ios" && pod install --repo-update

echo "✅ 修正が完了しました"
echo "ℹ️ 重要: このままXcodeを完全に終了し、再度開いてからビルドしてください。"
echo "ℹ️ ターミナルから実行するには: killall Xcode && sleep 2 && open ios/Runner.xcworkspace"
exit 0
