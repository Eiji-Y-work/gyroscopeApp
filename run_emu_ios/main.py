#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import argparse
import platform
import datetime
import sys
import subprocess
import time
import shutil
import json
import re

def run_command(cmd, description="", timeout=None, show_output=True, show_progress=False):
    """コマンドを実行し、結果を表示する"""
    if description:
        print(f"\n===== {description} =====")
        print(f"実行: {cmd}")
    
    try:
        if show_output:
            if show_progress:
                process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
                for line in iter(process.stdout.readline, ''):
                    if line:  # 空行をスキップ
                        print(line.rstrip())
                process.stdout.close()
                return_code = process.wait(timeout=timeout)
            else:
                result = subprocess.run(cmd, shell=True, check=False, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=timeout)
                if result.stdout:
                    print(result.stdout)
                return_code = result.returncode
        else:
            result = subprocess.run(cmd, shell=True, check=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=timeout)
            return_code = result.returncode
            stdout = result.stdout
        
        if return_code != 0 and show_output:
            print(f"エラー発生 (コード: {return_code})")
            if not show_progress:
                print(f"エラー詳細: {result.stdout}")
            return False, None
        
        return True, stdout if not show_output else None
    except subprocess.TimeoutExpired:
        print(f"タイムアウト: {cmd}")
        return False, None
    except Exception as e:
        print(f"例外発生: {e}")
        return False, None

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

def get_flutter_version():
    """Flutterのバージョン情報を取得する"""
    try:
        result = subprocess.run("flutter --version", shell=True, check=True, text=True, capture_output=True)
        version_line = result.stdout.strip().split('\n')[0]
        return version_line
    except:
        return "不明"

def check_xcode_installation():
    """Xcodeのインストールを確認する"""
    if platform.system() != "Darwin":  # macOSでない場合
        print("⚠️ iOSシミュレータはmacOSでのみ使用できます。")
        return False
    
    # xcodeの存在確認
    xcode_path = shutil.which("xcodebuild")
    if not xcode_path:
        print("⚠️ Xcodeが見つかりません。App StoreからXcodeをインストールしてください。")
        return False
    
    # xcodeのバージョン確認
    success, output = run_command("xcodebuild -version", "Xcodeのバージョン確認", show_output=False)
    if not success:
        print("⚠️ Xcodeのバージョン取得に失敗しました。")
        return False
    
    # バックスラッシュエラーを修正
    if isinstance(output, bytes):
        output_text = output.decode('utf-8').splitlines()[0]
    else:
        output_text = output.splitlines()[0]
    print(f"✅ Xcode確認済み: {output_text}")
    
    return True

def get_available_simulators():
    """利用可能なiOSシミュレータの一覧を取得する"""
    print("\n🔍 利用可能なiOSシミュレータを検索しています...")
    
    # すべてのデバイスを取得 (フィルタオプションなし)
    success, output = run_command("xcrun simctl list devices --json", show_output=False)
    if not success or not output:
        print("⚠️ シミュレータの一覧取得に失敗しました。")
        return []
    
    try:
        if isinstance(output, bytes):
            output = output.decode('utf-8')
        
        print(f"📊 取得したデバイス情報のサイズ: {len(output)} バイト")
        
        # JSONを解析
        devices_info = json.loads(output)
        
        # JSONの構造を詳細に出力（デバッグ用）
        print("🔍 シミュレータJSONの構造を調査中...")
        runtimes = list(devices_info.get('devices', {}).keys())
        print(f"🔧 検出したランタイム: {len(runtimes)}個")
        for i, runtime in enumerate(runtimes):
            devices_count = len(devices_info['devices'][runtime])
            print(f"  - {runtime}: {devices_count}台のデバイス")
        
        # 利用可能なデバイスを抽出
        available_devices = []
        for runtime, devices in devices_info.get('devices', {}).items():
            # より寛容なiOSランタイムの検出 (com.apple.CoreSimulator.SimRuntime.iOS- なども含める)
            is_ios = 'iOS' in runtime or '.iOS-' in runtime
            
            if not is_ios:
                continue
                
            ios_version_match = re.search(r'iOS[- ](\d+\.\d+)', runtime)
            ios_version = ios_version_match.group(1) if ios_version_match else "不明"
            
            for device in devices:
                # デバイス情報をデバッグ出力
                device_name = device.get('name', '名前なし')
                device_state = device.get('state', '不明')
                device_available = device.get('isAvailable', False)
                
                print(f"  デバイス: {device_name} - 状態: {device_state} - 利用可能: {device_available}")
                
                # 条件を緩和 - どんな状態でも含める（削除済みのみ除外）
                if not device.get('isDeleted', False):
                    available_devices.append({
                        'udid': device.get('udid'),
                        'name': device.get('name', '名前不明'),
                        'state': device.get('state', '不明'),
                        'ios_version': ios_version,
                        'runtime': runtime
                    })
        
        print(f"🔍 検出したシミュレータ: {len(available_devices)}台")
        return available_devices
    except Exception as e:
        print(f"⚠️ シミュレータ情報の解析に失敗しました: {e}")
        import traceback
        print(traceback.format_exc())
        
        # エラーの詳細情報を表示
        if isinstance(output, str) and len(output) > 0:
            print(f"受信データのプレビュー: {output[:200]}...")
        return []

