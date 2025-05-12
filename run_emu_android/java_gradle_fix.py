#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import shutil
import subprocess
import platform
import sys
import json

def get_java_version():
    """実行中のJavaバージョンを詳細に取得"""
    try:
        # Javaコマンドの場所を確認
        java_path = subprocess.run("which java" if platform.system() != "Windows" else "where java",
                                  shell=True, capture_output=True, text=True).stdout.strip()
        
        # Javaバージョン情報を取得
        result = subprocess.run(["java", "-version"], 
                               capture_output=True, text=True, stderr=subprocess.STDOUT)
        version_output = result.stdout
        
        # バージョン文字列から詳細情報を抽出
        java_info = {
            "path": java_path,
            "full_output": version_output,
            "major_version": 11  # デフォルト値
        }
        
        # メジャーバージョンを抽出
        if "version" in version_output:
            if '"1.8' in version_output:
                java_info["major_version"] = 8
            elif '"11' in version_output or "11." in version_output:
                java_info["major_version"] = 11
            elif '"17' in version_output or "17." in version_output:
                java_info["major_version"] = 17
            elif '"21' in version_output or "21." in version_output:
                java_info["major_version"] = 21
            
            match = re.search(r'version "([0-9.]+)', version_output)
            if match:
                java_info["version_string"] = match.group(1)
                
                # 単一の数字の場合はメジャーバージョン
                if match.group(1).isdigit():
                    java_info["major_version"] = int(match.group(1))
        
        print(f"✅ Java情報:\n  パス: {java_info['path']}\n  バージョン: {java_info.get('version_string', '不明')}\n  メジャーバージョン: {java_info['major_version']}")
        return java_info
    
    except Exception as e:
        print(f"⚠️ Javaバージョン検出エラー: {e}")
        return {"major_version": 11, "error": str(e)}  # デフォルト値

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
    print("\n🔧 Java/Gradle互換性問題を修正しています...")
    
    # 現在のJavaバージョンを詳細に検出
    java_info = get_java_version()
    java_version = java_info["major_version"]
    
    # Java 17には8.0以上、Java 11には7.xが最適
    if java_version >= 17:
        gradle_version = "8.0.2"
        kotlin_version = "1.8.10"
        agp_version = "7.3.0"
    elif java_version >= 11:
        gradle_version = "7.6.1" 
        kotlin_version = "1.7.10"
        agp_version = "7.2.0"
    else:  # Java 8
        gradle_version = "6.7.1"
        kotlin_version = "1.5.31" 
        agp_version = "4.1.3"
    
    print(f"✅ Java {java_version}に最適な設定:\n  - Gradle: {gradle_version}\n  - Kotlin: {kotlin_version}\n  - Android Gradle Plugin: {agp_version}")
    
    # プロジェクトのルートディレクトリ
    project_dir = os.getcwd()
    android_dir = os.path.join(project_dir, 'android')
    
    # 1. gradle-wrapper.propertiesを修正
    wrapper_props = os.path.join(android_dir, 'gradle', 'wrapper', 'gradle-wrapper.properties')
    if os.path.exists(wrapper_props):
        # バックアップを作成
        backup_file = f"{wrapper_props}.javafix.bak"
        shutil.copy2(wrapper_props, backup_file)
        
        # 新しいcontent作成
        with open(wrapper_props, 'w') as f:
            f.write(f"""distributionBase=GRADLE_USER_HOME
distributionPath=wrapper/dists
zipStoreBase=GRADLE_USER_HOME
zipStorePath=wrapper/dists
distributionUrl=https\\://services.gradle.org/distributions/gradle-{gradle_version}-all.zip
""")
        print(f"✅ gradle-wrapper.propertiesをGradle {gradle_version}に更新しました")
    else:
        print("⚠️ gradle-wrapper.propertiesが見つかりません")
        # ディレクトリを作成して新規作成
        os.makedirs(os.path.dirname(wrapper_props), exist_ok=True)
        with open(wrapper_props, 'w') as f:
            f.write(f"""distributionBase=GRADLE_USER_HOME
distributionPath=wrapper/dists
zipStoreBase=GRADLE_USER_HOME
zipStorePath=wrapper/dists
distributionUrl=https\\://services.gradle.org/distributions/gradle-{gradle_version}-all.zip
""")
        print(f"✅ 新しいgradle-wrapper.propertiesを作成しました")
    
    # 2. build.gradleファイルを修正
    root_gradle = os.path.join(android_dir, 'build.gradle')
    if os.path.exists(root_gradle):
        # バックアップを作成
        backup_file = f"{root_gradle}.javafix.bak"
        shutil.copy2(root_gradle, backup_file)
        
        with open(root_gradle, 'r') as f:
            content = f.read()
        
        # KotlinバージョンとAGPバージョンを更新
        content = re.sub(
            r'ext\.kotlin_version\s*=\s*[\'"].*?[\'"]', 
            f'ext.kotlin_version = "{kotlin_version}"', 
            content
        )
        
        content = re.sub(
            r'com\.android\.tools\.build:gradle:[^\'"]*[\'"]',
            f'com.android.tools.build:gradle:{agp_version}"',
            content
        )
        
        with open(root_gradle, 'w') as f:
            f.write(content)
        
        print("✅ build.gradleファイルを更新しました")
    else:
        print("⚠️ ルートbuild.gradleファイルが見つかりません")
    
    # 3. キャッシュをクリア
    cache_dirs = [
        os.path.join(android_dir, '.gradle'),
        os.path.join(android_dir, 'build'),
        os.path.join(android_dir, 'app', 'build')
    ]
    
    print("\n🧹 キャッシュをクリアしています...")
    for cache_dir in cache_dirs:
        if os.path.exists(cache_dir):
            try:
                shutil.rmtree(cache_dir)
                print(f"✅ キャッシュ削除: {cache_dir}")
            except Exception as e:
                print(f"⚠️ キャッシュ削除エラー: {e}")
    
    print("\n✅ Java/Gradle互換性修正が完了しました\n")
    return True

if __name__ == "__main__":
    fix_java_gradle_compatibility()
