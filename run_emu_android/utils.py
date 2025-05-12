#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import subprocess
import re
import platform
import time
import datetime
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

def get_flutter_version():
    """Flutterのバージョン情報を取得する"""
    try:
        result = subprocess.run("flutter --version", shell=True, check=True, text=True, capture_output=True)
        version_line = result.stdout.strip().split('\n')[0]
        return version_line
    except:
        return "不明"

def prepare_output_directory():
    """出力ディレクトリを準備する"""
    os.makedirs("output/android_emulator", exist_ok=True)
    return True
