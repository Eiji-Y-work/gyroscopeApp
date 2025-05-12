#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import argparse
import datetime
import sys
import platform  # Java/Gradle互換性チェック用に追加
import shutil  # Android再構築用に追加
import re  # 追加: NDKバージョン抽出などのために必要
from utils import get_flutter_version, prepare_output_directory, run_command  # run_commandを明示的にインポート
from env_check import check_flutter_installation, check_android_sdk, check_project_directory
from emulator import get_available_emulators, print_emulator_list, select_emulator
from build import build_and_run_android_emulator
from plugin_helper import check_flutter_plugins, fix_build_gradle_kts

# Java/Gradle互換性問題検出・修正機能
def detect_java_gradle_incompatibility(error_message):
    """エラーメッセージからJava/Gradle互換性問題を検出する"""
    keywords = [
        "Unsupported class file major version",
        "incompatible with the Java version",
        "Your project's Gradle version is incompatible with the Java"
    ]
    
    for keyword in keywords:
        if keyword in error_message:
            return True
    return False

def get_java_version_info():
    """システムのJava情報を詳細に取得"""
    try:
        result = run_command("java -version", "Javaバージョン確認", show_output=False)
        if result[0]:
            output = result[1].decode('utf-8') if isinstance(result[1], bytes) else result[1]
            return output.strip()
        return "不明"
    except:
        return "取得不可"

def run_java_gradle_fix():
    """Java/Gradle互換性問題を修正する"""
    print("\n🔧 Java/Gradle互換性問題を修正しています...")
    try:
        # 直接java_gradle_fixモジュールを作成して実行
        java_gradle_fix_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "java_gradle_fix.py")
        
        if not os.path.exists(java_gradle_fix_path):
            print("✨ 最適なGradle設定を生成します...")
            # 詳細なJava情報を取得
            java_version_info = get_java_version_info()
            print(f"🔍 検出されたJava環境: {java_version_info}")
            
            # java_gradle_fix.pyを作成
            create_java_gradle_fix_module(java_gradle_fix_path)
        
        # モジュールをインポートして実行
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        from java_gradle_fix import fix_java_gradle_compatibility
        return fix_java_gradle_compatibility()
    
    except Exception as e:
        print(f"⚠️ Java/Gradle互換性修正中にエラーが発生しました: {e}")
        return False

