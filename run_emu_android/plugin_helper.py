#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import subprocess
import platform
import shutil
from utils import run_command as original_run_command

# 無効なオプションのリスト
INVALID_FLUTTER_OPTIONS = ['--no-enable-ios', '--no-enable-android', '--no-example']

def filtered_run_command(cmd, description="", timeout=None, show_output=True, show_progress=False):
    """無効なオプションを除外してコマンドを実行する"""
    if cmd.startswith('flutter'):
        original_cmd = cmd
        for option in INVALID_FLUTTER_OPTIONS:
            cmd = cmd.replace(option, '')
        
        # 連続スペースを単一スペースに変換
        cmd = re.sub(r'\s+', ' ', cmd).strip()
        
        if cmd != original_cmd:
            print(f"⚠️ 警告: コマンドから無効なオプションを削除しました")
            print(f"  修正前: {original_cmd}")
            print(f"  修正後: {cmd}")
    
    # 元のrun_commandを使用して実行
    return original_run_command(cmd, description, timeout, show_output, show_progress)

def check_valid_flutter_options():
    """Flutterコマンドの無効なオプションを検出し、修正する"""
    print("\n🔍 Flutterコマンドオプションの検証と修正を行っています...")
    
    # グローバルな関数を修正したバージョンで上書き
    import utils
    utils.run_command = filtered_run_command
    
    # 他のモジュールでも使用されている可能性のある関数を修正
    import build
    build.run_command = filtered_run_command
    
    try:
        # エミュレータモジュールの関数も修正
        import emulator
        emulator.run_command = filtered_run_command
    except:
        pass
    
    print("✅ 無効なFlutterオプションは自動的に除外されるようになりました")
    return True

def check_flutter_plugins():
    """Flutterプラグインの問題を診断する"""
    print("\n🔍 Flutterプラグインの互換性をチェックしています...")
    
    # プラグインのバージョン情報を取得
    success, output = filtered_run_command("flutter pub deps", "プラグイン依存関係の確認", show_output=False)
    if not success:
        print("⚠️ プラグイン情報の取得に失敗しました")
        return False
        
    # 既知の問題のあるプラグインとバージョン (バージョンをキーに問題とワークアラウンドを保存)
    problematic_plugins = {
        "vibration": {
            "current": "1.9.0",  # 現在検出されているバージョン
            "recommended": "1.9.2",  # 推奨バージョン
            "min_compatible": "1.9.2",  # 最小互換性バージョン
            "latest": "3.1.3",  # 最新バージョン
            "issue": "Flutter v1 embedding APIを使用しており、最新のFlutterでは動作しません",
            "solution": "依存関係をアップグレードするか、互換性のあるバージョンに固定してください"
        }
    }
    
    # 問題が見つかったプラグイン
    found_issues = []
    
    # プラグインバージョンを検出
    plugin_versions = {}
    output_text = output.decode('utf-8') if isinstance(output, bytes) else output
    
    for line in output_text.split('\n'):
        for plugin in problematic_plugins.keys():
            if plugin in line:
                version_match = re.search(r'\b' + plugin + r'\s+([0-9.]+)', line)
                if version_match:
                    version = version_match.group(1)
                    plugin_versions[plugin] = version
                    problematic_plugins[plugin]["current"] = version
                    found_issues.append(plugin)
    
    if found_issues:
        print("\n⚠️ 以下のプラグインに互換性の問題が検出されました:")
        for plugin in found_issues:
            info = problematic_plugins[plugin]
            print(f"  • {plugin} {info['current']}:")
            print(f"    問題: {info['issue']}")
            print(f"    解決策: {info['solution']}")
            print(f"    推奨バージョン: {info['recommended']}（最新: {info['latest']}）")
        
        # 自動修正を提案
        print("\n🔧 この問題を解決するために次のオプションがあります:")
        print("  1. すべての依存関係を更新 (flutter pub upgrade)")
        print("  2. 問題のあるプラグインのバージョンを固定 (pubspec.yaml の編集)")
        print("  3. 代替プラグインを使用")
        print("  4. vibration プラグインを強制アップデート (推奨)")
        
        try:
            choice = input("\n修正方法を選択してください (1-4、または q で続行せずに終了): ")
            if choice == "1":
                return upgrade_all_dependencies()
            elif choice == "2":
                return fix_problematic_plugins(problematic_plugins)
            elif choice == "3":
                return suggest_alternative_plugins(problematic_plugins)
            elif choice == "4":
                return fix_vibration_plugin()
            elif choice.lower() == "q":
                print("処理を中止します")
                return False
            else:
                print("無効な選択です。続行せずに進みます。")
        except KeyboardInterrupt:
            print("\n選択がキャンセルされました。")
            return False
    else:
        print("✅ プラグイン互換性の問題は検出されませんでした")
        return True

