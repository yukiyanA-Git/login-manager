from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit, QFrame, QApplication, QTextEdit
)
from PySide6.QtCore import Qt, QTimer, QPoint
from PySide6.QtGui import QFont, QClipboard

class FloatingPopupWindow(QWidget):
    def __init__(self, account_data: dict, pos: QPoint = None, parent=None):
        super().__init__(parent)
        self.account_data = account_data
        self.password_visible = False
        self.notes_expanded = False

        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedWidth(360)
        self.setFixedHeight(230)

        if pos:
            screen = QApplication.primaryScreen().geometry()
            x = min(pos.x() + 10, screen.width() - 370)
            y = min(pos.y() + 10, screen.height() - 300)
            self.move(max(10, x), max(10, y))

        self.init_ui()

    def init_ui(self):
        self.main_frame = QFrame(self)
        self.main_frame.setGeometry(0, 0, 360, 230)
        self.main_frame.setStyleSheet("""
            QFrame {
                background-color: #111827;
                border: 2px solid #0078D4;
                border-radius: 12px;
                color: #F9FAFB;
            }
            QLabel {
                border: none;
                font-family: 'Segoe UI', 'Meiryo', sans-serif;
            }
            QPushButton {
                background-color: #1F2937;
                border: 1px solid #374151;
                border-radius: 6px;
                color: #F3F4F6;
                padding: 4px 10px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #0078D4;
                color: #FFFFFF;
            }
            QLineEdit, QTextEdit {
                background-color: #1F2937;
                border: 1px solid #374151;
                border-radius: 6px;
                color: #6EE7B7;
                padding: 4px 8px;
                font-weight: bold;
            }
        """)

        self.layout = QVBoxLayout(self.main_frame)
        self.layout.setContentsMargins(16, 12, 16, 12)
        self.layout.setSpacing(8)

        # Header bar
        header_layout = QHBoxLayout()
        name_label = QLabel(f"🏢 <b>{self.account_data.get('name', 'サービス名')}</b>")
        name_label.setFont(QFont("Segoe UI", 12, QFont.Bold))

        sec_level = self.account_data.get('security_level', 1)
        badge_text = "🟢 低 (標準)" if sec_level == 1 else "🔒 高 (要認証)"
        badge_color = "#10B981" if sec_level == 1 else "#F59E0B"
        badge = QLabel(badge_text)
        badge.setStyleSheet(f"background: {badge_color}; color: white; border-radius: 4px; padding: 2px 6px; font-size: 10px; font-weight: bold;")

        btn_close = QPushButton("✕")
        btn_close.setFixedSize(24, 24)
        btn_close.setStyleSheet("background: transparent; border: none; color: #9CA3AF; font-size: 14px;")
        btn_close.clicked.connect(self.close)

        header_layout.addWidget(name_label)
        header_layout.addWidget(badge)
        header_layout.addStretch()
        header_layout.addWidget(btn_close)
        self.layout.addLayout(header_layout)

        # ID Line with prominent 1-click copy button
        id_layout = QHBoxLayout()
        id_label = QLabel("ID / メール:")
        id_label.setFixedWidth(75)
        self.id_field = QLineEdit(self.account_data.get('username', ''))
        self.id_field.setReadOnly(True)

        btn_copy_id = QPushButton("📋 IDをコピー")
        btn_copy_id.setStyleSheet("background-color: #059669; color: white; font-weight: bold;")
        btn_copy_id.clicked.connect(self.copy_id)

        id_layout.addWidget(id_label)
        id_layout.addWidget(self.id_field)
        id_layout.addWidget(btn_copy_id)
        self.layout.addLayout(id_layout)

        # Password Line with prominent 1-click copy button
        pass_layout = QHBoxLayout()
        pass_label = QLabel("パスワード:")
        pass_label.setFixedWidth(75)

        self.pass_field = QLineEdit(self.account_data.get('password', ''))
        self.pass_field.setEchoMode(QLineEdit.Password)
        self.pass_field.setReadOnly(True)

        btn_toggle = QPushButton("👁️")
        btn_toggle.setFixedWidth(30)
        btn_toggle.clicked.connect(self.toggle_password_visibility)

        btn_copy_pass = QPushButton("📋 パスワードコピー")
        btn_copy_pass.setStyleSheet("background-color: #2563EB; color: white; font-weight: bold;")
        btn_copy_pass.clicked.connect(self.copy_password)

        pass_layout.addWidget(pass_label)
        pass_layout.addWidget(self.pass_field)
        pass_layout.addWidget(btn_toggle)
        pass_layout.addWidget(btn_copy_pass)
        self.layout.addLayout(pass_layout)

        # Optional Notes & Security Questions Accordion
        has_notes = bool(self.account_data.get("notes") or self.account_data.get("sec_question") or self.account_data.get("sec_answer"))
        if has_notes:
            self.btn_expand_notes = QPushButton("📝 備考・秘密の質問を表示 (▼)")
            self.btn_expand_notes.setStyleSheet("background-color: #374151; color: #F3F4F6; font-size: 11px;")
            self.btn_expand_notes.clicked.connect(self.toggle_notes)
            self.layout.addWidget(self.btn_expand_notes)

            self.notes_container = QWidget()
            notes_layout = QVBoxLayout(self.notes_container)
            notes_layout.setContentsMargins(0, 0, 0, 0)
            notes_layout.setSpacing(6)

            if self.account_data.get("sec_question"):
                q_label = QLabel(f"<b>秘密の質問:</b> {self.account_data.get('sec_question')}")
                q_label.setStyleSheet("color: #FBBF24; font-size: 11px;")
                notes_layout.addWidget(q_label)

            if self.account_data.get("sec_answer"):
                ans_layout = QHBoxLayout()
                ans_label = QLabel("秘密の答え:")
                ans_label.setFixedWidth(75)
                ans_field = QLineEdit(self.account_data.get("sec_answer"))
                ans_field.setReadOnly(True)
                btn_copy_ans = QPushButton("📋 コピー")
                btn_copy_ans.clicked.connect(lambda: self.copy_text(self.account_data.get("sec_answer"), "秘密の答えをコピーしました！"))
                ans_layout.addWidget(ans_label)
                ans_layout.addWidget(ans_field)
                ans_layout.addWidget(btn_copy_ans)
                notes_layout.addLayout(ans_layout)

            if self.account_data.get("notes"):
                note_edit = QTextEdit()
                note_edit.setPlainText(self.account_data.get("notes"))
                note_edit.setReadOnly(True)
                note_edit.setFixedHeight(50)
                notes_layout.addWidget(note_edit)

            self.notes_container.setVisible(False)
            self.layout.addWidget(self.notes_container)

        # Toast notification label
        self.toast_label = QLabel("")
        self.toast_label.setAlignment(Qt.AlignCenter)
        self.toast_label.setStyleSheet("color: #34D399; font-size: 11px; font-weight: bold;")
        self.layout.addWidget(self.toast_label)

    def toggle_notes(self):
        self.notes_expanded = not self.notes_expanded
        self.notes_container.setVisible(self.notes_expanded)
        if self.notes_expanded:
            self.btn_expand_notes.setText("📝 備考・秘密の質問を閉じる (▲)")
            self.setFixedHeight(340)
            self.main_frame.setFixedHeight(340)
        else:
            self.btn_expand_notes.setText("📝 備考・秘密の質問を表示 (▼)")
            self.setFixedHeight(230)
            self.main_frame.setFixedHeight(230)

    def toggle_password_visibility(self):
        self.password_visible = not self.password_visible
        if self.password_visible:
            self.pass_field.setEchoMode(QLineEdit.Normal)
        else:
            self.pass_field.setEchoMode(QLineEdit.Password)

    def copy_id(self):
        self.copy_text(self.account_data.get('username', ''), "📋 IDをコピーしました！(Ctrl+Vで貼り付け)")

    def copy_password(self):
        self.copy_text(self.account_data.get('password', ''), "📋 パスワードをコピーしました！(Ctrl+Vで貼り付け)")

    def copy_text(self, text: str, toast_msg: str):
        clipboard = QApplication.clipboard()
        clipboard.setText(text)
        self.toast_label.setText(toast_msg)
        QTimer.singleShot(2500, lambda: self.toast_label.setText(""))
