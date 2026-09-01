import os
import csv
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QFileDialog, QMessageBox,
    QDialog, QFormLayout, QLineEdit, QComboBox, QGroupBox, QTextEdit, QApplication,
    QFrame, QTabWidget, QTextBrowser
)
from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QColor, QFont, QClipboard, QDesktopServices, QPixmap

from autostart_helper import is_autostart_enabled, set_autostart

class DataMigrationHelpDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("💡 PCのお引っ越し ＆ バックアップ保存 完全ガイド")
        self.resize(600, 480)

        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        title_label = QLabel("<b>💡 パスワードデータのバックアップ ＆ 新PCへの移行手順</b>")
        title_label.setStyleSheet("font-size: 14px; color: #1F2937;")
        layout.addWidget(title_label)

        browser = QTextBrowser()
        browser.setOpenExternalLinks(True)
        html_content = """
        <style>
            body { font-family: sans-serif; font-size: 12px; color: #374151; line-height: 1.6; }
            h3 { color: #0078D4; margin-top: 14px; margin-bottom: 6px; border-bottom: 1px solid #E5E7EB; padding-bottom: 4px; }
            .box { background-color: #F3F4F6; border-left: 4px solid #0078D4; padding: 10px; margin: 8px 0; border-radius: 4px; }
            .tip { background-color: #ECFDF5; border-left: 4px solid #10B981; padding: 10px; margin: 8px 0; border-radius: 4px; }
            ul { margin-top: 4px; padding-left: 20px; }
            li { margin-bottom: 4px; }
            b { color: #111827; }
        </style>

        <div class="box">
            <b>🔑 本アプリの基本動作（ローカル安全設計）</b><br>
            本アプリはお客様のセキュリティとプライバシーを守るため、<b>通常時は100%完全オフライン（PC内部のAES-256暗号化ファイル）</b>で安全・高速に動作します。
        </div>

        <h3>📦 方法1. CSVファイルを使ったお引っ越し（手軽・おすすめ）</h3>
        <p>USBメモリやファイル共有を使って、最も簡単かつ確実にデータを移行できます。</p>
        <ul>
            <li><b>【旧PCでの操作】</b>: 管理画面の <b>[📤 登録データをCSV出力(バックアップ)]</b> をクリックし、CSVファイルをUSBメモリ等に保存します。</li>
            <li><b>【新PCでの操作】</b>: 新しいPCにLoginManagerをインストール後、管理画面の <b>[📥 CSV一括取り込み]</b> をクリックして先ほどのファイルを選択します。一秒で全データが復元されます！</li>
        </ul>

        <h3>☁️ 方法2. オンデマンド・クラウドバックアップを使ったお引っ越し</h3>
        <p>USBメモリが手元にない場合や、定期的なオンラインバックアップとして活用できます。</p>
        <ul>
            <li><b>【旧PCでの操作】</b>: 管理画面の <b>[☁️ クラウドへ保存]</b> を押し、マスターPINとGoogleメールアドレスを入力して保存します。<b>※保存完了後通信は即座に完全自動切断されます。</b></li>
            <li><b>【新PCでの操作】</b>: 新PCの管理画面で <b>[☁️ クラウドから復元]</b> を押し、同じGoogleアドレスとマスターPINを入力するだけで復元完了です。</li>
        </ul>

        <div class="tip">
            <b>🛡️ 定期バックアップのススメ</b><br>
            万が一のパソコンの故障や紛失に備え、月に1回程度<b>「CSV出力」</b>または<b>「クラウドへ保存」</b>を行っておくことを推奨いたします。
        </div>
        """
        browser.setHtml(html_content)
        layout.addWidget(browser)

        btn_close = QPushButton("閉じる")
        btn_close.setStyleSheet("background-color: #0078D4; color: white; font-weight: bold; padding: 6px 20px;")
        btn_close.clicked.connect(self.accept)

        btn_box = QHBoxLayout()
        btn_box.addStretch()
        btn_box.addWidget(btn_close)
        layout.addLayout(btn_box)


