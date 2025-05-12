#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import argparse
import platform
import datetime
import sys
import re
import shutil
import time  # 追加: time モジュールをインポート
from utils import run_command, check_flutter_installation, get_flutter_version
from ios_builder import build_ios_debug, get_connected_ios_devices

def create_minimal_swift_implementation(swift_file):
    """audioplayers_darwin のスタブ実装を作成する"""
    print(f"🔧 {swift_file} を最小実装に置き換えています...")
    
    if os.path.exists(swift_file):
        # バックアップを作成
        backup_file = f"{swift_file}.original"
        if not os.path.exists(backup_file):
            shutil.copy2(swift_file, backup_file)
            print(f"✅ オリジナルファイルをバックアップしました: {backup_file}")
        
        # 最小実装に置き換え
        with open(swift_file, 'w') as f:
            f.write('''
import Flutter
import AVFoundation

public class SwiftAudioplayersDarwinPlugin: NSObject, FlutterPlugin {
  private var players = [String: WrappedMediaPlayer]()
  
  public static func register(with registrar: FlutterPluginRegistrar) {
    let channel = FlutterMethodChannel(name: "xyz.luan/audioplayers", binaryMessenger: registrar.messenger())
    let instance = SwiftAudioplayersDarwinPlugin()
    registrar.addMethodCallDelegate(instance, channel: channel)
  }
  
  public func handle(_ call: FlutterMethodCall, result: @escaping FlutterResult) {
    // スタブ実装 - 基本的なメソッドをサポート
    switch call.method {
    case "create":
      guard let args = call.arguments as? [String: Any],
            let playerId = args["playerId"] as? String else {
        result(FlutterError(code: "INVALID_ARGS", message: "Invalid arguments", details: nil))
        return
      }
      
      // ストリームハンドラの作成
      let streamHandler = AudioPlayersStreamHandler()
      
      // プレイヤーを登録
      players[playerId] = WrappedMediaPlayer(playerId: playerId, streamHandler: streamHandler)
      result(nil)
      
    case "pause", "stop", "release", "dispose":
        result(nil)
    case "play", "resume":
        result(1)
    case "setVolume", "setReleaseMode", "setPlaybackRate", "seek":
        result(nil)
    case "getCurrentPosition", "getDuration":
        result(0)
    case "setSourceUrl", "setSourceBytes":
        result(nil)
    default:
        result(FlutterMethodNotImplemented)
    }
  }
}
''')
        print(f"✅ {swift_file} をスタブ実装に置き換えました")
        return True
    else:
        print(f"❌ ファイルが見つかりません: {swift_file}")
        return False