def create_java_gradle_fix_module(java_gradle_fix_path):
    """Java/Gradle互換性修正モジュールを作成する"""
    print(f"✨ Java/Gradle互換性修正モジュールを作成: {java_gradle_fix_path}")
    
    with open(java_gradle_fix_path, 'w') as f:
        f.write('''#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import shutil
import subprocess
import platform
import sys
import json

def get_java_version():
    """実行中のJavaバージョンを取得"""
    try:
        result = subprocess.run(["java", "-version"], capture_output=True, text=True, stderr=subprocess.STDOUT)
        version_output = result.stdout
        
        # バージョン文字列からメジャーバージョンを抽出
        if "version" in version_output:
            if '"1.8' in version_output:
                return 8
            elif '"11' in version_output or "11." in version_output:
                return 11
            elif '"17' in version_output or "17." in version_output:
                return 17
            elif '"21' in version_output or "21." in version_output:
                return 21
            
            # 一般的なバージョン番号パターンを検出
            match = re.search(r'version "([0-9]+)', version_output)
            if match:
                return int(match.group(1))
        
        # 判断できない場合は11を仮定（最も一般的なバージョン）
        return 11
    except Exception as e:
        print(f"⚠️ Javaバージョン検出エラー: {e}")
        return 11  # デフォルト値

def get_compatible_gradle_version(java_version):
    """指定されたJavaバージョンと互換性のあるGradleバージョンを返す"""
    # Javaバージョンに最適なGradleバージョンをマッピング
    compatibility_map = {
        8: "6.7.1",   # Java 8には6.x系が安定
        11: "7.6.1",  # Java 11には7.x系が最適
        17: "8.0.2",  # Java 17には8.0+が必要
        21: "8.4",    # Java 21には8.3+が必要
    }
    
    # 最も近いキーを見つける（上限に基づく）
    compatible_version = "7.6.1"  # デフォルトは7.6.1
    for key in sorted(compatibility_map.keys()):
        if java_version <= key:
            compatible_version = compatibility_map[key]
            break
    
    return compatible_version

def fix_java_gradle_compatibility():
    """Java/Gradle互換性問題を修正"""
    print("\\n🔍 Java/Gradle互換性問題を診断しています...")
    
    # 現在のJavaバージョンを検出
    java_version = get_java_version()
    print(f"✅ 検出されたJavaバージョン: {java_version}")
    
    # 互換性のあるGradleバージョンを取得
    gradle_version = get_compatible_gradle_version(java_version)
    print(f"✅ 選択されたGradleバージョン: {gradle_version}")
    
    # プロジェクトのルートディレクトリ
    project_dir = os.getcwd()
    android_dir = os.path.join(project_dir, 'android')
    
    # gradle-wrapper.properties を更新
    wrapper_props = os.path.join(android_dir, 'gradle', 'wrapper', 'gradle-wrapper.properties')
    if (os.path.exists(wrapper_props)):
        # バックアップを作成
        backup_file = f"{wrapper_props}.javafix.bak"
        shutil.copy2(wrapper_props, backup_file)
        print(f"💾 バックアップを作成しました: {backup_file}")
        
        # 現在のURL形式を保持しながらバージョンのみ更新
        with open(wrapper_props, 'r') as f:
            content = f.read()
        
        # すべてのディストリビューションタイプ（bin, all, etc）をサポート
        current_dist_type = 'bin'
        dist_match = re.search(r'gradle-[0-9.]+-([^\.]+)\.zip', content)
        if dist_match:
            current_dist_type = dist_match.group(1)
        
        # URL形式を保持しながらバージョンのみ更新
        new_content = re.sub(
            r'distributionUrl=.*gradle-[0-9.]+-.*\.zip',
            f'distributionUrl=https\\\\://services.gradle.org/distributions/gradle-{gradle_version}-{current_dist_type}.zip',
            content
        )
        
        with open(wrapper_props, 'w') as f:
            f.write(new_content)
        
        print(f"✅ gradle-wrapper.propertiesをJava {java_version}と互換性のあるGradle {gradle_version}に更新しました")
    else:
        print("⚠️ gradle-wrapper.propertiesファイルが見つかりません")
        os.makedirs(os.path.dirname(wrapper_props), exist_ok=True)
        
        # デフォルトのWrapper設定を作成
        with open(wrapper_props, 'w') as f:
            f.write(f"""distributionBase=GRADLE_USER_HOME
distributionPath=wrapper/dists
zipStoreBase=GRADLE_USER_HOME
zipStorePath=wrapper/dists
distributionUrl=https\\\\://services.gradle.org/distributions/gradle-{gradle_version}-all.zip
""")
        print(f"✅ 新しいgradle-wrapper.propertiesファイルを作成しました（Gradle {gradle_version}）")
    
    # build.gradleファイルの内容も確認し、必要に応じて更新
    root_gradle = os.path.join(android_dir, 'build.gradle')
    if os.path.exists(root_gradle):
        with open(root_gradle, 'r') as f:
            content = f.read()
        
        # KotlinバージョンとAndroid Gradle Pluginバージョンの互換性を確保
        updates = []
        
        # Java 17の場合、Kotlinバージョンを1.8.0以上に、AGPを7.3.0以上に
        if java_version >= 17:
            if re.search(r'ext\.kotlin_version\s*=\s*[\'"]([^\'"]+)[\'"]', content):
                content = re.sub(
                    r'ext\.kotlin_version\s*=\s*[\'"]([^\'"]+)[\'"]',
                    'ext.kotlin_version = "1.8.10"',
                    content
                )
                updates.append("Kotlinバージョンを1.8.10に更新")
            
            if re.search(r'com\.android\.tools\.build:gradle:[^\'"]+[\'"]', content):
                content = re.sub(
                    r'com\.android\.tools\.build:gradle:[^\'"]+[\'"]',
                    'com.android.tools.build:gradle:7.3.0"',
                    content
                )
                updates.append("Android Gradle Pluginを7.3.0に更新")
        
        # 変更があれば保存
        if updates:
            with open(root_gradle, 'w') as f:
                f.write(content)
            print("✅ build.gradleを更新しました:")
            for update in updates:
                print(f"  - {update}")
    
    print("\\n✅ Java/Gradle互換性問題の修正が完了しました")
    
    # キャッシュをクリア
    cache_dirs = [
        os.path.join(android_dir, '.gradle'),
        os.path.join(android_dir, 'build'),
        os.path.join(android_dir, 'app', 'build')
    ]
    
    print("\\n🧹 Gradleキャッシュをクリアしています...")
    for cache_dir in cache_dirs:
        if os.path.exists(cache_dir):
            try:
                shutil.rmtree(cache_dir)
                print(f"✅ キャッシュを削除: {cache_dir}")
            except Exception as e:
                print(f"⚠️ キャッシュ削除エラー: {e}")
    
    return True

if __name__ == "__main__":
    fix_java_gradle_compatibility()
''')
    print(f"✅ Java/Gradle互換性修正モジュールを作成しました: {java_gradle_fix_path}")
    return True

