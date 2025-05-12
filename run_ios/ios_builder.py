#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import subprocess
import platform
import shutil
import time
import re
from pathlib import Path
from utils import run_command, check_cocoapods

def build_ios_debug(verbose=False, skip_clean=False, auto_install=False):
    """iOS用のデバッグビルドを作成"""
    if platform.system() != "Darwin":
        print("iOSビルドはmacOSでのみ実行できます。")
        return False

    # CocoaPodsチェックを追加
    if not check_cocoapods():
        print("⚠️ CocoaPodsがインストールされていないか、PATHに設定されていません。ビルドをスキップします。")
        return False

    # 開始時間を記録
    start_time = time.time()

    # クリーンビルドは時間がかかるのでスキップオプション
    if not skip_clean:
        clean_success, _ = run_command("flutter clean", "Flutterプロジェクトをクリーン", show_progress=True)
        if not clean_success:
            print("警告: クリーンに失敗しましたが、ビルドを続行します")
    else:
        print("クリーンステップをスキップします")

    # 依存関係を解決
    pub_success, _ = run_command("flutter pub get", "Flutter依存関係の解決", timeout=120, show_progress=True)
    if not pub_success:
        print("⚠️ 依存関係の解決に失敗しました。")
        return False
    
    # ポッドのインストール
    pod_success, _ = run_command("cd ios && pod install", "CocoaPodsのインストール", timeout=300, show_progress=True)
    if not pod_success:
        print("⚠️ CocoaPodsのインストールに失敗しました。")
        print("以下のコマンドを試してみてください:")
        print("cd ios && pod install --repo-update")
        
        # pod repo update の実行を提案
        print("\nPod repoを更新中...")
        run_command("pod repo update", "Pod Repo更新", timeout=300, show_progress=True)
        # 再試行
        pod_success, _ = run_command("cd ios && pod install --repo-update", 
                                  "CocoaPodsのインストール (リトライ)", 
                                  timeout=300, show_progress=True)
        if not pod_success:
            print("⚠️ CocoaPodsのインストールにまた失敗しました。")
            return False
    
    # ビルド前の追加フラグ
    extra_flags = "--verbose" if verbose else ""
    
    print("\n⏱️ iOSビルドには数分かかる場合があります。\n")
    
    # audioplayers_darwinパッケージの包括的な修正
    print("\n⚙️ audioplayers_darwin パッケージのSwiftファイルを修正しています...")
    
    # パスの取得とファイル権限の確保
    current_dir = os.path.dirname(os.path.abspath(__file__))
    fix_script_path = os.path.join(current_dir, "fix_audioplayers.sh")
    
    # スクリプトの実行権限を確保
    os.chmod(fix_script_path, 0o755)
    
    # 修正スクリプトの実行
    print(f"修正スクリプトを実行中: {fix_script_path}")
    fix_success, fix_output = run_command(fix_script_path, "Swift修正スクリプト", timeout=60, show_progress=True)
    print(fix_output)
    if fix_success:
        print("✅ audioplayers_darwin の修正に成功しました")
    else:
        print("⚠️ audioplayers_darwinの修正に失敗しましたが、ビルドを続行します")
    
    # 外部パッケージの警告を修正するためのパッチを適用
    print("\n依存パッケージの警告を修正するパッチを適用中...")
    
    # 問題のあるライブラリのパス
    pub_cache_dir = os.path.expanduser("~/.pub-cache/hosted/pub.dev")
    patch_targets = {
        "device_info_plus-11.4.0": {
            "file": "ios/device_info_plus/Sources/device_info_plus/FPPDeviceInfoPlusPlugin.m",
            "patches": [
                {
                    "search": "natural_t",
                    "replace": "vm_size_t"  # 型をvm_size_tに統一して精度損失を防ぐ
                }
            ]
        },
        "vibration-1.9.0": {
            "file": "ios/Classes/VibrationPluginSwift.swift",
            "patches": [
                {
                    "search": "var params",
                    "replace": "var _ /* params */"  # 未使用変数をアンダースコアに置き換え
                }
            ]
        }
    }
    
    # 他の依存パッケージも修正を試みる
    patch_applied = False
    for package, config in patch_targets.items():
        package_path = os.path.join(pub_cache_dir, package)
        file_path = os.path.join(package_path, config["file"])
        
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                
                original_content = content
                for patch in config["patches"]:
                    if patch["search"] in content:
                        content = content.replace(patch["search"], patch["replace"])
                
                # 変更があればファイルを上書き
                if content != original_content:
                    # バックアップを作成
                    backup_path = f"{file_path}.bak"
                    if not os.path.exists(backup_path):
                        shutil.copy2(file_path, backup_path)
                    
                    with open(file_path, 'w') as f:
                        f.write(content)
                    print(f"✅ パッチを適用: {file_path}")
                    patch_applied = True
            except Exception as e:
                print(f"⚠️ パッチ適用エラー ({package}): {e}")
    
    if not patch_applied:
        print("パッチ対象ファイルが見つからないか、既に修正済みです。")
    
    # 古いビルドの痕跡をクリーンアップ
    print("古いビルドファイルをクリーンアップしています...")
    stale_dirs = [
        "build/ios/Debug-iphoneos",
        "build/ios/Release-iphoneos",
        "ios/Pods",
        "ios/Flutter/Flutter.podspec",
        "ios/Flutter/ephemeral",
        ".dart_tool/flutter_build",
        "build/ios/iphonesimulator",
        "build/ios/iphoneos"
    ]
    for path in stale_dirs:
        if os.path.exists(path):
            try:
                if os.path.isdir(path):
                    shutil.rmtree(path)
                    print(f"削除: {path}")
                else:
                    os.remove(path)
                    print(f"削除: {path}")
            except Exception as e:
                print(f"警告: {path} の削除に失敗しました - {e}")
    
    # Podfileに警告抑制設定を追加
    podfile_path = "ios/Podfile"
    if os.path.exists(podfile_path):
        print("Podfileに警告抑制の設定を追加中...")
        try:
            with open(podfile_path, 'r') as f:
                content = f.read()
            
            # 既存の警告抑制設定がなければ追加
            if "post_install do |installer|" not in content:
                podfile_addition = """
post_install do |installer|
  installer.pods_project.targets.each do |target|
    target.build_configurations.each do |config|
      config.build_settings['GCC_WARN_INHIBIT_ALL_WARNINGS'] = 'YES'
      config.build_settings['SWIFT_SUPPRESS_WARNINGS'] = 'YES'
      
      # 非推奨APIの警告を抑制
      config.build_settings['CLANG_WARN_DEPRECATED_OBJC_IMPLEMENTATIONS'] = 'NO'
      config.build_settings['GCC_WARN_ABOUT_DEPRECATED_FUNCTIONS'] = 'NO'
      config.build_settings['CLANG_WARN_DEPRECATED_OBJC_IMPLEMENTATIONS'] = 'NO'
      
      # 型変換の警告を抑制
      config.build_settings['GCC_WARN_ABOUT_INCOMPATIBLE_POINTER_TYPES'] = 'NO'
      config.build_settings['GCC_WARN_64_TO_32_BIT_CONVERSION'] = 'NO'
      
      # 未使用変数の警告を抑制
      config.build_settings['GCC_WARN_UNUSED_VARIABLE'] = 'NO'
      config.build_settings['GCC_WARN_UNUSED_VALUE'] = 'NO'
      
      # M1 Macのサポート
      config.build_settings['EXCLUDED_ARCHS[sdk=iphonesimulator*]'] = 'arm64'
      
      # ビルド設定の更新
      config.build_settings['IPHONEOS_DEPLOYMENT_TARGET'] = '12.0'
    end
  end
end
"""
                with open(podfile_path, 'a') as f:
                    f.write(podfile_addition)
                print("✅ Podfileを更新しました")
        except Exception as e:
            print(f"警告: Podfileの更新に失敗しました - {e}")
    
    # ポッドの再インストール
    print("\nCocoaPodsを更新設定で再インストールしています...")
    run_command("cd ios && pod install --repo-update", 
                "CocoaPodsの再インストール", timeout=300, show_progress=True)
    
    # iOSビルド - コード署名のため--no-codesignフラグを削除し、警告を無視するフラグを追加
    build_success, _ = run_command(f"flutter build ios --debug {extra_flags} --no-tree-shake-icons", 
                               "iOSデバッグビルド", timeout=900, show_progress=True)
    if not build_success:
        print("⚠️ iOSビルドに失敗しました。")
        print("警告を無視してビルドを再試行します...")
        
        # 警告を無視してビルドを再試行
        os.environ["FLUTTER_XCODE_ONLY_SHOW_ERRORS"] = "1"  # 警告を表示しない環境変数
        build_success, _ = run_command(f"flutter build ios --debug {extra_flags} --no-tree-shake-icons --suppress-analytics", 
                                   "iOSデバッグビルド (警告無視)", timeout=900, show_progress=True)
        if not build_success:
            print("⚠️ iOSビルドに再度失敗しました。")
            return False
    
    # ビルド時間の計算
    build_duration = time.time() - start_time
    minutes, seconds = divmod(int(build_duration), 60)
    
    print(f"\n✅ iOSデバッグビルドが正常に作成されました (所要時間: {minutes}分{seconds}秒)")
    
    # 自動インストールが有効な場合はXcodeからの直接インストールを実行
    if auto_install:
        print("\nXcodeを通じて実機にアプリをインストールします...")
        return run_xcode_build_and_install()
    else:
        # Xcodeを開く
        print("Xcodeで開き、実機にインストールするには:")
        print("1. open ios/Runner.xcworkspace")
        print("2. 左上のデバイス選択から接続された実機を選択")
        print("3. ▶️ボタンをクリックしてビルド&インストール")
        
        subprocess.Popen("open ios/Runner.xcworkspace", shell=True)
        print("Xcodeが開かれました。左上のデバイス選択から接続された実機を選択し、▶️ボタンをクリックしてインストールしてください。")
    return True

