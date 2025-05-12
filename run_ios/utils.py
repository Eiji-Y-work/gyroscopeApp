#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import subprocess
import time
import signal
import threading
import platform

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
    if (result.returncode != 0):
        print("Flutterがインストールされていないか、PATHに設定されていません。")
        print("https://flutter.dev/docs/get-started/install からFlutterをインストールしてください。")
        return False
    print("Flutter確認済み:")
    print(result.stdout.split('\n')[0])
    return True

def check_cocoapods():
    """CocoaPodsがインストールされているか確認し、ない場合はインストール方法を表示する"""
    print("\n環境チェック: CocoaPods")
    
    if platform.system() != "Darwin":  # macOSの場合のみ確認
        return True
        
    try:
        result = subprocess.run("pod --version", shell=True, text=True, capture_output=True)
        if result.returncode == 0:
            print(f"✅ CocoaPodsがインストールされています (バージョン: {result.stdout.strip()})")
            return True
    except Exception:
        pass
    
    print("❌ CocoaPodsがインストールされていません。")
    print("\nCocoaPodsをインストールするには以下のコマンドを実行します:")
    
    print("\nCocoaPodsをインストール中...")
    try:
        # gemでCocoaPodsをインストール
        subprocess.run("sudo gem install cocoapods", shell=True, check=True)
        print("✅ CocoaPodsが正常にインストールされました。")
        return True
    except subprocess.CalledProcessError:
        print("⚠️ CocoaPodsのインストールに失敗しました。")
    
    print("\nCocoaPodsを手動でインストールするには次のコマンドを実行してください:")
    print("sudo gem install cocoapods")
    print("または")
    print("brew install cocoapods")
    return False

def get_flutter_version():
    """Flutterのバージョンを取得する"""
    try:
        result = subprocess.run("flutter --version", shell=True, text=True, capture_output=True)
        if result.returncode == 0:
            return result.stdout.splitlines()[0]
    except Exception:
        pass
    return "Unknown"
