#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import platform
import re
import time
from utils import run_command

def get_available_emulators():
    """利用可能なAndroidエミュレータの一覧を取得する"""
    print("\n🔍 利用可能なAndroidエミュレータを検索しています...")
    
    # 最初に環境変数のパスが正しく設定されているか確認
    from env_check import setup_android_paths
    setup_android_paths()
    
    # 実行中のエミュレータを先に検出
    running_emulators = []
    success, adb_output = run_command("adb devices", show_output=False)
    if success and adb_output:
        adb_output = adb_output.decode('utf-8') if isinstance(adb_output, bytes) else adb_output
        for line in adb_output.strip().split('\n')[1:]:  # ヘッダー行をスキップ
            if "emulator-" in line and "device" in line:
                # エミュレータが起動している
                emulator_id = line.split()[0]
                # エミュレータIDからポート番号を抽出 (例: emulator-5554 -> 5554)
                port = emulator_id.split('-')[1]
                running_emulators.append(port)
    
    # 利用可能なエミュレータリストを取得
    success, output = run_command("emulator -list-avds", show_output=False)
    if not success or not output:
        print("⚠️ エミュレータの一覧取得に失敗しました。Android SDK Emulatorがインストールされているか確認してください。")
        # SDKマネージャーでエミュレータをインストールするためのヘルプメッセージ
        print("ヒント: エミュレータをインストールするには、Android Studio > SDK Manager > SDK Toolsタブ > Android Emulator にチェックを入れてください")
        return []
    
    emulators = []
    if isinstance(output, bytes):
        output = output.decode('utf-8')
    
    # エミュレータ名のリストを取得
    avd_names = output.strip().split('\n')
    
    # 各エミュレータの詳細情報を取得
    for i, name in enumerate(avd_names):
        if name:  # 空行をスキップ
            # エミュレータ詳細情報を取得
            avd_info = {}
            avd_info['name'] = name
            avd_info['id'] = name  # Androidではエミュレータ名がIDとなる
            
            # デフォルトは停止中
            avd_info['state'] = "停止中"
            
            # 実行中のエミュレータリストと照合（より正確な検出）
            if running_emulators:
                # AVDプロセスと起動済みエミュレータのマッピングを取得
                try:
                    # エミュレータが起動しているか確認（様々な方法で）
                    success, emu_ps = run_command(f"ps aux | grep 'qemu.*{name}' | grep -v grep", show_output=False)
                    if success and emu_ps and len(emu_ps) > 0:
                        avd_info['state'] = "実行中"
                except:
                    pass
            
            # エミュレータのAPIレベルやバージョンを取得（可能であれば）
            try:
                # AVD設定ファイルのパスを特定
                avd_ini_paths = [
                    os.path.expanduser(f"~/.android/avd/{name}.avd/config.ini"),  # Linux/macOS
                    os.path.join(os.environ.get('USERPROFILE', ''), '.android', 'avd', f"{name}.avd", "config.ini")  # Windows
                ]
                
                avd_ini_path = None
                for path in avd_ini_paths:
                    if os.path.exists(path):
                        avd_ini_path = path
                        break
                
                if avd_ini_path:
                    with open(avd_ini_path, 'r') as f:
                        avd_config = f.read()
                    
                    # API レベルの抽出
                    target_match = re.search(r'target=([^\r\n]+)', avd_config)
                    if target_match:
                        target = target_match.group(1)
                        api_level_match = re.search(r'android-(\d+)', target)
                        if api_level_match:
                            avd_info['api_level'] = api_level_match.group(1)
                            # APIレベルからAndroidバージョンを推定
                            api_to_version = {
                                '33': '13.0', '32': '12.1', '31': '12.0', 
                                '30': '11.0', '29': '10.0', '28': '9.0',
                                '27': '8.1', '26': '8.0', '25': '7.1',
                                '24': '7.0', '23': '6.0', '22': '5.1'
                            }
                            avd_info['android_version'] = api_to_version.get(avd_info['api_level'], f"API {avd_info['api_level']}")
                    
                    # ABI情報の抽出
                    abi_match = re.search(r'abi\.type=([^\r\n]+)', avd_config)
                    if abi_match:
                        avd_info['abi'] = abi_match.group(1)
                    else:
                        # 代替方法：system-imagesディレクトリを探す
                        system_img_match = re.search(r'image\.sysdir\.1=([^\r\n]+)', avd_config)
                        if system_img_match:
                            system_img_path = system_img_match.group(1)
                            if 'x86' in system_img_path:
                                avd_info['abi'] = 'x86'
                            elif 'x86_64' in system_img_path:
                                avd_info['abi'] = 'x86_64'
                            elif 'arm64-v8a' in system_img_path:
                                avd_info['abi'] = 'arm64-v8a'
                            elif 'armeabi-v7a' in system_img_path:
                                avd_info['abi'] = 'armeabi-v7a'
                
                # デフォルト値を設定（情報が取得できなかった場合）
                if 'api_level' not in avd_info:
                    # 名前から推測
                    name_api_match = re.search(r'API_(\d+)', name)
                    if name_api_match:
                        avd_info['api_level'] = name_api_match.group(1)
                        api_to_version = {
                            '33': '13.0', '32': '12.1', '31': '12.0', 
                            '30': '11.0', '29': '10.0', '28': '9.0',
                            '27': '8.1', '26': '8.0', '25': '7.1',
                            '24': '7.0', '23': '6.0', '22': '5.1'
                        }
                        avd_info['android_version'] = api_to_version.get(avd_info['api_level'], f"API {avd_info['api_level']}")
                    else:
                        avd_info['api_level'] = "不明"
                        avd_info['android_version'] = "不明"
                
                if 'abi' not in avd_info:
                    # 名前から推測
                    if 'x86_64' in name:
                        avd_info['abi'] = 'x86_64'
                    elif 'x86' in name:
                        avd_info['abi'] = 'x86'
                    elif 'arm64' in name:
                        avd_info['abi'] = 'arm64-v8a'
                    else:
                        avd_info['abi'] = "不明"
            
            except Exception as e:
                print(f"  ⚠️ エミュレータ情報取得エラー ({name}): {e}")
                avd_info['api_level'] = "不明"
                avd_info['android_version'] = "不明"
                avd_info['abi'] = "不明"
            
            emulators.append(avd_info)
    
    print(f"🔍 検出したエミュレータ: {len(emulators)}台 (実行中: {len([e for e in emulators if e['state'] == '実行中'])}台)")
    return emulators

