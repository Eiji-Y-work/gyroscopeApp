#!/bin/bash

echo "=== Xcode 徹底クリーンアップスクリプト v1.0 ==="

# DerivedData ディレクトリのクリーンアップ
echo "🧹 Xcodeのキャッシュディレクトリをクリーンアップ中..."
DERIVED_DATA="$HOME/Library/Developer/Xcode/DerivedData"

if [ -d "$DERIVED_DATA" ]; then
  # Runner関連のディレクトリを探して削除
  RUNNER_DIRS=$(find "$DERIVED_DATA" -type d -name "*Runner*" -o -name "*gyroscope*")
  if [ -n "$RUNNER_DIRS" ]; then
    echo "$RUNNER_DIRS" | while read dir; do
      if [ -d "$dir" ]; then
        echo "  - 削除中: $dir"
        rm -rf "$dir" 2>/dev/null
      fi
    done
    echo "✅ プロジェクト関連のXcodeキャッシュを削除しました"
  else
    echo "  - プロジェクト関連のキャッシュは見つかりませんでした"
  fi
fi

# ModuleCache ディレクトリのクリーンアップ
MODULE_CACHE="$HOME/Library/Developer/Xcode/DerivedData/ModuleCache.noindex"
if [ -d "$MODULE_CACHE" ]; then
  echo "  - モジュールキャッシュをクリーンアップ中..."
  # 特定のモジュールを対象に
  for target in Flutter AudioPlayer audio Swift; do
    find "$MODULE_CACHE" -type d -name "*$target*" | while read cache; do
      echo "    削除中: $(basename "$cache")"
      rm -rf "$cache" 2>/dev/null
    done
  done
  echo "  ✅ モジュールキャッシュをクリーンアップしました"
fi

# Build Products ディレクトリのクリーンアップ
echo "🧹 ビルド成果物を削除中..."
PRODUCTS_DIR="$HOME/Library/Developer/Xcode/Products"
if [ -d "$PRODUCTS_DIR" ]; then
  rm -rf "$PRODUCTS_DIR"/*
  echo "✅ ビルド成果物を削除しました"
fi

# Staleファイル関連のサーチパスをリセット
echo "🧹 プロジェクトのビルド設定をクリーンアップ中..."
PROJECT_ROOT="${1:-$(pwd)}"
XCODEPROJ="$PROJECT_ROOT/ios/Runner.xcodeproj"

if [ -d "$XCODEPROJ" ]; then
  # Xcodeのプロジェクトファイルをバックアップ
  cp -r "$XCODEPROJ/project.pbxproj" "$XCODEPROJ/project.pbxproj.bak" 2>/dev/null
  
  # ビルド設定ファイルからStaleファイル参照を削除（実験的）
  sed -i'.original' -e 's/FRAMEWORK_SEARCH_PATHS = .*/FRAMEWORK_SEARCH_PATHS = "";/g' "$XCODEPROJ/project.pbxproj" 2>/dev/null
  sed -i'.original' -e 's/LIBRARY_SEARCH_PATHS = .*/LIBRARY_SEARCH_PATHS = "";/g' "$XCODEPROJ/project.pbxproj" 2>/dev/null
  
  echo "✅ プロジェクト設定を初期化しました"
fi

# CocoaPodsのキャッシュをクリーンアップ
echo "🧹 CocoaPodsのキャッシュをクリーンアップ中..."
pod cache clean --all 2>/dev/null
rm -rf "$HOME/Library/Caches/CocoaPods" 2>/dev/null
echo "✅ CocoaPodsのキャッシュをクリーンアップしました"

echo "✅ Xcodeクリーンアップが完了しました"
exit 0