def print_simulator_list(simulators):
    """シミュレータの一覧を表示する"""
    if not simulators:
        print("利用可能なiOSシミュレータがありません。")
        return
    
    print("\n===== 利用可能なiOSシミュレータ =====")
    print(f"{'番号':^4} | {'名前':<25} | {'iOS バージョン':<12} | {'状態':<10} | {'UDID':<36}")
    print("-" * 95)
    
    for i, sim in enumerate(simulators):
        state = "実行中" if sim['state'] == "Booted" else "停止中"
        print(f"{i+1:^4} | {sim['name']:<25} | {sim['ios_version']:<12} | {state:<10} | {sim['udid']}")

def boot_simulator(simulator_udid):
    """シミュレータを起動する"""
    print(f"\n🚀 シミュレータ (UDID: {simulator_udid}) を起動しています...")
    
    # シミュレータが既に起動しているか確認
    success, output = run_command(f"xcrun simctl list devices | grep {simulator_udid}", show_output=False)
    if success and output and "Booted" in output.decode('utf-8') if isinstance(output, bytes) else output:
        print("✅ シミュレータは既に起動しています")
        return True
    
    # シミュレータを起動
    success, _ = run_command(f"xcrun simctl boot {simulator_udid}", "シミュレータ起動")
    if not success:
        print("⚠️ シミュレータの起動に失敗しました")
        return False
    
    # Simulator.appを開く（UIを表示）
    run_command("open -a Simulator", "シミュレータアプリを開く")
    
    # シミュレータが完全に起動するまで少し待つ
    print("⏳ シミュレータの起動を待機しています...")
    time.sleep(5)
    
    return True

def build_and_run_ios_simulator(simulator_udid, verbose=False, no_clean=False):
    """Flutterアプリをビルドしてiシミュレータで実行する"""
    print("\n🚀 FlutterアプリをiOSシミュレータ用にビルドして実行します")
    
    # まずシミュレータを起動
    if not boot_simulator(simulator_udid):
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
    
    # iOSシミュレータでFlutterアプリを実行
    print(f"📱 iOSシミュレータ ({simulator_udid}) でアプリを起動しています...")
    print("💡 終了するにはこのターミナルでCtrl+Cを押してください")
    
    # シミュレータIDを指定して実行（コンソール出力をリアルタイム表示）
    if not run_command(f"flutter run -d {simulator_udid}", "iOSシミュレータでアプリを実行", show_output=True, show_progress=True)[0]:
        return False
    
    return True