def upgrade_all_dependencies():
    """すべての依存関係をアップグレード"""
    print("\n📦 すべての依存関係をアップグレードしています...")
    
    # 通常のアップグレードを試行
    success, output = filtered_run_command("flutter pub upgrade", "依存関係のアップグレード（通常モード）", show_output=True)
    
    # 出力をチェックして「No dependencies changed」が含まれているか確認
    output_text = output.decode('utf-8') if isinstance(output, bytes) else output
    if "No dependencies changed" in output_text:
        print("\n⚠️ 通常のアップグレードでは依存関係が変更されませんでした。メジャーバージョンアップグレードを試みます...")
        success, _ = filtered_run_command("flutter pub upgrade --major-versions", "依存関係のメジャーバージョンアップグレード", show_output=True)
    
    if success:
        print("✅ 依存関係のアップグレードが完了しました")
    else:
        print("⚠️ 依存関係のアップグレード中に問題が発生しました")
    
    return success

def fix_problematic_plugins(problematic_plugins):
    """問題のあるプラグインを修正する"""
    print("\n🔧 pubspec.yamlを編集して問題のあるプラグインを修正します...")
    
    pubspec_path = os.path.join(os.getcwd(), 'pubspec.yaml')
    if not os.path.exists(pubspec_path):
        print(f"⚠️ pubspec.yamlが見つかりません: {pubspec_path}")
        return False
    
    try:
        # ファイル内容を読み込む
        with open(pubspec_path, 'r') as f:
            content = f.read()
        
        # バックアップを作成
        backup_path = f"{pubspec_path}.bak"
        with open(backup_path, 'w') as f:
            f.write(content)
        print(f"💾 元のファイルをバックアップしました: {backup_path}")
        
        # 問題のあるプラグインのバージョン制約を書き換え
        for plugin, info in problematic_plugins.items():
            if "recommended" in info:
                # 該当プラグインの依存行を検索
                plugin_pattern = rf'{plugin}:\s.*'
                recommended = info["recommended"]
                
                if re.search(plugin_pattern, content):
                    # バージョンを固定して書き換え
                    new_content = re.sub(
                        plugin_pattern,
                        f'{plugin}: ^{recommended}  # 互換性のために固定',
                        content
                    )
                    content = new_content
                    print(f"✏️ {plugin} のバージョンを {recommended} に固定しました")
        
        # 更新内容を書き込み
        with open(pubspec_path, 'w') as f:
            f.write(content)
        
        # 依存関係を再取得 (無効なオプションを削除)
        print("\n📦 固定バージョンで依存関係を再取得しています...")
        success, _ = filtered_run_command("flutter pub get", "依存関係の再取得", show_output=True)
        
        if success:
            print("✅ 問題のあるプラグインの修正が完了しました")
        else:
            print("⚠️ 依存関係の再取得中に問題が発生しました")
            # バックアップから復元
            with open(backup_path, 'r') as f:
                original = f.read()
            with open(pubspec_path, 'w') as f:
                f.write(original)
            print("🔄 問題が発生したため元の pubspec.yaml を復元しました")
        
        return success
    
    except Exception as e:
        print(f"⚠️ pubspec.yamlの修正中にエラーが発生しました: {e}")
        return False

