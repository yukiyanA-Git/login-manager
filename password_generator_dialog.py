from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QCheckBox, QSlider, QSpinBox, QProgressBar, QGroupBox, QFrame, QApplication
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QColor
from password_generator import generate_password, evaluate_strength, SAFE_SYMBOLS

class PasswordGeneratorDialog(QDialog):
    def __init__(self, parent=None, for_field_callback=None, register_callback=None):
        """
        for_field_callback: 呼び出し元の入力欄に直接パスワードを代入するためのコールバック
        register_callback: 「このパスワードで新規アカウント登録」を押した時のコールバック
        """
        super().__init__(parent)
        self.setWindowTitle("🎲 安全なパスワード自動生成ツール")
        self.setFixedWidth(520)
        self.for_field_callback = for_field_callback
        self.register_callback = register_callback
        self.generated_password = ""

        self.setStyleSheet("""
            QDialog {
                background-color: #111827;
                color: #F9FAFB;
                font-family: 'Segoe UI', 'Meiryo', sans-serif;
            }
            QLabel {
                color: #E5E7EB;
                font-size: 13px;
            }
            QGroupBox {
                border: 1px solid #374151;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
                color: #9CA3AF;
                font-weight: bold;
                font-size: 12px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 4px;
            }
            QCheckBox {
                color: #F3F4F6;
                font-size: 12px;
                spacing: 6px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
            }
            QSlider::groove:horizontal {
                height: 6px;
                background: #374151;
                border-radius: 3px;
            }
            QSlider::sub-page:horizontal {
                background: #0078D4;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #60A5FA;
                width: 16px;
                margin-top: -5px;
                margin-bottom: -5px;
                border-radius: 8px;
            }
            QSpinBox {
                background-color: #1F2937;
                border: 1px solid #4B5563;
                border-radius: 4px;
                color: white;
                padding: 4px;
                font-weight: bold;
            }
            QPushButton {
                background-color: #374151;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 6px 12px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #4B5563;
            }
        """)

        self.init_ui()
        self.apply_preset("strong_16")

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(12)
        main_layout.setContentsMargins(18, 18, 18, 18)

        # 1. パスワード表示ボックス
        display_frame = QFrame()
        display_frame.setStyleSheet("""
            QFrame {
                background-color: #1F2937;
                border: 2px solid #0078D4;
                border-radius: 8px;
                padding: 4px 8px;
            }
        """)
        display_layout = QHBoxLayout(display_frame)
        display_layout.setContentsMargins(4, 4, 4, 4)
        display_layout.setSpacing(8)

        self.pass_display = QLineEdit()
        self.pass_display.setFont(QFont("Consolas", 15, QFont.Bold))
        self.pass_display.setStyleSheet("""
            QLineEdit {
                background: transparent;
                border: none;
                color: #38BDF8;
                selection-background-color: #0284C7;
            }
        """)
        self.pass_display.setPlaceholderText("生成されたパスワード")
        self.pass_display.textChanged.connect(self.on_password_edited)

        btn_refresh = QPushButton("🔄 再生成")
        btn_refresh.setToolTip("同じ条件で別のパスワードを再生成")
        btn_refresh.setStyleSheet("background-color: #0078D4; color: white; padding: 6px 14px;")
        btn_refresh.clicked.connect(self.generate)

        display_layout.addWidget(self.pass_display)
        display_layout.addWidget(btn_refresh)
        main_layout.addWidget(display_frame)

        # 2. 強度インジケーターバー
        strength_layout = QHBoxLayout()
        strength_layout.setContentsMargins(2, 0, 2, 0)
        self.strength_bar = QProgressBar()
        self.strength_bar.setFixedHeight(8)
        self.strength_bar.setTextVisible(False)
        self.strength_bar.setRange(0, 100)
        self.strength_bar.setStyleSheet("""
            QProgressBar {
                background-color: #374151;
                border-radius: 4px;
            }
            QProgressBar::chunk {
                background-color: #10B981;
                border-radius: 4px;
            }
        """)

        self.strength_label = QLabel("強度: 強固 (推奨)")
        self.strength_label.setFont(QFont("Segoe UI", 10, QFont.Bold))
        self.strength_label.setStyleSheet("color: #10B981;")

        strength_layout.addWidget(self.strength_bar)
        strength_layout.addWidget(self.strength_label)
        main_layout.addLayout(strength_layout)

        # 3. ワンクリック・クイックプリセット
        preset_group = QGroupBox("⚡ よく使うプリセット (ワンクリック設定)")
        preset_layout = QHBoxLayout(preset_group)
        preset_layout.setContentsMargins(8, 10, 8, 8)
        preset_layout.setSpacing(6)

        presets = [
            ("🔢 PIN 4桁", "pin_4", "数字のみ 4桁 (クレカ・暗証番号)"),
            ("🔢 PIN 6桁", "pin_6", "数字のみ 6桁 (スマホ・セキュリティPIN)"),
            ("🟡 英数 10桁", "alnum_10", "英大文字・小文字・数字 10桁 (記号なし)"),
            ("🔵 標準 12桁", "standard_12", "英数 ＋ 安全な記号 12桁 (Web標準)"),
            ("🟢 強固 16桁", "strong_16", "英数 ＋ 記号 16桁 (推奨・高セキュリティ)"),
            ("🛡️ 最強 24桁", "max_24", "英数 ＋ 記号 24桁 (最高安全)")
        ]

        for label, code, tip in presets:
            btn_p = QPushButton(label)
            btn_p.setToolTip(tip)
            btn_p.setStyleSheet("""
                QPushButton {
                    background-color: rgba(255, 255, 255, 0.08);
                    border: 1px solid rgba(255, 255, 255, 0.15);
                    color: #E5E7EB;
                    font-size: 11px;
                    padding: 5px 8px;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #0078D4;
                    color: white;
                    border-color: #60A5FA;
                }
            """)
            btn_p.clicked.connect(lambda _, c=code: self.apply_preset(c))
            preset_layout.addWidget(btn_p)

        main_layout.addWidget(preset_group)

        # 4. 詳細カスタマイズ
        custom_group = QGroupBox("⚙️ 詳細条件カスタマイズ")
        custom_layout = QVBoxLayout(custom_group)
        custom_layout.setSpacing(10)
        custom_layout.setContentsMargins(12, 12, 12, 10)

        # 長さスライダー
        length_layout = QHBoxLayout()
        length_layout.addWidget(QLabel("文字数 (桁数):"))

        self.length_slider = QSlider(Qt.Horizontal)
        self.length_slider.setRange(4, 32)
        self.length_slider.setValue(16)

        self.length_spin = QSpinBox()
        self.length_spin.setRange(4, 64)
        self.length_spin.setValue(16)
        self.length_spin.setFixedWidth(55)

        self.length_slider.valueChanged.connect(self.length_spin.setValue)
        self.length_spin.valueChanged.connect(self.length_slider.setValue)
        self.length_spin.valueChanged.connect(lambda _: self.generate())

        length_layout.addWidget(self.length_slider)
        length_layout.addWidget(self.length_spin)
        custom_layout.addLayout(length_layout)

        # 文字種チェックボックス (2列グリッド)
        checks_row1 = QHBoxLayout()
        self.chk_upper = QCheckBox("🔠 英大文字 (A-Z)")
        self.chk_lower = QCheckBox("🔡 英小文字 (a-z)")
        self.chk_digits = QCheckBox("🔢 数字 (0-9)")
        for chk in [self.chk_upper, self.chk_lower, self.chk_digits]:
            chk.setChecked(True)
            chk.stateChanged.connect(lambda _: self.generate())
            checks_row1.addWidget(chk)
        custom_layout.addLayout(checks_row1)

        checks_row2 = QHBoxLayout()
        self.chk_symbols = QCheckBox(f"✨ 安全な記号 ({SAFE_SYMBOLS})")
        self.chk_symbols.setChecked(True)
        self.chk_symbols.setToolTip("SQL/HTMLなどのトラブルを起こす記号( ' \" < > \\ 等)を除外した安全な記号セット")
        self.chk_symbols.stateChanged.connect(lambda _: self.generate())

        self.chk_exclude_ambiguous = QCheckBox("👁️ 紛らわしい文字を除く (1, l, I, 0, O)")
        self.chk_exclude_ambiguous.setChecked(False)
        self.chk_exclude_ambiguous.setToolTip("紙のメモや手動入力時に見間違いやすい文字をあらかじめ除外します")
        self.chk_exclude_ambiguous.stateChanged.connect(lambda _: self.generate())

        checks_row2.addWidget(self.chk_symbols)
        checks_row2.addWidget(self.chk_exclude_ambiguous)
        custom_layout.addLayout(checks_row2)

        main_layout.addWidget(custom_group)

        # 5. アクションボタン群
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        btn_layout.setContentsMargins(0, 8, 0, 0)

        self.btn_copy = QPushButton("📋 パスワードをコピー")
        self.btn_copy.setStyleSheet("""
            QPushButton {
                background-color: #10B981;
                color: white;
                font-size: 13px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #059669;
            }
        """)
        self.btn_copy.clicked.connect(self.copy_password)
        btn_layout.addWidget(self.btn_copy)

        if self.for_field_callback:
            btn_use = QPushButton("✓ 入力欄にセットして閉じる")
            btn_use.setStyleSheet("""
                QPushButton {
                    background-color: #0078D4;
                    color: white;
                    font-size: 13px;
                    padding: 8px 16px;
                }
                QPushButton:hover {
                    background-color: #005A9E;
                }
            """)
            btn_use.clicked.connect(self.apply_to_field)
            btn_layout.addWidget(btn_use)

        btn_register = QPushButton("➕ このパスワードで新規アカウント登録")
        btn_register.setStyleSheet("""
            QPushButton {
                background-color: #4F46E5;
                color: white;
                font-size: 13px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #4338CA;
            }
        """)
        btn_register.clicked.connect(self.trigger_register_with_password)
        btn_layout.addWidget(btn_register)

        btn_close = QPushButton("閉じる")
        btn_close.clicked.connect(self.reject)
        btn_layout.addWidget(btn_close)

        main_layout.addLayout(btn_layout)

    def apply_preset(self, preset_code: str):
        self.blockSignals(True)
        if preset_code == "pin_4":
            self.length_spin.setValue(4)
            self.chk_upper.setChecked(False)
            self.chk_lower.setChecked(False)
            self.chk_digits.setChecked(True)
            self.chk_symbols.setChecked(False)
        elif preset_code == "pin_6":
            self.length_spin.setValue(6)
            self.chk_upper.setChecked(False)
            self.chk_lower.setChecked(False)
            self.chk_digits.setChecked(True)
            self.chk_symbols.setChecked(False)
        elif preset_code == "alnum_10":
            self.length_spin.setValue(10)
            self.chk_upper.setChecked(True)
            self.chk_lower.setChecked(True)
            self.chk_digits.setChecked(True)
            self.chk_symbols.setChecked(False)
        elif preset_code == "standard_12":
            self.length_spin.setValue(12)
            self.chk_upper.setChecked(True)
            self.chk_lower.setChecked(True)
            self.chk_digits.setChecked(True)
            self.chk_symbols.setChecked(True)
        elif preset_code == "strong_16":
            self.length_spin.setValue(16)
            self.chk_upper.setChecked(True)
            self.chk_lower.setChecked(True)
            self.chk_digits.setChecked(True)
            self.chk_symbols.setChecked(True)
        elif preset_code == "max_24":
            self.length_spin.setValue(24)
            self.chk_upper.setChecked(True)
            self.chk_lower.setChecked(True)
            self.chk_digits.setChecked(True)
            self.chk_symbols.setChecked(True)
        self.blockSignals(False)
        self.generate()

    def generate(self):
        length = self.length_spin.value()
        use_upper = self.chk_upper.isChecked()
        use_lower = self.chk_lower.isChecked()
        use_digits = self.chk_digits.isChecked()
        use_symbols = self.chk_symbols.isChecked()
        exclude_ambiguous = self.chk_exclude_ambiguous.isChecked()

        pw = generate_password(
            length=length,
            use_upper=use_upper,
            use_lower=use_lower,
            use_digits=use_digits,
            use_symbols=use_symbols,
            exclude_ambiguous=exclude_ambiguous
        )
        self.generated_password = pw
        self.pass_display.setText(pw)
        self.update_strength(pw)

    def on_password_edited(self, text: str):
        self.generated_password = text
        self.update_strength(text)

    def update_strength(self, pw: str):
        score, label, color = evaluate_strength(pw)
        self.strength_bar.setValue(score)
        self.strength_bar.setStyleSheet(f"""
            QProgressBar {{
                background-color: #374151;
                border-radius: 4px;
            }}
            QProgressBar::chunk {{
                background-color: {color};
                border-radius: 4px;
            }}
        """)
        self.strength_label.setText(f"強度: {label}")
        self.strength_label.setStyleSheet(f"color: {color};")

    def copy_password(self):
        pw = self.pass_display.text()
        if pw:
            QApplication.clipboard().setText(pw)
            self.btn_copy.setText("✅ コピーしました！")
            QTimer.singleShot(1500, lambda: self.btn_copy.setText("📋 パスワードをコピー"))

    def apply_to_field(self):
        pw = self.pass_display.text()
        if self.for_field_callback and pw:
            self.for_field_callback(pw)
        self.accept()

    def trigger_register_with_password(self):
        pw = self.pass_display.text()
        if self.register_callback and pw:
            self.accept()
            self.register_callback(pw)
        elif self.for_field_callback and pw:
            self.apply_to_field()
        else:
            self.copy_password()
            self.accept()