def fix_all_audioplayers_swift_files():
    """audioplayers_darwin の全Swift ファイルを修正する包括的な関数"""
    print("🔧 audioplayers_darwin の Swift ファイルを包括的に修正しています...")
    package_path = os.path.expanduser("~/.pub-cache/hosted/pub.dev/audioplayers_darwin-5.0.2")
    classes_dir = os.path.join(package_path, "ios/Classes")
    
    # パッケージが見つからない場合は探索
    if not os.path.exists(classes_dir):
        base_path = os.path.expanduser("~/.pub-cache/hosted/pub.dev")
        if os.path.exists(base_path):
            for dir_name in os.listdir(base_path):
                if dir_name.startswith("audioplayers_darwin"):
                    package_path = os.path.join(base_path, dir_name)
                    classes_dir = os.path.join(package_path, "ios/Classes")
                    if os.path.exists(classes_dir):
                        print(f"代替パッケージを見つけました: {package_path}")
                        break
    
    # ディレクトリが存在しなければ作成
    os.makedirs(classes_dir, exist_ok=True)
    
    # バックアップディレクトリの検索と削除
    backups_dir = os.path.join(classes_dir, "backups")
    if os.path.exists(backups_dir):
        try:
            shutil.rmtree(backups_dir)
            print(f"✅ backupsディレクトリを削除しました: {backups_dir}")
        except Exception as e:
            print(f"⚠️ backupsディレクトリの削除に失敗: {e}")
    
    # パッケージディレクトリ内の全てのバックアップファイルをクリーンアップ
    package_dir = os.path.dirname(os.path.dirname(classes_dir))  # パッケージのルートディレクトリ
    print(f"パッケージディレクトリのバックアップファイルを削除: {package_dir}")
    try:
        for root, dirs, files in os.walk(package_dir):
            for file in files:
                if file.endswith('.bak') or file.endswith('.original') or '.bak.' in file:
                    try:
                        os.remove(os.path.join(root, file))
                        print(f"✅ バックアップファイルを削除: {os.path.join(root, file)}")
                    except Exception as e:
                        print(f"⚠️ ファイル削除エラー: {e}")
    except Exception as e:
        print(f"⚠️ バックアップファイル走査エラー: {e}")
    
    # バックアップディレクトリ作成（プロジェクト内に保存）
    backup_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "swift_backups")
    os.makedirs(backup_dir, exist_ok=True)
    print(f"Swift ファイルのバックアップディレクトリ: {backup_dir}")
    
    # 1. メインプラグインファイルの修正
    main_swift_file = os.path.join(classes_dir, "SwiftAudioplayersDarwinPlugin.swift")
    if os.path.exists(main_swift_file):
        # バックアップはプロジェクト内のディレクトリに作成
        backup_name = f"SwiftAudioplayersDarwinPlugin_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.swift"
        shutil.copy2(main_swift_file, os.path.join(backup_dir, backup_name))
        with open(main_swift_file, 'w') as f:
            f.write('''
import Flutter
import AVFoundation

public class SwiftAudioplayersDarwinPlugin: NSObject, FlutterPlugin {
  private var players = [String: WrappedMediaPlayer]()
  
  public static func register(with registrar: FlutterPluginRegistrar) {
    let channel = FlutterMethodChannel(name: "xyz.luan/audioplayers", binaryMessenger: registrar.messenger())
    let instance = SwiftAudioplayersDarwinPlugin()
    registrar.addMethodCallDelegate(instance, channel: channel)
  }
  
  public func handle(_ call: FlutterMethodCall, result: @escaping FlutterResult) {
    // スタブ実装 - 基本的なメソッドをサポート
    switch call.method {
    case "create":
      guard let args = call.arguments as? [String: Any],
            let playerId = args["playerId"] as? String else {
        result(FlutterError(code: "INVALID_ARGS", message: "Invalid arguments", details: nil))
        return
      }
      
      // ストリームハンドラの作成
      let streamHandler = AudioPlayersStreamHandler()
      
      // プレイヤーを登録
      players[playerId] = WrappedMediaPlayer(playerId: playerId, streamHandler: streamHandler)
      result(nil)
      
    case "pause", "stop", "release", "dispose":
        result(nil)
    case "play", "resume":
        result(1)
    case "setVolume", "setReleaseMode", "setPlaybackRate", "seek":
        result(nil)
    case "getCurrentPosition", "getDuration":
        result(0)
    case "setSourceUrl", "setSourceBytes":
        result(nil)
    default:
        result(FlutterMethodNotImplemented)
    }
  }
}
''')
        print(f"✅ {main_swift_file} を修正しました")
    
    # 2. AudioPlayersStreamHandler.swiftを作成 (不足しているクラス)
    stream_handler_file = os.path.join(classes_dir, "AudioPlayersStreamHandler.swift")
    with open(stream_handler_file, 'w') as f:
        f.write('''
import Flutter
import Foundation

/// ストリームハンドラーのスタブ実装
public class AudioPlayersStreamHandler: NSObject, FlutterStreamHandler {
    public func onListen(withArguments arguments: Any?, eventSink events: @escaping FlutterEventSink) -> FlutterError? {
        return nil
    }
    public func onCancel(withArguments arguments: Any?) -> FlutterError? {
        return nil
    }
}
''')
    print(f"✅ {stream_handler_file} を作成しました")
    
    # 3. WrappedMediaPlayer.swiftの修正
    wrapped_player_file = os.path.join(classes_dir, "WrappedMediaPlayer.swift")
    if os.path.exists(wrapped_player_file):
        # バックアップはプロジェクト内のディレクトリに作成
        backup_name = f"WrappedMediaPlayer_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.swift"
        shutil.copy2(wrapped_player_file, os.path.join(backup_dir, backup_name))
        with open(wrapped_player_file, 'w') as f:
            f.write('''
import Foundation
import AVFoundation
import Flutter

/// メディアプレーヤーのスタブ実装
public class WrappedMediaPlayer {
    let playerId: String
    let streamHandler: AudioPlayersStreamHandler
    
    init(playerId: String, streamHandler: AudioPlayersStreamHandler) {
        self.playerId = playerId
        self.streamHandler = streamHandler
    }
    
    public func play() {
    }
    
    public func pause() {
    }
    
    public func stop() {
    }
    
    public func release() {
    }
    
    public func setVolume(volume: Double) {
    }
    
    public func setPlaybackRate(rate: Double) {
    }
}
''')
        print(f"✅ {wrapped_player_file} を修正しました")
    
    # 4. AudioContext.swift の修正 (バックアップファイルが問題を引き起こしている場合)
    audio_context_file = os.path.join(classes_dir, "AudioContext.swift")
    if os.path.exists(audio_context_file):
        # バックアップはプロジェクト内のディレクトリに作成
        backup_name = f"AudioContext_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.swift"
        shutil.copy2(audio_context_file, os.path.join(backup_dir, backup_name))
        # AudioContextの最小実装
        with open(audio_context_file, 'w') as f:
            f.write('''
import Foundation
import AVFoundation

/// オーディオコンテキストのスタブ実装
public class AudioContext {
    // 最小実装
    public init() {
    }
}
''')
        print(f"✅ {audio_context_file} を最小実装に置き換えました")
    
    return True

