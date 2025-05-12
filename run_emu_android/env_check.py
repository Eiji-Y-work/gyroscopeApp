#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import platform
import shutil
import re
import subprocess  # 追加: subprocess モジュールをインポート
from utils import run_command, get_flutter_version

def check_flutter_installation():
    """Flutter SDKのインストールを確認する"""
    flutter_path = shutil.which("flutter")
    if not flutter_path:
        print("Flutterが見つかりません。Flutterがインストールされ、PATHに追加されていることを確認してください。")
        return False
    
    print(f"Flutter確認済み:")
    flutter_version = get_flutter_version()
    print(flutter_version)
    return True

def setup_android_paths():
    """Android関連のパスを環境変数に設定し、必要に応じてシンボリックリンクを作成する"""
    print("\n🔧 Android開発環境のパスを設定しています...")
    
    # ANDROID_HOME または ANDROID_SDK_ROOT 環境変数をチェック
    android_home = os.environ.get('ANDROID_HOME') or os.environ.get('ANDROID_SDK_ROOT')
    
    if not android_home:
        # macOSならデフォルトの場所をチェック
        if platform.system() == "Darwin":
            default_paths = [
                os.path.expanduser('~/Library/Android/sdk'),
                '/Applications/Android Studio.app/Contents/sdk'
            ]
            for path in default_paths:
                if os.path.exists(path):
                    android_home = path
                    break
        # Windowsならデフォルトの場所をチェック
        elif platform.system() == "Windows":
            default_paths = [
                os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Android/Sdk'),
                os.path.join(os.environ.get('APPDATA', ''), 'Local/Android/Sdk')
            ]
            for path in default_paths:
                if os.path.exists(path):
                    android_home = path
                    break
    
    if not android_home:
        print("⚠️ Android SDKが見つかりません")
        return False
    
    os.environ['ANDROID_HOME'] = android_home
    os.environ['ANDROID_SDK_ROOT'] = android_home
    
    # 必要なディレクトリをPATHに追加
    path_dirs = [
        os.path.join(android_home, 'platform-tools'),
        os.path.join(android_home, 'tools'),
        os.path.join(android_home, 'tools/bin'),
        os.path.join(android_home, 'emulator')
    ]
    
    # 既存のPATHを取得
    current_path = os.environ.get('PATH', '')
    
    # パスを修正・更新
    updated = False
    for directory in path_dirs:
        if os.path.exists(directory) and directory not in current_path:
            os.environ['PATH'] = directory + os.pathsep + os.environ['PATH']
            print(f"✅ PATHに追加しました: {directory}")
            updated = True
    
    # PATHの更新を反映する試み（現在のプロセスのみに影響）
    os.environ['PATH'] = os.environ['PATH'].replace(";;", ";").replace("::", ":")
    
    # ホームディレクトリにシンボリックリンクを作成
    try:
        home_dir = os.path.expanduser('~')
        android_sdk_link = os.path.join(home_dir, 'android-sdk')
        if not os.path.exists(android_sdk_link) and platform.system() != "Windows":
            os.symlink(android_home, android_sdk_link)
            print(f"✅ シンボリックリンクを作成しました: {android_sdk_link} → {android_home}")
    except Exception as e:
        print(f"⚠️ シンボリックリンク作成中にエラーが発生しました: {e}")
    
    # adbとemulatorが直接実行可能かチェック
    adb_path = shutil.which("adb")
    if adb_path:
        print(f"✅ adbパス: {adb_path}")
    else:
        # 直接パスを探す
        direct_adb_path = os.path.join(android_home, 'platform-tools', 'adb')
        direct_adb_path_exe = os.path.join(android_home, 'platform-tools', 'adb.exe')
        if os.path.exists(direct_adb_path):
            print(f"✅ adbの直接パス: {direct_adb_path}")
        elif os.path.exists(direct_adb_path_exe):
            print(f"✅ adbの直接パス: {direct_adb_path_exe}")
        else:
            print("⚠️ adbが見つかりません")
            return False
    
    emulator_path = shutil.which("emulator")
    if emulator_path:
        print(f"✅ emulatorパス: {emulator_path}")
    else:
        direct_emulator_path = os.path.join(android_home, 'emulator', 'emulator')
        direct_emulator_path_exe = os.path.join(android_home, 'emulator', 'emulator.exe')
        if os.path.exists(direct_emulator_path):
            print(f"✅ emulatorの直接パス: {direct_emulator_path}")
        elif os.path.exists(direct_emulator_path_exe):
            print(f"✅ emulatorの直接パス: {direct_emulator_path_exe}")
        else:
            print("⚠️ emulatorが見つかりません")
    
    return True