class OnDemandCloudDialog(QDialog):
    def __init__(self, firebase_client, mode="backup", parent=None):
        super().__init__(parent)
        self.firebase = firebase_client
        self.mode = mode

        is_backup = (mode == "backup")
        self.setWindowTitle("☁️ オンデマンド・クラウド保存 (暗号化バックアップ)" if is_backup else "☁️ クラウドからデータを復元")
        self.setFixedWidth(440)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        info_text = (
            "<b>安全な一時クラウドバックアップ保存</b><br>"
            "暗証確認後、あなた専用のGoogleクラウド保存領域へデータを安全送信します。<br>"
            "<b>※保存完了後、通信は即座に完全自動切断されます。</b>"
        ) if is_backup else (
            "<b>クラウドからの安全データ復元</b><br>"
            "暗証確認後、以前保存したバックアップデータをGoogleクラウドからダウンロード復元します。<br>"
            "<b>※復元完了後、通信は即座に完全自動切断されます。</b>"
        )

        info_label = QLabel(info_text)
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: #374151; font-size: 11px;")
        layout.addWidget(info_label)

        form = QFormLayout()

        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("例: your_name@gmail.com")

        self.pin_input = QLineEdit()
        self.pin_input.setEchoMode(QLineEdit.Password)
        self.pin_input.setPlaceholderText("マスターPIN (4〜6桁 / 初期: 1234)")

        form.addRow("Googleメールアドレス:", self.email_input)
        form.addRow("マスターPIN (暗証番号):", self.pin_input)
        layout.addLayout(form)

        btn_box = QHBoxLayout()
        btn_cancel = QPushButton("キャンセル")
        btn_cancel.clicked.connect(self.reject)

        btn_action = QPushButton("☁️ 今すぐクラウドへ保存" if is_backup else "☁️ クラウドからデータを復元")
        btn_action.setStyleSheet("background-color: #0078D4; color: white; font-weight: bold; padding: 6px 14px;")
        btn_action.clicked.connect(self.do_action)

        btn_box.addWidget(btn_cancel)
        btn_box.addWidget(btn_action)
        layout.addLayout(btn_box)

    def do_action(self):
        email = self.email_input.text().strip()
        pin = self.pin_input.text().strip()

        if not email or "@" not in email:
            QMessageBox.warning(self, "入力エラー", "有効なGoogleメールアドレスを入力してください。")
            return

        if not pin:
            QMessageBox.warning(self, "入力エラー", "マスターPIN（暗証番号）を入力してください。")
            return

        self.user_email = email
        self.user_pin = pin
        self.accept()


