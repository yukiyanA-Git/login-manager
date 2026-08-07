import asyncio
from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QHBoxLayout, QMessageBox
from PySide6.QtCore import Qt
from firebase_client import FirebaseClient

class FallbackAuthDialog(QDialog):
    def __init__(self, item_name: str, parent=None):
        super().__init__(parent)
        self.firebase = FirebaseClient()
        self.setWindowTitle("🔒 高セキュリティ認証 (Windows Hello / 予備マスターPIN)")
        self.setFixedSize(390, 210)
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.Dialog)
        self.authenticated = False

        layout = QVBoxLayout()
        layout.setSpacing(12)

        icon_label = QLabel(f"🔒 <b>{item_name}</b> は【高セキュリティ保護】です。")
        icon_label.setStyleSheet("font-size: 13px;")
        icon_label.setWordWrap(True)
        layout.addWidget(icon_label)

        sub_label = QLabel("予備マスターPINまたはパスワードを入力してください:")
        sub_label.setStyleSheet("color: #4B5563; font-size: 11px;")
        layout.addWidget(sub_label)

        self.pin_input = QLineEdit()
        self.pin_input.setEchoMode(QLineEdit.Password)
        self.pin_input.setPlaceholderText("予備マスターPINを入力 (初期: 1234)")
        self.pin_input.returnPressed.connect(self.verify_pin)
        layout.addWidget(self.pin_input)

        btn_layout = QHBoxLayout()
        btn_cancel = QPushButton("キャンセル")
        btn_cancel.clicked.connect(self.reject)
        btn_ok = QPushButton("認証して表示")
        btn_ok.setStyleSheet("background-color: #0078D4; color: white; font-weight: bold; padding: 6px 12px;")
        btn_ok.clicked.connect(self.verify_pin)

        btn_layout.addWidget(btn_cancel)
        btn_layout.addWidget(btn_ok)
        layout.addLayout(btn_layout)

        self.setLayout(layout)

    def verify_pin(self):
        typed = self.pin_input.text().strip()
        if self.firebase.verify_master_pin(typed):
            self.authenticated = True
            self.accept()
        else:
            QMessageBox.warning(self, "認証失敗", "マスターPINが正しくありません。")

def authenticate_windows_hello(item_name: str, parent=None) -> bool:
    try:
        from winrt.windows.security.credentials.ui import UserConsentVerifier, UserConsentVerificationResult

        async def verify_win_hello():
            result = await UserConsentVerifier.request_verification_async(
                f"【{item_name}】を表示するため本人確認を行います"
            )
            return result == UserConsentVerificationResult.VERIFIED

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        verified = loop.run_until_complete(verify_win_hello())
        loop.close()

        if verified:
            return True
    except Exception as e:
        print(f"[Auth Notice] Windows Hello API fallback: {e}")

    dialog = FallbackAuthDialog(item_name, parent)
    dialog.exec()
    return dialog.authenticated

class WindowsHelloAuthenticator:
    def authenticate(self, reason: str = "") -> bool:
        return authenticate_windows_hello(item_name=reason)