def check_android_sdk():
    """Android SDKのインストールを確認し、パスを設定する"""
    # ANDROID_HOME または ANDROID_SDK_ROOT 環境変数をチェック
    android_home = os.environ.get('ANDROID_HOME') or os.environ.get('ANDROID_SDK_ROOT')
    
    if not android_home:
        # macOSならデフォルトの場所をチェック
        if platform.system() == "Darwin":
            default_paths = [
                os.path.expanduser('~/Library/Android/sdk'),
                '/Applications/Android Studio.app/Contents/sdk'
            ]
            for path in default_paths:
                if os.path.exists(path):
                    android_home = path
                    break
        # Windowsならデフォルトの場所をチェック
        elif platform.system() == "Windows":
            default_paths = [
                os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Android/Sdk'),
                os.path.join(os.environ.get('APPDATA', ''), 'Local/Android/Sdk')
            ]
            for path in default_paths:
                if os.path.exists(path):
                    android_home = path
                    break
    
    if not android_home or not os.path.exists(android_home):
        print("⚠️ Android SDKが見つかりません。Android Studioをインストールして、環境変数を設定してください。")
        return False
    
    # 一般的なAndroid SDK構成要素のチェック
    sdk_components = {
        'platform-tools': os.path.join(android_home, 'platform-tools'),
        'tools': os.path.join(android_home, 'tools'),
        'emulator': os.path.join(android_home, 'emulator')
    }
    
    for name, path in sdk_components.items():
        if not os.path.exists(path):
            print(f"⚠️ Android SDK {name}が見つかりません: {path}")
            if name == 'emulator':
                return False
    
    # adb コマンドがPATHにあるかチェック
    adb_path = shutil.which("adb")
    if not adb_path:
        print("⚠️ adbがPATHに設定されていません。Android Studioの設定を確認してください。")
        # それでも続行はできるようにする
    else:
        print(f"✅ adbパス: {adb_path}")
    
    # エミュレータコマンドがPATHにあるかチェック
    emulator_path = shutil.which("emulator")
    if not emulator_path:
        # 直接パスを探す
        if os.path.exists(os.path.join(android_home, 'emulator', 'emulator')):
            emulator_path = os.path.join(android_home, 'emulator', 'emulator')
            print(f"⚠️ emulatorがPATHに設定されていません。直接パスを使用します: {emulator_path}")
            os.environ['PATH'] = os.environ['PATH'] + os.pathsep + os.path.dirname(emulator_path)
        else:
            print("⚠️ emulatorコマンドが見つかりません。Android SDK Emulatorがインストールされているか確認してください。")
            return False
    else:
        print(f"✅ emulatorパス: {emulator_path}")
    
    print(f"✅ Android SDK確認済み: {android_home}")
    
    # パスの設定を自動的に行う
    setup_android_paths()
    
    return True

def find_installed_ndk_version():
    """インストールされているNDKのバージョンを取得する"""
    print("🔍 インストール済みのNDKバージョンを確認中...")
    
    # ANDROID_HOME または ANDROID_SDK_ROOT 環境変数をチェック
    android_home = os.environ.get('ANDROID_HOME') or os.environ.get('ANDROID_SDK_ROOT')
    
    if not android_home:
        # macOSならデフォルトの場所をチェック
        if platform.system() == "Darwin":
            default_paths = [
                os.path.expanduser('~/Library/Android/sdk'),
                '/Applications/Android Studio.app/Contents/sdk'
            ]
            for path in default_paths:
                if os.path.exists(path):
                    android_home = path
                    break
    
    if not android_home:
        print("⚠️ Android SDKディレクトリが見つかりません")
        return None

    # NDKディレクトリを確認
    ndk_dir = os.path.join(android_home, 'ndk')
    if not os.path.exists(ndk_dir):
        print(f"⚠️ NDKディレクトリが見つかりません: {ndk_dir}")
        return None
    
    # インストールされているNDKバージョンを検索
    try:
        ndk_versions = [d for d in os.listdir(ndk_dir) if os.path.isdir(os.path.join(ndk_dir, d))]
        if not ndk_versions:
            print("⚠️ NDKバージョンが見つかりません")
            return None
        
        # 最新のNDKバージョンを返す（通常はソート順で最後のもの）
        latest_version = sorted(ndk_versions)[-1]
        print(f"✅ インストール済みNDKバージョン: {latest_version}")
        return latest_version
    except Exception as e:
        print(f"⚠️ NDKバージョンの確認中にエラーが発生しました: {e}")
        return None

def check_project_directory():
    """プロジェクトディレクトリの確認"""
    if not os.path.exists('lib/main.dart'):
        print("エラー: このディレクトリはFlutterプロジェクトではないようです。")
        print("Flutterプロジェクトのルートディレクトリで実行してください。")
        return False
    return True