def suggest_alternative_plugins(problematic_plugins):
    """代替プラグインを提案"""
    print("\n💡 問題のあるプラグインの代替案:")
    
    alternatives = {
        "vibration": [
            {"name": "flutter_vibrate", "url": "https://pub.dev/packages/flutter_vibrate"},
            {"name": "haptic_feedback", "url": "https://pub.dev/packages/haptic_feedback"}
        ]
    }
    
    for plugin in problematic_plugins:
        print(f"\n📌 {plugin} の代替プラグイン:")
        if plugin in alternatives:
            for alt in alternatives[plugin]:
                print(f"  • {alt['name']}: {alt['url']}")
        else:
            print("  代替プラグインの提案がありません")
    
    print("\nℹ️ 代替プラグインを使用するには:")
    print("1. pubspec.yamlから問題のプラグインを削除")
    print("2. 代替プラグインを追加")
    print("3. flutter pub get を実行")
    print("4. コードを新しいプラグインの使用方法に合わせて更新")
    
    print("\n🔍 コードの変更が必要なため、手動での対応をお願いします。")
    return False

def fix_vibration_plugin():
    """vibrationプラグインの問題を特別に修正する"""
    print("\n🔧 vibrationプラグインの問題を修正しています...")
    
    # プロジェクトのpubspec.yamlパス
    pubspec_path = os.path.join(os.getcwd(), 'pubspec.yaml')
    if not os.path.exists(pubspec_path):
        print(f"⚠️ pubspec.yamlが見つかりません: {pubspec_path}")
        return False
    
    try:
        # ファイル内容を読み込む
        with open(pubspec_path, 'r') as f:
            content = f.read()
        
        # バックアップを作成
        backup_path = f"{pubspec_path}.bak"
        with open(backup_path, 'w') as f:
            f.write(content)
        print(f"💾 元のファイルをバックアップしました: {backup_path}")
        
        # vibrationプラグインを最新互換バージョンに固定
        vibration_pattern = r'vibration:\s.*'
        if re.search(vibration_pattern, content):
            new_content = re.sub(
                vibration_pattern,
                'vibration: ^3.1.3  # 強制的に互換性のあるバージョンに固定',
                content
            )
            content = new_content
            print("✏️ vibrationプラグインを最新バージョン 3.1.3 に設定しました")
        else:
            # dependency_overridesセクションを追加
            if 'dependency_overrides:' not in content:
                content += """

dependency_overrides:
  vibration: ^3.1.3
  vibration_platform_interface: ^0.1.0
"""
                print("✏️ dependency_overridesセクションを追加してvibrationプラグインを強制指定しました")
        
        # 更新内容を書き込み
        with open(pubspec_path, 'w') as f:
            f.write(content)
        
        print("\n📦 更新したバージョンで依存関係を取得しています...")
        
        # Flutter依存関係解決でキャッシュを強制的に更新 (無効なオプションを削除)
        filtered_run_command("flutter pub cache clean", "パッケージキャッシュのクリア", show_output=False)
        # 標準の flutter pub get コマンドを使用 (無効なオプションなし)
        success, _ = filtered_run_command("flutter pub get", "依存関係の再取得", show_output=True)
        
        if success:
            print("✅ vibrationプラグインの問題が修正されました")
            return True
        else:
            print("⚠️ 依存関係の更新に失敗しました。別の方法を試します...")
            
            # バージョン1.9.2を試す
            with open(pubspec_path, 'r') as f:
                content = f.read()
            
            content = content.replace('vibration: ^3.1.3', 'vibration: ^1.9.2')
            
            with open(pubspec_path, 'w') as f:
                f.write(content)
            
            print("\n📦 互換バージョン 1.9.2 で依存関係を再取得しています...")
            filtered_run_command("flutter pub cache clean", "パッケージキャッシュのクリア", show_output=False)
            success, _ = filtered_run_command("flutter pub get", "依存関係の再取得", show_output=True)
            
            if not success:
                # バックアップから復元
                with open(backup_path, 'r') as f:
                    original = f.read()
                with open(pubspec_path, 'w') as f:
                    f.write(original)
                print("🔄 問題が発生したため元の pubspec.yaml を復元しました")
            else:
                print("✅ vibrationプラグインをバージョン 1.9.2 で固定しました")
                return True
        
        return False
    
    except Exception as e:
        print(f"⚠️ vibrationプラグインの修正中にエラーが発生しました: {e}")
        return False