def run_xcode_build_and_install():
    """XcodeビルドとRunを実行する（コード署名とインストールを含む）"""
    print("Xcodeでビルドとインストールを実行します...")
    
    # 接続されているデバイスを確認
    devices = get_connected_ios_devices()
    if not devices:
        print("⚠️ 接続されているiOSデバイスが見つかりません。")
        print("シミュレータを使用します。")
        # シミュレータIDを取得（なければ作成）
        simulator_id = get_or_create_simulator()
        if not simulator_id:
            print("⚠️ シミュレータの準備に失敗しました。")
            print("Xcodeを手動で開きます...")
            subprocess.Popen("open ios/Runner.xcworkspace", shell=True)
            return False
    else:
        # 最初のデバイスを選択
        device_id = devices[0]['id']
        print(f"使用するデバイス: {devices[0]['name']}")
    
    # Xcodeを開く
    workspace_path = "ios/Runner.xcworkspace"
    print("Xcodeを起動中...")
    subprocess.Popen(f"open {workspace_path}", shell=True)
    time.sleep(3)  # Xcodeが起動するまで待機
    
    # AppleScriptを使用してXcodeでの操作を自動化
    print("AppleScriptでXcodeの操作を実行中...")
    apple_script = '''
    tell application "Xcode"
        activate
        delay 3
        tell application "System Events"
            tell process "Xcode"
                -- プロジェクトがロードされるまで待機
                delay 3
                
                -- ツールバーの実行ボタンをクリック
                click button 1 of group 1 of toolbar 1 of window 1
                
                -- 署名やその他の問題が発生した場合のために少し長めに待機
                delay 5
                
                -- キーボードショートカットで実行 (コマンド+R)を実行
                -- これは標準のRun操作をトリガーするためのバックアップメソッド
                key code 15 using {command down}
            end tell
        end tell
    end tell
    '''
    
    # AppleScriptを一時ファイルに保存して実行
    script_path = "/tmp/xcode_run.scpt"
    with open(script_path, "w") as f:
        f.write(apple_script)
    
    print("Xcodeでアプリのビルドと実行を開始...")
    subprocess.run(f"osascript {script_path}", shell=True)
    
    print("✅ Xcodeでのビルドと実行リクエストを送信しました")
    print("⚠️ 注意: Xcodeで署名やプロビジョニングの設定が必要な場合は、画面を確認して必要な作業を行ってください")
    return True