class MasterPinSettingDialog(QDialog):
    def __init__(self, firebase_client, parent=None):
        super().__init__(parent)
        self.firebase = firebase_client
        self.setWindowTitle("🔑 予備マスターPINの変更")
        self.setFixedWidth(420)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        info_label = QLabel(
            "<b>予備マスターPIN（高セキュリティ解除用）の変更</b><br>"
            "Windows Helloが使えない環境や会社PCで使う暗証番号（4〜6桁）と、思い出せるヒントを設定します。"
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: #374151; font-size: 11px;")
        layout.addWidget(info_label)

        form = QFormLayout()
        self.old_pin_input = QLineEdit()
        self.old_pin_input.setEchoMode(QLineEdit.Password)
        self.old_pin_input.setPlaceholderText("現在のマスターPIN (初期: 1234)")

        self.new_pin_input = QLineEdit()
        self.new_pin_input.setEchoMode(QLineEdit.Password)
        self.new_pin_input.setPlaceholderText("新しいマスターPIN (4〜6桁)")

        self.confirm_pin_input = QLineEdit()
        self.confirm_pin_input.setEchoMode(QLineEdit.Password)
        self.confirm_pin_input.setPlaceholderText("新しいマスターPIN (確認用再入力)")

        self.hint_input = QLineEdit()
        self.hint_input.setText(self.firebase.master_pin_hint)
        self.hint_input.setPlaceholderText("例: 母親の誕生日の下4桁 / 愛車のナンバー")

        form.addRow("現在のマスターPIN:", self.old_pin_input)
        form.addRow("新しいマスターPIN:", self.new_pin_input)
        form.addRow("新しいPIN(確認):", self.confirm_pin_input)
        form.addRow("忘れた時のヒント:", self.hint_input)
        layout.addLayout(form)

        btn_box = QHBoxLayout()
        btn_cancel = QPushButton("キャンセル")
        btn_cancel.clicked.connect(self.reject)

        btn_save = QPushButton("💾 マスターPINを保存")
        btn_save.setStyleSheet("background-color: #0078D4; color: white; font-weight: bold; padding: 6px 14px;")
        btn_save.clicked.connect(self.do_save)

        btn_box.addWidget(btn_cancel)
        btn_box.addWidget(btn_save)
        layout.addLayout(btn_box)

    def do_save(self):
        old_typed = self.old_pin_input.text().strip()
        new_typed = self.new_pin_input.text().strip()
        confirm_typed = self.confirm_pin_input.text().strip()
        hint_typed = self.hint_input.text().strip()

        if not self.firebase.verify_master_pin(old_typed):
            QMessageBox.warning(self, "エラー", "現在のマスターPINが正しくありません。")
            return

        if len(new_typed) < 4:
            QMessageBox.warning(self, "エラー", "新しいマスターPINは4桁以上で入力してください。")
            return

        if new_typed != confirm_typed:
            QMessageBox.warning(self, "エラー", "新しいマスターPINと確認用の入力が一致しません。")
            return

        self.firebase.save_master_pin(new_typed, hint=hint_typed)
        QMessageBox.information(self, "変更完了", "マスターPINおよびヒントメモを正常に変更保存しました。")
        self.accept()


class AccountAddDialog(QDialog):
    def __init__(self, initial_name: str = "", logo_b64: str = "", edit_data: dict = None, overlay_callback=None, parent=None):
        super().__init__(parent)
        self.edit_data = edit_data
        is_edit = bool(edit_data)

        self.setWindowTitle("✏️ アカウント情報の編集" if is_edit else "新しいログイン情報の登録")
        self.setFixedWidth(470)
        self.overlay_callback = overlay_callback
        self.logo_b64 = logo_b64 or (edit_data.get("logo_image", "") if edit_data else "")
        self.extra_expanded = is_edit

        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        logo_box = QHBoxLayout()
        self.logo_status_label = QLabel("🖼️ ロゴ画像: あり (比較照合可能)" if self.logo_b64 else "🖼️ ロゴ画像: 未登録")
        self.logo_status_label.setStyleSheet("color: #059669; font-weight: bold; font-size: 11px;" if self.logo_b64 else "color: #9CA3AF; font-size: 11px;")

        btn_capture_logo = QPushButton("🖼️ 画面からロゴ画像を取得/変更")
        btn_capture_logo.setStyleSheet("background-color: #059669; color: white; font-size: 11px; font-weight: bold;")
        btn_capture_logo.clicked.connect(self.trigger_capture_logo)

        logo_box.addWidget(self.logo_status_label)
        logo_box.addStretch()
        logo_box.addWidget(btn_capture_logo)
        layout.addLayout(logo_box)

        form_layout = QFormLayout()
        form_layout.setSpacing(10)

        name_layout = QHBoxLayout()
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("例: Sansan, マネーフォワード, Amazon")

        clip_text = QApplication.clipboard().text().strip()
        if is_edit:
            self.name_input.setText(edit_data.get("name", ""))
        elif initial_name:
            self.name_input.setText(initial_name)
        elif clip_text and len(clip_text) < 50:
            self.name_input.setText(clip_text)

        btn_ocr_fill = QPushButton("📋 コピー文/画面から自動入力")
        btn_ocr_fill.setStyleSheet("background-color: #4F46E5; color: white; font-size: 11px; font-weight: bold;")
        btn_ocr_fill.clicked.connect(self.trigger_auto_fill)

        name_layout.addWidget(self.name_input)
        name_layout.addWidget(btn_ocr_fill)
        form_layout.addRow("会社名 *:", name_layout)

        self.user_input = QLineEdit()
        self.user_input.setPlaceholderText("例: user@example.com / ID")
        if is_edit:
            self.user_input.setText(edit_data.get("username", ""))
        form_layout.addRow("ID / メール *:", self.user_input)

        self.pass_input = QLineEdit()
        self.pass_input.setEchoMode(QLineEdit.Password)
        self.pass_input.setPlaceholderText("パスワード")
        if is_edit:
            self.pass_input.setText(edit_data.get("password", ""))
        form_layout.addRow("パスワード *:", self.pass_input)

        self.level_combo = QComboBox()
        self.level_combo.addItem("🟢 セキュリティ：低 (認証なし・すぐ表示)", 1)
        self.level_combo.addItem("🔒 セキュリティ：高 (顔認証/指紋/PINを要求)", 3)
        if is_edit:
            idx = self.level_combo.findData(edit_data.get("security_level", 1))
            if idx >= 0:
                self.level_combo.setCurrentIndex(idx)
        form_layout.addRow("セキュリティレベル *:", self.level_combo)

        layout.addLayout(form_layout)

        self.btn_toggle_extra = QPushButton("－ 詳細・製品名(別名)を隠す (▲)" if is_edit else "＋ 製品名(別名)・備考・秘密の質問を追加 (オプション)")
        self.btn_toggle_extra.setStyleSheet("background-color: #374151; color: #F3F4F6; font-size: 11px;")
        self.btn_toggle_extra.clicked.connect(self.toggle_extra_fields)
        layout.addWidget(self.btn_toggle_extra)

        self.extra_widget = QWidget()
        extra_form = QFormLayout(self.extra_widget)
        extra_form.setContentsMargins(0, 0, 0, 0)
        extra_form.setSpacing(8)

        f1_layout = QHBoxLayout()
        self.field1_name_input = QLineEdit()
        self.field1_name_input.setPlaceholderText("項目名 (例: 契約番号)")
        self.field1_name_input.setFixedWidth(150)
        self.field1_val_input = QLineEdit()
        self.field1_val_input.setPlaceholderText("文字列 (例: C12345678)")

        if is_edit:
            f1_n = edit_data.get("field1_name", "")
            if f1_n and f1_n != "追加項目1":
                self.field1_name_input.setText(f1_n)
            self.field1_val_input.setText(edit_data.get("field1_value") or edit_data.get("alias1", ""))

        f1_layout.addWidget(self.field1_name_input)
        f1_layout.addWidget(self.field1_val_input)

        f2_layout = QHBoxLayout()
        self.field2_name_input = QLineEdit()
        self.field2_name_input.setPlaceholderText("項目名 (例: 法人コード)")
        self.field2_name_input.setFixedWidth(150)
        self.field2_val_input = QLineEdit()
        self.field2_val_input.setPlaceholderText("文字列 (例: CORP-998)")

        if is_edit:
            f2_n = edit_data.get("field2_name", "")
            if f2_n and f2_n != "追加項目2":
                self.field2_name_input.setText(f2_n)
            self.field2_val_input.setText(edit_data.get("field2_value") or edit_data.get("alias2", ""))

        f2_layout.addWidget(self.field2_name_input)
        f2_layout.addWidget(self.field2_val_input)

        self.notes_input = QTextEdit()
        self.notes_input.setPlaceholderText("メモ、製品名別名、補足など")
        self.notes_input.setFixedHeight(45)
        if is_edit:
            self.notes_input.setPlainText(edit_data.get("notes", ""))

        self.sec_q_input = QLineEdit()
        self.sec_q_input.setPlaceholderText("例: 母親の旧姓 / 初めて飼ったペット")
        if is_edit:
            self.sec_q_input.setText(edit_data.get("sec_question", ""))

        self.sec_a_input = QLineEdit()
        self.sec_a_input.setPlaceholderText("秘密の答え")
        if is_edit:
            self.sec_a_input.setText(edit_data.get("sec_answer", ""))

        self.category_input = QLineEdit()
        self.category_input.setText(edit_data.get("category", "一般") if is_edit else "一般")

        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://...")
        if is_edit:
            self.url_input.setText(edit_data.get("url", ""))

        extra_form.addRow("🔑 第3の認証項目:", f1_layout)
        extra_form.addRow("🔑 第4の認証項目:", f2_layout)
        extra_form.addRow("備考・メモ:", self.notes_input)
        extra_form.addRow("秘密の質問:", self.sec_q_input)
        extra_form.addRow("秘密の答え:", self.sec_a_input)
        extra_form.addRow("カテゴリー:", self.category_input)
        extra_form.addRow("URL:", self.url_input)

        self.extra_widget.setVisible(self.extra_expanded)
        layout.addWidget(self.extra_widget)

        btn_box = QHBoxLayout()
        btn_cancel = QPushButton("キャンセル")
        btn_cancel.clicked.connect(self.reject)
        btn_save = QPushButton("更新保存" if is_edit else "保存")
        btn_save.setStyleSheet("background-color: #0078D4; color: white; font-weight: bold; padding: 6px 16px;")
        btn_save.clicked.connect(self.accept)

        btn_box.addWidget(btn_cancel)
        btn_box.addWidget(btn_save)
        layout.addLayout(btn_box)

    def trigger_capture_logo(self):
        if self.overlay_callback:
            self.hide()
            self.overlay_callback(self.set_logo_and_reopen)

    def set_logo_and_reopen(self, detected_name: str, logo_b64: str = ""):
        if logo_b64:
            self.logo_b64 = logo_b64
            self.logo_status_label.setText("🖼️ ロゴ画像: キャプチャ登録完了")
            self.logo_status_label.setStyleSheet("color: #059669; font-weight: bold; font-size: 11px;")
        if detected_name and not self.name_input.text():
            self.name_input.setText(detected_name)
        self.show()

    def toggle_extra_fields(self):
        self.extra_expanded = not self.extra_expanded
        self.extra_widget.setVisible(self.extra_expanded)
        if self.extra_expanded:
            self.btn_toggle_extra.setText("－ 詳細・製品名(別名)を隠す (▲)")
        else:
            self.btn_toggle_extra.setText("＋ 製品名(別名)・備考・秘密の質問を追加 (オプション)")

    def trigger_auto_fill(self):
        clip_text = QApplication.clipboard().text().strip()
        if clip_text and len(clip_text) < 50:
            self.name_input.setText(clip_text)
            return

        if self.overlay_callback:
            self.hide()
            self.overlay_callback(self.set_company_name_and_reopen)

    def set_company_name_and_reopen(self, detected_name: str, logo_b64: str = ""):
        if detected_name:
            self.name_input.setText(detected_name)
        if logo_b64:
            self.logo_b64 = logo_b64
            self.logo_status_label.setText("🖼️ ロゴ画像: あり (比較照合可能)")
            self.logo_status_label.setStyleSheet("color: #059669; font-weight: bold; font-size: 11px;")
        self.show()

    def get_data(self):
        f1_name = self.field1_name_input.text().strip()
        f1_val = self.field1_val_input.text().strip()
        f2_name = self.field2_name_input.text().strip()
        f2_val = self.field2_val_input.text().strip()

        return {
            "name": self.name_input.text().strip(),
            "alias1": f1_val,
            "alias2": f2_val,
            "field1_name": f1_name,
            "field1_value": f1_val,
            "field2_name": f2_name,
            "field2_value": f2_val,
            "username": self.user_input.text().strip(),
            "password": self.pass_input.text().strip(),
            "security_level": self.level_combo.currentData(),
            "notes": self.notes_input.toPlainText().strip(),
            "sec_question": self.sec_q_input.text().strip(),
            "sec_answer": self.sec_a_input.text().strip(),
            "category": self.category_input.text().strip(),
            "url": self.url_input.text().strip(),
            "logo_image": self.logo_b64
        }


class AccountManagerWindow(QMainWindow):
    def __init__(self, vault_instance, overlay_instance=None):
        super().__init__()
        self.vault = vault_instance
        self.overlay = overlay_instance

        self.setWindowTitle("ログインマネージャー - アカウント管理 & 設定")
        self.resize(960, 600)
        self.init_ui()

    def closeEvent(self, event):
        event.ignore()
        self.hide()

    def init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)

        header_box = QGroupBox("セキュリティ ＆ バックアップ動作設定")
        header_layout = QHBoxLayout(header_box)

        self.status_label = QLabel("🟢 ローカル安全動作モード (完全オフライン保存中)")
        self.status_label.setFont(QFont("Segoe UI", 9, QFont.Bold))
        self.status_label.setStyleSheet("color: #059669;")

        btn_cloud_save = QPushButton("☁️ クラウドへ保存")
        btn_cloud_save.setStyleSheet("background-color: #0078D4; color: white; font-weight: bold; padding: 4px 10px;")
        btn_cloud_save.clicked.connect(self.on_cloud_backup_clicked)

        btn_cloud_restore = QPushButton("☁️ クラウドから復元")
        btn_cloud_restore.setStyleSheet("background-color: #0284C7; color: white; font-weight: bold; padding: 4px 10px;")
        btn_cloud_restore.clicked.connect(self.on_cloud_restore_clicked)

        btn_help_guide = QPushButton("💡 PCお引っ越し・移行ガイド")
        btn_help_guide.setStyleSheet("background-color: #4F46E5; color: white; font-weight: bold; padding: 4px 10px;")
        btn_help_guide.clicked.connect(self.open_migration_guide)

        btn_pin = QPushButton("🔑 マスターPIN変更")
        btn_pin.setStyleSheet("background-color: #374151; color: white; font-weight: bold; padding: 4px 10px;")
        btn_pin.clicked.connect(self.open_master_pin_dialog)

        self.btn_autostart = QPushButton()
        self.update_autostart_button_style()
        self.btn_autostart.clicked.connect(self.toggle_autostart)

        header_layout.addWidget(self.status_label)
        header_layout.addStretch()
        header_layout.addWidget(btn_cloud_save)
        header_layout.addWidget(btn_cloud_restore)
        header_layout.addWidget(btn_help_guide)
        header_layout.addWidget(btn_pin)
        header_layout.addWidget(self.btn_autostart)
        main_layout.addWidget(header_box)

        action_layout = QHBoxLayout()

        btn_add = QPushButton("＋ 新規アカウント追加")
        btn_add.setStyleSheet("background-color: #10B981; color: white; font-weight: bold; padding: 6px 14px;")
        btn_add.clicked.connect(lambda: self.open_add_dialog())

        btn_template = QPushButton("📄 CSV雛形データを出力")
        btn_template.setStyleSheet("background-color: #059669; color: white; font-weight: bold; padding: 6px 12px;")
        btn_template.clicked.connect(self.export_csv_template)

        btn_export = QPushButton("📤 登録データをCSV出力(バックアップ)")
        btn_export.setStyleSheet("background-color: #2563EB; color: white; font-weight: bold; padding: 6px 12px;")
        btn_export.clicked.connect(self.export_all_accounts_csv)

        btn_import = QPushButton("📥 CSV一括取り込み")
        btn_import.setStyleSheet("background-color: #6366F1; color: white; font-weight: bold; padding: 6px 14px;")
        btn_import.clicked.connect(self.import_csv)

        btn_test_overlay = QPushButton("🔍 クリップボード / 画面で検索")
        btn_test_overlay.setStyleSheet("background-color: #0078D4; color: white; font-weight: bold; padding: 6px 14px;")
        btn_test_overlay.clicked.connect(self.trigger_search)

        action_layout.addWidget(btn_add)
        action_layout.addWidget(btn_template)
        action_layout.addWidget(btn_export)
        action_layout.addWidget(btn_import)
        action_layout.addStretch()
        action_layout.addWidget(btn_test_overlay)
        main_layout.addLayout(action_layout)

        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["会社名 (製品名)", "ロゴ画像", "ID / ユーザー名", "セキュリティ設定", "備考 / 秘密の質問", "操作"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        main_layout.addWidget(self.table)

        # ✨【ユーザー様ご要望】yukiyanArt 公式ロゴ ＆ Dark Glassmorphism サポートボタン付きコンパクトバナー
        ad_frame = QFrame()
        ad_frame.setObjectName("yukiyanArtBanner")
        ad_frame.setStyleSheet("""
            QFrame#yukiyanArtBanner {
                background-color: rgba(17, 24, 39, 0.85);
                border: 1px solid rgba(255, 255, 255, 0.12);
                border-radius: 8px;
                padding: 3px 8px;
            }
        """)
        ad_layout = QHBoxLayout(ad_frame)
        ad_layout.setContentsMargins(8, 3, 8, 3)
        ad_layout.setSpacing(10)

        # 公式ロゴ画像 (C:\Users\Iwamoto\.gemini\antigravity\scratch\feedback_hub\assets\icons\yukiyanart_logo.jpg)
        logo_path = r"C:\Users\Iwamoto\.gemini\antigravity\scratch\feedback_hub\assets\icons\yukiyanart_logo.jpg"
        if not os.path.exists(logo_path):
            logo_path = os.path.join(os.path.dirname(__file__), "yukiyanart_logo.jpg")

        if os.path.exists(logo_path):
            logo_pixmap = QPixmap(logo_path)
            if not logo_pixmap.isNull():
                scaled_logo = logo_pixmap.scaled(22, 22, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                logo_label = QLabel()
                logo_label.setPixmap(scaled_logo)
                logo_label.setFixedSize(22, 22)
                ad_layout.addWidget(logo_label)

        brand_label = QLabel("<b>yukiyanArt</b>")
        brand_label.setStyleSheet("color: #F9FAFB; font-size: 11px; font-weight: bold; font-family: 'Segoe UI', sans-serif;")
        ad_layout.addWidget(brand_label)

        ad_title = QLabel("｜ 📢 <b>公式サポート ＆ 関連ツール:</b>")
        ad_title.setStyleSheet("color: #9CA3AF; font-size: 11px;")
        ad_layout.addWidget(ad_title)

        # yukiyanArt 共通デザイン 'Dark Glassmorphism' ボタン (feedbackhub://open?app_id=LoginManager 起動)
        btn_feedback = QPushButton("💬 ご意見・ご要望・サポート窓口")
        btn_feedback.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 0.08);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 5px;
                color: #6EE7B7;
                font-weight: bold;
                font-size: 11px;
                padding: 3px 10px;
            }
            QPushButton:hover {
                background-color: rgba(16, 185, 129, 0.25);
                border: 1px solid rgba(52, 211, 153, 0.6);
                color: #A7F3D0;
            }
        """)
        btn_feedback.setToolTip("タップするとyukiyanArt Feedback Hubアプリを起動します")
        btn_feedback.clicked.connect(lambda: QDesktopServices.openUrl(QUrl("feedbackhub://open?app_id=LoginManager")))

        btn_chronos = QPushButton("⏱️ Chronos")
        btn_chronos.setStyleSheet("""
            QPushButton {
                background-color: rgba(79, 70, 229, 0.3);
                border: 1px solid rgba(99, 102, 241, 0.4);
                color: #C7D2FE;
                font-weight: bold;
                font-size: 11px;
                padding: 3px 8px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: rgba(79, 70, 229, 0.6);
                color: #FFFFFF;
            }
        """)
        btn_chronos.clicked.connect(lambda: QDesktopServices.openUrl(QUrl("https://github.com/yukiyanA-Git")))

        btn_github = QPushButton("🌐 公式GitHub")
        btn_github.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.15);
                color: #D1D5DB;
                font-weight: bold;
                font-size: 11px;
                padding: 3px 8px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.15);
                color: #FFFFFF;
            }
        """)
        btn_github.clicked.connect(lambda: QDesktopServices.openUrl(QUrl("https://github.com/yukiyanA-Git/login-manager")))

        ad_layout.addWidget(btn_feedback)
        ad_layout.addWidget(btn_chronos)
        ad_layout.addWidget(btn_github)
        ad_layout.addStretch()

        main_layout.addWidget(ad_frame)

        self.refresh_table()

    def open_migration_guide(self):
        dialog = DataMigrationHelpDialog(self)
        dialog.exec()

    def on_cloud_backup_clicked(self):
        dialog = OnDemandCloudDialog(self.vault.firebase, mode="backup", parent=self)
        if dialog.exec() == QDialog.Accepted:
            success, msg = self.vault.firebase.sync_to_cloud_ondemand(
                email=dialog.user_email,
                pin=dialog.user_pin,
                accounts=self.vault.accounts
            )
            if success:
                QMessageBox.information(self, "クラウド保存完了", msg)
            else:
                QMessageBox.warning(self, "クラウド保存エラー", msg)

    def on_cloud_restore_clicked(self):
        dialog = OnDemandCloudDialog(self.vault.firebase, mode="restore", parent=self)
        if dialog.exec() == QDialog.Accepted:
            cloud_accs, msg = self.vault.firebase.fetch_from_cloud_ondemand(
                email=dialog.user_email,
                pin=dialog.user_pin
            )
            if cloud_accs is not None:
                self.vault.merge_accounts(cloud_accs)
                self.refresh_table()
                QMessageBox.information(self, "クラウド復元完了", msg)
            else:
                QMessageBox.warning(self, "クラウド復元エラー", msg)

    def update_autostart_button_style(self):
        enabled = is_autostart_enabled()
        if enabled:
            self.btn_autostart.setText("⚙️ PC起動時自動スタート: ON")
            self.btn_autostart.setStyleSheet("background-color: #059669; color: white; font-weight: bold; padding: 4px 10px;")
            self.btn_autostart.setToolTip("クリックするとPC起動時の自動常駐を無効化(OFF)にします。")
        else:
            self.btn_autostart.setText("⚙️ PC起動時自動スタート: OFF")
            self.btn_autostart.setStyleSheet("background-color: #4B5563; color: white; padding: 4px 10px;")
            self.btn_autostart.setToolTip("クリックするとPC起動時に自動でタスクバー右下に常駐スタート(ON)します。")

    def toggle_autostart(self):
        current_state = is_autostart_enabled()
        new_state = not current_state
        success = set_autostart(new_state)
        if success:
            self.update_autostart_button_style()
            msg = "【PC起動時の自動常駐: ON】に設定しました。\nパソコンの起動時に自動でタスクバー右下に常駐スタートします。" if new_state else "【PC起動時の自動常駐: OFF】に設定しました。\n必要な時にダブルクリックで手動起動してください。"
            QMessageBox.information(self, "設定変更完了", msg)
        else:
            QMessageBox.warning(self, "設定エラー", "スタートアップ設定の変更に失敗しました。")

    def open_master_pin_dialog(self):
        dialog = MasterPinSettingDialog(self.vault.firebase, self)
        dialog.exec()

    def export_csv_template(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "CSV一括取込用の雛形データを出力保存", "import_template.csv", "CSV Files (*.csv)")
        if file_path:
            headers = [
                "会社名", "製品名1/別名1", "製品名2/別名2", "ID", "パスワード", "セキュリティレベル",
                "第3項目タイトル", "第3項目文字列", "第4項目タイトル", "第4項目文字列",
                "備考", "秘密の質問", "秘密の答え", "カテゴリー", "URL"
            ]
            sample_row = [
                "サンプル株式会社 (記入例)", "サンプル製品名1", "製品名別名2",
                "sample_user_id@example.com", "SamplePass2026!", "1",
                "契約番号", "C12345678", "法人コード", "CORP-9988",
                "ここに備考メモを記入", "秘密の質問サンプル", "秘密の答えサンプル",
                "一般", "https://example.com"
            ]
            with open(file_path, "w", encoding="utf-8-sig", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(headers)
                writer.writerow(sample_row)
            QMessageBox.information(self, "雛形出力完了", f"CSV一括取込用の雛形データ（新フォーマット・記入例1行付き）を出力しました:\n\n{file_path}")

    def export_all_accounts_csv(self):
        if not self.vault.accounts:
            QMessageBox.warning(self, "出力エラー", "出力する登録データが存在しません。")
            return

        file_path, _ = QFileDialog.getSaveFileName(self, "登録データのCSVバックアップ出力", "my_passwords_backup.csv", "CSV Files (*.csv)")
        if file_path:
            count = self.vault.export_accounts_to_csv(file_path)
            QMessageBox.information(self, "バックアップ完了", f"現在登録されている {count} 件のデータをCSV出力しました:\n\n{file_path}")

    def refresh_table(self):
        self.table.setRowCount(0)
        for acc in self.vault.accounts:
            row = self.table.rowCount()
            self.table.insertRow(row)

            sec_level = acc.get("security_level", 1)
            sec_text = "🟢 セキュリティ：低 (即表示)" if sec_level == 1 else "🔒 セキュリティ：高 (要認証)"

            display_name = acc.get("name", "")
            aliases = [a for a in [acc.get("alias1"), acc.get("alias2")] if a]
            if aliases:
                display_name += f" ({', '.join(aliases)})"

            has_logo = "🖼️ あり" if acc.get("logo_image") else "なし"

            notes_info = []
            if acc.get("field1_name") and acc.get("field1_value"):
                notes_info.append(f"{acc.get('field1_name')}:{acc.get('field1_value')}")
            if acc.get("field2_name") and acc.get("field2_value"):
                notes_info.append(f"{acc.get('field2_name')}:{acc.get('field2_value')}")
            if acc.get("notes"):
                notes_info.append(acc.get("notes"))
            if acc.get("sec_question"):
                notes_info.append(f"Q:{acc.get('sec_question')}")

            has_notes = " / ".join(notes_info) if notes_info else "なし"

            item_name = QTableWidgetItem(display_name)
            item_logo = QTableWidgetItem(has_logo)
            item_user = QTableWidgetItem(acc.get("username", ""))
            item_sec = QTableWidgetItem(sec_text)
            item_notes = QTableWidgetItem(has_notes)

            if acc.get("logo_image"):
                item_logo.setForeground(QColor("#059669"))
                item_logo.setFont(QFont("Segoe UI", 9, QFont.Bold))

            if sec_level == 3:
                item_sec.setForeground(QColor("#D97706"))

            self.table.setItem(row, 0, item_name)
            self.table.setItem(row, 1, item_logo)
            self.table.setItem(row, 2, item_user)
            self.table.setItem(row, 3, item_sec)
            self.table.setItem(row, 4, item_notes)

            action_widget = QWidget()
            action_layout = QHBoxLayout(action_widget)
            action_layout.setContentsMargins(2, 2, 2, 2)
            action_layout.setSpacing(4)

            btn_edit = QPushButton("✏️ 編集")
            btn_edit.setStyleSheet("background-color: #0078D4; color: white; padding: 2px 8px; font-weight: bold;")
            acc_data = acc
            btn_edit.clicked.connect(lambda _, a=acc_data: self.edit_acc(a))

            btn_delete = QPushButton("削除")
            btn_delete.setStyleSheet("background-color: #EF4444; color: white; padding: 2px 8px;")
            acc_id = acc.get("id")
            btn_delete.clicked.connect(lambda _, a_id=acc_id: self.delete_acc(a_id))

            action_layout.addWidget(btn_edit)
            action_layout.addWidget(btn_delete)
            self.table.setCellWidget(row, 5, action_widget)

    def edit_acc(self, acc_data: dict):
        overlay_cb = self.overlay.show_overlay_for_register if self.overlay else None
        dialog = AccountAddDialog(edit_data=acc_data, overlay_callback=overlay_cb, parent=self)
        if dialog.exec() == QDialog.Accepted:
            new_data = dialog.get_data()
            if new_data["name"]:
                acc_data["name"] = new_data["name"]
                acc_data["username"] = new_data["username"]
                acc_data["password"] = new_data["password"]
                acc_data["security_level"] = new_data["security_level"]
                acc_data["category"] = new_data["category"]
                acc_data["url"] = new_data["url"]
                acc_data["notes"] = new_data["notes"]
                acc_data["sec_question"] = new_data["sec_question"]
                acc_data["sec_answer"] = new_data["sec_answer"]
                acc_data["alias1"] = new_data["alias1"]
                acc_data["alias2"] = new_data["alias2"]
                acc_data["field1_name"] = new_data["field1_name"]
                acc_data["field1_value"] = new_data["field1_value"]
                acc_data["field2_name"] = new_data["field2_name"]
                acc_data["field2_value"] = new_data["field2_value"]

                if new_data["logo_image"]:
                    acc_data["logo_image"] = new_data["logo_image"]

                aliases = [new_data["name"].lower()]
                if new_data["alias1"]:
                    aliases.append(new_data["alias1"].lower())
                if new_data["alias2"]:
                    aliases.append(new_data["alias2"].lower())
                if new_data["field1_name"]:
                    aliases.append(new_data["field1_name"].lower())
                if new_data["field2_name"]:
                    aliases.append(new_data["field2_name"].lower())

                acc_data["aliases"] = aliases

                self.vault.save_vault()
                self.refresh_table()

    def open_add_dialog(self, initial_name: str = "", logo_b64: str = ""):
        overlay_cb = self.overlay.show_overlay_for_register if self.overlay else None
        dialog = AccountAddDialog(initial_name=initial_name, logo_b64=logo_b64, overlay_callback=overlay_cb, parent=self)
        if dialog.exec() == QDialog.Accepted:
            data = dialog.get_data()
            if data["name"]:
                self.vault.add_account(
                    name=data["name"],
                    username=data["username"],
                    password=data["password"],
                    security_level=data["security_level"],
                    category=data["category"],
                    url=data["url"],
                    notes=data["notes"],
                    sec_question=data["sec_question"],
                    sec_answer=data["sec_answer"],
                    alias1=data["alias1"],
                    alias2=data["alias2"],
                    logo_image=data["logo_image"],
                    field1_name=data["field1_name"],
                    field1_value=data["field1_value"],
                    field2_name=data["field2_name"],
                    field2_value=data["field2_value"]
                )
                self.refresh_table()

    def import_csv(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "CSVファイルの取り込み", "", "CSV Files (*.csv)")
        if file_path:
            count = self.vault.import_csv(file_path)
            QMessageBox.information(self, "インポート完了", f"{count} 件のアカウント情報をCSVから読み込みました。")
            self.refresh_table()

    def delete_acc(self, acc_id: str):
        self.vault.delete_account(acc_id)
        self.refresh_table()

    def trigger_search(self):
        self.hide()
        if self.overlay:
            self.overlay.smart_search()
