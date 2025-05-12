import os
import shutil
import subprocess

def deep_clean():
    """徹底的なクリーンアップ処理を実行する"""
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    
    # ビルドディレクトリの完全削除
    build_dir = os.path.join(project_root, "build")
    ios_build_dir = os.path.join(project_root, "ios", "build")
    
    for dir_path in [build_dir, ios_build_dir]:
        if os.path.exists(dir_path):
            print(f"🧹 削除中: {dir_path}")
            shutil.rmtree(dir_path, ignore_errors=True)
    
    # Xcodeのキャッシュクリア
    derived_data = os.path.expanduser("~/Library/Developer/Xcode/DerivedData")
    runner_derived = None
    
    if os.path.exists(derived_data):
        for item in os.listdir(derived_data):
            if "Runner" in item:
                runner_derived = os.path.join(derived_data, item)
                if os.path.exists(runner_derived):
                    print(f"🧹 Xcodeキャッシュ削除中: {runner_derived}")
                    shutil.rmtree(runner_derived, ignore_errors=True)
    
    # Flutterクリーンの実行
    print("🧹 Flutter cleanを実行中...")
    subprocess.run(["flutter", "clean"], cwd=project_root)
    
    print("✅ 徹底的なクリーンアップが完了しました")

if __name__ == "__main__":
    deep_clean()