def print_emulator_list(emulators):
    """エミュレータの一覧を表示する"""
    if not emulators:
        print("利用可能なAndroidエミュレータがありません。")
        return
    
    print("\n===== 利用可能なAndroidエミュレータ =====")
    print(f"{'番号':^4} | {'名前':<25} | {'Android バージョン':<15} | {'API':<5} | {'ABI':<10} | {'状態':<10}")
    print("-" * 85)
    
    for i, emu in enumerate(emulators):
        android_ver = emu.get('android_version', '不明')
        api_level = emu.get('api_level', '??')
        abi = emu.get('abi', '不明')
        state = emu.get('state', '不明')
        print(f"{i+1:^4} | {emu['name']:<25} | {android_ver:<15} | {api_level:<5} | {abi:<10} | {state:<10}")

def boot_emulator(emulator_name, wait_time=60):
    """エミュレータを起動する"""
    print(f"\n🚀 エミュレータ「{emulator_name}」を起動しています...")
    
    # より正確に実行中のエミュレータを検出
    success, adb_output = run_command("adb devices", show_output=False)
    success2, ps_output = run_command(f"ps aux | grep '{emulator_name}' | grep -v grep", show_output=False)
    
    is_running = False
    if success and adb_output:
        adb_text = adb_output.decode('utf-8') if isinstance(adb_output, bytes) else adb_output
        if "emulator-" in adb_text and "device" in adb_text:
            is_running = True
    
    if success2 and ps_output and len(ps_output) > 0:
        is_running = True
    
    if is_running:
        print("✅ エミュレータは既に起動しています。そのまま使用します。")
        return True
    
    # バックグラウンドでエミュレータを起動
    if platform.system() == "Windows":
        start_cmd = f"start /B emulator -avd {emulator_name}"
    else:
        start_cmd = f"nohup emulator -avd {emulator_name} > /dev/null 2>&1 &"
    
    success, _ = run_command(start_cmd, "エミュレータ起動")
    if not success:
        print("⚠️ エミュレータの起動に失敗しました")
        return False
    
    # エミュレータの起動を待機
    print("⏳ エミュレータの起動を待機しています...")
    start_time = time.time()
    while time.time() - start_time < wait_time:
        success, output = run_command("adb devices", show_output=False)
        if success and output:
            devices_output = output.decode('utf-8') if isinstance(output, bytes) else output
            if "device" in devices_output and "emulator" in devices_output:
                # bootアニメーションが終了したか確認
                success, boot_output = run_command(
                    "adb shell getprop sys.boot_completed", show_output=False
                )
                if success and boot_output:
                    boot_status = boot_output.decode('utf-8').strip() if isinstance(boot_output, bytes) else boot_output.strip()
                    if boot_status == "1":
                        print(f"✅ エミュレータの起動が完了しました ({int(time.time() - start_time)}秒)")
                        # 追加の待機時間（UIの読み込み待ち）
                        time.sleep(2)
                        return True
        
        # 5秒ごとに状態を表示
        if int(time.time() - start_time) % 5 == 0:
            print(f"  起動中... {int(time.time() - start_time)}秒経過")
        
        time.sleep(1)
    
    print("⚠️ エミュレータの起動がタイムアウトしました。それでも続行します。")
    return True  # タイムアウトしても一応続行する

def select_emulator(args, emulators):
    """コマンドライン引数またはユーザー入力によりエミュレータを選択する"""
    if not emulators:
        print("利用可能なAndroidエミュレータがありません。")
        return None
    
    selected_emulator = None
    
    if args.emulator:
        # 名前が指定された場合
        for emu in emulators:
            if emu['name'] == args.emulator:
                selected_emulator = emu
                break
                
        # 番号が指定された場合
        if not selected_emulator:
            try:
                idx = int(args.emulator) - 1  # 1ベースのインデックスを0ベースに変換
                if 0 <= idx < len(emulators):
                    selected_emulator = emulators[idx]
                else:
                    print(f"⚠️ 指定されたインデックス '{args.emulator}' は範囲外です。")
                    return None
            except ValueError:
                print(f"⚠️ '{args.emulator}' は有効なエミュレータ名またはインデックスではありません。")
                return None
    else:
        # エミュレータが指定されていない場合はユーザーに選択させる
        while True:
            try:
                choice = input("\nエミュレータの番号を選択してください (Ctrl+Cで終了): ")
                idx = int(choice) - 1
                if 0 <= idx < len(emulators):
                    selected_emulator = emulators[idx]
                    break
                else:
                    print("⚠️ 有効な番号を入力してください。")
            except ValueError:
                print("⚠️ 数字を入力してください。")
            except KeyboardInterrupt:
                print("\n\n⚠️ ユーザーにより操作が中断されました。")
                return None
    
    return selected_emulator