def fix_kotlin_dsl_issues():
    """Kotlin DSL (.kts) Gradleファイルの互換性問題を修正"""
    print("\n🔧 Kotlin DSL Gradleファイルの互換性問題を修正しています...")
    
    android_dir = os.path.join(os.getcwd(), 'android')
    
    # 1. settings.gradle.kts を修正
    settings_gradle_kts = os.path.join(android_dir, 'settings.gradle.kts')
    settings_gradle = os.path.join(android_dir, 'settings.gradle')
    
    if os.path.exists(settings_gradle_kts):
        print(f"📝 Kotlin DSL settings.gradle.kts ファイルを通常の settings.gradle に変換します")
        # バックアップを作成
        backup_file = f"{settings_gradle_kts}.bak"
        shutil.copy2(settings_gradle_kts, backup_file)
        print(f"💾 バックアップを作成しました: {backup_file}")
        
        try:
            # ファイルの内容を読み取り
            with open(settings_gradle_kts, 'r') as f:
                content = f.read()
            
            # Kotlin DSL 特有の構文を Groovy 構文に変換
            content = content.replace('plugins {', '// plugins {')  # コメントアウト
            content = content.replace('}', '// }')  # コメントアウト
            content = content.replace('rootProject.name = ', '// rootProject.name = ')  # コメントアウト
            content = content.replace('include(', 'include(')  # そのまま
            content = content.replace('val flutterSdkPath', 'def flutterSdkPath')  # val → def
            content = content.replace('val localPropertiesFile', 'def localPropertiesFile')  # val → def
            content = content.replace('val properties', 'def properties')  # val → def
            content = content.replace('.toFile()', '')  # .toFile() を削除
            content = content.replace('properties.getProperty("flutter.sdk")', 'properties.getProperty("flutter.sdk")')  # そのまま
            content = content.replace('apply(from:', 'apply from:')  # apply(from: → apply from:
            content = content.replace('apply {', '// apply {')  # コメントアウト
            content = content.replace('}.from(', '// }.from(')  # コメントアウト
            
            # 従来形式の settings.gradle ファイルを作成
            new_content = '''// Flutter Android プロジェクト用の標準 settings.gradle
include ':app'

def flutterSdkPath = properties.getProperty("flutter.sdk")
assert flutterSdkPath != null, "flutter.sdk not set in local.properties"
apply from: "$flutterSdkPath/packages/flutter_tools/gradle/app_plugin_loader.gradle"
'''
            
            # 通常の settings.gradle として保存
            with open(settings_gradle, 'w') as f:
                f.write(new_content)
                
            # 元の .kts ファイルの名前変更（無効化）
            os.rename(settings_gradle_kts, f"{settings_gradle_kts}.disabled")
            print("✅ settings.gradle.kts を標準形式の settings.gradle に変換しました")
            
        except Exception as e:
            print(f"⚠️ settings.gradle.kts の変換中にエラー: {e}")
            
            # エラーが発生した場合、シンプルバージョンの settings.gradle を作成
            with open(settings_gradle, 'w') as f:
                f.write('''include ':app'

def localPropertiesFile = new File(rootProject.projectDir, "local.properties")
def properties = new Properties()

assert localPropertiesFile.exists()
localPropertiesFile.withReader("UTF-8") { reader -> properties.load(reader) }

def flutterSdkPath = properties.getProperty("flutter.sdk")
assert flutterSdkPath != null, "flutter.sdk not set in local.properties"
apply from: "$flutterSdkPath/packages/flutter_tools/gradle/app_plugin_loader.gradle"
''')
            print("✅ 代替の settings.gradle ファイルを作成しました")
    
    # 2. build.gradle.kts を修正（もし存在する場合）
    app_build_gradle_kts = os.path.join(android_dir, 'app', 'build.gradle.kts')
    app_build_gradle = os.path.join(android_dir, 'app', 'build.gradle')
    
    if os.path.exists(app_build_gradle_kts):
        print(f"📝 Kotlin DSL build.gradle.kts ファイルを通常の build.gradle に変換します")
        # バックアップを作成
        backup_file = f"{app_build_gradle_kts}.bak"
        shutil.copy2(app_build_gradle_kts, backup_file)
        
        # .kts ファイルを無効化（手動変換は複雑なため）
        os.rename(app_build_gradle_kts, f"{app_build_gradle_kts}.disabled")
        
        # AndroidManifestからパッケージ名を取得
        manifest_file = os.path.join(android_dir, 'app', 'src', 'main', 'AndroidManifest.xml')
        package_name = "com.example.gyroscopeapp"
        
        if os.path.exists(manifest_file):
            try:
                with open(manifest_file, 'r') as f:
                    manifest_content = f.read()
                
                package_match = re.search(r'package\s*=\s*[\'"]([^\'"]+)[\'"]', manifest_content)
                if package_match:
                    package_name = package_match.group(1)
            except:
                pass
        
        # 標準的な build.gradle ファイルを作成
        with open(app_build_gradle, 'w') as f:
            f.write(f'''def localProperties = new Properties()
def localPropertiesFile = rootProject.file('local.properties')
if (localPropertiesFile.exists()) {{
    localPropertiesFile.withReader('UTF-8') {{ reader ->
        localProperties.load(reader)
    }}
}}

def flutterRoot = localProperties.getProperty('flutter.sdk')
if (flutterRoot == null) {{
    throw new GradleException("Flutter SDK not found. Define location with flutter.sdk in the local.properties file.")
}}

def flutterVersionCode = localProperties.getProperty('flutter.versionCode')
if (flutterVersionCode == null) {{
    flutterVersionCode = '1'
}}

def flutterVersionName = localProperties.getProperty('flutter.versionName')
if (flutterVersionName == null) {{
    flutterVersionName = '1.0'
}}

apply plugin: 'com.android.application'
apply plugin: 'kotlin-android'
apply from: "$flutterRoot/packages/flutter_tools/gradle/flutter.gradle"

android {{
    namespace "{package_name}"
    compileSdkVersion flutter.compileSdkVersion
    ndkVersion flutter.ndkVersion

    compileOptions {{
        sourceCompatibility JavaVersion.VERSION_1_8
        targetCompatibility JavaVersion.VERSION_1_8
    }}

    kotlinOptions {{
        jvmTarget = '1.8'
    }}

    sourceSets {{
        main.java.srcDirs += 'src/main/kotlin'
    }}

    defaultConfig {{
        applicationId "{package_name}"
        // Flutter.gradle タスクで定義された最小 SDK バージョンと一致させる
        minSdkVersion flutter.minSdkVersion
        targetSdkVersion flutter.targetSdkVersion
        versionCode flutterVersionCode.toInteger()
        versionName flutterVersionName
    }}

    buildTypes {{
        release {{
            signingConfig signingConfigs.debug
        }}
    }}
}}

flutter {{
    source '../..'
}}

dependencies {{
    implementation "org.jetbrains.kotlin:kotlin-stdlib-jdk7:$kotlin_version"
}}
''')
        print("✅ 標準形式の build.gradle ファイルを作成しました")
    
    # 3. Gradle キャッシュをクリア
    print("\n🧹 Gradle キャッシュをクリアしています...")
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
                print(f"⚠️ キャッシュ削除エラー: {e}")
    
    print("\n✅ Kotlin DSL Gradleファイルの互換性問題の修正が完了しました")
    return True