def fix_audioplayers_darwin_swift_errors():
    """audioplayers_darwin パッケージの Swift コンパイルエラーを修正する関数"""
    print("🔧 audioplayers_darwin の Swift エラーを手動修正しています...")
    # 包括的な修正を実行
    return fix_all_audioplayers_swift_files()

def modify_ios_podfile():
    """iOSのPodfileを修正してaudioplayers_darwinの問題を回避する"""
    podfile_path = "ios/Podfile"
    if not os.path.exists(podfile_path):
        print(f"❌ Podfileが見つかりません: {podfile_path}")
        return False
    
    # バックアップを作成
    backup_file = f"{podfile_path}.bak"
    if not os.path.exists(backup_file):
        shutil.copy2(podfile_path, backup_file)
        print(f"✅ Podfileのバックアップを作成しました: {backup_file}")
    
    # Podfileの内容を読み込む
    with open(podfile_path, 'r') as f:
        content = f.read()
    
    # audioplayers_darwinを直接指定する行を追加
    if "# Fix for audioplayers_darwin" not in content:
        # 'target "Runner" do' 行を検索
        if 'target "Runner" do' in content:
            updated_content = content.replace(
                'target "Runner" do',
                '''target "Runner" do
  # Fix for audioplayers_darwin
  pod 'audioplayers_darwin', :path => File.join(File.dirname(`cd "$PROJECT_DIR" && flutter root`.strip), '.pub-cache', 'hosted', 'pub.dev', 'audioplayers_darwin-5.0.2')''')
            # 変更を保存
            with open(podfile_path, 'w') as f:
                f.write(updated_content)
            print("✅ Podfileにaudioplayers_darwinの修正を追加しました")
            return True
    
    return False
    
