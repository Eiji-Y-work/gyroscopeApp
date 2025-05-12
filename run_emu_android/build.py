#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
from utils import run_command
from emulator import boot_emulator

def update_gradle_ndk_version(ndk_version):
    """build.gradleファイルのNDKバージョンを更新する"""
    print(f"🔧 build.gradleファイルのNDKバージョンを {ndk_version} に更新しています...")
    
    # プロジェクトのbuild.gradleファイルのパス
    app_build_gradle = os.path.join(os.getcwd(), 'android', 'app', 'build.gradle')
    project_build_gradle = os.path.join(os.getcwd(), 'android', 'build.gradle')
    
    files_to_check = [app_build_gradle, project_build_gradle]
    updated = False
    
    for gradle_file in files_to_check:
        if os.path.exists(gradle_file):
            try:
                print(f"  Gradleファイルを処理中: {gradle_file}")
                with open(gradle_file, 'r') as f:
                    content = f.read()
                
                # ndkVersionの行を探して置換
                if 'ndkVersion' in content:
                    # 既存のNDKバージョン行を検索して表示
                    ndk_line_match = re.search(r'.*ndkVersion\s+[\'"].*?[\'"].*', content)
                    if ndk_line_match:
                        old_line = ndk_line_match.group(0).strip()
                        print(f"    検出した設定行: {old_line}")
                    
                    # 置換処理
                    old_content = content
                    new_content = re.sub(
                        r'ndkVersion\s+[\'"].*?[\'"]',
                        f'ndkVersion "{ndk_version}"',
                        content
                    )
                    
                    # 変更があれば保存
                    if new_content != old_content:
                        with open(gradle_file, 'w') as f:
                            f.write(new_content)
                        print(f"✅ {gradle_file} のNDKバージョンを {ndk_version} に更新しました")
                        updated = True
                    else:
                        print(f"⚠️ {gradle_file} の内容が変更されませんでした。既に同じ設定の可能性があります。")
            except Exception as e:
                print(f"⚠️ gradleファイルの更新中にエラーが発生しました: {e}")
    
    return updated

def check_and_fix_ndk_versions():
    """ビルド前にNDKバージョンの不一致を検出して修正する"""
    print("🔍 NDKバージョン設定を事前チェックしています...")
    
    android_dir = os.path.join(os.getcwd(), 'android')
    if not os.path.exists(android_dir):
        print("⚠️ Androidディレクトリが見つかりません")
        return False

    # NDKバージョン情報を格納する変数
    ndk_dir_version = None
    gradle_ndk_version = None
    
    # 1. local.propertiesからndk.dirを取得
    local_props_path = os.path.join(android_dir, 'local.properties')
    if os.path.exists(local_props_path):
        try:
            with open(local_props_path, 'r') as f:
                content = f.read()
            
            ndk_dir_match = re.search(r'ndk\.dir=(.+?)[\r\n]', content)
            if ndk_dir_match:
                ndk_dir_path = ndk_dir_match.group(1).strip()
                version_match = re.search(r'/ndk/([0-9.]+)', ndk_dir_path)
                if version_match:
                    ndk_dir_version = version_match.group(1)
                    print(f"  📌 local.properties内のNDKバージョン: {ndk_dir_version}")
        except Exception as e:
            print(f"  ⚠️ local.propertiesの読み取り中にエラー: {e}")
    
    # 2. build.gradleからndkVersionを取得
    gradle_files = []
    for root, dirs, files in os.walk(android_dir):
        for file in files:
            if file.endswith('.gradle'):
                gradle_files.append(os.path.join(root, file))
    
    # app/build.gradleを優先的に処理
    app_build_gradle = os.path.join(android_dir, 'app', 'build.gradle')
    if app_build_gradle in gradle_files:
        gradle_files.remove(app_build_gradle)
        gradle_files.insert(0, app_build_gradle)
    
    for gradle_file in gradle_files:
        try:
            with open(gradle_file, 'r') as f:
                content = f.read()
            
            ndk_version_match = re.search(r'ndkVersion\s+[\'"]([0-9.]+)[\'"]', content)
            if ndk_version_match:
                gradle_ndk_version = ndk_version_match.group(1)
                print(f"  📌 {os.path.basename(gradle_file)}内のNDKバージョン: {gradle_ndk_version}")
                break  # 最初に見つかったバージョンを使用
        except Exception as e:
            print(f"  ⚠️ {gradle_file}の読み取り中にエラー: {e}")
    
    # 3. バージョン不一致チェック
    if ndk_dir_version and gradle_ndk_version and ndk_dir_version != gradle_ndk_version:
        print(f"⚠️ NDKバージョン不一致を検出: ndk.dir({ndk_dir_version}) ≠ ndkVersion({gradle_ndk_version})")
        print("🔧 自動修正を試みます...")
        
        # ndk.dirのバージョンを優先して使用（実際のインストール済みバージョン）
        modified_files = direct_update_ndk_version(ndk_dir_version)
        if modified_files:
            print(f"✅ {len(modified_files)}個のファイルを更新しました")
            return True
    
    # 4. 明示的なndkVersion設定がない場合（潜在的な問題を回避）
    elif ndk_dir_version and not gradle_ndk_version:
        print(f"⚠️ build.gradleファイルにndkVersion設定がありません。ndk.dirのバージョンを使用します: {ndk_dir_version}")
        modified_files = direct_update_ndk_version(ndk_dir_version)
        if modified_files:
            print(f"✅ {len(modified_files)}個のファイルを更新しました")
            return True
    
    return False