def fix_ndk_version(build_error_output, verbose=False):
    """Android NDKバージョンの不一致を自動修正する"""
    print("\n🔍 Android NDKバージョンの不一致を検出・修正しています...")
    
    # エラーメッセージから必要なNDKバージョンを抽出
    required_ndk_version = "27.0.12077973"  # デフォルト値
    
    ndk_version_match = re.search(r'requires Android NDK ([0-9.]+)', build_error_output)
    if (ndk_version_match):
        required_ndk_version = ndk_version_match.group(1)
    
    print(f"🔧 Android NDKバージョンを {required_ndk_version} に更新します...")
    
    # プロジェクトのルートディレクトリからAndroidディレクトリを取得
    android_dir = os.path.join(os.getcwd(), 'android')
    
    # build.gradle.kts または build.gradle を更新
    app_build_gradle_kts = os.path.join(android_dir, 'app', 'build.gradle.kts')
    app_build_gradle = os.path.join(android_dir, 'app', 'build.gradle')
    
    updated = False
    
    # Kotlin DSLファイル(.kts)が存在する場合
    if os.path.exists(app_build_gradle_kts):
        try:
            with open(app_build_gradle_kts, 'r') as f:
                content = f.read()
            
            # ndkVersionが存在するか確認して更新または追加
            if 'ndkVersion' in content:
                content = re.sub(r'ndkVersion\s*=\s*[\'"]([^\'"]+)[\'"]', f'ndkVersion = "{required_ndk_version}"', content)
            else:
                content = re.sub(r'android\s*\{', f'android {{\n    ndkVersion = "{required_ndk_version}"', content)
            
            with open(app_build_gradle_kts, 'w') as f:
                f.write(content)
            
            print(f"✅ {app_build_gradle_kts} のNDKバージョンを {required_ndk_version} に設定しました")
            updated = True
        except Exception as e:
            print(f"⚠️ Kotlin DSL Gradle設定の更新エラー: {e}")
    
    # 通常のGradleファイルが存在する場合
    if os.path.exists(app_build_gradle) and not updated:
        try:
            with open(app_build_gradle, 'r') as f:
                content = f.read()
            
            # ndkVersionが存在するか確認して更新または追加
            if 'ndkVersion' in content:
                content = re.sub(r'ndkVersion[\s\t]*[\'"]([^\'"]+)[\'"]', f'ndkVersion "{required_ndk_version}"', content)
            else:
                content = re.sub(r'android\s*\{', f'android {{\n    ndkVersion "{required_ndk_version}"', content)
            
            with open(app_build_gradle, 'w') as f:
                f.write(content)
            
            print(f"✅ {app_build_gradle} のNDKバージョンを {required_ndk_version} に設定しました")
            updated = True
        except Exception as e:
            print(f"⚠️ Gradle設定の更新エラー: {e}")
    
    # ファイルが見つからない場合
    if not updated:
        print("⚠️ build.gradleファイルが見つかりません。手動での修正が必要です。")
        return False
    
    # Gradleキャッシュをクリアして設定を反映
    print("\n🧹 NDK設定変更を反映するためキャッシュをクリアしています...")
    cache_dirs = [
        os.path.join(android_dir, '.gradle'),
        os.path.join(android_dir, 'app', 'build')
    ]
    
    for cache_dir in cache_dirs:
        if os.path.exists(cache_dir):
            try:
                shutil.rmtree(cache_dir)
                if verbose:
                    print(f"✅ キャッシュを削除: {cache_dir}")
            except Exception as e:
                if verbose:
                    print(f"⚠️ キャッシュ削除エラー: {e}")
    
    return True

