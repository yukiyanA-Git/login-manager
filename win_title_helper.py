import ctypes
from typing import Optional

def get_active_window_title() -> str:
    """Returns the title string of the currently focused window on Windows."""
    try:
        hwnd = ctypes.windll.user32.GetForegroundWindow()
        length = ctypes.windll.user32.GetWindowTextLengthW(hwnd)
        if length > 0:
            buff = ctypes.create_unicode_buffer(length + 1)
            ctypes.windll.user32.GetWindowTextW(hwnd, buff, length + 1)
            return buff.value
    except Exception as e:
        print(f"Error getting window title: {e}")
    return ""