def direct_update_ndk_version(ndk_version):
    """build.gradleファイルを直接検索して更新する"""
    print(f"🔎 プロジェクト内のすべてのbuild.gradleファイルを検索し、NDK設定を更新します...")
    
    # Androidディレクトリをルートとして検索
    android_dir = os.path.join(os.getcwd(), 'android')
    if not os.path.exists(android_dir):
        print(f"⚠️ Androidディレクトリが見つかりません: {android_dir}")
        return []
    
    modified_files = []
    ndk_dir_version = None
    
    # local.propertiesファイルを最初に優先的に処理して、実際のNDKパスを取得
    local_props_path = os.path.join(android_dir, 'local.properties')
    if os.path.exists(local_props_path):
        print(f"  チェック中: {local_props_path}")
        try:
            with open(local_props_path, 'r') as f:
                content = f.read()
            
            # ndk.dirの行からバージョン情報を抽出
            if 'ndk.dir=' in content:
                ndk_dir_match = re.search(r'ndk\.dir=(.+?)[\r\n]', content)
                if ndk_dir_match:
                    ndk_dir_path = ndk_dir_match.group(1).strip()
                    print(f"  📌 検出したNDKパス: {ndk_dir_path}")
                    
                    # パスからバージョンを抽出
                    version_match = re.search(r'/ndk/([0-9.]+)', ndk_dir_path)
                    if version_match:
                        ndk_dir_version = version_match.group(1)
                        print(f"  📌 抽出したNDKバージョン: {ndk_dir_version}")
                        # 見つかった場合は、このバージョンを使用
                        if ndk_dir_version != ndk_version and ndk_dir_version:
                            print(f"  ⚠️ NDKバージョン不一致: ndk.dir({ndk_dir_version}) ≠ 指定値({ndk_version})")
                            print(f"  💡 ndk.dirで検出されたバージョン {ndk_dir_version} を優先して使用します")
                            ndk_version = ndk_dir_version
                
                # ndk.dir行をコメントアウト（GradleファイルにndkVersionを設定した後で無効化）
                old_content = content
                new_content = re.sub(
                    r'ndk\.dir=.*',
                    f'# ndk.dir=disabled_by_script (ビルドエラー修正のため、代わりにndkVersionを使用)',
                    content
                )
                if new_content != old_content:
                    with open(local_props_path, 'w') as f:
                        f.write(new_content)
                    print(f"  ✅ {local_props_path} のNDK設定を無効化しました")
                    modified_files.append(local_props_path)
        except Exception as e:
            print(f"  ⚠️ {local_props_path} の処理中にエラー: {e}")
    
    # すべてのgradleファイルを再帰的に検索
    for root, dirs, files in os.walk(android_dir):
        for file in files:
            if file.endswith('.gradle') or file.endswith('.properties'):
                full_path = os.path.join(root, file)
                # local.propertiesは既に処理済みなのでスキップ
                if full_path == local_props_path:
                    continue
                
                try:
                    print(f"  チェック中: {full_path}")
                    file_modified = False
                    
                    with open(full_path, 'r') as f:
                        content = f.read()
                    
                    # ndkVersionの行を探して置換
                    new_content = content
                    if 'ndkVersion' in content:
                        # 既存のNDKバージョン行を検索して表示
                        ndk_line_match = re.search(r'.*ndkVersion\s+[\'"].*?[\'"].*', content)
                        if ndk_line_match:
                            old_line = ndk_line_match.group(0).strip()
                            old_version_match = re.search(r'ndkVersion\s+[\'"]([0-9.]+)[\'"]', old_line)
                            if old_version_match:
                                old_version = old_version_match.group(1)
                                print(f"    検出したndkVersion設定: {old_version}")
                                if old_version != ndk_version:
                                    print(f"    ⚠️ バージョン不一致: Gradle({old_version}) ≠ 必要なバージョン({ndk_version})")
                        
                        old_content = content
                        # より正確なパターンマッチングと置換
                        new_content = re.sub(
                            r'(ndkVersion\s*[\'"]).*?([\'"])',
                            r'\1' + ndk_version + r'\2',
                            content
                        )
                        if new_content != old_content:
                            file_modified = True
                    
                    # ndk.dirの行を探して置換（他のpropertiesファイル）
                    if 'ndk.dir' in new_content:
                        old_content = new_content
                        new_content = re.sub(
                            r'ndk\.dir=.*',
                            f'# ndk.dir=disabled_by_script (ビルドエラー修正のため無効化)',
                            new_content
                        )
                        if new_content != old_content:
                            file_modified = True
                    
                    # 変更があれば保存
                    if file_modified:
                        with open(full_path, 'w') as f:
                            f.write(new_content)
                        print(f"  ✅ {full_path} を更新しました")
                        modified_files.append(full_path)
                
                except Exception as e:
                    print(f"  ⚠️ {full_path} の処理中にエラー: {e}")
    
    # 特別なケース: app/build.gradleファイルにndkVersionがない場合は追加
    app_build_gradle = os.path.join(android_dir, 'app', 'build.gradle')
    if not os.path.exists(app_build_gradle) or app_build_gradle not in modified_files:
        try:
            # ファイルが存在するかチェック
            if os.path.exists(app_build_gradle):
                # ファイルはあるがndkVersionの記述がない場合は追加
                with open(app_build_gradle, 'r') as f:
                    content = f.read()
                
                if 'android {' in content and 'ndkVersion' not in content:
                    print(f"  💡 app/build.gradle にndkVersionがありません。追加します。")
                    # android { ブロックの直後にndkVersionを追加
                    new_content = re.sub(
                        r'(android\s*\{)',
                        f'\\1\n    ndkVersion "{ndk_version}"',
                        content
                    )
                    with open(app_build_gradle, 'w') as f:
                        f.write(new_content)
                    print(f"  ✅ {app_build_gradle} にNDKバージョン設定を追加しました")
                    modified_files.append(app_build_gradle)
        except Exception as e:
            print(f"  ⚠️ app/build.gradleファイルの処理中にエラー: {e}")
    
    return modified_files