def fix_build_gradle_kts():
    """build.gradleまたはbuild.gradle.ktsファイルにNDKバージョン設定を追加する"""
    print("\n🔧 Gradle設定ファイルを更新しています...")
    
    # ファイルパスの指定
    app_gradle_kts = os.path.join(os.getcwd(), 'android', 'app', 'build.gradle.kts')
    app_gradle = os.path.join(os.getcwd(), 'android', 'app', 'build.gradle')
    
    # build.gradle.ktsファイルが存在する場合
    if os.path.exists(app_gradle_kts):
        gradle_file = app_gradle_kts
        print(f"📄 Kotlin DSLのGradleファイルを編集します: {app_gradle_kts}")
        is_kts = True
    # 通常のbuild.gradleファイルが存在する場合
    elif os.path.exists(app_gradle):
        gradle_file = app_gradle
        print(f"📄 Gradleファイルを編集します: {app_gradle}")
        is_kts = False
    else:
        print("⚠️ アプリのGradleファイルが見つかりません")
        return False
    
    try:
        # ファイル内容を読み込む
        with open(gradle_file, 'r') as f:
            content = f.read()
        
        # バックアップを作成
        backup_file = f"{gradle_file}.bak"
        with open(backup_file, 'w') as f:
            f.write(content)
        
        # NDKバージョンが既に設定されているか確認
        ndk_version_pattern = r'ndkVersion\s*=?\s*["\']([0-9.]+)["\']'
        ndk_match = re.search(ndk_version_pattern, content)
        
        if ndk_match:
            current_version = ndk_match.group(1)
            print(f"ℹ️ 既存のNDKバージョン設定: {current_version}")
            
            # バージョンが27.0.12077973でない場合のみ更新
            if current_version != "27.0.12077973":
                if is_kts:
                    new_content = re.sub(
                        ndk_version_pattern,
                        'ndkVersion = "27.0.12077973"',
                        content
                    )
                else:
                    new_content = re.sub(
                        ndk_version_pattern,
                        'ndkVersion "27.0.12077973"',
                        content
                    )
                
                with open(gradle_file, 'w') as f:
                    f.write(new_content)
                print("✅ NDKバージョンを 27.0.12077973 に更新しました")
            else:
                print("✅ NDKバージョンは既に正しく設定されています")
        else:
            print("ℹ️ NDKバージョン設定が見つかりません。追加します...")
            
            # android { ブロックを探し、NDKバージョンを追加
            if is_kts:
                android_block_pattern = r'(android\s*\{)'
                replacement = r'\1\n    ndkVersion = "27.0.12077973"'
            else:
                android_block_pattern = r'(android\s*\{)'
                replacement = r'\1\n    ndkVersion "27.0.12077973"'
            
            new_content = re.sub(android_block_pattern, replacement, content)
            
            if new_content == content:
                print("⚠️ android ブロックが見つかりませんでした")
                return False
            
            with open(gradle_file, 'w') as f:
                f.write(new_content)
            print("✅ NDKバージョン設定を追加しました")
        
        return True
    
    except Exception as e:
        print(f"⚠️ Gradleファイルの更新中にエラーが発生しました: {e}")
        return False