def ensure_adb_available():
    """ADBが確実に利用可能になるように設定する"""
    print("\n🔍 ADBの可用性を確認して強制設定しています...")
    
    # adbパスを確認
    adb_path = shutil.which("adb")
    
    if not adb_path:
        # デフォルトの場所から直接探す
        android_home = os.environ.get('ANDROID_HOME') or os.environ.get('ANDROID_SDK_ROOT')
        if android_home:
            potential_paths = [
                os.path.join(android_home, 'platform-tools', 'adb'),
                os.path.join(android_home, 'platform-tools', 'adb.exe')
            ]
            
            for path in potential_paths:
                if os.path.exists(path):
                    adb_path = path
                    print(f"✅ ADBを見つけました: {adb_path}")
                    
                    # utils.pyのrun_commandをオーバーライドしてADBパスを強制的に使用
                    original_run_command = run_command
                    
                    def adb_aware_run_command(cmd, description="", timeout=None, show_output=True, show_progress=False):
                        """ADBパスを置き換えた実行コマンド"""
                        # コマンドがadbで始まる場合、絶対パスで置換
                        if cmd.startswith('adb '):
                            cmd = f'"{adb_path}" {cmd[4:]}'
                            print(f"🔄 ADBコマンドを書き換えました: {cmd}")
                        return original_run_command(cmd, description, timeout, show_output, show_progress)
                    
                    # グローバル関数を置き換え
                    import utils
                    utils.run_command = adb_aware_run_command
                    
                    # emulator.pyでも置き換え
                    try:
                        import emulator
                        emulator.run_command = adb_aware_run_command
                    except:
                        pass
                    
                    # build.pyでも置き換え
                    try:
                        import build
                        build.run_command = adb_aware_run_command
                    except:
                        pass
                    
                    break
    
    if not adb_path:
        print("⚠️ ADBが見つかりません。以下のパスでインストールされている可能性があります：")
        print("  - macOS: ~/Library/Android/sdk/platform-tools/adb")
        print("  - Windows: %LOCALAPPDATA%\\Android\\sdk\\platform-tools\\adb.exe")
        print("  - Linux: ~/Android/Sdk/platform-tools/adb")
        print("Android SDKが適切にインストールされていることを確認してください。")
    else:
        print(f"✅ ADBを使用可能: {adb_path}")
        
        # 現在のPATHで使えるか確認
        result = subprocess.run("which adb" if platform.system() != "Windows" else "where adb", 
                               shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if result.returncode == 0:
            print(f"✅ システムPATHからもADBが見つかりました: {result.stdout.decode().strip()}")
        else:
            print(f"ℹ️ システムPATHからはADBが見つかりませんが、直接パスを使用して実行します")
    
    return adb_path is not None

def fix_android_gradle_settings():
    """Android Gradle設定の問題を修正する"""
    print("\n🔧 Android Gradle設定を修正しています...")
    
    # まずnamespaceの問題を修正
    fix_namespace_issue()
    
    # 次にKotlinバージョンの問題を修正
    fix_kotlin_version()
    
    return True

def fix_namespace_issue():
    """build.gradle.ktsファイルにnamespace設定を追加する"""
    print("\n🔧 namespace設定を修正しています...")
    
    # build.gradle.kts ファイルのパスを特定
    gradle_file = os.path.join(os.getcwd(), 'android', 'app', 'build.gradle.kts')
    if not os.path.exists(gradle_file):
        # 通常の build.gradle を探す
        gradle_file = os.path.join(os.getcwd(), 'android', 'app', 'build.gradle')
        if not os.path.exists(gradle_file):
            print("⚠️ Gradleファイルが見つかりません")
            return False
    
    # AndroidManifest.xmlからパッケージ名を取得
    manifest_file = os.path.join(os.getcwd(), 'android', 'app', 'src', 'main', 'AndroidManifest.xml')
    package_name = "com.example.app"  # デフォルト値
    
    if os.path.exists(manifest_file):
        try:
            with open(manifest_file, 'r') as f:
                manifest_content = f.read()
                package_match = re.search(r'package\s*=\s*["\']([^"\']+)["\']', manifest_content)
                if package_match:
                    package_name = package_match.group(1)
                    print(f"📦 AndroidManifestからパッケージ名を取得: {package_name}")
        except Exception as e:
            print(f"⚠️ AndroidManifestの読み取り中にエラー: {e}")
    else:
        print("ℹ️ AndroidManifestファイルが見つからないためデフォルトのパッケージ名を使用")
    
    # Gradle ファイルを編集して namespace を追加
    try:
        with open(gradle_file, 'r') as f:
            content = f.read()
        
        # バックアップ作成
        with open(f"{gradle_file}.bak", 'w') as f:
            f.write(content)
        print("💾 Gradleファイルのバックアップを作成")
        
        # すでに namespace が設定されているか確認
        if 'namespace' in content:
            print("✅ namespace は既に設定されています")
            return True
        
        # android ブロックを見つけて namespace を追加
        is_kts = gradle_file.endswith('.kts')
        
        if is_kts:
            # Kotlin DSL 形式
            new_content = re.sub(
                r'(android\s*\{)',
                f'\\1\n    namespace = "{package_name}"',
                content
            )
        else:
            # Groovy 形式
            new_content = re.sub(
                r'(android\s*\{)',
                f'\\1\n    namespace "{package_name}"',
                content
            )
        
        # 変更内容を保存
        with open(gradle_file, 'w') as f:
            f.write(new_content)
        
        print(f"✅ namespace を設定しました: {package_name}")
        return True
        
    except Exception as e:
        print(f"⚠️ Gradleファイルの修正中にエラーが発生: {e}")
        return False

def fix_kotlin_version():
    """Kotlin バージョンの互換性問題を修正する"""
    print("\n🔧 Kotlinバージョンを修正しています...")
    
    # rootプロジェクトのbuild.gradleファイル
    root_gradle_file = os.path.join(os.getcwd(), 'android', 'build.gradle')
    
    if not os.path.exists(root_gradle_file):
        print("⚠️ ルートGradleファイルが見つかりません")
        return False
    
    try:
        with open(root_gradle_file, 'r') as f:
            content = f.read()
        
        # バックアップ作成
        with open(f"{root_gradle_file}.bak", 'w') as f:
            f.write(content)
        print("💾 Gradleファイルのバックアップを作成しました")
        
        # Kotlinバージョンの更新（互換性のある値に）
        kotlin_version_pattern = r'(ext\.kotlin_version|kotlinVersion)\s*=\s*[\'"]([^\'"]+)[\'"]'
        if re.search(kotlin_version_pattern, content):
            new_content = re.sub(kotlin_version_pattern, r'\1 = "1.7.10"', content)
            with open(root_gradle_file, 'w') as f:
                f.write(new_content)
            print("✅ Kotlinバージョンを1.7.10に更新しました")
        else:
            # Kotlinバージョン設定がない場合は追加
            ext_block_pattern = r'(ext\s*\{)'
            if re.search(ext_block_pattern, content):
                new_content = re.sub(ext_block_pattern, r'\1\n        kotlin_version = "1.7.10"', content)
                with open(root_gradle_file, 'w') as f:
                    f.write(new_content)
                print("✅ Kotlinバージョン設定を追加しました")
            else:
                # extブロックがない場合は作成
                buildscript_pattern = r'(buildscript\s*\{)'
                if re.search(buildscript_pattern, content):
                    ext_block = """
    ext {
        kotlin_version = '1.7.10'
    }
"""
                    # 修正: f-stringとraw文字列の組み合わせを避ける
                    new_content = re.sub(buildscript_pattern, r'\1' + ext_block, content)
                    with open(root_gradle_file, 'w') as f:
                        f.write(new_content)
                    print("✅ extブロックとKotlinバージョン設定を追加しました")
                else:
                    print("⚠️ buildscriptブロックが見つかりません")
        
        return True
    except Exception as e:
        print(f"⚠️ Kotlinバージョン更新エラー: {e}")
        return False

def update_kotlin_plugin_version():
    """KotlinプラグインのバージョンをGradleファイルで更新する"""
    print("\n🔧 Kotlin Gradle Pluginを更新しています...")
    
    # android/build.gradle ファイルを探す
    root_gradle = os.path.join(os.getcwd(), 'android', 'build.gradle')
    root_gradle_kts = os.path.join(os.getcwd(), 'android', 'build.gradle.kts')
    
    gradle_file = root_gradle_kts if os.path.exists(root_gradle_kts) else root_gradle
    
    if not os.path.exists(gradle_file):
        print("⚠️ ルートGradleファイルが見つかりません")
        return False
    
    try:
        with open(gradle_file, 'r') as f:
            content = f.read()
        
        # kotlin-gradle-plugin の依存関係を探す
        kotlin_plugin_pattern = r'(classpath[^\n]*kotlin-gradle-plugin[^\n]*)[\'"]([^\'"]*)[\'"]\s*\)?'
        match = re.search(kotlin_plugin_pattern, content)
        
        if match:
            current = match.group(2)
            print(f"📋 現在のKotlin Gradle Plugin: {current}")
            
            # バージョンを 1.7.10 に更新
            new_content = re.sub(kotlin_plugin_pattern, r'\1"1.7.10")', content)
            
            with open(gradle_file, 'w') as f:
                f.write(new_content)
            print("✅ Kotlin Gradle Pluginを 1.7.10 に更新しました")
            
            # Gradleキャッシュをクリアして確実に反映させる
            clear_gradle_cache()
            
            return True
        else:
            print("⚠️ Kotlin Gradle Pluginの依存関係が見つかりません")
            return False
            
    except Exception as e:
        print(f"⚠️ Kotlin Gradle Plugin更新中にエラー: {e}")
        return False

def clear_gradle_cache():
    """Gradleキャッシュをクリアする"""
    print("\n🧹 Gradleキャッシュをクリアしています...")
    
    cache_dir = os.path.join(os.getcwd(), 'android', '.gradle')
    if os.path.exists(cache_dir):
        try:
            shutil.rmtree(cache_dir)
            print(f"✅ Gradleキャッシュを削除しました: {cache_dir}")
        except Exception as e:
            print(f"⚠️ キャッシュ削除中にエラー: {e}")
    
    # 念のためFlutterもクリーン
    try:
        run_command("flutter clean", "Flutter clean", show_output=True)
    except Exception as e:
        print(f"⚠️ Flutter clean中にエラー: {e}")

# 新規関数を追加
def perform_full_gradle_repair():
    """Android Gradleの問題を総合的に修復する"""
    print("\n🛠️ Android Gradleの問題を総合的に修復しています...")
    
    # 1. namespace設定の修正
    fix_gradle_namespace()
    
    # 2. Kotlinバージョンの修正
    fix_kotlin_version()
    
    # 3. Gradleプラグインのバージョン修正
    fix_gradle_plugin_version()
    
    # 4. Gradleのバージョン修正
    fix_gradle_wrapper_version()
    
    # 5. キャッシュとビルドディレクトリのクリア
    clear_all_caches()
    
    print("\n✅ Android Gradleの修復が完了しました")
    return True

def fix_gradle_namespace():
    """build.gradle.ktsファイルにnamespace設定を追加する"""
    # ...既存のコード...

def fix_kotlin_version():
    """Kotlin バージョンの互換性問題を修正する"""
    print("\n🔧 Kotlinバージョンを修正しています...")
    
    # rootプロジェクトのbuild.gradleファイル
    root_gradle_file = os.path.join(os.getcwd(), 'android', 'build.gradle')
    
    if not os.path.exists(root_gradle_file):
        print("⚠️ ルートGradleファイルが見つかりません")
        return False
    
    try:
        with open(root_gradle_file, 'r') as f:
            content = f.read()
        
        # バックアップ作成
        with open(f"{root_gradle_file}.bak", 'w') as f:
            f.write(content)
        print("💾 Gradleファイルのバックアップを作成しました")
        
        # Kotlinバージョンの更新（互換性のある値に）
        kotlin_version_pattern = r'(ext\.kotlin_version|kotlinVersion)\s*=\s*[\'"]([^\'"]+)[\'"]'
        if re.search(kotlin_version_pattern, content):
            new_content = re.sub(kotlin_version_pattern, r'\1 = "1.7.10"', content)
            with open(root_gradle_file, 'w') as f:
                f.write(new_content)
            print("✅ Kotlinバージョンを1.7.10に更新しました")
        else:
            # Kotlinバージョン設定がない場合は追加
            ext_block_pattern = r'(ext\s*\{)'
            if re.search(ext_block_pattern, content):
                new_content = re.sub(ext_block_pattern, r'\1\n        kotlin_version = "1.7.10"', content)
                with open(root_gradle_file, 'w') as f:
                    f.write(new_content)
                print("✅ Kotlinバージョン設定を追加しました")
            else:
                # extブロックがない場合は作成
                buildscript_pattern = r'(buildscript\s*\{)'
                if re.search(buildscript_pattern, content):
                    ext_block = """
    ext {
        kotlin_version = '1.7.10'
    }
"""
                    # 修正: f-stringとraw文字列の組み合わせを避ける
                    new_content = re.sub(buildscript_pattern, r'\1' + ext_block, content)
                    with open(root_gradle_file, 'w') as f:
                        f.write(new_content)
                    print("✅ extブロックとKotlinバージョン設定を追加しました")
                else:
                    print("⚠️ buildscriptブロックが見つかりません")
        
        return True
    except Exception as e:
        print(f"⚠️ Kotlinバージョン更新エラー: {e}")
        return False

def fix_gradle_plugin_version():
    """Android Gradle Pluginバージョンを修正する"""
    print("\n🔧 Android Gradle Pluginバージョンを修正しています...")
    
    root_gradle_file = os.path.join(os.getcwd(), 'android', 'build.gradle')
    
    if not os.path.exists(root_gradle_file):
        print("⚠️ Gradleファイルが見つかりません")
        return False
    
    try:
        with open(root_gradle_file, 'r') as f:
            content = f.read()
        
        # Android Gradle Plugin (AGP)のバージョンを更新
        agp_pattern = r'(classpath\s*[\'"]com\.android\.tools\.build:gradle:)([^\'"]*)[\'"]'
        if re.search(agp_pattern, content):
            # 安定版のAGPバージョンに更新（Flutter 3.29.xと互換性がある）
            new_content = re.sub(agp_pattern, r'\1' + '7.3.0' + r'"', content)
            with open(root_gradle_file, 'w') as f:
                f.write(new_content)
            print("✅ Android Gradle Pluginを7.3.0に更新しました")
            return True
        else:
            print("⚠️ Android Gradle Plugin依存関係が見つかりません")
            return False
    except Exception as e:
        print(f"⚠️ Gradle Plugin更新エラー: {e}")
        return False

def fix_gradle_wrapper_version():
    """Gradleラッパーのバージョンを修正する"""
    print("\n🔧 Gradleラッパーバージョンを修正しています...")
    
    # プロジェクトのGradleバージョンを指定したバージョンに更新
    gradle_version = "7.5"  # AGP 7.3.0 に対応するバージョン
    
    try:
        # gradleラッパーを更新
        cmd = f"cd {os.path.join(os.getcwd(), 'android')} && ./gradlew wrapper --gradle-version={gradle_version} --distribution-type=bin"
        result = subprocess.run(cmd, shell=True, capture_output=True)
        
        if result.returncode == 0:
            print(f"✅ Gradleラッパーを{gradle_version}に更新しました")
            return True
        else:
            print("⚠️ Gradleラッパー更新コマンドが失敗しました")
            print(f"エラー出力: {result.stderr.decode('utf-8') if result.stderr else 'なし'}")
            
            # 代替手段: gradle-wrapper.properties ファイルを直接編集
            props_file = os.path.join(os.getcwd(), 'android', 'gradle', 'wrapper', 'gradle-wrapper.properties')
            if os.path.exists(props_file):
                with open(props_file, 'r') as f:
                    content = f.read()
                
                # バージョン番号を更新
                new_content = re.sub(
                    r'distributionUrl=.*gradle-([0-9.]+)-.*\.zip',
                    f'distributionUrl=https\\://services.gradle.org/distributions/gradle-{gradle_version}-bin.zip',
                    content
                )
                
                with open(props_file, 'w') as f:
                    f.write(new_content)
                print(f"✅ gradle-wrapper.propertiesファイルを手動で{gradle_version}に更新しました")
                return True
            else:
                print("⚠️ gradle-wrapper.propertiesファイルが見つかりません")
                return False
    except Exception as e:
        print(f"⚠️ Gradleラッパー更新エラー: {e}")
        return False

def clear_all_caches():
    """全てのキャッシュとビルドディレクトリをクリアする"""
    print("\n🧹 全てのキャッシュとビルドディレクトリをクリアしています...")
    
    # Android ビルドディレクトリをクリア
    android_build_dir = os.path.join(os.getcwd(), 'android', 'build')
    if os.path.exists(android_build_dir):
        try:
            shutil.rmtree(android_build_dir)
            print(f"✅ Androidビルドディレクトリを削除: {android_build_dir}")
        except Exception as e:
            print(f"⚠️ ビルドディレクトリ削除エラー: {e}")
    
    # Android アプリのビルドディレクトリをクリア
    app_build_dir = os.path.join(os.getcwd(), 'android', 'app', 'build')
    if os.path.exists(app_build_dir):
        try:
            shutil.rmtree(app_build_dir)
            print(f"✅ アプリビルドディレクトリを削除: {app_build_dir}")
        except Exception as e:
            print(f"⚠️ アプリビルドディレクトリ削除エラー: {e}")
    
    # Gradle キャッシュをクリア
    gradle_cache_dir = os.path.join(os.getcwd(), 'android', '.gradle')
    if os.path.exists(gradle_cache_dir):
        try:
            shutil.rmtree(gradle_cache_dir)
            print(f"✅ Gradleキャッシュを削除: {gradle_cache_dir}")
        except Exception as e:
            print(f"⚠️ Gradleキャッシュ削除エラー: {e}")
    
    # Flutter ビルドディレクトリをクリア
    try:
        run_command("flutter clean", "Flutterクリーン", show_output=True)
        run_command("flutter pub get", "Flutterパッケージ再取得", show_output=True)
        print("✅ Flutterビルドをクリーンにしました")
    except Exception as e:
        print(f"⚠️ Flutterクリーンエラー: {e}")
    
    return True

# 関数をインポートするための定義を追加

def emergency_gradle_repair():
    """緊急Gradle修復を実行する"""
    try:
        # 緊急修復モジュールを動的にインポート
        import sys
        import os
        
        # emergency_gradle_repair.pyのパスを取得
        script_dir = os.path.dirname(os.path.realpath(__file__))
        emergency_module_path = os.path.join(script_dir, 'emergency_gradle_repair.py')
        
        if os.path.exists(emergency_module_path):
            # モジュールが見つかった場合は直接インポート
            sys.path.append(script_dir)
            from emergency_gradle_repair import emergency_gradle_repair as er
            return er()
        else:
            # モジュールが見つからない場合はその場で作成
            print("\n⚠️ 緊急修復モジュールが見つかりません。作成します...")
            with open(emergency_module_path, 'w') as f:
                f.write('''#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import shutil
import subprocess
import re

def emergency_gradle_repair():
    """Gradle関連の問題を緊急修復する（直接ファイルを置換）"""
    print("\\n🚨 Gradleの緊急修復を実行しています...")
    
    # プロジェクトのルートディレクトリ
    project_dir = os.getcwd()
    android_dir = os.path.join(project_dir, 'android')
    
    # 1. すべてのキャッシュをクリア
    clear_caches(android_dir)
    
    # 2. 互換性のあるGradleラッパーを強制的に使用
    fix_gradle_wrapper(android_dir)
    
    # 3. build.gradleファイルを修正
    fix_root_build_gradle(android_dir)
    
    # 4. アプリのbuild.gradle.ktsを修正
    fix_app_build_gradle(android_dir)
    
    # 5. local.propertiesを確認・修正
    fix_local_properties(android_dir)
    
    # 6. gradlewに実行権限を付与
    fix_gradlew_permissions(android_dir)
    
    print("\\n✅ Gradle緊急修復が完了しました")
    
    # 7. Flutterプロジェクトをクリーンにする
    print("\\n🧹 Flutterプロジェクトをクリーンにしています...")
    try:
        subprocess.run("flutter clean", shell=True, check=True)
        print("✅ Flutterプロジェクトをクリーンにしました")
    except subprocess.CalledProcessError:
        print("⚠️ flutter clean コマンドが失敗しました")
    
    try:
        subprocess.run("flutter pub get", shell=True, check=True)
        print("✅ パッケージを再取得しました")
    except subprocess.CalledProcessError:
        print("⚠️ flutter pub get コマンドが失敗しました")
        
    return True

def clear_caches(android_dir):
    """すべてのキャッシュをクリア"""
    print("\\n🧹 すべてのキャッシュをクリアしています...")
    
    # キャッシュディレクトリのリスト
    cache_dirs = [
        os.path.join(android_dir, '.gradle'),
        os.path.join(android_dir, 'build'),
        os.path.join(android_dir, 'app', 'build'),
        os.path.join(os.path.expanduser('~'), '.gradle', 'caches')
    ]
    
    for cache_dir in cache_dirs:
        if os.path.exists(cache_dir):
            try:
                shutil.rmtree(cache_dir)
                print(f"✅ キャッシュを削除: {cache_dir}")
            except Exception as e:
                print(f"⚠️ キャッシュの削除に失敗: {cache_dir}: {e}")

def fix_gradle_wrapper(android_dir):
    """互換性のあるGradleラッパーを強制的に使用"""
    print("\\n🔧 Gradleラッパーを修正しています...")
    
    # gradle-wrapper.propertiesファイルを直接編集
    wrapper_props = os.path.join(android_dir, 'gradle', 'wrapper', 'gradle-wrapper.properties')
    if os.path.exists(wrapper_props):
        try:
            with open(wrapper_props, 'r') as f:
                content = f.read()
            
            # バックアップを作成
            with open(f"{wrapper_props}.bak", 'w') as f:
                f.write(content)
            
            # Gradleバージョンを7.2に更新（Flutter 3.xとの互換性が高い）
            new_content = content.replace(
                'distributionUrl=https\\://services.gradle.org/distributions/gradle-', 
                'distributionUrl=https\\://services.gradle.org/distributions/gradle-7.2-'
            )
            
            with open(wrapper_props, 'w') as f:
                f.write(new_content)
                
            print("✅ Gradleラッパーを7.2に更新しました")
        except Exception as e:
            print(f"⚠️ Gradleラッパーの更新に失敗: {e}")

def fix_root_build_gradle(android_dir):
    """ルートのbuild.gradleファイルを修正"""
    print("\\n🔧 ルートbuild.gradleを修正しています...")
    
    build_gradle = os.path.join(android_dir, 'build.gradle')
    if os.path.exists(build_gradle):
        try:
            with open(build_gradle, 'r') as f:
                content = f.read()
            
            # バックアップを作成
            with open(f"{build_gradle}.bak", 'w') as f:
                f.write(content)
            
            # 1. Android Gradle Pluginバージョンを修正
            content = content.replace(
                'com.android.tools.build:gradle:',
                'com.android.tools.build:gradle:7.1.2'
            ).replace(
                'com.android.tools.build:gradle:7.1.2+',
                'com.android.tools.build:gradle:7.1.2'
            )
            
            # 2. Kotlinバージョンを修正
            if 'ext.kotlin_version' in content:
                content = re.sub(
                    r'ext\.kotlin_version\s*=\s*[\'"].*?[\'"]',
                    'ext.kotlin_version = "1.6.10"',
                    content
                )
            else:
                # extブロックを追加
                content = content.replace(
                    'buildscript {',
                    'buildscript {\\n    ext.kotlin_version = "1.6.10"'
                )
            
            # 3. repositoriesブロックを修正
            if 'repositories {' in content:
                if 'google()' not in content:
                    content = content.replace(
                        'repositories {',
                        'repositories {\\n        google()'
                    )
                if 'mavenCentral()' not in content:
                    content = content.replace(
                        'repositories {',
                        'repositories {\\n        mavenCentral()'
                    )
            
            with open(build_gradle, 'w') as f:
                f.write(content)
                
            print("✅ ルートbuild.gradleを修正しました")
        except Exception as e:
            print(f"⚠️ ルートbuild.gradleの修正に失敗: {e}")

def fix_app_build_gradle(android_dir):
    """アプリのbuild.gradle(.kts)を修正"""
    print("\\n🔧 アプリのbuild.gradle(.kts)を修正しています...")
    
    # 両方のファイル形式をチェック
    app_gradle_kts = os.path.join(android_dir, 'app', 'build.gradle.kts')
    app_gradle = os.path.join(android_dir, 'app', 'build.gradle')
    
    gradle_file = app_gradle_kts if os.path.exists(app_gradle_kts) else app_gradle
    is_kts = gradle_file.endswith('.kts')
    
    if os.path.exists(gradle_file):
        try:
            with open(gradle_file, 'r') as f:
                content = f.read()
            
            # バックアップを作成
            with open(f"{gradle_file}.bak", 'w') as f:
                f.write(content)
            
            # Android Manifestからパッケージ名を取得
            manifest_file = os.path.join(android_dir, 'app', 'src', 'main', 'AndroidManifest.xml')
            package_name = "com.example.app"
            
            if os.path.exists(manifest_file):
                try:
                    with open(manifest_file, 'r') as f:
                        manifest_content = f.read()
                    
                    package_match = re.search(r'package\\s*=\\s*[\\"\\']([^\\"\\\']+)[\\"\\']', manifest_content)
                    if package_match:
                        package_name = package_match.group(1)
                except Exception:
                    pass
            
            # namespaceを追加
            if 'namespace' not in content:
                if is_kts:
                    content = content.replace(
                        'android {',
                        f'android {{\\n    namespace = "{package_name}"'
                    )
                else:
                    content = content.replace(
                        'android {',
                        f'android {{\\n    namespace "{package_name}"'
                    )
            
            # compileSdkバージョンを修正
            if is_kts:
                if 'compileSdk = ' in content:
                    content = re.sub(
                        r'compileSdk\s*=\s*\d+',
                        'compileSdk = 33',
                        content
                    )
                else:
                    content = content.replace(
                        'android {',
                        'android {\\n    compileSdk = 33'
                    )
            else:
                if 'compileSdkVersion' in content:
                    content = re.sub(
                        r'compileSdkVersion\s*\d+',
                        'compileSdkVersion 33',
                        content
                    )
                else:
                    content = content.replace(
                        'android {',
                        'android {\\n    compileSdkVersion 33'
                    )
            
            # NDKバージョンを修正
            if 'ndkVersion' in content:
                if is_kts:
                    content = re.sub(
                        r'ndkVersion\s*=\s*[\\"\\'].*?[\\"\\']',
                        'ndkVersion = "21.4.7075529"',
                        content
                    )
                else:
                    content = re.sub(
                        r'ndkVersion\s*[\\"\\'].*?[\\"\\']',
                        'ndkVersion "21.4.7075529"',
                        content
                    )
            else:
                if is_kts:
                    content = content.replace(
                        'android {',
                        'android {\\n    ndkVersion = "21.4.7075529"'
                    )
                else:
                    content = content.replace(
                        'android {',
                        'android {\\n    ndkVersion "21.4.7075529"'
                    )
            
            with open(gradle_file, 'w') as f:
                f.write(content)
                
            print("✅ アプリのbuild.gradle(.kts)を修正しました")
        except Exception as e:
            print(f"⚠️ アプリのbuild.gradle(.kts)の修正に失敗: {e}")

def fix_local_properties(android_dir):
    """local.properties を確認・修正"""
    print("\\n🔧 local.propertiesを確認・修正しています...")
    
    local_props = os.path.join(android_dir, 'local.properties')
    if os.path.exists(local_props):
        try:
            with open(local_props, 'r') as f:
                content = f.read()
            
            # バックアップを作成
            with open(f"{local_props}.bak", 'w') as f:
                f.write(content)
            
            # ndk.dirを削除（競合の原因になる可能性がある）
            if 'ndk.dir=' in content:
                content = re.sub(r'ndk\\.dir=.*\\n', '', content)
            
            # flutter.sdkを確認
            if 'flutter.sdk=' not in content:
                # Flutterパスを取得
                flutter_path = None
                try:
                    result = subprocess.run("which flutter", shell=True, capture_output=True, text=True)
                    if result.returncode == 0:
                        flutter_path = os.path.dirname(os.path.dirname(result.stdout.strip()))
                except Exception:
                    pass
                
                if flutter_path:
                    content += f"\\nflutter.sdk={flutter_path}\\n"
            
            with open(local_props, 'w') as f:
                f.write(content)
                
            print("✅ local.propertiesを修正しました")
        except Exception as e:
            print(f"⚠️ local.propertiesの修正に失敗: {e}")

def fix_gradlew_permissions(android_dir):
    """gradlewに実行権限を付与"""
    print("\\n🔧 gradlewに実行権限を付与しています...")
    
    gradlew = os.path.join(android_dir, 'gradlew')
    if os.path.exists(gradlew):
        try:
            # UNIX系OSでのみ実行
            if os.name == 'posix':
                os.chmod(gradlew, 0o755)
                print("✅ gradlewに実行権限を付与しました")
        except Exception as e:
            print(f"⚠️ gradlewの権限設定に失敗: {e}")
''')
            print("✅ 緊急修復モジュールを作成しました")
            
            # 作成したモジュールをインポート
            sys.path.append(script_dir)
            from emergency_gradle_repair import emergency_gradle_repair as er
            return er()
            
        print("🛠️ Gradleの緊急修復を実行します...")
        return True
    except Exception as e:
        print(f"⚠️ 緊急修復の実行に失敗しました: {e}")
        return False
