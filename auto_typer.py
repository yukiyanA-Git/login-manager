import time
import ctypes
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer

# Windows Key Codes
VK_TAB = 0x09
VK_RETURN = 0x0D
VK_CONTROL = 0x11
VK_V = 0x56

KEYEVENTF_KEYUP = 0x0002

def _key_down(vk_code: int):
    ctypes.windll.user32.keybd_event(vk_code, 0, 0, 0)

def _key_up(vk_code: int):
    ctypes.windll.user32.keybd_event(vk_code, 0, KEYEVENTF_KEYUP, 0)

def _simulate_key(vk_code: int):
    _key_down(vk_code)
    time.sleep(0.03)
    _key_up(vk_code)
    time.sleep(0.05)

def _simulate_paste():
    """Simulates Ctrl + V keystroke."""
    _key_down(VK_CONTROL)
    _key_down(VK_V)
    time.sleep(0.04)
    _key_up(VK_V)
    _key_up(VK_CONTROL)
    time.sleep(0.08)

def copy_and_paste_text(text: str):
    """Copies text to clipboard and simulates Ctrl+V paste into active control."""
    if not text:
        return
    clipboard = QApplication.clipboard()
    clipboard.setText(text)
    time.sleep(0.05)
    _simulate_paste()

def auto_fill_credentials(username: str, password: str, auto_submit: bool = False, delay_ms: int = 350):
    """
    Auto-fills Username and Password into the target window:
    1. Waits delay_ms (so focus returns to browser window after popup hides).
    2. Pastes Username (via Ctrl+V).
    3. Simulates Tab key.
    4. Pastes Password (via Ctrl+V).
    5. Optionally simulates Enter key.
    """
    def _do_auto_fill():
        # Step 1: Paste Username
        if username:
            copy_and_paste_text(username)
            time.sleep(0.15)

        # Step 2: Tab to Password field
        _simulate_key(VK_TAB)
        time.sleep(0.15)

        # Step 3: Paste Password
        if password:
            copy_and_paste_text(password)
            time.sleep(0.15)

        # Step 4: Optional Enter
        if auto_submit:
            _simulate_key(VK_RETURN)

    QTimer.singleShot(delay_ms, _do_auto_fill)