def build_and_run_android_emulator(emulator_name, verbose=False, no_clean=False):
    """Flutterアプリをビルドして、Androidエミュレータで実行する"""
    print("\n🚀 FlutterアプリをAndroidエミュレータ用にビルドして実行します")
    
    # まずエミュレータを起動
    if not boot_emulator(emulator_name):
        return False
    
    # クリーンビルドが必要な場合
    if not no_clean:
        print("🧹 クリーンビルド実行中...")
        if not run_command("flutter clean", "クリーンビルド", show_output=verbose)[0]:
            return False
    
    # 依存関係の解決
    print("📦 依存パッケージを取得中...")
    if not run_command("flutter pub get", "依存関係の解決", show_output=verbose)[0]:
        return False
    
    # ビルド前にNDKバージョンをチェック・修正
    check_and_fix_ndk_versions()
    
    # エミュレータでFlutterアプリを実行
    print(f"📱 エミュレータ ({emulator_name}) でアプリを起動しています...")
    print("💡 終了するにはこのターミナルでCtrl+Cを押してください")
    
    # ADBを使用して正確なデバイスIDを取得
    success, adb_output = run_command("adb devices", "接続デバイス一覧", show_output=False)
    emulator_device_id = None
    
    if success and adb_output:
        output_text = adb_output.decode('utf-8') if isinstance(adb_output, bytes) else adb_output
        for line in output_text.strip().split('\n'):
            if "emulator-" in line and "device" in line:
                emulator_device_id = line.split()[0]
                print(f"✅ エミュレータデバイスIDを検出: {emulator_device_id}")
                break
    
    # 正確なデバイスIDが見つかった場合は直接指定してアプリを実行
    if emulator_device_id:
        run_cmd = f"flutter run -d {emulator_device_id}"
        success = run_command(run_cmd, "Androidエミュレータでアプリを実行", show_output=True, show_progress=True)[0]
        return success
    else:
        # デバイスIDが特定できない場合はデフォルトIDを使用
        print("⚠️ エミュレータIDが特定できません。デフォルトID（emulator-5554）を試します")
        run_cmd = "flutter run -d emulator-5554"
        success = run_command(run_cmd, "Androidエミュレータでアプリを実行", show_output=True, show_progress=True)[0]
        
        # 自動選択に失敗した場合は手動選択に切り替え
        if not success:
            print("⚠️ 自動デバイス選択に失敗しました。通常の実行方法を試します...")
            run_cmd = "flutter run"
            return run_command(run_cmd, "Androidエミュレータでアプリを実行（手動デバイス選択）", 
                              show_output=True, show_progress=True)[0]
        return success
