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
        
        if return_code != 0 and show_output:
            print(f"エラー発生 (コード: {return_code})")
            if not show_progress:
                print(f"エラー詳細: {result.stdout}")
            return False
        
        return True
    except subprocess.TimeoutExpired:
        print(f"タイムアウト: {cmd}")
        return False
    except Exception as e:
        print(f"例外発生: {e}")
        return False

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

def check_chrome_installation():
    """Chromeブラウザのインストールを確認する"""
    if platform.system() == "Darwin":  # macOS
        chrome_path = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
        if os.path.exists(chrome_path):
            print("✅ Google Chromeが見つかりました")
            return True
    elif platform.system() == "Windows":
        chrome_paths = [
            os.path.join(os.environ.get('PROGRAMFILES', ''), 'Google/Chrome/Application/chrome.exe'),
            os.path.join(os.environ.get('PROGRAMFILES(X86)', ''), 'Google/Chrome/Application/chrome.exe')
        ]
        for path in chrome_paths:
            if os.path.exists(path):
                print(f"✅ Google Chromeが見つかりました: {path}")
                return True
    elif platform.system() == "Linux":
        if shutil.which("google-chrome") or shutil.which("chrome"):
            print("✅ Google Chromeが見つかりました")
            return True
    
    print("⚠️ Google Chromeが見つかりませんでした。インストールしてください。")
    return False

def build_and_run_chrome(verbose=False, no_clean=False):
    """ChromeでFlutterアプリをビルドして実行する"""
    print("\n🚀 FlutterアプリをChromeでビルド・実行します")
    
    # クリーンビルドが必要な場合
    if not no_clean:
        print("🧹 クリーンビルド実行中...")
        if not run_command("flutter clean", "クリーンビルド", show_output=verbose):
            return False
    
    # 依存関係の解決
    print("📦 依存パッケージを取得中...")
    if not run_command("flutter pub get", "依存関係の解決", show_output=verbose):
        return False
    
    # Webビルド前の設定
    print("⚙️ Webビルドの設定中...")
    if not run_command("flutter config --enable-web", "Webの有効化", show_output=verbose):
        return False
    
    # デバッグモードでChromeで実行
    print("🌐 ChromeでFlutterアプリを起動中...")
    print("💡 終了するにはこのターミナルでCtrl+Cを押してください")
    
    # 以下のコマンドはブロッキングであり、ユーザーがCtrl+Cを押すまで実行し続ける
    if not run_command("flutter run -d chrome --web-port 8080", "ChromeでFlutterアプリを実行", show_output=True, show_progress=True):
        return False
    
    return True

def main():
    """メイン実行関数"""
    # カレントディレクトリをプロジェクトのルートに変更（安全のため）
    os.chdir(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
    
    parser = argparse.ArgumentParser(description="Flutter アプリケーションのChromeでの実行")
    parser.add_argument('--verbose', action='store_true', help='詳細な出力を表示')
    parser.add_argument('--no-clean', action='store_true', help='クリーンビルドをスキップ')
    args = parser.parse_args()
    
    print("=== ジャイロスコープアプリ Chrome 自動ビルド＆実行スクリプト ===")
    
    # Flutter環境のチェック
    if not check_flutter_installation():
        return 1
    
    # Chromeブラウザのチェック
    if not check_chrome_installation():
        print("GoogleChromeをインストールしてから再実行してください。")
        return 1
    
    # プロジェクトディレクトリの確認
    if not os.path.exists('lib/main.dart'):
        print("エラー: このディレクトリはFlutterプロジェクトではないようです。")
        print("Flutterプロジェクトのルートディレクトリで実行してください。")
        return 1
    
    # 出力フォルダの準備
    os.makedirs("output/web", exist_ok=True)
    
    # ビルドと実行
    try:
        if build_and_run_chrome(args.verbose, args.no_clean):
            print("\n✨ アプリの実行が終了しました")
            return 0
        else:
            print("\n⚠️ アプリの実行中に問題が発生しました")
            return 1
    except Exception as e:
        print(f"\n予期せぬエラーが発生しました: {e}")
        # エラーログを保存
        log_filename = f"chrome_run_error_log_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        try:
            with open(log_filename, 'w') as f:
                f.write("=== Chrome実行エラーログ ===\n")
                f.write(f"日時: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
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