def fix_gradle_namespace():
    """build.gradle.ktsファイルにnamespace設定を追加する"""
    print("\n🔧 Gradle namespaceの問題を修正しています...")
    
    # build.gradle.ktsファイルのパス
    app_gradle_kts = os.path.join(os.getcwd(), 'android', 'app', 'build.gradle.kts')
    app_gradle = os.path.join(os.getcwd(), 'android', 'app', 'build.gradle')
    
    gradle_file = None
    is_kts = False
    
    if os.path.exists(app_gradle_kts):
        gradle_file = app_gradle_kts
        is_kts = True
    elif os.path.exists(app_gradle):
        gradle_file = app_gradle
    else:
        print("⚠️ Gradleファイルが見つかりません")
        return False
    
    try:
        # AndroidManifest.xmlからpackage名を取得
        manifest_path = os.path.join(os.getcwd(), 'android', 'app', 'src', 'main', 'AndroidManifest.xml')
        package_name = "com.example.app"  # デフォルト値
        
        if (os.path.exists(manifest_path)):
            with open(manifest_path, 'r') as f:
                manifest_content = f.read()
                package_match = re.search(r'package\s*=\s*["\']([^"\']+)["\']', manifest_content)
                if package_match:
                    package_name = package_match.group(1)
                    print(f"📦 AndroidManifest.xmlからパッケージ名を取得: {package_name}")
        
        # ファイル内容を読み込む
        with open(gradle_file, 'r') as f:
            content = f.read()
        
        # バックアップを作成
        backup_file = f"{gradle_file}.bak"
        with open(backup_file, 'w') as f:
            f.write(content)
        print(f"💾 ファイルをバックアップしました: {backup_file}")
        
        # 既にnamespaceが設定されているか確認
        if "namespace" in content:
            print("✅ namespaceは既に設定されています")
            return True
        
        # android ブロックを探してnamespaceを追加
        if is_kts:
            # Kotlin DSLの場合の書き方
            android_block_pattern = r'android\s*\{'
            new_content = re.sub(
                android_block_pattern,
                f'android {{\n    namespace = "{package_name}"',
                content
            )
        else:
            # Groovy DSLの場合の書き方
            android_block_pattern = r'android\s*\{'
            new_content = re.sub(
                android_block_pattern,
                f'android {{\n    namespace "{package_name}"',
                content
            )
        
        # 変更を保存
        with open(gradle_file, 'w') as f:
            f.write(new_content)
        
        print(f"✅ namespaceを追加しました: {package_name}")
        return True
    
    except Exception as e:
        print(f"⚠️ Gradleファイルの更新中にエラーが発生しました: {e}")
        return False

def fix_gradle_build_issues():
    """Gradleビルドの問題を診断して修正する"""
    print("\n🔍 Gradleビルドの問題を診断しています...")

    # Androidディレクトリの検索
    android_dir = os.path.join(os.getcwd(), 'android')
    if not os.path.exists(android_dir):
        print(f"⚠️ Androidディレクトリが見つかりません: {android_dir}")
        return False
    
    # 1. NDKバージョンの強制設定
    force_ndk_version()
    
    # 2. Gradleキャッシュのクリア
    print("\n🧹 Gradleキャッシュをクリアしています...")
    gradle_cache_dir = os.path.join(android_dir, '.gradle')
    if os.path.exists(gradle_cache_dir):
        try:
            shutil.rmtree(gradle_cache_dir)
            print(f"✅ Gradleキャッシュを削除しました: {gradle_cache_dir}")
        except Exception as e:
            print(f"⚠️ Gradleキャッシュの削除中にエラーが発生しました: {e}")
    
    # 3. ビルドディレクトリのクリア
    build_dir = os.path.join(android_dir, 'build')
    if os.path.exists(build_dir):
        try:
            shutil.rmtree(build_dir)
            print(f"✅ ビルドディレクトリを削除しました: {build_dir}")
        except Exception as e:
            print(f"⚠️ ビルドディレクトリの削除中にエラーが発生しました: {e}")
    
    # 4. Gradleラッパーの更新
    print("\n🔄 Gradleラッパーを更新しています...")
    filtered_run_command("cd android && ./gradlew wrapper --gradle-version=7.6.1 --distribution-type=all",
               "Gradleラッパーの更新", show_output=False)
    
    # 5. build.gradle.ktsファイルの強制修正
    fix_build_gradle_kts_direct()
    
    return True