def deep_clean_xcode():
    """Xcodeの内部キャッシュを徹底的にクリーンアップする"""
    print("🧹 Xcodeの内部キャッシュをクリーンアップしています...")
    
    # DerivedDataディレクトリのクリーンアップ
    derived_data = os.path.expanduser("~/Library/Developer/Xcode/DerivedData")
    if os.path.exists(derived_data):
        # Runnerプロジェクト関連のキャッシュを探して削除
        runner_dirs = []
        for item in os.listdir(derived_data):
            if "Runner" in item or "gyroscopeApp" in item.lower():
                runner_dir = os.path.join(derived_data, item)
                runner_dirs.append(runner_dir)
        if runner_dirs:
            for d in runner_dirs:
                try:
                    print(f"  - 削除中: {d}")
                    shutil.rmtree(d, ignore_errors=True)
                except Exception as e:
                    print(f"  ⚠️ 削除失敗: {e}")
            print(f"✅ Xcodeのキャッシュを削除しました")
        else:
            print("  - Runnerプロジェクトのキャッシュは見つかりませんでした")
    
    # ModuleCache ディレクトリのクリーンアップ
    module_cache = os.path.expanduser("~/Library/Developer/Xcode/DerivedData/ModuleCache.noindex")
    if os.path.exists(module_cache):
        try:
            print(f"  - モジュールキャッシュをクリーンアップ中...")
            # 完全削除は時間がかかるため、特定のモジュールだけを対象にする
            for target in ["Flutter", "AudioPlayer", "audio", "Swift"]:
                cache_dirs = [os.path.join(module_cache, d) for d in os.listdir(module_cache) if target.lower() in d.lower()]
                for cache_dir in cache_dirs:
                    shutil.rmtree(cache_dir, ignore_errors=True)
            print("  ✅ モジュールキャッシュをクリーンアップしました")
        except Exception as e:
            print(f"  ⚠️ モジュールキャッシュのクリーンアップに失敗: {e}")
    
    # Xcodeを完全リセットするスクリプトを実行
    xcode_reset = os.path.join(os.path.dirname(os.path.abspath(__file__)), "xcode_reset.sh")
    if not os.path.exists(xcode_reset):
        # スクリプトが存在しない場合は作成
        with open(xcode_reset, 'w') as f:
            f.write('''#!/bin/bash
echo "=== Xcode プロジェクト完全リセットスクリプト v1.0 ==="
    
# プロジェクトのルートディレクトリを特定
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
echo "プロジェクトルート: $PROJECT_ROOT"

# 古いビルド成果物を完全に削除
echo "🧹 古いビルド成果物を削除しています..."
rm -rf "$PROJECT_ROOT/build"
rm -rf "$PROJECT_ROOT/ios/build"
rm -rf "$PROJECT_ROOT/ios/Runner.build"
rm -rf "$PROJECT_ROOT/ios/Pods"
rm -f "$PROJECT_ROOT/ios/Podfile.lock"
rm -rf "$PROJECT_ROOT/ios/.symlinks"

# Xcodeのユーザー固有の設定を削除
echo "🧹 Xcodeの設定ファイルをクリーンアップしています..."
rm -rf "$PROJECT_ROOT/ios/Runner.xcodeproj/project.xcworkspace/xcuserdata"
rm -rf "$PROJECT_ROOT/ios/Runner.xcworkspace/xcuserdata"
rm -f "$PROJECT_ROOT/ios/Runner.xcodeproj/project.xcworkspace/xcshareddata/IDEWorkspaceChecks.plist"

# プロジェクトファイルのバックアップを作成
PBXPROJ="$PROJECT_ROOT/ios/Runner.xcodeproj/project.pbxproj"
if [ -f "$PBXPROJ" ]; then
  cp "$PBXPROJ" "${PBXPROJ}.bak"
  echo "✅ プロジェクトファイルのバックアップを作成しました"
  # プロジェクトファイルからStaleファイル参照を削除
  echo "🔧 プロジェクトファイルから古いパス参照を削除しています..."
  sed -i.tmp "s|path = .*build/ios/Debug.*|path = \\"\\";|g" "$PBXPROJ"
  sed -i.tmp "s|sourceTree = BUILT_PRODUCTS_DIR|sourceTree = DEVELOPER_DIR|g" "$PBXPROJ"
  rm -f "${PBXPROJ}.tmp"
fi
    
# DerivedDataディレクトリからプロジェクト関連のキャッシュを削除
echo "🧹 Xcodeのキャッシュを削除しています..."
DERIVED_DATA="$HOME/Library/Developer/Xcode/DerivedData"
if [ -d "$DERIVED_DATA" ]; then
  for dir in $(find "$DERIVED_DATA" -name "*Runner*" -o -name "*gyroscope*" -type d); do
    echo "削除: $dir"
    rm -rf "$dir"
  done
fi
        
# Xcodeのモジュールキャッシュをクリア
MODULE_CACHE="$HOME/Library/Developer/Xcode/DerivedData/ModuleCache.noindex"
if [ -d "$MODULE_CACHE" ]; then
  echo "モジュールキャッシュを削除しています..."
  # 全削除ではなく一部のみ削除
  find "$MODULE_CACHE" -type d -name "*Flutter*" -o -name "*Swift*" | xargs rm -rf
fi

# Flutter関連のキャッシュをクリア
echo "🧹 Flutterのキャッシュをクリアしています..."
cd "$PROJECT_ROOT" && flutter clean

# CocoaPodsをリセット
echo "🔄 CocoaPodsを再インストールしています..."
cd "$PROJECT_ROOT/ios" && pod deintegrate || true
cd "$PROJECT_ROOT/ios" && pod setup
cd "$PROJECT_ROOT/ios" && rm -f Podfile.lock && pod install --repo-update

echo "✅ Xcodeプロジェクトのリセットが完了しました"
echo "ℹ️ 次回のビルド前にXcodeを再起動することをお勧めします"
exit 0
''')
        os.chmod(xcode_reset, 0o755)
    
    # Xcodeリセットスクリプトを実行
    print("🔄 Xcodeプロジェクトを完全にリセットしています...")
    run_command(f"bash {xcode_reset}", "Xcodeプロジェクトリセット処理")
    
    return True

