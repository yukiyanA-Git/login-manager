from PySide6.QtWidgets import QMenu, QWidget, QApplication
from PySide6.QtCore import Qt, QPoint, QUrl
from PySide6.QtGui import QAction, QFont, QIcon, QColor, QDesktopServices

class QuickTrayMenu(QMenu):
    def __init__(self, manager_win, overlay_instance, parent=None):
        super().__init__(parent)
        self.manager_win = manager_win
        self.overlay = overlay_instance

        self.setStyleSheet("""
            QMenu {
                background-color: #111827;
                border: 2px solid #0078D4;
                border-radius: 10px;
                color: #F9FAFB;
                padding: 6px;
                font-family: 'Segoe UI', 'Meiryo', sans-serif;
                font-size: 13px;
            }
            QMenu::item {
                padding: 8px 16px;
                border-radius: 6px;
                margin: 2px 4px;
            }
            QMenu::item:selected {
                background-color: #0078D4;
                color: #FFFFFF;
                font-weight: bold;
            }
            QMenu::separator {
                height: 1px;
                background-color: #374151;
                margin: 4px 8px;
            }
        """)

        self.aboutToShow.connect(self.build_menu)
        self.build_menu()

    def build_menu(self):
        self.clear()

        title_action = QAction("🔑  ログインマネージャー クイックメニュー", self)
        title_action.setEnabled(False)
        self.addAction(title_action)
        self.addSeparator()

        # Always explicitly display 🟢 ローカル安全保存モード (オフライン動作中)
        google_text = "🟢  ローカル安全保存モード (オフライン動作中)"
        action_google = QAction(google_text, self)
        action_google.setEnabled(False)
        self.addAction(action_google)

        self.addSeparator()

        # Dynamic Bookmark Submenu
        bookmark_menu = QMenu("🔖  登録サイトを開く (ブックマーク)", self)
        bookmark_menu.setStyleSheet("""
            QMenu {
                background-color: #1F2937;
                border: 1px solid #0078D4;
                border-radius: 8px;
                color: #F9FAFB;
                padding: 4px;
            }
            QMenu::item {
                padding: 6px 14px;
            }
            QMenu::item:selected {
                background-color: #4F46E5;
                color: #FFFFFF;
            }
        """)

        has_bookmarks = False
        accounts = self.manager_win.vault.accounts
        for acc in accounts:
            name = acc.get("name", "")
            url = acc.get("url", "")
            if name:
                has_bookmarks = True
                display_label = f"🌐  {name}"
                if url:
                    display_label += f" ({url[:25]}...)" if len(url) > 25 else f" ({url})"

                action_site = QAction(display_label, self)
                action_site.triggered.connect(lambda _, a=acc: self.open_bookmark_and_popup(a))
                bookmark_menu.addAction(action_site)

        if not has_bookmarks:
            action_empty = QAction("（登録サイトはありません）", self)
            action_empty.setEnabled(False)
            bookmark_menu.addAction(action_empty)

        self.addMenu(bookmark_menu)

        # Action: Register New Account
        action_register = QAction("➕  新規アカウント登録 (コピー文/画面ロゴから)", self)
        action_register.triggered.connect(self.trigger_register)
        self.addAction(action_register)

        # Action: Quick Clipboard / Window Search
        action_search = QAction("🔍  ログイン情報検索 (コピー文 Ctrl+C)", self)
        action_search.triggered.connect(self.trigger_search)
        self.addAction(action_search)

        # Action: Screen Region OCR & Logo Search
        action_ocr = QAction("📐  画面ロゴ/枠で囲んで検索 (画像比較)", self)
        action_ocr.triggered.connect(self.trigger_ocr)
        self.addAction(action_ocr)

        self.addSeparator()

        # Action: Open Manager Window
        action_manage = QAction("⚙️  アカウント管理画面を開く", self)
        action_manage.triggered.connect(self.open_manager_window)
        self.addAction(action_manage)

        self.addSeparator()

        # Action: Quit App
        action_quit = QAction("✕  アプリ完全終了", self)
        action_quit.triggered.connect(self.quit_app)
        self.addAction(action_quit)

    def open_bookmark_and_popup(self, acc_data: dict):
        url = acc_data.get("url", "")
        if url:
            if not url.startswith("http://") and not url.startswith("https://"):
                url = "https://" + url
            QDesktopServices.openUrl(QUrl(url))

        if self.overlay:
            self.overlay.handle_account_found(acc_data)

    def trigger_register(self):
        clip_text = QApplication.clipboard().text().strip()
        if self.overlay:
            self.manager_win.open_add_dialog(initial_name=clip_text)

    def trigger_search(self):
        if self.overlay:
            self.overlay.smart_search()

    def trigger_ocr(self):
        if self.overlay:
            self.overlay.show_overlay()

    def open_manager_window(self):
        self.manager_win.show()
        self.manager_win.raise_()
        self.manager_win.activateWindow()

    def quit_app(self):
        QApplication.quit()
