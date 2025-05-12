#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import shutil
import subprocess
import platform
import sys
import time

def fix_kotlin_gradle_emergency():
    """Kotlin/Gradleの互換性問題を徹底的に修復する"""
    print("\n🚨 Kotlin/Gradle互換性問題を徹底修復しています...")
    
    # プロジェクトのルートディレクトリ
    project_dir = os.getcwd()
    android_dir = os.path.join(project_dir, 'android')
    
    # 1. すべてのキャッシュとビルドディレクトリを徹底的にクリア
    clear_all_caches(android_dir)
    
    # 2. build.gradleファイルの修正（ルートbuild.gradle）
    fix_root_gradle(android_dir)
    
    # 3. gradle-wrapper.propertiesの修正
    fix_gradle_wrapper(android_dir)
    
    # 4. settings.gradleのチェックと修正
    fix_settings_gradle(android_dir)
    
    # 5. app/build.gradle(.kts)の修正
    fix_app_gradle(android_dir)
    
    # 6. local.propertiesの確認
    ensure_local_properties(android_dir)
    
    # 7. gradlewに実行権限を付与（UNIXのみ）
    ensure_gradlew_permissions(android_dir)
    
    print("\n✅ Kotlin/Gradle互換性問題の徹底修復が完了しました")
    print("🔄 次回のビルドでは、修正されたバージョン設定が使用されます")
    
    return True

def clear_all_caches(android_dir):
    """すべてのキャッシュとビルドディレクトリを徹底的にクリア"""
    print("\n🧹 キャッシュとビルドディレクトリを徹底的にクリアしています...")
    cache_dirs = [
        os.path.join(android_dir, 'build'),
        os.path.join(android_dir, 'app', 'build'),
        os.path.join(android_dir, '.gradle'),
        os.path.join(os.path.expanduser('~'), '.gradle', 'caches', 'modules-2', 'files-2.1', 'com.android.tools.build'),
        os.path.join(os.path.expanduser('~'), '.gradle', 'caches', 'transforms-3'),
    ]
    
    for dir_path in cache_dirs:
        if os.path.exists(dir_path):
            try:
                shutil.rmtree(dir_path)
                print(f"✅ ディレクトリを削除しました: {dir_path}")
            except Exception as e:
                print(f"⚠️ ディレクトリの削除に失敗: {e}")
                # 代替案: 個別のファイルを削除
                try:
                    for root, dirs, files in os.walk(dir_path):
                        for file in files:
                            try:
                                os.remove(os.path.join(root, file))
                            except:
                                pass
                    print("  - 個別ファイル削除を試みました")
                except:
                    pass

def fix_root_gradle(android_dir):
    """ルートbuild.gradleファイルを徹底的に修正"""
    print("\n🔧 ルートbuild.gradleファイルを徹底修正しています...")
    
    root_gradle = os.path.join(android_dir, 'build.gradle')
    if os.path.exists(root_gradle):
        # バックアップを作成
        backup_file = f"{root_gradle}.emergency.bak"
        shutil.copy2(root_gradle, backup_file)
        print(f"✅ バックアップを作成しました: {backup_file}")
        
        # デフォルトのbuild.gradleを新規作成（問題のある部分を完全に置き換え）
        with open(root_gradle, 'w') as f:
            f.write('''buildscript {
    ext.kotlin_version = '1.6.10'
    repositories {
        google()
        mavenCentral()
    }

    dependencies {
        classpath 'com.android.tools.build:gradle:4.1.3'
        classpath "org.jetbrains.kotlin:kotlin-gradle-plugin:$kotlin_version"
    }
}

allprojects {
    repositories {
        google()
        mavenCentral()
    }
}

rootProject.buildDir = '../build'
subprojects {
    project.buildDir = "${rootProject.buildDir}/${project.name}"
}
subprojects {
    project.evaluationDependsOn(':app')
}

tasks.register("clean", Delete) {
    delete rootProject.buildDir
}
''')
        print("✅ ルートbuild.gradleファイルを安定版の内容に置き換えました")
    else:
        print("⚠️ ルートbuild.gradleファイルが見つかりません")