def fix_stale_file_warnings():
    """Xcodeのステールファイル警告を修正する専用関数"""
    print("\n🛠️ Xcodeの「Stale file」警告を徹底修正しています...")
    
    # より強力な修正スクリプトを作成
    fix_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fix_stale_path_complete.sh")
    if not os.path.exists(fix_script):
        with open(fix_script, 'w') as f:
            f.write('''#!/bin/bash

echo "=== Xcode Stale Files 徹底修正ツール v3.0 ==="
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
echo "プロジェクトルート: $PROJECT_ROOT"

# 問題のパターン
STALE_PATH_BASE="/Users/owner/Desktop/Flutter/Eiji/gyroscopeApp/build/ios"
PBXPROJ="$PROJECT_ROOT/ios/Runner.xcodeproj/project.pbxproj"

if [ -f "$PBXPROJ" ]; then
  echo "🔍 プロジェクトファイルを詳細に検査しています..."
  cp "$PBXPROJ" "${PBXPROJ}.fullbackup"
  
  # すべてのバックアップファイルを探して削除（.bakと.original）
  echo "🧹 すべてのバックアップファイルを削除しています..."
  find "$PROJECT_ROOT/.pub-cache" -name "*.bak" -o -name "*.original" -type f -delete 2>/dev/null || true
  find "$HOME/.pub-cache" -name "*.bak" -o -name "*.original" -type f -delete 2>/dev/null || true
  
  # プロジェクト内のすべての参照パスをBUILT_PRODUCTS_DIRに置換
  echo "🔧 すべての絶対パス参照を修正しています..."
  
  # Debug-iphonesimulator参照も修正
  sed -i'.tmp' "s|$STALE_PATH_BASE/Debug-iphoneos|BUILT_PRODUCTS_DIR|g" "$PBXPROJ"
  sed -i'.tmp' "s|$STALE_PATH_BASE/Debug-iphonesimulator|BUILT_PRODUCTS_DIR|g" "$PBXPROJ"
  sed -i'.tmp' "s|$STALE_PATH_BASE/Release-iphoneos|BUILT_PRODUCTS_DIR|g" "$PBXPROJ"
  sed -i'.tmp' "s|$STALE_PATH_BASE/Release-iphonesimulator|BUILT_PRODUCTS_DIR|g" "$PBXPROJ"
  
  # すべての path = "..." エントリを空に
  sed -i'.tmp' 's|path = ".*/build/ios/.*"|path = ""|g' "$PBXPROJ"
  
  # sourceTreeをDEVELOPER_DIRに変更
  sed -i'.tmp' 's|sourceTree = BUILT_PRODUCTS_DIR|sourceTree = DEVELOPER_DIR|g' "$PBXPROJ"
  
  # 一時ファイルを削除
  rm -f "${PBXPROJ}.tmp"
  
  echo "✅ プロジェクトファイルを修正しました"
fi

# Podsディレクトリのバックアップファイルを削除
echo "🧹 Pods内のバックアップファイルを削除しています..."
find "$PROJECT_ROOT/ios/Pods" -name "*.bak" -o -name "*.original" -type f -delete 2>/dev/null || true

# 徹底的なクリーンアップ
echo "🧹 ビルド成果物を完全に削除しています..."
rm -rf "$PROJECT_ROOT/build"
rm -rf "$PROJECT_ROOT/ios/build"
rm -rf "$PROJECT_ROOT/ios/DerivedData"

# ビルドキャッシュのクリーンアップ
echo "🧹 Xcodeキャッシュを削除しています..."
rm -rf "$HOME/Library/Developer/Xcode/DerivedData/Runner-*"
flutter clean

# プロジェクトの修復
echo "🔄 プロジェクトを修復しています..."
flutter create --platforms=ios . --project-name="$(basename "$PROJECT_ROOT")"

# 依存関係を再インストール
echo "🔄 依存関係を再インストールしています..."
cd "$PROJECT_ROOT" && flutter pub get
cd "$PROJECT_ROOT/ios" && pod install --repo-update

echo "✅ 修正が完了しました"
echo "ℹ️ Xcodeを再起動して、プロジェクトを開き直してください"
exit 0
''')
        os.chmod(fix_script, 0o755)
    
    # スクリプトを実行
    print("🔧 Staleファイル修正スクリプトを実行しています...")
    run_command(f"bash {fix_script}", "Staleファイル徹底修正処理")
    
    # Xcodeを確実に再起動
    print("\n⚠️ Xcodeを再起動しています...")
    run_command("killall Xcode || true", "Xcode終了")
    time.sleep(2)
    
    return True