def force_ndk_version():
    """NDKバージョン設定を強制的に更新する"""
    print("\n🔧 NDKバージョン設定を強制的に更新しています...")
    
    # build.gradle.ktsファイルのパス
    app_gradle_kts = os.path.join(os.getcwd(), 'android', 'app', 'build.gradle.kts')
    app_gradle = os.path.join(os.getcwd(), 'android', 'app', 'build.gradle')
    
    # どちらのファイルが存在するか確認
    if os.path.exists(app_gradle_kts):
        gradle_file = app_gradle_kts
        print(f"📄 Kotlin DSLファイルを修正します: {app_gradle_kts}")
        is_kts = True
    elif os.path.exists(app_gradle):
        gradle_file = app_gradle
        print(f"📄 通常のGradleファイルを修正します: {app_gradle}")
        is_kts = False
    else:
        print("⚠️ Gradleファイルが見つかりません")
        return False
    
    # local.propertiesファイルのNDK設定も確認
    local_props = os.path.join(os.getcwd(), 'android', 'local.properties')
    if (os.path.exists(local_props)):
        with open(local_props, 'r') as f:
            content = f.read()
        
        # ndk.dir設定を削除
        if 'ndk.dir=' in content:
            new_content = re.sub(r'ndk\.dir=.*\n', '', content)
            with open(local_props, 'w') as f:
                f.write(new_content)
            print("✅ local.propertiesからndk.dir設定を削除しました")
    
    # Gradleファイルを修正
    try:
        with open(gradle_file, 'r') as f:
            content = f.read()
        
        # ファイルのバックアップ
        with open(f"{gradle_file}.bak", 'w') as f:
            f.write(content)
        
        # ファイルの中身を表示して診断
        print("📝 現在のファイル内容:")
        lines = content.split('\n')
        for i, line in enumerate(lines[:20]):  # 最初の20行だけ表示
            if 'ndk' in line.lower():
                print(f"   {i+1}: {line} 👈 NDK関連")
            elif 'android' in line.lower() and '{' in line:
                print(f"   {i+1}: {line} 👈 androidブロック")
        
        # androidブロックを見つけてNDKバージョン設定を挿入/更新
        android_block_pattern = r'android\s*\{'
        android_block_match = re.search(android_block_pattern, content)
        
        if android_block_match:
            # androidブロックの位置を特定
            block_start = android_block_match.start()
            
            # android { の次の行にNDK設定を挿入
            if is_kts:
                ndk_line = '\n    ndkVersion = "27.0.12077973"\n'
            else:
                ndk_line = '\n    ndkVersion "27.0.12077973"\n'
            
            # 既存のndkVersionを探す
            ndk_pattern = r'ndkVersion\s*=?\s*[\'"].*?[\'"]'
            if re.search(ndk_pattern, content):
                # 既存のNDK設定を置換
                new_content = re.sub(ndk_pattern, 
                                    'ndkVersion = "27.0.12077973"' if is_kts else 'ndkVersion "27.0.12077973"', 
                                    content)
                print("🔄 既存のNDKバージョン設定を置換しました")
            else:
                # NDK設定がなければ挿入
                position = android_block_match.end()
                new_content = content[:position] + ndk_line + content[position:]
                print("➕ NDKバージョン設定を追加しました")
            
            # 変更を保存
            with open(gradle_file, 'w') as f:
                f.write(new_content)
            
            print("✅ NDKバージョンを27.0.12077973に強制設定しました")
            return True
        else:
            print("⚠️ androidブロックが見つかりませんでした")
            return False
    
    except Exception as e:
        print(f"⚠️ Gradleファイル修正中にエラーが発生しました: {e}")
        return False

