#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import subprocess
import platform
import datetime
import shutil
import argparse
import time
import signal
import threading
import sys
from pathlib import Path
import re

def run_command(command, description=None, timeout=None, show_progress=False):
    """コマンドを実行し、結果を返す"""
    if description:
        print(f"\n===== {description} =====")
    
    print(f"実行: {command}")
    
    # プログレス表示用スレッド
    stop_progress = False
    
    def show_progress_indicator():
        symbols = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
        i = 0
        start_time = time.time()
        while not stop_progress:
            elapsed = int(time.time() - start_time)
            minutes, seconds = divmod(elapsed, 60)
            print(f"\r{symbols[i % len(symbols)]} 処理中... ({minutes:02d}:{seconds:02d})", end='', flush=True)
            i += 1
            time.sleep(0.1)
    
    # プログレス表示を開始
    progress_thread = None
    if show_progress:
        progress_thread = threading.Thread(target=show_progress_indicator)
        progress_thread.daemon = True
        progress_thread.start()
    
    try:
        # プロセス開始
        process = subprocess.Popen(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        # 標準出力と標準エラー出力を読み込む
        stdout_data = []
        stderr_data = []
        
        def read_output(pipe, data_list):
            for line in iter(pipe.readline, ''):
                data_list.append(line)
                if not show_progress:  # プログレス表示中は出力しない
                    print(line, end='')
        
        # 出力読み込みスレッド
        stdout_thread = threading.Thread(target=read_output, args=(process.stdout, stdout_data))
        stderr_thread = threading.Thread(target=read_output, args=(process.stderr, stderr_data))
        stdout_thread.daemon = True
        stderr_thread.daemon = True
        stdout_thread.start()
        stderr_thread.start()
        
        # 指定時間待機
        exit_code = None
        start_time = time.time()
        while True:
            exit_code = process.poll()
            if exit_code is not None:
                break
                
            # タイムアウトチェック
            if timeout and time.time() - start_time > timeout:
                print(f"\n\n⚠️ コマンドが{timeout}秒以上応答していないため強制終了します")
                # Unix/Linux/Macの場合はSIGTERMを送信
                if os.name != 'nt':
                    process.send_signal(signal.SIGTERM)
                    time.sleep(2)  # 正常終了の猶予
                    if process.poll() is None:  # まだ終了していない
                        process.send_signal(signal.SIGKILL)
                else:  # Windowsの場合
                    process.terminate()
                    time.sleep(2)
                    if process.poll() is None:
                        process.kill()
                
                # プログレス表示を停止
                if show_progress:
                    stop_progress = True
                    progress_thread.join(1)
                    print("\r                                        ", end='\r')  # プログレス行をクリア
                
                return False, "タイムアウトにより中断されました"
            
            time.sleep(0.1)
        
        # スレッドの終了を待つ
        stdout_thread.join()
        stderr_thread.join()
        
        # 出力結果を結合
        stdout_output = ''.join(stdout_data)
        stderr_output = ''.join(stderr_data)
        
        # プログレス表示を停止
        if show_progress:
            stop_progress = True
            progress_thread.join(1)
            print("\r                                        ", end='\r')  # プログレス行をクリア
        
        if exit_code == 0:
            if stdout_output:
                print(stdout_output)
            return True, stdout_output
        else:
            print(f"エラー発生 (コード: {exit_code}):")
            if stderr_output:
                print(f"エラー詳細: {stderr_output}")
            return False, stderr_output
            
    except KeyboardInterrupt:
        print("\n\n⚠️ ユーザーによって中断されました")
        if 'process' in locals() and process.poll() is None:
            process.terminate()
        if show_progress:
            stop_progress = True
            progress_thread.join(1)
            print("\r                                        ", end='\r')
        return False, "ユーザーによって中断されました"
    except Exception as e:
        if show_progress:
            stop_progress = True
            progress_thread.join(1)
            print("\r                                        ", end='\r')
        print(f"予期せぬエラーが発生しました: {e}")
        return False, str(e)

def check_flutter_installation():
    """Flutterがインストールされているか確認する"""
    result = subprocess.run("flutter --version", shell=True, text=True, capture_output=True)
    if result.returncode != 0:
        print("Flutterがインストールされていないか、PATHに設定されていません。")
        print("https://flutter.dev/docs/get-started/install からFlutterをインストールしてください。")
        return False
    print("Flutter確認済み:")
    print(result.stdout.split('\n')[0])
    return True

def check_android_ndk():
    """AndroidのNDKがインストールされているか確認し、必要に応じてインストールする"""
    print("\n環境チェック: Android NDK")
    
    # Android SDK のパスを確認
    home = os.path.expanduser("~")
    sdk_locations = [
        os.path.join(home, "Library/Android/sdk"),  # macOS
        os.path.join(home, "Android/Sdk"),          # Linux
        os.path.join(home, "AppData/Local/Android/Sdk")  # Windows
    ]
    
    android_sdk_path = None
    for location in sdk_locations:
        if os.path.exists(location):
            android_sdk_path = location
            break
    
    if not android_sdk_path:
        print("⚠️ Android SDKが見つかりません。Android Studioをインストールしていることを確認してください。")
        return False
    
    # NDKディレクトリの確認
    ndk_path = os.path.join(android_sdk_path, "ndk")
    if not os.path.exists(ndk_path):
        print(f"NDKディレクトリが見つかりません: {ndk_path}")
        if input("Android SDKマネージャーでNDKをインストールしますか？ (y/n): ").lower() == 'y':
            # SDKマネージャーを使用してNDKをインストール
            cmd = f"sdkmanager --install \"ndk;21.4.7075529\""
            print(f"実行: {cmd}")
            print("これには数分かかることがあります...")
            
            if platform.system() == "Windows":
                # Windowsの場合はsdkmanager.batを使用
                cmd = os.path.join(android_sdk_path, "tools", "bin", "sdkmanager.bat") + " \"ndk;21.4.7075529\""
            else:
                # Linux/macOSの場合
                cmd = os.path.join(android_sdk_path, "tools", "bin", "sdkmanager") + " \"ndk;21.4.7075529\""
            
            try:
                subprocess.run(cmd, shell=True, check=True)
                print("✅ NDKが正常にインストールされました。")
            except subprocess.CalledProcessError:
                print("⚠️ NDKのインストールに失敗しました。")
                print("Android Studioを開き、SDK Managerから手動でNDKをインストールしてください。")
                print("Settings > Appearance & Behavior > System Settings > Android SDK > SDK Tools")
                return False
        else:
            print("\nNDKを手動でインストールするには:")
            print("1. Android Studioを開く")
            print("2. Settings > Appearance & Behavior > System Settings > Android SDK > SDK Tools")
            print("3. 'NDK (Side by side)' を選択してインストール")
            print("4. 'CMake' も選択することをお勧めします")
            return False
    
    # フラッターがNDKを認識するようにlocal.properties を更新
    local_props_path = "android/local.properties"
    
    # ディレクトリ内の最新のNDKバージョンを探す
    ndk_versions = []
    if os.path.exists(ndk_path):
        for item in os.listdir(ndk_path):
            full_path = os.path.join(ndk_path, item)
            if os.path.isdir(full_path) and os.path.exists(os.path.join(full_path, "source.properties")):
                ndk_versions.append(item)
    
    if not ndk_versions:
        print("⚠️ 有効なNDKバージョンが見つかりませんでした。")
        print("Android Studioを開き、SDK Managerから手動でNDKをインストールしてください。")
        return False
    
    # 最新のNDKバージョンを使用（単純な文字列比較）
    latest_ndk = max(ndk_versions)
    ndk_full_path = os.path.join(ndk_path, latest_ndk).replace("\\", "\\\\")
    
    # local.propertiesファイルを更新
    has_ndk_prop = False
    new_lines = []
    
    if os.path.exists(local_props_path):
        with open(local_props_path, 'r') as f:
            for line in f:
                if line.startswith('ndk.dir='):
                    new_lines.append(f'ndk.dir={ndk_full_path}\n')
                    has_ndk_prop = True
                else:
                    new_lines.append(line)
    
    if not has_ndk_prop:
        new_lines.append(f'\nndk.dir={ndk_full_path}\n')
    
    with open(local_props_path, 'w') as f:
        f.writelines(new_lines)
    
    print(f"✅ NDKの設定を更新しました: {ndk_full_path}")
    return True

def build_android_apk(release_mode=True, verbose=False, skip_clean=False, fast_build=False):
    """Android APKをビルドする"""
    # NDKチェックを追加
    if not check_android_ndk():
        print("⚠️ Android NDKの設定が不完全です。ビルドをスキップします。")
        return False
        
    build_mode = "--release" if release_mode else "--debug"
    output_dir = "build/app/outputs/flutter-apk"
    
    # 開始時間を記録
    start_time = time.time()
    
    # クリーンビルドは時間がかかるのでスキップオプション
    if not skip_clean:
        clean_success, _ = run_command("flutter clean", "Flutterプロジェクトをクリーン", show_progress=True)
        if not clean_success:
            print("警告: クリーンに失敗しましたが、ビルドを続行します")
    else:
        print("クリーンステップをスキップします")
    
    # 依存関係の取得
    print("依存関係を取得中...")
    pub_success, _ = run_command("flutter pub get", "Flutter依存関係の解決", timeout=120, show_progress=True)
    if not pub_success:
        print("⚠️ 依存関係の解決に失敗しました。ネットワーク接続を確認してください。")
        return False
    
    # 高速ビルドのための追加オプション
    build_flags = []
    if fast_build and release_mode:
        # R8/ProGuardを無効化すると高速になるが、アプリサイズが大きくなる
        build_flags.append("--no-shrink")
        print("注: 高速ビルドモードが有効です (R8/ProGuard無効)")
    
    # ビルド前の追加フラグ
    extra_flags = "--verbose" if verbose else ""
    extra_flags += " " + " ".join(build_flags)
    
    # Flutterビルドを実行
    build_command = f"flutter build apk {build_mode} --split-per-abi {extra_flags}"
    print("\n⏱️ Androidのビルドには、特に初回実行時は5〜10分程度かかる場合があります。")
    print("   （次回以降のビルドでは '--no-clean --fast-build' オプションを使用すると高速化できます）\n")
    
    build_success, _ = run_command(build_command, "Android APKビルド", timeout=1200, show_progress=True)
    if not build_success:
        print("\n⚠️ APKビルドに失敗しました。詳細なエラーログを確認してください。")
        print("問題解決のためのヒント:")
        print("1. 'flutter doctor' を実行して環境の問題をチェック")
        print("2. Android SDK、JDK、Gradleのバージョン互換性を確認")
        print("3. '--verbose'フラグを付けて再実行するとより詳細な情報を表示できます")
        return False
    
    # ビルド結果の確認
    apk_path = os.path.join(output_dir, "app-armeabi-v7a-release.apk" if release_mode else "app-debug.apk")
    if not os.path.exists(apk_path):
        # Split APKが見つからない場合は通常のAPKを確認
        apk_path = os.path.join(output_dir, "app-release.apk" if release_mode else "app-debug.apk")
        if not os.path.exists(apk_path):
            print(f"APKファイルが見つかりません: {apk_path}")
            return False
    
    # 出力ディレクトリの作成
    output_folder = "output/android"
    os.makedirs(output_folder, exist_ok=True)
    
    # タイムスタンプ付きのファイル名
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = f"gyroscope_app_{timestamp}.apk"
    output_path = os.path.join(output_folder, output_filename)
    
    # ビルド時間の計算
    build_duration = time.time() - start_time
    minutes, seconds = divmod(int(build_duration), 60)
    
    # ファイルのコピー
    shutil.copy2(apk_path, output_path)
    print(f"\n✅ APKが正常にビルドされました: {output_path}")
    print(f"ファイルサイズ: {os.path.getsize(output_path) / (1024 * 1024):.2f} MB")
    print(f"ビルド時間: {minutes}分{seconds}秒")
    
    return True

def get_flutter_version():
    """Flutterのバージョンを取得する"""
    try:
        result = subprocess.run("flutter --version", shell=True, text=True, capture_output=True)
        if result.returncode == 0:
            return result.stdout.splitlines()[0]
    except Exception:
        pass
    return "Unknown"

def main():
    """メイン実行関数"""
    parser = argparse.ArgumentParser(description="Flutter アプリケーションのAndroid APKをビルド")
    parser.add_argument('--debug', action='store_true', help='デバッグモードでビルド')
    parser.add_argument('--verbose', action='store_true', help='詳細な出力を表示')
    parser.add_argument('--no-clean', action='store_true', help='クリーンステップをスキップして高速化')
    parser.add_argument('--fast-build', action='store_true', help='高速ビルド (サイズ最適化を無効化)')
    args = parser.parse_args()
    
    print("=== ジャイロスコープアプリ Android ビルドスクリプト ===")
    
    # Flutter Doctorの実行を提案
    if input("Flutter doctor を実行して環境を確認しますか？ (y/n): ").lower() == 'y':
        run_command("flutter doctor -v", "Flutter環境診断", timeout=60, show_progress=True)
    
    # 現在のディレクトリを表示
    print(f"現在のディレクトリ: {os.getcwd()}")
    
    # スクリプトの作業ディレクトリを修正
    script_dir = os.path.dirname(os.path.abspath(__file__))
    if os.getcwd() != script_dir:
        print(f"作業ディレクトリを変更: {script_dir}")
        os.chdir(script_dir)
    
    # Flutterの確認
    if not check_flutter_installation():
        return 1
    
    # プロジェクトディレクトリの確認
    if not os.path.exists('lib/main.dart'):
        print("エラー: このディレクトリはFlutterプロジェクトではないようです。")
        print("Flutterプロジェクトのルートディレクトリで実行してください。")
        return 1
    
    # 出力フォルダの準備
    os.makedirs("output/android", exist_ok=True)
    
    # ビルドの実行
    success = True
    
    try:
        if not build_android_apk(not args.debug, args.verbose, args.no_clean, args.fast_build):
            success = False
            print("⚠️ Android APKのビルドに失敗しました")
        
        if success:
            print("\n✨ Androidビルドが正常に完了しました! ✨")
        else:
            print("\n⚠️ ビルドで問題が発生しました。上記のエラーを確認してください。")
            return 1
    
    except KeyboardInterrupt:
        print("\n\n⚠️ ビルドがユーザーによって中断されました。")
        return 1
    
    # 問題があったとき、エラーメッセージをログファイルに保存
    if not success:
        log_filename = f"android_build_error_log_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        try:
            with open(log_filename, 'w') as f:
                f.write("=== Androidビルドエラーログ ===\n")
                f.write(f"日時: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Flutterバージョン: {get_flutter_version()}\n")
                f.write("エラーメッセージ:\n")
        except Exception as e:
            print(f"エラーログの保存に失敗しました: {e}")
    
    return 0 if success else 1

if __name__ == "__main__":
    try:
        exit(main())
    except KeyboardInterrupt:
        print("\n\nビルドプロセスが中断されました。")
        exit(1)
    except Exception as e:
        print(f"\n予期せぬエラーが発生しました: {e}")
        exit(1)