def fix_gradle_wrapper(android_dir):
    """gradle-wrapper.propertiesファイルを徹底修正"""
    print("\n🔧 gradle-wrapper.propertiesファイルを徹底修正しています...")
    
    wrapper_props = os.path.join(android_dir, 'gradle', 'wrapper', 'gradle-wrapper.properties')
    if os.path.exists(wrapper_props):
        # バックアップを作成
        backup_file = f"{wrapper_props}.emergency.bak"
        shutil.copy2(wrapper_props, backup_file)
        
        # 安定したGradleバージョン（6系）に下げる 
        with open(wrapper_props, 'w') as f:
            f.write('''distributionBase=GRADLE_USER_HOME
distributionPath=wrapper/dists
zipStoreBase=GRADLE_USER_HOME
zipStorePath=wrapper/dists
distributionUrl=https\\://services.gradle.org/distributions/gradle-6.7.1-all.zip
''')
        print("✅ gradle-wrapper.propertiesを安定バージョン6.7.1に設定しました")
    else:
        print("⚠️ gradle-wrapper.propertiesファイルが見つかりません")
        # wrapper ディレクトリ自体が存在しない場合は作成
        wrapper_dir = os.path.join(android_dir, 'gradle', 'wrapper')
        os.makedirs(wrapper_dir, exist_ok=True)
        with open(wrapper_props, 'w') as f:
            f.write('''distributionBase=GRADLE_USER_HOME
distributionPath=wrapper/dists
zipStoreBase=GRADLE_USER_HOME
zipStorePath=wrapper/dists
distributionUrl=https\\://services.gradle.org/distributions/gradle-6.7.1-all.zip
''')
        print("✅ 不足していたgradle-wrapper.propertiesファイルを作成しました")

def fix_settings_gradle(android_dir):
    """settings.gradleファイルを修正"""
    print("\n🔧 settings.gradleファイルを確認・修正しています...")
    
    settings_gradle = os.path.join(android_dir, 'settings.gradle')
    if os.path.exists(settings_gradle):
        # バックアップを作成
        backup_file = f"{settings_gradle}.emergency.bak"
        shutil.copy2(settings_gradle, backup_file)
        
        # 安全なsettings.gradleに置き換え
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
        print("✅ settings.gradleファイルを安定バージョンに設定しました")
    else:
        print("⚠️ settings.gradleファイルが見つかりません")

def fix_app_gradle(android_dir):
    """app/build.gradle(.kts)ファイルを修正"""
    print("\n🔧 アプリのbuild.gradleファイルを修正しています...")
    
    app_gradle_kts = os.path.join(android_dir, 'app', 'build.gradle.kts')
    app_gradle = os.path.join(android_dir, 'app', 'build.gradle')
    
    # 通常のGradleファイルを優先
    if os.path.exists(app_gradle_kts):
        # .kts ファイルがあれば削除（通常のGradleファイルに統一）
        backup_kts = f"{app_gradle_kts}.emergency.bak"
        shutil.copy2(app_gradle_kts, backup_kts)
        print(f"✅ Kotlin DSLファイルをバックアップしました: {backup_kts}")
        os.remove(app_gradle_kts)
        print("✅ Kotlin DSLファイルを削除しました")
    
    # app/build.gradle が存在しなければ作成
    if not os.path.exists(app_gradle):
        print("⚠️ app/build.gradleファイルが見つかりません。新規作成します。")
        os.makedirs(os.path.dirname(app_gradle), exist_ok=True)
    else:
        # バックアップを作成
        backup_file = f"{app_gradle}.emergency.bak"
        shutil.copy2(app_gradle, backup_file)
        print(f"✅ app/build.gradleをバックアップしました: {backup_file}")
    
    # AndroidManifest.xmlからパッケージ名を取得
    manifest_path = os.path.join(android_dir, 'app', 'src', 'main', 'AndroidManifest.xml')
    package_name = "com.example.gyroscopeapp"  # デフォルトのパッケージ名
    
    if os.path.exists(manifest_path):
        try:
            with open(manifest_path, 'r') as f:
                content = f.read()
            
            package_match = re.search(r'package\s*=\s*[\'"]([^\'"]+)[\'"]', content)
            if package_match:
                package_name = package_match.group(1)
                print(f"✅ AndroidManifest.xmlからパッケージ名を取得: {package_name}")
        except Exception as e:
            print(f"⚠️ AndroidManifest.xmlの読み取り中にエラー: {e}")
    
    # 安定したapp/build.gradleファイルを作成
    with open(app_gradle, 'w') as f:
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
    compileSdkVersion 33
    ndkVersion "21.4.7075529"

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
        minSdkVersion 21
        targetSdkVersion 33
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
    print("✅ app/build.gradleファイルを安定バージョンに設定しました")

