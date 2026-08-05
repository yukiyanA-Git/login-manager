from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QFileDialog, QMessageBox,
    QDialog, QFormLayout, QLineEdit, QComboBox, QGroupBox, QTextEdit, QApplication
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QClipboard

class FirebaseLoginDialog(QDialog):
    def __init__(self, firebase_client, parent=None):
        super().__init__(parent)
        self.firebase = firebase_client
        self.setWindowTitle("👤 Firebaseクラウド同期・アカウント設定")
        self.setFixedWidth(440)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        info_label = QLabel(
            "<b>クラウド同期（Firebase）の設定</b><br>"
            "Google FirebaseのプロジェクトIDを入力すると、複数のPC間で全ログインデータが自動リアルタイム同期されます。"
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: #374151; font-size: 11px;")
        layout.addWidget(info_label)

        form = QFormLayout()
        self.project_input = QLineEdit()
        self.project_input.setText(self.firebase.project_id if self.firebase.enabled else "")
        self.project_input.setPlaceholderText("例: my-login-manager-12345")
        form.addRow("FirebaseプロジェクトID:", self.project_input)
        layout.addLayout(form)

        btn_box = QHBoxLayout()
        btn_logout = QPushButton("🚪 同期解除 (ログアウト)")
        btn_logout.setStyleSheet("background-color: #EF4444; color: white;")
        btn_logout.clicked.connect(self.do_logout)

        btn_save = QPushButton("💾 連携保存 (ログイン同期)")
        btn_save.setStyleSheet("background-color: #0078D4; color: white; font-weight: bold;")
        btn_save.clicked.connect(self.do_save)

        btn_box.addWidget(btn_logout)
        btn_box.addWidget(btn_save)
        layout.addLayout(btn_box)

    def do_save(self):
        pid = self.project_input.text().strip()
        if pid:
            self.firebase.project_id = pid
            self.firebase.enabled = True
            self.firebase.save_config_file(enabled=True, project_id=pid)
            QMessageBox.information(self, "同期完了", f"Firebaseプロジェクト【{pid}】に連携接続しました。")
            self.accept()

    def do_logout(self):
        self.firebase.enabled = False
        self.firebase.save_config_file(enabled=False, project_id="")
        QMessageBox.information(self, "ログアウト", "Firebaseクラウド同期を解除（ログアウト）し、ローカル保存モードに変更しました。")
        self.accept()


class AccountAddDialog(QDialog):
    def __init__(self, initial_name: str = "", overlay_callback=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("新しいログイン情報の登録")
        self.setFixedWidth(450)
        self.overlay_callback = overlay_callback
        self.extra_expanded = False

        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        form_layout = QFormLayout()
        form_layout.setSpacing(10)

        name_layout = QHBoxLayout()
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("例: Sansan, マネーフォワード, Amazon")

        clip_text = QApplication.clipboard().text().strip()
        if initial_name:
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
        form_layout.addRow("ID / メール *:", self.user_input)

        self.pass_input = QLineEdit()
        self.pass_input.setEchoMode(QLineEdit.Password)
        self.pass_input.setPlaceholderText("パスワード")
        form_layout.addRow("パスワード *:", self.pass_input)

        self.level_combo = QComboBox()
        self.level_combo.addItem("🟢 セキュリティ：低 (認証なし・すぐ表示)", 1)
        self.level_combo.addItem("🔒 セキュリティ：高 (顔認証/指紋/PINを要求)", 3)
        form_layout.addRow("セキュリティレベル *:", self.level_combo)

        layout.addLayout(form_layout)

        self.btn_toggle_extra = QPushButton("＋ 製品名(別名)・備考・秘密の質問を追加 (オプション)")
        self.btn_toggle_extra.setStyleSheet("background-color: #374151; color: #F3F4F6; font-size: 11px;")
        self.btn_toggle_extra.clicked.connect(self.toggle_extra_fields)
        layout.addWidget(self.btn_toggle_extra)

        self.extra_widget = QWidget()
        extra_form = QFormLayout(self.extra_widget)
        extra_form.setContentsMargins(0, 0, 0, 0)
        extra_form.setSpacing(8)

        self.alias1_input = QLineEdit()
        self.alias1_input.setPlaceholderText("例: Eight (ログイン画面に製品名がある場合)")

        self.alias2_input = QLineEdit()
        self.alias2_input.setPlaceholderText("例: MFクラウド")

        self.notes_input = QTextEdit()
        self.notes_input.setPlaceholderText("メモ、契約番号、第2パスワードなど")
        self.notes_input.setFixedHeight(45)

        self.sec_q_input = QLineEdit()
        self.sec_q_input.setPlaceholderText("例: 母親の旧姓 / 初めて飼ったペット")

        self.sec_a_input = QLineEdit()
        self.sec_a_input.setPlaceholderText("秘密の質問の答え")

        self.category_input = QLineEdit()
        self.category_input.setText("一般")

        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://...")

        extra_form.addRow("製品名 / 別名1:", self.alias1_input)
        extra_form.addRow("製品名 / 別名2:", self.alias2_input)
        extra_form.addRow("備考・メモ:", self.notes_input)
        extra_form.addRow("秘密の質問:", self.sec_q_input)
        extra_form.addRow("秘密の答え:", self.sec_a_input)
        extra_form.addRow("カテゴリー:", self.category_input)
        extra_form.addRow("URL:", self.url_input)

        self.extra_widget.setVisible(False)
        layout.addWidget(self.extra_widget)

        btn_box = QHBoxLayout()
        btn_cancel = QPushButton("キャンセル")
        btn_cancel.clicked.connect(self.reject)
        btn_save = QPushButton("保存")
        btn_save.setStyleSheet("background-color: #0078D4; color: white; font-weight: bold; padding: 6px 16px;")
        btn_save.clicked.connect(self.accept)

        btn_box.addWidget(btn_cancel)
        btn_box.addWidget(btn_save)
        layout.addLayout(btn_box)

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

    def set_company_name_and_reopen(self, detected_name: str):
        if detected_name:
            self.name_input.setText(detected_name)
        self.show()

    def get_data(self):
        return {
            "name": self.name_input.text().strip(),
            "alias1": self.alias1_input.text().strip(),
            "alias2": self.alias2_input.text().strip(),
            "username": self.user_input.text().strip(),
            "password": self.pass_input.text().strip(),
            "security_level": self.level_combo.currentData(),
            "notes": self.notes_input.toPlainText().strip(),
            "sec_question": self.sec_q_input.text().strip(),
            "sec_answer": self.sec_a_input.text().strip(),
            "category": self.category_input.text().strip(),
            "url": self.url_input.text().strip()
        }


class AccountManagerWindow(QMainWindow):
    def __init__(self, vault_instance, overlay_instance=None):
        super().__init__()
        self.vault = vault_instance
        self.overlay = overlay_instance

        self.setWindowTitle("ログインマネージャー - アカウント管理 & クラウド同期")
        self.resize(850, 540)
        self.init_ui()

    def init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)

        # Header Info & Cloud Sync Status
        header_box = QGroupBox("設定・クラウド同期ステータス")
        header_layout = QHBoxLayout(header_box)

        fb_enabled = self.vault.firebase.enabled
        pid = self.vault.firebase.project_id
        status_text = f"🟢 Firebaseクラウド同期モード ({pid})" if fb_enabled else "🟡 ローカル暗号化保存モード (オフライン)"
        self.status_label = QLabel(status_text)
        self.status_label.setFont(QFont("Segoe UI", 10, QFont.Bold))

        btn_account = QPushButton("👤 クラウド設定 / ログイン")
        btn_account.setStyleSheet("background-color: #4F46E5; color: white; font-weight: bold;")
        btn_account.clicked.connect(self.open_account_dialog)

        btn_sync_now = QPushButton("🔄 今すぐ同期")
        btn_sync_now.clicked.connect(self.sync_now)

        header_layout.addWidget(self.status_label)
        header_layout.addStretch()
        header_layout.addWidget(btn_account)
        header_layout.addWidget(btn_sync_now)
        main_layout.addWidget(header_box)

        action_layout = QHBoxLayout()

        btn_add = QPushButton("＋ 新規アカウント追加")
        btn_add.setStyleSheet("background-color: #10B981; color: white; font-weight: bold; padding: 6px 14px;")
        btn_add.clicked.connect(lambda: self.open_add_dialog())

        btn_import = QPushButton("📥 CSV一括取り込み")
        btn_import.setStyleSheet("background-color: #6366F1; color: white; font-weight: bold; padding: 6px 14px;")
        btn_import.clicked.connect(self.import_csv)

        btn_test_overlay = QPushButton("🔍 クリップボード / 画面で検索")
        btn_test_overlay.setStyleSheet("background-color: #0078D4; color: white; font-weight: bold; padding: 6px 14px;")
        btn_test_overlay.clicked.connect(self.trigger_search)

        action_layout.addWidget(btn_add)
        action_layout.addWidget(btn_import)
        action_layout.addStretch()
        action_layout.addWidget(btn_test_overlay)
        main_layout.addLayout(action_layout)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["会社名 (製品名)", "ID / ユーザー名", "セキュリティ設定", "備考 / 秘密の質問", "操作"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        main_layout.addWidget(self.table)

        self.refresh_table()

    def open_account_dialog(self):
        dialog = FirebaseLoginDialog(self.vault.firebase, self)
        if dialog.exec() == QDialog.Accepted:
            fb_enabled = self.vault.firebase.enabled
            pid = self.vault.firebase.project_id
            status_text = f"🟢 Firebaseクラウド同期モード ({pid})" if fb_enabled else "🟡 ローカル暗号化保存モード (オフライン)"
            self.status_label.setText(status_text)
            self.sync_now()

    def sync_now(self):
        self.vault.save_vault()
        QMessageBox.information(self, "同期完了", "データを保存およびクラウド同期しました。")

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

            has_notes = "あり 📝" if (acc.get("notes") or acc.get("sec_question")) else "なし"

            item_name = QTableWidgetItem(display_name)
            item_user = QTableWidgetItem(acc.get("username", ""))
            item_sec = QTableWidgetItem(sec_text)
            item_notes = QTableWidgetItem(has_notes)

            if sec_level == 3:
                item_sec.setForeground(QColor("#D97706"))

            self.table.setItem(row, 0, item_name)
            self.table.setItem(row, 1, item_user)
            self.table.setItem(row, 2, item_sec)
            self.table.setItem(row, 3, item_notes)

            btn_delete = QPushButton("削除")
            btn_delete.setStyleSheet("background-color: #EF4444; color: white; padding: 2px 8px;")
            acc_id = acc.get("id")
            btn_delete.clicked.connect(lambda _, a_id=acc_id: self.delete_acc(a_id))
            self.table.setCellWidget(row, 4, btn_delete)

    def open_add_dialog(self, initial_name: str = ""):
        overlay_cb = self.overlay.show_overlay_for_register if self.overlay else None
        dialog = AccountAddDialog(initial_name=initial_name, overlay_callback=overlay_cb, parent=self)
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
                    alias2=data["alias2"]
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