def main():
    """メイン実行関数"""
    # カレントディレクトリをプロジェクトのルートに変更（安全のため）
    os.chdir(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
    
    parser = argparse.ArgumentParser(description="Flutter アプリケーションのiOSシミュレータでの実行")
    parser.add_argument('--verbose', action='store_true', help='詳細な出力を表示')
    parser.add_argument('--no-clean', action='store_true', help='クリーンビルドをスキップ')
    parser.add_argument('--list', action='store_true', help='利用可能なシミュレータの一覧を表示するだけ')
    parser.add_argument('--simulator', type=str, help='使用するシミュレータのUDIDまたはインデックス番号')
    args = parser.parse_args()
    
    print("=== ジャイロスコープアプリ iOS シミュレータ 自動ビルド＆実行スクリプト ===")
    
    # macOSかどうか確認
    if platform.system() != "Darwin":
        print("⚠️ このスクリプトはmacOSでのみ実行できます。")
        return 1
    
    # Flutter環境のチェック
    if not check_flutter_installation():
        return 1
    
    # Xcode環境のチェック
    if not check_xcode_installation():
        return 1
    
    # プロジェクトディレクトリの確認
    if not os.path.exists('lib/main.dart'):
        print("エラー: このディレクトリはFlutterプロジェクトではないようです。")
        print("Flutterプロジェクトのルートディレクトリで実行してください。")
        return 1
    
    # 出力フォルダの準備
    os.makedirs("output/ios_simulator", exist_ok=True)
    
    # 利用可能なシミュレータの一覧を取得
    simulators = get_available_simulators()
    print_simulator_list(simulators)
    
    # 一覧表示のみの場合はここで終了
    if args.list or not simulators:
        return 0 if simulators else 1
    
    # シミュレータの選択
    selected_simulator = None
    
    if args.simulator:
        # UDIDが指定された場合
        if len(args.simulator) > 8:  # UDIDは通常長い文字列
            for sim in simulators:
                if sim['udid'] == args.simulator:
                    selected_simulator = sim
                    break
            if not selected_simulator:
                print(f"⚠️ 指定されたUDID '{args.simulator}' のシミュレータが見つかりません。")
                return 1
        else:
            # インデックスが指定された場合
            try:
                idx = int(args.simulator) - 1  # 1ベースのインデックスを0ベースに変換
                if 0 <= idx < len(simulators):
                    selected_simulator = simulators[idx]
                else:
                    print(f"⚠️ 指定されたインデックス '{args.simulator}' は範囲外です。")
                    return 1
            except ValueError:
                print(f"⚠️ '{args.simulator}' は有効なUDIDまたはインデックスではありません。")
                return 1
    else:
        # シミュレータが指定されていない場合はユーザーに選択させる
        while True:
            try:
                choice = input("\nシミュレータの番号を選択してください (Ctrl+Cで終了): ")
                idx = int(choice) - 1
                if 0 <= idx < len(simulators):
                    selected_simulator = simulators[idx]
                    break
                else:
                    print("⚠️ 有効な番号を入力してください。")
            except ValueError:
                print("⚠️ 数字を入力してください。")
            except KeyboardInterrupt:
                print("\n\n⚠️ ユーザーにより操作が中断されました。")
                return 1
    
    print(f"\n✅ 選択されたシミュレータ: {selected_simulator['name']} (iOS {selected_simulator['ios_version']})")
    
    # ビルドと実行
    try:
        if build_and_run_ios_simulator(selected_simulator['udid'], args.verbose, args.no_clean):
            print("\n✨ アプリの実行が終了しました")
            return 0
        else:
            print("\n⚠️ アプリの実行中に問題が発生しました")
            return 1
    except Exception as e:
        print(f"\n予期せぬエラーが発生しました: {e}")
        # エラーログを保存
        log_filename = f"ios_simulator_error_log_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        try:
            with open(log_filename, 'w') as f:
                f.write("=== iOSシミュレータ実行エラーログ ===\n")
                f.write(f"日時: {datetime.datetime.now().strftime('%Y-%m-%d %H%M%S')}\n")
                f.write(f"Flutterバージョン: {get_flutter_version()}\n")
                f.write(f"シミュレータ: {selected_simulator['name']} (iOS {selected_simulator['ios_version']})\n")
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