def fix_build_gradle_kts_direct():
    """build.gradle.kts または build.gradle ファイルを直接編集して修正する"""
    print("\n🔧 Gradleファイルを直接編集しています...")
    
    # ファイルパス
    app_gradle_kts = os.path.join(os.getcwd(), 'android', 'app', 'build.gradle.kts')
    app_gradle = os.path.join(os.getcwd(), 'android', 'app', 'build.gradle')
    
    gradle_file = None
    is_kts = False
    
    if os.path.exists(app_gradle_kts):
        gradle_file = app_gradle_kts
        is_kts = True
    elif os.path.exists(app_gradle):
        gradle_file = app_gradle
    
    if not gradle_file:
        print("⚠️ Gradleファイルが見つかりません")
        return False
    
    try:
        # ファイル内容を読み込む
        with open(gradle_file, 'r') as f:
            original_content = f.read()
        
        # 新しい内容を作成
        if is_kts:
            content = """
android {
    ndkVersion = "27.0.12077973"
    compileSdk = 34
    
    defaultConfig {
        // その他の設定
        minSdk = 21
    }
    
    // 残りの設定
"""
        else:
            content = """
android {
    ndkVersion "27.0.12077973"
    compileSdkVersion 34
    
    defaultConfig {
        // その他の設定
        minSdkVersion 21
    }
    
    // 残りの設定
"""
        
        # androidブロック全体を置換
        android_block_pattern = r'android\s*\{[^}]*\}'
        if re.search(android_block_pattern, original_content, re.DOTALL):
            new_content = re.sub(android_block_pattern, content.strip(), original_content, flags=re.DOTALL)
            
            # ファイルに書き込む前にバックアップ
            backup_file = f"{gradle_file}.orig"
            with open(backup_file, 'w') as f:
                f.write(original_content)
            
            # 新しい内容を書き込む
            with open(gradle_file, 'w') as f:
                f.write(new_content)
            
            print(f"✅ {os.path.basename(gradle_file)}のandroidブロックを完全に置き換えました")
            print(f"💾 元のファイルをバックアップしました: {backup_file}")
            return True
        else:
            print("⚠️ androidブロックが見つかりませんでした")
            return False
    
    except Exception as e:
        print(f"⚠️ Gradleファイル修正中にエラーが発生しました: {e}")
        return False

