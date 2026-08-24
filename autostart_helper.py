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

def remove_all_registry_autostart():
    """Completely wipe any legacy Registry entries in HKCU & HKLM to avoid double startup."""
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_ALL_ACCESS)
        winreg.DeleteValue(key, APP_NAME)
        winreg.CloseKey(key)
    except Exception:
        pass

def is_autostart_enabled() -> bool:
    shortcut = get_shortcut_path()
    return bool(shortcut and os.path.exists(shortcut))

def set_autostart(enable: bool) -> bool:
    exe_path = get_executable_path()
    shortcut_path = get_shortcut_path()

    # Always wipe Registry entries to ensure ONLY 1 startup location exists!
    remove_all_registry_autostart()

    if shortcut_path:
        if enable:
            try:
                os.makedirs(os.path.dirname(shortcut_path), exist_ok=True)
                vbs_script = f"""
                Set WshShell = CreateObject("WScript.Shell")
                Set shortcut = WshShell.CreateShortcut("{shortcut_path}")
                shortcut.TargetPath = "{exe_path}"
                shortcut.Arguments = "--autostart"
                shortcut.WorkingDirectory = "{os.path.dirname(exe_path)}"
                shortcut.Save
                """
                vbs_path = os.path.join(os.path.dirname(exe_path), "create_shortcut.vbs")
                with open(vbs_path, "w", encoding="utf-8") as f:
                    f.write(vbs_script)
                os.system(f'cscript //Nologo "{vbs_path}"')
                if os.path.exists(vbs_path):
                    os.remove(vbs_path)
                return os.path.exists(shortcut_path)
            except Exception as e:
                print(f"Error creating startup shortcut: {e}")
                return False
        else:
            try:
                if os.path.exists(shortcut_path):
                    os.remove(shortcut_path)
                return True
            except Exception as e:
                print(f"Error removing startup shortcut: {e}")
                return False

    return False