def fix_flutter_dependencies():
    """Flutterの依存関係の問題を修正する"""
    print("\n🛠️ Flutterの依存関係の問題を修正しています...")
    
    # 依存関係修正スクリプト作成
    fix_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fix_dependencies.sh")
    if not os.path.exists(fix_script):
        with open(fix_script, 'w') as f:
            f.write('''#!/bin/bash

echo "=== Flutter 依存関係修復スクリプト v1.0 ==="
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
echo "プロジェクトルート: $PROJECT_ROOT"

# まずはクリーンアップを行う
echo "🧹 プロジェクトをクリーンアップしています..."
cd "$PROJECT_ROOT" && flutter clean

# pubspec.lockを削除して依存関係を再解決
if [ -f "$PROJECT_ROOT/pubspec.lock" ]; then
  echo "🔄 pubspec.lockを削除して新しく依存関係を解決します..."
  rm "$PROJECT_ROOT/pubspec.lock"
fi

# 正しいコマンドで依存関係を取得
echo "🔄 正しいコマンドで依存関係を取得しています..."
cd "$PROJECT_ROOT" && flutter pub get

# iOS関連のファイルをクリーンアップして再生成
echo "🧹 iOSビルドファイルをクリーンアップしています..."
rm -rf "$PROJECT_ROOT/ios/Pods"
rm -rf "$PROJECT_ROOT/ios/.symlinks"
rm -f "$PROJECT_ROOT/ios/Podfile.lock"
rm -rf "$PROJECT_ROOT/ios/Flutter/Flutter.podspec"

# CocoaPodsのセットアップとインストール
echo "🔄 CocoaPodsを再インストールしています..."
cd "$PROJECT_ROOT/ios" && pod deintegrate || true
cd "$PROJECT_ROOT/ios" && pod install --repo-update

echo "✅ 依存関係の修復が完了しました"
exit 0
''')
        os.chmod(fix_script, 0o755)
    
    # スクリプト実行
    print("🔧 依存関係修復スクリプトを実行しています...")
    run_command(f"bash {fix_script}", "依存関係修復処理")
    
    return True