def fix_manifest_issues():
    """AndroidManifest.xmlの問題を診断して修正する"""
    print("\n🔍 AndroidManifest.xmlの問題を診断しています...")
    
    # AndroidManifest.xmlのパス
    manifest_path = os.path.join(os.getcwd(), 'android', 'app', 'src', 'main', 'AndroidManifest.xml')
    
    # ファイルが存在するか確認
    if not os.path.exists(manifest_path):
        print(f"⚠️ AndroidManifest.xmlが見つかりません: {manifest_path}")
        print("🔧 flutter createコマンドを実行してAndroidManifest.xmlを再生成します...")
        
        # flutter createを実行してAndroidフォルダを初期化（無効なオプションは使用しない）
        success, _ = filtered_run_command("flutter create --platforms=android .", 
                               "Androidプラットフォームを再生成", show_output=True)
        
        if success and os.path.exists(manifest_path):
            print(f"✅ AndroidManifest.xmlが生成されました: {manifest_path}")
        else:
            print(f"⚠️ AndroidManifest.xmlの生成に失敗しました")
            return False
    
    # AndroidManifest.xmlの内容確認と修正
    try:
        with open(manifest_path, 'r') as f:
            content = f.read()
        
        # バックアップを作成
        backup_path = f"{manifest_path}.bak"
        with open(backup_path, 'w') as f:
            f.write(content)
            
        print("💾 AndroidManifest.xmlのバックアップを作成しました")
        
        # package属性とmainActivityを確認
        package_match = re.search(r'package\s*=\s*["\']([^"\']+)["\']', content)
        activity_match = re.search(r'<activity[^>]*android:name\s*=\s*["\']([^"\']+)["\']', content)
        
        issues_found = False
        
        if not package_match:
            print("⚠️ packageの指定が見つかりません")
            issues_found = True
        else:
            print(f"📦 検出されたpackage名: {package_match.group(1)}")
        
        if not activity_match:
            print("⚠️ メインアクティビティが見つかりません")
            issues_found = True
        else:
            print(f"🚀 検出されたメインアクティビティ: {activity_match.group(1)}")
            
        # launch activityが見つからない場合の修正
        if issues_found:
            print("🔧 AndroidManifest.xmlを修正しています...")
            
            # デフォルトのFlutter Manifestテンプレートでファイルを再構築
            default_manifest = '''<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android"
    package="com.example.gyroscopeApp">

    <application
        android:name="${applicationName}"
        android:icon="@mipmap/ic_launcher"
        android:label="gyroscopeApp">
        <activity
            android:name=".MainActivity"
            android:configChanges="orientation|keyboardHidden|keyboard|screenSize|smallestScreenSize|locale|layoutDirection|fontScale|screenLayout|density|uiMode"
            android:exported="true"
            android:hardwareAccelerated="true"
            android:launchMode="singleTop"
            android:theme="@style/LaunchTheme"
            android:windowSoftInputMode="adjustResize">
            <meta-data
                android:name="io.flutter.embedding.android.NormalTheme"
                android:resource="@style/NormalTheme" />
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity>
        <meta-data
            android:name="flutterEmbedding"
            android:value="2" />
    </application>
</manifest>'''
            
            # ファイルにデフォルトManifestを書き込む
            with open(manifest_path, 'w') as f:
                f.write(default_manifest)
                
            print("✅ AndroidManifest.xmlをデフォルトテンプレートで修正しました")
            
            # build.gradleのアプリケーションIDも確認・修正
            build_gradle = os.path.join(os.getcwd(), 'android', 'app', 'build.gradle')
            build_gradle_kts = os.path.join(os.getcwd(), 'android', 'app', 'build.gradle.kts')
            
            gradle_path = build_gradle_kts if os.path.exists(build_gradle_kts) else build_gradle
            
            if os.path.exists(gradle_path):
                with open(gradle_path, 'r') as f:
                    gradle_content = f.read()
                
                # applicationIdを探して修正
                app_id_match = re.search(r'applicationId\s*=?\s*[\'"]([^\'"]+)[\'"]', gradle_content)
                
                if app_id_match:
                    print(f"📱 現在のapplicationId: {app_id_match.group(1)}")
                else:
                    print("⚠️ applicationIdが見つかりません。追加しています...")
                    # applicationIdをbuild.gradleに追加
                    if gradle_path.endswith('.kts'):
                        new_gradle_content = re.sub(
                            r'(defaultConfig\s*\{)',
                            r'\1\n        applicationId = "com.example.gyroscopeApp"',
                            gradle_content
                        )
                    else:
                        new_gradle_content = re.sub(
                            r'(defaultConfig\s*\{)',
                            r'\1\n        applicationId "com.example.gyroscopeApp"',
                            gradle_content
                        )
                    
                    with open(gradle_path, 'w') as f:
                        f.write(new_gradle_content)
                    
                    print("✅ applicationIdを追加しました: com.example.gyroscopeApp")
                
        # pubspec.yamlのFlutterコンポーネントも確認
        pubspec_path = os.path.join(os.getcwd(), 'pubspec.yaml')
        if os.path.exists(pubspec_path):
            with open(pubspec_path, 'r') as f:
                pubspec_content = f.read()
            
            if 'flutter:' not in pubspec_content:
                print("⚠️ pubspec.yamlにflutterセクションがありません")
            else:
                if 'android:' not in pubspec_content:
                    print("ℹ️ Androidプラットフォーム設定が明示的に指定されていません")
        
        # プロジェクトを再度configureする
        print("\n🔄 Flutterプロジェクトをリフレッシュしています...")
        filtered_run_command("flutter clean", "プロジェクトクリーンアップ", show_output=True)
        filtered_run_command("flutter pub get", "依存関係の再取得", show_output=True)
        
        return True
    
    except Exception as e:
        print(f"⚠️ AndroidManifest.xmlの処理中にエラーが発生しました: {e}")
        return False

def safe_flutter_command(flutter_cmd, description="", show_output=True):
    """無効なオプションを自動的に除外してFlutterコマンドを実行する"""
    cmd = flutter_cmd
    for invalid_option in INVALID_FLUTTER_OPTIONS:
        if invalid_option in cmd:
            cmd = cmd.replace(invalid_option, '')
    
    # 連続スペースを単一スペースに置換
    cmd = re.sub(r'\s+', ' ', cmd).strip()
    
    # 修正: original_run_command を使用
    return original_run_command(cmd, description, None, show_output)
