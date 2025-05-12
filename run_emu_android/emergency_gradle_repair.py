#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import shutil
import subprocess

def emergency_gradle_repair():
    """Gradle関連の問題を緊急修復する（直接ファイルを置換）"""
    print("\n🚨 Gradleの緊急修復を実行しています...")
    
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
    
    print("\n✅ Gradle緊急修復が完了しました")
    
    # 7. Flutterプロジェクトをクリーンにする
    print("\n🧹 Flutterプロジェクトをクリーンにしています...")
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
    print("\n🧹 すべてのキャッシュをクリアしています...")
    
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
    print("\n🔧 Gradleラッパーを修正しています...")
    
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
    print("\n🔧 ルートbuild.gradleを修正しています...")
    
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
                content = content.replace(
                    'ext.kotlin_version =',
                    'ext.kotlin_version = "1.6.10" //'
                )
            else:
                # extブロックを追加
                content = content.replace(
                    'buildscript {',
                    'buildscript {\n    ext.kotlin_version = "1.6.10"'
                )
            
            # 3. repositoriesブロックを修正
            if 'repositories {' in content:
                if 'google()' not in content:
                    content = content.replace(
                        'repositories {',
                        'repositories {\n        google()'
                    )
                if 'mavenCentral()' not in content:
                    content = content.replace(
                        'repositories {',
                        'repositories {\n        mavenCentral()'
                    )
            
            with open(build_gradle, 'w') as f:
                f.write(content)
                
            print("✅ ルートbuild.gradleを修正しました")
        except Exception as e:
            print(f"⚠️ ルートbuild.gradleの修正に失敗: {e}")

def fix_app_build_gradle(android_dir):
    """アプリのbuild.gradle(.kts)を修正"""
    print("\n🔧 アプリのbuild.gradle(.kts)を修正しています...")
    
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
                    
                    import re
                    package_match = re.search(r'package\s*=\s*["\']([^"\']+)["\']', manifest_content)
                    if package_match:
                        package_name = package_match.group(1)
                except Exception:
                    pass
            
            # namespaceを追加
            if 'namespace' not in content:
                if is_kts:
                    content = content.replace(
                        'android {',
                        f'android {{\n    namespace = "{package_name}"'
                    )
                else:
                    content = content.replace(
                        'android {',
                        f'android {{\n    namespace "{package_name}"'
                    )
            
            # compileSdkバージョンを修正
            if is_kts:
                content = content.replace(
                    'compileSdk =',
                    'compileSdk = 33 //'
                )
            else:
                content = content.replace(
                    'compileSdkVersion',
                    'compileSdkVersion 33 //'
                )
            
            # NDKバージョンを修正
            if 'ndkVersion' in content:
                if is_kts:
                    content = re.sub(
                        r'ndkVersion\s*=\s*["\'].*?["\']',
                        'ndkVersion = "21.4.7075529"',
                        content
                    )
                else:
                    content = re.sub(
                        r'ndkVersion\s*["\'].*?["\']',
                        'ndkVersion "21.4.7075529"',
                        content
                    )
            else:
                if is_kts:
                    content = content.replace(
                        'android {',
                        'android {\n    ndkVersion = "21.4.7075529"'
                    )
                else:
                    content = content.replace(
                        'android {',
                        'android {\n    ndkVersion "21.4.7075529"'
                    )
            
            with open(gradle_file, 'w') as f:
                f.write(content)
                
            print("✅ アプリのbuild.gradle(.kts)を修正しました")
        except Exception as e:
            print(f"⚠️ アプリのbuild.gradle(.kts)の修正に失敗: {e}")

def fix_local_properties(android_dir):
    """local.properties を確認・修正"""
    print("\n🔧 local.propertiesを確認・修正しています...")
    
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
                content = re.sub(r'ndk\.dir=.*\n', '', content)
            
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
                    content += f"\nflutter.sdk={flutter_path}\n"
            
            with open(local_props, 'w') as f:
                f.write(content)
                
            print("✅ local.propertiesを修正しました")
        except Exception as e:
            print(f"⚠️ local.propertiesの修正に失敗: {e}")

def fix_gradlew_permissions(android_dir):
    """gradlewに実行権限を付与"""
    print("\n🔧 gradlewに実行権限を付与しています...")
    
    gradlew = os.path.join(android_dir, 'gradlew')
    if os.path.exists(gradlew):
        try:
            # UNIX系OSでのみ実行
            if os.name == 'posix':
                os.chmod(gradlew, 0o755)
                print("✅ gradlewに実行権限を付与しました")
        except Exception as e:
            print(f"⚠️ gradlewの権限設定に失敗: {e}")

# env_check.pyにimport関数を追加
def import_emergency_repair():
    """緊急修復モジュールをインポート"""
    from emergency_gradle_repair import emergency_gradle_repair
    return emergency_gradle_repair