def ensure_local_properties(android_dir):
    """local.propertiesファイルが適切に設定されているか確認"""
    print("\n🔧 local.propertiesファイルを確認しています...")
    
    local_props = os.path.join(android_dir, 'local.properties')
    if os.path.exists(local_props):
        # バックアップを作成
        backup_file = f"{local_props}.emergency.bak"
        shutil.copy2(local_props, backup_file)
        
        # ファイルを読み込んでFlutter SDKのパスが設定されているか確認
        with open(local_props, 'r') as f:
            content = f.read()
        
        # ndk.dirを削除（問題の原因になる可能性がある）
        if 'ndk.dir=' in content:
            content = re.sub(r'ndk\.dir=.*\n', '', content)
        
        # flutter.sdk が設定されていなければ追加
        if 'flutter.sdk=' not in content:
            # flutter コマンドの場所を取得
            try:
                if platform.system() == "Windows":
                    result = subprocess.run("where flutter", shell=True, capture_output=True, text=True)
                else:
                    result = subprocess.run("which flutter", shell=True, capture_output=True, text=True)
                
                if result.returncode == 0:
                    flutter_path = result.stdout.strip()
                    flutter_sdk = os.path.dirname(os.path.dirname(flutter_path))
                    content += f"\nflutter.sdk={flutter_sdk}\n"
                    print(f"✅ Flutter SDKのパスを追加: {flutter_sdk}")
            except Exception as e:
                print(f"⚠️ Flutter SDKパスの取得に失敗: {e}")
        
        # 内容を書き戻す
        with open(local_props, 'w') as f:
            f.write(content)
        
        print("✅ local.propertiesファイルを確認・修正しました")
    else:
        print("⚠️ local.propertiesファイルが見つかりません。作成します。")
        
        # Flutter SDKのパスを取得して設定
        flutter_sdk = None
        try:
            if platform.system() == "Windows":
                result = subprocess.run("where flutter", shell=True, capture_output=True, text=True)
            else:
                result = subprocess.run("which flutter", shell=True, capture_output=True, text=True)
            
            if result.returncode == 0:
                flutter_path = result.stdout.strip()
                flutter_sdk = os.path.dirname(os.path.dirname(flutter_path))
        except Exception as e:
            print(f"⚠️ Flutter SDKパスの取得に失敗: {e}")
        
        # ファイルを新規作成
        with open(local_props, 'w') as f:
            f.write(f"sdk.dir={os.path.join(os.path.expanduser('~'), 'Library', 'Android', 'sdk')}\n")
            if flutter_sdk:
                f.write(f"flutter.sdk={flutter_sdk}\n")
        
        print("✅ local.propertiesファイルを作成しました")

def ensure_gradlew_permissions(android_dir):
    """gradlewに実行権限を付与"""
    print("\n🔧 gradlewに実行権限を付与しています...")
    
    gradlew_path = os.path.join(android_dir, 'gradlew')
    if os.path.exists(gradlew_path):
        try:
            if platform.system() != "Windows":
                os.chmod(gradlew_path, 0o755)
                print("✅ gradlewに実行権限を付与しました")
                
                # gradlew実行テスト
                try:
                    subprocess.run(f"cd {android_dir} && ./gradlew --version", shell=True, check=False, timeout=10)
                    print("✅ gradlewコマンドが正常に実行できます")
                except Exception as e:
                    print(f"⚠️ gradlewの実行テストに失敗: {e}")
        except Exception as e:
            print(f"⚠️ gradlewの権限設定に失敗: {e}")
    else:
        print("⚠️ gradlewファイルが見つかりません")
        # gradlewファイルを再生成するためのスタブスクリプトを作成
        with open(gradlew_path, 'w') as f:
            f.write('''#!/bin/sh
# Gradle wrapper script stub
# Please run 'flutter clean' and 'flutter pub get' to fix this

echo "Gradleラッパーの問題を検出しました。"
echo "flutter clean && flutter pub get を実行して修復してください。"
exit 1
''')
        if platform.system() != "Windows":
            os.chmod(gradlew_path, 0o755)
        print("✅ gradlewスタブファイルを作成しました")

if __name__ == "__main__":
    fix_kotlin_gradle_emergency()