def build_apk(output_dir=None, build_type="release", verbose=False):
    """APKファイルをビルドする"""
    print("\n📦 APKファイルをビルドしています...")
    
    # まずFlutter pub getを実行してパッケージを更新
    run_command("flutter pub get", "Flutter パッケージ取得", show_output=verbose)
    
    build_cmd = "flutter build apk"
    if build_type == "debug":
        build_cmd += " --debug"
    elif build_type == "profile":
        build_cmd += " --profile"
    else:  # release モード（デフォルト）
        build_cmd += " --release"
    
    # 出力ディレクトリが指定されている場合
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        # カスタム出力先を設定
        build_cmd += f" --split-per-abi"
    
    if verbose:
        print(f"実行: {build_cmd}")
    
    result = run_command(build_cmd, "APKビルド", show_output=verbose)
    
    if not result[0]:
        error_output = result[1] if isinstance(result, tuple) and len(result) > 1 else ""
        print("❌ APKビルドに失敗しました")
        
        # NDKバージョンエラーを検出して修正
        if "requires Android NDK" in str(error_output):
            print("\n🔍 NDKバージョンの問題を検出しました。自動修正を試みます...")
            if fix_ndk_version(str(error_output), verbose):
                print("\n🔄 NDKバージョン修正後に再ビルドを実行します...")
                return build_apk(output_dir, build_type, verbose)  # 再帰呼び出し
        return False
    
    # ビルド成功、APKファイルの場所を表示
    apk_path = os.path.join(os.getcwd(), "build", "app", "outputs", "flutter-apk")
    apk_files = []
    
    if os.path.exists(apk_path):
        for file in os.listdir(apk_path):
            if file.endswith(".apk"):
                apk_files.append(os.path.join(apk_path, file))
                
                # 出力ディレクトリが指定されている場合はコピー
                if output_dir:
                    dest_path = os.path.join(output_dir, file)
                    shutil.copy2(os.path.join(apk_path, file), dest_path)
                    print(f"✅ APKファイルをコピーしました: {dest_path}")
    
    if apk_files:
        print("\n✅ APKファイルが生成されました:")
        for apk_file in apk_files:
            print(f"  - {apk_file}")
        return True
    else:
        print("\n⚠️ APKファイルが見つかりません")
        return False