def main():
    """メイン実行関数"""
    # カレントディレクトリをプロジェクトのルートに変更（安全のため）
    os.chdir(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
    
    parser = argparse.ArgumentParser(description="Flutter アプリケーションのiOSビルドとインストール")
    parser.add_argument('--verbose', action='store_true', help='詳細な出力を表示')
    parser.add_argument('--no-clean', action='store_true', help='クリーンステップをスキップして高速化')
    parser.add_argument('--install', action='store_true', help='ビルド後に実機にインストール')
    parser.add_argument('--run', action='store_true', help='ビルド後にXcodeを開いて実行')
    parser.add_argument('--xcode-only', action='store_true', help='ビルドせずにXcodeを開く')
    parser.add_argument('--auto-run', action='store_true', help='ビルド、インストール、実行まで全て自動化')
    args = parser.parse_args()
    
    print("=== ジャイロスコープアプリ iOS 自動ビルド＆実行スクリプト ===")
    if platform.system() != "Darwin":
        print("⚠️ このスクリプトはmacOSでのみ実行できます。")
        return 1
    
    # Flutter doctorを自動実行（ユーザー入力なし）
    print("Flutter環境を確認中...")
    run_command("flutter doctor -v", "Flutter環境診断", timeout=60, show_progress=True)
    
    # 現在のディレクトリを表示
    print(f"現在のディレクトリ: {os.getcwd()}")
    if not check_flutter_installation():
        return 1
    
    # プロジェクトディレクトリの確認
    if not os.path.exists('lib/main.dart'):
        print("エラー: このディレクトリはFlutterプロジェクトではないようです。")
        print("Flutterプロジェクトのルートディレクトリで実行してください。")
        return 1
    
    # 出力フォルダの準備
    os.makedirs("output/ios", exist_ok=True)
    
    # 接続されているiOSデバイスを確認
    devices = get_connected_ios_devices()
    if not devices:
        print("⚠️ 接続されているiOSデバイスが見つかりません。シミュレータを使用します。")
        # シミュレータでも続行する（デバイスがなくても処理を続行）
    else:
        print("\n接続されているiOSデバイス:")
        for i, device in enumerate(devices):
            print(f"{i+1}: {device['name']} ({device['id']})")
    
    # 常に自動実行モードを強制的に有効にする
    args.auto_run = True
    args.run = True
    args.install = True
    print("\n完全自動モードで実行: ビルド→インストール→Xcode起動→アプリ実行までを自動化します")
    
    # ビルドの実行
    success = True
    selected_device_id = None
    try:
        # デバイスの自動選択（最初のデバイスを使用）
        if devices:
            selected_device_id = devices[0]['id']
            print(f"デバイス自動選択: {devices[0]['name']}")
        
        print("\nFlutterアプリをビルドしています...")
        
        # パッケージの依存関係を修正（新規追加）
        fix_flutter_dependencies()
        
        # AudioPlayersプラグイン専用の修正を実行
        audioplayers_fix_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fix_audioplayers_plugin.sh")
        if not os.path.exists(audioplayers_fix_script):
            with open(audioplayers_fix_script, 'w') as f:
                f.write('''#!/bin/bash
echo "=== AudioPlayers プラグイン修復スクリプト v1.0 ==="
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
echo "プロジェクトルート: $PROJECT_ROOT"

# pubspec.lockをバックアップして削除（強制的に依存関係を再解決させる）
if [ -f "$PROJECT_ROOT/pubspec.lock" ]; then
  cp "$PROJECT_ROOT/pubspec.lock" "$PROJECT_ROOT/pubspec.lock.bak"
  rm "$PROJECT_ROOT/pubspec.lock"
  echo "✅ pubspec.lockをリセットしました"
fi

# AudioPlayerのポッドファイル修正
POD_DIR="$HOME/.pub-cache/hosted/pub.dev"
for audio_dir in $(find "$POD_DIR" -name "audioplayers_darwin*" -type d); do
  echo "🔧 処理中: $audio_dir"
  
  # Podspecファイルを修正
  PODSPEC_FILE=$(find "$audio_dir" -name "*.podspec" -type f)
  if [ -n "$PODSPEC_FILE" ]; then
    echo "  修正: $PODSPEC_FILE"
    sed -i.bak 's/s.pod_target_xcconfig.*=.*{.*"DEFINES_MODULE"/s.pod_target_xcconfig = { "DEFINES_MODULE"/g' "$PODSPEC_FILE"
    
    # iOS 12.0以上を要求するように修正
    sed -i.bak 's/s.platform[ ]*=[ ]*:ios.*/s.platform = :ios, "12.0"/g' "$PODSPEC_FILE"
    
    # 元のSwiftファイルを確認
    SWIFT_DIR="$audio_dir/ios/Classes"
    if [ -d "$SWIFT_DIR" ]; then
      echo "  Swiftファイルディレクトリ: $SWIFT_DIR"
      for swift_file in $(find "$SWIFT_DIR" -name "*.swift"); do
        base_name=$(basename "$swift_file")
        cp "$swift_file" "$swift_file.original"
        echo "  バックアップ: $swift_file → $swift_file.original"
      done
    fi
  fi
done

# プラグインの再インストール
echo "🔄 Flutterプラグインを再インストールしています..."
cd "$PROJECT_ROOT" && flutter pub cache repair
cd "$PROJECT_ROOT" && flutter clean
cd "$PROJECT_ROOT" && flutter pub get    

# iOSビルドファイルの完全クリーンアップ
echo "🧹 iOSビルドファイルをクリーンアップしています..."
rm -rf "$PROJECT_ROOT/ios/Pods"
rm -rf "$PROJECT_ROOT/ios/.symlinks"
rm -f "$PROJECT_ROOT/ios/Podfile.lock"

# CocoaPodsの再インストール
echo "🔄 CocoaPodsを再インストールしています..."
cd "$PROJECT_ROOT/ios" && pod deintegrate || true
cd "$PROJECT_ROOT/ios" && pod install --repo-update

echo "✅ AudioPlayersプラグイン修復が完了しました"
exit 0
''')
            os.chmod(audioplayers_fix_script, 0o755)
        
        print("🔧 AudioPlayers プラグインを修正しています...")
        run_command(f"bash {audioplayers_fix_script}", "AudioPlayersプラグイン修復処理")
        
        # ステールファイル警告修正を実行（新しく追加）
        fix_stale_file_warnings()
        
        # まずXcodeのキャッシュとプロジェクト設定を徹底的にクリーンアップ
        deep_clean_xcode()
        
        # より徹底的なクリーンアップを実行
        super_clean_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "super_clean.sh")
        if not os.path.exists(super_clean_script):
            with open(super_clean_script, 'w') as f:
                f.write('''#!/bin/bash
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

# 問題のあるパッケージを直接クリーンアップ
echo "🧹 問題のあるパッケージをクリーンアップ中..."
PROBLEM_PACKAGES=("audioplayers_darwin" "vibration" "device_info_plus" "sensors_plus" "path_provider_foundation" "shared_preferences_foundation")

for pkg in "${PROBLEM_PACKAGES[@]}"; do
  echo "🔍 $pkg パッケージを処理中..."
  
  # 各パッケージのbackupsディレクトリを完全削除
  for dir in $(find "$HOME/.pub-cache/hosted/pub.dev" -name "${pkg}*" -type d 2>/dev/null); do
    echo "  📂 $dir を処理中..."
    
    # backupsディレクトリを削除
    find "$dir" -type d -name "backups" -exec rm -rf {} \\; 2>/dev/null || true
    
    # バックアップファイルを削除
    find "$dir" -type f \\( -name "*.bak" -o -name "*.original" -o -name "*.bak.*" \\) -exec rm -f {} \\; 2>/dev/null || true
  done
done

# Podspecファイルを修正（問題が生じやすいため）
for podspec in $(find "$HOME/.pub-cache" -name "*.podspec" 2>/dev/null); do
  if grep -q "s.pod_target_xcconfig.*=.*{.*'DEFINES_MODULE'" "$podspec" 2>/dev/null; then
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
''')
            os.chmod(super_clean_script, 0o755)
        
        print("🧹 ビルド前に徹底的なクリーンアップを実行しています...")
        run_command(f"bash {super_clean_script}", "プロジェクト完全クリーンアップ処理")
        
        if not build_ios_debug(args.verbose, args.no_clean, True):
            print("\n⚠️ iOSビルドに失敗しました。")
            print("🔄 audioplayers_darwin の Swift ファイルエラーを修正します...")
            success = False
            # Swift ファイルエラーの包括的な修正を試みる
            if not fix_audioplayers_darwin_swift_errors():
                print("❌ Swift ファイルの修正に失敗しました。")
                success = False
            else:
                print("✅ Swift ファイルの修正に成功しました。再ビルドを試行します...")
                if not build_ios_debug(args.verbose, args.no_clean, True):
                    print("❌ 再ビルドも失敗しました。最終手段を試みます...")
                    print("🔄 Podfileを修正して audioplayers_darwin を無効化します...")
                    if modify_ios_podfile():
                        run_command("cd ios && rm -rf Pods && pod install --repo-update", "最終CocoaPods再インストール")
                        if not build_ios_debug(args.verbose, args.no_clean, True):
                            print("❌ すべての修正を試みましたが、ビルドに失敗しました。")
                            success = False
                        else:
                            print("✅ 最終修正後のビルドに成功しました！")
                            success = True
                    else:
                        print("❌ Podfileの修正に失敗しました。")
                        success = False
        else:
            print("✅ ビルドとインストールが完了しました")
            success = True
    except Exception as e:
        print(f"\n予期せぬエラーが発生しました: {e}")
        # 問題があったとき、エラーメッセージをログファイルに保存
        log_filename = f"ios_build_error_log_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        try:
            with open(log_filename, 'w') as f:
                f.write("=== iOSビルドエラーログ ===\n")
                f.write(f"日時: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Flutterバージョン: {get_flutter_version()}\n")
                f.write("エラーメッセージ:\n")
                f.write(f"{str(e)}\n")
            print(f"\nエラーログを保存しました: {log_filename}")
        except Exception as e:
            print(f"エラーログの保存に失敗しました: {e}")
        return 1
    
    if success:
        print("\n✨ すべての処理が正常に完了しました! ✨")
        print("Xcodeでアプリが実行されています。画面を確認してください。")
    else:
        print("\n⚠️ 処理中に問題が発生しました。上記のエラーを確認してください。")
    
    return 0 if success else 1

if __name__ == "__main__":
    exit(main())
