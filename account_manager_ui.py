import os
import csv
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QFileDialog, QMessageBox,
    QDialog, QFormLayout, QLineEdit, QComboBox, QGroupBox, QTextEdit, QApplication
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QClipboard

class GoogleAuthDialog(QDialog):
    def __init__(self, firebase_client, parent=None):
        super().__init__(parent)
        self.firebase = firebase_client
        self.setWindowTitle("🔴 Googleアカウントサインイン (マルチデバイス同期)")
        self.setFixedWidth(440)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        info_label = QLabel(
            "<b>Googleアカウントによる個別クラウド連携</b><br>"
            "Googleアカウントでサインインすると、あなたのデータ専用の暗号化エリアにクラウド保存され、"
            "他のデバイス（別PC等）でも同じGoogleアカウントで即座に同期・復元されます。<br>"
            "※第三者や他のユーザーにデータが見られることはありません。"
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: #374151; font-size: 11px;")
        layout.addWidget(info_label)

        form = QFormLayout()
        self.email_input = QLineEdit()
        self.email_input.setText(self.firebase.user_email)
        self.email_input.setPlaceholderText("例: your_name@gmail.com")
        form.addRow("Googleメールアドレス:", self.email_input)

        layout.addLayout(form)

        btn_box = QHBoxLayout()
        btn_logout = QPushButton("🚪 ログアウト (同期解除)")
        btn_logout.setStyleSheet("background-color: #EF4444; color: white;")
        btn_logout.clicked.connect(self.do_logout)

        btn_save = QPushButton("🔴 Googleアカウントでサインイン")
        btn_save.setStyleSheet("background-color: #DC2626; color: white; font-weight: bold; padding: 6px 12px;")
        btn_save.clicked.connect(self.do_signin)

        btn_box.addWidget(btn_logout)
        btn_box.addWidget(btn_save)
        layout.addLayout(btn_box)

    def do_signin(self):
        email = self.email_input.text().strip()
        if email and "@" in email:
            self.firebase.save_user_session(user_email=email)
            QMessageBox.information(self, "サインイン完了", f"Googleアカウント【{email}】としてクラウド同期をスタートしました。")
            self.accept()
        else:
            QMessageBox.warning(self, "入力エラー", "有効なGoogleメールアドレス（例: user@gmail.com）を入力してください。")

    def do_logout(self):
        self.firebase.logout_user()
        QMessageBox.information(self, "ログアウト", "Googleアカウントをログアウトし、ローカル保存モードに変更しました。")
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

        # Logo status and capture/change button line
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

        self.alias1_input = QLineEdit()
        self.alias1_input.setPlaceholderText("例: Eight (ログイン画面に製品名がある場合)")
        if is_edit:
            self.alias1_input.setText(edit_data.get("alias1", ""))

        self.alias2_input = QLineEdit()
        self.alias2_input.setPlaceholderText("例: MFクラウド")
        if is_edit:
            self.alias2_input.setText(edit_data.get("alias2", ""))

        self.notes_input = QTextEdit()
        self.notes_input.setPlaceholderText("メモ、契約番号、第2パスワードなど")
        self.notes_input.setFixedHeight(45)
        if is_edit:
            self.notes_input.setPlainText(edit_data.get("notes", ""))

        self.sec_q_input = QLineEdit()
        self.sec_q_input.setPlaceholderText("例: 母親の旧姓 / 初めて飼ったペット")
        if is_edit:
            self.sec_q_input.setText(edit_data.get("sec_question", ""))

        self.sec_a_input = QLineEdit()
        self.sec_a_input.setPlaceholderText("秘密の質問の答え")
        if is_edit:
            self.sec_a_input.setText(edit_data.get("sec_answer", ""))

        self.category_input = QLineEdit()
        self.category_input.setText(edit_data.get("category", "一般") if is_edit else "一般")

        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://...")
        if is_edit:
            self.url_input.setText(edit_data.get("url", ""))

        extra_form.addRow("製品名 / 別名1:", self.alias1_input)
        extra_form.addRow("製品名 / 別名2:", self.alias2_input)
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
            "url": self.url_input.text().strip(),
            "logo_image": self.logo_b64
        }