def main():
    """メイン実行関数"""
    # カレントディレクトリをプロジェクトのルートに変更（安全のため）
    os.chdir(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
    
    parser = argparse.ArgumentParser(description="Flutter アプリケーションのAndroidエミュレータでの実行")
    parser.add_argument('--verbose', action='store_true', help='詳細な出力を表示')
    parser.add_argument('--no-clean', action='store_true', help='クリーンビルドをスキップ')
    parser.add_argument('--list', action='store_true', help='利用可能なエミュレータの一覧を表示するだけ')
    parser.add_argument('--emulator', type=str, help='使用するエミュレータの名前またはインデックス番号')
    parser.add_argument('--build-apk', action='store_true', help='APKファイルをビルドする')
    parser.add_argument('--apk-output', type=str, help='APKファイルの出力ディレクトリ', default="apk_output")
    parser.add_argument('--apk-type', type=str, choices=['debug', 'profile', 'release'], 
                        default='release', help='APKのビルドタイプ (debug/profile/release)')
    args = parser.parse_args()
    
    print("=== ジャイロスコープアプリ Android エミュレータ 自動ビルド＆実行スクリプト ===")
    
    # Flutter環境のチェック
    if not check_flutter_installation():
        return 1
    
    # Android SDK環境のチェック
    if not check_android_sdk():
        return 1
    
    # プロジェクトディレクトリの確認
    if not check_project_directory():
        return 1
    
    # 出力フォルダの準備
    prepare_output_directory()
    
    # APKビルドのみのモードかチェック
    if args.build_apk:
        print("\n📱 APKビルドモードが選択されました")
        
        # プラグインの互換性チェックを追加
        print("\n🔍 Flutter プラグインの互換性をチェックしています...")
        plugin_check_result = check_flutter_plugins()
        
        # build.gradle.ktsの修正を試みる（NDKバージョン問題の修正）
        gradle_fix_result = fix_build_gradle_kts()
        
        # APKをビルド
        apk_result = build_apk(args.apk_output, args.apk_type, args.verbose)
        return 0 if apk_result else 1
    
    # 利用可能なエミュレータの一覧を取得
    emulators = get_available_emulators()
    print_emulator_list(emulators)
    
    # 一覧表示のみの場合はここで終了
    if args.list or not emulators:
        return 0 if emulators else 1
    
    # エミュレータの選択
    selected_emulator = select_emulator(args, emulators)
    if not selected_emulator:
        return 1
    
    android_version = selected_emulator.get('android_version', 'バージョン不明')
    print(f"\n✅ 選択されたエミュレータ: {selected_emulator['name']} (Android {android_version})")
    
    # ビルドと実行
    try:
        # プラグインの互換性チェックを追加
        print("\n🔍 Flutter プラグインの互換性をチェックしています...")
        plugin_check_result = check_flutter_plugins()
        
        # build.gradle.ktsの修正を試みる（NDKバージョン問題の修正）
        gradle_fix_result = fix_build_gradle_kts()
        
        # アプリの実行を試みる前にJavaバージョンを確認
        java_info = get_java_version_info()
        print(f"\n🔍 Javaバージョンを確認: {java_info}")
        
        # アプリの実行を試みる
        build_result = build_and_run_android_emulator(selected_emulator['name'], args.verbose, args.no_clean)
        build_error_output = ""  # エラー出力を格納する変数
        
        if isinstance(build_result, tuple) and len(build_result) > 1:
            build_result_status = build_result[0]
            build_error_output = str(build_result[1])
        else:
            build_result_status = build_result
            
        if build_result_status:
            print("\n✨ アプリの実行が終了しました")
            return 0
        else:
            print("\n⚠️ アプリの実行中に問題が発生しました")
            
            # 特定のエラーパターンを検出
            kotlin_dsl_error = "Kotlin DSL" in build_error_output or ".kts" in build_error_output
            java_gradle_error = "Unsupported class file major version" in build_error_output or "incompatible with the Java" in build_error_output
            ndk_version_error = "Your project is configured with Android NDK" in build_error_output and "requires Android NDK" in build_error_output
            
            # エラーの重大度に応じた修復フローを実行
            android_dir = os.path.join(os.getcwd(), 'android')
            tried_fixes = []
            
            # 0. まずNDKバージョン問題を確認・修正（プラグインの互換性に関わる問題）
            if ndk_version_error:
                print("\n🔍 Android NDKバージョンの不一致を検出しました...")
                # 必要なNDKバージョンを抽出
                ndk_version_match = re.search(r'requires Android NDK ([0-9.]+)', build_error_output)
                required_ndk_version = ndk_version_match.group(1) if ndk_version_match else "27.0.12077973"  # デフォルト値
                
                print(f"🔧 Android NDKバージョンを {required_ndk_version} に更新します...")
                
                # build.gradle.kts または build.gradle を更新
                app_build_gradle_kts = os.path.join(android_dir, 'app', 'build.gradle.kts')
                app_build_gradle = os.path.join(android_dir, 'app', 'build.gradle')
                
                if os.path.exists(app_build_gradle_kts):
                    # Kotlin DSLファイル(.kts)の場合
                    with open(app_build_gradle_kts, 'r') as f:
                        content = f.read()
                    
                    # ndkVersionが存在するか確認して更新または追加
                    if 'ndkVersion' in content:
                        content = re.sub(r'ndkVersion\s*=\s*[\'"]([^\'"]+)[\'"]', f'ndkVersion = "{required_ndk_version}"', content)
                    else:
                        # androidブロックにndkVersionを追加
                        content = re.sub(r'android\s*\{', f'android {{\n    ndkVersion = "{required_ndk_version}"', content)
                    
                    with open(app_build_gradle_kts, 'w') as f:
                        f.write(content)
                    
                    print(f"✅ {app_build_gradle_kts} のNDKバージョンを {required_ndk_version} に設定しました")
                
                elif os.path.exists(app_build_gradle):
                    # 通常のGradleファイルの場合
                    with open(app_build_gradle, 'r') as f:
                        content = f.read()
                    
                    # ndkVersionが存在するか確認して更新または追加
                    if 'ndkVersion' in content:
                        content = re.sub(r'ndkVersion\s*[\'"]([^\'"]+)[\'"]', f'ndkVersion "{required_ndk_version}"', content)
                    else:
                        # androidブロックにndkVersionを追加
                        content = re.sub(r'android\s*\{', f'android {{\n    ndkVersion "{required_ndk_version}"', content)
                    
                    with open(app_build_gradle, 'w') as f:
                        f.write(content)
                    
                    print(f"✅ {app_build_gradle} のNDKバージョンを {required_ndk_version} に設定しました")
                
                tried_fixes.append("NDKバージョン修正")
                
                # NDKバージョン修正後に再ビルド
                print("\n🔄 NDKバージョン修正後に再ビルドを実行します...")
                if build_and_run_android_emulator(selected_emulator['name'], args.verbose, False):
                    print("\n✨ NDKバージョン修正後、アプリの実行が成功しました")
                    return 0
            
            # 1. まずKotlin DSL問題を確認・修正（最も一般的な問題）
            print("\n🔍 Kotlin DSL (.kts) の互換性問題を確認しています...")
            kotlin_dsl_files = []
            if os.path.exists(os.path.join(android_dir, 'settings.gradle.kts')):
                kotlin_dsl_files.append("settings.gradle.kts")
            if os.path.exists(os.path.join(android_dir, 'app', 'build.gradle.kts')):
                kotlin_dsl_files.append("app/build.gradle.kts")
                
            if kotlin_dsl_files or kotlin_dsl_error:
                print(f"🚨 Kotlin DSL ファイルが検出されました: {', '.join(kotlin_dsl_files) if kotlin_dsl_files else '(エラー出力から検出)'}")
                print("  Kotlin DSLを標準Groovy形式に変換します...")
                fix_kotlin_dsl_issues()
                tried_fixes.append("Kotlin DSL修正")
                
                # Kotlin DSL修正後に再ビルド
                print("\n🔄 Kotlin DSL修正後に再ビルドを実行します...")
                if build_and_run_android_emulator(selected_emulator['name'], args.verbose, False):
                    print("\n✨ Kotlin DSL修正後、アプリの実行が成功しました")
                    return 0
            
            # 2. 次にJava/Gradle互換性問題を確認・修正
            print("\n🔍 Java/Gradle互換性問題を確認しています...")
            if java_gradle_error or "Unsupported class file major version" in java_info or "incompatible with the Java" in java_info:
                print("\n🚨 Java/Gradle互換性問題を検出しました。自動修正を実行します...")
                run_java_gradle_fix()
                tried_fixes.append("Java/Gradle互換性修正")
                
                print("\n🔄 Java/Gradle互換性修復後に再ビルドを実行します...")
                if build_and_run_android_emulator(selected_emulator['name'], args.verbose, False):
                    print("\n✨ Java/Gradle互換性修復後、アプリの実行が成功しました")
                    return 0
            
            # 3. プラグインの問題を修正
            print("\n🔍 Flutter プラグインの互換性問題を確認しています...")
            from plugin_helper import fix_vibration_plugin
            fix_result = fix_vibration_plugin()
            if fix_result:
                tried_fixes.append("Vibrationプラグイン修正")
                print("\n🔄 プラグイン修正後に再ビルドを実行します...")
                if build_and_run_android_emulator(selected_emulator['name'], args.verbose, False):
                    print("\n✨ プラグイン修正後、アプリの実行が成功しました")
                    return 0
            
            # 4. 最後の手段：Android ディレクトリの完全再構築
            if len(tried_fixes) > 0:
                print(f"\n⚠️ 試した修正 ({', '.join(tried_fixes)}) では問題が解決しませんでした")
                print("\n🚨 最終手段：Androidディレクトリを完全に再構築します...")
                try:
                    android_backup = f"{android_dir}_backup_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
                    shutil.move(android_dir, android_backup)
                    print(f"✅ 既存のAndroidディレクトリをバックアップしました: {android_backup}")
                    run_command("flutter create --platforms=android .", "Androidプラットフォームを再生成", show_output=True)
                    if os.path.exists(android_dir):
                        print("✅ Androidディレクトリを再作成しました")
                        run_command("flutter pub get", "パッケージを再取得", show_output=True)
                        if build_and_run_android_emulator(selected_emulator['name'], args.verbose, False):
                            print("\n✨ Android再構築後、アプリの実行が成功しました")
                            return 0
                except Exception as rebuild_error:
                    print(f"⚠️ 再構築中にエラーが発生しました: {rebuild_error}")
            
            # すべての修正が失敗したケース
            print("\n⚠️ すべての修復方法を試しましたが、問題が解決しませんでした。")
            print("手動での対応をお勧めします - Android Studioで直接プロジェクトを開いてみてください。")
            
            # エラーログ保存
            log_filename = f"android_emulator_error_log_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            try:
                with open(log_filename, 'w') as f:
                    f.write("=== Androidエミュレータ実行エラーログ ===\n")
                    f.write(f"日時: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"エミュレータ: {selected_emulator['name']} (Android {android_version})\n")
                    f.write(f"Flutterバージョン: {get_flutter_version()}\n")
                    f.write(f"試行済み修正: {', '.join(tried_fixes)}\n")
                    f.write("エラーメッセージ:\n")
                    f.write(f"{build_error_output}\n")
                print(f"\nエラーログを保存しました: {log_filename}")
            except Exception as e:
                print(f"エラーログの保存に失敗しました: {e}")
            return 1
    
    except Exception as e:
        print(f"\n予期せぬエラーが発生しました: {e}")
        log_filename = f"android_emulator_error_log_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        # エラーログを保存
        try:
            with open(log_filename, 'w') as f:
                f.write("=== Androidエミュレータ実行エラーログ ===\n")
                f.write(f"日時: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"エミュレータ: {selected_emulator['name']} (Android {android_version})\n")
                f.write(f"Flutterバージョン: {get_flutter_version()}\n")
                f.write("エラーメッセージ:\n")
                f.write(f"{str(e)}\n")
            print(f"\nエラーログを保存しました: {log_filename}")
        except Exception as e:
            print(f"エラーログの保存に失敗しました: {e}")
        return 1

if __name__ == "__main__":
    try:
        exit(main())
    except KeyboardInterrupt:
        print("\n\n⚠️ ユーザーによりプログラムが中断されました")
        exit(1)