def get_or_create_simulator():
    """利用可能なiOSシミュレータを取得または作成する"""
    try:
        # 利用可能なシミュレータの一覧を取得
        result = subprocess.run("xcrun simctl list devices available", 
                              shell=True, text=True, capture_output=True)
        
        if result.returncode != 0:
            return None
        
        # 利用可能なiPhone/iPadシミュレータを検索
        simulator_id = None
        for line in result.stdout.splitlines():
            if ("iPhone" in line or "iPad" in line) and "unavailable" not in line:
                # シミュレータIDを抽出
                sim_id_match = re.search(r'\(([\w-]+)\)', line)
                if sim_id_match:
                    simulator_id = sim_id_match.group(1)
                    simulator_name = line.split(" (")[0]
                    print(f"利用可能なシミュレータ: {simulator_name}")
                    break
        
        # シミュレータが見つからない場合は新しいものを作成
        if not simulator_id:
            print("利用可能なシミュレータが見つかりません。新しいシミュレータを作成中...")
            # 最新のiOSランタイムを取得
            runtime_result = subprocess.run("xcrun simctl list runtimes", 
                                          shell=True, text=True, capture_output=True)
            ios_runtime = None
            for line in runtime_result.stdout.splitlines():
                if "iOS" in line and "available" in line:
                    ios_runtime_match = re.search(r'com\.apple\.CoreSimulator\.SimRuntime\.iOS-\d+-\d+', line)
                    if ios_runtime_match:
                        ios_runtime = ios_runtime_match.group(0)
            
            if not ios_runtime:
                print("⚠️ 利用可能なiOSランタイムが見つかりません。")
                return None
            
            # 新しいシミュレータを作成
            create_result = subprocess.run(
                f"xcrun simctl create 'FlutterTestDevice' com.apple.CoreSimulator.SimDeviceType.iPhone-13 {ios_runtime}",
                shell=True, text=True, capture_output=True)
            
            if create_result.returncode == 0:
                simulator_id = create_result.stdout.strip()
                print(f"新しいシミュレータを作成しました: {simulator_id}")
            else:
                print("⚠️ シミュレータの作成に失敗しました。")
                return None
        return simulator_id
    
    except Exception as e:
        print(f"シミュレータ取得エラー: {e}")
        return None

def get_connected_ios_devices():
    """接続されているiOSデバイスの一覧を取得"""
    if platform.system() != "Darwin":
        return []
    
    try:
        result = subprocess.run("xcrun xctrace list devices", 
                               shell=True, text=True, capture_output=True)
        
        if result.returncode != 0:
            return []
        
        devices = []
        for line in result.stdout.splitlines():
            if ("iPhone" in line or "iPad" in line) and "Simulator" not in line:
                # デバイスIDを抽出
                device_id_match = re.search(r'\(([\w-]+)\)$', line)
                if device_id_match:
                    device_id = device_id_match.group(1)
                    device_name = line.split(" (")[0]
                    devices.append({"id": device_id, "name": device_name, "full_info": line})
        
        return devices
    except Exception as e:
        print(f"デバイス一覧取得エラー: {e}")
        return []