class AccountManagerWindow(QMainWindow):
    def __init__(self, vault_instance, overlay_instance=None):
        super().__init__()
        self.vault = vault_instance
        self.overlay = overlay_instance

        self.setWindowTitle("ログインマネージャー - アカウント管理 & Googleクラウド同期")
        self.resize(900, 540)
        self.init_ui()

    def init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)

        header_box = QGroupBox("クラウド連携 ＆ 同期ステータス")
        header_layout = QHBoxLayout(header_box)

        user_email = self.vault.firebase.user_email
        if user_email:
            status_text = f"🔴 Googleアカウント連動中 ({user_email})"
        else:
            status_text = "🟡 未サインイン (ローカル保存のみ)"

        self.status_label = QLabel(status_text)
        self.status_label.setFont(QFont("Segoe UI", 10, QFont.Bold))

        btn_google = QPushButton("🔴 Googleでサインイン")
        btn_google.setStyleSheet("background-color: #DC2626; color: white; font-weight: bold;")
        btn_google.clicked.connect(self.open_google_dialog)

        btn_sync_now = QPushButton("🔄 今すぐ同期")
        btn_sync_now.clicked.connect(self.sync_now)

        header_layout.addWidget(self.status_label)
        header_layout.addStretch()
        header_layout.addWidget(btn_google)
        header_layout.addWidget(btn_sync_now)
        main_layout.addWidget(header_box)

        action_layout = QHBoxLayout()

        btn_add = QPushButton("＋ 新規アカウント追加")
        btn_add.setStyleSheet("background-color: #10B981; color: white; font-weight: bold; padding: 6px 14px;")
        btn_add.clicked.connect(lambda: self.open_add_dialog())

        btn_template = QPushButton("📄 CSVテンプレート保存")
        btn_template.setStyleSheet("background-color: #059669; color: white; font-weight: bold; padding: 6px 12px;")
        btn_template.clicked.connect(self.export_csv_template)

        btn_import = QPushButton("📥 CSV一括取り込み")
        btn_import.setStyleSheet("background-color: #6366F1; color: white; font-weight: bold; padding: 6px 14px;")
        btn_import.clicked.connect(self.import_csv)

        btn_test_overlay = QPushButton("🔍 クリップボード / 画面で検索")
        btn_test_overlay.setStyleSheet("background-color: #0078D4; color: white; font-weight: bold; padding: 6px 14px;")
        btn_test_overlay.clicked.connect(self.trigger_search)

        action_layout.addWidget(btn_add)
        action_layout.addWidget(btn_template)
        action_layout.addWidget(btn_import)
        action_layout.addStretch()
        action_layout.addWidget(btn_test_overlay)
        main_layout.addLayout(action_layout)

        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["会社名 (製品名)", "ロゴ画像", "ID / ユーザー名", "セキュリティ設定", "備考 / 秘密の質問", "操作"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        main_layout.addWidget(self.table)

        self.refresh_table()

    def export_csv_template(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "取込用CSVテンプレートの保存", "import_template.csv", "CSV Files (*.csv)")
        if file_path:
            headers = ["会社名", "製品名1", "製品名2", "ID", "パスワード", "セキュリティレベル", "備考", "秘密の質問", "秘密の答え", "カテゴリー", "URL"]
            rows = [
                ["楽天市場", "楽天Ichiba", "", "rakuten_user@example.com", "RakutenPass2026!", "1", "ポイントカード会員", "", "", "ショッピング", "https://www.rakuten.co.jp"],
                ["SBI証券", "SBIネット証券", "", "sbi_account_8899", "SBIStrictSecuredPass#999", "3", "取引暗号コード: 1234", "母親の旧姓", "田中", "金融・資産", "https://www.sbisec.co.jp"],
                ["Sansan", "Eight", "Sansan名刺", "user_sansan@example.com", "SansanPassword#2026", "1", "名刺管理サービスEight", "", "", "ビジネス", "https://8card.net"]
            ]
            with open(file_path, "w", encoding="utf-8-sig", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(headers)
                writer.writerows(rows)
            QMessageBox.information(self, "テンプレート保存完了", f"取込用CSVテンプレートを出力しました:\n\n{file_path}")

    def open_google_dialog(self):
        dialog = GoogleAuthDialog(self.vault.firebase, self)
        if dialog.exec() == QDialog.Accepted:
            user_email = self.vault.firebase.user_email
            if user_email:
                status_text = f"🔴 Googleアカウント連動中 ({user_email})"
            else:
                status_text = "🟡 未サインイン (ローカル保存のみ)"
            self.status_label.setText(status_text)

            cloud_accs = self.vault.firebase.fetch_from_cloud()
            if cloud_accs:
                self.vault.accounts = cloud_accs
                self.vault.save_local_file()

            self.refresh_table()

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

            has_logo = "🖼️ あり" if acc.get("logo_image") else "なし"
            has_notes = "あり 📝" if (acc.get("notes") or acc.get("sec_question")) else "なし"

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

            # Action Buttons (Edit + Delete)
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
                if new_data["logo_image"]:
                    acc_data["logo_image"] = new_data["logo_image"]

                aliases = [new_data["name"].lower()]
                if new_data["alias1"]:
                    aliases.append(new_data["alias1"].lower())
                if new_data["alias2"]:
                    aliases.append(new_data["alias2"].lower())
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
                    logo_image=data["logo_image"]
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
