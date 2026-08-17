import sys
import os
import winreg

APP_NAME = "LoginManager"

def get_executable_path() -> str:
    if getattr(sys, 'frozen', False):
        return sys.executable
    return os.path.abspath(sys.argv[0])

def get_startup_folder_path() -> str:
    appdata = os.getenv('APPDATA')
    if appdata:
        return os.path.join(appdata, r"Microsoft\Windows\Start Menu\Programs\Startup")
    return ""

def get_shortcut_path() -> str:
    startup_dir = get_startup_folder_path()
    if startup_dir:
        return os.path.join(startup_dir, "LoginManager.lnk")
    return ""

def is_autostart_enabled() -> bool:
    # 1. Check Startup folder shortcut
    shortcut = get_shortcut_path()
    if shortcut and os.path.exists(shortcut):
        return True

    # 2. Check Windows Registry Run key
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_READ)
        value, _ = winreg.QueryValueEx(key, APP_NAME)
        winreg.CloseKey(key)
        return bool(value)
    except Exception:
        return False

def set_autostart(enable: bool) -> bool:
    exe_path = get_executable_path()
    shortcut_path = get_shortcut_path()

    success = False

    # A. Manage Startup Folder Shortcut via VBScript
    if shortcut_path:
        if enable:
            try:
                os.makedirs(os.path.dirname(shortcut_path), exist_ok=True)
                vbs_script = f"""
                Set WshShell = CreateObject("WScript.Shell")
                Set shortcut = WshShell.CreateShortcut("{shortcut_path}")
                shortcut.TargetPath = "{exe_path}"
                shortcut.WorkingDirectory = "{os.path.dirname(exe_path)}"
                shortcut.Save
                """
                vbs_path = os.path.join(os.path.dirname(exe_path), "create_shortcut.vbs")
                with open(vbs_path, "w", encoding="utf-8") as f:
                    f.write(vbs_script)
                os.system(f'cscript //Nologo "{vbs_path}"')
                if os.path.exists(vbs_path):
                    os.remove(vbs_path)
                success = os.path.exists(shortcut_path)
            except Exception as e:
                print(f"Error creating startup shortcut: {e}")
        else:
            try:
                if os.path.exists(shortcut_path):
                    os.remove(shortcut_path)
                success = True
            except Exception as e:
                print(f"Error removing startup shortcut: {e}")

    # B. Manage Windows Registry Run key
    try:
        key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run")
        if enable:
            winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, f'"{exe_path}"')
        else:
            try:
                winreg.DeleteValue(key, APP_NAME)
            except Exception:
                pass
        winreg.CloseKey(key)
        success = True
    except Exception as e:
        print(f"Error setting registry autostart: {e}")

    return success
