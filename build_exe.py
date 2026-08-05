import os
import subprocess
import sys

def build_standalone_exe():
    app_dir = os.path.dirname(os.path.abspath(__file__))
    main_py = os.path.join(app_dir, "main.py")
    dist_dir = os.path.join(app_dir, "dist")

    # Kill running process to avoid PermissionError during build
    try:
        subprocess.run(["taskkill", "/F", "/IM", "LoginManager.exe"], capture_output=True)
        subprocess.run(["taskkill", "/F", "/IM", "PasswordManager.exe"], capture_output=True)
    except Exception:
        pass

    print(f"Building Standalone LoginManager.exe from: {main_py}")

    cmd = [
        sys.executable,
        "-m", "PyInstaller",
        "--noconfirm",
        "--onedir",
        "--windowed",
        "--name=LoginManager",
        f"--distpath={dist_dir}",
        "--hidden-import=PySide6",
        "--hidden-import=cryptography",
        "--hidden-import=requests",
        "--hidden-import=winrt.windows.foundation",
        "--hidden-import=winrt.windows.media.ocr",
        "--hidden-import=winrt.windows.security.credentials.ui",
        main_py
    ]

    try:
        res = subprocess.run(cmd, cwd=app_dir, capture_output=True, text=True)
        if res.returncode == 0:
            exe_path = os.path.join(dist_dir, "LoginManager", "LoginManager.exe")
            print(f"\n[BUILD SUCCESS] LoginManager.exe successfully created at:\n{exe_path}\n")
            print("This folder can be zipped and distributed to any Windows PC for installation!")
            return exe_path
        else:
            print(f"[BUILD ERROR] PyInstaller failed:\n{res.stderr}")
    except Exception as e:
        print(f"Build exception: {e}")
    return None

if __name__ == "__main__":
    build_standalone_exe()
